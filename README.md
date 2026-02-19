# Arthronyx 1.0.1 (Pure Python Auth) — Evidence-Structured Orthopedic Intelligence Engine

> Citation-grounded, conflict-aware, time-weighted, guideline-aware orthopedic evidence synthesis.

## Overview

Arthronyx is a **production-grade medical evidence platform** that retrieves, ranks, and synthesizes orthopedic literature with:

- **Hybrid retrieval** (BM25 + dense embeddings + cross-encoder re-ranking)
- **Time-weighted scoring** with evidence hierarchy weighting
- **Conflict detection** across RCT outcomes
- **Hallucination prevention** with DOI-level citation validation
- **Structured output** following a mandatory 8-section format
- **Medico-legal compliance** with audit logging

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your credentials

# 2. Launch all services
docker compose up -d

# 3. Ingest initial corpus
curl -X POST http://localhost:8000/api/v1/ingest

# 4. Query
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "cemented vs uncemented total hip arthroplasty outcomes"}'
```

## Architecture

| Layer         | Technology                       |
|---------------|----------------------------------|
| Vector DB     | Qdrant                           |
| Relational DB | PostgreSQL 16                    |
| Graph DB      | Neo4j 5.x                        |
| Backend       | FastAPI (Python 3.11+)           |
| Frontend      | React + Vite                     |
| Embeddings    | bge-large-en-v1.5                |
| Re-ranker     | PubMedBERT cross-encoder         |
| LLM           | GPT-4 (temperature=0)           |

## Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Example Workflow](docs/EXAMPLE_WORKFLOW.md)

## Disclaimer

This system is an evidence synthesis engine. It does **not** provide medical advice and must not be used as a substitute for qualified clinical judgment.
