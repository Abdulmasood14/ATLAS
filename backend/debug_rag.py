
import sys
import asyncio
from pathlib import Path
import os

# Add backend directory to path so imports work
BACKEND_DIR = Path(__file__).parent
sys.path.insert(0, str(BACKEND_DIR))

# Mock environment variable for API URL if needed, though RAGService uses defaults
# os.environ["TEXT_LLM_ENDPOINT"] = "..." 

try:
    from services.rag_service import RAGService
    print("Successfully imported RAGService")
except ImportError as e:
    print(f"Failed to import RAGService: {e}")
    sys.exit(1)

async def main():
    print("Initializing RAGService...")
    try:
        rag = RAGService()
        print("RAGService initialized.")
    except Exception as e:
        print(f"Failed to initialize RAGService: {e}")
        import traceback
        traceback.print_exc()
        return

    print("Fetching companies...")
    try:
        companies = await rag.get_available_companies()
        print(f"Companies fetched: {companies}")
    except Exception as e:
        print(f"Failed to fetch companies: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
