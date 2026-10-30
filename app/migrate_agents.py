from app.database import DATABASE_PATH, get_connection


def migrate_agents(database_path=DATABASE_PATH):
    demo_agents = [
        ("DH001", "Demo Agent 1", "Agent", 1),
        ("DH002", "Demo Agent 2", "Agent", 1),
        ("SR001", "Demo Approved Senior", "Approved Senior", 0),
        ("MGR001", "Demo Manager", "Manager", 0),
    ]

    with get_connection(database_path) as connection:
        connection.execute("BEGIN IMMEDIATE;")

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS review_agents (
                agent_code TEXT NOT NULL PRIMARY KEY,
                display_name TEXT NOT NULL,
                application_role TEXT NOT NULL DEFAULT 'Agent'
                    CHECK (application_role IN (
                        'Agent', 'Approved Senior', 'Manager'
                    )),
                training_status TEXT NOT NULL DEFAULT 'In Training'
                    CHECK (training_status IN (
                        'In Training', 'Authorised', 'Inactive'
                    )),
                access_enabled INTEGER NOT NULL DEFAULT 0
                    CHECK (access_enabled IN (0, 1)),
                eligible_for_assignment INTEGER NOT NULL DEFAULT 0
                    CHECK (eligible_for_assignment IN (0, 1))
            );
            """
        )

        connection.executemany(
            """
            INSERT INTO review_agents (
                agent_code,
                display_name,
                application_role,
                training_status,
                access_enabled,
                eligible_for_assignment
            )
            VALUES (?, ?, ?, 'Authorised', 1, ?)
            ON CONFLICT (agent_code) DO NOTHING;
            """,
            demo_agents,
        )

        agents = connection.execute(
            """
            SELECT
                agent_code,
                application_role,
                eligible_for_assignment
            FROM review_agents
            ORDER BY agent_code;
            """
        ).fetchall()

    print("Agent register is ready.")

    for code, role, eligible in agents:
        print(f"{code}: {role}; can receive cases: {bool(eligible)}")


if __name__ == "__main__":
    migrate_agents()