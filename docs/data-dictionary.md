# Data Dictionary

## Purpose

This document describes the fields used throughout the synthetic missed refund dataset.

The dataset has been designed to reflect the structure of a real operational insurance process while containing no genuine customer or company data.

This data dictionary supports the accompanying Python notebooks and Power BI dashboard by explaining the purpose and data type of each field.


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
| Cancelling Department | Category | Department that processed the cancellation | Based on real process | 
| Cancelling Agent | Category | Agent who processed the cancellation | Synthetic |
| Refund missed | Boolean | Whether the refund was initially missed | Synthetic |
| Refund Type | Category | Cancellation reason | Based on real process | 


## Notes

- All customer and policy information has been anonymised or synthetically generated.
- The dataset is intended for portfolio demonstration purposes only.
- Business rules were based on a real operational workflow but have been simplified where appropriate.