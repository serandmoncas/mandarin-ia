"""Deterministic audio file keys shared by the build and the TTS step."""
import hashlib

WORD_VOICES = ("zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural", "zh-CN-XiaoyiNeural")
SENTENCE_VOICE = "zh-CN-XiaoxiaoNeural"


def audio_key(text: str, voice: str) -> str:
    digest = hashlib.sha1(f"{voice}|{text}".encode("utf-8")).hexdigest()
    return f"{digest[:16]}.mp3"
