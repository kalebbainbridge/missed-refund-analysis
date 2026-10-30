from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from app.database import DATABASE_PATH, get_connection
from app.migrate_no_refund_reason import migrate_no_refund_reason


class ReasonMigrationTests(unittest.TestCase):
    def test_migration_preserves_data_and_is_repeatable(self):
        Path("work").mkdir(exist_ok=True)

        with TemporaryDirectory(dir="work") as temporary_folder:
            test_path = Path(temporary_folder) / "reason_migration.db"

            with closing(sqlite3.connect(
                DATABASE_PATH.resolve().as_uri() + "?mode=ro",
                uri=True,
            )) as original:
                with closing(sqlite3.connect(test_path)) as destination:
                    original.backup(destination)

            def snapshot():
                with get_connection(test_path) as connection:
                    return {
                        "cases": connection.execute(
                            'SELECT * FROM agent_updates ORDER BY "Case ID";'
                        ).fetchall(),
                        "events": connection.execute(
                            "SELECT * FROM workflow_events ORDER BY Event_ID;"
                        ).fetchall(),
                        "report": connection.execute(
                            """
                            SELECT * FROM operational_case_view
                            ORDER BY "Case ID";
                            """
                        ).fetchall(),
                        "other_schema": connection.execute(
                            """
                            SELECT type, name, tbl_name, sql
                            FROM sqlite_master
                            WHERE name <> 'agent_updates'
                              AND name NOT LIKE 'sqlite_%'
                            ORDER BY type, name;
                            """
                        ).fetchall(),
                    }

            before = snapshot()

            migrate_no_refund_reason(test_path)

            self.assertEqual(snapshot(), before)

            with get_connection(test_path) as connection:
                case_id = connection.execute(
                    """
                    SELECT "Case ID"
                    FROM agent_updates
                    ORDER BY "Case ID"
                    LIMIT 1;
                    """
                ).fetchone()[0]

                # Probe the new value, then undo the probe.
                connection.execute("SAVEPOINT reason_probe;")

                connection.execute(
                    """
                    UPDATE agent_updates
                    SET "Investigation Reason" = 'No Refund Due'
                    WHERE "Case ID" = ?;
                    """,
                    (case_id,),
                )

                saved_reason = connection.execute(
                    """
                    SELECT "Investigation Reason"
                    FROM agent_updates
                    WHERE "Case ID" = ?;
                    """,
                    (case_id,),
                ).fetchone()[0]

                self.assertEqual(saved_reason, "No Refund Due")

                connection.execute("ROLLBACK TO reason_probe;")
                connection.execute("RELEASE reason_probe;")

            with self.assertRaises(sqlite3.IntegrityError):
                with get_connection(test_path) as connection:
                    connection.execute(
                        """
                        UPDATE agent_updates
                        SET "Investigation Reason" = 'Invalid Reason'
                        WHERE "Case ID" = ?;
                        """,
                        (case_id,),
                    )

            self.assertEqual(snapshot(), before)

            with get_connection(test_path) as connection:
                schema_after_first_run = connection.execute(
                    """
                    SELECT sql FROM sqlite_master
                    WHERE type = 'table' AND name = 'agent_updates';
                    """
                ).fetchone()[0]

            migrate_no_refund_reason(test_path)

            with get_connection(test_path) as connection:
                schema_after_second_run = connection.execute(
                    """
                    SELECT sql FROM sqlite_master
                    WHERE type = 'table' AND name = 'agent_updates';
                    """
                ).fetchone()[0]

            self.assertEqual(
                schema_after_second_run, schema_after_first_run
            )
            self.assertEqual(snapshot(), before)


if __name__ == "__main__":
    unittest.main()