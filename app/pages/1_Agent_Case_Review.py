from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Agent Case Review",
    page_icon="🐾",
    layout="wide",
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "prototype"
    / "missed_refunds_prototype.db"
)

if not DATABASE_PATH.exists():
    st.error(
        "The prototype database has not been initialised."
    )
    st.code(
        "python app/init_database.py",
        language="powershell",
    )
    st.stop()
AGENTS = ["DH001", "DH002"]

st.title("Agent Case Review")

st.info(
    "Portfolio prototype using entirely synthetic data. "
    "Agent selection simulates authentication."
)

selected_agent = st.selectbox(
    "Select agent",
    options=[""] + AGENTS,
)

if not selected_agent:
    st.warning(
        "Select an agent to access the case-review queue."
    )
    st.stop()

st.success(f"Working as {selected_agent}")
with sqlite3.connect(DATABASE_PATH) as connection:
    agent_queue = pd.read_sql_query(
        """
        SELECT
            [Case ID],
            [Policy Number],
            [Client Number],
            [Outstanding Amount],
            [Cancellation Status],
            [Refund Type],
            [Root Cause],
            [Agent Working],
            [Agent Notes],
            [Case Status],
            [Final Outcome],
            [Automated Check Result],
            [Accounting Transactions Found],
            [Valid Match Count],
            [Refund Transaction ID],
            [Matched Refund Amount],
            [Refund Processed By],
            [Refund Processed Date],
            [Refund Reason]
        FROM operational_case_view
        WHERE [Case Status] = 'Open'
          AND (
              [Agent Working] IS NULL
              OR TRIM([Agent Working]) = ''
              OR [Agent Working] = ?
          )
        ORDER BY [Snapshot Date], [Case ID]
        """,
        connection,
        params=(selected_agent,),
    )

assigned_to_agent = agent_queue[
    agent_queue["Agent Working"].eq(selected_agent)
]

unassigned_cases = agent_queue[
    agent_queue["Agent Working"].isna()
    | agent_queue["Agent Working"].fillna("").eq("")
]

metric_1, metric_2 = st.columns(2)

metric_1.metric(
    "Assigned to me",
    len(assigned_to_agent),
)

metric_2.metric(
    "Available unassigned cases",
    len(unassigned_cases),
)
filter_1, filter_2 = st.columns(2)

search_value = filter_1.text_input(
    "Search case, policy or client",
)

check_result_options = [
    "All",
    *sorted(
        agent_queue["Automated Check Result"]
        .dropna()
        .unique()
        .tolist()
    ),
]

selected_check_result = filter_2.selectbox(
    "Automated check result",
    options=check_result_options,
)

queue_view = st.radio(
    "Queue view",
    options=[
        "Available cases",
        "My assigned cases",
    ],
    horizontal=True,
)

if queue_view == "My assigned cases":
    filtered_queue = assigned_to_agent.copy()
else:
    filtered_queue = unassigned_cases.copy()
if search_value.strip():
    search_term = search_value.strip().lower()

    search_mask = (
        filtered_queue["Case ID"]
        .astype(str)
        .str.lower()
        .str.contains(search_term, regex=False)
        |
        filtered_queue["Policy Number"]
        .astype(str)
        .str.lower()
        .str.contains(search_term, regex=False)
        |
        filtered_queue["Client Number"]
        .astype(str)
        .str.lower()
        .str.contains(search_term, regex=False)
    )
    filtered_queue = filtered_queue.loc[
        search_mask
    ].copy()

if selected_check_result != "All":
    filtered_queue = filtered_queue.loc[
        filtered_queue["Automated Check Result"]
        .eq(selected_check_result)
    ].copy()

if queue_view == "My assigned cases":
    queue_heading = "My assigned case queue"
else:
    queue_heading = "Available case queue"

st.subheader(queue_heading)

st.caption(
    f"{len(filtered_queue):,} cases match "
    "the current queue and filters."
)
filtered_queue = filtered_queue.reset_index(drop=True)

queue_display = filtered_queue[
    [
        "Case ID",
        "Policy Number",
        "Client Number",
        "Outstanding Amount",
        "Cancellation Status",
        "Refund Type",
        "Root Cause",
        "Automated Check Result",
        "Agent Working",
    ]
]

queue_selection = st.dataframe(
    queue_display,
    width="stretch",
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        "Outstanding Amount": st.column_config.NumberColumn(
            "Outstanding Amount",
            format="£%.2f",
        ),
    },
)

selected_rows = queue_selection.selection.rows

selected_case_id = None

if selected_rows:
    selected_case_id = filtered_queue.iloc[
        selected_rows[0]
    ]["Case ID"]
else:
    st.info(
        "Select a row in the table to review the case."
    )

if selected_case_id:
    selected_case = (
        agent_queue.loc[
            agent_queue["Case ID"].eq(selected_case_id)
        ]
        .iloc[0]
    )

    detail_1, detail_2, detail_3 = st.columns(3)

    detail_1.metric(
        "Outstanding amount",
        f"£{selected_case['Outstanding Amount']:,.2f}",
    )

    detail_2.write("**Policy number**")
    detail_2.write(selected_case["Policy Number"])

    detail_3.write("**Client number**")
    detail_3.write(selected_case["Client Number"])

    st.write("**Cancellation status**")
    st.write(selected_case["Cancellation Status"])

    st.write("**Refund type**")
    st.write(selected_case["Refund Type"])

    st.write("**Root cause**")
    st.write(selected_case["Root Cause"])

    st.subheader("Automated accounting check")

    st.write("**Check result**")
    st.write(selected_case["Automated Check Result"])

    st.write("**Accounting transactions found**")
    st.write(
        int(
            selected_case[
                "Accounting Transactions Found"
            ]
        )
    )

    refund_transaction_id = selected_case[
        "Refund Transaction ID"
    ]

    if pd.notna(refund_transaction_id):
        st.write("**Matched transaction**")
        st.write(refund_transaction_id)

        st.write("**Refund processed by**")
        st.write(selected_case["Refund Processed By"])

        st.write("**Refund processed date**")
        st.write(selected_case["Refund Processed Date"])

        st.write("**Refund reason**")
        st.write(selected_case["Refund Reason"])
    else:
        st.caption(
            "No unique confirmed refund transaction "
            "is attached to this case."
        )

    current_assignment = selected_case["Agent Working"]

    case_is_unassigned = (
        pd.isna(current_assignment)
        or current_assignment == ""
    )

    if case_is_unassigned:
        st.write("**Current assignment:** Unassigned")

        if st.button(
            "Assign to me",
            type="primary",
        ):
            with sqlite3.connect(DATABASE_PATH) as connection:
                update_result = connection.execute(
                    """
                    UPDATE agent_updates
                    SET
                        [Agent Working] = ?,
                        [Last Updated Date] = DATE('now')
                    WHERE [Case ID] = ?
                      AND [Case Status] = 'Open'
                      AND (
                          [Agent Working] IS NULL
                          OR TRIM([Agent Working]) = ''
                      )
                    """,
                    (
                        selected_agent,
                        selected_case_id,
                    ),
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
                            selected_case_id,
                            "Case Assigned",
                            "Open",
                            "Open",
                            selected_agent,
                            "Case assigned to agent.",
                        ),
                    )

            if update_result.rowcount == 1:
                st.rerun()
            else:
                st.error(
                    "The case could not be assigned. "
                    "It may have been updated by another agent."
                )
    else:
        st.write(
            f"**Current assignment:** {current_assignment}"
        )

        existing_notes = selected_case["Agent Notes"]

        if pd.isna(existing_notes):
            existing_notes = ""
        with st.form(
            key=f"case_form_{selected_case_id}"
        ):
            updated_notes = st.text_area(
                "Agent notes",
                value=existing_notes,
                height=120,
            )

            final_outcome = st.selectbox(
                "Final outcome",
                options=[
                    "",
                    "Refund Processed",
                    "Refund Already Processed",
                    "No Refund Due",
                ],
            )

            button_1, button_2 = st.columns(2)
            button_3, button_4 = st.columns(2)

            save_notes = button_1.form_submit_button(
                "Save notes"
            )

            await_senior_review = (
                button_2.form_submit_button(
                    "Await senior review"
                )
            )

            await_other_department = (
                button_3.form_submit_button(
                    "Await other department"
                )
            )

            complete_case = button_4.form_submit_button(
                "Complete case",
                type="primary",
            )
        if save_notes:
            with sqlite3.connect(DATABASE_PATH) as connection:
                update_result = connection.execute(
                    """
                    UPDATE agent_updates
                    SET
                        [Agent Notes] = ?,
                        [Last Updated Date] = DATE('now')
                    WHERE [Case ID] = ?
                      AND [Case Status] = 'Open'
                      AND [Agent Working] = ?
                    """,
                    (
                        updated_notes,
                        selected_case_id,
                        selected_agent,
                    ),
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
                            selected_case_id,
                            "Notes Updated",
                            "Open",
                            "Open",
                            selected_agent,
                            updated_notes,
                        ),
                    )

            if update_result.rowcount == 1:
                st.success("Notes saved.")
            else:
                st.error(
                    "The notes could not be saved. "
                    "The case may have changed."
                )
        dependency_status = None

        if await_senior_review:
            dependency_status = "Awaiting Senior Review"

        if await_other_department:
            dependency_status = "Awaiting Other Department"

        if dependency_status:
            if not updated_notes.strip():
                st.error(
                    "Add a note explaining the dependency "
                    "before referring the case."
                )
            else:
                with sqlite3.connect(DATABASE_PATH) as connection:
                    update_result = connection.execute(
                        """
                        UPDATE agent_updates
                        SET
                            [Agent Notes] = ?,
                            [Case Status] = ?,
                            [Final Outcome] = NULL,
                            [Agent Working] = NULL,
                            [Last Updated Date] = DATE('now')
                        WHERE [Case ID] = ?
                          AND [Case Status] = 'Open'
                          AND [Agent Working] = ?
                        """,
                        (
                            updated_notes,
                            dependency_status,
                            selected_case_id,
                            selected_agent,
                        ),
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
                                selected_case_id,
                                "Dependency Raised",
                                "Open",
                                dependency_status,
                                selected_agent,
                                updated_notes,
                            ),
                        )

                if update_result.rowcount == 1:
                    st.rerun()
                else:
                    st.error(
                        "The dependency could not be saved. "
                        "The case may have changed."
                    )
        if complete_case:
            if not final_outcome:
                st.error(
                    "Select a final outcome before "
                    "completing the case."
                )
            else:
                with sqlite3.connect(DATABASE_PATH) as connection:
                    update_result = connection.execute(
                        """
                        UPDATE agent_updates
                        SET
                            [Agent Notes] = ?,
                            [Case Status] = 'Completed',
                            [Final Outcome] = ?,
                            [Completed By] = ?,
                            [Completion Date] = DATE('now'),
                            [Last Updated Date] = DATE('now')
                        WHERE [Case ID] = ?
                          AND [Case Status] = 'Open'
                          AND [Agent Working] = ?
                        """,
                        (
                            updated_notes,
                            final_outcome,
                            selected_agent,
                            selected_case_id,
                            selected_agent,
                        ),
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
                                selected_case_id,
                                "Case Completed",
                                "Open",
                                "Completed",
                                selected_agent,
                                (
                                    f"Final outcome: {final_outcome}. "
                                    f"{updated_notes}"
                                ),
                            ),
                        )

                if update_result.rowcount == 1:
                    st.rerun()
                else:
                    st.error(
                        "The case could not be completed. "
                        "It may have changed."
                    )

        if (
            not case_is_unassigned
            and current_assignment == selected_agent
            and st.button("Remove assignment")
        ):
            with sqlite3.connect(DATABASE_PATH) as connection:
                update_result = connection.execute(
                    """
                    UPDATE agent_updates
                    SET
                        [Agent Working] = NULL,
                        [Last Updated Date] = DATE('now')
                    WHERE [Case ID] = ?
                      AND [Case Status] = 'Open'
                      AND [Agent Working] = ?
                    """,
                    (
                        selected_case_id,
                        selected_agent,
                    ),
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
                            selected_case_id,
                            "Assignment Removed",
                            "Open",
                            "Open",
                            selected_agent,
                            "Agent returned case to shared queue.",
                        ),
                    )

            if update_result.rowcount == 1:
                st.rerun()
            else:
                st.error(
                    "The assignment could not be removed. "
                    "The case may have changed."
                )