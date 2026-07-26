
from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Missed Refund Operations",
    page_icon="🐾",
    layout="wide",
)

st.title("Missed Refund Operations")

st.info(
    "Portfolio prototype using entirely synthetic data."
)

st.write(
    "This application supports agent case review "
    "and operational oversight."
)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "prototype"
    / "missed_refunds_prototype.db"
)
with sqlite3.connect(DATABASE_PATH) as connection:
    case_summary = pd.read_sql_query(
        """
        SELECT
            COUNT(*) AS Total_Cases,
            SUM(
                CASE WHEN [Case Status] <> 'Completed'
                THEN 1 ELSE 0 END
            ) AS Current_Backlog,
            SUM(
                CASE
                    WHEN [Case Status] IN (
                        'Awaiting Senior Review',
                        'Awaiting Other Department'
                    )
                    THEN 1 ELSE 0
                END
            ) AS Dependency_Cases,
            SUM(
                CASE WHEN [Case Status] = 'Completed'
                THEN 1 ELSE 0 END
            ) AS Completed_Cases,
            SUM(
                CASE WHEN [Completed By] = 'Automated Check'
                THEN 1 ELSE 0 END
            ) AS Automated_Completions
        FROM operational_case_view
        """,
        connection,
    ).iloc[0]

st.subheader("Current operational position")

column_1, column_2, column_3, column_4 = st.columns(4)

column_1, column_2, column_3, column_4, column_5 = (
    st.columns(5)
)

column_1.metric(
    "Total cases",
    int(case_summary["Total_Cases"]),
)

column_2.metric(
    "Current backlog",
    int(case_summary["Current_Backlog"]),
)

column_3.metric(
    "Dependencies",
    int(case_summary["Dependency_Cases"]),
)

column_4.metric(
    "Completed cases",
    int(case_summary["Completed_Cases"]),
)

column_5.metric(
    "Automated completions",
    int(case_summary["Automated_Completions"]),
)
with sqlite3.connect(DATABASE_PATH) as connection:
    open_cases = pd.read_sql_query(
        """
        SELECT
            [Case ID],
            [Policy Number],
            [Client Number],
            [Outstanding Amount],
            [Cancelling Department],
            [Refund Type],
            [Root Cause],
            [Agent Working]
        FROM operational_case_view
        WHERE [Case Status] = 'Open'
        ORDER BY [Snapshot Date], [Case ID]
        """,
        connection,
    )

st.subheader("Open case queue")

st.caption(
    f"{len(open_cases):,} cases currently require review."
)

st.dataframe(
    open_cases,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Outstanding Amount": st.column_config.NumberColumn(
            "Outstanding Amount",
            format="£%.2f",
        ),
    },
)
with sqlite3.connect(DATABASE_PATH) as connection:
    dependency_cases = pd.read_sql_query(
        """
        SELECT
            [Case ID],
            [Policy Number],
            [Client Number],
            [Outstanding Amount],
            [Case Status],
            [Agent Notes],
            [Last Updated Date]
        FROM operational_case_view
        WHERE [Case Status] IN (
            'Awaiting Senior Review',
            'Awaiting Other Department'
        )
        ORDER BY [Last Updated Date], [Case ID]
        """,
        connection,
    )

st.subheader("Dependency queue")

st.caption(
    f"{len(dependency_cases):,} unresolved cases "
    "are waiting for dependency action."
)

st.dataframe(
    dependency_cases,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Outstanding Amount": st.column_config.NumberColumn(
            "Outstanding Amount",
            format="£%.2f",
        ),
    },
)
if not dependency_cases.empty:
    selected_dependency_case = st.selectbox(
        "Select a resolved dependency",
        options=[""]
        + dependency_cases["Case ID"].tolist(),
    )

    if selected_dependency_case:
        previous_dependency_status = (
            dependency_cases.loc[
                dependency_cases["Case ID"].eq(
                    selected_dependency_case
                ),
                "Case Status",
            ]
            .iloc[0]
        )

        if st.button(
            "Return case to agent queue",
            type="primary",
        ):
            with sqlite3.connect(DATABASE_PATH) as connection:
                update_result = connection.execute(
                    """
                    UPDATE agent_updates
                    SET
                        [Case Status] = 'Open',
                        [Last Updated Date] = DATE('now')
                    WHERE [Case ID] = ?
                      AND [Case Status] IN (
                          'Awaiting Senior Review',
                          'Awaiting Other Department'
                      )
                      AND [Agent Working] IS NULL
                    """,
                    (selected_dependency_case,),
                )

                if update_result.rowcount == 1:
                    connection.execute(
                        """
                        INSERT INTO workflow_events (
                            Case_ID,
                            Event_Type,
                            From_Status,
                            To_Status,
                            Agent_ID,
                            Event_Notes
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            selected_dependency_case,
                            "Dependency Resolved",
                            previous_dependency_status,
                            "Open",
                            "Operations",
                            (
                                "Dependency resolved; case "
                                "returned to shared queue."
                            ),
                        ),
                    )

            if update_result.rowcount == 1:
                st.rerun()
            else:
                st.error(
                    "The case could not be returned. "
                    "It may have changed."
                )
with sqlite3.connect(DATABASE_PATH) as connection:
    completed_cases = pd.read_sql_query(
        """
        SELECT
            [Case ID],
            [Policy Number],
            [Client Number],
            [Outstanding Amount],
            [Final Outcome],
            [Completed By],
            [Completion Date]
        FROM operational_case_view
        WHERE [Case Status] = 'Completed'
        ORDER BY [Completion Date] DESC, [Case ID]
        """,
        connection,
    )

st.subheader("Completed case register")

st.caption(
    f"{len(completed_cases):,} cases have been completed."
)

st.dataframe(
    completed_cases,
    width="stretch",
    hide_index=True,
    column_config={
        "Outstanding Amount": st.column_config.NumberColumn(
            "Outstanding Amount",
            format="£%.2f",
        ),
    },
)
with sqlite3.connect(DATABASE_PATH) as connection:
    workflow_events = pd.read_sql_query(
        """
        SELECT
            Event_ID,
            Case_ID,
            Event_Type,
            From_Status,
            To_Status,
            Agent_ID,
            Event_Date,
            Event_Notes
        FROM workflow_events
        ORDER BY Event_ID DESC
        """,
        connection,
    )

st.subheader("Workflow audit trail")

st.caption(
    f"{len(workflow_events):,} workflow events recorded."
)

st.dataframe(
    workflow_events,
    width="stretch",
    hide_index=True,
)