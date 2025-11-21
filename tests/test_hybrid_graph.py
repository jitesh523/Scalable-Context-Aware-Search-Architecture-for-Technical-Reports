import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.search.hybrid_search import HybridSearchEngine
from config.settings import settings

@pytest.mark.asyncio
async def test_hybrid_search_with_graph():
    """Test hybrid search integration with graph retrieval."""
    settings.features.mock_mode = True
    
    with patch("src.search.hybrid_search.MilvusClient") as mock_milvus_cls, \
         patch("src.search.hybrid_search.ElasticsearchClient") as mock_es_cls, \
         patch("src.search.hybrid_search.OpenAIEmbeddings") as mock_embed_cls, \
         patch("src.search.hybrid_search.GraphRetriever") as mock_graph_cls:
             
        # Setup mocks
        mock_milvus = mock_milvus_cls.return_value
        mock_milvus.search.return_value = [{"id": "1", "content": "Dense result", "score": 0.9}]
        
        mock_es = mock_es_cls.return_value
        mock_es.search = AsyncMock(return_value=[{"id": "2", "content": "Lexical result", "score": 0.8}])
        
        mock_embed = mock_embed_cls.return_value
        mock_embed.aembed_query = AsyncMock(return_value=[0.1] * 1536)
        
        mock_graph = mock_graph_cls.return_value
        mock_graph.retrieve = AsyncMock(return_value=["Entity A is RELATED_TO Entity B"])
        
        # Initialize engine
        engine = HybridSearchEngine()
        
        # Run search
        results = await engine.search("test query")
        
        # Verify results
        # Should have graph result + fused result
        assert len(results) >= 2
        assert results[0]["content"] == "[GRAPH KNOWLEDGE] Entity A is RELATED_TO Entity B"
        assert results[0]["metadata"]["source"] == "knowledge_graph"
        
        mock_graph.retrieve.assert_called_once()
