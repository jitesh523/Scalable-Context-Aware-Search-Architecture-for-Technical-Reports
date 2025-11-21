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
from src.graph.extractor import GraphExtractor
from src.graph.neo4j_client import Neo4jClient
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
        self.graph_extractor = GraphExtractor()
        self.neo4j = Neo4jClient()
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
                image_data = img.get("image_data_base64", "") 
                if image_data:
                    caption = await self.vlm.generate_caption(image_data)
                    img["generated_caption"] = caption
                    markdown_content += f"\n\n![Image: {caption}]\n"
            
            metadata["image_count"] = len(images)
        
        # 3. Chunking
        logger.info("Chunking document...")
        chunks = self.chunker.hierarchical_chunking(markdown_content, metadata)
        logger.info(f"Generated {len(chunks)} chunks")
        
        # 4. Graph Extraction & Indexing
        logger.info("Extracting knowledge graph...")
        graph_nodes = 0
        graph_edges = 0
        
        # We only extract from parent chunks to save tokens/time
        parent_chunks = [c for c in chunks if c.metadata.get("level") == "parent"]
        
        for chunk in parent_chunks:
            graph_data = await self.graph_extractor.extract(chunk.content)
            
            # Store in Neo4j
            for entity in graph_data.get("entities", []):
                await self.neo4j.add_entity(
                    label=entity["type"], 
                    name=entity["name"],
                    properties={"source_doc": metadata["filename"]}
                )
                graph_nodes += 1
                
            for rel in graph_data.get("relationships", []):
                await self.neo4j.add_relationship(
                    source_name=rel["source"],
                    target_name=rel["target"],
                    relation_type=rel["type"]
                )
                graph_edges += 1
                
        logger.info(f"Graph extraction complete: {graph_nodes} nodes, {graph_edges} edges")
        
        # 5. Embedding (Optional here, can be done during indexing)
        # chunks = await self.chunker.embed_chunks(chunks)
        
        # 6. Indexing (Placeholder)
        # await self.search_engine.index_chunks(chunks)
        
        return {
            "status": "success",
            "chunks_count": len(chunks),
            "metadata": metadata,
            "processed_images": len(images),
            "graph_stats": {"nodes": graph_nodes, "edges": graph_edges}
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

