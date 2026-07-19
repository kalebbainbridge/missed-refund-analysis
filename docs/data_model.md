# Data Model

## Purpose

This document describes the structure and relationships of the synthetic data used in the missed-refund analysis.

The current analytical model combines 18 monthly Power BI-style snapshots into one dataset for Python, SQLite, SQL and Power BI analysis.

No real customer, policy, employee or company data is included.

## Current Analytical Dataset

**File:** `data/combined_missed_refunds.csv`  
**SQLite table:** `missed_refunds`

### Data Grain

Each row represents one unique missed-refund case identified within one monthly snapshot.

`Case ID` is the unique identifier for each case.

The dataset currently contains:

- 18 monthly snapshots
- 2,871 unique cases
- reporting dates from January 2025 to June 2026

## Dataset Components

The dataset contains three main groups of information:

1. **Case identifiers**  
   Case, policy and client identifiers.

2. **Cancellation context**  
   Snapshot date, cancellation status, cancelling department, cancelling agent, refund type and outstanding amount.

3. **Investigation result**  
   Reviewing analyst, root cause, customer-contact status and case outcome.

## Data Relationships

- One `Client Number` may be associated with multiple `Policy Number` values.
- Each generated `Policy Number` is associated with one `Case ID` in the current dataset.
- Each `Case ID` belongs to one monthly `Snapshot Date`.
- Each `Cancelling Agent` belongs to one `Cancelling Department`.
- Each case is reviewed by one synthetic `Agent Working`.
- Refund type influences cancellation status, root cause and outcome within the generation rules.

## Modelled Business Rules

- `Cancellation from Renewal (Void)` cases always have a cancellation status of `Void`.
- `Cancellation Before Premium Due` cases always have a cancellation status of `Cancelled`.
- `Death of Pet` cases may be either `Cancelled` or `Void`.
- Outstanding amounts range from £0.50 to approximately £300.
- A case has one root cause and one outcome.
- A case may indicate that the customer had already contacted the business.
- All case IDs and policy numbers are unique within the current dataset.

## Weekly Operational Dataset

**Detailed file:** `data/weekly/weekly_case_status.csv`

**Summary file:** `data/weekly/weekly_operational_summary.csv`

The weekly dataset records how missed-refund cases change over time.

### Weekly Data Grain

Each detailed row represents one case on one Friday reporting date.

The combination of `Case ID` and `Reporting Date` uniquely identifies each weekly record.

A case may appear across multiple reporting weeks while unresolved. It appears as `Completed` during its completion week and is excluded from later snapshots.

### Relationship to Source Data

`Case ID` links the weekly operational data to the source analytical dataset.

The weekly feed contains the core workbook fields required for operational use. Additional attributes such as cancelling department, cancelling agent, refund type and root cause remain available from the source table.

### Weekly Summary Grain

Each row in `weekly_operational_summary.csv` represents one Friday reporting date and summarises:

- new cases
- processing capacity
- cases reviewed and completed
- new dependencies
- open and dependency backlogs
- total unresolved backlog

The detailed operational design and simulation assumptions are documented in `operational_workflow.md`.

## Refresh-Safe Operational Model

The operational workbook will separate source-controlled case data from agent-maintained updates.

This prevents a source-data refresh from overwriting agent notes, outcomes or completion information.

### Source Cases Table

**Table name:** `source_cases`

**Grain:** One row per `Case ID`.

This table contains case information supplied by the monthly source snapshots. It can be rebuilt or refreshed from the source files because agents do not manually edit it.

#### Source Fields

| Field | Description |
|---|---|
| `Case ID` | Unique identifier for the source case and join key. |
| `Policy Number` | Synthetic policy identifier. |
| `Client Number` | Synthetic customer identifier. |
| `Snapshot Date` | Month-end date of the source snapshot. |
| `Outstanding Amount` | Balance requiring investigation. |
| `Cancellation Status` | Whether the policy is `Cancelled` or `Void`. |
| `Cancelling Department` | Department that processed the cancellation. |
| `Cancelling Agent` | Synthetic identifier for the cancelling agent. |
| `Refund Type` | Cancellation scenario associated with the refund. |
| `Root Cause` | Analytical reason the refund remained outstanding. |
| `Customer Contacted` | Whether the customer had contacted the business before review. |

`Agent Working` and `Outcome` are excluded because they represent agent activity rather than source-controlled case attributes.

### Agent Updates Table

**Table name:** `agent_updates`

**Grain:** One row per `Case ID`.

This table contains information entered or maintained by trained agents. It is stored separately and is never replaced during a source refresh.
#### Operational Update Fields

| Field | Maintained By | Description |
|---|---|---|
| `Case ID` | System | Unique join key linking the update to `source_cases`. |
| `Agent Working` | Agent | Agent who has temporarily selected the case; blank when unassigned. |
| `Agent Notes` | Agent | Free-text operational notes entered during review. |
| `Case Status` | Agent | `Open`, `Awaiting Senior Review`, `Awaiting Other Department` or `Completed`. |
| `Final Outcome` | Agent | Completion result; blank until the case is completed. |
| `Completed By` | System | Automatically copied from `Agent Working` when the case is completed. |
| `Completion Date` | System | Automatically recorded when the status changes to `Completed`. |
| `Last Updated Date` | System | Automatically recorded whenever agent record changes. |

### Agent Update Rules

- Each `Case ID` can appear only once in `agent_updates`.
- New cases are automatically created with a status of `Open`.
- Agents manually update only `Agent Working`, `Agent Notes`, `Case Status` and `Final Outcome`.
- If an agent cannot complete a case, `Agent Working` is cleared so another trained agent can select it.
- When a case becomes `Completed`, the system automatically records `Completed By` and `Completion Date`.
- System-generated dates do not require manual entry.
- `Agent Notes` and other agent updates remain unchanged when the source data refreshes.


### Reporting View

**View name:** `operational_case_view`

**Grain:** One combined row per `Case ID`.

The reporting view joins `source_cases` to `agent_updates` using `Case ID`. It provides the complete current case record for reporting without storing agent updates inside the refreshable source table.

### Refresh Logic

When new monthly source data becomes available:

1. Rebuild or refresh `source_cases` from the source snapshot files.
2. Compare the refreshed `Case ID` values with the existing `agent_updates` table.
3. Create a new default agent record only for case IDs not already present.
4. Preserve every existing agent record without replacing its notes or outcomes.
5. Recreate `operational_case_view` by joining the two tables on `Case ID`.

New agent records begin with:

- `Agent Working`: blank
- `Agent Notes`: blank
- `Case Status`: `Open`
- `Final Outcome`: blank
- `Completed By`: blank
- `Completion Date`: blank
- `Last Updated Date`: the date the case was added

Existing `agent_updates` rows are never replaced by a source refresh.