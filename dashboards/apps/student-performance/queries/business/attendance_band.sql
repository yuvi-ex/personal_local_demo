SELECT
    CASE
        WHEN "Attendance (%)" < 60 THEN '<60%'
        WHEN "Attendance (%)" < 70 THEN '60-70%'
        WHEN "Attendance (%)" < 80 THEN '70-80%'
        WHEN "Attendance (%)" < 90 THEN '80-90%'
        ELSE '90-100%'
    END AS "LABEL",
    CAST(AVG("Total_Score") AS DOUBLE) AS "VALUE",
    CASE
        WHEN "Attendance (%)" < 60 THEN 1
        WHEN "Attendance (%)" < 70 THEN 2
        WHEN "Attendance (%)" < 80 THEN 3
        WHEN "Attendance (%)" < 90 THEN 4
        ELSE 5
    END AS "SORT_ORDER"
FROM "STARTER_KIT"."STUDENTS_PERFORMANCE_DATASET_CLEAN"
WHERE ({department_all!d} = 1 OR "Department" IN ({department!s}))
  AND ({gender_all!d} = 1 OR "Gender" IN ({gender!s}))
  AND ({income_all!d} = 1 OR "Family_Income_Level" IN ({income!s}))
  AND ({extracurricular_all!d} = 1 OR "Extracurricular_Activities" IN ({extracurricular!s}))
GROUP BY 1, 3
ORDER BY 3
