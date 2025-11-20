"""
Snowflake client for analytics and feedback loops.
Leverages Snowflake Cortex for vector operations.
"""

import logging
from typing import List, Dict, Any
import snowflake.connector
from snowflake.connector import DictCursor

from config.settings import settings

logger = logging.getLogger(__name__)

class SnowflakeClient:
    """
    Client for Snowflake Data Warehouse.
    """
    
    def __init__(self):
        if not settings.snowflake:
            logger.warning("Snowflake settings not configured. Client disabled.")
            self.enabled = False
            return
            
        self.enabled = True
        self.conn_params = {
            "user": settings.snowflake.snowflake_user,
            "password": settings.snowflake.snowflake_password,
            "account": settings.snowflake.snowflake_account,
            "warehouse": settings.snowflake.snowflake_warehouse,
            "database": settings.snowflake.snowflake_database,
            "schema": settings.snowflake.snowflake_schema
        }

    def log_feedback(self, feedback_data: Dict[str, Any]):
        """
        Log user feedback to Snowflake.
        """
        if not self.enabled:
            return

        query = """
        INSERT INTO RAG_FEEDBACK_LOGS 
        (QUERY_ID, USER_ID, PROMPT_TEXT, RETRIEVED_DOC_IDS, RESPONSE_TEXT, FEEDBACK_SCORE, CORRECTION_COMMENT)
        VALUES (%(query_id)s, %(user_id)s, %(prompt_text)s, %(retrieved_doc_ids)s, %(response_text)s, %(feedback_score)s, %(correction_comment)s)
        """
        
        try:
            with snowflake.connector.connect(**self.conn_params) as conn:
                with conn.cursor() as cur:
                    # Convert list to string for array storage if needed, or use VARIANT
                    if isinstance(feedback_data.get("retrieved_doc_ids"), list):
                        feedback_data["retrieved_doc_ids"] = str(feedback_data["retrieved_doc_ids"])
                        
                    cur.execute(query, feedback_data)
            logger.info("Logged feedback to Snowflake")
        except Exception as e:
            logger.error(f"Failed to log feedback to Snowflake: {e}")

    def generate_embedding_cortex(self, text: str) -> List[float]:
        """
        Generate embedding using Snowflake Cortex (if available).
        """
        if not self.enabled:
            return []
            
        query = "SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m', %(text)s) as embedding"
        
        try:
            with snowflake.connector.connect(**self.conn_params) as conn:
                with conn.cursor(DictCursor) as cur:
                    cur.execute(query, {"text": text})
                    result = cur.fetchone()
                    return result["embedding"] if result else []
        except Exception as e:
            logger.error(f"Cortex embedding failed: {e}")
            return []
