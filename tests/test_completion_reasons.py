import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3

from app.database import DATABASE_PATH, get_connection
from app.case_actions import complete_case
from tests.test_completion import read_case, event_count


def main():
    scenarios = [
        ("Not Yet Determined", "", False),
        ("Not Yet Determined", "Financial outcome confirmed; cause unknown.", True),
        ("Other", "", False),
        ("Other", "Unusual cause explained here.", True),
        ("Refund Action Missed", "", True),
    ]

    Path("work").mkdir(exist_ok=True)

    with TemporaryDirectory(dir="work") as temporary_folder:
        test_path = Path(temporary_folder) / "completion_reasons.db"

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
                    LIMIT 5;
                    """
                )
            ]

        assert len(case_ids) == len(scenarios)

        for case_id, (reason, notes, should_complete) in zip(
            case_ids, scenarios
        ):
            with get_connection(test_path) as connection:
                connection.execute(
                    """
                    UPDATE agent_updates
                    SET "Agent Working" = 'DH001',
                        "Investigation Reason" = ?,
                        "Record Version" = "Record Version" + 1
                    WHERE "Case ID" = ?;
                    """,
                    (reason, case_id),
                )

            before = read_case(test_path, case_id)
            events_before = event_count(test_path)

            try:
                result = complete_case(
                    case_id,
                    "DH001",
                    "No Refund Due",
                    notes,
                    before["Record Version"],
                    database_path=test_path,
                )
            except ValueError as exc:
                if should_complete:
                    raise
                assert "Explain" in str(exc)
                assert read_case(test_path, case_id) == before
                assert event_count(test_path) == events_before
            else:
                assert should_complete, "Missing explanation was accepted."
                assert result

                after = read_case(test_path, case_id)
                assert after["Case Status"] == "Completed"
                assert after["Investigation Reason"] == reason
                assert after["Agent Notes"] == notes
                assert after["Record Version"] == before["Record Version"] + 1
                assert event_count(test_path) == events_before + 1

            expected = "completed" if should_complete else "blocked"
            print(f"{reason}, notes={bool(notes)}: {expected}.")

    print("Live database unchanged; temporary copy removed.")


class CaseActionTest(unittest.TestCase):
    def test_scenario(self):
        main()


if __name__ == "__main__":
    unittest.main()