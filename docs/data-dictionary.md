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
| `Agent Working` | Text | Synthetic identifier for the trained analyst who reviewed the case. |
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

- `Actioned` — the reviewing analyst processed the refund.
- `No Action` — the refund had already been processed or no refund was due.
- `Raised` — the case required senior review or action by another department.

## Notes

- All identifiers and records are entirely synthetic; no real customer information has been anonymised or included.
- The dataset is intended only for portfolio demonstration.
- The fields and relationships are informed by operational experience but have been simplified for this project.