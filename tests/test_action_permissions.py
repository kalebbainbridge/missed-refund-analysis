from contextlib import closing
from datetime import datetime, timedelta, timezone
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from app.database import DATABASE_PATH, get_connection
from app.case_actions import (
    claim_case,
    save_case_notes,
    complete_case,
    release_case,
    raise_dependency,
    resolve_dependency,
)


class ActionPermissionTests(unittest.TestCase):
    def test_disabled_agent_cannot_perform_case_actions(self):
        Path("work").mkdir(exist_ok=True)

        with TemporaryDirectory(dir="work") as temporary_folder:
            test_path = Path(temporary_folder) / "action_permissions.db"

            with closing(sqlite3.connect(
                DATABASE_PATH.resolve().as_uri() + "?mode=ro",
                uri=True,
            )) as original:
                with closing(sqlite3.connect(test_path)) as destination:
                    original.backup(destination)

            target_date = (
                datetime.now(timezone.utc).date() + timedelta(days=5)
            ).isoformat()

            with get_connection(test_path) as connection:
                case_ids = [
                    row[0]
                    for row in connection.execute(
                        """
                        SELECT "Case ID"
                        FROM agent_updates
                        WHERE "Case Status" = 'Open'
                        ORDER BY "Case ID"
                        LIMIT 3;
                        """
                    )
                ]

                self.assertEqual(len(case_ids), 3)
                available_id, assigned_id, dependency_id = case_ids

                for case_id, agent, status in [
                    (available_id, None, "Open"),
                    (assigned_id, "DH001", "Open"),
                    (dependency_id, "DH001", "Awaiting Dependency"),
                ]:
                    connection.execute(
                        """
                        UPDATE agent_updates
                        SET "Agent Working" = ?,
                            "Case Status" = ?,
                            "Record Version" = "Record Version" + 1
                        WHERE "Case ID" = ?;
                        """,
                        (agent, status, case_id),
                    )

                connection.execute(
                    """
                    UPDATE review_agents
                    SET access_enabled = 0
                    WHERE agent_code = 'DH001';
                    """
                )

                versions = dict(connection.execute(
                    """
                    SELECT "Case ID", "Record Version"
                    FROM agent_updates;
                    """
                ).fetchall())

            calls = {
                "claim": partial(
                    claim_case,
                    available_id, "DH001", versions[available_id],
                    database_path=test_path,
                ),
                "save investigation": partial(
                    save_case_notes,
                    assigned_id, "DH001", "Valid notes",
                    versions[assigned_id],
                    database_path=test_path,
                ),
                "complete": partial(
                    complete_case,
                    assigned_id, "DH001", "No Refund Due",
                    "Financial outcome confirmed.",
                    versions[assigned_id],
                    database_path=test_path,
                ),
                "release": partial(
                    release_case,
                    assigned_id, "DH001", versions[assigned_id],
                    database_path=test_path,
                ),
                "raise dependency": partial(
                    raise_dependency,
                    assigned_id, "DH001", "Senior Review",
                    "Synthetic Team", target_date,
                    "Review required.", "Investigation notes.",
                    versions[assigned_id],
                    database_path=test_path,
                ),
                "resolve dependency": partial(
                    resolve_dependency,
                    dependency_id, "DH001", "Review resolved.",
                    versions[dependency_id],
                    database_path=test_path,
                ),
            }

            def snapshot():
                with get_connection(test_path) as connection:
                    return (
                        connection.execute(
                            'SELECT * FROM agent_updates ORDER BY "Case ID";'
                        ).fetchall(),
                        connection.execute(
                            "SELECT * FROM workflow_events ORDER BY Event_ID;"
                        ).fetchall(),
                    )

            before = snapshot()

            for name, action in calls.items():
                with self.subTest(action=name):
                    with self.assertRaisesRegex(
                        PermissionError, "access is disabled"
                    ):
                        action()

                    self.assertEqual(snapshot(), before)


if __name__ == "__main__":
    unittest.main()