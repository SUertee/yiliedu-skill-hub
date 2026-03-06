import json
import requests

BASE_URL = "http://skill-hub:8000/api"
API_KEY = "super-secret-key-2026"


class Tools:
    def _headers(self):
        return {"x-api-key": API_KEY}

    def _get(self, path: str, params: dict | None = None) -> str:
        try:
            resp = requests.get(
                f"{BASE_URL}{path}",
                params=params or {},
                headers=self._headers(),
                timeout=20,
            )
            resp.raise_for_status()
            return json.dumps(resp.json(), ensure_ascii=False, indent=2)
        except Exception as e:
            return f"调用失败: {e}"

    def student_search(self, q: str, limit: int = 10, offset: int = 0) -> str:
        """按姓名/学号/班级/预警/辅导关键词搜索学生"""
        return self._get("/mlh_st_psy_search", {"q": q, "limit": limit, "offset": offset})

    def student_detail(self, student_id: str, event_limit: int = 20, warning_limit: int = 20) -> str:
        """获取学生详情（近期辅导+近期预警）"""
        return self._get(
            f"/mlh_st_psy_search/{student_id}",
            {"event_limit": event_limit, "warning_limit": warning_limit},
        )

    def counseling_events(
        self,
        q: str = "",
        student_id: str = "",
        event_type: str = "",
        counselor: str = "",
        limit: int = 20,
    ) -> str:
        """查询学生辅导事件（普通个案+特殊个案）"""
        params = {"limit": limit}
        if q.strip():
            params["q"] = q.strip()
        if student_id.strip():
            params["student_id"] = student_id.strip()
        if event_type.strip():
            params["event_type"] = event_type.strip()
        if counselor.strip():
            params["counselor"] = counselor.strip()
        return self._get("/mlh_st_psy_search/counseling_events", params)

    def warning_search(
        self,
        q: str = "",
        student_id: str = "",
        warning_level: str = "",
        warning_type: str = "",
        limit: int = 20,
    ) -> str:
        """查询学生预警记录"""
        params = {"limit": limit}
        if q.strip():
            params["q"] = q.strip()
        if student_id.strip():
            params["student_id"] = student_id.strip()
        if warning_level.strip():
            params["warning_level"] = warning_level.strip()
        if warning_type.strip():
            params["warning_type"] = warning_type.strip()
        return self._get("/mlh_st_psy_search/warnings", params)
