WITH FILTERED AS (
  SELECT *
  FROM "STARTER_KIT"."EMPLOYEES"
  WHERE ({department_all!d} = 1 OR "department" IN ({department!s}))
    AND ({active_only!d} = 0 OR "is_active" = TRUE)
)
SELECT
    CAST(YEAR("hire_date") AS VARCHAR(4)) AS "LABEL",
    CAST(COUNT(*) AS DOUBLE) AS "VALUE"
FROM FILTERED
GROUP BY YEAR("hire_date")
ORDER BY YEAR("hire_date")
