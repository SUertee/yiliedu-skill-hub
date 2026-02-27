from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import UploadFile


def guess_format(upload: UploadFile) -> str:
    filename = (upload.filename or '').lower()
    content_type = (upload.content_type or '').lower()

    if filename.endswith('.wav') or 'wav' in content_type:
        return 'wav'
    if filename.endswith('.ogg') or 'ogg' in content_type:
        return 'ogg'
    if filename.endswith('.mp3') or 'mpeg' in content_type or 'mp3' in content_type:
        return 'mp3'
    if filename.endswith('.m4a') or 'mp4' in content_type or filename.endswith('.mp4'):
        return 'mp4'
    if filename.endswith('.webm') or 'webm' in content_type:
        return 'webm'
    return 'pcm'


def chunk_size(fmt: str, rate: int, bits: int, channel: int) -> int:
    if fmt in {'pcm', 'wav'}:
        bytes_per_second = rate * max(bits // 8, 1) * channel
        return max(bytes_per_second // 5, 1)
    return 8192


def normalize_audio_for_flash(audio_bytes: bytes, source_format: str) -> tuple[bytes, str]:
    """
    Volcengine flash accepts WAV / MP3 / OGG(OPUS).
    Open WebUI typically uploads WEBM/MP4 from MediaRecorder, so convert them to WAV.
    """
    if source_format in {'wav', 'mp3', 'ogg'}:
        return audio_bytes, source_format

    if source_format not in {'webm', 'mp4', 'm4a', 'pcm'}:
        return audio_bytes, source_format

    ffmpeg_path = shutil.which('ffmpeg')
    if not ffmpeg_path:
        raise RuntimeError('ffmpeg is required to convert uploaded audio to wav')

    suffix = '.bin' if source_format == 'pcm' else f'.{source_format}'

    with TemporaryDirectory(prefix='stt-volc-') as tmpdir:
        src = Path(tmpdir) / f'input{suffix}'
        dst = Path(tmpdir) / 'output.wav'
        src.write_bytes(audio_bytes)

        cmd = [
            ffmpeg_path,
            '-y',
            '-i',
            str(src),
            '-ac',
            '1',
            '-ar',
            '16000',
            '-f',
            'wav',
            str(dst),
        ]
        completed = subprocess.run(cmd, capture_output=True, text=True)
        if completed.returncode != 0 or not dst.exists():
            stderr = completed.stderr.strip() or 'unknown ffmpeg error'
            raise RuntimeError(f'ffmpeg conversion failed: {stderr}')

        return dst.read_bytes(), 'wav'
