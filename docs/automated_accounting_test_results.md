# Controlled Accounting Check — Test Results

## Scope

Notebook: `notebooks/12_controlled_accounting_check.ipynb`

The implementation uses isolated SQLite test databases and entirely synthetic accounting data. It does not process real refunds.

## Matching Rules

Automatic completion requires:

- An unresolved operational case.
- Matching policy and client identifiers.
- An exact amount match, compared in integer pennies.
- A refund date strictly after First Identified Date.
- A refund date on or before the accounting extract date.
- Exactly one transaction satisfying all rules.

Previously completed cases are excluded regardless of who completed them. Future-dated transactions are retained unchanged and cannot qualify.

## Scenario Results

Ten controlled scenarios produced:

- 2 automatic-completion approvals.
- 7 agent-review decisions.
- 1 ambiguous-match decision.

Tests covered exact matches, amount mismatches, pre-identification and same-day refunds, multiple valid matches, missing transactions, future transactions, extract-date boundary matching, incorrect client identifiers and rules matching different transactions.

## Application and Audit Tests

Verified that:

- The fresh-baseline runner checked 2,372 unresolved cases and excluded 501 completed cases.
- Only DH000001 and DH000008 were completed.
- Completion details and both history events were correct.
- Existing completions, assignments and notes were preserved.
- Repeating a successful run ID returned its saved summary without database changes.
- Newer agent notes and agent completions blocked stale approvals in controlled guard tests.
- Duplicate transaction IDs caused a retained Rejected run record.
- An intentional event-write failure rolled back completions and case-level results while retaining a Failed run record.

## Date and Audit Semantics

First Identified Date controls the lower matching boundary. Snapshot Date remains the latest source reporting date.

Completion Date records the matched refund’s processed date. Last Updated Date records the actual automation application timestamp.

Approval and successful application are recorded separately.

## Limitations and Remaining Work

- Representative Power Automate tests remain outstanding.
- Conflict tests simulated intervening changes; they were not simultaneous multi-user tests.
- Files that cannot be read fail before a run record is created.
- A successful run ID returns its original results. A new logical check requires a new run ID.
- The notebook contains one-off setup and deliberate failure tests and should not be executed using Run All against populated test databases.
- Production authentication, deployment and Dataverse integration are outside this local test scope.

## Status

Local Python/SQLite implementation and the documented tests are complete. Phase 4 remains in progress pending representative Power Automate testing.