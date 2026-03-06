-- 2. 学生主表
create table if not exists ml_students (
    id                      varchar primary key,         -- 学生UserID（来自钉钉）
    student_number          varchar,                     -- 学籍号
    name                    varchar not null,            -- 学生姓名
    gender                  varchar(10),                  -- 性别
    birth_date              date,                         -- 出生年月
    ethnicity               varchar(50),                  -- 民族
    native_place            varchar(200),                 -- 籍贯
    enroll_year             int,                          -- 入学年份
    interests               text,                         -- 兴趣特长
    home_address            text,                         -- 家庭住址
    health_status           varchar(50),                  -- 健康状况
    medical_history         varchar(200),                 -- 过往病史（逗号分隔）
    medical_history_desc    text,                         -- 其他病史描述
    height                  numeric(5,2),                 -- 身高
    weight                  numeric(5,2),                 -- 体重
    class_id                varchar,
    class_name              varchar,                     
    grade_level             varchar,                      -- 年级级别（如：2025级）
    semester                varchar,                      -- 学期
    fill_date               date,                         -- 填表日期
    raw_payload             jsonb,
    user_id                 varchar unique,  -- 关联用户ID
    created_at              timestamptz,
    updated_at              timestamptz
);

-- 家庭成员表
create table if not exists ml_st_family_members (
    id                      serial primary key,           
    student_id              varchar not null,
    relationship            varchar(50),                  -- 称谓（爸爸/妈妈/哥哥等）
    name                    varchar(100),                 -- 姓名
    age                     int,                          -- 年龄
    occupation              varchar(100),                 -- 职业
    personality             text,                         -- 个性特点
    affection_level         varchar(50),                  -- 喜爱程度
    sub_instance_id         varchar,                      -- 子表实例ID（原系统）
    created_at              timestamptz
);

-- 家庭环境表
create table if not exists ml_st_family_environments (
    id                      serial primary key,
    student_id              varchar not null,
    economic_status         varchar(50),                  -- 经济情况
    parent_relationship     varchar(50),                  -- 父母关系
    family_atmosphere       varchar(50),                  -- 家庭气氛
    interaction_pattern     varchar(50),                  -- 相处模式
    parenting_style         varchar(50),                  -- 教育方式
    record_date             date,                          -- 记录日期
    created_at              timestamptz
);

-- 学习经历表
create table if not exists ml_st_study_experiences (
    id                      serial primary key,
    student_id              varchar not null,
    school_name             varchar(200),                 -- 在何校学习
    position                varchar(100),                 -- 担任职务
    affection_level         varchar(50),                  -- 对集体的喜爱程度
    start_year              varchar(20),                   -- 开始年份
    end_year                varchar(20),                   -- 结束年份
    sub_instance_id         varchar,                      -- 子表实例ID
    created_at              timestamptz
);

--  重大生活事件表
create table if not exists ml_st_life_events (
    id                      serial primary key,
    student_id              varchar not null,
    event_time              varchar(50),                  -- 事件时间
    event_description       text,                         -- 事件经过
    specific_worry          text,                         -- 具体困扰
    expected_help           text,                         -- 期望的帮助
    sub_instance_id         varchar,                      -- 子表实例ID
    created_at              timestamptz
);

-- 学生综合评估表
create table if not exists ml_st_general_evaluation (
    id                      serial primary key,
    student_id              varchar not null,
    interpersonal           varchar(100),                 -- 人际关系
    interpersonal_remark    text,                          -- 人际关系备注
    learning_attitude       varchar(100),                  -- 学习态度
    attitude_remark         text,                          -- 学习态度备注
    sports                  varchar(100),                  -- 体育运动
    sports_remark           text,                          -- 体育运动备注
    academic_performance    varchar(100),                  -- 学习成绩
    performance_remark      text,                          -- 学习成绩备注
    learning_habit          varchar(100),                  -- 学习习惯
    habit_remark            text,                          -- 学习习惯备注
    living_environment      varchar(100),                  -- 居住环境
    environment_remark      text,                          -- 居住环境备注
    created_at              timestamptz
);

-- 1. 心理房间预约表
create table if not exists ml_st_room_appointments (
    id                      varchar primary key,          -- 实例ID
    student_id              varchar,
    student_name            varchar,                      -- 学生姓名
    appointment_date        date not null,                -- 预约日期
    room                    varchar(50),                  -- 预约房间（房间1/房间2/房间3）
    is_booked               boolean default false,        -- 是否预约
    class_name              varchar,                      -- 班级
    submitter               varchar,                      -- 提交人
    created_at              timestamptz,                  -- 创建时间
    modified_at             timestamptz               -- 修改时间
);

-- 3. 单独个案记录
create table if not exists ml_st_counseling_record (
    id                      varchar primary key,         -- 实例ID
    student_id              varchar not null,
    class_name              varchar(100),                -- 班级

    counseling_type         varchar(20),                 -- 辅导类型（如：面询等）
    counseling_motivation   text,                        -- 个案来源（如：主动/被动）
    counseling_issue        varchar(20),                 -- 问题类型（如：人际关系/学习压力等）

    attachment              text,                        -- 附件URL（如有）
    session_time            timestamptz not null,        -- 辅导时间
    session_duration        int,                         -- 辅导时长（分钟）
    counseling_date         date,                        -- 辅导日期
    counselor               varchar(100),                -- 辅导员
    created_at              timestamptz,
    updated_at              timestamptz
);

-- 4. 特殊个案记录
create table if not exists ml_st_counseling_special (
  id                      varchar primary key,         -- 实例ID
  student_id              varchar not null,
  class_name              varchar(100),                -- 班级
  
  counseling_type         varchar(20),                 -- 辅导类型（如：情绪辅导/学习辅导等）
  counseling_process      text,                        -- 辅导过程记录
  counseling_result       text,                        -- 辅导结果记录

  session_time            timestamptz not null,        -- 辅导时间
  created_at              timestamptz,
  updated_at              timestamptz
);

-- 5. 预警记录表
create table if not exists ml_st_warning_records (
  id                varchar primary key,
  student_id        varchar not null,
  semester          varchar(50),
  warning_level     varchar(20),
  warning_type      varchar(50),
  warning_reason    text,
  warning_date      date,
  handler           varchar(100),
  created_at        timestamptz,
  updated_at        timestamptz
);

-- 心理档案报告表
create table if not exists ml_st_report (
    student_id        varchar primary key not null,
    term_status         varchar not null default 'processing'
                 check (term_status in ('processing','completed')),
    report_url     text,                         -- 报告链接（生成后写入）
    report_preview_url text,                     -- 报告预览图链接（生成后写入）
    report_txt     jsonb,                        -- 报告文本内容（生成后写入）
    error_message  text,                         -- 失败原因
    created_at     timestamptz default now()
);

-- 常用检索索引
create index if not exists idx_ml_students_name on ml_students(name);
create index if not exists idx_ml_students_class_grade on ml_students(class_name, grade_level);
create index if not exists idx_ml_students_fill_date on ml_students(fill_date);

create index if not exists idx_ml_st_family_members_student_id on ml_st_family_members(student_id);
create index if not exists idx_ml_st_family_environments_student_id_created_at on ml_st_family_environments(student_id, created_at desc);
create index if not exists idx_ml_st_general_evaluation_student_id_created_at on ml_st_general_evaluation(student_id, created_at desc);

create index if not exists idx_ml_st_room_appointments_student_id_appt_date on ml_st_room_appointments(student_id, appointment_date desc);
create index if not exists idx_ml_st_room_appointments_student_name_appt_date on ml_st_room_appointments(student_name, appointment_date desc);

create index if not exists idx_ml_st_counseling_record_student_time on ml_st_counseling_record(student_id, session_time desc);
create index if not exists idx_ml_st_counseling_special_student_time on ml_st_counseling_special(student_id, session_time desc);

create index if not exists idx_ml_st_warning_records_student_warning_date on ml_st_warning_records(student_id, warning_date desc);
create index if not exists idx_ml_st_warning_records_level_type on ml_st_warning_records(warning_level, warning_type);
