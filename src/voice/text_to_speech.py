"""
Text-to-Speech service with support for ElevenLabs and OpenAI TTS.
"""

import logging
import hashlib
from typing import Optional
from pathlib import Path

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from .voice_models import SynthesisRequest, SynthesisResponse, VoiceProvider
from config.settings import settings

logger = logging.getLogger(__name__)


class TextToSpeechService:
    """
    Text-to-Speech service supporting multiple providers.
    """
    
    def __init__(
        self,
        provider: VoiceProvider = VoiceProvider.OPENAI,
        api_key: Optional[str] = None,
        elevenlabs_api_key: Optional[str] = None
    ):
        self.provider = provider
        self.api_key = api_key or settings.llm.openai_api_key
        self.elevenlabs_api_key = elevenlabs_api_key
        self.cache_dir = Path("/tmp/tts_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        if self.provider == VoiceProvider.OPENAI:
            self.client = AsyncOpenAI(api_key=self.api_key)
        elif self.provider == VoiceProvider.ELEVENLABS:
            self._init_elevenlabs()
        
        logger.info(f"Initialized TTS service with provider: {self.provider}")
    
    def _init_elevenlabs(self):
        """Initialize ElevenLabs client"""
        try:
            from elevenlabs import AsyncElevenLabs
            if not self.elevenlabs_api_key:
                raise ValueError("ElevenLabs API key not provided")
            self.elevenlabs_client = AsyncElevenLabs(api_key=self.elevenlabs_api_key)
            logger.info("Initialized ElevenLabs client")
        except ImportError:
            logger.warning("elevenlabs package not installed. Install with: pip install elevenlabs")
            self.elevenlabs_client = None
    
    def _get_cache_key(self, text: str, voice_id: Optional[str]) -> str:
        """Generate cache key for text and voice"""
        cache_string = f"{text}_{voice_id}_{self.provider}"
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _get_cached_audio(self, cache_key: str) -> Optional[bytes]:
        """Retrieve cached audio if available"""
        cache_file = self.cache_dir / f"{cache_key}.mp3"
        if cache_file.exists():
            logger.info(f"Cache hit for key: {cache_key}")
            return cache_file.read_bytes()
        return None
    
    def _cache_audio(self, cache_key: str, audio_data: bytes):
        """Cache audio data"""
        cache_file = self.cache_dir / f"{cache_key}.mp3"
        cache_file.write_bytes(audio_data)
        logger.info(f"Cached audio for key: {cache_key}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def synthesize(
        self,
        request: SynthesisRequest
    ) -> SynthesisResponse:
        """
        Synthesize speech from text.
        
        Args:
            request: SynthesisRequest with text and options
        
        Returns:
            SynthesisResponse with audio data
        """
        # Check cache first
        cache_key = self._get_cache_key(request.text, request.voice_id)
        cached_audio = self._get_cached_audio(cache_key)
        
        if cached_audio:
            return SynthesisResponse(
                audio_data=cached_audio,
                format="mp3"
            )
        
        # Generate new audio
        if self.provider == VoiceProvider.OPENAI:
            response = await self._synthesize_openai(request)
        elif self.provider == VoiceProvider.ELEVENLABS:
            response = await self._synthesize_elevenlabs(request)
        else:
            raise ValueError(f"Unsupported TTS provider: {self.provider}")
        
        # Cache the result
        self._cache_audio(cache_key, response.audio_data)
        
        return response
    
    async def _synthesize_openai(
        self,
        request: SynthesisRequest
    ) -> SynthesisResponse:
        """Synthesize using OpenAI TTS API"""
        try:
            # Map voice_id to OpenAI voices
            voice_map = {
                "alloy": "alloy",
                "echo": "echo",
                "fable": "fable",
                "onyx": "onyx",
                "nova": "nova",
                "shimmer": "shimmer"
            }
            
            voice = voice_map.get(request.voice_id, "alloy")
            
            response = await self.client.audio.speech.create(
                model="tts-1",  # or "tts-1-hd" for higher quality
                voice=voice,
                input=request.text,
                speed=request.speed
            )
            
            # Read audio data
            audio_data = b""
            async for chunk in response.iter_bytes():
                audio_data += chunk
            
            return SynthesisResponse(
                audio_data=audio_data,
                format="mp3"
            )
            
        except Exception as e:
            logger.error(f"OpenAI TTS failed: {e}")
            raise
    
    async def _synthesize_elevenlabs(
        self,
        request: SynthesisRequest
    ) -> SynthesisResponse:
        """Synthesize using ElevenLabs API"""
        if self.elevenlabs_client is None:
            raise RuntimeError("ElevenLabs client not initialized")
        
        try:
            # Use default voice if not specified
            voice_id = request.voice_id or "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
            
            # Generate audio
            audio_generator = await self.elevenlabs_client.generate(
                text=request.text,
                voice=voice_id,
                model="eleven_monolingual_v1"
            )
            
            # Collect audio chunks
            audio_data = b""
            async for chunk in audio_generator:
                audio_data += chunk
            
            return SynthesisResponse(
                audio_data=audio_data,
                format="mp3"
            )
            
        except Exception as e:
            logger.error(f"ElevenLabs TTS failed: {e}")
            raise
    
    async def synthesize_stream(
        self,
        text: str,
        voice_id: Optional[str] = None
    ):
        """
        Stream synthesized audio in chunks.
        
        Args:
            text: Text to synthesize
            voice_id: Optional voice identifier
        
        Yields:
            Audio chunks as bytes
        """
        request = SynthesisRequest(text=text, voice_id=voice_id)
        
        if self.provider == VoiceProvider.OPENAI:
            response = await self.client.audio.speech.create(
                model="tts-1",
                voice=voice_id or "alloy",
                input=text
            )
            
            async for chunk in response.iter_bytes():
                yield chunk
        
        elif self.provider == VoiceProvider.ELEVENLABS:
            if self.elevenlabs_client is None:
                raise RuntimeError("ElevenLabs client not initialized")
            
            voice_id = voice_id or "21m00Tcm4TlvDq8ikWAM"
            audio_generator = await self.elevenlabs_client.generate(
                text=text,
                voice=voice_id,
                model="eleven_monolingual_v1",
                stream=True
            )
            
            async for chunk in audio_generator:
                yield chunk
