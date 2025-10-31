"""Debug script to investigate route generation issue."""

import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)

from src.gc2_copilot_strands.agents import generate_gc2_pipeline

print("\n" + "="*60)
print("DEBUGGING ROUTE GENERATION ISSUE")
print("="*60)

# Simple test case
pipeline = generate_gc2_pipeline(
    user_request="Move CSV files from S3 to another S3 bucket",
    output_file="tmp/debug-route.json"
)

print("\n" + "="*60)
print("RESULT")
print("="*60)

if pipeline and "resources" in pipeline:
    print(f"✅ Pipeline generated with {len(pipeline['resources'])} resources")
    for resource in pipeline['resources']:
        print(f"  - {resource.get('resourceName')} ({resource.get('type')})")
else:
    print("❌ Pipeline generation failed")
