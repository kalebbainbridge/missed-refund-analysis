# Simulated Operational Workflow

## Purpose

This phase extends the missed-refund analysis from a static monthly snapshot into a simulated operational reporting workflow.

The workflow will model how missed-refund cases change over time, including:

- new cases entering the backlog
- cases remaining open while awaiting review
- customers making contact
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
- Cases awaiting senior review or another department may retain a named owner or responsible team for follow-up.

Once completed, the case will appear as `Completed` in that reporting week and will not appear in later weekly backlog snapshots.

## Weekly Status Feed Design

### Identifiers and Dates

| Field | Description |
|---|---|
| `Case ID` | Unique identifier for the missed-refund case. |
| `Reporting Date` | Weekly date on which the case status is recorded. |
| `Source Snapshot Date` | Monthly snapshot from which the case originated. |
| `Date Added` | Simulated date the case entered the operational workflow. |
| `Completion Date` | Date the case was resolved; blank while unresolved. |
| `Case Age Days` | Number of days between `Date Added` and the reporting date, or completion date if resolved. |

The combination of `Case ID` and `Reporting Date` will uniquely identify each row in the weekly feed.