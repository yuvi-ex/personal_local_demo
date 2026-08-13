WITH FILTERED AS (
  SELECT *
  FROM "STARTER_KIT"."CHURN_SCORES"
  WHERE ({contract_all!d} = 1 OR "Contract" IN ({contract!s}))
    AND ({high_risk_only!d} = 0 OR "CHURN_PROBABILITY" >= 0.5)
)
SELECT
    "Contract" AS "LABEL",
    CAST(AVG("CHURN_PROBABILITY") * 100 AS DOUBLE) AS "VALUE"
FROM FILTERED
GROUP BY "Contract"
ORDER BY "VALUE" DESC
