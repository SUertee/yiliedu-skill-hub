from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from .audio import guess_format, normalize_audio_for_flash
from .flash_client import recognize_via_flash, transcript_from_result
from .websocket_client import recognize_via_websocket


router = APIRouter(prefix='/api/stt_volc', tags=['stt_volc'])


@router.post('/audio/transcriptions')
async def openai_compatible_transcribe(
    file: UploadFile = File(...),
    language: str | None = Form(None),
    model: str = Form('bigmodel'),
):
    """
    OpenAI-compatible STT endpoint for Open WebUI.

    Configure Open WebUI STT engine as "OpenAI" and set API Base URL to:
    http://<skill-hub-host>:<port>/api/stt_volc
    """
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail='empty audio file')

    source_format = guess_format(file)

    try:
        normalized_audio, normalized_format = normalize_audio_for_flash(audio_bytes, source_format)
        result = recognize_via_flash(
            normalized_audio,
            audio_format=normalized_format,
            language=language,
            model_name=model or 'bigmodel',
        )
        text = transcript_from_result(result)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f'volc stt failed: {exc}') from exc

    return {'text': text}


@router.post('/transcribe')
async def transcribe(
    file: UploadFile = File(...),
    language: str | None = Form(None),
    sample_rate: int = Form(16000),
    bits: int = Form(16),
    channel: int = Form(1),
    model_name: str = Form('bigmodel'),
    show_utterances: bool = Form(True),
    enable_itn: bool = Form(True),
    enable_punc: bool = Form(True),
    enable_ddc: bool = Form(False),
    result_type: str = Form('full'),
    use_nostream: bool = Form(True),
):
    """
    Debug endpoint for direct Volcengine STT access.

    Default mode uses the existing SAUC websocket path to return provider-native output.
    """
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail='empty audio file')

    audio_format = guess_format(file)

    try:
        result = await recognize_via_websocket(
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
        raise HTTPException(status_code=502, detail=f'volc stt failed: {exc}') from exc

    return result
