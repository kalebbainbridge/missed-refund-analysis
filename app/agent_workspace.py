from uuid import uuid4

import streamlit as st

from app.database import get_connection
from app.permissions import require_case_worker
from app.case_queries import load_agent_queue
from app.case_actions import claim_case
from app.agent_case_details import render_investigation_form


def render_agent_workspace():
    st.title("Agent Workspace")

    st.info(
        "Synthetic portfolio prototype. "
        "Identity selection simulates sign-in."
    )

    with get_connection() as connection:
        agents = connection.execute(
            """
            SELECT agent_code, display_name
            FROM review_agents
            WHERE access_enabled = 1
              AND training_status = 'Authorised'
              AND eligible_for_assignment = 1
            ORDER BY agent_code;
            """
        ).fetchall()

    names = dict(agents)

    agent_id = st.selectbox(
        "Work as",
        options=[""] + list(names),
        format_func=lambda code: (
            f"{names[code]} ({code})" if code else "Select an agent"
        ),
        key="workspace_agent",
    )

    if not agent_id:
        st.stop()

    try:
        with get_connection() as connection:
            require_case_worker(connection, agent_id)
    except PermissionError as exc:
        st.error(str(exc))
        st.stop()

    def refresh_queues():
        st.session_state["workspace_snapshot"] = {
            "agent": agent_id,
            "revision": uuid4().hex,
            "queues": {
                name: load_agent_queue(agent_id, name)
                for name in ["available", "mine", "completed"]
            },
        }

    snapshot = st.session_state.get("workspace_snapshot")

    try:
        if snapshot is None or snapshot["agent"] != agent_id:
            refresh_queues()

        if st.button("Refresh queues"):
            refresh_queues()
    except PermissionError as exc:
        st.error(str(exc))
        st.stop()

    snapshot = st.session_state["workspace_snapshot"]
    queues = snapshot["queues"]

    message = st.session_state.pop("workspace_message", None)

    if message and message["agent"] == agent_id:
        st.info(message["text"])

    available_column, mine_column, completed_column = st.columns(3)

    available_column.metric("Available cases", len(queues["available"]))
    mine_column.metric("My queue", len(queues["mine"]))
    completed_column.metric("My completed work", len(queues["completed"]))

    labels = {
        "Available Cases": "available",
        "My Queue": "mine",
        "Completed Work": "completed",
    }

    selected_view = st.radio(
        "View",
        options=list(labels),
        horizontal=True,
        key="workspace_view",
    )

    queue_name = labels[selected_view]
    cases = queues[queue_name]

    st.subheader(selected_view)
    st.caption("Refresh queues to load the latest changes.")

    if cases.empty:
        st.info("No cases in this queue.")
        return

    display_columns = [
        "Case ID",
        "Policy Number",
        "Client Number",
        "Outstanding Amount",
        "Case Status",
        "Agent Working",
        "Automated Check Result",
    ]

    selection = st.dataframe(
        cases[display_columns],
        hide_index=True,
        width="stretch",
        on_select="rerun",
        selection_mode=(
            "multi-row" if queue_name == "available" else "single-row"
        ),
        key=(
            f"workspace_table_{agent_id}_{queue_name}_"
            f"{snapshot['revision']}"
        ),
        column_config={
            "Outstanding Amount": st.column_config.NumberColumn(
                "Outstanding amount",
                format="£%.2f",
            ),
        },
    )

    selected_rows = selection.selection.rows

    if not selected_rows:
        st.caption(
            "Select cases to claim."
            if queue_name == "available"
            else "Select a case to view its details."
        )
        return

    selected_cases = cases.iloc[selected_rows]

    if queue_name == "available":
        st.write(
            "Selected cases:",
            ", ".join(selected_cases["Case ID"].astype(str)),
        )

        if st.button("Assign selected cases to me", type="primary"):
            results = []

            for _, case in selected_cases.iterrows():
                case_id = case["Case ID"]

                try:
                    claimed = claim_case(
                        case_id,
                        agent_id,
                        int(case["Record Version"]),
                    )
                except PermissionError as exc:
                    results.append(f"{case_id}: blocked — {exc}")
                else:
                    results.append(
                        f"{case_id}: assigned."
                        if claimed
                        else f"{case_id}: changed or no longer available."
                    )

            st.session_state["workspace_message"] = {
                "agent": agent_id,
                "text": "\n\n".join(results),
            }

            # Force a fresh snapshot and clear the old row selection.
            st.session_state.pop("workspace_snapshot", None)
            st.rerun()

    else:
        case = selected_cases.iloc[0]

        st.subheader(f"Case {case['Case ID']}")

        visible_details = case.drop(labels=["Record Version"])

        st.dataframe(
            visible_details.astype(str).rename("Value").to_frame(),
            width="stretch",
        )

        if queue_name == "completed":
            st.caption("Completed work is read-only.")
        else:
            render_investigation_form(
                case,
                agent_id,
                snapshot["revision"],
            )