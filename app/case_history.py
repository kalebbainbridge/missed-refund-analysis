import pandas as pd

from app.database import DATABASE_PATH, get_connection
from app.permissions import get_active_agent


def load_case_history(
    case_id,
    actor_id,
    database_path=DATABASE_PATH,
):
    with get_connection(database_path) as connection:
        connection.execute("BEGIN;")
        actor = get_active_agent(connection, actor_id)

        case = connection.execute(
            """
            SELECT
                "Case Status",
                "Agent Working",
                "Completed By"
            FROM agent_updates
            WHERE "Case ID" = ?;
            """,
            (case_id,),
        ).fetchone()

        if case is None:
            raise ValueError("Case not found.")

        status, assigned_agent, completed_by = case

        is_management = actor["application_role"] in {
            "Manager",
            "Approved Senior",
        }

        if not is_management:
            authorised_worker = (
                actor["training_status"] == "Authorised"
                and actor["eligible_for_assignment"] == 1
            )

            own_case = assigned_agent == actor_id

            own_completed_case = (
                status == "Completed"
                and completed_by == actor_id
            )

            available_case = (
                status == "Open"
                and (
                    assigned_agent is None
                    or not assigned_agent.strip()
                )
            )

            if not authorised_worker or not (
                own_case or own_completed_case or available_case
            ):
                raise PermissionError(
                    "You cannot view this case's history."
                )

        return pd.read_sql_query(
            """
            SELECT
                Event_ID AS "Event ID",
                Event_Date AS "Recorded At",
                Event_Type AS "Action",
                Agent_ID AS "Recorded By",
                From_Status AS "Previous Status",
                To_Status AS "New Status",
                Event_Notes AS "Details"
            FROM workflow_events
            WHERE Case_ID = ?
            ORDER BY Event_ID DESC;
            """,
            connection,
            params=(case_id,),
        )