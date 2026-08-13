WITH FILTERED AS (
  SELECT *
  FROM "STARTER_KIT"."EMPLOYEES"
  WHERE ({department_all!d} = 1 OR "department" IN ({department!s}))
    AND ({active_only!d} = 0 OR "is_active" = TRUE)
)
SELECT
    "department" AS "LABEL",
    CAST(AVG("salary") AS DOUBLE) AS "VALUE"
FROM FILTERED
GROUP BY "department"
ORDER BY "VALUE" DESC
