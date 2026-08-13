SELECT
    CAST(AVG("Midterm_Score") AS DOUBLE) AS "AVG_MIDTERM",
    CAST(AVG("Final_Score") AS DOUBLE) AS "AVG_FINAL",
    CAST(AVG("Assignments_Avg") AS DOUBLE) AS "AVG_ASSIGNMENTS",
    CAST(AVG("Quizzes_Avg") AS DOUBLE) AS "AVG_QUIZZES",
    CAST(AVG("Participation_Score") AS DOUBLE) AS "AVG_PARTICIPATION",
    CAST(AVG("Projects_Score") AS DOUBLE) AS "AVG_PROJECTS"
FROM "STARTER_KIT"."STUDENTS_PERFORMANCE_DATASET_CLEAN"
WHERE ({department_all!d} = 1 OR "Department" IN ({department!s}))
  AND ({gender_all!d} = 1 OR "Gender" IN ({gender!s}))
  AND ({income_all!d} = 1 OR "Family_Income_Level" IN ({income!s}))
  AND ({extracurricular_all!d} = 1 OR "Extracurricular_Activities" IN ({extracurricular!s}))
