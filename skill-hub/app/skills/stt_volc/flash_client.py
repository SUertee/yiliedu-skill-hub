from __future__ import annotations

import base64
import json
import uuid
from typing import Any

import requests

from .env import env


def extract_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()

    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            text = extract_text(item)
            if text and text not in parts:
                parts.append(text)
        return ' '.join(parts).strip()

    if not isinstance(value, dict):
        return ''

    for key in ('text', 'transcript', 'utterance_text', 'recognition_text'):
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()

    for key in ('utterances', 'segments', 'results', 'items'):
        if key in value:
            text = extract_text(value[key])
            if text:
                return text

    for key in ('result', 'response', 'payload_msg', 'data'):
        if key in value:
            text = extract_text(value[key])
            if text:
                return text

    parts: list[str] = []
    for nested in value.values():
        text = extract_text(nested)
        if text and text not in parts:
            parts.append(text)
    return ' '.join(parts).strip()


def transcript_from_result(result: dict[str, Any]) -> str:
    text = extract_text(result)
    if text:
        return text
    raise RuntimeError('Unable to extract transcript text from Volcengine response')


def recognize_via_flash(
    audio_bytes: bytes,
    *,
    audio_format: str,
    language: str | None,
    model_name: str,
) -> dict[str, Any]:
    api_url = env(
        'STT_VOLC_FLASH_API_URL',
        'https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash',
    )
    app_id = env('STT_VOLC_APP_ID')
    access_token = env('STT_VOLC_ACCESS_TOKEN')
    resource_id = env('STT_VOLC_FLASH_RESOURCE_ID', 'volc.bigasr.auc_turbo')

    if not app_id or not access_token:
        raise RuntimeError('Missing STT_VOLC_APP_ID or STT_VOLC_ACCESS_TOKEN in app/skills/.env')

    request_id = str(uuid.uuid4())
    headers = {
        'Content-Type': 'application/json',
        'X-Api-App-Key': app_id,
        'X-Api-Access-Key': access_token,
        'X-Api-Resource-Id': resource_id,
        'X-Api-Request-Id': request_id,
        'X-Api-Sequence': '-1',
    }

    request_payload: dict[str, Any] = {
        'model_name': model_name,
        'audio_format': audio_format,
    }
    if language:
        request_payload['language'] = language

    payload = {
        'user': {'uid': app_id},
        'audio': {
            'format': audio_format,
            'data': base64.b64encode(audio_bytes).decode('utf-8'),
        },
        'request': request_payload,
    }

    response = requests.post(api_url, headers=headers, json=payload, timeout=180)
    response.raise_for_status()
    data = response.json()

    if isinstance(data, dict) and data.get('code') not in (None, 0, '0'):
        detail = data.get('message') or data.get('msg') or json.dumps(data, ensure_ascii=False)
        raise RuntimeError(f'Volcengine flash error: {detail}')

    return data
