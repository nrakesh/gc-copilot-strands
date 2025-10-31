"""Test the complete workflow: Planner → S3 Specialist."""

from src.gc2_copilot_strands.agents.planner import plan_pipeline
from src.gc2_copilot_strands.agents.s3_specialist import generate_s3_resource
import json

print("=" * 60)
print("Testing Complete Workflow: Planner → S3 Specialist")
print("=" * 60)

# Step 1: Get resource plan from planner
user_request = "Move CSV files from an S3 bucket to another S3 bucket"
print(f"\nUser Request: {user_request}")
print("\n🤖 Step 1: Planning resources with planner agent...")

plan = plan_pipeline(user_request)

if not plan:
    print("❌ Planning failed")
    exit(1)

print(f"\n✅ Plan created: {plan.pattern_type}")
print(f"   Resources: {len(plan.resources)}")

# Step 2: Generate S3 configurations for each S3 resource
print("\n🤖 Step 2: Generating S3 configurations with specialist agent...")

s3_resources = []
for resource in plan.resources:
    if resource.type == "aws-s3":
        print(f"\n   Generating config for: {resource.name} ({resource.role})")
        s3_resource = generate_s3_resource(resource, user_request)
        s3_resources.append(s3_resource)
        print(f"   ✅ Generated: {s3_resource.properties.s3Path}")

# Step 3: Display complete configurations
print("\n" + "=" * 60)
print("Complete S3 Resource Configurations")
print("=" * 60)

for s3_res in s3_resources:
    print(f"\n{s3_res.resourceName}:")
    print(json.dumps(s3_res.model_dump(), indent=2))

print("\n" + "=" * 60)
print(f"✅ Successfully generated {len(s3_resources)} S3 resource configurations!")
print("=" * 60)

# Show what's left to do
route_count = sum(1 for r in plan.resources if r.type == "route")
print(f"\nNext steps:")
print(f"  - Create Route Specialist Agent (need to generate {route_count} routes)")
print(f"  - Create Orchestrator to assemble complete DAG")
print(f"  - Add validation and export to JSON")
