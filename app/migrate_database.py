from app.database import get_connection


def migrate_database():
    additions = {
        "Record Version": """
            INTEGER NOT NULL DEFAULT 0
            CHECK ("Record Version" >= 0)
        """,
        "Investigation Reason": """
            TEXT NOT NULL DEFAULT 'Not Yet Determined'
            CHECK ("Investigation Reason" IN (
                'Not Yet Determined',
                'Payment Date Misunderstood',
                'Refund Action Missed',
                'Waiting for Information',
                'Refund Mailbox Delay',
                'Other'
            ))
        """,
        "Dependency Type": """
            TEXT CHECK (
                "Dependency Type" IS NULL
                OR "Dependency Type" IN (
                    'Senior Review',
                    'Other Department'
                )
            )
        """,
        "Dependency Owner": "TEXT",
        "Dependency Raised Date": "TEXT",
        "Dependency Target Date": "TEXT",
        "Dependency Details": "TEXT",
    }

    added_columns = []

    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE;")

        original_columns = [
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(agent_updates);"
            )
        ]

        column_sql = ", ".join(
            '"' + column.replace('"', '""') + '"'
            for column in original_columns
        )

        comparison_query = (
            f"SELECT {column_sql} "
            'FROM agent_updates ORDER BY "Case ID";'
        )

        before_records = connection.execute(
            comparison_query
        ).fetchall()

        for column, definition in additions.items():
            if column not in original_columns:
                connection.execute(
                    f'ALTER TABLE agent_updates '
                    f'ADD COLUMN "{column}" {definition};'
                )
                added_columns.append(column)

        invalid_versions = connection.execute(
            """
            SELECT COUNT(*)
            FROM agent_updates
            WHERE "Record Version" IS NULL
               OR typeof("Record Version") <> 'integer'
               OR "Record Version" < 0;
            """
        ).fetchone()[0]

        if invalid_versions:
            raise ValueError("Invalid record versions detected.")

        after_records = connection.execute(
            comparison_query
        ).fetchall()

        if before_records != after_records:
            raise ValueError(
                "Existing operational values changed during migration."
            )

    print("Added fields:", added_columns)
    print("Operational records:", len(after_records))
    print("All pre-existing operational values are unchanged.")


if __name__ == "__main__":
    migrate_database()