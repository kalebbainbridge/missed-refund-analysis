# Missed Refund Analysis and Process Improvement

An end-to-end data and process-improvement portfolio project using Python, Pandas, SQLite, SQL, Excel, Power Query, Power BI and Streamlit to analyse and improve a synthetic insurance operations workflow.

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
- Design a refresh-safe data model that preserves agent notes and operational updates
- Automate checks for refunds already processed
- Build a working shared operational and agent workflow prototype

---
## Working Workflow Prototype

A working Streamlit prototype demonstrates how the missed-refund process could move from a static Power BI export and shared Excel workbook to a controlled SQLite-backed workflow.

The prototype provides two connected interfaces:

- **Operational Control** — monitors open cases, dependencies, completed cases and the workflow audit trail.
- **Agent Case Review** — allows agents to find, assign, investigate, refer and complete cases through a shared queue.

The workflow includes:

- shared case assignment
- agent notes
- controlled final outcomes
- senior-review and other-department dependencies
- automated accounting-check results
- completed-case tracking
- timestamped workflow events
- protection against conflicting updates

The application uses entirely synthetic data and simulates authentication through agent selection.

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

- The dataset contains **2,871 cases** with a combined outstanding value of **£160,215.80**.
- Approximately **82% of reviewed cases** resulted in the agent processing a refund, indicating substantial missed-refund exposure within the simulated workload.
- `Payment Date Misunderstood` was the leading root cause, accounting for approximately **46% of cases**.
- Following the simulated training intervention, payment-date misunderstandings decreased from **55.7% to 40.2%**.
- After the simulated new starters joined, this increased to **44.2%**, demonstrating how onboarding changes could be monitored.
- Refund mailbox delays represented **16.8% of cases during December and January**, compared with **9.5% in other months**.
- Retentions and Customer Service generated approximately **78% of missed-refund cases**, although total cancellation volumes would be required to compare departmental error rates fairly.

These findings demonstrate analytical methods using intentionally generated scenarios and do not represent the performance of a real organisation.

---

## Repository Structure

```text
missed-refund-analysis/
│
├── app/
│   ├── Operational_Control.py
│   ├── init_database.py
│   └── pages/
│       └── 1_Agent_Case_Review.py
│
├── dashboard/
│   └── Missed_Refund_Analysis_Dashboard.pbix
│
├── data/
│   ├── accounting/
│   │   ├── automated_refund_check_results.csv
│   │   └── refund_transactions.csv
│   ├── operational/
│   │   ├── agent_case_workbook.xlsx
│   │   ├── agent_updates.csv
│   │   └── source_cases.csv
│   ├── raw/                         # Synthetic monthly snapshots
│   ├── reference/                   # Supporting category data
│   ├── weekly/                      # Weekly operational simulation
│   └── combined_missed_refunds.csv
│
├── docs/
│   ├── business-process.md
│   ├── business_profile.md
│   ├── business_questions.md
│   ├── business_rules.md
│   ├── data-dictionary.md
│   ├── data_model.md
│   ├── operational_workflow.md
│   └── project-charter.md
│
├── images/
│   └── dashboard-overview.png
│
├── notebooks/
│   ├── 01_generate_powerbi_snapshot.ipynb
│   ├── 02_validate_snapshot.ipynb
│   ├── 03_exploratory_analysis.ipynb
│   ├── 04_process_improvements.ipynb
│   ├── 05_create_sql_database.ipynb
│   ├── 06_sql_business_analysis.ipynb
│   ├── 07_generate_weekly_status_feed.ipynb
│   ├── 08_create_refresh_safe_tables.ipynb
│   ├── 09_create_agent_workbook.ipynb
│   └── 10_auto_check_processed_refunds.ipynb
│
├── sql/                             # Generated analytical SQLite database
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Running the Project

### Install the dependencies

Create and activate a virtual environment, then install the required packages:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Initialise the workflow prototype

Build the local SQLite prototype database from the synthetic CSV files:

```powershell
python app/init_database.py
```

This creates:

```text
data/prototype/missed_refunds_prototype.db
```

Running the initialisation script again resets prototype case activity and the workflow audit trail.

### Launch the Streamlit application

```powershell
python -m streamlit run app/Operational_Control.py
```

The application provides:

- an Operational Control page for backlog, dependency, completion and audit monitoring
- an Agent Case Review page for shared case assignment and processing

Agent selection simulates authentication. All displayed information is synthetic.

### Run the analytical notebooks

Start Jupyter from the notebooks directory:

```powershell
cd notebooks
python -m jupyterlab
```

Run the notebooks in numerical order. They generate and validate the synthetic source data, analytical outputs, weekly operational feeds, refresh-safe tables, agent workbook and automated accounting checks.

---


## Skills Demonstrated

This project demonstrates practical experience with:

- **Python** – generating and preparing synthetic datasets
- **Pandas** – data manipulation and transformation
- **SQL & SQLite** – creating a reproducible database, querying operational data, using aggregation, grouping, `CASE` statements and conditional calculations
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

## Refresh-Safe Agent Workbook

The project includes a simulated Excel workbook for agents reviewing missed-refund cases.

Fresh source data is kept separate from persistent agent updates. Notebook `09_create_agent_workbook.ipynb` merges them by `Case ID`, preserves existing workbook edits and synchronises agent-entered values back to the update table.

The workbook includes:

- essential policy, client, balance and cancellation information
- visually highlighted editable fields
- controlled dropdown lists for agents, statuses and outcomes
- automatic completion ownership and dates
- protection against source refreshes overwriting agent notes