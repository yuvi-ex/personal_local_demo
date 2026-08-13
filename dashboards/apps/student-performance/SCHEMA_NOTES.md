# Student Performance Dashboard

Source: `STARTER_KIT.STUDENTS_PERFORMANCE_DATASET_CLEAN` (5,000 rows).

## Filters (applied to every query below)

- `Department`, `Gender`, `Family_Income_Level`, `Extracurricular_Activities`.
- Options are loaded live via `queries/business/filter_options.sql` (SELECT DISTINCT)
  on page load - never hardcoded, so they stay correct if the data changes.
- Each business query takes an `{x_all}`/`{x}` pair of pyexasol params per
  filter: `{x_all!d} = 1 OR column = {x!s}`. `x_all = 1` means "no filter
  selected" (all rows), `x_all = 0` filters to `x`. This avoids the pyexasol
  empty-string-renders-to-NULL pitfall for `{x!s}` documented in
  `dash://exasol/help/sql-placeholders`.
- `queries/sql_smoke.json` supplies sample values for every parameterized file
  so `app_build`'s SQL smoke preflight can bind and parse them before
  promotion.

## Panels

- **Key summary metrics** (`summary.sql`): filtered student count (of total),
  average total score, average attendance %, pass rate (grade != F), average
  weekly study hours, average nightly sleep hours.
- **Grade Distribution** (`grade_distribution.sql`): count per letter grade,
  ordered A -> F.
- **Average Score by Subject** (`scores_by_department.sql`): average
  `Total_Score` per `Department` - the closest analog to "subject" in this
  dataset (there is no separate subject/course column).
- **Score Breakdown by Assessment Type** (`score_components.sql`): average of
  Midterm / Final / Assignments / Quizzes / Participation / Projects in one
  row, unpacked into a bar chart in `app.py` - shows where students are
  strongest/weakest across assessment types.
- **Average Score by Attendance** (`attendance_band.sql`): `Total_Score`
  averaged over 5 attendance bands (<60% ... 90-100%) - attendance/performance
  correlation.
- **Average Score by Weekly Study Hours** (`study_hours_band.sql`): same idea
  over 5 study-hour bands (<10h ... 25h+).
- **Average Score by Family Income Level** (`income_level.sql`): equity check
  across Low/Medium/High income.
