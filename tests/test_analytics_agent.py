import pytest
from unittest.mock import AsyncMock, patch
from src.agents.analytics_agent import AnalyticsAgent
from config.settings import settings

@pytest.mark.asyncio
async def test_analytics_agent_mock_mode():
    """Test analytics agent in mock mode."""
    settings.features.mock_mode = True
    agent = AnalyticsAgent()
    
    result = await agent.analyze("What is the average?")
    assert result["output"] == "Mock analysis result"
    assert result["error"] is None
    assert result["code"] == "print('Mock code')"

