"""
Docling-based PDF parser service.
Handles high-fidelity extraction of tables, equations, and hierarchical structure.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import json

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions

from config.settings import settings

logger = logging.getLogger(__name__)

class DoclingParser:
    """
    Advanced PDF parser using Docling.
    Preserves document structure, tables, and equations.
    """
    
    def __init__(self):
        """Initialize the Docling converter with custom pipeline options."""
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options = TableStructureOptions(
            do_cell_matching=True
        )
        
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        
    def parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a PDF file and return structured content.
        
        Args:
            file_path: Absolute path to the PDF file
            
        Returns:
            Dictionary containing:
            - markdown: Full markdown representation
            - tables: List of extracted tables
            - metadata: Document metadata
            - structure: Hierarchical document structure
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        logger.info(f"Parsing PDF: {file_path}")
        
        try:
            # Convert the document
            result = self.converter.convert(path)
            doc = result.document
            
            # Serialize to Markdown
            markdown_content = doc.export_to_markdown()
            
            # Extract tables
            tables = []
            for table in doc.tables:
                tables.append({
                    "data": table.export_to_dataframe().to_dict(orient="records"),
                    "caption": table.caption_text(doc) if hasattr(table, "caption_text") else None,
                    "page_no": table.prov[0].page_no if table.prov else None
                })
                
            # Extract metadata
            metadata = {
                "filename": path.name,
                "page_count": doc.page_count if hasattr(doc, "page_count") else None,
                "title": doc.name,
                "source_path": str(path)
            }
            
            return {
                "markdown": markdown_content,
                "tables": tables,
                "metadata": metadata,
                "json_structure": doc.export_to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {str(e)}")
            raise

    def batch_process(self, directory_path: str) -> List[Dict[str, Any]]:
        """
        Process all PDFs in a directory.
        """
        path = Path(directory_path)
        results = []
        
        for file_path in path.glob("*.pdf"):
            try:
                result = self.parse_pdf(str(file_path))
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                continue
                
        return results
