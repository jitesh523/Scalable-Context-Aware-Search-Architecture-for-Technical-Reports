"""
Tests for Ollama client.
"""

import pytest
from unittest.mock import AsyncMock, patch
from src.llm.ollama_client import OllamaClient


@pytest.mark.asyncio
class TestOllamaClient:
    """Test Ollama client functionality"""
    
    async def test_client_initialization(self):
        """Test client initialization"""
        client = OllamaClient(
            base_url="http://localhost:11434",
            model="llama3"
        )
        
        assert client.base_url == "http://localhost:11434"
        assert client.model == "llama3"
    
    @patch('httpx.AsyncClient.post')
    async def test_generate(self, mock_post):
        """Test text generation"""
        # Mock response
        mock_response = AsyncMock()
        mock_response.json.return_value = {"response": "This is a test response"}
        mock_response.raise_for_status = AsyncMock()
        mock_post.return_value = mock_response
        
        client = OllamaClient()
        result = await client.generate("Test prompt")
        
        assert result == "This is a test response"
        mock_post.assert_called_once()
    
    @patch('httpx.AsyncClient.post')
    async def test_chat(self, mock_post):
        """Test chat completion"""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "message": {"content": "Chat response"}
        }
        mock_response.raise_for_status = AsyncMock()
        mock_post.return_value = mock_response
        
        client = OllamaClient()
        messages = [
            {"role": "user", "content": "Hello"}
        ]
        result = await client.chat(messages)
        
        assert result == "Chat response"
    
    @patch('httpx.AsyncClient.get')
    async def test_list_models(self, mock_get):
        """Test listing available models"""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3"},
                {"name": "phi3"},
                {"name": "mistral"}
            ]
        }
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response
        
        client = OllamaClient()
        models = await client.list_models()
        
        assert "llama3" in models
        assert "phi3" in models
        assert "mistral" in models
    
    @patch('httpx.AsyncClient.get')
    async def test_health_check(self, mock_get):
        """Test health check"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        client = OllamaClient()
        is_healthy = await client.health_check()
        
        assert is_healthy is True
