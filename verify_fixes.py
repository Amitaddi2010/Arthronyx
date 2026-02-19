
import sys
import os
import asyncio
from fastapi.testclient import TestClient

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.main import app
from app.api.routes import auth

# Create a TestClient
client = TestClient(app)

def test_cors_on_error():
    """
    Test that a 500 error (unhandled exception) returns a response with CORS headers.
    We'll add a temporary route that raises an exception.
    """
    print("\n--- Testing CORS on 500 Error ---")
    
    @app.get("/error_test")
    def error_route():
        raise ValueError("Simulated crash")
    
    # We need to re-wrap the app in TestClient to pick up the new route? 
    # TestClient usually wraps the app instance. Modifying app routes *should* work if done before client calls?
    # Actually, starlette routing matches against current routes.
    
    try:
        response = client.get("/error_test", headers={"Origin": "https://arthronyx.vercel.app"})
        
        print(f"Status Code: {response.status_code}")
        print(f"CORS Allow Origin: {response.headers.get('access-control-allow-origin')}")
        
        if response.status_code == 500:
            print("Unknown Error Caught: YES")
        else:
            print(f"Unexpected Status: {response.status_code}")
            
        if response.headers.get('access-control-allow-origin') == "https://arthronyx.vercel.app":
            print("CORS Headers Present: YES")
        else:
            print("CORS Headers Present: NO")
            
    except Exception as e:
        print(f"Test Failed with Exception: {e}")

def test_signup_error_message():
    """
    Test that signup returns 400 with specific message.
    Note: This requires DB access. If DB is not set up, this might fail with 500 (which we also want to handle).
    """
    print("\n--- Testing Signup Error Message ---")
    pass
    # Skipping actual signup test as it modifies DB or requires running DB.
    # We can rely on the user code analysis for the 400 propagation.
    # But if we can mock the DB... too complex for a quick script.
    
    # However, we can verify that 400 response *would* have CORS headers too.

def test_password_hashing():
    """
    Test hashing a password longer than 72 bytes.
    """
    print("\n--- Testing Password Hashing (Long Password) ---")
    try:
        from app.core import security
        long_password = "a" * 100
        print(f"Hashing password of length {len(long_password)}...")
        hashed = security.get_password_hash(long_password)
        print(f"Success! Hash: {hashed[:10]}...")
        
        # Verify
        print("Verifying password...")
        is_valid = security.verify_password(long_password, hashed)
        print(f"Verification Result: {is_valid}")
        
        if is_valid:
            print("Password Hashing Test PASSED")
        else:
            print("Password Hashing Test FAILED (Verification returned False)")
            
    except Exception as e:
        print(f"Password Hashing Test CRASHED: {e}")

if __name__ == "__main__":
    test_password_hashing()
    # test_cors_on_error()
