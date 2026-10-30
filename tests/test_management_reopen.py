from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from app.database import DATABASE_PATH, get_connection
from app.case_actions import reopen_case
from tests.test_completion import read_case, event_count


class ManagementReopenTests(unittest.TestCase):
    def setUp(self):
        Path("work").mkdir(exist_ok=True)

        temporary = TemporaryDirectory(dir="work")
        self.addCleanup(temporary.cleanup)
        self.database_path = Path(temporary.name) / "reopen.db"

        with closing(sqlite3.connect(
            DATABASE_PATH.resolve().as_uri() + "?mode=ro",
            uri=True,
        )) as original:
            with closing(
                sqlite3.connect(self.database_path)
            ) as destination:
                original.backup(destination)

        with get_connection(self.database_path) as connection:
            self.case_id = connection.execute(
                """
                SELECT "Case ID"
                FROM agent_updates
                WHERE "Case Status" = 'Completed'
                ORDER BY "Case ID"
                LIMIT 1;
                """
            ).fetchone()[0]

    def prepare_completed_case(self):
        with get_connection(self.database_path) as connection:
            connection.execute(
                """
                UPDATE agent_updates
                SET "Case Status" = 'Completed',
                    "Agent Working" = 'DH001',
                    "Agent Notes" = 'Keep these investigation notes.',
                    "Investigation Reason" = 'Refund Action Missed',
                    "Final Outcome" = 'Refund Processed',
                    "Completed By" = 'DH001',
                    "Completion Date" = '2026-07-15',
                    "Record Version" = "Record Version" + 1
                WHERE "Case ID" = ?;
                """,
                (self.case_id,),
            )

        return read_case(self.database_path, self.case_id)

    def test_both_roles_preserve_details_and_history(self):
        for actor in ["MGR001", "SR001"]:
            with self.subTest(actor=actor):
                before = self.prepare_completed_case()
                events_before = event_count(self.database_path)

                self.assertTrue(reopen_case(
                    self.case_id, actor, "Further investigation needed.",
                    before["Record Version"],
                    database_path=self.database_path,
                ))

                after = read_case(self.database_path, self.case_id)

                expected = {
                    **before,
                    "Case Status": "Open",
                    "Final Outcome": None,
                    "Completed By": None,
                    "Completion Date": None,
                    "Record Version": before["Record Version"] + 1,
                    "Last Updated Date": after["Last Updated Date"],
                }

                self.assertEqual(after, expected)
                self.assertTrue(after["Last Updated Date"])
                self.assertEqual(
                    event_count(self.database_path), events_before + 1
                )

                with get_connection(self.database_path) as connection:
                    event = connection.execute(
                        """
                        SELECT Event_Type, From_Status, To_Status,
                               Agent_ID, Event_Notes
                        FROM workflow_events
                        WHERE Case_ID = ?
                        ORDER BY Event_ID DESC
                        LIMIT 1;
                        """,
                        (self.case_id,),
                    ).fetchone()

                self.assertEqual(
                    event[:4],
                    ("Case Reopened", "Completed", "Open", actor),
                )

                for text in [
                    "Further investigation needed.",
                    "Refund Processed",
                    "DH001",
                    "2026-07-15",
                ]:
                    self.assertIn(text, event[4])

    def test_reason_is_required(self):
        before = self.prepare_completed_case()
        events_before = event_count(self.database_path)

        for reason in ["", " ", None]:
            with self.subTest(reason=reason):
                with self.assertRaises(ValueError):
                    reopen_case(
                        self.case_id, "MGR001", reason,
                        before["Record Version"],
                        database_path=self.database_path,
                    )

                self.assertEqual(
                    read_case(self.database_path, self.case_id), before
                )
                self.assertEqual(
                    event_count(self.database_path), events_before
                )

    def test_agent_and_disabled_management_are_blocked(self):
        before = self.prepare_completed_case()
        events_before = event_count(self.database_path)

        with get_connection(self.database_path) as connection:
            connection.execute(
                """
                UPDATE review_agents
                SET access_enabled = 0
                WHERE agent_code IN ('MGR001', 'SR001');
                """
            )

        for actor in ["DH001", "MGR001", "SR001"]:
            with self.subTest(actor=actor):
                with self.assertRaises(PermissionError):
                    reopen_case(
                        self.case_id, actor, "Review requested.",
                        before["Record Version"],
                        database_path=self.database_path,
                    )

                self.assertEqual(
                    read_case(self.database_path, self.case_id), before
                )
                self.assertEqual(
                    event_count(self.database_path), events_before
                )

    def test_stale_and_repeated_reopening_are_blocked(self):
        before = self.prepare_completed_case()
        events_before = event_count(self.database_path)

        self.assertFalse(reopen_case(
            self.case_id, "MGR001", "Stale attempt.",
            before["Record Version"] - 1,
            database_path=self.database_path,
        ))

        self.assertEqual(
            read_case(self.database_path, self.case_id), before
        )
        self.assertEqual(event_count(self.database_path), events_before)

        self.assertTrue(reopen_case(
            self.case_id, "MGR001", "Review requested.",
            before["Record Version"],
            database_path=self.database_path,
        ))

        after = read_case(self.database_path, self.case_id)

        self.assertFalse(reopen_case(
            self.case_id, "MGR001", "Repeated attempt.",
            after["Record Version"],
            database_path=self.database_path,
        ))

        self.assertEqual(
            read_case(self.database_path, self.case_id), after
        )
        self.assertEqual(
            event_count(self.database_path), events_before + 1
        )

    def test_audit_failure_rolls_back_reopening(self):
        before = self.prepare_completed_case()
        events_before = event_count(self.database_path)

        with get_connection(self.database_path) as connection:
            connection.execute(
                """
                CREATE TRIGGER force_reopen_audit_failure
                BEFORE INSERT ON workflow_events
                BEGIN
                    SELECT RAISE(ABORT, 'Intentional audit failure');
                END;
                """
            )

        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "Intentional audit failure"
        ):
            reopen_case(
                self.case_id, "MGR001", "Review requested.",
                before["Record Version"],
                database_path=self.database_path,
            )

        self.assertEqual(
            read_case(self.database_path, self.case_id), before
        )
        self.assertEqual(event_count(self.database_path), events_before)


if __name__ == "__main__":
    unittest.main()