"""
Speech-to-Text service with support for OpenAI Whisper API and local Whisper.
"""

import logging
import io
import tempfile
from typing import Optional
from pathlib import Path

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from .voice_models import AudioChunk, TranscriptionResponse, VoiceProvider
from config.settings import settings

logger = logging.getLogger(__name__)


class SpeechToTextService:
    """
    Speech-to-Text service supporting multiple providers.
    """
    
    def __init__(
        self,
        provider: VoiceProvider = VoiceProvider.OPENAI,
        api_key: Optional[str] = None
    ):
        self.provider = provider
        self.api_key = api_key or settings.llm.openai_api_key
        
        if self.provider == VoiceProvider.OPENAI:
            self.client = AsyncOpenAI(api_key=self.api_key)
        elif self.provider == VoiceProvider.LOCAL_WHISPER:
            self._init_local_whisper()
        
        logger.info(f"Initialized STT service with provider: {self.provider}")
    
    def _init_local_whisper(self):
        """Initialize local Whisper model (optional)"""
        try:
            import whisper
            self.whisper_model = whisper.load_model("base")
            logger.info("Loaded local Whisper model")
        except ImportError:
            logger.warning("whisper package not installed. Install with: pip install openai-whisper")
            self.whisper_model = None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        format: str = "webm"
    ) -> TranscriptionResponse:
        """
        Transcribe audio to text.
        
        Args:
            audio_data: Audio data in bytes
            language: Optional language code (e.g., 'en', 'es')
            format: Audio format (webm, wav, mp3)
        
        Returns:
            TranscriptionResponse with transcribed text
        """
        if self.provider == VoiceProvider.OPENAI:
            return await self._transcribe_openai(audio_data, language, format)
        elif self.provider == VoiceProvider.LOCAL_WHISPER:
            return await self._transcribe_local(audio_data, language)
        else:
            raise ValueError(f"Unsupported STT provider: {self.provider}")
    
    async def _transcribe_openai(
        self,
        audio_data: bytes,
        language: Optional[str],
        format: str
    ) -> TranscriptionResponse:
        """Transcribe using OpenAI Whisper API"""
        try:
            # Create a temporary file-like object
            audio_file = io.BytesIO(audio_data)
            audio_file.name = f"audio.{format}"
            
            # Call OpenAI Whisper API
            response = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format="verbose_json"
            )
            
            return TranscriptionResponse(
                text=response.text,
                language=response.language if hasattr(response, 'language') else language,
                duration=response.duration if hasattr(response, 'duration') else None,
                is_final=True
            )
            
        except Exception as e:
            logger.error(f"OpenAI transcription failed: {e}")
            raise
    
    async def _transcribe_local(
        self,
        audio_data: bytes,
        language: Optional[str]
    ) -> TranscriptionResponse:
        """Transcribe using local Whisper model"""
        if self.whisper_model is None:
            raise RuntimeError("Local Whisper model not initialized")
        
        try:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            # Transcribe
            result = self.whisper_model.transcribe(
                temp_path,
                language=language,
                fp16=False
            )
            
            # Clean up
            Path(temp_path).unlink()
            
            return TranscriptionResponse(
                text=result["text"],
                language=result.get("language"),
                is_final=True
            )
            
        except Exception as e:
            logger.error(f"Local Whisper transcription failed: {e}")
            raise
    
    async def transcribe_stream(
        self,
        audio_chunks: list[AudioChunk],
        language: Optional[str] = None
    ) -> TranscriptionResponse:
        """
        Transcribe a stream of audio chunks.
        
        Args:
            audio_chunks: List of audio chunks
            language: Optional language code
        
        Returns:
            TranscriptionResponse with transcribed text
        """
        # Concatenate all audio chunks
        combined_audio = b"".join([chunk.data for chunk in audio_chunks])
        
        # Use the format from the first chunk
        format = audio_chunks[0].format if audio_chunks else "webm"
        
        return await self.transcribe(combined_audio, language, format)
