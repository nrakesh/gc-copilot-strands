"""Test the complete multi-agent workflow using the Orchestrator Agent."""

import sys
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.gc2_copilot_strands.agents import generate_gc2_pipeline
import json

# Test Case 1: S3 to S3 with PGP decryption
print("\n" + "=" * 60)
print("TEST CASE 1: S3 → S3 with PGP Decryption")
print("=" * 60)

pipeline1 = generate_gc2_pipeline(
    user_request="Move PGP encrypted CSV files from S3, decrypt them, and save to another S3 bucket",
    output_file="tmp/pipeline-s3-decrypt.json"
)

print("\n📄 Pipeline JSON Preview:")
print(json.dumps(pipeline1, indent=2)[:1000] + "...")


# Test Case 2: Simple S3 to S3 transfer
print("\n\n" + "=" * 60)
print("TEST CASE 2: Simple S3 → S3 Transfer")
print("=" * 60)

pipeline2 = generate_gc2_pipeline(
    user_request="Move CSV files from S3 to another S3 bucket",
    output_file="tmp/pipeline-s3-to-s3.json"
)

print("\n📄 Pipeline JSON Preview:")
print(json.dumps(pipeline2, indent=2)[:1000] + "...")


print("\n\n" + "=" * 60)
print("ALL TESTS COMPLETE")
print("=" * 60)
print(f"\n✅ Test Case 1: {len(pipeline1['resources'])} resources generated")
print(f"✅ Test Case 2: {len(pipeline2['resources'])} resources generated")
print("\nGenerated files:")
print("  - tmp/pipeline-s3-decrypt.json")
print("  - tmp/pipeline-s3-to-s3.json")
