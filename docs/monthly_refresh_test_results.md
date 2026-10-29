# Monthly Refresh Test Results

## Scope

Phase 3 implements and tests the refresh-safe monthly process locally using SQLite and entirely synthetic data.

Notebook: `notebooks/11_refresh_safe_monthly_process.ipynb`

Test files and databases: `data/prototype/refresh_testing/`

## Baseline

The starting population contained:

- 2,871 source cases and corresponding operational records
- 501 completed cases, including 500 automated completions
- Persistent assignments, notes, statuses, outcomes and completion information

## Test Results

| Test | Verified result |
|---|---|
| Valid July refresh | 12 rows received: 2 inserted and 10 updated |
| Operational preservation | All 2,871 existing operational records remained unchanged |
| New operational records | Both new cases received default Open records |
| Source reconciliation | The complete source table matched the expected result |
| Original dates | Existing First Identified Date values were preserved |
| Cases absent from input | Retained in the source table |
| Repeated valid input | 12 unchanged; no duplicate records |
| Invalid-row processing | 6 accepted and 6 quarantined with original values and rejection reasons |
| Missing required column | Attempt recorded as Rejected; case tables unchanged |
| Deliberate processing failure | Attempt recorded as Failed; all case changes rolled back |
| Out-of-order snapshot | June input rejected against July source data; rejection logged and both case tables unchanged |

The valid refresh produced 2,873 source cases and 2,873 operational records.

## Design Decisions

- Snapshot Date records the latest accepted snapshot containing a case.
- First Identified Date preserves the original identification date.
- Source refreshes do not modify existing operational records.
- Invalid rows are quarantined; valid rows in the same file may still be processed.
- Succeeded means accepted rows were processed successfully, not that every input row was valid.
- Each refresh attempt receives a separate audit record.
- Files that cannot be read fail before an audit record is created.

## Status and Follow-up

Phase 3 is complete for the local SQLite prototype.

The Power Platform implementation remains planned. Phase 4 must explicitly use the preserved identification date when adapting accounting matching and confirm the agreed date semantics.

The refresh tests demonstrate preservation of existing assignments and notes. They do not constitute concurrent-user or production-readiness testing.