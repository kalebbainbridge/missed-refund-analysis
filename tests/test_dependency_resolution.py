import unittest
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3

from app.database import DATABASE_PATH, get_connection
from app.case_actions import raise_dependency, resolve_dependency
from tests.test_completion import read_case, event_count


def main():
    target_date = (
        datetime.now(timezone.utc).date() + timedelta(days=5)
    ).isoformat()

    Path("work").mkdir(exist_ok=True)

    with TemporaryDirectory(dir="work") as temporary_folder:
        test_path = Path(temporary_folder) / "resolution_test.db"

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

        original = read_case(test_path, case_id)

        assert raise_dependency(
            case_id,
            "DH001",
            "Senior Review",
            "Synthetic Senior Team",
            target_date,
            "Confirm whether a refund is due.",
            "Keep these investigation notes.",
            original["Record Version"],
            database_path=test_path,
        )

        before = read_case(test_path, case_id)
        version = before["Record Version"]
        events_before = event_count(test_path)

        assert not resolve_dependency(
            case_id, "DH002", "Reviewed",
            version, database_path=test_path,
        )

        assert not resolve_dependency(
            case_id, "DH001", "Stale resolution",
            version - 1, database_path=test_path,
        )

        try:
            resolve_dependency(
                case_id, "DH001", " ",
                version, database_path=test_path,
            )
        except ValueError as exc:
            assert "resolution note" in str(exc)
        else:
            raise AssertionError("Blank resolution note was accepted.")

        assert read_case(test_path, case_id) == before
        assert event_count(test_path) == events_before

        assert resolve_dependency(
            case_id,
            "DH001",
            "Senior confirmed the next action.",
            version,
            database_path=test_path,
        )

        after = read_case(test_path, case_id)

        cleared_fields = {
            "Dependency Type",
            "Dependency Owner",
            "Dependency Raised Date",
            "Dependency Target Date",
            "Dependency Details",
        }

        assert after["Case Status"] == "Open"
        assert after["Record Version"] == version + 1
        assert after["Last Updated Date"]

        for column in cleared_fields:
            assert after[column] is None, column

        changed_fields = cleared_fields | {
            "Case Status",
            "Record Version",
            "Last Updated Date",
        }

        for column in before:
            if column not in changed_fields:
                assert after[column] == before[column], column

        with get_connection(test_path) as connection:
            event_type, from_status, to_status, event_notes = (
                connection.execute(
                    """
                    SELECT Event_Type, From_Status, To_Status, Event_Notes
                    FROM workflow_events
                    WHERE Case_ID = ?
                    ORDER BY Event_ID DESC
                    LIMIT 1;
                    """,
                    (case_id,),
                ).fetchone()
            )

        assert event_type == "Dependency Resolved"
        assert from_status == "Awaiting Dependency"
        assert to_status == "Open"

        for expected_text in [
            "Senior confirmed the next action.",
            "Senior Review",
            "Synthetic Senior Team",
            target_date,
            "Confirm whether a refund is due.",
        ]:
            assert expected_text in event_notes

        assert not resolve_dependency(
            case_id, "DH001", "Repeated resolution",
            version + 1, database_path=test_path,
        )

        assert read_case(test_path, case_id) == after
        assert event_count(test_path) == events_before + 1

    print("Raise and resolve journey: passed.")
    print("Assignment and investigation notes preserved.")
    print("Previous dependency details retained in history.")
    print("Wrong-agent, stale, blank and repeated attempts blocked.")
    print("Live database unchanged; temporary copy removed.")


class CaseActionTest(unittest.TestCase):
    def test_scenario(self):
        main()


if __name__ == "__main__":
    unittest.main()