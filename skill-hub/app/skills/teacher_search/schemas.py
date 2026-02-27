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
    recent_lessons: List[Dict[str, Any]] = Field(default_factory=list)
    recent_evaluations: List[Dict[str, Any]] = Field(default_factory=list)


class LessonSummary(BaseModel):
    lesson_id: str
    lesson_date: Optional[str] = None
    subject: Optional[str] = None
    class_name: Optional[str] = None
    topic: Optional[str] = None
    school_name: Optional[str] = None
    evaluation_count: int = 0
    avg_total_score: Optional[float] = None
    last_eval_date: Optional[str] = None


class TeacherLessonsResponse(BaseModel):
    ok: bool = True
    total: int
    items: List[LessonSummary] = Field(default_factory=list)


class LessonEvaluationsResponse(BaseModel):
    ok: bool = True
    lesson_id: str
    total: int
    items: List[Dict[str, Any]] = Field(default_factory=list)


class TopicEvaluationsResponse(BaseModel):
    ok: bool = True
    teacher_name: str
    topic: str
    matched_lesson_id: str
    matched_lesson: Dict[str, Any]
    total: int
    items: List[Dict[str, Any]] = Field(default_factory=list)
