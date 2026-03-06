from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core.db import fetch_all, fetch_one

from . import sql


def _clean_q(q: Optional[str]) -> str:
    if not q:
        return ""

    cleaned = q.strip()
    for token in ("学生", "同学", "心理", "辅导", "咨询", "个案", "预警", "档案"):
        cleaned = cleaned.replace(token, "")
    return " ".join(cleaned.split())


def _search_text(q: Optional[str]) -> str:
    cleaned = _clean_q(q)
    return cleaned or ""


def _to_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    return int(value)


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


def _student_row_to_summary(row: tuple) -> Dict[str, Any]:
    return {
        "student_id": _to_str(row[0]),
        "student_number": row[1],
        "name": row[2],
        "class_id": row[3],
        "class_name": row[4],
        "grade_level": row[5],
        "gender": row[6],
        "age_years": _to_int(row[7]),
        "semester": row[8],
        "fill_date": _to_str(row[9]),
        "health_status": row[10],
        "warning_level": row[11],
        "warning_type": row[12],
        "warning_date": _to_str(row[13]),
        "latest_counseling_type": row[14],
        "latest_counseling_issue": row[15],
        "latest_special_type": row[16],
        "latest_session_time": _to_str(row[17]),
        "latest_appointment_date": _to_str(row[18]),
        "latest_room": row[19],
        "report_status": row[20],
        "report_url": row[21],
        "report_preview_url": row[22],
        "event_count": _to_int(row[23]) or 0,
        "warning_count": _to_int(row[24]) or 0,
    }


def _event_row_to_item(row: tuple) -> Dict[str, Any]:
    return {
        "source_id": _to_str(row[0]),
        "student_id": _to_str(row[1]),
        "student_name": row[2],
        "class_name": row[3],
        "event_type": row[4],
        "session_time": _to_str(row[5]),
        "counseling_date": _to_str(row[6]),
        "counseling_type": row[7],
        "special_counseling_type": row[8],
        "counseling_issue": row[9],
        "counseling_motivation": row[10],
        "counseling_process": row[11],
        "counseling_result": row[12],
        "issue_summary": row[13],
        "event_text": row[14],
        "session_duration": _to_int(row[15]),
        "counselor": row[16],
        "attachment": row[17],
        "created_at": _to_str(row[18]),
        "updated_at": _to_str(row[19]),
    }


def _warning_row_to_item(row: tuple) -> Dict[str, Any]:
    return {
        "warning_id": _to_str(row[0]),
        "student_id": _to_str(row[1]),
        "student_name": row[2],
        "class_name": row[3],
        "semester": row[4],
        "warning_level": row[5],
        "warning_type": row[6],
        "warning_reason": row[7],
        "warning_date": _to_str(row[8]),
        "handler": row[9],
        "created_at": _to_str(row[10]),
        "updated_at": _to_str(row[11]),
    }


def search_students(
    *,
    q: Optional[str] = None,
    student_id: Optional[str] = None,
    class_name: Optional[str] = None,
    grade_level: Optional[str] = None,
    warning_level: Optional[str] = None,
    start_fill_date: Optional[date] = None,
    end_fill_date: Optional[date] = None,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[int, List[Dict[str, Any]]]:
    params = {
        **_build_text_params(q),
        "student_id": student_id.strip() if student_id else None,
        "class_name_kw": _like(class_name),
        "grade_level": grade_level.strip() if grade_level else None,
        "warning_level": warning_level.strip() if warning_level else None,
        "start_fill_date": _to_str(start_fill_date),
        "end_fill_date": _to_str(end_fill_date),
        "limit": limit,
        "offset": offset,
    }

    total_row = fetch_one(sql.SQL_COUNT_STUDENTS, params)
    total = int(total_row[0]) if total_row else 0
    rows = fetch_all(sql.SQL_SEARCH_STUDENTS, params)
    return total, [_student_row_to_summary(r) for r in rows]


def get_student_detail(
    student_id: str,
    event_limit: int = 20,
    warning_limit: int = 20,
):
    base = fetch_one(sql.SQL_GET_STUDENT_BY_ID, {"student_id": student_id})
    if not base:
        return None

    student = _student_row_to_summary(base)
    _, recent_events = search_counseling_events(
        student_id=student_id,
        limit=event_limit,
        offset=0,
    )
    _, recent_warnings = search_warnings(
        student_id=student_id,
        limit=warning_limit,
        offset=0,
    )
    return student, recent_events, recent_warnings


def search_counseling_events(
    *,
    q: Optional[str] = None,
    student_id: Optional[str] = None,
    event_type: Optional[str] = None,
    counselor: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[int, List[Dict[str, Any]]]:
    params = {
        **_build_text_params(q),
        "student_id": student_id.strip() if student_id else None,
        "event_type": event_type.strip() if event_type else None,
        "counselor_kw": _like(counselor),
        "start_time": _to_str(start_time),
        "end_time": _to_str(end_time),
        "limit": limit,
        "offset": offset,
    }
    total_row = fetch_one(sql.SQL_COUNT_COUNSELING_EVENTS, params)
    total = int(total_row[0]) if total_row else 0
    rows = fetch_all(sql.SQL_SEARCH_COUNSELING_EVENTS, params)
    return total, [_event_row_to_item(r) for r in rows]


def search_warnings(
    *,
    q: Optional[str] = None,
    student_id: Optional[str] = None,
    warning_level: Optional[str] = None,
    warning_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[int, List[Dict[str, Any]]]:
    params = {
        **_build_text_params(q),
        "student_id": student_id.strip() if student_id else None,
        "warning_level": warning_level.strip() if warning_level else None,
        "warning_type": warning_type.strip() if warning_type else None,
        "start_date": _to_str(start_date),
        "end_date": _to_str(end_date),
        "limit": limit,
        "offset": offset,
    }
    total_row = fetch_one(sql.SQL_COUNT_WARNINGS, params)
    total = int(total_row[0]) if total_row else 0
    rows = fetch_all(sql.SQL_SEARCH_WARNINGS, params)
    return total, [_warning_row_to_item(r) for r in rows]


def general_search(q: str, limit: int = 8) -> Dict[str, Any]:
    student_total, students = search_students(q=q, limit=limit, offset=0)
    event_total, counseling_events = search_counseling_events(q=q, limit=limit, offset=0)
    warning_total, warnings = search_warnings(q=q, limit=limit, offset=0)

    matched_classes: List[str] = []
    for item in students:
        class_name = item.get("class_name")
        if class_name and class_name not in matched_classes:
            matched_classes.append(class_name)
    for item in warnings:
        class_name = item.get("class_name")
        if class_name and class_name not in matched_classes:
            matched_classes.append(class_name)

    matched_warning_levels: List[str] = []
    for item in warnings:
        level = item.get("warning_level")
        if level and level not in matched_warning_levels:
            matched_warning_levels.append(level)

    return {
        "q": q,
        "summary": {
            "student_matches": student_total,
            "counseling_event_matches": event_total,
            "warning_matches": warning_total,
            "matched_classes": matched_classes[:8],
            "matched_warning_levels": matched_warning_levels[:8],
        },
        "students": students,
        "counseling_events": counseling_events,
        "warnings": warnings,
        "extra": {
            "event_type_options": ["counseling_record", "counseling_special"],
        },
    }
