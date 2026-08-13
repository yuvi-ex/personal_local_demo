WITH FILTERED AS (
  SELECT *
  FROM "STARTER_KIT"."EMPLOYEES"
  WHERE ({department_all!d} = 1 OR "department" IN ({department!s}))
    AND ({active_only!d} = 0 OR "is_active" = TRUE)
)
SELECT
    "department" AS "LABEL",
    CAST(COUNT(*) AS DOUBLE) AS "VALUE",
    CASE WHEN "is_active" THEN 'Active' ELSE 'Inactive' END AS "CATEGORY"
FROM FILTERED
GROUP BY "department", "is_active"
ORDER BY "LABEL"
