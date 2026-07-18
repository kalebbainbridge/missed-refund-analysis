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
 business.
- All case IDs and policy numbers are unique within the current dataset.

## Planned Operational Extension

The next project phase will introduce a weekly case-status dataset.

Unlike the current dataset, a case may appear on multiple weekly reporting dates while it remains unresolved. The combination of `Case ID` and `Reporting Date` will uniquely identify each weekly status record.

The detailed design is documented in `operational_workflow.md`.