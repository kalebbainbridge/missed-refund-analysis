import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3

from app.database import DATABASE_PATH, get_connection
from app.case_actions import complete_case, save_case_notes


def read_case(database_path, case_id):
    with get_connection(database_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            'SELECT * FROM agent_updates WHERE "Case ID" = ?;',
            (case_id,),
        ).fetchone()
        return dict(row)


def event_count(database_path):
    with get_connection(database_path) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM workflow_events;"
        ).fetchone()[0]


def main():
    Path("work").mkdir(exist_ok=True)

    with TemporaryDirectory(dir="work") as temporary_folder:
        test_path = Path(temporary_folder) / "completion_test.db"

        with closing(sqlite3.connect(
            DATABASE_PATH.resolve().as_uri() + "?mode=ro",
            uri=True,
        )) as original:
            with closing(sqlite3.connect(test_path)) as destination:
                original.backup(destination)

        with get_connection(test_path) as connection:
            case_ids = [
                row[0]
                for row in connection.execute(
                    """
                    SELECT "Case ID"
                    FROM agent_updates
                    WHERE "Case Status" = 'Open'
                    ORDER BY "Case ID"
                    LIMIT 3;
                    """
                )
            ]

        assert len(case_ids) == 3

        outcomes = [
            "Refund Processed",
            "Refund Already Processed",
            "No Refund Due",
        ]

        for case_id, outcome in zip(case_ids, outcomes):
            with get_connection(test_path) as connection:
                connection.execute(
                    """
                    UPDATE agent_updates
                    SET "Agent Working" = 'DH001',
                        "Record Version" = "Record Version" + 1
                    WHERE "Case ID" = ?;
                    """,
                    (case_id,),
                )

            before = read_case(test_path, case_id)
            version = before["Record Version"]
            events_before = event_count(test_path)

            assert not complete_case(
                case_id, "DH002", outcome, "Wrong agent",
                version, database_path=test_path,
            )

            assert not complete_case(
                case_id, "DH001", outcome, "Stale attempt",
                version - 1, database_path=test_path,
            )

            assert read_case(test_path, case_id) == before
            assert event_count(test_path) == events_before

            assert complete_case(
                case_id, "DH001", outcome, "Investigation finished",
                version, database_path=test_path,
            )

            after = read_case(test_path, case_id)

            assert after["Case Status"] == "Completed"
            assert after["Final Outcome"] == outcome
            assert after["Completed By"] == "DH001"
            assert after["Agent Notes"] == "Investigation finished"
            assert after["Completion Date"]
            assert after["Last Updated Date"]
            assert after["Record Version"] == version + 1
            assert event_count(test_path) == events_before + 1

            assert not complete_case(
                case_id, "DH001", "No Refund Due", "Overwrite attempt",
                version + 1, database_path=test_path,
            )

            assert not save_case_notes(
                case_id, "DH001", "Changed after completion",
                version + 1, database_path=test_path,
            )

            assert read_case(test_path, case_id) == after
            assert event_count(test_path) == events_before + 1

            print(f"{outcome}: passed.")

    print("Wrong-agent and stale completion attempts blocked.")
    print("Completed outcomes and notes cannot be overwritten.")
    print("Exactly one event added per successful completion.")
    print("Live database unchanged; temporary copy removed.")


class CaseActionTest(unittest.TestCase):
    def test_scenario(self):
        main()


if __name__ == "__main__":
    unittest.main()
