def _host_match(lesson_alias: str, teacher_id_expr: str, teacher_name_expr: str) -> str:
    return f"""
(
  {lesson_alias}.host_user_id::text = {teacher_id_expr}
  OR (
    ({lesson_alias}.host_user_id IS NULL OR {lesson_alias}.host_user_id::text = '')
    AND NULLIF({teacher_name_expr}, '') IS NOT NULL
    AND {lesson_alias}.host_name_snapshot = {teacher_name_expr}
  )
)
"""


_HOST_MATCH_FOR_USER = _host_match("l", "u.id::text", "u.name")

TEACHER_SELECT = """
SELECT
  u.id::text AS teacher_id,
  COALESCE(NULLIF(u.name, ''), latest_lesson.lesson_host_name, u.id::text) AS teacher_name,
  latest_lesson.school_id::text,
  latest_lesson.school_name,
  COALESCE(lesson_stats.lesson_count, 0) AS lesson_count,
  COALESCE(eval_stats.evaluation_count, 0) AS evaluation_count,
  eval_stats.avg_total_score::float,
  lesson_stats.last_lesson_date,
  eval_stats.last_eval_date,
  COALESCE(lesson_stats.subjects, ARRAY[]::text[]) AS subjects,
  COALESCE(lesson_stats.terms, ARRAY[]::text[]) AS terms,
  COALESCE(lesson_stats.school_years, ARRAY[]::text[]) AS school_years
"""

TEACHER_FROM = f"""
FROM pl_users u
LEFT JOIN LATERAL (
  SELECT
    COUNT(DISTINCT l.id) AS lesson_count,
    MAX(l.lesson_date) AS last_lesson_date,
    ARRAY_REMOVE(ARRAY_AGG(DISTINCT l.subject), NULL) AS subjects,
    ARRAY_REMOVE(ARRAY_AGG(DISTINCT l.term), NULL) AS terms,
    ARRAY_REMOVE(ARRAY_AGG(DISTINCT l.school_year), NULL) AS school_years
  FROM pl_lessons l
  WHERE {_HOST_MATCH_FOR_USER}
) AS lesson_stats ON TRUE
LEFT JOIN LATERAL (
  SELECT
    COUNT(1) AS evaluation_count,
    AVG(e.total_score) AS avg_total_score,
    MAX(e.eval_date) AS last_eval_date
  FROM pl_lessons l
  JOIN pl_evaluations e
    ON e.lesson_id = l.id
  WHERE {_HOST_MATCH_FOR_USER}
) AS eval_stats ON TRUE
LEFT JOIN LATERAL (
  SELECT
    l.school_id,
    COALESCE(NULLIF(l.school_name, ''), s.name) AS school_name,
    COALESCE(NULLIF(l.host_name_snapshot, ''), NULLIF(u.name, '')) AS lesson_host_name
  FROM pl_lessons l
  LEFT JOIN pl_schools s
    ON s.id = l.school_id
  WHERE {_HOST_MATCH_FOR_USER}
  ORDER BY l.lesson_date DESC NULLS LAST, l.updated_at DESC NULLS LAST
  LIMIT 1
) AS latest_lesson ON TRUE
"""

TEACHER_ACTIVE_FILTER = """
(
  COALESCE(u.user_type, 'teacher') = 'teacher'
  OR COALESCE(lesson_stats.lesson_count, 0) > 0
)
"""

TEACHER_QUERY_FILTER = """
(
  %(q_empty)s
  OR u.id::text = %(q_exact)s
  OR COALESCE(u.name, '') ILIKE %(q_like)s
  OR COALESCE(latest_lesson.school_name, '') ILIKE %(q_like)s
  OR EXISTS (
    SELECT 1
    FROM pl_lessons l
    WHERE
      {host_match}
      AND (
        l.id::text = %(q_exact)s
        OR COALESCE(l.topic, '') ILIKE %(q_like)s
        OR COALESCE(l.subject, '') ILIKE %(q_like)s
        OR COALESCE(l.class_name, '') ILIKE %(q_like)s
        OR COALESCE(l.term, '') ILIKE %(q_like)s
        OR COALESCE(l.school_year, '') ILIKE %(q_like)s
        OR COALESCE(l.lesson_level, '') ILIKE %(q_like)s
        OR COALESCE(l.lesson_type, '') ILIKE %(q_like)s
        OR COALESCE(l.school_name, '') ILIKE %(q_like)s
      )
  )
)
""".format(host_match=_HOST_MATCH_FOR_USER)

TEACHER_SEARCH_BASE = f"""
{TEACHER_SELECT}
{TEACHER_FROM}
WHERE
  {TEACHER_QUERY_FILTER}
  AND {TEACHER_ACTIVE_FILTER}
"""

SQL_SEARCH_TEACHERS = f"""
{TEACHER_SEARCH_BASE}
ORDER BY lesson_stats.last_lesson_date DESC NULLS LAST, teacher_name ASC
LIMIT %(limit)s OFFSET %(offset)s;
"""

SQL_COUNT_TEACHERS = f"""
SELECT COUNT(1)
FROM (
  {TEACHER_SEARCH_BASE}
) AS teacher_matches;
"""

SQL_GET_TEACHER_BY_ID = f"""
{TEACHER_SELECT}
{TEACHER_FROM}
WHERE
  u.id::text = %(teacher_id)s
  AND {TEACHER_ACTIVE_FILTER}
LIMIT 1;
"""

LESSON_SEARCH_BASE = """
SELECT
  l.id::text AS lesson_id,
  l.lesson_date,
  l.school_year,
  l.term,
  l.period_no,
  l.subject,
  l.class_name,
  l.topic,
  l.lesson_level,
  l.lesson_type,
  l.host_user_id::text,
  COALESCE(NULLIF(l.host_name_snapshot, ''), host_user.name) AS host_name,
  l.school_id::text,
  COALESCE(NULLIF(l.school_name, ''), s.name) AS school_name,
  COALESCE(eval_stats.evaluation_count, 0) AS evaluation_count,
  eval_stats.avg_total_score::float,
  eval_stats.last_eval_date,
  lr.term_status AS report_status,
  lr.report_url,
  lr.report_preview_url
FROM pl_lessons l
LEFT JOIN pl_users host_user
  ON host_user.id = l.host_user_id
LEFT JOIN pl_schools s
  ON s.id = l.school_id
LEFT JOIN LATERAL (
  SELECT
    COUNT(1) AS evaluation_count,
    AVG(e.total_score) AS avg_total_score,
    MAX(e.eval_date) AS last_eval_date
  FROM pl_evaluations e
  WHERE e.lesson_id = l.id
) AS eval_stats ON TRUE
LEFT JOIN pl_lesson_reports lr
  ON lr.lesson_id = l.id
WHERE
  (
    %(q_empty)s
    OR l.id::text = %(q_exact)s
    OR COALESCE(l.topic, '') ILIKE %(q_like)s
    OR COALESCE(l.subject, '') ILIKE %(q_like)s
    OR COALESCE(l.class_name, '') ILIKE %(q_like)s
    OR COALESCE(l.term, '') ILIKE %(q_like)s
    OR COALESCE(l.school_year, '') ILIKE %(q_like)s
    OR COALESCE(l.lesson_level, '') ILIKE %(q_like)s
    OR COALESCE(l.lesson_type, '') ILIKE %(q_like)s
    OR COALESCE(l.school_name, '') ILIKE %(q_like)s
    OR COALESCE(l.host_name_snapshot, '') ILIKE %(q_like)s
    OR COALESCE(host_user.name, '') ILIKE %(q_like)s
    OR COALESCE(l.host_user_id::text, '') = %(q_exact)s
  )
  AND (%(teacher_id)s::text IS NULL OR l.host_user_id::text = %(teacher_id)s::text)
  AND (
    %(teacher_name)s::text IS NULL
    OR COALESCE(NULLIF(l.host_name_snapshot, ''), host_user.name) = %(teacher_name)s::text
  )
  AND (%(topic_kw)s::text IS NULL OR COALESCE(l.topic, '') ILIKE %(topic_kw)s::text)
  AND (%(school_id)s::text IS NULL OR l.school_id::text = %(school_id)s::text)
  AND (
    %(school_name_kw)s::text IS NULL
    OR COALESCE(NULLIF(l.school_name, ''), s.name, '') ILIKE %(school_name_kw)s::text
  )
  AND (%(subject)s::text IS NULL OR l.subject = %(subject)s::text)
  AND (%(term)s::text IS NULL OR l.term = %(term)s::text)
  AND (%(school_year)s::text IS NULL OR l.school_year = %(school_year)s::text)
  AND (%(start_date)s::date IS NULL OR l.lesson_date >= %(start_date)s::date)
  AND (%(end_date)s::date IS NULL OR l.lesson_date <= %(end_date)s::date)
  AND (
    %(min_avg_score)s::numeric IS NULL
    OR COALESCE(eval_stats.avg_total_score, 0) >= %(min_avg_score)s::numeric
  )
"""

SQL_SEARCH_LESSONS = f"""
{LESSON_SEARCH_BASE}
ORDER BY l.lesson_date DESC NULLS LAST, eval_stats.last_eval_date DESC NULLS LAST
LIMIT %(limit)s OFFSET %(offset)s;
"""

SQL_COUNT_LESSONS = f"""
SELECT COUNT(1)
FROM (
  {LESSON_SEARCH_BASE}
) AS lesson_matches;
"""

EVALUATION_SEARCH_BASE = """
SELECT
  e.id::text AS evaluation_id,
  e.lesson_id::text,
  l.lesson_date,
  e.eval_date,
  e.total_score::float,
  e.grade_text,
  e.comment,
  e.evaluator_user_id::text,
  COALESCE(NULLIF(e.evaluator_name_snapshot, ''), evaluator.name) AS evaluator_name,
  e.evaluator_employee_ref,
  l.subject,
  l.class_name,
  l.topic,
  COALESCE(NULLIF(l.school_name, ''), s.name) AS school_name,
  l.host_user_id::text,
  COALESCE(NULLIF(l.host_name_snapshot, ''), host_user.name) AS host_name,
  lr.term_status AS report_status,
  lr.report_url,
  lr.report_preview_url,
  COALESCE(score_items.scores_json, '[]'::jsonb) AS scores_json
FROM pl_evaluations e
JOIN pl_lessons l
  ON l.id = e.lesson_id
LEFT JOIN pl_users evaluator
  ON evaluator.id = e.evaluator_user_id
LEFT JOIN pl_users host_user
  ON host_user.id = l.host_user_id
LEFT JOIN pl_schools s
  ON s.id = COALESCE(l.school_id, e.school_id)
LEFT JOIN pl_lesson_reports lr
  ON lr.lesson_id = e.lesson_id
LEFT JOIN LATERAL (
  SELECT jsonb_agg(
    jsonb_build_object(
      'item_key', es.item_key,
      'item_label', es.item_label,
      'score', es.score
    )
    ORDER BY es.item_label
  ) AS scores_json
  FROM pl_evaluation_scores es
  WHERE es.evaluation_id = e.id
) AS score_items ON TRUE
WHERE
  (
    %(q_empty)s
    OR e.id::text = %(q_exact)s
    OR e.lesson_id::text = %(q_exact)s
    OR COALESCE(e.grade_text, '') ILIKE %(q_like)s
    OR COALESCE(e.comment, '') ILIKE %(q_like)s
    OR COALESCE(e.evaluator_name_snapshot, '') ILIKE %(q_like)s
    OR COALESCE(evaluator.name, '') ILIKE %(q_like)s
    OR COALESCE(l.topic, '') ILIKE %(q_like)s
    OR COALESCE(l.subject, '') ILIKE %(q_like)s
    OR COALESCE(l.class_name, '') ILIKE %(q_like)s
    OR COALESCE(l.school_name, '') ILIKE %(q_like)s
    OR COALESCE(l.host_name_snapshot, '') ILIKE %(q_like)s
    OR COALESCE(host_user.name, '') ILIKE %(q_like)s
    OR EXISTS (
      SELECT 1
      FROM pl_evaluation_scores es
      WHERE
        es.evaluation_id = e.id
        AND (
          es.item_key = %(q_exact)s
          OR COALESCE(es.item_label, '') ILIKE %(q_like)s
        )
    )
  )
  AND (%(lesson_id)s::text IS NULL OR e.lesson_id::text = %(lesson_id)s::text)
  AND (%(teacher_id)s::text IS NULL OR l.host_user_id::text = %(teacher_id)s::text)
  AND (
    %(teacher_name)s::text IS NULL
    OR COALESCE(NULLIF(l.host_name_snapshot, ''), host_user.name) = %(teacher_name)s::text
  )
  AND (
    %(evaluator_name_kw)s::text IS NULL
    OR COALESCE(NULLIF(e.evaluator_name_snapshot, ''), evaluator.name, '') ILIKE %(evaluator_name_kw)s::text
  )
  AND (%(topic_kw)s::text IS NULL OR COALESCE(l.topic, '') ILIKE %(topic_kw)s::text)
  AND (%(school_id)s::text IS NULL OR COALESCE(l.school_id, e.school_id)::text = %(school_id)s::text)
  AND (
    %(school_name_kw)s::text IS NULL
    OR COALESCE(NULLIF(l.school_name, ''), s.name, '') ILIKE %(school_name_kw)s::text
  )
  AND (%(subject)s::text IS NULL OR l.subject = %(subject)s::text)
  AND (%(min_score)s::numeric IS NULL OR e.total_score >= %(min_score)s::numeric)
  AND (%(max_score)s::numeric IS NULL OR e.total_score <= %(max_score)s::numeric)
"""

SQL_SEARCH_EVALUATIONS = f"""
{EVALUATION_SEARCH_BASE}
ORDER BY l.lesson_date DESC NULLS LAST, e.eval_date DESC NULLS LAST
LIMIT %(limit)s OFFSET %(offset)s;
"""

SQL_COUNT_EVALUATIONS = f"""
SELECT COUNT(1)
FROM (
  {EVALUATION_SEARCH_BASE}
) AS evaluation_matches;
"""
