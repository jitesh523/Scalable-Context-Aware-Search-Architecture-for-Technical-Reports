"""
Unit tests for data ingestion components.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.ingestion.docling_parser import DoclingParser
from src.ingestion.chunking_strategy import ChunkingStrategy, Chunk
from src.ingestion.pipeline import IngestionPipeline

# Mock data
SAMPLE_MARKDOWN = """
# Title
Introduction text.

## Section 1
Section 1 text.

### Subsection 1.1
Subsection text.
"""

@pytest.fixture
def mock_docling():
    with patch("src.ingestion.docling_parser.DocumentConverter") as mock:
        yield mock

@pytest.fixture
def mock_embeddings():
    with patch("src.ingestion.chunking_strategy.OpenAIEmbeddings") as mock:
        yield mock

def test_docling_parser_init(mock_docling):
    parser = DoclingParser()
    assert parser.converter is not None

def test_chunking_strategy_hierarchical(mock_embeddings):
    strategy = ChunkingStrategy()
    chunks = strategy.hierarchical_chunking(SAMPLE_MARKDOWN, {"filename": "test.pdf"})
    
    assert len(chunks) > 0
    
    # Check for parent chunks
    parents = [c for c in chunks if c.metadata["type"] == "parent"]
    assert len(parents) > 0
    
    # Check for child chunks
    children = [c for c in chunks if c.metadata["type"] == "child"]
    assert len(children) > 0
    
    # Check hierarchy linkage
    assert children[0].parent_id is not None

@pytest.mark.asyncio
async def test_ingestion_pipeline(mock_docling, mock_embeddings):
    # Setup mocks
    mock_converter_instance = mock_docling.return_value
    mock_doc = MagicMock()
    mock_doc.export_to_markdown.return_value = SAMPLE_MARKDOWN
    mock_doc.tables = []
    mock_doc.name = "Test Doc"
    mock_converter_instance.convert.return_value.document = mock_doc
    
    pipeline = IngestionPipeline()
    
    # Mock file existence check
    with patch("pathlib.Path.exists", return_value=True):
        result = await pipeline.process_document("/path/to/test.pdf")
        
    assert result["status"] == "success"
    assert result["chunks_count"] > 0
