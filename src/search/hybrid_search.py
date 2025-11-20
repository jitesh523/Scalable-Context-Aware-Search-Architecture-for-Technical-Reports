"""
Unified Hybrid Search Engine.
Orchestrates Milvus and Elasticsearch with RRF.
"""

import logging
import asyncio
from typing import List, Dict, Any

from src.search.milvus_client import MilvusClient
from src.search.elasticsearch_client import ElasticsearchClient
from src.search.rrf_fusion import RRFFusion
from langchain_openai import OpenAIEmbeddings

from config.settings import settings

logger = logging.getLogger(__name__)

class HybridSearchEngine:
    """
    Main search engine class combining dense and sparse retrieval.
    """
    
    def __init__(self):
        self.milvus = MilvusClient()
        self.es = ElasticsearchClient()
        self.rrf = RRFFusion()
        self.embeddings = OpenAIEmbeddings(
            model=settings.llm.embedding_model,
            api_key=settings.llm.openai_api_key
        )
        
    async def initialize(self):
        """Initialize async components."""
        await self.es.ensure_index()

    async def index_chunks(self, chunks: List[Any]):
        """
        Index chunks into both databases.
        """
        # Prepare data format
        formatted_chunks = []
        for chunk in chunks:
            formatted_chunks.append({
                "id": chunk.chunk_id,
                "content": chunk.content,
                "embedding": chunk.embedding,
                "metadata": chunk.metadata,
                "parent_id": chunk.parent_id
            })
            
        # Parallel indexing
        await asyncio.gather(
            self.es.index_chunks(formatted_chunks),
            asyncio.to_thread(self.milvus.insert_chunks, formatted_chunks)
        )
        logger.info(f"Indexed {len(chunks)} chunks in hybrid engine")

    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform hybrid search.
        """
        # 1. Generate embedding for query
        query_vector = await self.embeddings.aembed_query(query)
        
        # 2. Parallel search execution
        semantic_task = asyncio.to_thread(
            self.milvus.search, 
            vector=query_vector, 
            limit=limit * 2 # Fetch more for re-ranking
        )
        lexical_task = self.es.search(query, limit=limit * 2)
        
        semantic_results, lexical_results = await asyncio.gather(
            semantic_task, lexical_task
        )
        
        # 3. RRF Fusion
        fused_results = self.rrf.fuse(
            semantic_results, 
            lexical_results, 
            limit=limit
        )
        
        return fused_results
        
    async def close(self):
        await self.es.close()
