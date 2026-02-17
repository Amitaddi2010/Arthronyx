
import asyncio
import os
from openai import AsyncOpenAI

# Load key from env or hardcode for test if needed (but better from env)
# We know the key is in config
import sys
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from app.config import settings

async def list_models():
    if not settings.llm_api_key:
        print("No API Key found")
        return

    client = AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url
    )
    
    try:
        models = await client.models.list()
        print("Available Models:")
        for m in models.data:
            print(f" - {m.id}")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    asyncio.run(list_models())
