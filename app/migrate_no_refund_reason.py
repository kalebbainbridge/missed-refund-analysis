import re

from app.database import DATABASE_PATH, get_connection


def quote_name(name):
    return '"' + name.replace('"', '""') + '"'


def migrate_no_refund_reason(database_path=DATABASE_PATH):
    with get_connection(database_path) as connection:
        connection.execute("BEGIN IMMEDIATE;")

        original_sql = connection.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table' AND name = 'agent_updates';
            """
        ).fetchone()[0]

        pattern = re.compile(
            r'CHECK\s*\(\s*"Investigation Reason"\s+IN\s*\((.*?)\)\s*\)',
            re.DOTALL,
        )

        match = pattern.search(original_sql)

        if match is None:
            raise ValueError("Investigation-reason constraint not found.")

        if "'No Refund Due'" in match.group(1):
            print("No Refund Due is already permitted. No changes made.")
            return

        expanded_constraint = (
            'CHECK ("Investigation Reason" IN ('
            + match.group(1).rstrip()
            + ", 'No Refund Due'))"
        )

        updated_sql = (
            original_sql[:match.start()]
            + expanded_constraint
            + original_sql[match.end():]
        )

        temporary_table = "agent_updates_reason_upgrade"

        if connection.execute(
            "SELECT 1 FROM sqlite_master WHERE name = ?;",
            (temporary_table,),
        ).fetchone():
            raise ValueError("An upgrade table already exists.")

        # Stop if another table depends on this table through a foreign key.
        table_names = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table';"
        ).fetchall()

        for (table_name,) in table_names:
            foreign_keys = connection.execute(
                f"PRAGMA foreign_key_list({quote_name(table_name)});"
            ).fetchall()

            if any(row[2] == "agent_updates" for row in foreign_keys):
                raise ValueError(
                    "Dependent foreign keys require a separate migration."
                )

        before_records = connection.execute(
            'SELECT * FROM agent_updates ORDER BY "Case ID";'
        ).fetchall()

        before_events = connection.execute(
            "SELECT * FROM workflow_events ORDER BY Event_ID;"
        ).fetchall()

        views = connection.execute(
            """
            SELECT name, sql
            FROM sqlite_master
            WHERE type = 'view'
            ORDER BY rowid;
            """
        ).fetchall()

        view_counts = {
            name: connection.execute(
                f"SELECT COUNT(*) FROM {quote_name(name)};"
            ).fetchone()[0]
            for name, _ in views
        }

        dependent_objects = connection.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE tbl_name = 'agent_updates'
              AND type IN ('index', 'trigger')
              AND sql IS NOT NULL;
            """
        ).fetchall()

        for name, _ in views:
            connection.execute(f"DROP VIEW {quote_name(name)};")

        create_sql = (
            f"CREATE TABLE {quote_name(temporary_table)} "
            + updated_sql[updated_sql.index("("):]
        )

        connection.execute(create_sql)

        connection.execute(
            f"""
            INSERT INTO {quote_name(temporary_table)}
            SELECT * FROM agent_updates;
            """
        )

        connection.execute("DROP TABLE agent_updates;")

        connection.execute(
            f"""
            ALTER TABLE {quote_name(temporary_table)}
            RENAME TO agent_updates;
            """
        )

        for (sql,) in dependent_objects:
            connection.execute(sql)

        for _, sql in views:
            connection.execute(sql)

        after_records = connection.execute(
            'SELECT * FROM agent_updates ORDER BY "Case ID";'
        ).fetchall()

        after_events = connection.execute(
            "SELECT * FROM workflow_events ORDER BY Event_ID;"
        ).fetchall()

        if before_records != after_records:
            raise ValueError("Operational records changed unexpectedly.")

        if before_events != after_events:
            raise ValueError("Workflow history changed unexpectedly.")

        for name, expected_count in view_counts.items():
            actual_count = connection.execute(
                f"SELECT COUNT(*) FROM {quote_name(name)};"
            ).fetchone()[0]

            if actual_count != expected_count:
                raise ValueError(f"Reporting view changed: {name}")

        integrity = connection.execute(
            "PRAGMA integrity_check;"
        ).fetchone()[0]

        if integrity != "ok":
            raise ValueError(f"Database integrity failed: {integrity}")

    print("No Refund Due added to permitted investigation reasons.")
    print("Operational records and workflow history preserved.")
    print("Reporting views restored; database integrity: ok.")