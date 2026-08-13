WITH FILTERED AS (
  SELECT *
  FROM "STARTER_KIT"."EMPLOYEES"
  WHERE ({department_all!d} = 1 OR "department" IN ({department!s}))
    AND ({active_only!d} = 0 OR "is_active" = TRUE)
)
SELECT
    "department" AS "DEPARTMENT",
    CAST(COUNT(*) AS DOUBLE) AS "HEADCOUNT",
    CAST(AVG("salary") AS DOUBLE) AS "AVG_SALARY",
    SUM(CASE WHEN "is_active" THEN 1 ELSE 0 END) AS "ACTIVE_COUNT",
    CAST(AVG(DAYS_BETWEEN(CURRENT_DATE, "hire_date")) / 365.25 AS DOUBLE) AS "AVG_TENURE_YEARS",
    MIN("hire_date") AS "EARLIEST_HIRE"
FROM FILTERED
GROUP BY "department"
ORDER BY "HEADCOUNT" DESC
