from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from app.database import DATABASE_PATH, get_connection
from app.case_history import load_case_history


class CaseHistoryTests(unittest.TestCase):
    def setUp(self):
        Path("work").mkdir(exist_ok=True)

        temporary = TemporaryDirectory(dir="work")
        self.addCleanup(temporary.cleanup)
        self.database_path = Path(temporary.name) / "history.db"

        with closing(sqlite3.connect(
            DATABASE_PATH.resolve().as_uri() + "?mode=ro",
            uri=True,
        )) as original:
            with closing(
                sqlite3.connect(self.database_path)
            ) as destination:
                original.backup(destination)

        with get_connection(self.database_path) as connection:
            case_ids = [
                row[0]
                for row in connection.execute(
                    """
                    SELECT "Case ID"
                    FROM agent_updates
                    ORDER BY "Case ID"
                    LIMIT 2;
                    """
                )
            ]

            self.case_id, self.other_case_id = case_ids

            for case_id in case_ids:
                connection.execute(
                    """
                    INSERT INTO workflow_events (
                        Case_ID, Event_Type, From_Status,
                        To_Status, Agent_ID, Event_Notes
                    )
                    VALUES (?, 'History Test', 'Open', 'Open',
                            'DH001', 'Synthetic history fixture');
                    """,
                    (case_id,),
                )

        self.prepare_case()

    def prepare_case(
        self,
        status="Open",
        assigned_agent="DH001",
        completed_by=None,
    ):
        with get_connection(self.database_path) as connection:
            connection.execute(
                """
                UPDATE agent_updates
                SET "Case Status" = ?,
                    "Agent Working" = ?,
                    "Completed By" = ?
                WHERE "Case ID" = ?;
                """,
                (
                    status,
                    assigned_agent,
                    completed_by,
                    self.case_id,
                ),
            )

    def assert_expected_history(self, actor):
        history = load_case_history(
            self.case_id,
            actor,
            database_path=self.database_path,
        )

        with get_connection(self.database_path) as connection:
            expected_ids = [
                row[0]
                for row in connection.execute(
                    """
                    SELECT Event_ID
                    FROM workflow_events
                    WHERE Case_ID = ?
                    ORDER BY Event_ID DESC;
                    """,
                    (self.case_id,),
                )
            ]

        self.assertEqual(history["Event ID"].tolist(), expected_ids)
        self.assertTrue(expected_ids)

    def test_management_can_view_any_case(self):
        self.prepare_case(assigned_agent="DH002")

        for actor in ["MGR001", "SR001"]:
            with self.subTest(actor=actor):
                self.assert_expected_history(actor)

    def test_agent_can_view_own_case(self):
        self.assert_expected_history("DH001")

    def test_other_agents_case_is_blocked(self):
        self.prepare_case(assigned_agent="DH002")

        with self.assertRaises(PermissionError):
            load_case_history(
                self.case_id,
                "DH001",
                database_path=self.database_path,
            )

    def test_available_case_can_be_viewed(self):
        self.prepare_case(assigned_agent=None)
        self.assert_expected_history("DH001")

    def test_own_completed_case_can_be_viewed(self):
        self.prepare_case(
            status="Completed",
            assigned_agent="DH002",
            completed_by="DH001",
        )
        self.assert_expected_history("DH001")

    def test_disabled_or_inactive_actors_are_blocked(self):
        for actor in ["DH001", "MGR001", "SR001"]:
            for access, training in [
                (0, "Authorised"),
                (1, "Inactive"),
            ]:
                with self.subTest(actor=actor, training=training):
                    with get_connection(self.database_path) as connection:
                        connection.execute(
                            """
                            UPDATE review_agents
                            SET access_enabled = ?,
                                training_status = ?
                            WHERE agent_code = ?;
                            """,
                            (access, training, actor),
                        )

                    with self.assertRaises(PermissionError):
                        load_case_history(
                            self.case_id,
                            actor,
                            database_path=self.database_path,
                        )

    def test_missing_case_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Case not found"):
            load_case_history(
                "NONEXISTENT-TEST-CASE",
                "MGR001",
                database_path=self.database_path,
            )


if __name__ == "__main__":
    unittest.main()