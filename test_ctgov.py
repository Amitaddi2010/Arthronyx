
import asyncio
import httpx

async def test_search():
    BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.term": "platelet-rich plasma",
        "pageSize": 5,
        "format": "json",
        "fields": "NCTId,BriefTitle"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://clinicaltrials.gov/"
    }
    
    print(f"Testing connection to {BASE_URL} with httpx...")
    try:
        async with httpx.AsyncClient(timeout=10, headers=headers) as client:
            resp = await client.get(BASE_URL, params=params)
            print(f"Status Code: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"Success! Found {len(data.get('studies', []))} studies.")
            else:
                print(f"Error: {resp.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_search())
