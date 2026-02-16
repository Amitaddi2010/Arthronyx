# Example Query Workflow

This document illustrates an end-to-end workflow for a typical clinical query in Arthronyx.

## Scenario
**Clinical Question:** "Is antibiotic-loaded bone cement superior to plain cement for preventing infection in primary total knee arthroplasty (TKA)?"

## Step 1: Ingestion
First, ensure the system has relevant data.
```bash
curl -X POST "http://localhost:8000/api/v1/ingest?query=antibiotic%20bone%20cement%20TKA&max_pubmed=200"
```
*System action*: Fetches ~200 articles from PubMed, classifies them (RCTs, cohorts), chunks text, generates embeddings, and builds the citation graph.

## Step 2: Query Execution
Submit the specific query via the API or Frontend.

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "efficacy of antibiotic-loaded bone cement in primary TKA for infection prevention",
    "subdomain_filter": "Arthroplasty",
    "study_types": ["RCT", "Meta-analysis", "Systematic Review"]
  }'
```

## Step 3: System Processing (Internal)

1. **Retrieval**:
   - **BM25** finds papers containing "antibiotic", "cement", "infection".
   - **Dense Search** finds semantically related terms like "gentamicin-loaded", "periprosthetic joint infection".
   - **Re-ranking** promotes high-quality RCTs over case reports.

2. **Analysis**:
   - **Stance Classifier** reads abstracts.
     - Study A (2023): "No significant reduction in infection rates." → **No Significant Difference**
     - Study B (2020): "Lower infection rates in high-risk patients." → **Positive Effect**
   - **Conflict Detection**: Identifies a potential conflict or nuance (routine vs high-risk).

3. **Synthesis**:
   - LLM generates a summary citing Study A and B.
   - Validator checks that Study A and B DOIs are in the retrieval set.

## Step 4: Output Review

The system returns a structured response:

**Final Evidence Position**:
> "Current high-level evidence (Level I-II) suggests that antibiotic-loaded bone cement **does not** significantly reduce deep infection rates in **routine** primary TKA compared to plain cement (DOI: 10.1xxx/...). However, some evidence supports its use in **high-risk** populations (DOI: 10.1xxx/...). Routine use varies by national registry data."

**Conflict Report**:
- **Cluster 1 (No Difference)**: 12 studies (n=45,000)
- **Cluster 2 (Positive Effect)**: 4 studies (n=12,000)
- **Summary**: "Partial conflict: Majority of evidence shows no benefit in unselected patients, while a smaller subset suggests benefit in specific high-risk groups."

## Step 5: Decision
The clinician uses this synthesis to inform their decision, noting the distinction between routine and high-risk patients highlighted by the system.
