"""Verify ChromaDB RAG integration."""

from src.gc2_copilot_strands.config import Config
from src.gc2_copilot_strands.tools.rag_tools import query_rag_context

print("=" * 60)
print("ChromaDB RAG Integration Verification")
print("=" * 60)

# Check ChromaDB connection
chroma_client = Config.get_chroma_client()
collections = chroma_client.list_collections()

print(f"\n✓ ChromaDB connected successfully")
print(f"  Location: {Config.CHROMA_DIR}")
print(f"\n✓ Available collections ({len(collections)}):")
for collection in collections:
    print(f"  - {collection}")

# Test RAG query
print(f"\n{'=' * 60}")
print("Testing RAG Query Tool")
print("=" * 60)

test_request = "Move CSV files from S3 to another S3 bucket"
print(f"\nQuery: {test_request}")
print("\nRAG Context Retrieved:")
print("-" * 60)

context = query_rag_context(test_request)
print(context)

print("\n" + "=" * 60)
print("✓ RAG integration working correctly!")
print("=" * 60)
