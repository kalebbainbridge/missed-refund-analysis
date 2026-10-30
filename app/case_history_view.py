import pandas as pd
import streamlit as st

from app.case_history import load_case_history


def render_case_history(case_id, actor_id):
    try:
        history = load_case_history(case_id, actor_id)
    except (ValueError, PermissionError) as exc:
        st.warning(str(exc))
        return

    with st.expander(f"Case history ({len(history)} events)"):
        if history.empty:
            st.info("No workflow events have been recorded for this case.")
            return

        st.caption("Newest events first. History is read-only.")
        st.dataframe(
            history.drop(columns=["Details"]),
            hide_index=True,
            width="stretch",
        )

        events = history.set_index("Event ID")
        newest_event = int(history.iloc[0]["Event ID"])

        def event_label(event_id):
            event = events.loc[event_id]
            actor = event["Recorded By"]
            if pd.isna(actor) or not str(actor).strip():
                actor = "Not recorded"
            return f"{event['Action']} - {event['Recorded At']} - {actor}"

        selected_id = st.selectbox(
            "View event details",
            options=history["Event ID"].tolist(),
            format_func=event_label,
            key=f"history_event_{actor_id}_{case_id}_{newest_event}",
        )

        details = events.loc[selected_id, "Details"]
        st.text(
            str(details)
            if pd.notna(details) and str(details).strip()
            else "No additional details recorded."
        )
