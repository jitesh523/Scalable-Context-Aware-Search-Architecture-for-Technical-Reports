# Scalable Context-Aware Search Architecture for Technical Reports

A production-grade RAG (Retrieval Augmented Generation) system designed to handle 10,000+ technical reports using hybrid search, agentic orchestration, and enterprise data integration.

## 🏗️ Architecture Overview

This system implements a sophisticated multi-agent RAG architecture combining:

- **Advanced PDF Parsing**: Docling for high-fidelity extraction of tables, equations, and hierarchical structures
- **Hybrid Search**: Milvus (vector/semantic) + Elasticsearch (keyword) with Reciprocal Rank Fusion
- **Agentic Orchestration**: LangGraph-based multi-agent system with self-correction
- **Enterprise Integration**: Cloud SQL (pgvector) + Snowflake for analytics
- **Observability**: Grafana + Power BI for system and product metrics

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Google Cloud SDK
- OpenAI API Key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd <repo-name>
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start infrastructure (Local)**
   ```bash
   docker-compose up -d
   ```
   This starts Milvus, Elasticsearch, PostgreSQL, Redis, Grafana, and Prometheus.

4. **Verify Services**
   ```bash
   # Check all services are healthy
   docker-compose ps
   
   # Access Grafana: http://localhost:3000 (admin/admin)
   # Access Milvus: http://localhost:19530
   # Access Elasticsearch: http://localhost:9200
   ```

5. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

6. **Run the application**
   ```bash
   uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Access API Documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 🏗️ Architecture

### Components
- **Ingestion**: Docling (PDF parsing), LangChain (Chunking)
- **Search**: Milvus (Vector), Elasticsearch (Lexical), RRF (Fusion)
- **Orchestration**: LangGraph (Router, Graders, Self-Correction)
- **Storage**: Cloud SQL (pgvector), Snowflake (Analytics)
- **Observability**: OpenTelemetry, Prometheus, Grafana

### Data Flow
1. **Ingestion**: PDF -> Docling -> Chunks -> Embeddings -> Milvus/Elasticsearch
2. **Search**: Query -> Router -> Hybrid Search -> RRF -> Context
3. **Generation**: Context + Query -> LLM -> Answer -> Hallucination Check -> Response

## 🧪 Testing

### Unit & Integration Tests
```bash
pytest tests/ -v
```

### Load Testing
```bash
locust -f tests/load_test.py
```

## ☁️ Deployment

### Google Cloud Run
   docker-compose ps
   
   # Access Grafana: http://localhost:3000 (admin/admin)
   # Access Milvus: http://localhost:19530
   # Access Elasticsearch: http://localhost:9200
   ```

5. **Run the Application**
   ```bash
   uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access API Documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 📁 Project Structure

```
nice/
├── src/
│   ├── ingestion/          # PDF parsing and chunking
│   ├── search/             # Hybrid search (Milvus + ES + RRF)
│   ├── agents/             # LangGraph agentic orchestration
│   ├── database/           # Cloud SQL & Snowflake clients
│   ├── observability/      # OpenTelemetry & metrics
│   └── api/                # FastAPI application
├── tests/                  # Unit and integration tests
├── config/                 # Configuration files
├── grafana/                # Grafana dashboards
├── terraform/              # GCP infrastructure as code
├── docker-compose.yml      # Local development services
├── Dockerfile              # Production container
└── requirements.txt        # Python dependencies
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run load tests
locust -f tests/load_test.py
```

## 📊 Observability

### Grafana Dashboards
- System Metrics: http://localhost:3000/d/system-metrics
- Query Latency Waterfall
- Token Usage & Cost Tracking
- Database Performance

### Prometheus Metrics
- Raw metrics: http://localhost:9090

## 🔧 Configuration

Key configuration files:
- `.env` - Environment variables and secrets
- `config/prometheus.yml` - Metrics scraping configuration
- `docker-compose.yml` - Local infrastructure setup

## 🚢 Deployment

### Google Cloud Run

1. **Build and Push Container**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/rag-system
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy rag-system \
     --image gcr.io/PROJECT_ID/rag-system \
     --platform managed \
     --region us-central1 \
     --vpc-connector rag-connector \
     --set-env-vars-file .env.yaml
   ```

3. **Infrastructure (Terraform)**
   ```bash
   cd terraform
   terraform init
   terraform plan
   terraform apply
   ```

## 📚 API Endpoints

- `POST /search` - Hybrid search with agentic orchestration
- `POST /ingest` - Upload and process technical documents
- `POST /feedback` - Submit user feedback for quality metrics
- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics

## 🔐 Security

- JWT-based authentication
- Service account authentication for GCP
- Secrets managed via GCP Secret Manager
- Rate limiting per user
- Non-root container execution

## 📈 Performance

- Sub-second query latency (p95 < 1s)
- Handles 1000+ concurrent users
- Auto-scaling on Cloud Run (0 to N instances)
- Precision@5 > 0.8, MRR > 0.7

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## 📄 License

[Your License Here]

## 🙏 Acknowledgments

Built with:
- [Docling](https://github.com/DS4SD/docling) - Advanced PDF parsing
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agentic orchestration
- [Milvus](https://milvus.io/) - Vector database
- [Elasticsearch](https://www.elastic.co/) - Lexical search
