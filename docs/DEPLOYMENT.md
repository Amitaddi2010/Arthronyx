# Arthronyx Deployment Guide

This guide covers setting up Arthronyx for production or local development.

## Prerequisites

- **Docker & Docker Compose** (v2.20+)
- **API Keys**:
  - OpenAI API Key (for GPT-4)
  - PubMed API Key (optional, for higher rate limits)
  - NCBI Email (required for PubMed E-Utilities)

## Environment Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your credentials:
   ```ini
   # LLM Configuration
   LLM_API_KEY=sk-your-openai-key-here
   LLM_MODEL=gpt-4

   # PubMed Configuration
   PUBMED_EMAIL=your.email@institution.edu
   PUBMED_API_KEY=your-ncbi-key

   # Service Secrets (Change for production!)
   POSTGRES_PASSWORD=use_strong_password
   NEO4J_PASSWORD=use_strong_password
   SECRET_KEY=generate_random_string
   ```

## Launching the Stack

Run the following command to build and start all services:

```bash
docker compose up -d --build
```

This will launch:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard
- **Neo4j Browser**: http://localhost:7474

## Data Ingestion

The system starts empty. To hydrate the database with orthopedic evidence:

1. **Trigger Ingestion via API**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/ingest?query=orthopedic%20surgery&max_pubmed=200"
   ```

2. **Monitor Progress**:
   Check the backend logs:
   ```bash
   docker compose logs -f backend
   ```

## Verification

1. **Check Health**:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```
   Should return `{"status": "healthy", ...}`.

2. **Test Query**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/query \
     -H "Content-Type: application/json" \
     -d '{"query": "outcomes of total hip arthroplasty in patients over 80"}'
   ```

## Troubleshooting

- **Container OOM**: The embedding model (bge-large) requires ~2GB RAM. Ensure Docker has at least 8GB memory allocated.
- **Neo4j Connection**: Takes ~30s to start. The backend will retry connection automatically.
- **PubMed Rate Limits**: Ensure `PUBMED_API_KEY` is set to allow 10 requests/sec (vs 3 without key).
