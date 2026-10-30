import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3

from app.database import DATABASE_PATH, get_connection
from app.case_actions import complete_case
from tests.test_completion import read_case, event_count


def main():
    Path("work").mkdir(exist_ok=True)

    with TemporaryDirectory(dir="work") as temporary_folder:
        test_path = Path(temporary_folder) / "safety_test.db"

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

        for status in [
            "Awaiting Dependency",
            "Awaiting Senior Review",
            "Awaiting Other Department",
        ]:
            with get_connection(test_path) as connection:
                connection.execute(
                    """
                    UPDATE agent_updates
                    SET "Agent Working" = 'DH001',
                        "Case Status" = ?,
                        "Record Version" = "Record Version" + 1
                    WHERE "Case ID" = ?;
                    """,
                    (status, case_id),
                )

            before = read_case(test_path, case_id)
            events_before = event_count(test_path)

            assert not complete_case(
                case_id,
                "DH001",
                "Refund Processed",
                "Attempt while dependency remains",
                before["Record Version"],
                database_path=test_path,
            )

            assert read_case(test_path, case_id) == before
            assert event_count(test_path) == events_before

            print(f"{status}: completion blocked.")

        with get_connection(test_path) as connection:
            connection.execute(
                """
                UPDATE agent_updates
                SET "Case Status" = 'Open',
                    "Record Version" = "Record Version" + 1
                WHERE "Case ID" = ?;
                """,
                (case_id,),
            )

            # This trigger exists only in the disposable database.
            connection.execute(
                """
                CREATE TRIGGER force_test_audit_failure
                BEFORE INSERT ON workflow_events
                BEGIN
                    SELECT RAISE(ABORT, 'Intentional audit failure');
                END;
                """
            )

        before = read_case(test_path, case_id)
        events_before = event_count(test_path)

        try:
            complete_case(
                case_id,
                "DH001",
                "Refund Processed",
                "This completion must roll back",
                before["Record Version"],
                database_path=test_path,
            )
        except sqlite3.IntegrityError as exc:
            assert "Intentional audit failure" in str(exc)
        else:
            raise AssertionError("The audit failure did not occur.")

        assert read_case(test_path, case_id) == before
        assert event_count(test_path) == events_before

        print("Audit failure: completion and version rolled back.")

    print("Live database unchanged; temporary copy removed.")


class CaseActionTest(unittest.TestCase):
    def test_scenario(self):
        main()


if __name__ == "__main__":
    unittest.main()