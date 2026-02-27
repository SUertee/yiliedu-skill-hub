from datetime import date

from app.core.auth import require_api_key
from app.core.errors import bad_request, not_found
from fastapi import APIRouter, Depends, Query

from .schemas import (
    EvaluationSearchResponse,
    GeneralSearchResponse,
    LessonEvaluationsResponse,
    TeacherDetailResponse,
    TeacherLessonsResponse,
    TeacherSearchResponse,
    TopicEvaluationsResponse,
)
from .service import (
    general_search,
    get_lesson_evaluations,
    get_teacher_detail,
    get_topic_evaluations,
    list_teacher_lessons,
    search_evaluations,
    search_teachers,
)

router = APIRouter(prefix="/api/teacher_search", tags=["teacher_search"])


@router.get("", response_model=TeacherSearchResponse)
def teacher_search(
    q: str = Query(..., min_length=1, description="老师姓名/关键词/ID"),
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    _auth=Depends(require_api_key),
):
    if not q.strip():
        bad_request("q 不能为空")

    total, items = search_teachers(q=q, limit=limit, offset=offset)
    return {"ok": True, "q": q, "total": total, "items": items}


@router.get("/query", response_model=GeneralSearchResponse)
def teacher_search_query(
    q: str = Query(..., min_length=1, description="自然语言关键词，如老师、课题、学科、学校"),
    limit: int = Query(8, ge=1, le=30),
    _auth=Depends(require_api_key),
):
    if not q.strip():
        bad_request("q 不能为空")

    return {"ok": True, **general_search(q=q, limit=limit)}


@router.get("/lessons", response_model=TeacherLessonsResponse)
def teacher_lessons(
    q: str | None = Query(None, description="通用关键词：老师、课题、学科、学校、学期"),
    teacher_id: str | None = Query(None, description="老师ID"),
    teacher_name: str | None = Query(None, description="老师姓名"),
    topic_keyword: str | None = Query(None, description="课题关键词"),
    school_id: str | None = Query(None, description="学校ID"),
    school_name: str | None = Query(None, description="学校名称"),
    subject: str | None = Query(None, description="学科"),
    term: str | None = Query(None, description="学期"),
    school_year: str | None = Query(None, description="学年"),
    start_date: date | None = Query(None, description="起始日期"),
    end_date: date | None = Query(None, description="结束日期"),
    min_avg_score: float | None = Query(None, ge=0, description="最低平均分"),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _auth=Depends(require_api_key),
):
    total, items = list_teacher_lessons(
        q=q,
        teacher_id=teacher_id,
        teacher_name=teacher_name,
        topic_keyword=topic_keyword,
        school_id=school_id,
        school_name=school_name,
        subject=subject,
        term=term,
        school_year=school_year,
        start_date=start_date,
        end_date=end_date,
        min_avg_score=min_avg_score,
        limit=limit,
        offset=offset,
    )
    return {"ok": True, "q": q, "total": total, "items": items}


@router.get("/evaluations", response_model=EvaluationSearchResponse)
def teacher_evaluations(
    q: str | None = Query(None, description="通用关键词：老师、评语、课题、学科、学校"),
    lesson_id: str | None = Query(None, description="公开课ID"),
    teacher_id: str | None = Query(None, description="授课老师ID"),
    teacher_name: str | None = Query(None, description="授课老师姓名"),
    evaluator_name: str | None = Query(None, description="评价人姓名"),
    topic_keyword: str | None = Query(None, description="课题关键词"),
    school_id: str | None = Query(None, description="学校ID"),
    school_name: str | None = Query(None, description="学校名称"),
    subject: str | None = Query(None, description="学科"),
    min_score: float | None = Query(None, ge=0, description="最低分"),
    max_score: float | None = Query(None, ge=0, description="最高分"),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _auth=Depends(require_api_key),
):
    total, items = search_evaluations(
        q=q,
        lesson_id=lesson_id,
        teacher_id=teacher_id,
        teacher_name=teacher_name,
        evaluator_name=evaluator_name,
        topic_keyword=topic_keyword,
        school_id=school_id,
        school_name=school_name,
        subject=subject,
        min_score=min_score,
        max_score=max_score,
        limit=limit,
        offset=offset,
    )
    return {"ok": True, "q": q, "total": total, "items": items}


@router.get("/lesson/{lesson_id}/evaluations", response_model=LessonEvaluationsResponse)
def lesson_evaluations(
    lesson_id: str,
    limit: int = Query(100, ge=1, le=500),
    _auth=Depends(require_api_key),
):
    items = get_lesson_evaluations(lesson_id=lesson_id, limit=limit)
    if not items:
        not_found("lesson not found or no evaluations")

    return {"ok": True, "lesson_id": lesson_id, "total": len(items), "items": items}


@router.get("/topic/evaluations", response_model=TopicEvaluationsResponse)
def topic_evaluations(
    teacher_name: str = Query(..., min_length=1, description="老师姓名"),
    topic: str = Query(..., min_length=1, description="课题名称"),
    limit: int = Query(20, ge=1, le=200),
    _auth=Depends(require_api_key),
):
    result = get_topic_evaluations(teacher_name=teacher_name, topic=topic, limit=limit)
    if not result:
        not_found("no matched lesson/evaluations for teacher_name + topic")
    return {"ok": True, **result}


@router.get("/{teacher_id}", response_model=TeacherDetailResponse)
def teacher_detail(
    teacher_id: str,
    lesson_limit: int = Query(10, ge=1, le=100),
    eval_limit: int = Query(50, ge=1, le=200),
    _auth=Depends(require_api_key),
):
    detail = get_teacher_detail(
        teacher_id=teacher_id, lesson_limit=lesson_limit, eval_limit=eval_limit
    )
    if not detail:
        not_found("teacher not found")

    summary, recent_lessons, recent_evaluations = detail
    return {
        "ok": True,
        "teacher": summary,
        "recent_lessons": recent_lessons,
        "recent_evaluations": recent_evaluations,
    }
