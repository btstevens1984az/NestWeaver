"""Voice I/O stubs — wake word / STT / TTS interfaces for local pipelines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class VoiceUtterance:
    text: str
    confidence: float = 1.0
    is_final: bool = True


class SpeechToText(ABC):
    @abstractmethod
    def transcribe(self, pcm16_mono: bytes, sample_rate: int = 16000) -> VoiceUtterance: ...


class TextToSpeech(ABC):
    @abstractmethod
    def synthesize(self, text: str) -> bytes: ...


class EchoSTT(SpeechToText):
    """Dev stub — returns a canned phrase or UTF-8 decode of payload."""

    def __init__(self, canned: str = "bring me a water bottle") -> None:
        self.canned = canned

    def transcribe(self, pcm16_mono: bytes, sample_rate: int = 16000) -> VoiceUtterance:
        _ = sample_rate
        if not pcm16_mono:
            return VoiceUtterance(text=self.canned, confidence=0.5)
        try:
            text = pcm16_mono.decode("utf-8", errors="ignore").strip() or self.canned
        except Exception:
            text = self.canned
        return VoiceUtterance(text=text, confidence=0.8)


class EchoTTS(TextToSpeech):
    def synthesize(self, text: str) -> bytes:
        return text.encode("utf-8")


class VoiceSession:
    """Glue: mic buffer → STT → LLM → TTS. Runs fully local when backends do."""

    def __init__(self, stt: SpeechToText | None = None, tts: TextToSpeech | None = None, llm=None):
        self.stt = stt or EchoSTT()
        self.tts = tts or EchoTTS()
        self.llm = llm

    def handle_audio(self, pcm16_mono: bytes, context: dict | None = None) -> tuple[str, bytes]:
        utterance = self.stt.transcribe(pcm16_mono)
        if self.llm is None:
            reply = f"I understood: {utterance.text}"
        else:
            reply = self.llm.chat(utterance.text, context=context)
        audio = self.tts.synthesize(reply)
        return reply, audio
