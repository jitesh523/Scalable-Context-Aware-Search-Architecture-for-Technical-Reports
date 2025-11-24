"""
Voice processing module for Speech-to-Text and Text-to-Speech.
"""

from .speech_to_text import SpeechToTextService
from .text_to_speech import TextToSpeechService
from .voice_models import (
    VoiceMessage,
    AudioChunk,
    TranscriptionResponse,
    SynthesisRequest,
    VoiceConfig
)

__all__ = [
    "SpeechToTextService",
    "TextToSpeechService",
    "VoiceMessage",
    "AudioChunk",
    "TranscriptionResponse",
    "SynthesisRequest",
    "VoiceConfig"
]
