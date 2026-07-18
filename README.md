# Missed Refund Analysis Dashboard

An end-to-end data analytics portfolio project using Python, SQL and Power BI to analyse a synthetic insurance operations dataset.

## Overview

This project recreates a manual refund tracking process using synthetic data based on a real operational workflow within the insurance industry.

The aim is to investigate the characteristics of outstanding balances and identify opportunities to improve refund processing, reporting and operational efficiency.

No real customer or company data is used in this project.

---

## Business Problem

The Debt Held process relies on a monthly Power BI snapshot that is exported into an Excel workbook. Agents manually review each case, determine whether a refund is required and update the workbook as work progresses.

This project investigates the operational process using synthetic data to answer business questions and propose process improvements.

---

## Project Goals

- Understand the Debt Held workflow
- Create a realistic synthetic dataset
- Analyse refund processing performance
- Build an interactive Power BI dashboard
- Recommend improvements to the process

---

## Dashboard Preview

![Missed Refund Dashboard](images/dashboard-overview.png)

The Power BI dashboard provides an executive view of the synthetic operational dataset, allowing users to explore trends, identify operational issues and filter results by month, department and refund type.

Key dashboard features include:

- Executive KPI summary
- Monthly case volume trends
- Case outcome distribution
- Root cause analysis
- Department-level analysis
- Interactive slicers

---

## Key Findings

Analysis of the synthetic dataset identified several operational patterns:

- Most cases were successfully actioned, indicating the refund process generally functions effectively.
- Payment Date Misunderstood was the most common root cause of missed refunds, suggesting additional training could reduce processing errors.
- The Retentions department generated the highest number of missed refund cases due to its larger volume of policy cancellations.
- The dashboard highlighted monthly fluctuations in case volumes, allowing operational teams to identify periods of increased workload.
- Interactive filtering enables managers to investigate trends by month, department and refund type, supporting data-driven operational decisions.
---

## Repository Structure

```text
DebtHeld-MissedRefundAnalysis/
│
├── dashboard/
│   └── Missed_Refund_Analysis_Dashboard.pbix
│
├── data/
│   ├── raw/              # Synthetic monthly datasets
│   └── reference/        # Supporting reference data
│
├── notebooks/
│   ├── 01_generate_data.ipynb
│   ├── 02_exploratory_analysis.ipynb
│   ├── 03_business_analysis.ipynb
│   └── 04_powerbi_dashboard.ipynb
│
├── images/
│   └── dashboard-overview.png
│
├── docs/
│
├── sql/
│
└── README.md
```
---

## Skills Demonstrated

This project demonstrates practical experience with:

- **Python** – generating and preparing synthetic datasets
- **Pandas** – data manipulation and transformation
- **Power BI** – interactive dashboard development
- **DAX** – creating KPIs and business measures
- **Data Visualisation** – presenting operational insights through charts and dashboards
- **Business Analysis** – identifying trends, root causes and improvement opportunities
- **Data Modelling** – structuring data for reporting and analysis
- **Git & GitHub** – version control and project documentation

---

## Tools

- Python
- Pandas
- SQL
- Power BI
- Git & GitHub
- VS Code

## About the Data

This project does not contain real customer or company data.

The dataset is entirely synthetic and has been generated using business rules based on operational experience within an insurance environment.

The distributions and relationships are designed to simulate realistic patterns rather than reproduce actual company data.

## Why Synthetic Data?

This project was inspired by a genuine operational process encountered in an insurance environment.

To protect customer privacy and confidential business information, all data used in this repository is synthetically generated using documented business rules and operational assumptions.

The aim is to demonstrate analytical thinking, data modelling and reporting techniques rather than reproduce production data.