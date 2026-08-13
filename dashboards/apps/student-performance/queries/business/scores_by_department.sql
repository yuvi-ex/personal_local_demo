SELECT
    "Department" AS "LABEL",
    CAST(AVG("Total_Score") AS DOUBLE) AS "VALUE"
FROM "STARTER_KIT"."STUDENTS_PERFORMANCE_DATASET_CLEAN"
WHERE ({department_all!d} = 1 OR "Department" IN ({department!s}))
  AND ({gender_all!d} = 1 OR "Gender" IN ({gender!s}))
  AND ({income_all!d} = 1 OR "Family_Income_Level" IN ({income!s}))
  AND ({extracurricular_all!d} = 1 OR "Extracurricular_Activities" IN ({extracurricular!s}))
GROUP BY "Department"
ORDER BY "VALUE" DESC
