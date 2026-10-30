from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from app.database import DATABASE_PATH, get_connection
from app.case_actions import reassign_case
from tests.test_completion import read_case, event_count


class ManagementReassignTests(unittest.TestCase):
    def setUp(self):
        Path("work").mkdir(exist_ok=True)

        temporary = TemporaryDirectory(dir="work")
        self.addCleanup(temporary.cleanup)
        self.database_path = Path(temporary.name) / "reassign.db"

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
                    "Agent Notes" = 'Keep the investigation notes.',
                    "Investigation Reason" = 'Refund Action Missed',
                    "Record Version" = "Record Version" + 1
                WHERE "Case ID" = ?;
                """,
                (assigned_agent, status, self.case_id),
            )

            if status == "Awaiting Dependency":
                connection.execute(
                    """
                    UPDATE agent_updates
                    SET "Dependency Type" = 'Senior Review',
                        "Dependency Owner" = 'Synthetic Senior Team',
                        "Dependency Details" = 'Review still outstanding.'
                    WHERE "Case ID" = ?;
                    """,
                    (self.case_id,),
                )

        return read_case(self.database_path, self.case_id)

    def test_both_roles_can_reassign_without_losing_case_details(self):
        for actor in ["MGR001", "SR001"]:
            for status in ["Open", "Awaiting Dependency"]:
                for previous_agent in ["DH001", None]:
                    with self.subTest(
                        actor=actor,
                        status=status,
                        previous_agent=previous_agent,
                    ):
                        before = self.prepare_case(status, previous_agent)
                        events_before = event_count(self.database_path)

                        self.assertTrue(reassign_case(
                            self.case_id,
                            actor,
                            "DH002",
                            before["Record Version"],
                            database_path=self.database_path,
                        ))

                        after = read_case(self.database_path, self.case_id)

                        self.assertEqual(after["Agent Working"], "DH002")
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

    def test_ordinary_agent_cannot_reassign(self):
        before = self.prepare_case()
        events_before = event_count(self.database_path)

        with self.assertRaises(PermissionError):
            reassign_case(
                self.case_id, "DH001", "DH002",
                before["Record Version"],
                database_path=self.database_path,
            )

        self.assertEqual(
            read_case(self.database_path, self.case_id), before
        )
        self.assertEqual(event_count(self.database_path), events_before)

    def test_unavailable_target_is_blocked(self):
        before = self.prepare_case()
        events_before = event_count(self.database_path)

        for access, training, eligible in [
            (0, "Authorised", 1),
            (1, "In Training", 1),
            (1, "Inactive", 1),
            (1, "Authorised", 0),
        ]:
            with self.subTest(
                access=access, training=training, eligible=eligible
            ):
                with get_connection(self.database_path) as connection:
                    connection.execute(
                        """
                        UPDATE review_agents
                        SET access_enabled = ?,
                            training_status = ?,
                            eligible_for_assignment = ?
                        WHERE agent_code = 'DH002';
                        """,
                        (access, training, eligible),
                    )

                with self.assertRaises(PermissionError):
                    reassign_case(
                        self.case_id, "MGR001", "DH002",
                        before["Record Version"],
                        database_path=self.database_path,
                    )

                self.assertEqual(
                    read_case(self.database_path, self.case_id), before
                )
                self.assertEqual(
                    event_count(self.database_path), events_before
                )

    def test_stale_completed_and_same_assignment_are_blocked(self):
        for status, target, stale in [
            ("Open", "DH002", True),
            ("Completed", "DH002", False),
            ("Open", "DH001", False),
        ]:
            with self.subTest(status=status, target=target, stale=stale):
                before = self.prepare_case(status)
                events_before = event_count(self.database_path)

                self.assertFalse(reassign_case(
                    self.case_id,
                    "MGR001",
                    target,
                    before["Record Version"] - int(stale),
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