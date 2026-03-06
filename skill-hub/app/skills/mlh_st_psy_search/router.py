from datetime import date, datetime

from app.core.auth import require_api_key
from app.core.errors import bad_request, not_found
from fastapi import APIRouter, Depends, Query

from .schemas import (
    CounselingEventSearchResponse,
    GeneralSearchResponse,
    StudentDetailResponse,
    StudentSearchResponse,
    WarningSearchResponse,
)
from .service import (
    general_search,
    get_student_detail,
    search_counseling_events,
    search_students,
    search_warnings,
)

router = APIRouter(prefix="/api/mlh_st_psy_search", tags=["mlh_st_psy_search"])


@router.get("", response_model=StudentSearchResponse)
def student_search(
    q: str = Query(..., min_length=1, description="学生姓名/学号/班级/预警/辅导关键词"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _auth=Depends(require_api_key),
):
    if not q.strip():
        bad_request("q 不能为空")

    total, items = search_students(q=q, limit=limit, offset=offset)
    return {"ok": True, "q": q, "total": total, "items": items}


@router.get("/query", response_model=GeneralSearchResponse)
def student_search_query(
    q: str = Query(..., min_length=1, description="自然语言关键词，如学生、班级、预警、辅导主题"),
    limit: int = Query(8, ge=1, le=50),
    _auth=Depends(require_api_key),
):
    if not q.strip():
        bad_request("q 不能为空")

    return {"ok": True, **general_search(q=q, limit=limit)}


@router.get("/students", response_model=StudentSearchResponse)
def students(
    q: str | None = Query(None, description="通用关键词：学生、班级、预警、辅导"),
    student_id: str | None = Query(None, description="学生ID"),
    class_name: str | None = Query(None, description="班级关键词"),
    grade_level: str | None = Query(None, description="年级，如2025级"),
    warning_level: str | None = Query(None, description="预警等级"),
    start_fill_date: date | None = Query(None, description="起始填表日期"),
    end_fill_date: date | None = Query(None, description="结束填表日期"),
    limit: int = Query(20, ge=1, le=300),
    offset: int = Query(0, ge=0),
    _auth=Depends(require_api_key),
):
    total, items = search_students(
        q=q,
        student_id=student_id,
        class_name=class_name,
        grade_level=grade_level,
        warning_level=warning_level,
        start_fill_date=start_fill_date,
        end_fill_date=end_fill_date,
        limit=limit,
        offset=offset,
    )
    return {"ok": True, "q": q, "total": total, "items": items}


@router.get("/counseling_events", response_model=CounselingEventSearchResponse)
def counseling_events(
    q: str | None = Query(None, description="通用关键词：学生、辅导主题、个案描述、咨询师"),
    student_id: str | None = Query(None, description="学生ID"),
    event_type: str | None = Query(None, description="counseling_record/counseling_special"),
    counselor: str | None = Query(None, description="咨询师关键词"),
    start_time: datetime | None = Query(None, description="起始辅导时间"),
    end_time: datetime | None = Query(None, description="结束辅导时间"),
    limit: int = Query(20, ge=1, le=300),
    offset: int = Query(0, ge=0),
    _auth=Depends(require_api_key),
):
    total, items = search_counseling_events(
        q=q,
        student_id=student_id,
        event_type=event_type,
        counselor=counselor,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )
    return {"ok": True, "q": q, "total": total, "items": items}


@router.get("/warnings", response_model=WarningSearchResponse)
def warnings(
    q: str | None = Query(None, description="通用关键词：学生、预警等级、预警类型、处理人"),
    student_id: str | None = Query(None, description="学生ID"),
    warning_level: str | None = Query(None, description="预警等级"),
    warning_type: str | None = Query(None, description="预警类型"),
    start_date: date | None = Query(None, description="起始预警日期"),
    end_date: date | None = Query(None, description="结束预警日期"),
    limit: int = Query(20, ge=1, le=300),
    offset: int = Query(0, ge=0),
    _auth=Depends(require_api_key),
):
    total, items = search_warnings(
        q=q,
        student_id=student_id,
        warning_level=warning_level,
        warning_type=warning_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    return {"ok": True, "q": q, "total": total, "items": items}


@router.get("/{student_id}", response_model=StudentDetailResponse)
def student_detail(
    student_id: str,
    event_limit: int = Query(20, ge=1, le=200),
    warning_limit: int = Query(20, ge=1, le=200),
    _auth=Depends(require_api_key),
):
    detail = get_student_detail(
        student_id=student_id,
        event_limit=event_limit,
        warning_limit=warning_limit,
    )
    if not detail:
        not_found("student not found")

    student, recent_counseling_events, recent_warnings = detail
    return {
        "ok": True,
        "student": student,
        "recent_counseling_events": recent_counseling_events,
        "recent_warnings": recent_warnings,
    }
