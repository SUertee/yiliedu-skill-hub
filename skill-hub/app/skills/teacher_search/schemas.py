from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TeacherSummary(BaseModel):
    teacher_id: str
    teacher_name: str
    school_id: Optional[str] = None
    school_name: Optional[str] = None
    lesson_count: int = 0
    evaluation_count: int = 0
    avg_total_score: Optional[float] = None
    last_lesson_date: Optional[str] = None
    last_eval_date: Optional[str] = None
    subjects: List[str] = Field(default_factory=list)
    terms: List[str] = Field(default_factory=list)
    school_years: List[str] = Field(default_factory=list)


class TeacherSearchResponse(BaseModel):
    ok: bool = True
    q: str
    total: int
    items: List[TeacherSummary] = Field(default_factory=list)


class TeacherDetailResponse(BaseModel):
    ok: bool = True
    teacher: TeacherSummary
    recent_lessons: List["LessonSearchItem"] = Field(default_factory=list)
    recent_evaluations: List["EvaluationItem"] = Field(default_factory=list)


class LessonSearchItem(BaseModel):
    lesson_id: str
    lesson_date: Optional[str] = None
    school_year: Optional[str] = None
    term: Optional[str] = None
    period_no: Optional[int] = None
    subject: Optional[str] = None
    class_name: Optional[str] = None
    topic: Optional[str] = None
    lesson_level: Optional[str] = None
    lesson_type: Optional[str] = None
    host_user_id: Optional[str] = None
    host_name: Optional[str] = None
    school_id: Optional[str] = None
    school_name: Optional[str] = None
    evaluation_count: int = 0
    avg_total_score: Optional[float] = None
    last_eval_date: Optional[str] = None
    report_status: Optional[str] = None
    report_url: Optional[str] = None
    report_preview_url: Optional[str] = None


class TeacherLessonsResponse(BaseModel):
    ok: bool = True
    q: Optional[str] = None
    total: int
    items: List[LessonSearchItem] = Field(default_factory=list)


class EvaluationItem(BaseModel):
    evaluation_id: str
    lesson_id: str
    lesson_date: Optional[str] = None
    eval_date: Optional[str] = None
    total_score: Optional[float] = None
    grade_text: Optional[str] = None
    comment: Optional[str] = None
    evaluator_user_id: Optional[str] = None
    evaluator_name: Optional[str] = None
    evaluator_employee_ref: Optional[str] = None
    subject: Optional[str] = None
    class_name: Optional[str] = None
    topic: Optional[str] = None
    school_name: Optional[str] = None
    host_user_id: Optional[str] = None
    host_name: Optional[str] = None
    report_status: Optional[str] = None
    report_url: Optional[str] = None
    report_preview_url: Optional[str] = None
    scores_json: List[Dict[str, Any]] = Field(default_factory=list)


class LessonEvaluationsResponse(BaseModel):
    ok: bool = True
    lesson_id: str
    total: int
    items: List[EvaluationItem] = Field(default_factory=list)


class EvaluationSearchResponse(BaseModel):
    ok: bool = True
    q: Optional[str] = None
    total: int
    items: List[EvaluationItem] = Field(default_factory=list)


class TopicEvaluationsResponse(BaseModel):
    ok: bool = True
    teacher_name: str
    topic: str
    matched_lesson_id: str
    matched_lesson: LessonSearchItem
    total: int
    items: List[EvaluationItem] = Field(default_factory=list)


class GeneralSearchSummary(BaseModel):
    teacher_matches: int = 0
    lesson_matches: int = 0
    evaluation_matches: int = 0
    matched_schools: List[str] = Field(default_factory=list)
    matched_subjects: List[str] = Field(default_factory=list)


class GeneralSearchResponse(BaseModel):
    ok: bool = True
    q: str
    summary: GeneralSearchSummary
    teachers: List[TeacherSummary] = Field(default_factory=list)
    lessons: List[LessonSearchItem] = Field(default_factory=list)
    evaluations: List[EvaluationItem] = Field(default_factory=list)
