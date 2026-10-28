# Power Automate — Representative Accounting Tests

## Status

Planned; not executed. The development environment remains inactive pending preparation and licensing checks.

The Python/SQLite implementation provides the reference behaviour. It does not prove that equivalent Power Automate controls have been implemented.

## Proposed Test Flow

1. Manually trigger a synthetic accounting check.
2. Record the run identifier, extract date and rule version.
3. Load unresolved cases and validated accounting transactions.
4. Evaluate identifiers, exact amounts, identification dates and extract-date limits.
5. Record each decision and reason.
6. Apply approved completions using backend-enforced conflict protection.
7. Record completion events and reconcile run totals.
8. Record failures without leaving partial completions.

The mechanism providing atomic updates and conflict protection must be established before implementation. A separate read followed by an unconditional update is insufficient.

## Representative Tests

| Scenario | Expected behaviour |
|---|---|
| One exact valid match | Complete the case and record the result and event |
| Amount mismatch | Retain for agent review |
| Refund on or before identification | Retain for agent review |
| Refund after extract date | Retain for agent review |
| Multiple valid matches | Record ambiguity; do not complete |
| Previously completed case | Exclude from matching |
| Agent changes case after approval | Block stale application |
| Repeat successful logical run | No duplicate completion, result or event |
| Failure during application | No partial completion; retain failure evidence |

## Activation Gate

Before activating the environment:

- Finish agent and manager screen designs.
- Confirm available licensing, expiry and potential charges.
- Confirm backend support for required controls.
- Prepare synthetic inputs and expected results.
- Define the evidence to capture for each test.