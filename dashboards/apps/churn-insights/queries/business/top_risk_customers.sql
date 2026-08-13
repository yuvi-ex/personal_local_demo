WITH FILTERED AS (
  SELECT *
  FROM "STARTER_KIT"."CHURN_SCORES"
  WHERE ({contract_all!d} = 1 OR "Contract" IN ({contract!s}))
    AND ({high_risk_only!d} = 0 OR "CHURN_PROBABILITY" >= 0.5)
)
SELECT "customerID" AS "CUSTOMER_ID",
       "tenure" AS "TENURE_MONTHS",
       "MonthlyCharges" AS "MONTHLY_CHARGES",
       "Contract" AS "CONTRACT",
       "Churn" AS "ACTUAL_CHURN",
       CAST(ROUND("CHURN_PROBABILITY" * 100, 1) AS DOUBLE) AS "CHURN_RISK_PCT"
FROM FILTERED
ORDER BY "CHURN_PROBABILITY" DESC
LIMIT 25
