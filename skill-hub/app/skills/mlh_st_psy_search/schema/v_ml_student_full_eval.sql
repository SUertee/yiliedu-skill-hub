CREATE OR REPLACE VIEW v_ml_student_full_eval AS
WITH base AS (
  SELECT
    s.id AS student_id,
    s.student_number,
    s.name,
    s.class_id,
    s.class_name,
    s.grade_level,
    s.enroll_year,
    s.gender,
    s.birth_date,
    s.interests,
    s.ethnicity,
    s.native_place,
    s.home_address,
    s.health_status,
    s.medical_history,
    s.medical_history_desc,
    s.height,
    s.weight,
    s.semester,
    s.fill_date,
    s.user_id,
    s.created_at,
    s.updated_at
  FROM ml_students s
),
fam AS (
  SELECT
    student_id,
    string_agg(
      CONCAT_WS('',
        COALESCE(relationship,''), '：', COALESCE(name,''),
        CASE WHEN age IS NOT NULL THEN CONCAT('(', age, '岁)') ELSE '' END
      ),
      '；' ORDER BY id
    ) AS family_members_summary,
    string_agg(DISTINCT relationship, '、' ORDER BY relationship) AS family_roles
  FROM ml_st_family_members
  GROUP BY student_id
),
env AS (
  SELECT DISTINCT ON (student_id)
    student_id,
    economic_status,
    parent_relationship,
    family_atmosphere,
    interaction_pattern,
    parenting_style,
    record_date
  FROM ml_st_family_environments
  ORDER BY student_id, created_at DESC NULLS LAST, id DESC
),
eval AS (
  SELECT DISTINCT ON (student_id)
    student_id,
    interpersonal,
    interpersonal_remark,
    learning_attitude,
    attitude_remark,
    sports,
    sports_remark,
    academic_performance,
    performance_remark,
    learning_habit,
    habit_remark,
    living_environment,
    environment_remark,
    created_at AS eval_created_at
  FROM ml_st_general_evaluation
  ORDER BY student_id, created_at DESC NULLS LAST, id DESC
),
warning_latest AS (
  SELECT DISTINCT ON (student_id)
    student_id,
    semester AS warning_semester,
    warning_level,
    warning_type,
    warning_reason,
    warning_date,
    handler AS warning_handler,
    created_at AS warning_created_at
  FROM ml_st_warning_records
  ORDER BY student_id, warning_date DESC NULLS LAST, created_at DESC NULLS LAST
),
counsel_latest AS (
  SELECT DISTINCT ON (student_id)
    student_id,
    counseling_type AS latest_counseling_type,
    counseling_issue AS latest_counseling_issue,
    counseling_motivation AS latest_counseling_motivation,
    counselor AS latest_counselor,
    session_time AS latest_session_time,
    session_duration AS latest_session_duration
  FROM ml_st_counseling_record
  ORDER BY student_id, session_time DESC NULLS LAST, created_at DESC NULLS LAST, id DESC
),
special_latest AS (
  SELECT DISTINCT ON (student_id)
    student_id,
    counseling_type AS latest_special_type,
    session_time AS latest_special_time
  FROM ml_st_counseling_special
  ORDER BY student_id, session_time DESC NULLS LAST, created_at DESC NULLS LAST, id DESC
)

SELECT
  b.*,

  CASE
    WHEN b.birth_date IS NULL THEN NULL
    ELSE date_part('year', age(current_date, b.birth_date))::int
  END AS age_years,

  f.family_roles,
  f.family_members_summary,

  e.economic_status,
  e.parent_relationship,
  e.family_atmosphere,
  e.interaction_pattern,
  e.parenting_style,
  e.record_date AS family_env_record_date,

  ev.interpersonal,
  ev.interpersonal_remark,
  ev.learning_attitude,
  ev.attitude_remark,
  ev.sports,
  ev.sports_remark,
  ev.academic_performance,
  ev.performance_remark,
  ev.learning_habit,
  ev.habit_remark,
  ev.living_environment,
  ev.environment_remark,
  ev.eval_created_at,

  wl.warning_semester,
  wl.warning_level,
  wl.warning_type,
  wl.warning_reason,
  wl.warning_date,
  wl.warning_handler,
  wl.warning_created_at,

  cl.latest_counseling_type,
  cl.latest_counseling_issue,
  cl.latest_counseling_motivation,
  cl.latest_counselor,
  cl.latest_session_time,
  cl.latest_session_duration,

  sl.latest_special_type,
  sl.latest_special_time,

  al.latest_appointment_date,
  al.latest_room,
  al.latest_is_booked,
  al.latest_submitter

FROM base b
LEFT JOIN fam f ON f.student_id = b.student_id
LEFT JOIN env e ON e.student_id = b.student_id
LEFT JOIN eval ev ON ev.student_id = b.student_id
LEFT JOIN warning_latest wl ON wl.student_id = b.student_id
LEFT JOIN counsel_latest cl ON cl.student_id = b.student_id
LEFT JOIN special_latest sl ON sl.student_id = b.student_id
LEFT JOIN LATERAL (
  SELECT
    a.appointment_date AS latest_appointment_date,
    a.room AS latest_room,
    a.is_booked AS latest_is_booked,
    a.submitter AS latest_submitter
  FROM ml_st_room_appointments a
  WHERE
    (
      NULLIF(trim(a.student_id), '') IS NOT NULL
      AND a.student_id = b.student_id
    )
    OR (
      NULLIF(trim(a.student_id), '') IS NULL
      AND NULLIF(trim(a.student_name), '') IS NOT NULL
      AND lower(trim(a.student_name)) = lower(trim(b.name))
    )
  ORDER BY
    a.appointment_date DESC NULLS LAST,
    a.modified_at DESC NULLS LAST,
    a.created_at DESC NULLS LAST
  LIMIT 1
) al ON TRUE;
