from __future__ import annotations

import gzip
import json
import struct
import uuid
from typing import Any

import websockets

from .audio import chunk_size
from .env import env


def _gzip(data: bytes) -> bytes:
    return gzip.compress(data)


def _build_header(message_type: int, flags: int, serialization: int, compression: int) -> bytes:
    return bytes(
        [
            0x11,
            ((message_type & 0x0F) << 4) | (flags & 0x0F),
            ((serialization & 0x0F) << 4) | (compression & 0x0F),
            0x00,
        ]
    )


def _build_full_client_request(payload: dict[str, Any]) -> bytes:
    payload_bytes = _gzip(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
    header = _build_header(message_type=0x1, flags=0x0, serialization=0x1, compression=0x1)
    return header + struct.pack('>I', len(payload_bytes)) + payload_bytes


def _build_audio_request(chunk: bytes, sequence: int, is_last: bool) -> bytes:
    compressed = _gzip(chunk)
    flags = 0x3 if is_last else 0x1
    seq_num = -sequence if is_last else sequence
    header = _build_header(message_type=0x2, flags=flags, serialization=0x0, compression=0x1)
    return header + struct.pack('>i', seq_num) + struct.pack('>I', len(compressed)) + compressed


def _parse_server_message(message: bytes) -> dict[str, Any]:
    if len(message) < 4:
        raise RuntimeError('Invalid websocket frame: header too short')

    header = message[:4]
    header_size = (header[0] & 0x0F) * 4
    message_type = (header[1] >> 4) & 0x0F
    flags = header[1] & 0x0F
    serialization = (header[2] >> 4) & 0x0F
    compression = header[2] & 0x0F
    body = message[header_size:]

    if message_type == 0xF:
        if len(body) < 8:
            raise RuntimeError('Invalid server error frame')
        error_code = struct.unpack('>I', body[:4])[0]
        error_size = struct.unpack('>I', body[4:8])[0]
        error_message = body[8 : 8 + error_size].decode('utf-8', errors='replace')
        raise RuntimeError(f'Volcengine server error {error_code}: {error_message}')

    if message_type != 0x9:
        return {'message_type': message_type, 'flags': flags}

    if len(body) < 8:
        raise RuntimeError('Invalid server response frame')

    sequence = struct.unpack('>i', body[:4])[0]
    payload_size = struct.unpack('>I', body[4:8])[0]
    payload = body[8 : 8 + payload_size]

    if compression == 0x1:
        payload = gzip.decompress(payload)

    if serialization == 0x1:
        parsed = json.loads(payload.decode('utf-8'))
    else:
        parsed = {'raw_payload': payload.decode('utf-8', errors='replace')}

    return {'sequence': sequence, 'data': parsed, 'flags': flags}


def _response_headers_map(ws: Any) -> dict[str, str]:
    headers = getattr(ws, 'response_headers', None)
    if headers is None:
        return {}

    if hasattr(headers, 'raw_items'):
        return {k.lower(): v for k, v in headers.raw_items()}

    if hasattr(headers, 'items'):
        return {str(k).lower(): str(v) for k, v in headers.items()}

    return {}


async def recognize_via_websocket(
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
    api_url = env(
        'STT_VOLC_API_URL',
        'wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_nostream'
        if use_nostream
        else 'wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_async',
    )
    app_id = env('STT_VOLC_APP_ID')
    access_token = env('STT_VOLC_ACCESS_TOKEN')
    resource_id = env('STT_VOLC_RESOURCE_ID', 'volc.seedasr.sauc.duration')

    if not app_id or not access_token:
        raise RuntimeError('Missing STT_VOLC_APP_ID or STT_VOLC_ACCESS_TOKEN in app/skills/.env')

    connect_id = str(uuid.uuid4())
    headers = {
        'X-Api-App-Key': app_id,
        'X-Api-Access-Key': access_token,
        'X-Api-Resource-Id': resource_id,
        'X-Api-Connect-Id': connect_id,
    }

    payload = {
        'user': {'uid': 'skill-hub'},
        'audio': {
            'format': audio_format,
            'codec': 'opus' if audio_format == 'ogg' else 'raw',
            'rate': sample_rate,
            'bits': bits,
            'channel': channel,
        },
        'request': {
            'model_name': model_name,
            'enable_itn': enable_itn,
            'enable_punc': enable_punc,
            'enable_ddc': enable_ddc,
            'show_utterances': show_utterances,
            'result_type': result_type,
        },
    }
    if use_nostream and language:
        payload['audio']['language'] = language

    packet_size = chunk_size(audio_format, sample_rate, bits, channel)
    chunks = [audio_bytes[i : i + packet_size] for i in range(0, len(audio_bytes), packet_size)] or [b'']

    latest_result: dict[str, Any] | None = None
    responses: list[dict[str, Any]] = []

    async with websockets.connect(api_url, extra_headers=headers, max_size=None) as ws:
        response_headers = _response_headers_map(ws)
        await ws.send(_build_full_client_request(payload))
        first_response = _parse_server_message(await ws.recv())
        responses.append(first_response)
        if 'data' in first_response:
            latest_result = first_response['data']

        for index, chunk in enumerate(chunks, start=1):
            is_last = index == len(chunks)
            await ws.send(_build_audio_request(chunk, sequence=index, is_last=is_last))
            frame = _parse_server_message(await ws.recv())
            responses.append(frame)
            if 'data' in frame:
                latest_result = frame['data']

    return {
        'connect_id': connect_id,
        'log_id': response_headers.get('x-tt-logid'),
        'resource_id': resource_id,
        'api_url': api_url,
        'response': latest_result or {},
        'frames': responses,
    }
