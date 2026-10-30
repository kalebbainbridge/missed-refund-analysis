from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

from app.case_actions import (
    INVESTIGATION_REASONS,
    save_case_notes,
    complete_case,
    release_case,
    raise_dependency,
    resolve_dependency,
)

def render_investigation_form(case, agent_id, revision):
    case_id = case["Case ID"]
    loaded_version = int(case["Record Version"])

    existing_notes = (
        case["Agent Notes"]
        if pd.notna(case["Agent Notes"])
        else ""
    )

    existing_reason = case["Investigation Reason"]
    can_complete = case["Case Status"] == "Open"

    with st.form(
        key=f"investigation_{agent_id}_{case_id}_{revision}"
    ):
        reason = st.selectbox(
            "Investigation reason",
            options=INVESTIGATION_REASONS,
            index=INVESTIGATION_REASONS.index(existing_reason),
        )

        notes = st.text_area(
            "Investigation notes",
            value=existing_notes,
            height=160,
        )

        final_outcome = st.selectbox(
            "Final outcome — used when completing the case",
            options=[
                "",
                "Refund Processed",
                "Refund Already Processed",
                "No Refund Due",
            ],
            format_func=lambda value: value or "Select an outcome",
        )

        save_column, complete_column = st.columns(2)

        save_submitted = save_column.form_submit_button(
            "Save investigation",
        )

        complete_submitted = complete_column.form_submit_button(
            "Complete case",
            type="primary",
            disabled=not can_complete,
        )

        if not can_complete:
            st.caption(
                "Resolve the outstanding dependency before completing."
            )

    if not save_submitted and not complete_submitted:
        return

    if complete_submitted and not final_outcome:
        st.error("Select a final outcome before completing.")
        return

    try:
        if complete_submitted:
            saved = complete_case(
                case_id,
                agent_id,
                final_outcome,
                notes,
                loaded_version,
                investigation_reason=reason,
            )
            success_message = f"{case_id}: case completed."
        else:
            saved = save_case_notes(
                case_id,
                agent_id,
                notes,
                loaded_version,
                investigation_reason=reason,
            )
            success_message = f"{case_id}: investigation saved."

    except (ValueError, PermissionError) as exc:
        st.error(str(exc))
        return

    if not saved:
        st.warning(
            "The case changed or is no longer assigned to you. "
            "Your changes were not saved. Refresh the queues "
            "and review the latest case."
        )
        return

    st.session_state["workspace_message"] = {
        "agent": agent_id,
        "text": success_message,
    }

    st.session_state.pop("workspace_snapshot", None)
    st.rerun()

def render_release_control(case, agent_id, revision):
    case_id = case["Case ID"]

    st.divider()
    st.caption(
        "Save any investigation changes before releasing. "
        "Saved notes and dependency details will be preserved."
    )

    if st.button(
        "Return case to shared queue",
        key=f"release_{agent_id}_{case_id}_{revision}",
    ):
        try:
            released = release_case(
                case_id,
                agent_id,
                int(case["Record Version"]),
            )
        except (ValueError, PermissionError) as exc:
            st.error(str(exc))
            return

        if not released:
            st.warning(
                "The case changed or is no longer assigned to you. "
                "Refresh the queues and review its current state."
            )
            return

        st.session_state["workspace_message"] = {
            "agent": agent_id,
            "text": f"{case_id}: returned to the shared queue.",
        }

        st.session_state.pop("workspace_snapshot", None)
        st.rerun()


def render_raise_dependency_form(case, agent_id, revision):
    if case["Case Status"] != "Open":
        return

    case_id = case["Case ID"]
    today = datetime.now(timezone.utc).date()

    st.subheader("Raise a dependency")
    st.caption(
        "Save investigation changes above first. "
        "The case will remain assigned to you."
    )

    with st.form(
        key=f"raise_dependency_{agent_id}_{case_id}_{revision}"
    ):
        dependency_type = st.selectbox(
            "Dependency type",
            options=["Senior Review", "Other Department"],
        )

        owner = st.text_input("Dependency owner")

        target_date = st.date_input(
            "Target date",
            value=today + timedelta(days=5),
            min_value=today,
        )

        details = st.text_area("Dependency details")

        submitted = st.form_submit_button("Raise dependency")

    if not submitted:
        return

    saved_notes = (
        case["Agent Notes"]
        if pd.notna(case["Agent Notes"])
        else ""
    )

    try:
        raised = raise_dependency(
            case_id,
            agent_id,
            dependency_type,
            owner,
            target_date.isoformat(),
            details,
            saved_notes,
            int(case["Record Version"]),
        )
    except (ValueError, PermissionError) as exc:
        st.error(str(exc))
        return

    if not raised:
        st.warning(
            "The case changed or is no longer assigned to you. "
            "Refresh the queues before trying again."
        )
        return

    st.session_state["workspace_message"] = {
        "agent": agent_id,
        "text": f"{case_id}: dependency raised; still assigned to you.",
    }

    st.session_state.pop("workspace_snapshot", None)
    st.rerun()


def render_resolve_dependency_form(case, agent_id, revision):
    if case["Case Status"] not in {
        "Awaiting Dependency",
        "Awaiting Senior Review",
        "Awaiting Other Department",
    }:
        return

    case_id = case["Case ID"]

    st.subheader("Resolve dependency")
    st.caption(
        "Record the response received. Resolving the dependency "
        "returns the case to Open and keeps it assigned to you."
    )

    with st.form(
        key=f"resolve_dependency_{agent_id}_{case_id}_{revision}"
    ):
        resolution_note = st.text_area("Resolution note")
        submitted = st.form_submit_button("Resolve dependency")

    if not submitted:
        return

    try:
        resolved = resolve_dependency(
            case_id,
            agent_id,
            resolution_note,
            int(case["Record Version"]),
        )
    except (ValueError, PermissionError) as exc:
        st.error(str(exc))
        return

    if not resolved:
        st.warning(
            "The case changed or is no longer assigned to you. "
            "Refresh the queues before trying again."
        )
        return

    st.session_state["workspace_message"] = {
        "agent": agent_id,
        "text": f"{case_id}: dependency resolved; case returned to Open.",
    }

    st.session_state.pop("workspace_snapshot", None)
    st.rerun()
