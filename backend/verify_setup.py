import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def verify_imports():
    print("Verifying backend imports...")
    try:
        from app.main import app
        from app.config import settings
        from app.models.document import DocumentMetadata
        from app.ingestion.pipeline import run_full_ingestion
        from app.retrieval.hybrid import hybrid_retrieve
        from app.synthesis.generator import generate_synthesis
        print("✅ Backend imports successful!")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_imports()
