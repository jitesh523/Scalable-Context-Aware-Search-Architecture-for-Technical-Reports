"""
Tests for Model Router.
"""

import pytest
from unittest.mock import AsyncMock, patch
from src.llm.model_router import ModelRouter, ModelProvider


@pytest.mark.asyncio
class TestModelRouter:
    """Test model routing logic"""
    
    async def test_router_initialization(self):
        """Test router initialization"""
        router = ModelRouter(
            default_provider=ModelProvider.OPENAI,
            privacy_mode=False
        )
        
        assert router.default_provider == ModelProvider.OPENAI
        assert router.privacy_mode is False
    
    def test_select_provider_default(self):
        """Test default provider selection"""
        router = ModelRouter(default_provider=ModelProvider.OPENAI)
        
        provider = router.select_provider("Simple query")
        assert provider == ModelProvider.OPENAI
    
    def test_select_provider_privacy_mode(self):
        """Test provider selection in privacy mode"""
        router = ModelRouter(privacy_mode=True)
        router._provider_health[ModelProvider.OLLAMA] = True
        
        provider = router.select_provider("Test query")
        # Should prefer local provider in privacy mode
        assert provider == ModelProvider.OLLAMA
    
    def test_select_provider_force(self):
        """Test forcing specific provider"""
        router = ModelRouter()
        router._provider_health[ModelProvider.OLLAMA] = True
        
        provider = router.select_provider(
            "Test query",
            force_provider=ModelProvider.OLLAMA
        )
        assert provider == ModelProvider.OLLAMA
    
    def test_complexity_estimation(self):
        """Test query complexity estimation"""
        router = ModelRouter()
        
        # Simple query
        simple_complexity = router._estimate_complexity("What is 2+2?")
        assert simple_complexity < 0.5
        
        # Complex query
        complex_query = """
        Explain the implementation of a distributed machine learning algorithm
        for neural network optimization with performance considerations and
        scalability requirements in a cloud architecture.
        """
        complex_complexity = router._estimate_complexity(complex_query)
        assert complex_complexity > 0.5
    
    @patch('src.llm.model_router.AsyncOpenAI')
    async def test_generate_openai(self, mock_openai):
        """Test generation with OpenAI"""
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock(message=AsyncMock(content="Test response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        router = ModelRouter()
        router.openai_client = mock_client
        
        result = await router.generate(
            "Test prompt",
            provider=ModelProvider.OPENAI
        )
        
        assert result == "Test response"
    
    async def test_fallback_to_openai(self):
        """Test fallback to OpenAI when local provider fails"""
        router = ModelRouter()
        router._provider_health[ModelProvider.OLLAMA] = True
        
        # Mock Ollama to fail
        router.ollama_client.generate = AsyncMock(side_effect=Exception("Connection failed"))
        
        # Mock OpenAI to succeed
        router.openai_client.chat.completions.create = AsyncMock(
            return_value=AsyncMock(
                choices=[AsyncMock(message=AsyncMock(content="Fallback response"))]
            )
        )
        
        result = await router.generate(
            "Test prompt",
            provider=ModelProvider.OLLAMA
        )
        
        assert result == "Fallback response"
