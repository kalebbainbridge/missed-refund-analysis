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