import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3

from app.database import DATABASE_PATH, get_connection
from app.case_actions import save_case_notes
from tests.test_completion import read_case, event_count


def main():
    Path("work").mkdir(exist_ok=True)

    with TemporaryDirectory(dir="work") as temporary_folder:
        test_path = Path(temporary_folder) / "investigation_test.db"

        with closing(sqlite3.connect(
            DATABASE_PATH.resolve().as_uri() + "?mode=ro",
            uri=True,
        )) as original:
            with closing(sqlite3.connect(test_path)) as destination:
                original.backup(destination)

        with get_connection(test_path) as connection:
            case_id = connection.execute(
                """
                SELECT "Case ID"
                FROM agent_updates
                WHERE "Case Status" = 'Open'
                ORDER BY "Case ID"
                LIMIT 1;
                """
            ).fetchone()[0]

            connection.execute(
                """
                UPDATE agent_updates
                SET "Agent Working" = 'DH001',
                    "Record Version" = "Record Version" + 1
                WHERE "Case ID" = ?;
                """,
                (case_id,),
            )

        def expect_rejection(reason, notes):
            before = read_case(test_path, case_id)
            events_before = event_count(test_path)

            try:
                save_case_notes(
                    case_id,
                    "DH001",
                    notes,
                    before["Record Version"],
                    database_path=test_path,
                    investigation_reason=reason,
                )
            except ValueError:
                pass
            else:
                raise AssertionError("Invalid investigation was accepted.")

            assert read_case(test_path, case_id) == before
            assert event_count(test_path) == events_before

        expect_rejection("Other", "")
        expect_rejection("Unrecognised Reason", "Some notes")

        before = read_case(test_path, case_id)
        events_before = event_count(test_path)

        assert save_case_notes(
            case_id,
            "DH001",
            "Explanation of the unusual cause.",
            before["Record Version"],
            database_path=test_path,
            investigation_reason="Other",
        )

        after = read_case(test_path, case_id)

        assert after["Investigation Reason"] == "Other"
        assert after["Record Version"] == before["Record Version"] + 1
        assert event_count(test_path) == events_before + 1

        # Omitting the reason must preserve Other and its note requirement.
        expect_rejection(None, " ")

        assert save_case_notes(
            case_id,
            "DH001",
            "Updated explanation of the unusual cause.",
            after["Record Version"],
            database_path=test_path,
        )

        latest = read_case(test_path, case_id)
        assert latest["Investigation Reason"] == "Other"

        assert not save_case_notes(
            case_id,
            "DH001",
            "Stale attempt to change the reason.",
            before["Record Version"],
            database_path=test_path,
            investigation_reason="Refund Action Missed",
        )

        assert read_case(test_path, case_id) == latest

        # Test investigation updates while awaiting a dependency.
        with get_connection(test_path) as connection:
            connection.execute(
                """
                UPDATE agent_updates
                SET "Case Status" = 'Awaiting Dependency',
                    "Dependency Type" = 'Senior Review',
                    "Dependency Owner" = 'Synthetic Senior Team',
                    "Dependency Details" = 'Review remains outstanding.',
                    "Record Version" = "Record Version" + 1
                WHERE "Case ID" = ?;
                """,
                (case_id,),
            )

        before = read_case(test_path, case_id)
        events_before = event_count(test_path)

        assert save_case_notes(
            case_id,
            "DH001",
            "Cause established; senior review still outstanding.",
            before["Record Version"],
            database_path=test_path,
            investigation_reason="Refund Action Missed",
        )

        after = read_case(test_path, case_id)

        assert after["Investigation Reason"] == "Refund Action Missed"
        assert after["Record Version"] == before["Record Version"] + 1
        assert event_count(test_path) == events_before + 1

        for column in before:
            if column not in {
                "Agent Notes",
                "Investigation Reason",
                "Last Updated Date",
                "Record Version",
            }:
                assert after[column] == before[column], column

    print("Invalid reasons and unexplained Other blocked.")
    print("Notes-only saves preserve the saved reason.")
    print("Stale investigation updates blocked.")
    print("Dependency status, details and assignment preserved.")
    print("Live database unchanged; temporary copy removed.")


class CaseActionTest(unittest.TestCase):
    def test_scenario(self):
        main()


if __name__ == "__main__":
    unittest.main()