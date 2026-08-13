SELECT
    "Grade" AS "LABEL",
    CAST(COUNT(*) AS DOUBLE) AS "VALUE",
    CASE "Grade"
        WHEN 'A' THEN 1 WHEN 'B' THEN 2 WHEN 'C' THEN 3 WHEN 'D' THEN 4 WHEN 'F' THEN 5 ELSE 6
    END AS "SORT_ORDER"
FROM "STARTER_KIT"."STUDENTS_PERFORMANCE_DATASET_CLEAN"
WHERE ({department_all!d} = 1 OR "Department" IN ({department!s}))
  AND ({gender_all!d} = 1 OR "Gender" IN ({gender!s}))
  AND ({income_all!d} = 1 OR "Family_Income_Level" IN ({income!s}))
  AND ({extracurricular_all!d} = 1 OR "Extracurricular_Activities" IN ({extracurricular!s}))
GROUP BY "Grade"
ORDER BY "SORT_ORDER"
