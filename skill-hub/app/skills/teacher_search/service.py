from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from app.core.db import fetch_all, fetch_one

from . import sql


def _clean_q(q: Optional[str]) -> str:
    if not q:
        return ""

    cleaned = q.strip()
    for token in ("老师", "教师", "公开课", "课程", "讲课"):
        cleaned = cleaned.replace(token, "")

    return " ".join(cleaned.split())


def _search_text(q: Optional[str]) -> str:
    cleaned = _clean_q(q)
    return cleaned or ""


def _to_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    return float(value)


def _to_date(value: Optional[date]) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat()


def _like(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    stripped = value.strip()
    if not stripped:
        return None
    return f"%{stripped}%"


def _build_text_params(q: Optional[str]) -> Dict[str, Any]:
    q_text = _search_text(q)
    return {
        "q_empty": not bool(q_text),
        "q_exact": q_text,
        "q_like": "%" if not q_text else f"%{q_text}%",
    }


def _teacher_row_to_summary(row: tuple) -> Dict[str, Any]:
    subjects = list(row[9]) if row[9] else []
    terms = list(row[10]) if row[10] else []
    school_years = list(row[11]) if row[11] else []

    return {
        "teacher_id": _to_str(row[0]),
        "teacher_name": row[1],
        "school_id": _to_str(row[2]),
        "school_name": row[3],
        "lesson_count": int(row[4] or 0),
        "evaluation_count": int(row[5] or 0),
        "avg_total_score": _to_float(row[6]),
        "last_lesson_date": _to_str(row[7]),
        "last_eval_date": _to_str(row[8]),
        "subjects": subjects,
        "terms": terms,
        "school_years": school_years,
    }


def _lesson_row_to_item(row: tuple) -> Dict[str, Any]:
    return {
        "lesson_id": _to_str(row[0]),
        "lesson_date": _to_str(row[1]),
        "school_year": row[2],
        "term": row[3],
        "period_no": row[4],
        "subject": row[5],
        "class_name": row[6],
        "topic": row[7],
        "lesson_level": row[8],
        "lesson_type": row[9],
        "host_user_id": _to_str(row[10]),
        "host_name": row[11],
        "school_id": _to_str(row[12]),
        "school_name": row[13],
        "evaluation_count": int(row[14] or 0),
        "avg_total_score": _to_float(row[15]),
        "last_eval_date": _to_str(row[16]),
        "report_status": row[17],
        "report_url": row[18],
        "report_preview_url": row[19],
    }


def _evaluation_row_to_item(row: tuple) -> Dict[str, Any]:
    return {
        "evaluation_id": _to_str(row[0]),
        "lesson_id": _to_str(row[1]),
        "lesson_date": _to_str(row[2]),
        "eval_date": _to_str(row[3]),
        "total_score": _to_float(row[4]),
        "grade_text": row[5],
        "comment": row[6],
        "evaluator_user_id": _to_str(row[7]),
        "evaluator_name": row[8],
        "evaluator_employee_ref": row[9],
        "subject": row[10],
        "class_name": row[11],
        "topic": row[12],
        "school_name": row[13],
        "host_user_id": _to_str(row[14]),
        "host_name": row[15],
        "report_status": row[16],
        "report_url": row[17],
        "report_preview_url": row[18],
        "scores_json": list(row[19]) if row[19] else [],
    }


def search_teachers(
    q: str, limit: int, offset: int
) -> Tuple[int, List[Dict[str, Any]]]:
    params = {
        **_build_text_params(q),
        "limit": limit,
        "offset": offset,
    }
    total_row = fetch_one(sql.SQL_COUNT_TEACHERS, params)
    total = int(total_row[0]) if total_row else 0

    rows = fetch_all(sql.SQL_SEARCH_TEACHERS, params)
    items = [_teacher_row_to_summary(r) for r in rows]
    return total, items


def get_teacher_detail(teacher_id: str, lesson_limit: int = 10, eval_limit: int = 50):
    base = fetch_one(sql.SQL_GET_TEACHER_BY_ID, {"teacher_id": teacher_id})
    if not base:
        return None

    summary = _teacher_row_to_summary(base)
    _, recent_lessons = search_lessons(teacher_id=teacher_id, limit=lesson_limit, offset=0)
    _, recent_evaluations = search_evaluations(
        teacher_id=teacher_id, limit=eval_limit, offset=0
    )
    return summary, recent_lessons, recent_evaluations


def search_lessons(
    *,
    q: Optional[str] = None,
    teacher_id: Optional[str] = None,
    teacher_name: Optional[str] = None,
    topic_keyword: Optional[str] = None,
    school_id: Optional[str] = None,
    school_name: Optional[str] = None,
    subject: Optional[str] = None,
    term: Optional[str] = None,
    school_year: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_avg_score: Optional[float] = None,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[int, List[Dict[str, Any]]]:
    params = {
        **_build_text_params(q),
        "teacher_id": teacher_id.strip() if teacher_id else None,
        "teacher_name": teacher_name.strip() if teacher_name else None,
        "topic_kw": _like(topic_keyword),
        "school_id": school_id.strip() if school_id else None,
        "school_name_kw": _like(school_name),
        "subject": subject.strip() if subject else None,
        "term": term.strip() if term else None,
        "school_year": school_year.strip() if school_year else None,
        "start_date": _to_date(start_date),
        "end_date": _to_date(end_date),
        "min_avg_score": min_avg_score,
        "limit": limit,
        "offset": offset,
    }

    total_row = fetch_one(sql.SQL_COUNT_LESSONS, params)
    total = int(total_row[0]) if total_row else 0
    rows = fetch_all(sql.SQL_SEARCH_LESSONS, params)
    return total, [_lesson_row_to_item(r) for r in rows]


def list_teacher_lessons(
    teacher_id: Optional[str] = None,
    teacher_name: Optional[str] = None,
    topic_keyword: Optional[str] = None,
    q: Optional[str] = None,
    school_id: Optional[str] = None,
    school_name: Optional[str] = None,
    subject: Optional[str] = None,
    term: Optional[str] = None,
    school_year: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_avg_score: Optional[float] = None,
    limit: int = 20,
    offset: int = 0,
):
    return search_lessons(
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


def search_evaluations(
    *,
    q: Optional[str] = None,
    lesson_id: Optional[str] = None,
    teacher_id: Optional[str] = None,
    teacher_name: Optional[str] = None,
    evaluator_name: Optional[str] = None,
    topic_keyword: Optional[str] = None,
    school_id: Optional[str] = None,
    school_name: Optional[str] = None,
    subject: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[int, List[Dict[str, Any]]]:
    params = {
        **_build_text_params(q),
        "lesson_id": lesson_id.strip() if lesson_id else None,
        "teacher_id": teacher_id.strip() if teacher_id else None,
        "teacher_name": teacher_name.strip() if teacher_name else None,
        "evaluator_name_kw": _like(evaluator_name),
        "topic_kw": _like(topic_keyword),
        "school_id": school_id.strip() if school_id else None,
        "school_name_kw": _like(school_name),
        "subject": subject.strip() if subject else None,
        "min_score": min_score,
        "max_score": max_score,
        "limit": limit,
        "offset": offset,
    }

    total_row = fetch_one(sql.SQL_COUNT_EVALUATIONS, params)
    total = int(total_row[0]) if total_row else 0
    rows = fetch_all(sql.SQL_SEARCH_EVALUATIONS, params)
    return total, [_evaluation_row_to_item(r) for r in rows]


def get_lesson_evaluations(lesson_id: str, limit: int = 100):
    _, items = search_evaluations(lesson_id=lesson_id, limit=limit, offset=0)
    return items


def get_topic_evaluations(
    teacher_name: str,
    topic: str,
    limit: int = 20,
):
    teacher_name_clean = teacher_name.strip()
    topic_clean = topic.strip()
    if not teacher_name_clean or not topic_clean:
        return None

    _, candidates = search_lessons(
        teacher_name=teacher_name_clean,
        topic_keyword=topic_clean,
        limit=20,
        offset=0,
    )
    if not candidates:
        return None

    matched = None
    for lesson in candidates:
        if (lesson.get("topic") or "").strip() == topic_clean:
            matched = lesson
            break
    if matched is None:
        matched = candidates[0]

    lesson_id = matched["lesson_id"]
    total, items = search_evaluations(lesson_id=lesson_id, limit=limit, offset=0)
    if not items:
        return None

    return {
        "teacher_name": teacher_name_clean,
        "topic": topic_clean,
        "matched_lesson_id": lesson_id,
        "matched_lesson": matched,
        "total": total,
        "items": items,
    }


def general_search(q: str, limit: int = 8) -> Dict[str, Any]:
    teacher_total, teachers = search_teachers(q=q, limit=limit, offset=0)
    lesson_total, lessons = search_lessons(q=q, limit=limit, offset=0)
    evaluation_total, evaluations = search_evaluations(q=q, limit=limit, offset=0)

    matched_schools: List[str] = []
    for item in teachers:
        school_name = item.get("school_name")
        if school_name and school_name not in matched_schools:
            matched_schools.append(school_name)
    for item in lessons:
        school_name = item.get("school_name")
        if school_name and school_name not in matched_schools:
            matched_schools.append(school_name)

    matched_subjects: List[str] = []
    for item in lessons:
        subject = item.get("subject")
        if subject and subject not in matched_subjects:
            matched_subjects.append(subject)

    return {
        "q": q,
        "summary": {
            "teacher_matches": teacher_total,
            "lesson_matches": lesson_total,
            "evaluation_matches": evaluation_total,
            "matched_schools": matched_schools[:8],
            "matched_subjects": matched_subjects[:8],
        },
        "teachers": teachers,
        "lessons": lessons,
        "evaluations": evaluations,
    }
