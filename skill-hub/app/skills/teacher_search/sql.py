# Search teacher summaries directly from view v_teacher_search
SQL_SEARCH_TEACHERS = """
SELECT
  teacher_user_id::text,
  teacher_name,
  school_id::text,
  school_name,
  lesson_count,
  evaluation_count,
  avg_total_score::float,
  last_lesson_date,
  last_eval_date,
  subjects,
  terms,
  school_years
FROM v_teacher_search
WHERE
  teacher_name ILIKE %(q_like)s
  OR teacher_user_id::text = %(q_exact)s
ORDER BY last_lesson_date DESC NULLS LAST, teacher_name ASC
LIMIT %(limit)s OFFSET %(offset)s;
"""

SQL_COUNT_TEACHERS = """
SELECT COUNT(1)
FROM v_teacher_search
WHERE
  teacher_name ILIKE %(q_like)s
  OR teacher_user_id::text = %(q_exact)s;
"""

SQL_GET_TEACHER_BY_ID = """
SELECT
  teacher_user_id::text,
  teacher_name,
  school_id::text,
  school_name,
  lesson_count,
  evaluation_count,
  avg_total_score::float,
  last_lesson_date,
  last_eval_date,
  subjects,
  terms,
  school_years
FROM v_teacher_search
WHERE teacher_user_id::text = %(teacher_id)s
LIMIT 1;
"""

# Recent lessons from v_eval_flat (de-duplicated by lesson_id)
SQL_RECENT_LESSONS = """
SELECT
  x.lesson_id::text,
  x.lesson_date,
  x.school_year,
  x.term,
  x.period_no,
  x.subject,
  x.class_name,
  x.topic,
  x.lesson_level,
  x.lesson_type,
  x.school_id::text,
  x.school_name
FROM (
  SELECT DISTINCT ON (f.lesson_id)
    f.lesson_id,
    f.lesson_date,
    f.school_year,
    f.term,
    f.period_no,
    f.subject,
    f.class_name,
    f.topic,
    f.lesson_level,
    f.lesson_type,
    f.school_id,
    f.school_name,
    f.eval_date
  FROM v_eval_flat f
  LEFT JOIN v_teacher_search t
    ON t.teacher_user_id::text = %(teacher_id)s
  WHERE
    f.host_user_id::text = %(teacher_id)s
    OR (
      (f.host_user_id IS NULL OR f.host_user_id::text = '')
      AND t.teacher_name IS NOT NULL
      AND f.host_name = t.teacher_name
    )
  ORDER BY f.lesson_id, f.lesson_date DESC NULLS LAST, f.eval_date DESC NULLS LAST
) x
ORDER BY x.lesson_date DESC NULLS LAST
LIMIT %(limit)s;
"""

# Recent evaluations from v_eval_flat + report status from pl_lesson_reports
SQL_RECENT_EVALUATIONS = """
SELECT
  f.evaluation_id::text,
  f.lesson_id::text,
  f.lesson_date,
  f.eval_date,
  f.total_score::float,
  f.grade_text,
  f.comment,
  f.evaluator_user_id::text,
  f.evaluator_name,
  f.evaluator_employee_ref,
  f.subject,
  f.class_name,
  f.topic,
  f.school_name,
  lr.term_status AS report_status,
  lr.report_url,
  lr.report_preview_url,
  f.scores_json
FROM v_eval_flat f
LEFT JOIN pl_lesson_reports lr
  ON lr.lesson_id = f.lesson_id
LEFT JOIN v_teacher_search t
  ON t.teacher_user_id::text = %(teacher_id)s
WHERE
  f.host_user_id::text = %(teacher_id)s
  OR (
    (f.host_user_id IS NULL OR f.host_user_id::text = '')
    AND t.teacher_name IS NOT NULL
    AND f.host_name = t.teacher_name
  )
ORDER BY f.lesson_date DESC NULLS LAST, f.eval_date DESC NULLS LAST
LIMIT %(limit)s;
"""
