"""
Cloud SQL (PostgreSQL) client with pgvector support.
Handles user query history and conversation memory.
"""

import logging
from typing import List, Dict, Any, Optional
import psycopg
from psycopg.rows import dict_row
from pgvector.psycopg import register_vector

from config.settings import settings

logger = logging.getLogger(__name__)

class CloudSQLClient:
    """
    Client for PostgreSQL with pgvector.
    """
    
    def __init__(self):
        self.mock_mode = settings.features.mock_mode
        self.conn_str = settings.postgres.database_url
        self.mock_history = []
        
        if not self.mock_mode:
            self._init_db()
        else:
            logger.info("CloudSQLClient initialized in MOCK MODE")
        
    def _init_db(self):
        """Initialize database connection and extensions."""
        try:
            with psycopg.connect(self.conn_str, autocommit=True) as conn:
                conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                register_vector(conn)
                logger.info("Connected to Cloud SQL and enabled pgvector")
        except Exception as e:
            logger.error(f"Failed to connect to Cloud SQL: {e}")
            raise

    def save_interaction(self, user_id: str, query: str, response: str, embedding: List[float]):
        """
        Save user interaction with embedding for memory.
        """
        if self.mock_mode:
            self.mock_history.append({
                "user_id": user_id,
                "query_text": query,
                "response_text": response,
                "embedding": embedding,
                "timestamp": "2024-01-01T00:00:00" # Dummy timestamp
            })
            logger.info("[MOCK] Saved interaction to CloudSQL mock")
            return

        with psycopg.connect(self.conn_str, autocommit=True) as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO user_query_history (user_id, query_text, response_text, embedding)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (user_id, query, response, embedding)
                )

    def get_user_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent user history.
        """
        if self.mock_mode:
            user_history = [h for h in self.mock_history if h["user_id"] == user_id]
            return user_history[-limit:]

        with psycopg.connect(self.conn_str, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT query_text, response_text, timestamp 
                    FROM user_query_history 
                    WHERE user_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                    """,
                    (user_id, limit)
                )
                return cur.fetchall()

    def search_memory(self, user_id: str, query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Semantic search over user's conversation history.
        """
        if self.mock_mode:
            # Return empty or random for mock
            return []

        with psycopg.connect(self.conn_str, row_factory=dict_row) as conn:
            register_vector(conn)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT query_text, response_text, timestamp, 
                           1 - (embedding <=> %s) as similarity
                    FROM user_query_history 
                    WHERE user_id = %s 
                    ORDER BY similarity DESC 
                    LIMIT %s
                    """,
                    (query_embedding, user_id, limit)
                )
                return cur.fetchall()
