# Current Business Process

```text
Customer Data System
        │
        ▼
Monthly Power BI Snapshot
        │
        ▼
Export to Excel
        │
        ▼
Debt Held Workbook
        │
        ▼
Agent reviews case
        │
        ├───────────────┐
        │               │
Refund required?       No refund required
        │               │
        ▼               ▼
Process refund       Mark No Action
        │               │
        └──────┬────────┘
               ▼
Update workbook
               │
               ▼
Case completed
```

## Pain Points
Monthly snapshot means some cases may already be weeks old
Manual import relies on user and delays operations

# Detailed operational workflow
1. Open the shared Debt Held workbook.
2. Select and assign one or more cases to work.
3. Copy the policy number from the workbook.
4. Search for the policy in the customer management system.
5. Review the policy notes and history.
6. Check whether a refund has already been processed.
7. Determine whether a refund is still due.
8. If a refund is required:
    - Process the refund.
    - Add an appropriate note if required.
    - Mark the case as Actioned in the workbook.
9. If no further action is required:
    - Mark the case as No Action in the workbook.
10. Move on to the next case until all assigned work has been completed. 
