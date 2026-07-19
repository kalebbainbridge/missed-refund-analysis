# Data Dictionary

## Purpose

This document describes the fields used throughout the synthetic missed refund dataset.

The dataset has been designed to reflect the structure of a real operational insurance process while containing no genuine customer or company data.

This data dictionary supports the accompanying Python notebooks and Power BI dashboard by explaining the purpose and data type of each field.

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