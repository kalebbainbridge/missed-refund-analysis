# Data Model

## Purpose

This document describes the structure of the synthetic dataset used throughout the project.

The aim is to recreate the Debt Held operational workflow while protecting confidential company and customer information.

---

# Dataset 1 - Monthly Power BI Snapshot

This dataset represents the monthly snapshot exported from Power BI.

| Column | Type | Description |
|---------|------|-------------|
| Case ID | Text | Unique case identifier |
| Policy Number | Text | Anonymised policy identifier |
| Client Number | Text | Anonymised customer identifier |
| Outstanding Amount | Currency | Amount outstanding |
| Cancellation Status | Category | Cancelled / Void |
| Cancelling Department | Category | Department that cancelled the policy |
| Cancelling Agent | Category | Agent who cancelled the policy |

---

## Cancelling department
- Retentions
- Customer Service
- Claims
- Complaints

---


# Dataset 2 - Operational Tracker

This dataset represents the Excel workbook used by agents.

| Column | Type | Description |
|---------|------|-------------|
| Case ID | Text | Links to snapshot |
| Agent Working | Text | Agent currently working the case |
| Outcome | Category | Actioned / N/A / Raised |
| Comments | Text | Operational notes |
| Refund Processed Date | Date | Date refund completed |
|Customer Chased | Category | Has the customer contacted the business to chase a refund (y/n) |
| Root Cause | Category | Reason the refund appeared on the report |

---
## Root Cause Categories
- Agent oversight
- Business Rule misunderstanding
- Refund mailbox delay
- awaiting additional information

---
## Processing Agent Assumptions
- Only a small number of agents are trained to work the Debt Held workbook
- The agents working the workbook may change each month
- Work is not divided equally as agents may not be allocated the same amount of time on the workbool
- Cases remain unassigned until an agent begins reviewing them 
- Synthetic agent labels will be used
---
## Outcome Categories
### Actioned 
The case has been reviewed and the agent workng the workbook has processed the refund.
### NA
The case does not reqire furter action
Examples include: 
- No refund due 
- Refund already processed before review



# Calculated Fields

These fields will be created during the analysis.

| Field | Description |
|-------|-------------|
| Days Outstanding | Number of days between snapshot and completion |
| Refund Required | Yes / No |
| Refund Missed | Yes / No |
| Root Cause | Primary reason the case appeared on the report.

---

# Business Rules

- Each case ID must be unique 
- Outstanding amount must be greater than £0
- Some outstanding balances do not require a refund 
- One client may hold more than one policy
- Each policy belongs to one client
- A client number may therefore appear against multiple policy numbers


---

# Assumptions
Because this project uses synthetic data, several realisti assumptions have been made to recreate the operational process.
- Outstanstanding refund values range from £0.50 to approximately £300
- Most refund values fall between £5 and £150
- The workbook is typically worked by 1 to 2 agents.
- Cases may have already been resolved if the customer contacted the business before the monthly workbook was reviewed.
- Not every outstanding balance results in a refund

## Root Cause Distribution

Based on operational experience, the estimated distribution of root causes is:

| Root Cause | Estimated Frequency |
|------------|--------------------:|
| Payment Date Misunderstood | 55% |
| Agent Forgot | 20% |
| Waiting for Information | 15% |
| Refund Mailbox Delay | 10% |

These percentages are based on business knowledge and are used to generate realistic synthetic data.

