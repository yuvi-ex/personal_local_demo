# Churn Insights — hand-authored dashboard notes

Redesigned to match this project's shared dashboard design system (see
employee-insights/app.py for the original design tokens/components this was
forked from): hero header, filter row (Contract checklist + high-risk toggle),
dark "KEY INSIGHT" callout, 6-card KPI row, two side-by-side bar charts, a
full-width predicted-vs-actual comparison chart, and a styled highest-risk
customer table with color-coded risk badges.

Business SQL (all filter-aware via contract_all/contract/high_risk_only params):
- filter_options.sql: distinct Contract values for the filter checklist
- summary.sql: KPI row source (customer count, high-risk count, avg predicted
  risk, actual churn rate for calibration comparison)
- risk_by_contract.sql: average predicted risk % per contract type
- count_by_risk_band.sql: customer counts bucketed into 10%-wide risk bands
- predicted_vs_actual_by_contract.sql: predicted vs. actual churn rate side by
  side, per contract — the calibration story, segmented
- top_risk_customers.sql: the 25 highest predicted-risk customers

Source: STARTER_KIT.CHURN_SCORES, scored by the STARTER_KIT.predict_churn UDF
(RandomForestClassifier over tenure/MonthlyCharges/Contract).
