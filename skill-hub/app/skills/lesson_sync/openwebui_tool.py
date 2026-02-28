import json

import requests

BASE_URL = "http://skill-hub:8000/api"  # 同网络容器名访问
API_KEY = "super-secret-key-2026"


class Tools:
    def _headers(self):
        return {"x-api-key": API_KEY}

    def _post(self, path: str, payload: dict | None = None) -> str:
        try:
            resp = requests.post(
                f"{BASE_URL}{path}",
                json=payload or {},
                headers=self._headers(),
                timeout=20,
            )
            resp.raise_for_status()
            return json.dumps(resp.json(), ensure_ascii=False, indent=2)
        except Exception as e:
            return f"调用失败: {e}"

    def sync_existing_lessons(
        self,
        dry_run: bool = False,
        source: str = "openwebui_tool",
        sync_scope: str = "existing_data",
        data_json: str = "",
    ) -> str:
        """触发 lesson_sync，同步数据库已有数据到 n8n"""
        data = {}
        if data_json.strip():
            try:
                data = json.loads(data_json)
            except Exception as e:
                return f"data_json 不是合法 JSON: {e}"

        payload = {
            "source": source,
            "sync_scope": sync_scope,
            "dry_run": dry_run,
            "data": data,
        }
        return self._post("/lesson_sync/sync", payload)
