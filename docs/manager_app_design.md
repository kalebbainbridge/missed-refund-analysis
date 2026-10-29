# Manager and Senior Application Design

## Status

Screen design only. Implementation and permission testing remain pending.

## Workload Screen

Provides:

- Shared unresolved-case queue.
- Assigned and unassigned filters.
- Workload by agent.
- Search by case, policy or client identifier.
- Access to full case details and history.

Managers and authorised seniors can select one or more unresolved cases and:

- Unassign them to the shared queue.
- Reassign them directly to an eligible agent.

No reason is required for assignment changes.

Each action preserves notes, investigation reasons and dependency information. History automatically records the actor, timestamp and previous/new assignment.

For multiple selections, the application reports individual successes and blocked actions. Cases changed since selection must be refreshed rather than overwritten.

## Dependencies Screen

Displays cases awaiting senior review or another department, including:

- Assigned agent.
- Dependency type and owner.
- Raised date and target date.
- Dependency details.
- Overdue indicator.

Unassigned dependency cases remain visible here and retain their dependency status.

## Exceptions Screen

Provides visibility of:

- Ambiguous accounting matches.
- Other accounting-review results.
- Rejected source records and validation reasons.

Visibility does not grant permission to force an automated match or modify source and accounting information. Exception-resolution actions require a separate design.

## History and Runs Screen

Provides read-only access to:

- Case workflow history.
- Source refresh attempts and row counts.
- Accounting runs, decisions and applied/skipped totals.
- Rejection and failure details.

## Completed Cases

Completed cases are read-only during normal use.

Only an authorised manager or senior may reopen a completed case. Reopening requires a reason and preserves the previous completion details in history.



## Reporting Boundary

The application supports operational oversight and actions. Power BI provides trends, performance measures and management analysis.

## Planned Manager and Senior Screen Tests

These tests are specified but have not yet been executed in Power Apps.

- Managers and authorised seniors can view shared and agent-specific queues.
- Both roles can unassign unresolved cases without entering a reason.
- Unassigned open cases return to the available queue.
- Unassigned dependency cases retain their status and remain visible.
- Both roles can reassign unresolved cases to eligible agents.
- Ineligible agents cannot receive assignments.
- Assignment changes preserve notes, investigation reasons and dependencies.
- History records the actor, timestamp and previous/new assignment automatically.
- Bulk actions report successful and blocked changes individually.
- Stale updates cannot overwrite newer work.
- Completed cases cannot be unassigned or reassigned.
- Seniors cannot reopen completed cases.
- Managers must provide a reason to reopen a completed case.
- Reopening returns the case to Open and clears current completion fields.
- Previous completion details remain available in history.
- Exception and run-history views do not permit uncontrolled edits.
- No business or audit records can be deleted through the application.
## Data-Quality Exception Review

Managers and approved seniors can:

- Filter exceptions by refresh run and review status.
- View the source filename, row number and reported Case ID.
- Read validation reasons and original source values.
- Mark an exception Reviewed.

Review does not modify the original rejection evidence or load a case. Corrected input must pass a subsequent controlled refresh.

Review-status changes must record who changed the status and when. This requires exception-level auditing because an invalid row may not link to an existing case.

### Planned Tests

- Missing or invalid Case IDs do not prevent exception capture.
- One refresh attempt cannot contain duplicate exception records for the same source row.
- Managers and approved seniors can mark exceptions Reviewed.
- Agents cannot update review status.
- Original values and rejection reasons remain read-only.
- Marking Reviewed does not create or change a case.
- Review-status changes retain actor and timestamp evidence.