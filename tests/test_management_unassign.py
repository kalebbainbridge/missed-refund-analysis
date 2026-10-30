from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from app.database import DATABASE_PATH, get_connection
from app.case_actions import unassign_case
from tests.test_completion import read_case, event_count


class ManagementUnassignTests(unittest.TestCase):
    def setUp(self):
        Path("work").mkdir(exist_ok=True)

        temporary = TemporaryDirectory(dir="work")
        self.addCleanup(temporary.cleanup)

        self.database_path = Path(temporary.name) / "unassign.db"

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
                WHERE "Case Status" = 'Open'
                ORDER BY "Case ID"
                LIMIT 1;
                """
            ).fetchone()[0]

    def prepare_case(self, status="Open", assigned_agent="DH001"):
        with get_connection(self.database_path) as connection:
            connection.execute(
                """
                UPDATE agent_updates
                SET "Agent Working" = ?,
                    "Case Status" = ?,
                    "Agent Notes" = 'Preserve these notes.',
                    "Investigation Reason" = 'Refund Action Missed',
                    "Record Version" = "Record Version" + 1
                WHERE "Case ID" = ?;
                """,
                (assigned_agent, status, self.case_id),
            )

        return read_case(self.database_path, self.case_id)

    def test_manager_and_senior_can_unassign(self):
        for actor in ["MGR001", "SR001"]:
            for status in [
                "Open",
                "Awaiting Dependency",
                "Awaiting Senior Review",
                "Awaiting Other Department",
            ]:
                with self.subTest(actor=actor, status=status):
                    before = self.prepare_case(status)
                    events_before = event_count(self.database_path)

                    self.assertTrue(unassign_case(
                        self.case_id,
                        actor,
                        before["Record Version"],
                        database_path=self.database_path,
                    ))

                    after = read_case(self.database_path, self.case_id)

                    self.assertIsNone(after["Agent Working"])
                    self.assertEqual(
                        after["Record Version"],
                        before["Record Version"] + 1,
                    )

                    for column in before:
                        if column not in {
                            "Agent Working",
                            "Record Version",
                            "Last Updated Date",
                        }:
                            self.assertEqual(
                                after[column], before[column], column
                            )

                    self.assertEqual(
                        event_count(self.database_path),
                        events_before + 1,
                    )

                    with get_connection(self.database_path) as connection:
                        event = connection.execute(
                            """
                            SELECT Agent_ID, Event_Notes
                            FROM workflow_events
                            WHERE Case_ID = ?
                            ORDER BY Event_ID DESC
                            LIMIT 1;
                            """,
                            (self.case_id,),
                        ).fetchone()

                    self.assertEqual(event[0], actor)
                    self.assertIn("Previous agent: DH001", event[1])

    def test_agent_cannot_unassign_through_management_action(self):
        before = self.prepare_case()
        events_before = event_count(self.database_path)

        with self.assertRaises(PermissionError):
            unassign_case(
                self.case_id,
                "DH001",
                before["Record Version"],
                database_path=self.database_path,
            )

        self.assertEqual(
            read_case(self.database_path, self.case_id), before
        )
        self.assertEqual(
            event_count(self.database_path), events_before
        )

    def test_stale_completed_and_unassigned_cases_are_blocked(self):
        for status, assigned_agent, stale in [
            ("Open", "DH001", True),
            ("Completed", "DH001", False),
            ("Open", None, False),
        ]:
            with self.subTest(status=status, stale=stale):
                before = self.prepare_case(status, assigned_agent)
                events_before = event_count(self.database_path)

                version = before["Record Version"] - int(stale)

                self.assertFalse(unassign_case(
                    self.case_id,
                    "MGR001",
                    version,
                    database_path=self.database_path,
                ))

                self.assertEqual(
                    read_case(self.database_path, self.case_id), before
                )
                self.assertEqual(
                    event_count(self.database_path), events_before
                )


if __name__ == "__main__":
    unittest.main()