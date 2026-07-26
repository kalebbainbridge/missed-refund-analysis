from pathlib import Path
import sqlite3

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SOURCE_CASES_PATH = (
    PROJECT_ROOT / "data" / "operational" / "source_cases.csv"
)

AGENT_UPDATES_PATH = (
    PROJECT_ROOT / "data" / "operational" / "agent_updates.csv"
)
AUTOMATED_RESULTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "accounting"
    / "automated_refund_check_results.csv"
)

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "prototype"
    / "missed_refunds_prototype.db"
)

print("Project root:", PROJECT_ROOT)
print("Prototype database:", DATABASE_PATH)
source_cases = pd.read_csv(SOURCE_CASES_PATH)

agent_updates = pd.read_csv(AGENT_UPDATES_PATH)
automated_results = pd.read_csv(
    AUTOMATED_RESULTS_PATH
)

print(
    "Automated check results:",
    automated_results.shape,
)
print(
    "Duplicate audit Case IDs:",
    automated_results["Case ID"].duplicated().sum(),
)

print("Source cases:", source_cases.shape)
print("Agent updates:", agent_updates.shape)

print(
    "Duplicate source Case IDs:",
    source_cases["Case ID"].duplicated().sum(),
)

print(
    "Duplicate update Case IDs:",
    agent_updates["Case ID"].duplicated().sum(),
)
case_alignment = source_cases[["Case ID"]].merge(
    agent_updates[["Case ID"]],
    on="Case ID",
    how="outer",
    indicator=True,
    validate="one_to_one",
)

print("\nCase alignment:")
print(case_alignment["_merge"].value_counts())
with sqlite3.connect(DATABASE_PATH) as connection:
    source_cases.to_sql(
        "source_cases",
        connection,
        if_exists="replace",
        index=False,
    )

    agent_updates.to_sql(
        "agent_updates",
        connection,
        if_exists="replace",
        index=False,
    )
    automated_results.to_sql(
        "automated_check_results",
        connection,
        if_exists="replace",
        index=False,
    )

    source_row_count = connection.execute(
        "SELECT COUNT(*) FROM source_cases"
    ).fetchone()[0]

    update_row_count = connection.execute(
        "SELECT COUNT(*) FROM agent_updates"
    ).fetchone()[0]

    automated_row_count = connection.execute(
        "SELECT COUNT(*) FROM automated_check_results"
    ).fetchone()[0]
with sqlite3.connect(DATABASE_PATH) as connection:
    connection.execute(
        "DROP VIEW IF EXISTS operational_case_view"
    )

    connection.execute(
        """
        CREATE VIEW operational_case_view AS
        SELECT
            source_cases.*,
            agent_updates.[Agent Working],
            agent_updates.[Agent Notes],
            agent_updates.[Case Status],
            agent_updates.[Final Outcome],
            agent_updates.[Completed By],
            agent_updates.[Completion Date],
            agent_updates.[Last Updated Date],
            COALESCE(
                automated_check_results.[Review Result],
                'Not Included'
            ) AS [Automated Check Result],
            automated_check_results.[Transactions_Found]
                AS [Accounting Transactions Found],
            automated_check_results.[Valid_Match_Count]
                AS [Valid Match Count],
            automated_check_results.[Refund Transaction ID],
            automated_check_results.[Refund Amount]
                AS [Matched Refund Amount],
            automated_check_results.[Refund Processed By],
            automated_check_results.[Refund Processed Date],
            automated_check_results.[Refund Reason],
            automated_check_results.[Automated Completion]
        FROM source_cases
        LEFT JOIN agent_updates
            ON source_cases.[Case ID]
            = agent_updates.[Case ID]
                    LEFT JOIN automated_check_results
            ON source_cases.[Case ID]
            = automated_check_results.[Case ID]
        """
    )

    view_row_count = connection.execute(
        "SELECT COUNT(*) FROM operational_case_view"
    ).fetchone()[0]
    automated_row_count = connection.execute(
        "SELECT COUNT(*) FROM automated_check_results"
    ).fetchone()[0]

    connection.execute(
        "DROP TABLE IF EXISTS workflow_events"
    )

    connection.execute(
        """
        CREATE TABLE workflow_events (
            Event_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Case_ID TEXT NOT NULL,
            Event_Type TEXT NOT NULL,
            From_Status TEXT,
            To_Status TEXT,
            Agent_ID TEXT,
            Event_Date TEXT NOT NULL
                DEFAULT CURRENT_TIMESTAMP,
            Event_Notes TEXT
        )
        """
    )

    connection.execute(
        """
        CREATE INDEX workflow_events_case_id_index
        ON workflow_events (Case_ID)
        """
    )

    event_row_count = connection.execute(
        "SELECT COUNT(*) FROM workflow_events"
    ).fetchone()[0]

print("Operational view rows:", view_row_count)
print("Automated result rows written:", automated_row_count)
print("Workflow event rows:", event_row_count)
