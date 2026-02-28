import json
import requests

BASE_URL = "http://skill-hub:8000/api"  # 同网络容器名访问
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

    def teacher_search(self, q: str, limit: int = 10, offset: int = 0) -> str:
        """按姓名/关键词/老师ID搜索老师摘要信息"""
        return self._get(
            "/teacher_search",
            {"q": q, "limit": limit, "offset": offset},
        )

    def teacher_detail(
        self, teacher_id: str, lesson_limit: int = 10, eval_limit: int = 50
    ) -> str:
        """获取老师详情（近期课次+近期评价）"""
        return self._get(
            f"/teacher_search/{teacher_id}",
            {"lesson_limit": lesson_limit, "eval_limit": eval_limit},
        )

    def teacher_lessons(
        self,
        teacher_name: str = "",
        teacher_id: str = "",
        topic_keyword: str = "",
        limit: int = 20,
    ) -> str:
        """查询老师上过哪些课（基于 v_eval_flat）"""
        params = {"limit": limit}
        if teacher_name.strip():
            params["teacher_name"] = teacher_name.strip()
        if teacher_id.strip():
            params["teacher_id"] = teacher_id.strip()
        if topic_keyword.strip():
            params["topic_keyword"] = topic_keyword.strip()
        return self._get("/teacher_search/lessons", params)

    def lesson_evaluations(self, lesson_id: str, limit: int = 100) -> str:
        """查询某一节课的详细评价"""
        return self._get(
            f"/teacher_search/lesson/{lesson_id}/evaluations",
            {"limit": limit},
        )
