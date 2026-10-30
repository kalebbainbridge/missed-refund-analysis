import pandas as pd

from app.database import DATABASE_PATH, get_connection
from app.permissions import require_case_worker, require_management

def load_agent_queue(
    agent_id,
    queue_name,
    database_path=DATABASE_PATH,
):
    queue_filters = {
        "available": (
            """
            work."Case Status" = 'Open'
            AND (
                work."Agent Working" IS NULL
                OR TRIM(work."Agent Working") = ''
            )
            """,
            (),
        ),
        "mine": (
            """
            work."Agent Working" = ?
            AND work."Case Status" <> 'Completed'
            """,
            (agent_id,),
        ),
        "completed": (
            """
            work."Case Status" = 'Completed'
            AND (
                work."Agent Working" = ?
                OR work."Completed By" = ?
            )
            """,
            (agent_id, agent_id),
        ),
    }

    if queue_name not in queue_filters:
        raise ValueError("Select a valid queue.")

    condition, parameters = queue_filters[queue_name]

    with get_connection(database_path) as connection:
        require_case_worker(connection, agent_id)

        return pd.read_sql_query(
            f"""
            SELECT
                cases.*,
                work."Record Version",
                work."Investigation Reason",
                work."Dependency Type",
                work."Dependency Owner",
                work."Dependency Raised Date",
                work."Dependency Target Date",
                work."Dependency Details"
            FROM operational_case_view AS cases
            JOIN agent_updates AS work
                ON cases."Case ID" = work."Case ID"
            WHERE {condition}
            ORDER BY cases."Snapshot Date", cases."Case ID";
            """,
            connection,
            params=parameters,
        )


def load_management_queue(
    actor_id,
    queue_name,
    database_path=DATABASE_PATH,
):
    queue_filters = {
        "unresolved": """
            work."Case Status" <> 'Completed'
        """,
        "dependencies": """
            work."Case Status" IN (
                'Awaiting Dependency',
                'Awaiting Senior Review',
                'Awaiting Other Department'
            )
        """,
        "completed": """
            work."Case Status" = 'Completed'
        """,
    }

    if queue_name not in queue_filters:
        raise ValueError("Select a valid management queue.")

    condition = queue_filters[queue_name]

    with get_connection(database_path) as connection:
        require_management(connection, actor_id)

        return pd.read_sql_query(
            f"""
            SELECT
                cases.*,
                work."Record Version",
                work."Investigation Reason",
                work."Dependency Type",
                work."Dependency Owner",
                work."Dependency Raised Date",
                work."Dependency Target Date",
                work."Dependency Details"
            FROM operational_case_view AS cases
            JOIN agent_updates AS work
                ON cases."Case ID" = work."Case ID"
            WHERE {condition}
            ORDER BY cases."Snapshot Date", cases."Case ID";
            """,
            connection,
        )
