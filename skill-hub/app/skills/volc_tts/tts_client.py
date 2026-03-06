from __future__ import annotations

import base64
import json
import uuid
from typing import Any

import requests

from .env import env


SUCCESS_CODES = {None, 0, '0', 3000, '3000', 20000000, '20000000'}


class TTSResult(dict):
    audio_bytes: bytes


def _to_float(value: Any, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def synthesize_via_volc(
    *,
    text: str,
    voice_type: str | None = None,
    encoding: str | None = None,
    speed_ratio: float | None = None,
    volume_ratio: float | None = None,
    pitch_ratio: float | None = None,
    emotion: str | None = None,
    language: str | None = None,
) -> tuple[bytes, dict[str, Any]]:
    api_url = env('TTS_VOLC_API_URL', 'https://openspeech.bytedance.com/api/v1/tts')
    app_id = env('TTS_VOLC_APP_ID')
    access_token = env('TTS_VOLC_ACCESS_TOKEN')
    cluster = env('TTS_VOLC_CLUSTER', 'volcano_tts')
    uid = env('TTS_VOLC_UID', 'skill-hub')
    timeout_seconds = _to_float(env('TTS_VOLC_TIMEOUT_SECONDS', '60'), 60.0)

    if not app_id or not access_token:
        raise RuntimeError('Missing TTS_VOLC_APP_ID or TTS_VOLC_ACCESS_TOKEN in app/skills/.env')

    req_id = str(uuid.uuid4())
    out_encoding = (encoding or env('TTS_VOLC_ENCODING', 'mp3')).lower()
    out_voice = voice_type or env('TTS_VOLC_VOICE_TYPE', 'BV001_streaming')

    audio_payload: dict[str, Any] = {
        'voice_type': out_voice,
        'encoding': out_encoding,
        'speed_ratio': _to_float(speed_ratio, _to_float(env('TTS_VOLC_SPEED_RATIO', '1.0'), 1.0)),
        'volume_ratio': _to_float(volume_ratio, _to_float(env('TTS_VOLC_VOLUME_RATIO', '1.0'), 1.0)),
        'pitch_ratio': _to_float(pitch_ratio, _to_float(env('TTS_VOLC_PITCH_RATIO', '1.0'), 1.0)),
    }

    if emotion:
        audio_payload['emotion'] = emotion
    if language:
        audio_payload['language'] = language

    payload = {
        'app': {
            'appid': app_id,
            'token': access_token,
            'cluster': cluster,
        },
        'user': {
            'uid': uid,
        },
        'audio': audio_payload,
        'request': {
            'reqid': req_id,
            'text': text,
            'text_type': 'plain',
            'operation': 'query',
        },
    }

    header_candidates = [
        {'Authorization': f'Bearer;{access_token}', 'Content-Type': 'application/json'},
        {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'},
        {'Content-Type': 'application/json'},
    ]

    response = None
    data = None
    last_error: Exception | None = None
    for headers in header_candidates:
        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=timeout_seconds)
            response.raise_for_status()
            data = response.json()
            break
        except Exception as exc:
            last_error = exc
            continue

    if data is None:
        raise RuntimeError(f'Volcengine tts request failed: {last_error}')

    code = data.get('code') if isinstance(data, dict) else None
    audio_b64 = data.get('data') if isinstance(data, dict) else None
    if code not in SUCCESS_CODES or not isinstance(audio_b64, str) or not audio_b64:
        detail = data.get('message') if isinstance(data, dict) else None
        if not detail:
            detail = data.get('msg') if isinstance(data, dict) else None
        if not detail:
            detail = json.dumps(data, ensure_ascii=False)
        raise RuntimeError(f'Volcengine tts error: {detail}')

    try:
        audio_bytes = base64.b64decode(audio_b64)
    except Exception as exc:
        raise RuntimeError(f'Invalid base64 audio from Volcengine: {exc}') from exc

    return audio_bytes, {
        'reqid': data.get('reqid') if isinstance(data, dict) else req_id,
        'code': code,
        'message': data.get('message') if isinstance(data, dict) else None,
        'api_url': api_url,
        'voice_type': out_voice,
        'encoding': out_encoding,
        'cluster': cluster,
    }
