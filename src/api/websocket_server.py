"""
WebSocket server for real-time voice communication.
Handles bidirectional streaming of audio data and transcriptions.
"""

import logging
import time
import uuid
import json
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect, Depends
from fastapi.routing import APIRouter

from src.voice.speech_to_text import SpeechToTextService
from src.voice.text_to_speech import TextToSpeechService
from src.voice.voice_models import (
    VoiceMessage,
    MessageType,
    AudioChunk,
    VoiceSessionState,
    VoiceConfig,
    VoiceProvider,
    SynthesisRequest
)
from src.api.auth import AuthHandler
from src.agents.langgraph_workflow import RAGWorkflow
from config.settings import settings

logger = logging.getLogger(__name__)

# Router for WebSocket endpoints
router = APIRouter()

# Active sessions
active_sessions: Dict[str, VoiceSessionState] = {}


class VoiceWebSocketManager:
    """
    Manages WebSocket connections for voice communication.
    """
    
    def __init__(self):
        self.stt_service: Optional[SpeechToTextService] = None
        self.tts_service: Optional[TextToSpeechService] = None
        self.rag_workflow: Optional[RAGWorkflow] = None
        self.auth_handler = AuthHandler()
    
    def initialize(
        self,
        stt_provider: VoiceProvider = VoiceProvider.OPENAI,
        tts_provider: VoiceProvider = VoiceProvider.OPENAI,
        elevenlabs_api_key: Optional[str] = None
    ):
        """Initialize voice services"""
        self.stt_service = SpeechToTextService(provider=stt_provider)
        self.tts_service = TextToSpeechService(
            provider=tts_provider,
            elevenlabs_api_key=elevenlabs_api_key
        )
        self.rag_workflow = RAGWorkflow()
        logger.info("Voice WebSocket manager initialized")
    
    async def handle_connection(
        self,
        websocket: WebSocket,
        session_id: str,
        user_id: str
    ):
        """
        Handle WebSocket connection lifecycle.
        
        Args:
            websocket: WebSocket connection
            session_id: Session identifier
            user_id: User identifier
        """
        await websocket.accept()
        
        # Create session state
        session_state = VoiceSessionState(
            session_id=session_id,
            user_id=user_id,
            created_at=time.time(),
            last_activity=time.time()
        )
        active_sessions[session_id] = session_state
        
        logger.info(f"WebSocket connection established: session={session_id}, user={user_id}")
        
        # Send welcome message
        await self._send_message(
            websocket,
            MessageType.STATUS,
            session_id,
            {"status": "connected", "message": "Voice session started"}
        )
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Update last activity
                session_state.last_activity = time.time()
                
                # Handle message based on type
                await self._handle_message(websocket, session_state, message)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: session={session_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await self._send_error(websocket, session_id, str(e))
        finally:
            # Clean up session
            if session_id in active_sessions:
                del active_sessions[session_id]
            logger.info(f"Session cleaned up: {session_id}")
    
    async def _handle_message(
        self,
        websocket: WebSocket,
        session_state: VoiceSessionState,
        message: dict
    ):
        """Handle incoming WebSocket message"""
        msg_type = message.get("type")
        
        if msg_type == MessageType.AUDIO_CHUNK:
            await self._handle_audio_chunk(websocket, session_state, message)
        
        elif msg_type == MessageType.CONFIG:
            await self._handle_config_update(websocket, session_state, message)
        
        elif msg_type == "transcribe":
            await self._handle_transcribe_request(websocket, session_state)
        
        elif msg_type == "query":
            await self._handle_query(websocket, session_state, message)
        
        else:
            logger.warning(f"Unknown message type: {msg_type}")
    
    async def _handle_audio_chunk(
        self,
        websocket: WebSocket,
        session_state: VoiceSessionState,
        message: dict
    ):
        """Handle incoming audio chunk"""
        try:
            # Extract audio data (base64 encoded)
            import base64
            audio_data = base64.b64decode(message["data"])
            
            # Add to buffer
            session_state.buffer.append(audio_data)
            session_state.is_recording = True
            
            # Send acknowledgment
            await self._send_message(
                websocket,
                MessageType.STATUS,
                session_state.session_id,
                {"status": "recording", "buffer_size": len(session_state.buffer)}
            )
            
        except Exception as e:
            logger.error(f"Error handling audio chunk: {e}")
            await self._send_error(websocket, session_state.session_id, str(e))
    
    async def _handle_transcribe_request(
        self,
        websocket: WebSocket,
        session_state: VoiceSessionState
    ):
        """Transcribe buffered audio"""
        if not session_state.buffer:
            await self._send_error(websocket, session_state.session_id, "No audio to transcribe")
            return
        
        try:
            # Combine audio chunks
            combined_audio = b"".join(session_state.buffer)
            
            # Transcribe
            transcription = await self.stt_service.transcribe(
                audio_data=combined_audio,
                language=session_state.config.language,
                format="webm"
            )
            
            # Send transcription
            await self._send_message(
                websocket,
                MessageType.TRANSCRIPTION,
                session_state.session_id,
                {
                    "text": transcription.text,
                    "language": transcription.language,
                    "confidence": transcription.confidence
                }
            )
            
            # Clear buffer
            session_state.buffer.clear()
            session_state.is_recording = False
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            await self._send_error(websocket, session_state.session_id, str(e))
    
    async def _handle_query(
        self,
        websocket: WebSocket,
        session_state: VoiceSessionState,
        message: dict
    ):
        """Handle RAG query with voice response"""
        try:
            query_text = message.get("query")
            if not query_text:
                await self._send_error(websocket, session_state.session_id, "No query provided")
                return
            
            # Send processing status
            await self._send_message(
                websocket,
                MessageType.STATUS,
                session_state.session_id,
                {"status": "processing", "message": "Searching knowledge base..."}
            )
            
            # Execute RAG workflow
            result = await self.rag_workflow.app.ainvoke({
                "question": query_text,
                "iterations": 0
            })
            
            answer = result.get("generation", "No answer generated.")
            
            # Send text response
            await self._send_message(
                websocket,
                MessageType.STATUS,
                session_state.session_id,
                {"status": "generating_speech", "answer": answer}
            )
            
            # Generate speech
            synthesis_request = SynthesisRequest(
                text=answer,
                voice_id=session_state.config.voice_id
            )
            
            # Stream audio response
            async for audio_chunk in self.tts_service.synthesize_stream(
                text=answer,
                voice_id=session_state.config.voice_id
            ):
                import base64
                audio_b64 = base64.b64encode(audio_chunk).decode('utf-8')
                
                await self._send_message(
                    websocket,
                    MessageType.SYNTHESIS,
                    session_state.session_id,
                    {"audio_chunk": audio_b64, "format": "mp3"}
                )
            
            # Send completion status
            await self._send_message(
                websocket,
                MessageType.STATUS,
                session_state.session_id,
                {"status": "complete", "message": "Response generated"}
            )
            
        except Exception as e:
            logger.error(f"Query error: {e}")
            await self._send_error(websocket, session_state.session_id, str(e))
    
    async def _handle_config_update(
        self,
        websocket: WebSocket,
        session_state: VoiceSessionState,
        message: dict
    ):
        """Update session configuration"""
        try:
            config_data = message.get("config", {})
            session_state.config = VoiceConfig(**config_data)
            
            await self._send_message(
                websocket,
                MessageType.STATUS,
                session_state.session_id,
                {"status": "config_updated", "config": session_state.config.dict()}
            )
            
        except Exception as e:
            logger.error(f"Config update error: {e}")
            await self._send_error(websocket, session_state.session_id, str(e))
    
    async def _send_message(
        self,
        websocket: WebSocket,
        msg_type: MessageType,
        session_id: str,
        data: dict
    ):
        """Send message to client"""
        message = VoiceMessage(
            type=msg_type,
            session_id=session_id,
            data=data,
            timestamp=time.time()
        )
        await websocket.send_text(message.json())
    
    async def _send_error(
        self,
        websocket: WebSocket,
        session_id: str,
        error: str
    ):
        """Send error message to client"""
        message = VoiceMessage(
            type=MessageType.ERROR,
            session_id=session_id,
            data={},
            timestamp=time.time(),
            error=error
        )
        await websocket.send_text(message.json())


# Global manager instance
ws_manager = VoiceWebSocketManager()


@router.websocket("/ws/voice")
async def voice_websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None
):
    """
    WebSocket endpoint for voice communication.
    
    Query params:
        token: JWT authentication token
    """
    # Authenticate user
    try:
        auth_handler = AuthHandler()
        if token:
            user_id = auth_handler.get_current_user(token)
        else:
            # For development, use anonymous user
            user_id = "anonymous"
    except Exception as e:
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Handle connection
    await ws_manager.handle_connection(websocket, session_id, user_id)
