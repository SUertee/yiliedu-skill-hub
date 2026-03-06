STUDENT_SELECT = """
SELECT
  s.student_id,
  s.student_number,
  s.name,
  s.class_id,
  s.class_name,
  s.grade_level,
  s.gender,
  s.age_years,
  s.semester,
  s.fill_date,
  s.health_status,
  s.warning_level,
  s.warning_type,
  s.warning_date,
  s.latest_counseling_type,
  s.latest_counseling_issue,
  s.latest_special_type,
  s.latest_session_time,
  s.latest_appointment_date,
  s.latest_room,
  r.term_status,
  r.report_url,
  r.report_preview_url,
  COALESCE(event_stats.event_count, 0) AS event_count,
  COALESCE(warn_stats.warning_count, 0) AS warning_count
"""

STUDENT_FROM = """
FROM v_ml_student_full_eval s
LEFT JOIN ml_st_report r
  ON r.student_id = s.student_id
LEFT JOIN LATERAL (
  SELECT COUNT(1) AS event_count
  FROM v_ml_student_counseling_events ce
  WHERE ce.student_id = s.student_id
) AS event_stats ON TRUE
LEFT JOIN LATERAL (
  SELECT COUNT(1) AS warning_count
  FROM ml_st_warning_records w
  WHERE w.student_id = s.student_id
) AS warn_stats ON TRUE
"""

STUDENT_QUERY_FILTER = """
(
  %(q_empty)s
  OR s.student_id::text = %(q_exact)s
  OR COALESCE(s.student_number, '') = %(q_exact)s
  OR COALESCE(s.name, '') ILIKE %(q_like)s
  OR COALESCE(s.class_name, '') ILIKE %(q_like)s
  OR COALESCE(s.grade_level, '') ILIKE %(q_like)s
  OR COALESCE(s.semester, '') ILIKE %(q_like)s
  OR COALESCE(s.gender, '') ILIKE %(q_like)s
  OR COALESCE(s.ethnicity, '') ILIKE %(q_like)s
  OR COALESCE(s.native_place, '') ILIKE %(q_like)s
  OR COALESCE(s.interests, '') ILIKE %(q_like)s
  OR COALESCE(s.health_status, '') ILIKE %(q_like)s
  OR COALESCE(s.medical_history, '') ILIKE %(q_like)s
  OR COALESCE(s.medical_history_desc, '') ILIKE %(q_like)s
  OR COALESCE(s.family_roles, '') ILIKE %(q_like)s
  OR COALESCE(s.family_members_summary, '') ILIKE %(q_like)s
  OR COALESCE(s.parent_relationship, '') ILIKE %(q_like)s
  OR COALESCE(s.family_atmosphere, '') ILIKE %(q_like)s
  OR COALESCE(s.interpersonal, '') ILIKE %(q_like)s
  OR COALESCE(s.learning_attitude, '') ILIKE %(q_like)s
  OR COALESCE(s.academic_performance, '') ILIKE %(q_like)s
  OR COALESCE(s.warning_level, '') ILIKE %(q_like)s
  OR COALESCE(s.warning_type, '') ILIKE %(q_like)s
  OR COALESCE(s.warning_reason, '') ILIKE %(q_like)s
  OR COALESCE(s.latest_counseling_type, '') ILIKE %(q_like)s
  OR COALESCE(s.latest_counseling_issue, '') ILIKE %(q_like)s
  OR COALESCE(s.latest_counseling_motivation, '') ILIKE %(q_like)s
  OR COALESCE(s.latest_special_type, '') ILIKE %(q_like)s
  OR COALESCE(s.latest_counselor, '') ILIKE %(q_like)s
)
"""

STUDENT_SEARCH_BASE = f"""
{STUDENT_SELECT}
{STUDENT_FROM}
WHERE
  {STUDENT_QUERY_FILTER}
  AND (%(student_id)s::text IS NULL OR s.student_id::text = %(student_id)s::text)
  AND (%(class_name_kw)s::text IS NULL OR COALESCE(s.class_name, '') ILIKE %(class_name_kw)s::text)
  AND (%(grade_level)s::text IS NULL OR s.grade_level = %(grade_level)s::text)
  AND (%(warning_level)s::text IS NULL OR s.warning_level = %(warning_level)s::text)
  AND (%(start_fill_date)s::date IS NULL OR s.fill_date >= %(start_fill_date)s::date)
  AND (%(end_fill_date)s::date IS NULL OR s.fill_date <= %(end_fill_date)s::date)
"""

SQL_SEARCH_STUDENTS = f"""
{STUDENT_SEARCH_BASE}
ORDER BY s.warning_date DESC NULLS LAST, s.latest_session_time DESC NULLS LAST, s.name ASC
LIMIT %(limit)s OFFSET %(offset)s;
"""

SQL_COUNT_STUDENTS = f"""
SELECT COUNT(1)
FROM (
  {STUDENT_SEARCH_BASE}
) AS student_matches;
"""

SQL_GET_STUDENT_BY_ID = f"""
{STUDENT_SELECT}
{STUDENT_FROM}
WHERE s.student_id::text = %(student_id)s::text
LIMIT 1;
"""

COUNSELING_EVENT_SEARCH_BASE = """
SELECT
  ce.source_id,
  ce.student_id,
  COALESCE(s.name, ce.student_id) AS student_name,
  COALESCE(ce.class_name, s.class_name) AS class_name,
  ce.event_type,
  ce.session_time,
  ce.counseling_date,
  ce.counseling_type,
  ce.special_counseling_type,
  ce.counseling_issue,
  ce.counseling_motivation,
  ce.counseling_process,
  ce.counseling_result,
  ce.issue_summary,
  ce.event_text,
  ce.session_duration,
  ce.counselor,
  ce.attachment,
  ce.created_at,
  ce.updated_at
FROM v_ml_student_counseling_events ce
LEFT JOIN ml_students s
  ON s.id = ce.student_id
WHERE
  (
    %(q_empty)s
    OR ce.source_id::text = %(q_exact)s
    OR ce.student_id::text = %(q_exact)s
    OR COALESCE(s.name, '') ILIKE %(q_like)s
    OR COALESCE(ce.class_name, '') ILIKE %(q_like)s
    OR COALESCE(ce.event_type, '') ILIKE %(q_like)s
    OR COALESCE(ce.counseling_type, '') ILIKE %(q_like)s
    OR COALESCE(ce.special_counseling_type, '') ILIKE %(q_like)s
    OR COALESCE(ce.counseling_issue, '') ILIKE %(q_like)s
    OR COALESCE(ce.counseling_motivation, '') ILIKE %(q_like)s
    OR COALESCE(ce.issue_summary, '') ILIKE %(q_like)s
    OR COALESCE(ce.event_text, '') ILIKE %(q_like)s
    OR COALESCE(ce.counselor, '') ILIKE %(q_like)s
  )
  AND (%(student_id)s::text IS NULL OR ce.student_id::text = %(student_id)s::text)
  AND (%(event_type)s::text IS NULL OR ce.event_type = %(event_type)s::text)
  AND (%(counselor_kw)s::text IS NULL OR COALESCE(ce.counselor, '') ILIKE %(counselor_kw)s::text)
  AND (%(start_time)s::timestamptz IS NULL OR ce.session_time >= %(start_time)s::timestamptz)
  AND (%(end_time)s::timestamptz IS NULL OR ce.session_time <= %(end_time)s::timestamptz)
"""

SQL_SEARCH_COUNSELING_EVENTS = f"""
{COUNSELING_EVENT_SEARCH_BASE}
ORDER BY ce.session_time DESC NULLS LAST, ce.created_at DESC NULLS LAST
LIMIT %(limit)s OFFSET %(offset)s;
"""

SQL_COUNT_COUNSELING_EVENTS = f"""
SELECT COUNT(1)
FROM (
  {COUNSELING_EVENT_SEARCH_BASE}
) AS counseling_event_matches;
"""

WARNING_SEARCH_BASE = """
SELECT
  w.id::text AS warning_id,
  w.student_id,
  COALESCE(s.name, w.student_id) AS student_name,
  COALESCE(s.class_name, '') AS class_name,
  w.semester,
  w.warning_level,
  w.warning_type,
  w.warning_reason,
  w.warning_date,
  w.handler,
  w.created_at,
  w.updated_at
FROM ml_st_warning_records w
LEFT JOIN ml_students s
  ON s.id = w.student_id
WHERE
  (
    %(q_empty)s
    OR w.id::text = %(q_exact)s
    OR w.student_id::text = %(q_exact)s
    OR COALESCE(s.name, '') ILIKE %(q_like)s
    OR COALESCE(s.class_name, '') ILIKE %(q_like)s
    OR COALESCE(w.semester, '') ILIKE %(q_like)s
    OR COALESCE(w.warning_level, '') ILIKE %(q_like)s
    OR COALESCE(w.warning_type, '') ILIKE %(q_like)s
    OR COALESCE(w.warning_reason, '') ILIKE %(q_like)s
    OR COALESCE(w.handler, '') ILIKE %(q_like)s
  )
  AND (%(student_id)s::text IS NULL OR w.student_id::text = %(student_id)s::text)
  AND (%(warning_level)s::text IS NULL OR w.warning_level = %(warning_level)s::text)
  AND (%(warning_type)s::text IS NULL OR w.warning_type = %(warning_type)s::text)
  AND (%(start_date)s::date IS NULL OR w.warning_date >= %(start_date)s::date)
  AND (%(end_date)s::date IS NULL OR w.warning_date <= %(end_date)s::date)
"""

SQL_SEARCH_WARNINGS = f"""
{WARNING_SEARCH_BASE}
ORDER BY w.warning_date DESC NULLS LAST, w.created_at DESC NULLS LAST
LIMIT %(limit)s OFFSET %(offset)s;
"""

SQL_COUNT_WARNINGS = f"""
SELECT COUNT(1)
FROM (
  {WARNING_SEARCH_BASE}
) AS warning_matches;
"""
