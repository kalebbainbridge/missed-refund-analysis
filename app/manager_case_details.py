import pandas as pd
import streamlit as st

from app.case_actions import unassign_case, reassign_case, reopen_case
from app.database import get_connection
from app.permissions import require_management


def render_management_unassign(case, actor_id, revision):
    if case["Case Status"] == "Completed":
        st.caption("Completed cases cannot be unassigned.")
        return

    assigned_agent = case["Agent Working"]

    if pd.isna(assigned_agent) or not str(assigned_agent).strip():
        st.caption("This case is already in the shared unassigned queue.")
        return

    case_id = case["Case ID"]
    st.subheader("Assignment controls")
    st.write(f"Currently assigned to: **{assigned_agent}**")
    st.caption(
        "Unassigning returns this case to the shared queue. "
        "Saved notes, investigation reason and dependency details are retained."
    )

    if st.button(
        "Unassign to shared queue",
        key=f"management_unassign_{actor_id}_{case_id}_{revision}",
    ):
        try:
            changed = unassign_case(
                case_id,
                actor_id,
                int(case["Record Version"]),
            )
        except (ValueError, PermissionError) as exc:
            st.error(str(exc))
            return

        if not changed:
            st.warning(
                "The case changed or is already unassigned. "
                "Refresh the management queues and review the latest case."
            )
            return

        st.session_state["management_message"] = {
            "actor": actor_id,
            "text": f"{case_id}: unassigned to the shared queue.",
        }
        st.session_state.pop("management_snapshot", None)
        st.rerun()


def render_management_reassign(case, actor_id, revision):
    if case["Case Status"] == "Completed":
        return

    with get_connection() as connection:
        try:
            require_management(connection, actor_id)
        except PermissionError as exc:
            st.error(str(exc))
            return

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

    current_agent = case["Agent Working"]
    names = {
        code: name
        for code, name in agents
        if pd.isna(current_agent) or code != current_agent
    }

    st.subheader("Reassign case")

    if not names:
        st.info("No other eligible agents are available.")
        return

    case_id = case["Case ID"]
    target_agent = st.selectbox(
        "Assign to",
        options=[""] + list(names),
        format_func=lambda code: (
            f"{names[code]} ({code})" if code else "Select an eligible agent"
        ),
        key=f"management_target_{actor_id}_{case_id}_{revision}",
    )

    if st.button(
        "Reassign case",
        key=f"management_reassign_{actor_id}_{case_id}_{revision}",
    ):
        if not target_agent:
            st.warning("Select an eligible agent first.")
            return

        try:
            changed = reassign_case(
                case_id,
                actor_id,
                target_agent,
                int(case["Record Version"]),
            )
        except (ValueError, PermissionError) as exc:
            st.error(str(exc))
            return

        if not changed:
            st.warning(
                "The case changed or its assignment is already the same. "
                "Refresh the management queues before trying again."
            )
            return

        st.session_state["management_message"] = {
            "actor": actor_id,
            "text": f"{case_id}: assigned to {target_agent}.",
        }
        st.session_state.pop("management_snapshot", None)
        st.rerun()


def render_management_reopen(case, actor_id, revision):
    if case["Case Status"] != "Completed":
        return

    case_id = case["Case ID"]
    st.subheader("Reopen case")
    st.caption(
        "Reopening returns the case to Open, retaining its notes, "
        "investigation reason and current assignment. Previous completion "
        "details are preserved in history."
    )

    with st.form(
        key=f"management_reopen_{actor_id}_{case_id}_{revision}"
    ):
        reason = st.text_area("Reopening reason")
        submitted = st.form_submit_button("Reopen case", type="primary")

    if not submitted:
        return

    try:
        changed = reopen_case(
            case_id,
            actor_id,
            reason,
            int(case["Record Version"]),
        )
    except (ValueError, PermissionError) as exc:
        st.error(str(exc))
        return

    if not changed:
        st.warning(
            "The case changed or has already been reopened. "
            "Refresh the management queues and review the latest case."
        )
        return

    st.session_state["management_message"] = {
        "actor": actor_id,
        "text": f"{case_id}: reopened. Previous completion details retained in history.",
    }
    st.session_state.pop("management_snapshot", None)
    st.rerun()
