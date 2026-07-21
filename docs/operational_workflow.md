# Simulated Operational Workflow

## Purpose

This phase extends the missed-refund analysis from a static monthly snapshot into a simulated operational reporting workflow.

The workflow will model how missed-refund cases change over time, including:

- new cases entering the backlog
- cases remaining open while awaiting review
- cases ageing while unresolved
- cases awaiting senior review or another department
- cases being completed
- backlog reduction over time

## Reporting Workflow

Monthly Snapshot  
→ Data Validation  
→ SQLite Database  
→ Weekly Case Status Feed  
→ Power BI Dashboard

## Data Grain

Each row in the weekly status feed represents the status of one missed-refund case on one weekly reporting date.

A case may therefore appear in multiple weekly snapshots until it is completed or no longer requires action.

The combination of `Case ID` and `Reporting Date` will uniquely identify each weekly case record.

## Reporting Schedule

Each month-end source snapshot enters the operational workflow on the 15th of the following month.

- `Snapshot Date` represents the original month-end source date.
- `Date Added` is the 15th of the following month.
- `Reporting Date` is each Friday on or after the case was added.

For example:

| Snapshot Date | Date Added | First Reporting Date |
|---|---|---|
| 31 January 2025 | 15 February 2025 | 21 February 2025 |

A case continues to appear on subsequent Friday reporting dates until it is completed. It appears as `Completed` in its completion week and is excluded from later weekly snapshots.

## Processing Capacity

Debt Held work is normally completed through a monthly allocation rather than through consistent weekly processing.

### Capacity Assumptions

- Approximately 30 cases can be reviewed per allocated hour.
- A maximum of 10 combined hours is available across both trained agents in a month.
- The 10-hour maximum is not guaranteed because other workloads may reduce, delay or interrupt the allocation.
- The available hours are not divided equally between the two agents.
- Most weeks may have no dedicated Debt Held processing.
- Cases remain open until processing time becomes available.
- Older cases are normally selected first because agents work from the top of the workbook.

### Capacity Calculation

```text
Monthly Processing Capacity = Allocated Hours × 30 Cases
```

| Combined Hours Allocated | Maximum Cases Reviewed |
| -----------------------: | ---------------------: |
|                        0 |                      0 |
|                        2 |                     60 |
|                        5 |                    150 |
|                        8 |                    240 |
|                       10 |                    300 |


## Completion Work Distribution

Two synthetic trained agents complete the Debt Held workload:

| Agent ID | Simulated Share of Completed Cases |
|---|---:|
| `DH001` | 80% |
| `DH002` | 20% |

The distribution is applied probabilistically, so the exact split may vary between reporting periods while remaining close to the intended 80% / 20% pattern overall.

Temporary assignment is not tracked. `Completed By` records only the agent who completed the case.

## Dependency Cases

Cases recorded as `Raised` in the source dataset cannot be completed during their initial review.

These cases enter one of two temporary dependency statuses:

| Dependency Status | Simulated Share |
|---|---:|
| `Awaiting Other Department` | 85% |
| `Awaiting Senior Review` | 15% |

Raised cases follow one of these routes:

```text
Open → Awaiting Other Department → Completed
```

### Dependency Resolution Times

Dependency resolution dates are calculated using working days and exclude weekends.

- `Awaiting Senior Review` cases resolve five working days after they are raised.
- `Awaiting Other Department` cases resolve between one and five working days after they are raised.

A dependency may begin and resolve between two Friday reporting dates. In that situation, the case may move from `Open` in one weekly snapshot to `Completed` in the next without the temporary dependency status appearing in the weekly feed.

This reflects a limitation of weekly snapshot reporting: short-lived status changes may occur between reporting dates.

## Final Outcome Rules

The weekly feed replaces the broad source outcomes with clearer final outcomes.

### Source Outcome: Actioned

Cases recorded as `Actioned` become:

```text
Refund Processed
```

### Source Outcome: No Action

Cases recorded as `No Action` are split into clearer final outcomes based on their age when reviewed.

Older cases are more likely to have already been resolved before the Debt Held agent reaches them.

| Case Age at Review | Refund Already Processed | No Refund Due |
| ------------------ | -----------------------: | ------------: |
| 0–14 days          |                      20% |           80% |
| 15–30 days         |                      35% |           65% |
| 31–60 days         |                      55% |           45% |
| More than 60 days  |                      65% |           35% |

### Source Outcome: Raised

Cases recorded as `Raised` enter a temporary dependency status. Once the dependency is resolved, their final outcome becomes:

```text
Refund Processed
```

## Simulated Case Lifecycle

Cases are normally selected and completed by an agent within the same working session. Agents temporarily assign cases to themselves while reviewing them.

If an agent cannot complete a case, they remove their assignment so another trained agent can pick it up. The weekly feed will therefore not treat assignment or work in progress as persistent case statuses.

### Standard Route

`Open` → `Completed`

### Optional Dependency Routes

Some cases cannot be completed immediately and may require additional action:

`Open` → `Awaiting Senior Review` → `Completed`

or:

`Open` → `Awaiting Other Department` → `Completed`

### Status Definitions

- `Open`  
  The case is available for a trained agent to review.

- `Awaiting Senior Review`  
  The case requires a senior employee to check or approve the next action.

- `Awaiting Other Department`  
  Another department must complete or support the refund.

- `Completed`  
  The case has been resolved and has a final outcome.

### Assignment Rules

- An agent temporarily assigns a case to themselves when beginning the review.
- Most assigned cases are completed during the same working session.
- If the agent cannot complete the case, they remove their assignment so it becomes available to another trained agent.
- Temporary assignment activity is not expected to be visible in a weekly snapshot.
- Cases awaiting senior review or another department remain visible through their dependency status until completed.

Once completed, the case will appear as `Completed` in that reporting week and will not appear in later weekly backlog snapshots.


### Weekly Operational Feed Fields

| Field | Description |
|---|---|
| `Case ID` | Unique identifier linking the operational record to the source case. |
| `Policy Number` | Policy identifier used by the agent to locate the case. |
| `Client Number` | Customer identifier associated with the policy. |
| `Outstanding Amount` | Balance requiring investigation. |
| `Cancellation Status` | Whether the policy is recorded as `Cancelled` or `Void`. |
| `Date Added` | Date the case entered the operational workload. |
| `Reporting Date` | Weekly date on which the case status is recorded. |
| `Case Status` | Current status: `Open`, `Awaiting Senior Review`, `Awaiting Other Department` or `Completed`. |
| `Completion Date` | Date the case was resolved; blank while unresolved. |
| `Completed By` | Synthetic identifier for the agent who completed the case; blank while unresolved. |
| `Final Outcome` | How the case was resolved; blank until completion. |
| `Case Age Days` | Number of days from `Date Added` to the reporting or completion date. |

The combination of `Case ID` and `Reporting Date` uniquely identifies each weekly record.

### Final Outcome Values

Completed cases will use one of the following outcomes:

- `Refund Processed`
- `Refund Already Processed`
- `No Refund Due`

`Awaiting Senior Review` and `Awaiting Other Department` are workflow statuses rather than final outcomes.

## Separation of Source and Operational Data

The source dataset and operational weekly feed serve different purposes.

### Source Analytical Data

The existing SQLite `missed_refunds` table contains the generated case attributes and historical analysis fields:

- Case ID
- Policy Number
- Client Number
- Snapshot Date
- Outstanding Amount
- Cancellation Status
- Cancelling Department
- Cancelling Agent
- Agent Working
- Refund Type
- Root Cause
- Customer Contacted
- Outcome

The cancelling department, cancelling agent, refund type and root cause are available for analysis but are not displayed in the agents’ operational workbook.

### Operational Weekly Feed

The weekly feed records how cases change over time. It contains:

- Case ID
- Policy Number
- Client Number
- Outstanding Amount
- Cancellation Status
- Date Added
- Reporting Date
- Case Status
- Completion Date
- Completed By
- Final Outcome
- Case Age Days

### Agent Workbook View

The operational feed preserves the core information agents currently use to locate and investigate cases:

- Policy Number
- Client Number
- Outstanding Amount
- Cancellation Status

It also adds the status and completion fields required for weekly operational reporting.

### Reporting Relationship

`Case ID` links the source analytical data to the weekly operational feed.

The weekly feed intentionally repeats the four core workbook fields so that each weekly export can be understood and used independently. Additional analytical attributes, including cancelling department, refund type and root cause, remain available through the `Case ID` relationship.

This design allows Power BI and SQL to analyse backlog and completion performance without displaying unnecessary analytical fields in the agents’ working view.

### Source Case Data

The source data contains the static case attributes used for analysis, including:

- Case ID
- Policy Number
- Client Number
- Source Snapshot Date
- Outstanding Amount
- Cancellation Status
- Cancelling Department
- Cancelling Agent
- Refund Type
- Root Cause

These fields remain stored in the SQLite `missed_refunds` table.

### Operational Weekly Feed

The operational feed records how cases change over time. It contains:

- Case ID
- Policy Number
- Client Number
- Reporting Date
- Outstanding Amount
- Date Added
- Case Status
- Completion Date
- Completed By
- Final Outcome
- Case Age Days

### Agent Workbook View

Agents reviewing cases do not need to see all analytical source fields. Their working view contains only the information required to locate, investigate and update a case.

### Reporting Relationship

`Case ID` links the static source case data to the weekly operational feed.

This prevents static case details from being duplicated in every weekly record while allowing Power BI and SQL to analyse operational performance by department, refund type and root cause.

## Refresh-Safe Agent Workflow

The operational workbook separates refreshable source fields from persistent agent-entered fields.

1. Notebook 08 refreshes `source_cases.csv` and maintains `agent_updates.csv`.
2. Notebook 09 reads any existing edits from `agent_case_workbook.xlsx`.
3. Editable values are synchronised back to `agent_updates.csv`.
4. Fresh source fields and preserved updates are merged by `Case ID`.
5. The formatted agent workbook is rebuilt.
6. Power Query merges the source and update tables for operational reporting.

Agents work only with the combined Excel workbook. They do not need to edit the source table or system-maintained completion fields directly.

The workbook must be saved and closed before the refresh notebook runs.
