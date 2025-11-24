"""
Pydantic models for voice processing.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum


class VoiceProvider(str, Enum):
    """Voice service providers"""
    OPENAI = "openai"
    ELEVENLABS = "elevenlabs"
    LOCAL_WHISPER = "local_whisper"


class MessageType(str, Enum):
    """WebSocket message types"""
    AUDIO_CHUNK = "audio_chunk"
    TRANSCRIPTION = "transcription"
    SYNTHESIS = "synthesis"
    ERROR = "error"
    STATUS = "status"
    CONFIG = "config"


class VoiceConfig(BaseModel):
    """Voice configuration"""
    stt_provider: VoiceProvider = Field(default=VoiceProvider.OPENAI, description="Speech-to-Text provider")
    tts_provider: VoiceProvider = Field(default=VoiceProvider.OPENAI, description="Text-to-Speech provider")
    language: str = Field(default="en", description="Language code")
    voice_id: Optional[str] = Field(default=None, description="Voice ID for TTS")
    sample_rate: int = Field(default=16000, description="Audio sample rate")
    enable_vad: bool = Field(default=True, description="Enable Voice Activity Detection")


class AudioChunk(BaseModel):
    """Audio chunk data"""
    data: bytes = Field(..., description="Audio data in bytes")
    format: str = Field(default="webm", description="Audio format (webm, wav, mp3)")
    sample_rate: int = Field(default=16000, description="Sample rate in Hz")
    channels: int = Field(default=1, description="Number of audio channels")
    timestamp: float = Field(..., description="Timestamp of the chunk")


class TranscriptionResponse(BaseModel):
    """Speech-to-Text response"""
    text: str = Field(..., description="Transcribed text")
    language: Optional[str] = Field(default=None, description="Detected language")
    confidence: Optional[float] = Field(default=None, description="Confidence score")
    duration: Optional[float] = Field(default=None, description="Audio duration in seconds")
    is_final: bool = Field(default=True, description="Whether this is the final transcription")


class SynthesisRequest(BaseModel):
    """Text-to-Speech request"""
    text: str = Field(..., description="Text to synthesize")
    voice_id: Optional[str] = Field(default=None, description="Voice ID")
    language: Optional[str] = Field(default="en", description="Language code")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed")
    pitch: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech pitch")


class SynthesisResponse(BaseModel):
    """Text-to-Speech response"""
    audio_data: bytes = Field(..., description="Synthesized audio data")
    format: str = Field(default="mp3", description="Audio format")
    duration: Optional[float] = Field(default=None, description="Audio duration in seconds")


class VoiceMessage(BaseModel):
    """WebSocket message wrapper"""
    type: MessageType = Field(..., description="Message type")
    session_id: str = Field(..., description="Session identifier")
    data: dict = Field(default_factory=dict, description="Message payload")
    timestamp: float = Field(..., description="Message timestamp")
    error: Optional[str] = Field(default=None, description="Error message if any")


class VoiceSessionState(BaseModel):
    """Voice session state"""
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    config: VoiceConfig = Field(default_factory=VoiceConfig)
    is_recording: bool = Field(default=False, description="Whether currently recording")
    is_speaking: bool = Field(default=False, description="Whether currently speaking")
    buffer: list[bytes] = Field(default_factory=list, description="Audio buffer")
    created_at: float = Field(..., description="Session creation timestamp")
    last_activity: float = Field(..., description="Last activity timestamp")
