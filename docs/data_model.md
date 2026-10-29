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
   Reviewing agent, root cause, customer-contact status and case outcome.

`Refund Type`, `Root Cause`, `Customer Contacted`, `Agent Working` and `Outcome` are deliberately generated analytical enrichment. They support the exploratory, SQL and Power BI analysis but should not be interpreted as fields available directly from the real monthly discrepancy report. The project uses them to demonstrate the analysis that could become possible through improved structured data capture.

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

The operational model separates source-controlled case data from agent-maintained updates.

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
| `Cancellation Status` | Whether the policy is `Cancelled` or `Void`|
| `Cancelling Department` | Department that processed the cancellation. |
| `Cancelling Agent` | Synthetic identifier for the cancelling agent.

`Refund Type`, `Root Cause` and `Customer Contacted` remain available in the synthetic analytical dataset, but they are not fields supplied by the real source discrepancy report. They represent deliberately generated analytical enrichment informed by operational experience.

`Agent Working`, `Outcome`, notes and completion information are also excluded because they represent investigation or workflow activity rather than source-controlled case attributes.

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

These status values describe the current CSV and SQLite implementation. The planned Dataverse model consolidates `Awaiting Senior Review` and `Awaiting Other Department` into `Awaiting Dependency`, with `Dependency Type` identifying whether the case requires `Senior Review` or `Other Department`.

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

## Agent-Facing Workbook

**File:** `data/operational/agent_case_workbook.xlsx`

The agent-facing workbook is generated by `09_create_agent_workbook.ipynb`. It combines essential source case details with persistent agent updates using `Case ID`.

### Visible Fields

The workbook contains only the information agents need to review cases:

- Case ID
- Policy Number
- Client Number
- Outstanding Amount
- Cancellation Status
- Agent Working
- Agent Notes
- Case Status
- Final Outcome

Source-controlled fields are refreshed from `source_cases.csv`. Permitted agent-entered fields are preserved from the existing workbook and synchronised back to `agent_updates.csv`. Once a case is completed—whether by an agent or by `Automated Check`—it becomes controlled by the persistent backend and cannot be overwritten by older workbook values.

### Refresh Protection

Before rebuilding the workbook, the notebook reads its existing editable fields. This prevents assignments, notes, statuses and outcomes from being overwritten by a source refresh.

When an agent record changes:

- `Last Updated Date` is set automatically
- `Completed By` is populated from `Agent Working` when a case is completed
- `Completion Date` is populated automatically
- cases completed by an agent require an agent assignment and a final outcome
- automated completions require a final outcome but do not require an agent assignment
- all previously completed cases are read-only during workbook synchronisation

The workbook uses filters, frozen headings, currency formatting and controlled dropdown lists. Source fields remain visually separate from the pale-yellow editable fields.

## Automated Accounting Check

**Notebook:** `notebooks/10_auto_check_processed_refunds.ipynb`

**Accounting feed:** `data/accounting/refund_transactions.csv`

**Current run results:** `data/accounting/automated_refund_check_results.csv`

**Run history:** `data/accounting/automated_refund_check_history.csv`

The accounting feed has a grain of one row per refund transaction. Transactions are matched to operational cases using both `Policy Number` and `Client Number`.

A case can be completed automatically only when:

- its current `Case Status` is not `Completed`
- the policy and client numbers match
- the refund amount equals the outstanding amount
- the refund was processed after the snapshot date
- the refund was processed on or before the accounting extract date
- exactly one valid transaction matches the case

Cases with no transaction, an amount mismatch, a pre-snapshot transaction or multiple valid matches remain available for agent review.

Confirmed unique matches are recorded as:

- `Case Status`: `Completed`
- `Final Outcome`: `Refund Already Processed`
- `Completed By`: `Automated Check`
- `Completion Date`: accounting refund processed date

The current-results file records the latest case-level automation decision, matching counts and confirmed transaction details.

The history file adds an `Automation Run ID` and run date. The combination of `Automation Run ID` and `Case ID` must be unique. Rerunning the same automation run replaces that run’s earlier history rows rather than creating duplicates, while future run IDs can be retained for reporting and audit purposes.

## Workflow Prototype Database

**Initialisation script:** `app/init_database.py`

**Generated database:** `data/prototype/missed_refunds_prototype.db`

The generated SQLite prototype contains:

| Object | Purpose |
|---|---|
| `source_cases` | Refreshable case attributes from the synthetic source data. |
| `agent_updates` | Persistent assignment, notes, status and completion fields. |
| `automated_check_results` | Case-level outcomes from the automated accounting check. |
| `operational_case_view` | Combined reporting view joining the three data sources by `Case ID`. |
| `workflow_events` | Timestamped audit history for assignment, notes, dependencies and completion actions. |

The Streamlit application reads and updates the SQLite database rather than editing the source CSV files directly.

Conditional SQL updates protect cases from conflicting changes. For example, an agent can assign a case only when it is still open and unassigned.

Running `app/init_database.py` rebuilds the prototype from the controlled CSV inputs and resets the `workflow_events` table. This provides a clean, reproducible demonstration environment.

 the `workflow_events` table. This provides a clean, reproducible demonstration environment.
(.venv-1) PS C:\Missed Refund Detection and Process Improvement> Select-String -Path docs\*.md -Pattern 'â'
(.venv-1) PS C:\Missed Refund Detection and Process Improvement>

(.venv-1) PS C:\Missed Refund Detection and Process Improvement> git diff --check
docs/data_model.md:285: trailing whitespace.
+(.venv-1) PS C:\Missed Refund Detection and Process Improvement>
(.venv-1) PS C:\Missed Refund Detection and Process Improvement> ## Planned Dataverse Model

The planned Dataverse model translates the refresh-safe local prototype into a structured Power Platform data layer. It remains part of the same missed-refund project and does not replace the historical analytical dataset.

The model separates source-controlled information, agent-entered operational information, accounting transactions and append-only audit history. This prevents source refreshes and automated checks from overwriting completed operational work.

### Application Roles and Identity

Review Agents records application role separately from training and assignment eligibility.

| Role | Permitted actions |
|---|---|
| Agent | Claim available cases and work their own assigned cases when authorised and eligible. View permitted case information and history. |
| Approved Senior | Same application permissions as Manager. |
| Manager | Oversee workload, unassign and reassign unresolved cases, review exceptions and reopen completed cases with a reason. |

Access Enabled must be Yes for application actions. Inactive agents cannot act or receive assignments, regardless of role.

Managers and approved seniors need authorised training and assignment eligibility if they also receive cases.

Role, access, training and eligibility changes are administrator-controlled and audited. Application management permissions do not automatically grant administration rights.

Signed-in identity must map uniquely to the corresponding Review Agents record. Backend permissions must enforce the role rules; hiding controls in the interface is insufficient.

Historical identities and workflow events are retained when access is disabled.

### Planned Tables

| Table | Purpose |
|---|---|
| `Cases` | Refreshable case information originating from the monthly discrepancy report. |
| `Case Work` | Persistent assignment, notes, dependency, status and completion information. |
| `Review Agents` | Controlled list of agents currently or historically associated with the review process. |
| `Refund Transactions` | Read-only accounting transactions used for automated matching. |
| `Automation Runs` | One summary record for each logical automated accounting check. |
| `Automation Results` | One case-level result for each eligible case checked during a run. |
| `Refresh Runs` | Audit record for every attempted source refresh. |
| `Workflow Events` | Append-only history of assignments, updates, dependencies, completions and reopenings. |
| `Data Quality Exceptions` | Retains rejected source rows, validation reasons and review status, linked to the refresh attempt. |

Dependency information is stored in Case Work because the prototype requires no more than one current dependency per case.

Refresh Runs stores refresh totals and run-level outcomes. Data Quality Exceptions stores each rejected source row and its validation reasons. Rejected records remain available for review without entering Cases or overwriting existing case information.

A separate dependency table may be introduced later if multiple concurrent dependencies are required.

Case Work also stores a controlled, agent-captured Investigation Reason, defined in the data dictionary and protected from source refreshes and automation.

### Planned Relationships

| Parent table | Related table | Relationship | Purpose |
|---|---|---|---|
| `Cases` | `Case Work` | One to zero-or-one | Ensures each case has no more than one current operational record. |
| `Review Agents` | `Case Work` | One to many | Allows one authorised agent to work multiple cases. |
| `Cases` | `Workflow Events` | One to many | Preserves the complete history for each case. |
| `Review Agents` | `Workflow Events` | One to many | Identifies the agent responsible for a recorded action when applicable. |
| `Automation Runs` | `Automation Results` | One to many | Groups all case-level decisions produced by one run. |
| `Cases` | `Automation Results` | One to many | Allows unresolved cases to be checked again during later runs. |
| `Refund Transactions` | `Automation Results` | One to many | Links an optional confirmed transaction to results across different runs. |
| `Refresh Runs` | `Cases` | One to many | Records the first and most recent refresh associated with each case. |
| `Refresh Runs` | `Data Quality Exceptions` | One to many | Links each rejected source row to its refresh attempt. |
| `Dataverse User` | `Review Agents` | One to zero-or-one | Maps a signed-in user to at most one review identity. Required before authenticated access is enabled. |

A case may receive multiple automation results only while it remains unresolved. Cases with a status of `Completed` are excluded before matching and checked again immediately before any automated update is applied.

### Identifiers

Dataverse generates an internal GUID for every record. The following readable business identifiers and alternate keys support controlled imports, upserts and duplicate prevention.

| Table | Business identifier or alternate key |
|---|---|
| `Cases` | `Case ID` |
| `Case Work` | Unique `Case` lookup |
| `Review Agents` | `Agent Code` |
| `Refund Transactions` | `Refund Transaction ID` |
| `Automation Runs` | `Automation Run ID` |
| `Automation Results` | Combined `Automation Run` and `Case` lookups |
| `Refresh Runs` | `Refresh Run ID` |
| `Workflow Events` | Automatically generated `Event ID` |
| `Data Quality Exceptions` | Combined `Refresh Run` and `Source Row Number` |
| `Review Agents` | Unique populated `Signed-in User` lookup, in addition to the `Agent Code` alternate key |

The unique `Case` lookup in `Case Work` enforces the logical one-to-one relationship. The combined automation-result key prevents the same case from receiving duplicate results within one logical run.

The Signed-in User association must prevent duplicate populated user mappings. Historical synthetic agents may remain unmapped, but authenticated access cannot be enabled without a valid mapping.

The chosen backend enforcement must be verified during implementation. A lookup field alone does not enforce uniqueness or permissions.

### Update Ownership

| Table | Permitted creator or updater |
|---|---|
| `Cases` | Source refresh process only |
| `Case Work` | Agent app, manager app and controlled automation |
| `Review Agents` | Administrator maintains identity, role, access, training and assignment eligibility. Changes must be audited.
| `Refund Transactions` | Accounting import process only |
| `Automation Runs` | Automated process only |
| `Automation Results` | Automated process only |
| `Refresh Runs` | Refresh process only |
| `Workflow Events` | Append-only records created by apps and automation |
| `Data Quality Exceptions` | Refresh process creates records; managers and approved seniors may update Review Status only. Original rejection evidence remains read-only. |

Agents may self-assign or unassign open cases, enter notes, record dependencies and complete investigations. They cannot edit source, accounting or audit information.

Managers and authorised senior reviewers may unassign or reassign unresolved cases, including cases awaiting a dependency. No reason is required. Assignment changes preserve notes, investigation reasons and dependency details, and automatically record the actor, timestamp and previous/new assignment in Workflow Events.

Managers and approved senior reviewers have the same application permissions. Both may unassign or reassign unresolved cases without providing a reason.

Both may reopen completed cases with a mandatory reason. Reopening returns the status to Open, clears the current Final Outcome, Completed By and Completion Date, and preserves the previous completion details in Workflow Events.

These permissions apply only to approved senior reviewers, not automatically to every agent with seniority.

Automation may update only approved completion fields following an exact accounting match. It cannot alter assignments, agent notes or previously completed records.

Business and audit records cannot be deleted through the prototype application.

### Operational Status Definitions

| Case Status | Definition | Automation eligible |
|---|---|---|
| `Open` | Unresolved case, whether unassigned or assigned. | Yes |
| `Awaiting Dependency` | Waiting for another department or senior review. | Yes |
| `Completed` | Resolved case locked from normal updates. | No |

The model does not use an `In Progress` status. Assignment identifies that an agent is working a case.

`Reopened` is recorded as a workflow event. After an authorised manager reopens a case, its current status returns to `Open`.

### Final Outcome Definitions

| Final Outcome | Definition |
|---|---|
| `Refund Processed` | An agent processed the refund following investigation. |
| `Refund Already Processed` | A valid accounting transaction confirms that the refund had already been processed. |
| `No Refund Due` | Investigation confirmed that no refund was required. |

Automation may set only `Refund Already Processed`.

The historical analytical outcomes remain valid and map to the improved operational model as follows:

| Historical outcome | Improved operational interpretation |
|---|---|
| `Actioned` | `Refund Processed` |
| `No Action` | `Refund Already Processed` or `No Refund Due` |
| `Raised` | `Awaiting Dependency`, followed by a genuine final outcome |

### Dependency Definitions

| Dependency Type | Definition |
|---|---|
| `Other Department` | Another department must investigate or complete an action. |
| `Senior Review` | A senior agent or manager must decide or approve an action. |

A dependency records its owner, raised date, target date and current details within `Case Work`.

### Refresh Audit Design

Every refresh attempt creates one `Refresh Runs` record containing:

- the refresh ID, source filename, snapshot date and file hash
- start time, completion time, status and triggering user or process
- rows received, inserted, updated, unchanged and rejected
- duplicate and missing-required-value counts
- error details
- confirmation that operational records were preserved

Run status values are `Started`, `Succeeded`, `Rejected` and `Failed`.

A source refresh cannot be recorded as successful unless persistent assignments, notes, statuses and outcomes were preserved.

### Automation Audit Design

Every logical accounting check creates one `Automation Runs` record and one `Automation Results` record for each eligible case checked.

The run record stores:

- accounting extract details and source file hash
- automation rule version
- start time, completion time and run status
- eligible and excluded case totals
- decision and exception totals
- updates applied, skipped updates and error details

Each case-level result stores:

- the automation run and case
- check timestamp, decision and result reason
- optional matched refund transaction
- candidate count, expected amount and matched amount
- refund processed date
- whether automatic completion was approved and applied

Controlled decisions are `Auto Complete`, `Agent Review` and `Ambiguous Match`.

Controlled result reasons are:

- `Exact Match`
- `No Accounting Transaction`
- `Amount Mismatch`
- `Refund Not After Snapshot`
- `Multiple Valid Matches`

Completed cases are excluded before matching. Immediately before applying an approved update, the automation checks the persistent case status again. This protects cases completed by an agent while an automation run is in progress.

### Case Date and Retention Rules

- New cases receive the incoming snapshot date as both Snapshot Date and First Identified Date.
- Later accepted snapshots may update Snapshot Date but must preserve First Identified Date.
- Accounting matching requires Refund Processed Date to be strictly after First Identified Date and on or before Accounting Extract Date.
- Cases absent from a later snapshot are retained. Absence does not automatically complete or delete a case.
- Last Seen Refresh changes only when an accepted source row contains that case.
- Older snapshots must not overwrite newer source values. Out-of-order input requires rejection or a separately controlled historical-loading process.

The local Phase 3 tests verified original-date preservation and retention of absent cases. Out-of-order snapshot rejection is implemented and tested in the local SQLite refresh runner. Equivalent enforcement remains required in the planned Power Platform implementation.