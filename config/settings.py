"""
Centralized configuration management using Pydantic Settings.
Loads configuration from environment variables with validation.
"""

from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """LLM and Embedding Model Configuration"""
    
    openai_api_key: str = Field(..., description="OpenAI API Key")
    openai_model: str = Field(default="gpt-4-turbo-preview", description="LLM model name")
    embedding_model: str = Field(default="text-embedding-3-large", description="Embedding model")
    embedding_dimension: int = Field(default=768, description="Embedding vector dimension")
    temperature: float = Field(default=0.0, description="LLM temperature")
    max_tokens: int = Field(default=2048, description="Max tokens for generation")
    
    model_config = SettingsConfigDict(env_prefix="")


class MilvusSettings(BaseSettings):
    """Milvus Vector Database Configuration"""
    
    milvus_host: str = Field(default="localhost", description="Milvus host")
    milvus_port: int = Field(default=19530, description="Milvus port")
    milvus_user: str = Field(default="root", description="Milvus username")
    milvus_password: str = Field(default="Milvus", description="Milvus password")
    milvus_collection_name: str = Field(default="technical_reports", description="Collection name")
    
    # Index Configuration
    index_type: str = Field(default="HNSW", description="Index type (HNSW, IVF_FLAT, etc.)")
    metric_type: str = Field(default="COSINE", description="Similarity metric (COSINE, IP, L2)")
    hnsw_m: int = Field(default=16, description="HNSW M parameter")
    hnsw_ef_construction: int = Field(default=200, description="HNSW efConstruction")
    hnsw_ef_search: int = Field(default=100, description="HNSW ef search parameter")
    
    model_config = SettingsConfigDict(env_prefix="")


class ElasticsearchSettings(BaseSettings):
    """Elasticsearch Configuration"""
    
    elasticsearch_host: str = Field(default="localhost", description="Elasticsearch host")
    elasticsearch_port: int = Field(default=9200, description="Elasticsearch port")
    elasticsearch_user: str = Field(default="elastic", description="Elasticsearch username")
    elasticsearch_password: str = Field(default="changeme", description="Elasticsearch password")
    elasticsearch_index_name: str = Field(default="technical_reports", description="Index name")
    
    model_config = SettingsConfigDict(env_prefix="")


class HybridSearchSettings(BaseSettings):
    """Hybrid Search Configuration"""
    
    rrf_k_constant: int = Field(default=60, description="RRF k constant")
    semantic_weight: float = Field(default=0.5, description="Weight for semantic search")
    lexical_weight: float = Field(default=0.5, description="Weight for lexical search")
    top_k_results: int = Field(default=5, description="Number of results to return")
    
    @field_validator('semantic_weight', 'lexical_weight')
    @classmethod
    def validate_weights(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("Weights must be between 0.0 and 1.0")
        return v
    
    model_config = SettingsConfigDict(env_prefix="")


class PostgresSettings(BaseSettings):
    """PostgreSQL with pgvector Configuration"""
    
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_db: str = Field(default="rag_system", description="Database name")
    postgres_user: str = Field(default="postgres", description="PostgreSQL username")
    postgres_password: str = Field(default="postgres", description="PostgreSQL password")
    postgres_pool_size: int = Field(default=10, description="Connection pool size")
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    model_config = SettingsConfigDict(env_prefix="")


class SnowflakeSettings(BaseSettings):
    """Snowflake Data Warehouse Configuration"""
    
    snowflake_account: str = Field(..., description="Snowflake account identifier")
    snowflake_user: str = Field(..., description="Snowflake username")
    snowflake_password: str = Field(..., description="Snowflake password")
    snowflake_database: str = Field(default="RAG_ANALYTICS", description="Database name")
    snowflake_schema: str = Field(default="PUBLIC", description="Schema name")
    snowflake_warehouse: str = Field(default="COMPUTE_WH", description="Warehouse name")
    
    model_config = SettingsConfigDict(env_prefix="")


class ChunkingSettings(BaseSettings):
    """Document Chunking Configuration"""
    
    chunk_size: int = Field(default=512, description="Child chunk size in tokens")
    chunk_overlap: int = Field(default=100, description="Overlap between chunks")
    parent_chunk_size: int = Field(default=2048, description="Parent chunk size")
    semantic_similarity_threshold: float = Field(default=0.6, description="Threshold for semantic chunking")
    
    model_config = SettingsConfigDict(env_prefix="")


class LangGraphSettings(BaseSettings):
    """LangGraph Agentic Orchestration Configuration"""
    
    max_iterations: int = Field(default=3, description="Max iterations for self-correction")
    relevance_threshold: float = Field(default=0.7, description="Relevance score threshold")
    hallucination_check_enabled: bool = Field(default=True, description="Enable hallucination checking")
    
    model_config = SettingsConfigDict(env_prefix="")


class APISettings(BaseSettings):
    """API Server Configuration"""
    
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=4, description="Number of workers")
    cors_origins: List[str] = Field(default=["http://localhost:3000"], description="CORS origins")
    jwt_secret_key: str = Field(..., description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per user")
    
    model_config = SettingsConfigDict(env_prefix="")


class ObservabilitySettings(BaseSettings):
    """Observability and Monitoring Configuration"""
    
    otel_exporter_otlp_endpoint: str = Field(default="http://localhost:4317", description="OTLP endpoint")
    grafana_endpoint: str = Field(default="http://localhost:3000", description="Grafana endpoint")
    enable_tracing: bool = Field(default=True, description="Enable OpenTelemetry tracing")
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    log_level: str = Field(default="INFO", description="Logging level")
    
    model_config = SettingsConfigDict(env_prefix="")


class StorageSettings(BaseSettings):
    """Storage Configuration"""
    
    document_storage_path: str = Field(default="/data/documents", description="Document storage path")
    temp_upload_path: str = Field(default="/tmp/uploads", description="Temporary upload path")
    max_upload_size_mb: int = Field(default=50, description="Max upload size in MB")
    
    model_config = SettingsConfigDict(env_prefix="")


class FeatureFlagsSettings(BaseSettings):
    """Feature Flags"""
    
    enable_web_search: bool = Field(default=False, description="Enable web search fallback")
    enable_query_expansion: bool = Field(default=True, description="Enable query expansion")
    enable_caching: bool = Field(default=True, description="Enable response caching")
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")
    
    model_config = SettingsConfigDict(env_prefix="")


class Settings(BaseSettings):
    """Master Settings Container"""
    
    llm: LLMSettings = Field(default_factory=LLMSettings)
    milvus: MilvusSettings = Field(default_factory=MilvusSettings)
    elasticsearch: ElasticsearchSettings = Field(default_factory=ElasticsearchSettings)
    hybrid_search: HybridSearchSettings = Field(default_factory=HybridSearchSettings)
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    snowflake: Optional[SnowflakeSettings] = None
    chunking: ChunkingSettings = Field(default_factory=ChunkingSettings)
    langgraph: LangGraphSettings = Field(default_factory=LangGraphSettings)
    api: APISettings = Field(default_factory=APISettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    features: FeatureFlagsSettings = Field(default_factory=FeatureFlagsSettings)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
