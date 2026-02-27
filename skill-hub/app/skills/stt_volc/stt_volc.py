from __future__ import annotations

import gzip
import json
import os
import struct
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
import websockets


router = APIRouter(prefix="/api/stt_volc", tags=["stt_volc"])

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def _load_local_env() -> None:
    if not _ENV_PATH.exists():
        return

    for raw_line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'").strip('"'))


def _env(key: str, default: str = "") -> str:
    _load_local_env()
    return os.getenv(key, default).strip()


def _gzip(data: bytes) -> bytes:
    return gzip.compress(data)


def _build_header(message_type: int, flags: int, serialization: int, compression: int) -> bytes:
    return bytes(
        [
            0x11,  # protocol v1, 4-byte header
            ((message_type & 0x0F) << 4) | (flags & 0x0F),
            ((serialization & 0x0F) << 4) | (compression & 0x0F),
            0x00,
        ]
    )


def _build_full_client_request(payload: dict[str, Any]) -> bytes:
    payload_bytes = _gzip(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    header = _build_header(message_type=0x1, flags=0x0, serialization=0x1, compression=0x1)
    return header + struct.pack(">I", len(payload_bytes)) + payload_bytes


def _build_audio_request(chunk: bytes, sequence: int, is_last: bool) -> bytes:
    compressed = _gzip(chunk)
    flags = 0x3 if is_last else 0x1
    seq_num = -sequence if is_last else sequence
    header = _build_header(message_type=0x2, flags=flags, serialization=0x0, compression=0x1)
    return header + struct.pack(">i", seq_num) + struct.pack(">I", len(compressed)) + compressed


def _parse_server_message(message: bytes) -> dict[str, Any]:
    if len(message) < 4:
        raise RuntimeError("Invalid websocket frame: header too short")

    header = message[:4]
    header_size = (header[0] & 0x0F) * 4
    message_type = (header[1] >> 4) & 0x0F
    flags = header[1] & 0x0F
    serialization = (header[2] >> 4) & 0x0F
    compression = header[2] & 0x0F
    body = message[header_size:]

    if message_type == 0xF:
        if len(body) < 8:
            raise RuntimeError("Invalid server error frame")
        error_code = struct.unpack(">I", body[:4])[0]
        error_size = struct.unpack(">I", body[4:8])[0]
        error_message = body[8 : 8 + error_size].decode("utf-8", errors="replace")
        raise RuntimeError(f"Volcengine server error {error_code}: {error_message}")

    if message_type != 0x9:
        return {"message_type": message_type, "flags": flags}

    if len(body) < 8:
        raise RuntimeError("Invalid server response frame")

    sequence = struct.unpack(">i", body[:4])[0]
    payload_size = struct.unpack(">I", body[4:8])[0]
    payload = body[8 : 8 + payload_size]

    if compression == 0x1:
        payload = gzip.decompress(payload)

    if serialization == 0x1:
        parsed = json.loads(payload.decode("utf-8"))
    else:
        parsed = {"raw_payload": payload.decode("utf-8", errors="replace")}

    return {"sequence": sequence, "data": parsed, "flags": flags}


def _guess_format(upload: UploadFile) -> str:
    filename = (upload.filename or "").lower()
    content_type = (upload.content_type or "").lower()

    if filename.endswith(".wav") or "wav" in content_type:
        return "wav"
    if filename.endswith(".ogg") or "ogg" in content_type:
        return "ogg"
    if filename.endswith(".mp3") or "mpeg" in content_type or "mp3" in content_type:
        return "mp3"
    return "pcm"


def _chunk_size(fmt: str, rate: int, bits: int, channel: int) -> int:
    if fmt in {"pcm", "wav"}:
        bytes_per_second = rate * max(bits // 8, 1) * channel
        # 200ms packet, as recommended by Volcengine.
        return max(bytes_per_second // 5, 1)
    return 8192


async def _recognize_via_websocket(
    audio_bytes: bytes,
    *,
    audio_format: str,
    sample_rate: int,
    bits: int,
    channel: int,
    language: str | None,
    model_name: str,
    show_utterances: bool,
    enable_itn: bool,
    enable_punc: bool,
    enable_ddc: bool,
    result_type: str,
    use_nostream: bool,
) -> dict[str, Any]:
    api_url = _env(
        "STT_VOLC_API_URL",
        "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_nostream"
        if use_nostream
        else "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_async",
    )
    app_id = _env("STT_VOLC_APP_ID")
    access_token = _env("STT_VOLC_ACCESS_TOKEN")
    resource_id = _env("STT_VOLC_RESOURCE_ID", "volc.seedasr.sauc.duration")

    if not app_id or not access_token:
        raise RuntimeError("Missing STT_VOLC_APP_ID or STT_VOLC_ACCESS_TOKEN in app/skills/.env")

    connect_id = str(uuid.uuid4())
    headers = {
        "X-Api-App-Key": app_id,
        "X-Api-Access-Key": access_token,
        "X-Api-Resource-Id": resource_id,
        "X-Api-Connect-Id": connect_id,
    }

    payload = {
        "user": {"uid": "skill-hub"},
        "audio": {
            "format": audio_format,
            "codec": "opus" if audio_format == "ogg" else "raw",
            "rate": sample_rate,
            "bits": bits,
            "channel": channel,
        },
        "request": {
            "model_name": model_name,
            "enable_itn": enable_itn,
            "enable_punc": enable_punc,
            "enable_ddc": enable_ddc,
            "show_utterances": show_utterances,
            "result_type": result_type,
        },
    }
    if use_nostream and language:
        payload["audio"]["language"] = language

    chunk_size = _chunk_size(audio_format, sample_rate, bits, channel)
    chunks = [audio_bytes[i : i + chunk_size] for i in range(0, len(audio_bytes), chunk_size)] or [b""]

    latest_result: dict[str, Any] | None = None
    responses: list[dict[str, Any]] = []

    async with websockets.connect(api_url, additional_headers=headers, max_size=None) as ws:
        response_headers = dict(ws.response_headers)
        await ws.send(_build_full_client_request(payload))
        first_response = _parse_server_message(await ws.recv())
        responses.append(first_response)
        if "data" in first_response:
            latest_result = first_response["data"]

        for index, chunk in enumerate(chunks, start=1):
            is_last = index == len(chunks)
            await ws.send(_build_audio_request(chunk, sequence=index, is_last=is_last))
            frame = _parse_server_message(await ws.recv())
            responses.append(frame)
            if "data" in frame:
                latest_result = frame["data"]

    return {
        "connect_id": connect_id,
        "log_id": response_headers.get("X-Tt-Logid"),
        "resource_id": resource_id,
        "api_url": api_url,
        "response": latest_result or {},
        "frames": responses,
    }


@router.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: str | None = Form(None),
    sample_rate: int = Form(16000),
    bits: int = Form(16),
    channel: int = Form(1),
    model_name: str = Form("bigmodel"),
    show_utterances: bool = Form(True),
    enable_itn: bool = Form(True),
    enable_punc: bool = Form(True),
    enable_ddc: bool = Form(False),
    result_type: str = Form("full"),
    use_nostream: bool = Form(True),
):
    """
    Transcribe an uploaded audio file via Volcengine large-model streaming ASR.

    Default mode uses bigmodel_nostream for higher accuracy.
    """
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="empty audio file")

    audio_format = _guess_format(file)

    try:
        result = await _recognize_via_websocket(
            audio_bytes,
            audio_format=audio_format,
            sample_rate=sample_rate,
            bits=bits,
            channel=channel,
            language=language,
            model_name=model_name,
            show_utterances=show_utterances,
            enable_itn=enable_itn,
            enable_punc=enable_punc,
            enable_ddc=enable_ddc,
            result_type=result_type,
            use_nostream=use_nostream,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"volc stt failed: {exc}") from exc

    return result
