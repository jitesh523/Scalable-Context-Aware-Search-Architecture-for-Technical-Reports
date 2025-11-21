import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.ingestion.vlm_client import VLMClient
from config.settings import settings

@pytest.mark.asyncio
async def test_vlm_client_mock_mode():
    """Test VLM client in mock mode."""
    settings.features.mock_mode = True
    client = VLMClient()
    
    caption = await client.generate_caption("dummy_base64")
    assert caption == "A mock description of the image containing charts and data."

@pytest.mark.asyncio
async def test_vlm_client_real_call():
    """Test VLM client with mocked OpenAI call."""
    settings.features.mock_mode = False
    
    with patch("src.ingestion.vlm_client.ChatOpenAI") as mock_llm_cls:
        mock_llm = AsyncMock()
        mock_llm_cls.return_value = mock_llm
        
        # Mock response
        mock_response = MagicMock()
        mock_response.content = "A detailed description of the chart."
        mock_llm.ainvoke.return_value = mock_response
        
        client = VLMClient()
        caption = await client.generate_caption("dummy_base64")
        
        assert caption == "A detailed description of the chart."
        mock_llm.ainvoke.assert_called_once()
