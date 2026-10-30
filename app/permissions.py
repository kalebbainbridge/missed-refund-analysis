def get_active_agent(connection, agent_id):
    if not isinstance(agent_id, str) or not agent_id.strip():
        raise PermissionError("Select a valid demo identity.")

    row = connection.execute(
        """
        SELECT
            agent_code,
            application_role,
            training_status,
            access_enabled,
            eligible_for_assignment
        FROM review_agents
        WHERE agent_code = ?;
        """,
        (agent_id,),
    ).fetchone()

    if row is None:
        raise PermissionError("Identity is not registered.")

    agent = dict(zip(
        [
            "agent_code",
            "application_role",
            "training_status",
            "access_enabled",
            "eligible_for_assignment",
        ],
        row,
    ))

    if not agent["access_enabled"]:
        raise PermissionError("Application access is disabled.")

    if agent["training_status"] == "Inactive":
        raise PermissionError("This identity is inactive.")

    return agent


def require_case_worker(connection, agent_id):
    agent = get_active_agent(connection, agent_id)

    if agent["training_status"] != "Authorised":
        raise PermissionError("Authorised training is required.")

    if not agent["eligible_for_assignment"]:
        raise PermissionError("This identity cannot work assigned cases.")

    return agent


def require_management(connection, agent_id):
    agent = get_active_agent(connection, agent_id)

    if agent["application_role"] not in {
        "Approved Senior",
        "Manager",
    }:
        raise PermissionError(
            "Manager or approved-senior permission is required."
        )

    return agent