from __future__ import annotations

import base64
from typing import Any, Literal

from app.core.auth import require_api_key
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field

from .tts_client import synthesize_via_volc


router = APIRouter(prefix='/api/volc_tts', tags=['volc_tts'])


MEDIA_TYPES = {
    'mp3': 'audio/mpeg',
    'wav': 'audio/wav',
    'pcm': 'audio/pcm',
    'ogg': 'audio/ogg',
    'aac': 'audio/aac',
    'opus': 'audio/ogg',
    'flac': 'audio/flac',
}


def _media_type(fmt: str) -> str:
    return MEDIA_TYPES.get((fmt or '').lower(), 'application/octet-stream')


class OpenAITTSRequest(BaseModel):
    model_config = ConfigDict(extra='allow')

    model: str = 'volc_tts'
    input: str = Field(..., min_length=1)
    voice: str | None = None
    response_format: Literal['mp3', 'wav', 'pcm', 'ogg', 'aac', 'opus', 'flac'] = 'mp3'
    speed: float | None = Field(None, ge=0.2, le=3.0)


class VolcTTSRequest(BaseModel):
    model_config = ConfigDict(extra='allow')

    text: str = Field(..., min_length=1)
    voice_type: str | None = None
    encoding: Literal['mp3', 'wav', 'pcm', 'ogg', 'aac', 'opus', 'flac'] = 'mp3'
    speed_ratio: float | None = Field(None, ge=0.2, le=3.0)
    volume_ratio: float | None = Field(None, ge=0.0, le=3.0)
    pitch_ratio: float | None = Field(None, ge=0.1, le=3.0)
    emotion: str | None = None
    language: str | None = None
    return_base64: bool = False


@router.post('/audio/speech')
def openai_compatible_tts(req: OpenAITTSRequest, _auth=Depends(require_api_key)):
    """
    OpenAI-compatible TTS endpoint for Open WebUI.

    Open WebUI TTS settings:
    - Engine: OpenAI
    - API Base URL: http://<skill-hub-host>:8000/api/volc_tts
    - TTS Model: volc_tts (or any value)
    - TTS Voice: voice_type, e.g. BV001_streaming
    """
    try:
        audio_bytes, _meta = synthesize_via_volc(
            text=req.input,
            voice_type=req.voice,
            encoding=req.response_format,
            speed_ratio=req.speed,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f'volc tts failed: {exc}') from exc

    return Response(
        content=audio_bytes,
        media_type=_media_type(req.response_format),
        headers={
            'Content-Disposition': f'inline; filename="speech.{req.response_format}"',
        },
    )


@router.post('/synthesize')
def synthesize(req: VolcTTSRequest, _auth=Depends(require_api_key)):
    """Debug endpoint for direct Volcengine TTS access."""
    try:
        audio_bytes, meta = synthesize_via_volc(
            text=req.text,
            voice_type=req.voice_type,
            encoding=req.encoding,
            speed_ratio=req.speed_ratio,
            volume_ratio=req.volume_ratio,
            pitch_ratio=req.pitch_ratio,
            emotion=req.emotion,
            language=req.language,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f'volc tts failed: {exc}') from exc

    result: dict[str, Any] = {
        'ok': True,
        **meta,
        'audio_size': len(audio_bytes),
    }
    if req.return_base64:
        result['audio_base64'] = base64.b64encode(audio_bytes).decode('utf-8')
    return result
