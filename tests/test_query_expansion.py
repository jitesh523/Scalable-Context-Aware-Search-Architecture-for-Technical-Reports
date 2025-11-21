import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.search.query_expansion import QueryExpander
from config.settings import settings

@pytest.mark.asyncio
async def test_query_expander_enabled():
    """Test query expansion when enabled."""
    settings.features.enable_query_expansion = True
    
    with patch("src.search.query_expansion.ChatOpenAI") as mock_llm_cls:
        mock_chain = AsyncMock()
        # Mock the chain execution
        mock_chain.ainvoke.return_value = ["term1", "term2", "term3"]
        
        expander = QueryExpander()
        expander.chain = mock_chain
        
        results = await expander.expand_query("original")
        
        assert "original" in results
        assert "term1" in results
        assert len(results) == 4
        mock_chain.ainvoke.assert_called_once_with({"query": "original"})

@pytest.mark.asyncio
async def test_query_expander_disabled():
    """Test query expansion when disabled."""
    settings.features.enable_query_expansion = False
    
    expander = QueryExpander()
    results = await expander.expand_query("original")
    
    assert results == ["original"]

@pytest.mark.asyncio
async def test_query_expander_error_handling():
    """Test graceful failure on LLM error."""
    settings.features.enable_query_expansion = True
    
    with patch("src.search.query_expansion.ChatOpenAI") as mock_llm_cls:
        mock_chain = AsyncMock()
        mock_chain.ainvoke.side_effect = Exception("LLM Error")
        
        expander = QueryExpander()
        expander.chain = mock_chain
        
        results = await expander.expand_query("original")
        
        # Should return original query on failure
        assert results == ["original"]
