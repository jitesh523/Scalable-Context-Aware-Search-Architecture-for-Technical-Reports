import pytest
from unittest.mock import MagicMock, patch
from src.ingestion.docling_parser import DoclingParser

@pytest.mark.asyncio
async def test_docling_parser_image_extraction():
    """Test that DoclingParser is configured for images."""
    with patch("src.ingestion.docling_parser.DocumentConverter") as mock_converter_cls:
        mock_converter = MagicMock()
        mock_converter_cls.return_value = mock_converter
        
        # Mock document result
        mock_result = MagicMock()
        mock_doc = MagicMock()
        mock_result.document = mock_doc
        mock_converter.convert.return_value = mock_result
        
        # Mock content
        mock_doc.export_to_markdown.return_value = "# Test Document"
        mock_doc.tables = []
        
        # Mock pictures
        mock_pic = MagicMock()
        mock_pic.prov = [MagicMock(page_no=1)]
        mock_pic.caption_text.return_value = "Figure 1"
        mock_doc.pictures = [mock_pic]
        
        mock_doc.page_count = 1
        mock_doc.name = "test.pdf"
        mock_doc.export_to_dict.return_value = {}
        
        parser = DoclingParser()
        
        # Verify pipeline options
        # We can't easily inspect the inner options passed to constructor without more mocking,
        # but we can verify the parse logic.
        
        with patch("pathlib.Path.exists", return_value=True):
            result = parser.parse_pdf("dummy.pdf")
            
            assert "images" in result
            assert len(result["images"]) == 1
            assert result["images"][0]["caption"] == "Figure 1"
            assert result["images"][0]["page_no"] == 1
