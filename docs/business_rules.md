# Business Rules

## Purpose

This document records the business assumptions used to generate the synthetic Debt Held dataset. The rules are based on operational experience and are designed to create realistic data for analysis.

---

# Root Cause Distribution

Estimated distribution of missed refund root causes.

| Root Cause | Frequency |
|------------|----------:|
| Payment Date Misunderstood | 55% |
| Agent Forgot | 20% |
| Waiting for Information | 15% |
| Refund Mailbox Delay | 10% |

---

# Customer Contact

Probability that a customer has already contacted the business based on the root cause.

| Root Cause | Customer Contact Rate |
|------------|----------------------:|
| Agent Forgot | 45% |
| Waiting for Information | 30% |
| Refund Mailbox Delay | 25% |
| Payment Date Misunderstood | 10% |

---

# Outcome Distribution

Estimated outcome after investigation.

| Outcome | Frequency |
|---------|----------:|
| Actioned | 70% |
| N/A | 25% |
| Raised | 5% |

---

# Cancellation Status

Typical distribution of cancellation status.

| Status | Frequency |
|--------|----------:|
| Cancelled | 70% |
| Void | 30% |

---

# Cancelling Departments

Departments that can cancel policies.

- Retentions
- Customer Service
- Claims
- Complaints

Approximate workload distribution:

| Department | Relative Volume |
|------------|----------------:|
| Retentions | 30 |
| Customer Service | 25 |
| Claims | 10 |
| Complaints | 5 |

---

# Debt Held Process

- Power BI generates a monthly snapshot of outstanding balances.
- The report is exported into a shared workbook.
- Around two colleagues are trained to process Debt Held cases.
- Trained colleagues manually claim cases from the workbook.
- Cases are generally worked from the top of the workbook rather than prioritised by root cause.
- Once a case is claimed it is usually completed immediately unless additional advice or information is required.

---

# Business Assumptions

- Minimum outstanding amount: £0.50
- Typical refund range: £10.00–£100.00
- Maximum refund generated: £300.00
- A customer may hold multiple policies.
- Customer contact is influenced by the underlying root cause.
- This project uses synthetic data generated from operational business knowledge.

# Refund Type Distribution

Estimated distribution of refund types within the Debt Held process.

| Refund Type | Frequency |
|-------------|----------:|
| Death of Pet | 55% |
| Cancellation Before Premium Due | 25% |
| Cancellation from Renewal (Void) | 20% |

# Relationships Between Refund Type, Root Cause and Outcome

The synthetic data should reflect the following operational patterns:

- Death of Pet cancellations are most commonly associated with Payment Date Misunderstood.
- Cancellation from Renewal (Void) cases are most commonly associated with Agent Forgot.
- Cancellation Before Premium Due cases are more likely to result in an N/A outcome because the source system may not always distinguish between the cancellation date and the final day of cover.
- Refund Type, Root Cause and Outcome should therefore not be generated independently.

## Outcome by Refund Type

| Refund Type | Actioned | N/A | Raised |
|-------------|---------:|----:|-------:|
| Death of Pet | 95% | 4% | 1% |
| Cancellation Before Premium Due | 65% | 32% | 3% |
| Cancellation from Renewal (Void) | 70% | 28% | 2% |

## Cancellation Status by Refund Type

- Cancellation from Renewal (Void) cases can only have a cancellation status of `Void`.
- Cancellation Before Premium Due cases can only have a cancellation status of `Cancelled`.
- Death of Pet cases may have either `Cancelled` or `Void` status.