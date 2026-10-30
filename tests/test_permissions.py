from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from app.database import DATABASE_PATH, get_connection
from app.permissions import (
    get_active_agent,
    require_case_worker,
    require_management,
)


class PermissionTests(unittest.TestCase):
    def setUp(self):
        Path("work").mkdir(exist_ok=True)

        temporary = TemporaryDirectory(dir="work")
        self.addCleanup(temporary.cleanup)

        self.database_path = Path(temporary.name) / "permissions.db"

        with closing(sqlite3.connect(
            DATABASE_PATH.resolve().as_uri() + "?mode=ro",
            uri=True,
        )) as original:
            with closing(
                sqlite3.connect(self.database_path)
            ) as destination:
                original.backup(destination)

    def check(self, function, agent_id):
        with get_connection(self.database_path) as connection:
            return function(connection, agent_id)

    def test_role_boundaries(self):
        for agent_id in ["DH001", "DH002"]:
            self.check(require_case_worker, agent_id)

            with self.assertRaises(PermissionError):
                self.check(require_management, agent_id)

        for agent_id in ["SR001", "MGR001"]:
            self.check(require_management, agent_id)

            with self.assertRaises(PermissionError):
                self.check(require_case_worker, agent_id)

    def test_disabled_access_blocks_every_role(self):
        with get_connection(self.database_path) as connection:
            connection.execute(
                "UPDATE review_agents SET access_enabled = 0;"
            )

        for agent_id in ["DH001", "DH002", "SR001", "MGR001"]:
            for function in [
                get_active_agent,
                require_case_worker,
                require_management,
            ]:
                with self.subTest(agent=agent_id, check=function.__name__):
                    with self.assertRaises(PermissionError):
                        self.check(function, agent_id)

    def test_inactive_status_blocks_every_role(self):
        with get_connection(self.database_path) as connection:
            connection.execute(
                """
                UPDATE review_agents
                SET training_status = 'Inactive';
                """
            )

        for agent_id in ["DH001", "DH002", "SR001", "MGR001"]:
            for function in [
                get_active_agent,
                require_case_worker,
                require_management,
            ]:
                with self.subTest(agent=agent_id, check=function.__name__):
                    with self.assertRaises(PermissionError):
                        self.check(function, agent_id)

    def test_eligible_management_can_also_work_cases(self):
        with get_connection(self.database_path) as connection:
            connection.execute(
                """
                UPDATE review_agents
                SET eligible_for_assignment = 1
                WHERE agent_code IN ('SR001', 'MGR001');
                """
            )

        for agent_id in ["SR001", "MGR001"]:
            self.check(require_management, agent_id)
            self.check(require_case_worker, agent_id)

    def test_training_required_for_case_work(self):
        with get_connection(self.database_path) as connection:
            connection.execute(
                """
                UPDATE review_agents
                SET training_status = 'In Training'
                WHERE agent_code = 'DH001';
                """
            )

        self.check(get_active_agent, "DH001")

        with self.assertRaises(PermissionError):
            self.check(require_case_worker, "DH001")

    def test_unknown_or_missing_identity_is_blocked(self):
        for agent_id in ["UNKNOWN", "", None]:
            for function in [
                get_active_agent,
                require_case_worker,
                require_management,
            ]:
                with self.subTest(agent=agent_id, check=function.__name__):
                    with self.assertRaises(PermissionError):
                        self.check(function, agent_id)


if __name__ == "__main__":
    unittest.main()