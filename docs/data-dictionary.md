# Data Dictionary

| Column | Type | Description | Source |
|---------|------|-------------|--------|
| Case ID | Text | Unique case identifier | Synthetic |
| Policy Number | Text | Anonymised policy ID | Based on real process |
| Client Number | Text | Anonymised client ID | Based on real process |
| Snapshot Month | Date | Month the Power BI report was created | Synthetic |
| Amount Outstanding | Decimal | Outstanding balance to review | Based on real process |
| Cancellation Status | Category | Whether the policy is cancelled or void| Based on real process |
| Agent Working | Category | Agent assigned to the case | Synthetic |
| Comments | Text | Operational notes added by the agent | Synthetic |
| Outcome | Category | Actioned or N/A | Based on real process | 
Cancelling Department | Category | Department that processed the cancellation
Cancelling Agent | Category | Agent who processed the cancellation
Refund missed | Boolean | Whether the refund was initially missed
Refund Type | Category | Cancellation reason, 
