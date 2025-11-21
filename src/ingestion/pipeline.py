"""
Orchestrator for the data ingestion pipeline.
Coordinates parsing, chunking, and indexing.
"""

import logging
import asyncio
from typing import List, Dict, Any
from pathlib import Path

from src.ingestion.docling_parser import DoclingParser
from src.ingestion.chunking_strategy import ChunkingStrategy, Chunk
from src.ingestion.vlm_client import VLMClient
# We will import storage clients later when implemented
# from src.search.hybrid_search import HybridSearchEngine

from config.settings import settings

logger = logging.getLogger(__name__)

class IngestionPipeline:
    """
    End-to-end ingestion pipeline.
    """
    
    def __init__(self):
        self.parser = DoclingParser()
        self.chunker = ChunkingStrategy()
        self.vlm = VLMClient()
        # self.search_engine = HybridSearchEngine() # To be injected
        
    async def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process a single document from PDF to indexed chunks.
        """
        logger.info(f"Starting ingestion for {file_path}")
        
        # 1. Parse PDF
        parsed_data = self.parser.parse_pdf(file_path)
        markdown_content = parsed_data["markdown"]
        metadata = parsed_data["metadata"]
        images = parsed_data.get("images", [])
        
        # 2. Process Images (Multi-Modal)
        if images:
            logger.info(f"Found {len(images)} images. Generating captions...")
            for img in images:
                # In a real scenario, we would read the image data here.
                # For now, we assume we have a way to get the base64 or skip if not present.
                # Since DoclingParser in this setup isn't returning full base64 yet,
                # we will simulate or use a placeholder if image_data is missing.
                
                # Placeholder logic for demonstration if image_data is not passed
                image_data = img.get("image_data_base64", "") 
                if image_data:
                    caption = await self.vlm.generate_caption(image_data)
                    img["generated_caption"] = caption
                    # Append caption to markdown to make it searchable
                    markdown_content += f"\n\n![Image: {caption}]\n"
            
            metadata["image_count"] = len(images)
        
        # 3. Chunking
        logger.info("Chunking document...")
        chunks = self.chunker.hierarchical_chunking(markdown_content, metadata)
        logger.info(f"Generated {len(chunks)} chunks")
        
        # 4. Embedding (Optional here, can be done during indexing)
        # chunks = await self.chunker.embed_chunks(chunks)
        
        # 5. Indexing (Placeholder)
        # await self.search_engine.index_chunks(chunks)
        
        return {
            "status": "success",
            "chunks_count": len(chunks),
            "metadata": metadata,
            "processed_images": len(images)
        }

    async def batch_ingest(self, directory_path: str):
        """
        Ingest all PDFs in a directory.
        """
        path = Path(directory_path)
        tasks = []
        
        for file_path in path.glob("*.pdf"):
            tasks.append(self.process_document(str(file_path)))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
        logger.info(f"Batch ingestion complete. Success: {success_count}/{len(results)}")
        return results

