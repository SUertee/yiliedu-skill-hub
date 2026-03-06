CREATE OR REPLACE VIEW v_ml_student_full_eval AS
WITH base AS (
  SELECT
    s.id AS student_id,
    s.name,
    s.class_name,
    s.grade_level,
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
    s.fill_date
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
    string_agg(DISTINCT relationship, '、') AS family_roles
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
  ORDER BY student_id, created_at DESC
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
  ORDER BY student_id, created_at DESC
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
  ORDER BY student_id, session_time DESC
),
special_latest AS (
  SELECT DISTINCT ON (student_id)
    student_id,
    counseling_type AS latest_special_type,
    session_time AS latest_special_time
  FROM ml_st_counseling_special
  ORDER BY student_id, session_time DESC
),

/* ✅ 改动点：预约按 student_name 聚合成 “每个姓名最新一条” */
appt_latest AS (
  SELECT DISTINCT ON (student_name_key)
    student_name_key,
    student_name,
    appointment_date AS latest_appointment_date,
    room AS latest_room,
    is_booked AS latest_is_booked,
    submitter AS latest_submitter,
    student_id AS appt_student_id   -- 保留一下，方便你排查/迁移
  FROM (
    SELECT
      a.*,
      lower(trim(a.student_name)) AS student_name_key
    FROM ml_st_room_appointments a
    WHERE a.student_name IS NOT NULL
      AND trim(a.student_name) <> ''
  ) t
  ORDER BY
    student_name_key,
    appointment_date DESC NULLS LAST,
    modified_at DESC NULLS LAST,
    created_at DESC NULLS LAST
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

/* ✅ 改动点：用学生姓名 join */
LEFT JOIN appt_latest al
  ON al.student_name_key = lower(trim(b.name));