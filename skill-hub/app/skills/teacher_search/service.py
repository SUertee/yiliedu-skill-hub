from typing import Any, Dict, List, Optional, Tuple

from app.core.db import fetch_all, fetch_one

from . import sql


def _clean_q(q: str) -> str:
    return q.strip().replace("老师", "")


def _to_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)


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
        "avg_total_score": float(row[6]) if row[6] is not None else None,
        "last_lesson_date": _to_str(row[7]),
        "last_eval_date": _to_str(row[8]),
        "subjects": subjects,
        "terms": terms,
        "school_years": school_years,
    }


def search_teachers(
    q: str, limit: int, offset: int
) -> Tuple[int, List[Dict[str, Any]]]:
    q2 = _clean_q(q)
    params = {
        "q_like": f"%{q2}%",
        "q_exact": q2,
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

    lesson_rows = fetch_all(
        sql.SQL_RECENT_LESSONS, {"teacher_id": teacher_id, "limit": lesson_limit}
    )
    recent_lessons = [
        {
            "lesson_id": _to_str(r[0]),
            "lesson_date": _to_str(r[1]),
            "school_year": r[2],
            "term": r[3],
            "period_no": r[4],
            "subject": r[5],
            "class_name": r[6],
            "topic": r[7],
            "lesson_level": r[8],
            "lesson_type": r[9],
            "school_id": _to_str(r[10]),
            "school_name": r[11],
        }
        for r in lesson_rows
    ]

    eval_rows = fetch_all(
        sql.SQL_RECENT_EVALUATIONS, {"teacher_id": teacher_id, "limit": eval_limit}
    )
    recent_evaluations = [
        {
            "evaluation_id": _to_str(r[0]),
            "lesson_id": _to_str(r[1]),
            "lesson_date": _to_str(r[2]),
            "eval_date": _to_str(r[3]),
            "total_score": float(r[4]) if r[4] is not None else None,
            "grade_text": r[5],
            "comment": r[6],
            "evaluator_user_id": _to_str(r[7]),
            "evaluator_name": r[8],
            "evaluator_employee_ref": r[9],
            "subject": r[10],
            "class_name": r[11],
            "topic": r[12],
            "school_name": r[13],
            "report_status": r[14],
            "report_url": r[15],
            "report_preview_url": r[16],
            "scores_json": r[17],
        }
        for r in eval_rows
    ]

    return summary, recent_lessons, recent_evaluations
