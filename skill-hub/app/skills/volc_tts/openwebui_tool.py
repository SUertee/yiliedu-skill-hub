import base64
import json

import requests

BASE_URL = "http://skill-hub:8000/api"
API_KEY = "super-secret-key-2026"


class Tools:
    def _headers(self):
        return {"x-api-key": API_KEY}

    def _post(self, path: str, payload: dict) -> dict:
        response = requests.post(
            f"{BASE_URL}{path}",
            headers=self._headers(),
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        if "application/json" in response.headers.get("content-type", ""):
            return response.json()
        return {"raw": response.content}

    def tts_synthesize(
        self,
        text: str,
        voice_type: str = "zh_female_meilinvyou_moon_bigtts",
        encoding: str = "mp3",
        speed_ratio: float = 1.0,
    ) -> str:
        """Volc TTS: 将文本转语音（返回音频base64，便于调试）。"""
        try:
            result = self._post(
                "/volc_tts/synthesize",
                {
                    "text": text,
                    "voice_type": voice_type,
                    "encoding": encoding,
                    "speed_ratio": speed_ratio,
                    "return_base64": True,
                },
            )
            audio_b64 = result.get("audio_base64", "")
            result["audio_base64_preview"] = audio_b64[:80] + "..." if audio_b64 else ""
            result.pop("audio_base64", None)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"调用失败: {e}"

    def tts_audio_speech(
        self,
        text: str,
        voice: str = "BV001_streaming",
        response_format: str = "mp3",
        speed: float = 1.0,
    ) -> str:
        """OpenAI兼容接口 /audio/speech（返回音频长度和base64预览）。"""
        try:
            response = requests.post(
                f"{BASE_URL}/volc_tts/audio/speech",
                headers=self._headers(),
                json={
                    "model": "volc_tts",
                    "input": text,
                    "voice": voice,
                    "response_format": response_format,
                    "speed": speed,
                },
                timeout=60,
            )
            response.raise_for_status()
            b64 = base64.b64encode(response.content).decode("utf-8")
            return json.dumps(
                {
                    "ok": True,
                    "content_type": response.headers.get("content-type"),
                    "audio_size": len(response.content),
                    "audio_base64_preview": b64[:80] + "..." if b64 else "",
                },
                ensure_ascii=False,
                indent=2,
            )
        except Exception as e:
            return f"调用失败: {e}"
