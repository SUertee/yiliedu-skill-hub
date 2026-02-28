from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
from app.core.auth import require_api_key
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LessonSyncSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).with_name("config.env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    N8N_WEBHOOK_URL: str
    N8N_X_TOKEN: str | None = None
    N8N_TIMEOUT_SECONDS: float = 30.0


class LessonSyncRequest(BaseModel):
    source: str = Field(default="skill_hub")
    sync_scope: str = Field(default="existing_data")
    dry_run: bool = Field(default=False)
    data: dict[str, Any] = Field(default_factory=dict)


settings = LessonSyncSettings()
router = APIRouter(prefix="/api/lesson_sync", tags=["lesson_sync"])


@router.post("/sync")
async def sync_existing_data(
    payload: LessonSyncRequest | None = None,
    _auth=Depends(require_api_key),
):
    request_payload = payload or LessonSyncRequest()
    headers: dict[str, str] = {}
    if settings.N8N_X_TOKEN:
        headers["X-Token"] = settings.N8N_X_TOKEN

    try:
        async with httpx.AsyncClient(timeout=settings.N8N_TIMEOUT_SECONDS) as client:
            response = await client.post(
                settings.N8N_WEBHOOK_URL,
                json=request_payload.model_dump(),
                headers=headers,
            )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"n8n request failed: {exc}") from exc

    try:
        result: Any = response.json()
    except ValueError:
        result = response.text

    if response.is_error:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "n8n webhook returned error",
                "status_code": response.status_code,
                "result": result,
            },
        )

    return {
        "ok": True,
        "status_code": response.status_code,
        "result": result,
    }
