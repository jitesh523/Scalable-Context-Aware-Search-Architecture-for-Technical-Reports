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

from src.search.query_expansion import QueryExpander

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
        self.query_expander = QueryExpander()
        
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
        Perform hybrid search with query expansion.
        """
        # 1. Generate embedding for original query (Dense Search)
        query_vector = await self.embeddings.aembed_query(query)
        
        # 2. Expand query for Lexical Search
        expanded_terms = await self.query_expander.expand_query(query)
        expanded_query_str = " ".join(expanded_terms)
        logger.info(f"Expanded query: '{query}' -> '{expanded_query_str}'")
        
        # 3. Parallel search execution
        semantic_task = asyncio.to_thread(
            self.milvus.search, 
            vector=query_vector, 
            limit=limit * 2 
        )
        
        # Use expanded query for Elasticsearch
        lexical_task = self.es.search(expanded_query_str, limit=limit * 2)
        
        semantic_results, lexical_results = await asyncio.gather(
            semantic_task, lexical_task
        )
        
        # 4. RRF Fusion
        fused_results = self.rrf.fuse(
            semantic_results, 
            lexical_results, 
            limit=limit
        )
        
        return fused_results
        
    async def close(self):
        await self.es.close()
