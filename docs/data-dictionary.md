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
| `Snapshot Date` | Date | Month-end date of the simulated Power BI snapshot. |
| `Outstanding Amount` | Decimal | Outstanding balance requiring investigation, measured in pounds sterling. |
| `Cancellation Status` | Category | Whether the policy was recorded as `Cancelled` or `Void`. |
| `Cancelling Department` | Category | Department responsible for processing the policy cancellation. |
| `Cancelling Agent` | Text | Synthetic identifier for the agent who processed the cancellation. |
| `Agent Working` | Text | Synthetic identifier for the trained agent who reviewed the case. |
| `Refund Type` | Category | Cancellation scenario associated with the potential refund. |
| `Root Cause` | Category | Simulated reason the refund remained outstanding. |
| `Customer Contacted` | Category | Whether the customer had contacted the business before the case was reviewed. |
| `Outcome` | Category | Result of the case review: `Actioned`, `No Action` or `Raised`. |

## Synthetic Analytical Dataset

The main analytical dataset contains both simulated source attributes and deliberately generated analytical enrichment.

`Refund Type`, `Root Cause`, `Customer Contacted`, `Agent Working` and `Outcome` support the Python, SQL and Power BI analysis. They are informed by operational experience but are not presented as fields supplied directly by the real monthly discrepancy report.
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