SELECT
    COUNT(*) AS "STUDENT_COUNT",
    (SELECT COUNT(*) FROM "STARTER_KIT"."STUDENTS_PERFORMANCE_DATASET_CLEAN") AS "TOTAL_STUDENTS",
    CAST(AVG("Total_Score") AS DOUBLE) AS "AVG_TOTAL_SCORE",
    CAST(AVG("Attendance (%)") AS DOUBLE) AS "AVG_ATTENDANCE",
    CAST(100.0 * SUM(CASE WHEN "Grade" = 'F' THEN 0 ELSE 1 END) / NULLIF(COUNT(*), 0) AS DOUBLE) AS "PASS_RATE",
    CAST(AVG("Study_Hours_per_Week") AS DOUBLE) AS "AVG_STUDY_HOURS",
    CAST(AVG("Sleep_Hours_per_Night") AS DOUBLE) AS "AVG_SLEEP_HOURS"
FROM "STARTER_KIT"."STUDENTS_PERFORMANCE_DATASET_CLEAN"
WHERE ({department_all!d} = 1 OR "Department" IN ({department!s}))
  AND ({gender_all!d} = 1 OR "Gender" IN ({gender!s}))
  AND ({income_all!d} = 1 OR "Family_Income_Level" IN ({income!s}))
  AND ({extracurricular_all!d} = 1 OR "Extracurricular_Activities" IN ({extracurricular!s}))
