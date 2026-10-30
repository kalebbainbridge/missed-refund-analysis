import unittest
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3

from app.database import DATABASE_PATH, get_connection
from app.case_actions import raise_dependency
from tests.test_completion import read_case, event_count


def main():
    target_date = (
        datetime.now(timezone.utc).date() + timedelta(days=5)
    ).isoformat()

    Path("work").mkdir(exist_ok=True)

    with TemporaryDirectory(dir="work") as temporary_folder:
        test_path = Path(temporary_folder) / "dependency_test.db"

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
                    LIMIT 2;
                    """
                )
            ]

        assert len(case_ids) == 2

        for case_id, dependency_type in zip(
            case_ids,
            ["Senior Review", "Other Department"],
        ):
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

            arguments = {
                "case_id": case_id,
                "dependency_type": dependency_type,
                "owner": "Synthetic Review Team",
                "target_date": target_date,
                "details": "Please confirm the next action.",
                "notes": "Investigation remains with DH001.",
                "expected_version": version,
                "database_path": test_path,
            }

            assert not raise_dependency(
                agent_id="DH002", **arguments
            )

            assert not raise_dependency(
                agent_id="DH001",
                **{**arguments, "expected_version": version - 1},
            )

            assert read_case(test_path, case_id) == before
            assert event_count(test_path) == events_before

            assert raise_dependency(
                agent_id="DH001", **arguments
            )

            after = read_case(test_path, case_id)

            expected_changes = {
                "Agent Notes": arguments["notes"],
                "Case Status": "Awaiting Dependency",
                "Dependency Type": dependency_type,
                "Dependency Owner": arguments["owner"],
                "Dependency Target Date": target_date,
                "Dependency Details": arguments["details"],
                "Record Version": version + 1,
            }

            for column, expected in expected_changes.items():
                assert after[column] == expected, column

            assert after["Dependency Raised Date"]
            assert after["Last Updated Date"]
            assert after["Agent Working"] == "DH001"
            assert event_count(test_path) == events_before + 1

            changed_columns = set(expected_changes) | {
                "Dependency Raised Date",
                "Last Updated Date",
            }

            for column in before:
                if column not in changed_columns:
                    assert after[column] == before[column], column

            assert not raise_dependency(
                agent_id="DH001", **arguments
            )

            assert read_case(test_path, case_id) == after
            assert event_count(test_path) == events_before + 1

            print(f"{dependency_type}: passed.")

    print("Assignments and unrelated fields preserved.")
    print("Wrong-agent, stale and repeated attempts blocked.")
    print("Live database unchanged; temporary copy removed.")


class CaseActionTest(unittest.TestCase):
    def test_scenario(self):
        main()


if __name__ == "__main__":
    unittest.main()
