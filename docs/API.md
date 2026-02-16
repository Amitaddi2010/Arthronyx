# Arthronyx API Reference

Base URL: `http://localhost:8000/api/v1`

## Endpoints

### 1. Query Evidence
**POST** `/query`

Executes the full evidence synthesis pipeline.

**Request Body:**
```json
{
  "query": "outcomes of total hip arthroplasty in patients over 80",
  "subdomain_filter": "Arthroplasty",
  "year_from": 2015,
  "max_results": 10
}
```

**Response:**
```json
{
  "success": true,
  "query_id": "uuid-string",
  "result": {
    "clinical_question": "...",
    "evidence_overview": { ... },
    "priority_evidence": [ ... ],
    "conflict_report": {
      "has_conflict": true,
      "conflict_summary": "...",
      "clusters": [ ... ]
    },
    "evidence_synthesis": "...",
    "limitations": [ ... ],
    "final_position": "...",
    "disclaimer": "...",
    "citations": [ ... ]
  }
}
```

### 2. Trigger Ingestion
**POST** `/ingest`

Triggers the background data ingestion pipeline.

**Parameters:**
- `query` (string): Search term for PubMed/ClinicalTrials (default: "orthopedic surgery outcomes")
- `max_pubmed` (int): Max articles to fetch (default: 100)

**Response:**
```json
{
  "message": "Ingestion pipeline triggered in background.",
  "params": { ... }
}
```

### 3. Citiation Graph
**GET** `/citations/{doi}`

Retrieves network analysis for a specific paper.

**Response:**
```json
{
  "doi": "10.1016/j.arth.2023.01.001",
  "citation_network": [ ... ],
  "co_citations": [ ... ],
  "dominance": { "dominance_pct": 12.5 }
}
```

### 4. Audit Logs
**GET** `/audit`

Retrieves system usage logs (Admin only).

**Parameters:**
- `skip` (int): Pagination offset
- `limit` (int): Pagination limit

### 5. Health Check
**GET** `/health`

Returns service status.

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "postgres": "connected",
    "qdrant": "connected",
    "neo4j": "connected"
  }
}
```
