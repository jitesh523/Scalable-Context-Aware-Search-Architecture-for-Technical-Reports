"""
Elasticsearch client for lexical search.
Handles keyword matching with custom analyzers.
"""

import logging
from typing import List, Dict, Any
from elasticsearch import AsyncElasticsearch, helpers

from config.settings import settings

logger = logging.getLogger(__name__)

class ElasticsearchClient:
    """
    Client for Elasticsearch lexical search.
    """
    
    def __init__(self):
        self.client = AsyncElasticsearch(
            hosts=[f"http://{settings.elasticsearch.elasticsearch_host}:{settings.elasticsearch.elasticsearch_port}"],
            basic_auth=(settings.elasticsearch.elasticsearch_user, settings.elasticsearch.elasticsearch_password)
        )
        self.index_name = settings.elasticsearch.elasticsearch_index_name

    async def ensure_index(self):
        """Create index with custom settings if it doesn't exist."""
        if await self.client.indices.exists(index=self.index_name):
            return

        # Custom analyzer for technical text
        settings_body = {
            "analysis": {
                "analyzer": {
                    "technical_analyzer": {
                        "type": "custom",
                        "tokenizer": "whitespace",  # Preserve special chars like part numbers
                        "filter": ["lowercase", "stop", "snowball"]
                    }
                }
            }
        }
        
        mappings = {
            "properties": {
                "content": {
                    "type": "text",
                    "analyzer": "technical_analyzer"
                },
                "metadata": {"type": "object"},
                "parent_id": {"type": "keyword"},
                "chunk_id": {"type": "keyword"}
            }
        }
        
        await self.client.indices.create(
            index=self.index_name,
            settings=settings_body,
            mappings=mappings
        )
        logger.info(f"Created Elasticsearch index {self.index_name}")

    async def index_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Bulk index chunks.
        """
        actions = []
        for chunk in chunks:
            action = {
                "_index": self.index_name,
                "_id": chunk["id"],
                "_source": {
                    "content": chunk["content"],
                    "metadata": chunk["metadata"],
                    "parent_id": chunk.get("parent_id"),
                    "chunk_id": chunk["id"]
                }
            }
            actions.append(action)
            
        await helpers.async_bulk(self.client, actions)
        logger.info(f"Indexed {len(chunks)} documents in Elasticsearch")

    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform BM25 lexical search.
        """
        response = await self.client.search(
            index=self.index_name,
            query={
                "match": {
                    "content": {
                        "query": query,
                        "analyzer": "technical_analyzer"
                    }
                }
            },
            size=limit
        )
        
        hits = []
        for hit in response["hits"]["hits"]:
            hits.append({
                "id": hit["_id"],
                "score": hit["_score"],
                "content": hit["_source"]["content"],
                "metadata": hit["_source"]["metadata"],
                "parent_id": hit["_source"].get("parent_id")
            })
            
        return hits
        
    async def close(self):
        await self.client.close()
