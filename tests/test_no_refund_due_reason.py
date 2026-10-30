from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from app.database import DATABASE_PATH, get_connection
from app.case_actions import complete_case, save_case_notes
from app.migrate_no_refund_reason import migrate_no_refund_reason
from tests.test_completion import read_case, event_count


class NoRefundDueReasonTests(unittest.TestCase):
    def setUp(self):
        Path("work").mkdir(exist_ok=True)

        temporary = TemporaryDirectory(dir="work")
        self.addCleanup(temporary.cleanup)
        self.database_path = Path(temporary.name) / "no_refund_due.db"

        with closing(sqlite3.connect(
            DATABASE_PATH.resolve().as_uri() + "?mode=ro",
            uri=True,
        )) as original:
            with closing(
                sqlite3.connect(self.database_path)
            ) as destination:
                original.backup(destination)

        migrate_no_refund_reason(self.database_path)

        with get_connection(self.database_path) as connection:
            self.case_id = connection.execute(
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
                (self.case_id,),
            )

        self.before = read_case(self.database_path, self.case_id)
        self.events_before = event_count(self.database_path)

    def assert_unchanged(self):
        self.assertEqual(
            read_case(self.database_path, self.case_id),
            self.before,
        )
        self.assertEqual(
            event_count(self.database_path),
            self.events_before,
        )

    def test_matching_outcome_allows_no_refund_due_reason(self):
        self.assertTrue(complete_case(
            self.case_id,
            "DH001",
            "No Refund Due",
            "",
            self.before["Record Version"],
            database_path=self.database_path,
            investigation_reason="No Refund Due",
        ))

        after = read_case(self.database_path, self.case_id)

        self.assertEqual(after["Case Status"], "Completed")
        self.assertEqual(after["Final Outcome"], "No Refund Due")
        self.assertEqual(after["Investigation Reason"], "No Refund Due")
        self.assertEqual(after["Completed By"], "DH001")
        self.assertEqual(
            after["Record Version"],
            self.before["Record Version"] + 1,
        )
        self.assertEqual(
            event_count(self.database_path),
            self.events_before + 1,
        )

    def test_other_outcomes_reject_no_refund_due_reason(self):
        for outcome in ["Refund Processed", "Refund Already Processed"]:
            with self.subTest(outcome=outcome):
                with self.assertRaisesRegex(ValueError, "only"):
                    complete_case(
                        self.case_id,
                        "DH001",
                        outcome,
                        "An explanation cannot bypass the outcome rule.",
                        self.before["Record Version"],
                        database_path=self.database_path,
                        investigation_reason="No Refund Due",
                    )

                self.assert_unchanged()

    def test_reason_cannot_be_saved_without_completion(self):
        with self.assertRaisesRegex(ValueError, "only"):
            save_case_notes(
                self.case_id,
                "DH001",
                "Investigation notes.",
                self.before["Record Version"],
                database_path=self.database_path,
                investigation_reason="No Refund Due",
            )

        self.assert_unchanged()

    def test_genuine_reason_remains_allowed_with_no_refund_due(self):
        self.assertTrue(complete_case(
            self.case_id,
            "DH001",
            "No Refund Due",
            "Investigation established the cause and no refund is due.",
            self.before["Record Version"],
            database_path=self.database_path,
            investigation_reason="Refund Action Missed",
        ))

        after = read_case(self.database_path, self.case_id)

        self.assertEqual(after["Final Outcome"], "No Refund Due")
        self.assertEqual(
            after["Investigation Reason"], "Refund Action Missed"
        )


if __name__ == "__main__":
    unittest.main()