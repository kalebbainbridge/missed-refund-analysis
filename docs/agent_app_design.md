# Agent Application Design

## Status

Screen design only. Power Platform implementation and permission testing remain pending.

## Agent Journey

Available Cases → Assign to me → My Queue → Case Details

Agents claim cases before working them from their own queue.

## Available Cases

Shows open, unassigned cases.

- Search by case, policy or client identifier.
- Select one or more cases and choose Assign to me.
- Validate each assignment when saved.
- Only authorised, eligible agents may claim cases.
- A case must still be open and unassigned.
- For multiple selections, report which assignments succeeded and which were blocked.

## My Queue

Shows cases assigned to the current agent, including open cases and cases awaiting a dependency.

Displays case identifier, outstanding amount, first identified date, status and dependency summary.

Opening a case displays its full details.

## Case Details

Displays source information, relevant accounting results and workflow history.

Permitted actions include:

- Add investigation notes.
- Record or resolve a dependency.
- Record a structured investigation reason.
- Complete the case with a controlled final outcome.
- Release the assignment when unable to continue.

Source and accounting information are read-only. Updates must not overwrite a newer change or a completed case.

## Completed Work

A separate read-only view provides access to completed cases and their history.

## Manager and Senior Assignment Controls

Managers and authorised senior reviewers may unassign or reassign unresolved cases without entering a reason.

- Unassigning removes the case from the agent’s queue and returns it to the shared queue.
- Open, unassigned cases are available for agents to claim.
- Cases awaiting a dependency retain that status and appear in the shared dependency view.
- Reassignment moves a case directly to another eligible agent’s queue.
- Notes, investigation reasons and dependency details are preserved.
- History automatically records the actor, timestamp and previous/new assignment.
- Assignment changes must not overwrite newer updates.
- Completed cases cannot be unassigned or reassigned.
- Reopening a completed case remains a separate manager or approved senior action requiring a reason.

## Permission Follow-up

Senior-reviewer assignment authority must be added to the permission design and tested. It does not automatically grant other manager permissions.

## Case Details Screen

Opened from My Queue.

### Information Sections

| Section | Contents |
|---|---|
| Case summary | Case ID, status, assigned agent, outstanding amount and first identified date |
| Source details — read-only | Policy/client identifiers, latest snapshot date, cancellation status, cancelling department and agent |
| Accounting check — read-only | Latest decision, reason, check timestamp and confirmed transaction details where available |
| Investigation | Agent notes and structured investigation reason |
| Dependency | Type, owner, raised date, target date and details |
| History — read-only | Assignment changes, note updates, dependencies and completions |

### Agent Actions

- **Save notes:** retain the update and record a history event.
- **Raise dependency:** require type, owner, target date and details. Set status to Awaiting Dependency and retain assignment.
- **Resolve dependency:** require a resolution note, preserve dependency history and return the case to Open.
- **Complete case:** require a controlled final outcome and no unresolved dependency. Record completion identity and timestamp automatically.
- **Release case:** clear assignment while preserving notes and dependency details.

Permitted final outcomes are Refund Processed, Refund Already Processed and No Refund Due.

### Save Protection

Every action must verify that:

- The agent remains authorised.
- The case remains assigned to that agent.
- The case is not completed.
- The record has not changed since it was loaded.

A blocked save must explain that the case changed and prompt the agent to refresh. It must not silently overwrite newer work.

### Required Model Addition

Case Work requires an Investigation Reason choice field.

It defaults to Not Yet Determined. Its controlled choices must be agreed before implementation.

This is agent-recorded information, distinct from source fields and the historical synthetic Root Cause field. Automation must not infer or overwrite it.

## Planned Agent Screen Tests

These tests are specified but have not yet been executed in Power Apps.

- An authorised agent claims an available case, which moves to My Queue.
- Multiple selections report successful and blocked assignments individually.
- Two agents cannot claim the same case.
- An agent cannot edit another agent’s case.
- My Queue shows assigned open and dependency cases.
- Source and accounting details are read-only.
- Notes and investigation reasons survive source refreshes.
- Other investigation reasons require explanatory notes.
- Completion with Not Yet Determined requires an explanation.
- A dependency requires type, owner, target date and details.
- Resolving a dependency retains its history and returns the case to Open.
- Completion requires a final outcome and no unresolved dependency.
- Releasing a case preserves notes, investigation reason and dependency details.
- Manager or senior unassignment removes the case from the agent’s queue.
- A stale agent save after reassignment or unassignment is blocked.
- Completed cases are read-only.