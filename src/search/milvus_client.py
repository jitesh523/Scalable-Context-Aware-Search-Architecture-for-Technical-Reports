"""
Milvus vector database client.
Handles collection management and vector search.
"""

import logging
from typing import List, Dict, Any, Optional
from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility
)

from config.settings import settings

logger = logging.getLogger(__name__)

class MilvusClient:
    """
    Client for Milvus Vector Database (v2.5+).
    """
    
    def __init__(self):
        self.mock_mode = settings.features.mock_mode
        self.collection_name = settings.milvus.milvus_collection_name
        self.mock_storage = []
        
        if not self.mock_mode:
            self.connect()
            self._ensure_collection()
        else:
            logger.info("MilvusClient initialized in MOCK MODE")
        
    def connect(self):
        """Establish connection to Milvus."""
        try:
            connections.connect(
                alias="default",
                host=settings.milvus.milvus_host,
                port=settings.milvus.milvus_port,
                user=settings.milvus.milvus_user,
                password=settings.milvus.milvus_password
            )
            logger.info("Connected to Milvus")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise

    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            self.collection.load()
            return

        # Define schema
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.llm.embedding_dimension),
            FieldSchema(name="metadata", dtype=DataType.JSON),
            FieldSchema(name="parent_id", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="project_id", dtype=DataType.VARCHAR, max_length=64) # For filtering
        ]
        
        schema = CollectionSchema(fields, "Technical reports collection")
        
        self.collection = Collection(self.collection_name, schema)
        
        # Create HNSW index
        index_params = {
            "metric_type": settings.milvus.metric_type,
            "index_type": settings.milvus.index_type,
            "params": {
                "M": settings.milvus.hnsw_m,
                "efConstruction": settings.milvus.hnsw_ef_construction
            }
        }
        
        self.collection.create_index(field_name="embedding", index_params=index_params)
        self.collection.load()
        logger.info(f"Created collection {self.collection_name} with HNSW index")

    def insert_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Insert chunks into Milvus.
        """
        if self.mock_mode:
            self.mock_storage.extend(chunks)
            logger.info(f"[MOCK] Inserted {len(chunks)} chunks into Milvus mock storage")
            return

        data = [
            [c["id"] for c in chunks],
            [c["content"] for c in chunks],
            [c["embedding"] for c in chunks],
            [c["metadata"] for c in chunks],
            [c.get("parent_id", "") for c in chunks],
            [c["metadata"].get("project_id", "default") for c in chunks]
        ]
        
        self.collection.insert(data)
        self.collection.flush()
        logger.info(f"Inserted {len(chunks)} chunks into Milvus")

    def search(self, vector: List[float], limit: int = 10, expr: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search.
        """
        if self.mock_mode:
            # Simple mock search - return random or all documents
            # In a real mock, we could do cosine similarity, but for now just return up to limit
            hits = []
            for i, chunk in enumerate(self.mock_storage[:limit]):
                hits.append({
                    "id": chunk["id"],
                    "score": 0.9 - (i * 0.01), # Fake score
                    "content": chunk["content"],
                    "metadata": chunk["metadata"],
                    "parent_id": chunk.get("parent_id")
                })
            logger.info(f"[MOCK] Search returned {len(hits)} results")
            return hits

        search_params = {
            "metric_type": settings.milvus.metric_type,
            "params": {"ef": settings.milvus.hnsw_ef_search}
        }
        
        results = self.collection.search(
            data=[vector],
            anns_field="embedding",
            param=search_params,
            limit=limit,
            expr=expr,
            output_fields=["content", "metadata", "id", "parent_id"]
        )
        
        hits = []
        for hit in results[0]:
            hits.append({
                "id": hit.id,
                "score": hit.score,
                "content": hit.entity.get("content"),
                "metadata": hit.entity.get("metadata"),
                "parent_id": hit.entity.get("parent_id")
            })
            
        return hits
