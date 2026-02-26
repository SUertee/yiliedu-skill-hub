from app.core.auth import require_api_key
from app.core.errors import bad_request, not_found
from fastapi import APIRouter, Depends, Query

from .schemas import (
    LessonEvaluationsResponse,
    TeacherDetailResponse,
    TeacherLessonsResponse,
    TeacherSearchResponse,
)
from .service import (
    get_lesson_evaluations,
    get_teacher_detail,
    list_teacher_lessons,
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


@router.get("/lessons", response_model=TeacherLessonsResponse)
def teacher_lessons(
    teacher_id: str | None = Query(None, description="老师ID"),
    teacher_name: str | None = Query(None, description="老师姓名"),
    topic_keyword: str | None = Query(None, description="课题关键词"),
    limit: int = Query(20, ge=1, le=200),
    _auth=Depends(require_api_key),
):
    if not teacher_id and not teacher_name:
        bad_request("teacher_id 和 teacher_name 至少传一个")

    items = list_teacher_lessons(
        teacher_id=teacher_id,
        teacher_name=teacher_name,
        topic_keyword=topic_keyword,
        limit=limit,
    )
    return {"ok": True, "total": len(items), "items": items}


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
