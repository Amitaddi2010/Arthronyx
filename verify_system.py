
import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.config import settings
# Import conditionally to avoid failing immediately if dependencies issues exist
try:
    from app.ingestion.pubmed import search_and_fetch as pubmed_fetch
    from app.ingestion.openalex import search_and_fetch as openalex_fetch
    from app.ingestion.clinicaltrials import search_and_fetch as ctgov_fetch
    from app.retrieval.dense import _get_model
    from openai import AsyncOpenAI
except ImportError as e:
    print(f"CRITICAL IMPORT ERROR: {e}")
    sys.exit(1)

async def main():
    print(f"--- 1. Configuration Check ---")
    print(f"LLM API Key Present: {'YES' if settings.llm_api_key else 'NO'} ({settings.llm_api_key[:5]}...)")
    print(f"PubMed API Key Present: {'YES' if settings.pubmed_api_key else 'NO'}")
    print(f"OpenAlex API Key Present: {'YES' if settings.openalex_api_key else 'NO'}")

    print(f"\n--- 2. Dense Model Check ---")
    try:
        print(f"Loading Embedding Model (Model: {settings.embedding_model})...")
        model = _get_model()
        # Verify model object exists
        if model:
            print("Embedding Model Loaded Successfully.")
            print(f"Model Object: {type(model)}")
        else:
            print("Embedding Model Loaded but returned None.")
    except Exception as e:
        print(f"Dense Model Failed: {e}")

    print(f"\n--- 3. External Source Check (Query: 'ACL reconstruction') ---")
    query = "ACL reconstruction"
    
    # PubMed
    try:
        print("Fetching PubMed...", end="", flush=True)
        pm_docs = await pubmed_fetch(query, max_results=3)
        print(f" Success ({len(pm_docs)} docs)")
    except Exception as e:
        print(f" Failed: {e}")

    # OpenAlex
    try:
        print("Fetching OpenAlex...", end="", flush=True)
        oa_docs = await openalex_fetch(query, max_results=3)
        print(f" Success ({len(oa_docs)} docs)")
    except Exception as e:
        print(f" Failed: {e}")

    # ClinicalTrials
    try:
        print("Fetching ClinicalTrials...", end="", flush=True)
        ct_docs = await ctgov_fetch(query, max_results=3)
        print(f" Success ({len(ct_docs)} docs)")
    except Exception as e:
        print(f" Failed: {e}")

    print(f"\n--- 4. Groq API Check ---")
    if settings.llm_api_key:
        try:
            client = AsyncOpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
            print(f"Sending test request to Groq (Model: {settings.llm_model})...", end="", flush=True)
            resp = await client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": "Say 'OK' if you can hear me."}],
                max_tokens=10
            )
            print(f" Success! Response: {resp.choices[0].message.content}")
        except Exception as e:
            print(f" Failed: {e}")
    else:
        print("Skipping Groq check (No API Key)")

if __name__ == "__main__":
    asyncio.run(main())
