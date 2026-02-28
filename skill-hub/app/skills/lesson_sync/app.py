import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


def env(key: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(key, default)
    return v if v not in ("", None) else default


N8N_WEBHOOK_URL = env("N8N_WEBHOOK_URL")
N8N_X_TOKEN = env("N8N_X_TOKEN")  # 推荐：走 X-Token
N8N_BASIC_USER = env("N8N_BASIC_USER")
N8N_BASIC_PASS = env("N8N_BASIC_PASS")

if not N8N_WEBHOOK_URL:
    raise RuntimeError("Missing N8N_WEBHOOK_URL env")


app = FastAPI(title="lesson_sync")


# ---------
# 1) 业务函数：空 POST 触发 n8n
# ---------
async def trigger_lesson_sync() -> Dict[str, Any]:
    headers = {}
    auth = None

    # 方案 A：X-Token（推荐）
    if N8N_X_TOKEN:
        headers["X-Token"] = N8N_X_TOKEN

    # 方案 B：Basic Auth（nginx 层）
    if N8N_BASIC_USER and N8N_BASIC_PASS:
        auth = (N8N_BASIC_USER, N8N_BASIC_PASS)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(N8N_WEBHOOK_URL, headers=headers, auth=auth)
            r.raise_for_status()

            ct = (r.headers.get("content-type") or "").lower()
            if "application/json" in ct:
                resp = r.json()
            else:
                resp = {"text": r.text}

        return {"ok": True, "webhook": N8N_WEBHOOK_URL, "response": resp}

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"n8n webhook failed: {e.response.status_code} {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"n8n webhook error: {repr(e)}")


# ---------
# 2) MCP 风格：tools/list 与 tools/call
# ---------
class ToolsCallIn(BaseModel):
    name: str
    arguments: Dict[str, Any] = {}


@app.get("/tools/list")
async def tools_list() -> Dict[str, Any]:
    # OpenWebUI 通常需要这种 tool schema（function calling）
    return {
        "tools": [
            {
                "name": "lesson_sync_all",
                "description": "触发 n8n 执行公开课全量/批量同步（空 POST，不需要 body）",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            }
        ]
    }


@app.post("/tools/call")
async def tools_call(req: ToolsCallIn) -> Dict[str, Any]:
    if req.name == "lesson_sync_all":
        result = await trigger_lesson_sync()
        return {"ok": True, "result": result}

    raise HTTPException(status_code=404, detail=f"Unknown tool: {req.name}")


# （可选）给你一个直连调试入口，不走 tools/call 也能打
@app.post("/lesson_sync_all")
async def lesson_sync_all_direct() -> Dict[str, Any]:
    return await trigger_lesson_sync()
