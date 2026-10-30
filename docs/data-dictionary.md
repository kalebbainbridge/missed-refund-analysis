# Data Dictionary

## Purpose

This document describes the fields used throughout the synthetic missed refund dataset.

The dataset has been designed to reflect the structure of a real operational insurance process while containing no genuine customer or company data.

This data dictionary supports the accompanying Python notebooks and Power BI dashboard by explaining the purpose and data type of each field.

## Synthetic Analytical Dataset

The main analytical dataset contains both simulated source attributes and deliberately generated analytical enrichment.

`Refund Type`, `Root Cause`, `Customer Contacted`, `Agent Working` and `Outcome` support the Python, SQL and Power BI analysis. They are informed by operational experience but are not presented as fields supplied directly by the real monthly discrepancy report.

| Column | Type | Description |
|---|---|---|
| `Case ID` | Text | Unique synthetic identifier for each missed-refund case. |
| `Policy Number` | Text | Unique synthetic policy identifier. |
| `Client Number` | Text | Synthetic customer identifier; one client may hold multiple policies. |
| `Snapshot Date` | Date | Latest accepted monthly snapshot containing the case. Updated only by the source refresh process. |
| `First Identified Date` | Date | Original snapshot date when the case first entered the workflow. Set on creation and preserved during later refreshes. Used as the lower date boundary for accounting matching. |
| `Outstanding Amount` | Decimal | Outstanding balance requiring investigation, measured in pounds sterling. |
| `Cancellation Status` | Category | Whether the policy was recorded as `Cancelled` or `Void`. |
| `Cancelling Department` | Category | Department responsible for processing the policy cancellation. |
| `Cancelling Agent` | Text | Synthetic identifier for the agent who processed the cancellation. |
| `Agent Working` | Text | Synthetic identifier for the trained agent who reviewed the case. |
| `Refund Type` | Category | Cancellation scenario associated with the potential refund. |
| `Root Cause` | Category | Simulated reason the refund remained outstanding. |
| `Customer Contacted` | Category | Whether the customer had contacted the business before the case was reviewed. |
| `Outcome` | Category | Result of the case review: `Actioned`, `No Action` or `Raised`. |

## Refresh-Safe Source Cases

`data/operational/source_cases.csv` contains only the fields treated as refreshable source information.

| Column | Type | Description |
|---|---|---|
| `Case ID` | Text | Unique identifier used to link the source case to persistent operational records. |
| `Policy Number` | Text | Synthetic policy identifier used to locate the policy. |
| `Client Number` | Text | Synthetic customer identifier; one client may hold multiple policies. |
| `Snapshot Date` | Date | Month-end date of the discrepancy snapshot. |
| `Outstanding Amount` | Decimal | Accounting difference requiring investigation, measured in pounds sterling. |
| `Cancellation Status` | Category | Whether the policy is recorded as `Cancelled` or `Void`. |
| `Cancelling Department` | Category | Department that processed the cancellation. |
| `Cancelling Agent` | Text | Synthetic identifier for the agent who processed the cancellation. |

This operational source does not contain refund type, root cause, customer-contact history, agent notes or investigation outcomes.

## Persistent Agent Updates

`data/operational/agent_updates.csv` stores information that must survive every source refresh.

| Column | Type | Maintained By | Description |
|---|---|---|---|
| `Case ID` | Text | System | Unique key linking the update to the source case. |
| `Agent Working` | Text | Agent | Agent currently assigned to the case; blank when unassigned. |
| `Agent Notes` | Text | Agent | Operational notes recorded during investigation. |
| `Case Status` | Category | Agent or system | Current workflow status. |
| `Final Outcome` | Category | Agent or automation | How the case was resolved; blank until completion. |
| `Completed By` | Text | System | Agent identifier or `Automated Check`. |
| `Completion Date` | Date | System | Date the case was completed. |
| `Last Updated Date` | Date | System | Date the operational record last changed. |

Existing records are not replaced during a source refresh. Once a case is completed, it is protected from older workbook values.

## Category Values

### Cancellation Status

- `Cancelled`
- `Void`

### Refund Type

- `Death of Pet`
- `Cancellation Before Premium Due`
- `Cancellation from Renewal (Void)`

### Root Cause

- `Payment Date Misunderstood`
- `Agent Forgot`
- `Waiting for Information`
- `Refund Mailbox Delay`

### Customer Contacted

- `Yes`
- `No`

### Outcome

- `Actioned` — the reviewing agent processed the refund.
- `No Action` — the refund had already been processed or no refund was due.
- `Raised` — the case required senior review or action by another department.

## Notes

- All identifiers and records are entirely synthetic; no real customer information has been anonymised or included.
- The dataset is intended only for portfolio demonstration.
- The fields and relationships are informed by operational experience but have been simplified for this project.

## Refund Transactions

`data/accounting/refund_transactions.csv` simulates the accounting information that agents currently inspect manually.

Each row represents one refund transaction.

| Column | Type | Description |
|---|---|---|
| `Refund Transaction ID` | Text | Unique identifier for the simulated accounting transaction. |
| `Policy Number` | Text | Policy identifier used in matching. |
| `Client Number` | Text | Client identifier used in matching. |
| `Refund Amount` | Decimal | Amount of the processed refund. |
| `Refund Processed By` | Text | Synthetic identifier for the person who processed the refund. |
| `Refund Processed Date` | Date | Date the refund was processed. |
| `Refund Reason` | Text | Reason entered with the accounting transaction. |

The refund reason is retained for audit purposes but is not used as an automated matching rule.

## Automated Refund Check

The automated check produces two related files:

- `automated_refund_check_results.csv` — latest case-level result
- `automated_refund_check_history.csv` — retained results by automation run

The combination of `Automation Run ID` and `Case ID` is unique within the history file.

| Column | Type | Description |
|---|---|---|
| `Case ID` | Text | Case assessed by the automation. |
| `Transactions_Found` | Integer | Number of accounting transactions found for the case identifiers. |
| `Amount_Match_Count` | Integer | Number of transactions matching the outstanding amount. |
| `Post_Snapshot_Count` | Integer | Number of transactions processed after the snapshot date. |
| `Valid_Match_Count` | Integer | Number of transactions passing every matching rule. |
| `Review Result` | Category | Case-level result of the automated check. |
| `Refund Transaction ID` | Text | Confirmed transaction used for an automated completion; blank otherwise. |
| `Refund Amount` | Decimal | Amount of the confirmed transaction; blank without a unique match. |
| `Refund Processed By` | Text | Person who processed the confirmed refund. |
| `Refund Processed Date` | Date | Date the confirmed refund was processed. |
| `Refund Reason` | Text | Accounting reason attached to the confirmed transaction. |
| `Automated Completion` | Boolean | Whether the case qualifies for automatic completion. |
| `Automation Run ID` | Text | Stable identifier for the automation run. |
| `Automation Run Date` | Date | Date associated with the automation run. |

### Review Result Values

- `Confirmed Unique Match`
- `Amount Mismatch`
- `Refund Not After Snapshot`
- `Multiple Valid Matches`
- `No Accounting Transaction`

Only `Confirmed Unique Match` can produce an automated completion.

## Weekly Operational Dataset

The weekly operational feed contains one row per case per Friday reporting date.

| Column | Type | Description |
|---|---|---|
| `Case ID` | Text | Identifier linking the weekly record to the source case. |
| `Policy Number` | Text | Synthetic policy identifier used to locate the case. |
| `Client Number` | Text | Synthetic customer identifier associated with the policy. |
| `Outstanding Amount` | Decimal | Balance requiring investigation. |
| `Cancellation Status` | Category | Whether the policy is `Cancelled` or `Void`. |
| `Date Added` | Date | Date the case entered the operational workload. |
| `Reporting Date` | Date | Friday date represented by the weekly snapshot. |
| `Case Status` | Category | `Open`, `Awaiting Senior Review`, `Awaiting Other Department` or `Completed`. |
| `Completion Date` | Date | Date the case was resolved; blank while unresolved. |
| `Completed By` | Text | Synthetic identifier for the agent who completed the case. |
| `Final Outcome` | Category | `Refund Processed`, `Refund Already Processed` or `No Refund Due`; blank while unresolved. |
| `Case Age Days` | Integer | Days from `Date Added` to the reporting date or completion date. |

The combination of `Case ID` and `Reporting Date` uniquely identifies each weekly record.

The weekly dataset retains the two historical dependency statuses used by the existing simulation. The planned Dataverse model represents both as `Awaiting Dependency` and stores the specific requirement in `Dependency Type`.

## Planned Dataverse Tables

Dataverse automatically assigns every record an internal GUID and system-managed `Created On`, `Created By`, `Modified On` and `Modified By` values. The fields below describe the additional business columns required by the prototype.

### Cases

This table contains refreshable source information. App users cannot edit these fields.

| Column | Type | Description |
|---|---|---|
| `Case ID` | Text | Unique business identifier and alternate key. |
| `Policy Number` | Text | Synthetic policy identifier. |
| `Client Number` | Text | Synthetic customer identifier. |
| `Snapshot Date` | Date | Month-end date of the source discrepancy snapshot. |
| `Outstanding Amount` | Currency | Accounting difference requiring investigation. |
| `Cancellation Status` | Choice | `Cancelled` or `Void`. |
| `Cancelling Department` | Text | Department that processed the cancellation. |
| `Cancelling Agent` | Text | Synthetic identifier for the cancelling agent. |
| `First Seen Refresh` | Lookup | Refresh run that first created the case. |
| `Last Seen Refresh` | Lookup | Most recent refresh that inserted, updated or confirmed the case. |

### Case Work

This table contains persistent operational information protected from source refreshes. The `Case` lookup must be unique so that each case has no more than one current operational record.

| Column | Type | Description |
|---|---|---|
| `Case` | Lookup | Related record in `Cases`; alternate key for the table. |
| `Assigned Agent` | Lookup | Current agent selected from eligible `Review Agents`; blank when unassigned. |
| `Agent Notes` | Multiline text | Investigation notes entered through the agent application. |
| `Case Status` | Choice | `Open`, `Awaiting Dependency` or `Completed`. |
| `Dependency Type` | Choice | `Other Department` or `Senior Review`; blank without a dependency. |
| `Dependency Owner` | Text | Team or senior person currently responsible for the dependency. |
| `Dependency Raised Date` | Date | Date the dependency was created. |
| `Dependency Target Date` | Date | Expected resolution date. |
| `Dependency Details` | Multiline text | Information required to understand and resolve the dependency. |
| `Final Outcome` | Choice | `Refund Processed`, `Refund Already Processed` or `No Refund Due`; blank until completion. |
| `Completed By` | Text | Agent code or `Automated Check`; blank until completion. |
| `Completion Date` | Date | Date the case reached a terminal outcome. |
| `Last Updated Date` | Date and time | Most recent controlled operational update. |
| `Investigation Reason` | Choice | Agent-recorded reason; defaults to `Not Yet Determined`. See Agent-Captured Investigation Reason for values and rules. |

Assignment identifies whether an agent is working an open case, so no separate `In Progress` status is required.

A completed record is read-only for agents and automation. An authorised manager or approved senior reviewer may reopen it with a mandatory reason, which is retained in Workflow Events.

### Review Agents

This table controls who may be assigned work without deleting historical agent identities.

| Column | Type | Description |
|---|---|---|
| `Agent Code` | Text | Unique synthetic agent identifier and alternate key. |
| `Display Name` | Text | Name displayed in the prototype interface. |
| `Training Status` | Choice | `In Training`, `Authorised` or `Inactive`. |
| `Eligible for Assignment` | Boolean | Whether the agent can currently receive cases. |
| `Effective From` | Date | Date the agent became associated with the process. |
| `Effective To` | Date | Date the association ended; blank while current. |
| `Application Role` | Choice | `Agent`, `Approved Senior` or `Manager`. Defaults to `Agent`; controls permitted application actions. |
| `Access Enabled` | Boolean | Whether the person may currently use the application. Defaults to `No` until access is approved. |
| `Signed-in User` | Lookup | Associated Dataverse user identity. Must be unique when populated; required before enabling authenticated access. |

Only agents with `Training Status = Authorised` and `Eligible for Assignment = Yes` appear in assignment controls. Historical agent records are marked inactive rather than deleted.

### Application Access and Roles

Training Status, assignment eligibility and application permissions are separate controls.

- Access Enabled must be Yes before application actions are permitted.
- Agents may claim and work cases only when Training Status is Authorised and Eligible for Assignment is Yes.
- Approved Senior and Manager have the same application permissions, including unassignment, reassignment, exception review and controlled reopening.
- Reopening requires a reason; assignment changes do not.
- Receiving cases still requires authorised training and assignment eligibility, regardless of application role.
- Disabling access prevents further actions without deleting historical identity or activity.
- Role and access changes are restricted to an administrator and must be audited.
- App screen visibility alone does not enforce permissions. Equivalent controls must be enforced by the backend.
- The signed-in identity must be securely mapped to the relevant Review Agents record. Selecting an agent name is only suitable for the existing simulated prototype.
- Training Status must not be Inactive for any application action

### Refund Transactions

This table contains read-only accounting information imported for matching.

| Column | Type | Description |
|---|---|---|
| `Refund Transaction ID` | Text | Unique transaction identifier and alternate key. |
| `Policy Number` | Text | Policy identifier used during matching. |
| `Client Number` | Text | Client identifier used during matching. |
| `Refund Amount` | Currency | Amount of the processed refund. |
| `Refund Processed By` | Text | Synthetic identifier for the person who processed the refund. |
| `Refund Processed Date` | Date | Date the refund was processed. |
| `Refund Reason` | Multiline text | Accounting reason retained for reference and audit. |

`Refund Reason` is not an automated matching rule.

### Automation Runs

Each record summarises one logical automated accounting check.

| Column | Type | Description |
|---|---|---|
| `Automation Run ID` | Text | Unique logical run identifier and alternate key. |
| `Accounting Extract Date` | Date | Date represented by the accounting extract. |
| `Source File Name` | Text | Accounting file processed. |
| `Source File Hash` | Text | Fingerprint used to identify duplicate input files. |
| `Rule Version` | Text | Version of the matching rules applied. |
| `Started At` | Date and time | Time processing began. |
| `Completed At` | Date and time | Time processing ended. |
| `Run Status` | Choice | `Started`, `Succeeded`, `Rejected` or `Failed`. |
| `Eligible Case Count` | Whole number | Open or dependency cases eligible at the start of the run. |
| `Completed Cases Excluded` | Whole number | Terminal cases deliberately excluded from matching. |
| `Cases Checked` | Whole number | Case-level results created during the run. |
| `Exact Match Count` | Whole number | Cases approved for automatic completion. |
| `Agent Review Count` | Whole number | Cases requiring manual investigation. |
| `Ambiguous Match Count` | Whole number | Cases with multiple valid transaction candidates. |
| `Updates Applied` | Whole number | Case records successfully completed by automation. |
| `Updates Skipped` | Whole number | Approved updates blocked by a later status change or conflict. |
| `Error Details` | Multiline text | Run-level rejection or technical failure information. |
| `Triggered By` | Text | User, flow or scheduled process that initiated the run. |

### Automation Results

Each record contains the decision for one eligible case during one automation run. The combined `Automation Run` and `Case` lookups form the alternate key.

| Column | Type | Description |
|---|---|---|
| `Automation Run` | Lookup | Parent record in `Automation Runs`. |
| `Case` | Lookup | Case assessed during the run. |
| `Checked At` | Date and time | Time the case-level decision was made. |
| `Decision` | Choice | `Auto Complete`, `Agent Review` or `Ambiguous Match`. |
| `Result Reason` | Choice | Exact explanation for the automation decision. |
| `Matched Refund Transaction` | Lookup | Confirmed accounting transaction; blank without a unique match. |
| `Candidate Match Count` | Whole number | Number of possible transactions found. |
| `Expected Amount` | Currency | Outstanding case amount at check time. |
| `Matched Refund Amount` | Currency | Refund amount considered; blank without a match. |
| `Refund Processed Date` | Date | Date of the transaction considered. |
| `Automated Completion Approved` | Boolean | Whether all automatic-completion rules passed. |
| `Case Update Applied` | Boolean | Whether the persistent case record was successfully completed. |
| `Update Applied At` | Date and time | Time the controlled update succeeded. |

Permitted result reasons are:

- `Exact Match`
- `No Accounting Transaction`
- `Amount Mismatch`
- `Refund Not After Snapshot`
- `Multiple Valid Matches`

Only `Exact Match` can approve automatic completion.

### Refresh Runs

Each record provides an audit receipt for one attempted source refresh.

| Column | Type | Description |
|---|---|---|
| `Refresh Run ID` | Text | Unique readable identifier and alternate key. |
| `Source File Name` | Text | Source snapshot file processed. |
| `Source Snapshot Date` | Date | Reporting period represented by the source file. |
| `Source File Hash` | Text | Fingerprint used to detect repeated input files. |
| `Started At` | Date and time | Time processing began. |
| `Completed At` | Date and time | Time processing ended. |
| `Run Status` | Choice | `Started`, `Succeeded`, `Rejected` or `Failed`. |
| `Rows Received` | Whole number | Total source rows read. |
| `Rows Inserted` | Whole number | New cases created. |
| `Rows Updated` | Whole number | Existing source cases updated. |
| `Rows Unchanged` | Whole number | Existing cases requiring no source change. |
| `Rows Rejected` | Whole number | Rows prevented from loading. |
| `Duplicate Case Count` | Whole number | Duplicate Case IDs detected. |
| `Missing Required Count` | Whole number | Rows missing mandatory source values. |
| `Operational Records Preserved` | Boolean | Confirmation that persistent agent work was not overwritten. |
| `Error Details` | Multiline text | Validation rejection or technical failure information. |
| `Triggered By` | Text | User or process that initiated the refresh. |

A run cannot be marked `Succeeded` unless `Operational Records Preserved = Yes`.

### Workflow Events

This append-only table records the operational history of each case.

| Column | Type | Description |
|---|---|---|
| `Event ID` | Autonumber | Unique readable event identifier. |
| `Case` | Lookup | Case affected by the event. |
| `Event Type` | Choice | Assignment, dependency, completion, automation or reopening action. |
| `Event Timestamp` | Date and time | Time the action occurred. |
| `Actor Type` | Choice | `Agent`, `Manager`, `Senior` or `Automated Process`. |
| `Review Agent` | Lookup | Agent or manager responsible when applicable. |
| `Previous Status` | Choice | Case status before the action. |
| `New Status` | Choice | Case status after the action. |
| `Previous Assigned Agent` | Lookup | Assignment before the action. |
| `New Assigned Agent` | Lookup | Assignment after the action. |
| `Event Reason` | Multiline text | Required for manager and senior reopening; not required for assignment changes. |
| `Automation Run` | Lookup | Related automation run for automated events; blank otherwise. |
| `Previous Final Outcome` | Choice | Final outcome before reopening; blank when not applicable. |
| `Previous Completed By` | Text | Completion identity before reopening. |
| `Previous Completion Date` | Date | Completion date before reopening. |

Expected event types include assignment, unassignment, reassignment, notes updated, dependency raised, dependency resolved, manual completion, automated completion and manager reopening.

Existing workflow events cannot be edited or deleted through the prototype.

## Controlled Accounting Check — Phase 4

Notebook: `notebooks/12_controlled_accounting_check.ipynb`

This implementation extends the original accounting demonstration with persistent eligibility checks, guarded completion updates and transactional audit history.

### Matching Dates

- `First Identified Date` is the original case-identification date and remains unchanged by monthly refreshes.
- `Snapshot Date` is the latest accepted source snapshot containing the case.
- A matching refund must occur strictly after `First Identified Date` and on or before the accounting extract date.
- `Completion Date` records the matched refund’s processed date.
- `Last Updated Date` records the actual automation application timestamp.

### Decision Values

| Decision | Meaning |
|---|---|
| `Auto Complete` | Exactly one transaction satisfies every matching rule. |
| `Agent Review` | No transaction satisfies every matching rule. |
| `Ambiguous Match` | More than one transaction satisfies every matching rule. |

Approval does not guarantee application. The saved case is checked again before completion.

### Result Reasons

| Result Reason | Meaning |
|---|---|
| `Exact Match` | Exactly one transaction satisfies all rules. |
| `Multiple Valid Matches` | Multiple transactions satisfy all rules. |
| `No Accounting Transaction` | No transaction matches both policy and client identifiers. |
| `Amount Mismatch` | Transactions match the identifiers, but none matches the amount. |
| `Refund Not After Identification` | Amount-matching transactions do not occur after identification. |
| `Refund After Extract Date` | Amount-matching transactions occurring after identification are all later than the extract date. |

Reasons are evaluated in the order implemented by `explain_case_result`. Date reasons examine amount-matching transactions, ensuring separate transactions cannot combine to satisfy different rules.

`Refund Not After Identification` replaces the original implementation’s `Refund Not After Snapshot` terminology. `Refund After Extract Date` is an additional explicit reason.

### Audit Storage

- `automation_runs`: input fingerprint, extract date, rule version, run status and reconciliation counts.
- `automation_results`: one decision per run and case, including approval and application indicators.
- `workflow_events`: completion events saved atomically with applied updates.

Audit amounts are stored as integer pennies.

The combination of automation run ID and Case ID is unique. Repeating a successful run ID returns the original summary; a new logical check requires a new ID.

## Agent-Captured Investigation Reason

**Table:** Case Work
**Field:** Investigation Reason
**Type:** Choice
**Default:** Not Yet Determined
**Maintained by:** Assigned, authorised agent through controlled application updates

| Value | Meaning |
|---|---|
| Not Yet Determined | Investigation is ongoing or the cause cannot be established. |
| Payment Date Misunderstood | Investigation indicates confusion about payment or cover dates. |
| Refund Action Missed | A required refund action was not completed. |
| Waiting for Information | Missing information prevented progression. |
| Refund Mailbox Delay | Delay in the refund mailbox process. |
| Other | An established reason outside the controlled list. |
| No Refund Due | Investigation confirmed that no refund was required. Only saved when completing with the No Refund Due final outcome. |

### Rules

- Other requires explanatory notes.
- Completion with Not Yet Determined requires notes explaining that the financial outcome is established but the cause remains unknown.
- Investigation Reason and Final Outcome are separate fields.
- The reason is agent-recorded, not supplied by the monthly source report or inferred by automation.
- Refreshes and accounting automation must preserve it.
- Reason changes must be recorded in workflow history.
- Refund Action Missed is the operational counterpart of the historical synthetic Agent Forgot category; historical data remains unchanged.
- No Refund Due can only be saved during completion with the matching No Refund Due final outcome.
- It cannot be saved as an interim investigation reason or used with another final outcome.
- A genuine established investigation reason may still accompany a No Refund Due outcome.

### Data Quality Exceptions

One record represents one rejected source row within a refresh attempt. Multiple validation reasons may be recorded against that row.

| Column | Type | Description |
|---|---|---|
| `Exception ID` | Autonumber | Readable exception identifier. |
| `Refresh Run` | Lookup | Related Refresh Runs record. |
| `Source Row Number` | Whole number | Original CSV record position, including the heading row. |
| `Reported Case ID` | Text | Case identifier as received; may be blank or invalid. |
| `Rejection Reasons` | Multiline text | Validation failures preventing the row from loading. |
| `Original Row JSON` | Multiline text | Original source values retained for investigation. |
| `Recorded At` | Date and time | Time the exception was recorded. |
| `Review Status` | Choice | `Pending Review` or `Reviewed`; defaults to `Pending Review`. |

The combination of Refresh Run and Source Row Number forms an alternate key, preventing duplicate exception records within one attempt.

A Cases lookup is not mandatory because rejected records may have missing or invalid Case IDs.

Refresh processing creates exception records. Managers and approved seniors may mark them Reviewed. Original source values and rejection reasons remain read-only.

Reviewed does not mean the case was corrected or loaded. Corrected source data must pass a subsequent controlled refresh.

Review-status changes must be audited. Exception records cannot be deleted through the prototype application.