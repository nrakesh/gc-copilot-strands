# S3 Specialist Agent

## Overview

The S3 Specialist Agent is a specialized Strands agent that generates complete AWS S3 resource configurations based on high-level specifications from the planner agent.

## Architecture

```
┌─────────────────────────────────────────────┐
│ Planner Agent                               │
│ - Analyzes user request                     │
│ - Creates ResourceSpec (name, type, role)   │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│ S3 Specialist Agent                         │
│ - Queries RAG for S3 schemas & templates   │
│ - Generates complete S3 properties          │
│ - Validates against Pydantic models         │
└───────────────┬─────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│ S3Resource Output                           │
│ - resourceName                              │
│ - type: "aws-s3"                            │
│ - properties:                               │
│   - awsRegion                               │
│   - s3Path                                  │
│   - awsAccountName                          │
│   - kmsKey                                  │
│   - isEnabled                               │
│   - description                             │
└─────────────────────────────────────────────┘
```

## Files Created

### 1. Models (`src/gc2_copilot_strands/models/s3_resource.py`)

**S3Properties**
- Pydantic model with all required S3 properties
- Enforces constraints (max lengths, patterns, allowed values)
- Prevents extra fields

**S3Resource**
- Complete S3 resource structure
- Combines resourceName, type, and properties
- Ready for JSON export

### 2. Agent (`src/gc2_copilot_strands/agents/s3_specialist.py`)

**Functions:**
- `create_s3_specialist()` - Creates the agent instance
- `generate_s3_resource()` - Main generation function
- `test_s3_specialist()` - Standalone testing

**Agent Configuration:**
- Uses `structured_output_model=S3Properties`
- Automatically validates output against Pydantic schema
- Returns validated S3Properties object

## Generation Rules

The S3 specialist follows these critical rules:

### Region
- Default: `us-east-1`
- Supported: us-east-1, us-east-2, us-west-1, us-west-2, eu-west-2, eu-west-1, eu-central-1

### S3 Path (max 319 chars)
- **Source resources**: `source-bucket/input/csv`
- **Destination resources**: `destination-bucket/processed/csv`
- Logical folder structure based on file types

### AWS Account Name (max 100 chars)
- Descriptive names: `prod-data-account`, `dev-analytics`
- Default: `prod-account`

### KMS Key (max 50 chars)
- **ALWAYS use alias format**: `alias/aws/s3`
- **NEVER use ARNs** (exceed 50 char limit)

### isEnabled
- Always: `true`

### Description (max 100 chars)
- Clear description of role and purpose
- Mentions source/destination role

## RAG Integration

The specialist queries ChromaDB for:

1. **Schema Context** (`gc2_schemas` collection)
   - S3 property constraints
   - Required vs optional fields
   - Validation rules

2. **Template Examples** (`gc2_templates` collection)
   - Real S3 configurations
   - Source/destination patterns
   - Path structures

## Usage Example

```python
from src.gc2_copilot_strands.agents.planner import plan_pipeline
from src.gc2_copilot_strands.agents.s3_specialist import generate_s3_resource

# Step 1: Get plan from planner
user_request = "Move CSV files from S3 to another S3 bucket"
plan = plan_pipeline(user_request)

# Step 2: Generate S3 configs for each S3 resource
for resource in plan.resources:
    if resource.type == "aws-s3":
        s3_resource = generate_s3_resource(resource, user_request)
        print(s3_resource.model_dump_json(indent=2))
```

## Test Results

✅ **Standalone Test**
```bash
uv run python -m src.gc2_copilot_strands.agents.s3_specialist
```
- Generates valid S3 configuration
- All Pydantic validations pass
- Proper KMS alias format
- Logical S3 paths

✅ **Integrated Test**
```bash
uv run python test_s3_specialist.py
```
- Planner creates resource plan
- S3 specialist generates 2 S3 resources
- Source: `source-bucket/input/csv`
- Destination: `destination-bucket/processed/csv`

## Output Example

```json
{
  "resourceName": "source-s3-bucket",
  "type": "aws-s3",
  "properties": {
    "awsRegion": "us-east-1",
    "s3Path": "source-bucket/input/csv",
    "awsAccountName": "prod-account",
    "kmsKey": "alias/aws/s3",
    "isEnabled": true,
    "description": "Source S3 bucket containing CSV files to be transferred"
  }
}
```

## Next Steps

1. **Route Specialist Agent** - Generate route configurations
2. **Partner Specialist Agents** - Generate partner configurations
3. **Orchestrator Agent** - Coordinate all specialists and assemble final DAG
4. **Validation** - Validate complete DAG against JSON schema
5. **Export** - Save to output directory

## Key Benefits

✅ **Separation of Concerns** - Planning vs generation
✅ **Structured Output** - Type-safe Pydantic validation
✅ **RAG-Enhanced** - Uses real schemas and examples
✅ **Testable** - Can test specialist independently
✅ **Reusable** - Can be used for pipeline updates too
