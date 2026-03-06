CREATE OR REPLACE VIEW v_ml_student_counseling_events AS
SELECT
  -- 通用字段
  cr.student_id,
  cr.class_name,
  'counseling_record'::text AS event_type,
  cr.session_time,
  COALESCE(cr.counseling_date, cr.session_time::date) AS counseling_date,
  cr.created_at,
  cr.updated_at,
  cr.id AS source_id,

  -- 单独个案字段（保留 counseling_type）
  cr.counseling_type,
  cr.counseling_motivation,
  cr.counseling_issue,
  COALESCE(cr.counseling_issue, cr.counseling_type, '个案记录') AS issue_summary,
  CONCAT_WS('；', cr.counseling_motivation, cr.counseling_issue, cr.attachment) AS event_text,
  cr.attachment,
  cr.session_duration,
  cr.counselor,

  -- 特殊个案字段（避免冲突：用 special_counseling_type）
  NULL::varchar(20) AS special_counseling_type,
  NULL::text        AS counseling_process,
  NULL::text        AS counseling_result

FROM ml_st_counseling_record cr
UNION ALL

SELECT
  sp.student_id,
  sp.class_name,
  'counseling_special'::text AS event_type,
  sp.session_time,
  (sp.session_time::date) AS counseling_date,
  sp.created_at,
  sp.updated_at,
  sp.id AS source_id,

  -- 单独个案字段置空
  NULL::varchar(20) AS counseling_type,
  NULL::text        AS counseling_motivation,
  NULL::varchar(20) AS counseling_issue,
  COALESCE(sp.counseling_type, '特殊个案') AS issue_summary,
  CONCAT_WS('；', sp.counseling_process, sp.counseling_result) AS event_text,
  NULL::text        AS attachment,
  NULL::int         AS session_duration,
  NULL::varchar(100) AS counselor,

  -- 特殊个案字段（用 special_counseling_type）
  sp.counseling_type AS special_counseling_type,
  sp.counseling_process,
  sp.counseling_result

FROM ml_st_counseling_special sp
;
