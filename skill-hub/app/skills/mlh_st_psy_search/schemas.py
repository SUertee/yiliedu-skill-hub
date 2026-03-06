from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StudentSummary(BaseModel):
    student_id: str
    student_number: Optional[str] = None
    name: str
    class_id: Optional[str] = None
    class_name: Optional[str] = None
    grade_level: Optional[str] = None
    gender: Optional[str] = None
    age_years: Optional[int] = None
    semester: Optional[str] = None
    fill_date: Optional[str] = None
    health_status: Optional[str] = None
    warning_level: Optional[str] = None
    warning_type: Optional[str] = None
    warning_date: Optional[str] = None
    latest_counseling_type: Optional[str] = None
    latest_counseling_issue: Optional[str] = None
    latest_special_type: Optional[str] = None
    latest_session_time: Optional[str] = None
    latest_appointment_date: Optional[str] = None
    latest_room: Optional[str] = None
    report_status: Optional[str] = None
    report_url: Optional[str] = None
    report_preview_url: Optional[str] = None
    event_count: int = 0
    warning_count: int = 0


class StudentSearchResponse(BaseModel):
    ok: bool = True
    q: Optional[str] = None
    total: int
    items: List[StudentSummary] = Field(default_factory=list)


class CounselingEventItem(BaseModel):
    source_id: str
    student_id: str
    student_name: str
    class_name: Optional[str] = None
    event_type: str
    session_time: Optional[str] = None
    counseling_date: Optional[str] = None
    counseling_type: Optional[str] = None
    special_counseling_type: Optional[str] = None
    counseling_issue: Optional[str] = None
    counseling_motivation: Optional[str] = None
    counseling_process: Optional[str] = None
    counseling_result: Optional[str] = None
    issue_summary: Optional[str] = None
    event_text: Optional[str] = None
    session_duration: Optional[int] = None
    counselor: Optional[str] = None
    attachment: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CounselingEventSearchResponse(BaseModel):
    ok: bool = True
    q: Optional[str] = None
    total: int
    items: List[CounselingEventItem] = Field(default_factory=list)


class WarningItem(BaseModel):
    warning_id: str
    student_id: str
    student_name: str
    class_name: Optional[str] = None
    semester: Optional[str] = None
    warning_level: Optional[str] = None
    warning_type: Optional[str] = None
    warning_reason: Optional[str] = None
    warning_date: Optional[str] = None
    handler: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class WarningSearchResponse(BaseModel):
    ok: bool = True
    q: Optional[str] = None
    total: int
    items: List[WarningItem] = Field(default_factory=list)


class StudentDetailResponse(BaseModel):
    ok: bool = True
    student: StudentSummary
    recent_counseling_events: List[CounselingEventItem] = Field(default_factory=list)
    recent_warnings: List[WarningItem] = Field(default_factory=list)


class GeneralSearchSummary(BaseModel):
    student_matches: int = 0
    counseling_event_matches: int = 0
    warning_matches: int = 0
    matched_classes: List[str] = Field(default_factory=list)
    matched_warning_levels: List[str] = Field(default_factory=list)


class GeneralSearchResponse(BaseModel):
    ok: bool = True
    q: str
    summary: GeneralSearchSummary
    students: List[StudentSummary] = Field(default_factory=list)
    counseling_events: List[CounselingEventItem] = Field(default_factory=list)
    warnings: List[WarningItem] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)
