from uuid import uuid4
import hashlib

import streamlit as st

from app.database import get_connection
from app.queue_filters import filter_case_queue
from app.case_history_view import render_case_history
from app.permissions import require_management
from app.case_queries import load_management_queue
from app.manager_case_details import (
    render_management_unassign,
    render_management_reassign,
    render_management_reopen,
)


def render_manager_workspace():
    st.title("Manager and Senior Workspace")
    st.info(
        "Synthetic portfolio prototype. Identity selection simulates "
        "sign-in. Managers and approved seniors have the same permissions."
    )

    with get_connection() as connection:
        identities = connection.execute(
            """
            SELECT agent_code, display_name, application_role
            FROM review_agents
            WHERE access_enabled = 1
              AND training_status <> 'Inactive'
              AND application_role IN ('Manager', 'Approved Senior')
            ORDER BY agent_code;
            """
        ).fetchall()

    labels = {
        code: f"{name} ({code}) - {role}"
        for code, name, role in identities
    }

    actor_id = st.selectbox(
        "Work as",
        options=[""] + list(labels),
        format_func=lambda code: labels.get(code, "Select a manager or approved senior"),
        key="management_identity",
    )

    if not actor_id:
        st.stop()

    try:
        with get_connection() as connection:
            require_management(connection, actor_id)
    except PermissionError as exc:
        st.error(str(exc))
        st.stop()

    def refresh_queues():
        st.session_state["management_snapshot"] = {
            "actor": actor_id,
            "revision": uuid4().hex,
            "queues": {
                name: load_management_queue(actor_id, name)
                for name in ["unresolved", "dependencies", "completed"]
            },
        }

    snapshot = st.session_state.get("management_snapshot")

    try:
        if snapshot is None or snapshot["actor"] != actor_id:
            refresh_queues()

        if st.button("Refresh management queues"):
            refresh_queues()
    except PermissionError as exc:
        st.error(str(exc))
        st.stop()

    snapshot = st.session_state["management_snapshot"]
    message = st.session_state.pop("management_message", None)
    if message and message["actor"] == actor_id:
        st.info(message["text"])

    queues = snapshot["queues"]
    unresolved = queues["unresolved"]

    assigned = (
        unresolved["Agent Working"]
        .fillna("")
        .astype(str)
        .str.strip()
        .ne("")
    )

    columns = st.columns(5)
    columns[0].metric("Unresolved cases", len(unresolved))
    columns[1].metric("Unassigned", int((~assigned).sum()))
    columns[2].metric("Assigned", int(assigned.sum()))
    columns[3].metric("Dependencies", len(queues["dependencies"]))
    columns[4].metric("Completed cases", len(queues["completed"]))

    st.caption(
        f"Total cases: {len(unresolved) + len(queues['completed']):,}. "
        "Refresh queues to load the latest changes."
    )

    views = {
        "Unresolved Cases": "unresolved",
        "Dependencies": "dependencies",
        "Completed Cases": "completed",
    }

    selected_view = st.radio(
        "View",
        options=list(views),
        horizontal=True,
        key="management_view",
    )

    queue_name = views[selected_view]
    queue_cases = queues[queue_name]

    search_column, assignment_column = st.columns(2)
    search_text = search_column.text_input(
        "Search case, policy or client",
        key=f"management_search_{actor_id}_{queue_name}",
    )

    assignments = (
        queue_cases["Agent Working"].fillna("").astype(str).str.strip()
    )
    assigned_codes = sorted(assignments.loc[assignments.ne("")].unique())
    assignment_choice = assignment_column.selectbox(
        "Assigned agent",
        options=["All assignments", "Unassigned"] + assigned_codes,
        key=f"management_assignment_{actor_id}_{queue_name}",
    )

    if assignment_choice == "All assignments":
        assignment_mode, target_agent = "all", None
    elif assignment_choice == "Unassigned":
        assignment_mode, target_agent = "unassigned", None
    else:
        assignment_mode, target_agent = "agent", assignment_choice

    cases = filter_case_queue(
        queue_cases,
        search_text,
        assignment_mode=assignment_mode,
        agent_id=target_agent,
    )
    filter_signature = hashlib.sha256(
        repr((search_text.strip().casefold(), assignment_mode, target_agent))
        .encode("utf-8")
    ).hexdigest()[:16]
    st.subheader(selected_view)
    st.caption(
        f"Showing {len(cases):,} of {len(queue_cases):,} cases in this queue."
    )

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
        "Investigation Reason",
    ]

    selection = st.dataframe(
        cases[display_columns],
        hide_index=True,
        width="stretch",
        on_select="rerun",
        selection_mode="single-row",
        key=(
            f"management_table_{actor_id}_{queue_name}_"
            f"{snapshot['revision']}_{filter_signature}"
        ),
        column_config={
            "Outstanding Amount": st.column_config.NumberColumn(
                "Outstanding amount", format="£%.2f"
            ),
        },
    )

    selected_rows = selection.selection.rows

    if not selected_rows:
        st.caption("Select a case to view its details.")
        return

    case = cases.iloc[selected_rows[0]]
    st.subheader(f"Case {case['Case ID']}")
    visible_details = case.drop(labels=["Record Version"])
    st.dataframe(
        visible_details.astype(str).rename("Value").to_frame(),
        width="stretch",
    )
    render_case_history(case["Case ID"], actor_id)

    render_management_unassign(
        case,
        actor_id,
        snapshot["revision"],
    )

    render_management_reassign(
        case,
        actor_id,
        snapshot["revision"],
    )

    render_management_reopen(
        case,
        actor_id,
        snapshot["revision"],
    )
