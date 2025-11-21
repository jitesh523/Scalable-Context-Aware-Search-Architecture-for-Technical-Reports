import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.graph.extractor import GraphExtractor
from src.graph.neo4j_client import Neo4jClient
from config.settings import settings

@pytest.mark.asyncio
async def test_graph_extractor_mock_mode():
    """Test graph extractor in mock mode."""
    settings.features.mock_mode = True
    extractor = GraphExtractor()
    
    result = await extractor.extract("Some text about Python and Neo4j.")
    assert "entities" in result
    assert result["entities"][0]["name"] == "MockEntity"

@pytest.mark.asyncio
async def test_neo4j_client_mock_mode():
    """Test Neo4j client in mock mode."""
    settings.features.mock_mode = True
    client = Neo4jClient()
    
    # Should not raise exceptions
    await client.add_entity("CONCEPT", "Test")
    await client.add_relationship("Test", "Other", "RELATED_TO")
    
    results = await client.query_subgraph("Test")
    assert len(results) > 0
    assert results[0]["source"] == "Test"

@pytest.mark.asyncio
async def test_ingestion_pipeline_graph_integration():
    """Test that pipeline calls graph extractor and neo4j."""
    settings.features.mock_mode = True
    
    with patch("src.ingestion.pipeline.DoclingParser") as mock_parser_cls, \
         patch("src.ingestion.pipeline.ChunkingStrategy") as mock_chunker_cls, \
         patch("src.ingestion.pipeline.GraphExtractor") as mock_extractor_cls, \
         patch("src.ingestion.pipeline.Neo4jClient") as mock_neo4j_cls:
             
        # Setup mocks
        mock_parser = mock_parser_cls.return_value
        mock_parser.parse_pdf.return_value = {
            "markdown": "Text", "metadata": {"filename": "test.pdf"}, "images": []
        }
        
        mock_chunker = mock_chunker_cls.return_value
        mock_chunk = MagicMock()
        mock_chunk.content = "Chunk content"
        mock_chunk.metadata = {"level": "parent"}
        mock_chunker.hierarchical_chunking.return_value = [mock_chunk]
        
        mock_extractor = mock_extractor_cls.return_value
        mock_extractor.extract = AsyncMock(return_value={
            "entities": [{"name": "E1", "type": "T1"}],
            "relationships": [{"source": "E1", "target": "E2", "type": "R1"}]
        })
        
        mock_neo4j = mock_neo4j_cls.return_value
        mock_neo4j.add_entity = AsyncMock()
        mock_neo4j.add_relationship = AsyncMock()
        
        # Run pipeline
        from src.ingestion.pipeline import IngestionPipeline
        pipeline = IngestionPipeline()
        result = await pipeline.process_document("dummy.pdf")
        
        # Verify interactions
        assert result["graph_stats"]["nodes"] == 1
        assert result["graph_stats"]["edges"] == 1
        mock_extractor.extract.assert_called()
        mock_neo4j.add_entity.assert_called()
        mock_neo4j.add_relationship.assert_called()
