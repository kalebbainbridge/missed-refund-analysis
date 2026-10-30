import pandas as pd
import streamlit as st

from app.case_actions import (
    INVESTIGATION_REASONS,
    save_case_notes,
    complete_case,
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