"""
Unit tests for hybrid search components.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.search.rrf_fusion import RRFFusion
from src.search.hybrid_search import HybridSearchEngine

def test_rrf_fusion():
    rrf = RRFFusion()
    
    # Mock results
    semantic = [
        {"id": "1", "score": 0.9},
        {"id": "2", "score": 0.8}
    ]
    lexical = [
        {"id": "2", "score": 10.0},
        {"id": "3", "score": 5.0}
    ]
    
    fused = rrf.fuse(semantic, lexical, limit=3)
    
    # Doc 2 should be first (present in both)
    assert fused[0]["id"] == "2"
    assert len(fused) == 3

@pytest.mark.asyncio
async def test_hybrid_search_engine():
    with patch("src.search.hybrid_search.MilvusClient") as mock_milvus, \
         patch("src.search.hybrid_search.ElasticsearchClient") as mock_es, \
         patch("src.search.hybrid_search.OpenAIEmbeddings") as mock_embed:
             
        # Setup mocks
        engine = HybridSearchEngine()
        
        # Mock embedding - return awaitable
        async def mock_aembed_query(text):
            return [0.1] * 768
        engine.embeddings.aembed_query = mock_aembed_query
        
        # Mock search results
        mock_milvus.return_value.search.return_value = [{"id": "1", "score": 0.9}]
        mock_es.return_value.search = AsyncMock(return_value=[{"id": "1", "score": 10.0}])
        
        results = await engine.search("test query")
        
        assert len(results) > 0
        assert results[0]["id"] == "1"
