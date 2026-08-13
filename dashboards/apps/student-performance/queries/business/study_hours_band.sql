SELECT
    CASE
        WHEN "Study_Hours_per_Week" < 10 THEN '0-9 hrs/wk'
        WHEN "Study_Hours_per_Week" < 20 THEN '10-19 hrs/wk'
        WHEN "Study_Hours_per_Week" < 30 THEN '20-29 hrs/wk'
        ELSE '30+ hrs/wk'
    END AS "LABEL",
    CAST(AVG("Total_Score") AS DOUBLE) AS "VALUE",
    CASE
        WHEN "Study_Hours_per_Week" < 10 THEN 1
        WHEN "Study_Hours_per_Week" < 20 THEN 2
        WHEN "Study_Hours_per_Week" < 30 THEN 3
        ELSE 4
    END AS "SORT_ORDER"
FROM "STARTER_KIT"."STUDENTS_PERFORMANCE_DATASET_CLEAN"
WHERE ({department_all!d} = 1 OR "Department" IN ({department!s}))
  AND ({gender_all!d} = 1 OR "Gender" IN ({gender!s}))
  AND ({income_all!d} = 1 OR "Family_Income_Level" IN ({income!s}))
  AND ({extracurricular_all!d} = 1 OR "Extracurricular_Activities" IN ({extracurricular!s}))
GROUP BY 1, 3
ORDER BY 3
