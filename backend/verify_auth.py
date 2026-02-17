
import asyncio
import httpx
import time

BASE_URL = "http://localhost:8000/api/v1/auth"

async def test_auth_flow():
    # Helper to print steps
    def log(msg):
        print(f"\n[TEST] {msg}")

    async with httpx.AsyncClient() as client:
        # Wait for server to start
        log("Waiting for server...")
        for _ in range(10):
            try:
                await client.get("http://localhost:8000/api/v1/health")
                break
            except:
                await asyncio.sleep(1)
        
        email = f"testuser_{int(time.time())}@example.com"
        password = "securepassword123"
        name = "Test User"

        # 1. Signup
        log(f"Testing Signup: {email}")
        resp = await client.post(f"{BASE_URL}/signup", json={
            "email": email,
            "password": password,
            "full_name": name
        })
        if resp.status_code == 201:
            print("✅ Signup Successful:", resp.json())
        else:
            print("❌ Signup Failed:", resp.status_code, resp.text)
            return

        # 2. Login (Get Token)
        log("Testing Login (Token)")
        resp = await client.post(f"{BASE_URL}/token", data={
            "username": email,
            "password": password
        })
        if resp.status_code == 200:
            token_data = resp.json()
            access_token = token_data["access_token"]
            print(f"✅ Login Successful. Token: {access_token[:20]}...")
        else:
            print("❌ Login Failed:", resp.status_code, resp.text)
            return

        # 3. Get Me (Protected Route)
        log("Testing /me Endpoint")
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = await client.get(f"{BASE_URL}/me", headers=headers)
        if resp.status_code == 200:
            user_data = resp.json()
            print("✅ Profile Access Successful:", user_data)
            assert user_data["email"] == email
            assert user_data["full_name"] == name
        else:
            print("❌ Profile Access Failed:", resp.status_code, resp.text)

if __name__ == "__main__":
    asyncio.run(test_auth_flow())
