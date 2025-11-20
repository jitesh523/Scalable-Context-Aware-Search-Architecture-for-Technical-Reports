-- ============================================
-- PostgreSQL Schema (Cloud SQL)
-- ============================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- User Query History Table (Memory)
CREATE TABLE IF NOT EXISTS user_query_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    query_text TEXT NOT NULL,
    response_text TEXT NOT NULL,
    embedding vector(768),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create index for vector search
CREATE INDEX IF NOT EXISTS idx_query_embedding 
ON user_query_history 
USING hnsw (embedding vector_cosine_ops);


-- ============================================
-- Snowflake Schema (Analytics)
-- ============================================

/*
-- Run these commands in Snowflake

CREATE DATABASE IF NOT EXISTS RAG_ANALYTICS;
CREATE SCHEMA IF NOT EXISTS RAG_ANALYTICS.PUBLIC;

-- Feedback Logs Table
CREATE TABLE IF NOT EXISTS RAG_FEEDBACK_LOGS (
    QUERY_ID VARCHAR(255),
    USER_ID VARCHAR(255),
    PROMPT_TEXT STRING,
    RETRIEVED_DOC_IDS STRING, -- Stored as JSON string or ARRAY
    RESPONSE_TEXT STRING,
    FEEDBACK_SCORE INTEGER, -- 1 to 5
    CORRECTION_COMMENT STRING,
    TIMESTAMP TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Document Metadata Table (Golden Source)
CREATE TABLE IF NOT EXISTS DOCUMENT_METADATA (
    DOC_ID VARCHAR(255) PRIMARY KEY,
    FILENAME STRING,
    TITLE STRING,
    AUTHOR STRING,
    PUBLISH_DATE DATE,
    VERSION STRING,
    S3_PATH STRING,
    EMBEDDING VECTOR(FLOAT, 768) -- Snowflake Native Vector Type
);
*/
