# Multi-Agent Pipeline Generation Workflow

## Overview

The GC2 Copilot Strands system uses a **multi-agent architecture** to generate complete GrandCentral pipeline configurations. Each agent is a specialist responsible for a specific part of the pipeline, coordinated by an intelligent **Orchestrator Agent**.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│ USER REQUEST                                             │
│ "Move PGP encrypted CSV files from S3, decrypt them,    │
│  and save to another S3 bucket"                         │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ ORCHESTRATOR AGENT (Strands Agent)                       │
│ - Intelligent LLM-powered workflow coordination         │
│ - Decides which tools to call and when                  │
│ - Handles CREATE workflow (UPDATE coming soon)          │
│ - Multi-provider support (OpenAI/Anthropic)             │
│ - Retry logic for API resilience                        │
│                                                          │
│ Tools Available:                                         │
│   • plan_new_pipeline                                   │
│   • generate_s3_resource_config                         │
│   • generate_route_resource_config                      │
│   • assemble_pipeline_json                              │
│   • save_pipeline_to_file                               │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 1. PLANNING PHASE                                        │
│    Tool: plan_new_pipeline                              │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ PLANNER AGENT (with RAG)                                 │
│ - Queries ChromaDB for patterns, templates, schemas     │
│ - Creates high-level resource plan                      │
│ - Returns: PipelinePlan (ResourceSpecs + ConnectionSpecs)│
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 2. RESOURCE GENERATION PHASE                             │
│    Tools: generate_s3_resource_config (for each S3)     │
└────────────────────┬─────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│ S3 SPECIALIST    │    │ S3 SPECIALIST    │
│ (Source)         │    │ (Destination)    │
│ - Queries RAG    │    │ - Queries RAG    │
│ - Generates S3   │    │ - Generates S3   │
│   properties     │    │   properties     │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 3. ROUTE GENERATION PHASE                                │
│    Tools: generate_route_resource_config (per connection)│
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ ROUTE SPECIALIST                                         │
│ - Per ConnectionSpec from planner                        │
│ - Queries RAG for route schemas                         │
│ - Generates route properties with actions               │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 4. ASSEMBLY PHASE                                        │
│    Tool: assemble_pipeline_json                         │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ 5. SAVE PHASE                                            │
│    Tool: save_pipeline_to_file                          │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ COMPLETE GC2 PIPELINE JSON                               │
│ {                                                        │
│   "resources": [                                         │
│     { S3 source }, { S3 destination }, { route }        │
│   ]                                                      │
│ }                                                        │
└──────────────────────────────────────────────────────────┘
```

## Agents

### 1. Orchestrator Agent (`agents/orchestrator.py`) ⭐ NEW

**Purpose**: Intelligent coordination of the complete pipeline generation workflow

**Type**: **Strands Agent** with LLM-powered decision making

**Input**:
- User request (natural language)
- Optional output file path

**Tools Available**:
- `plan_new_pipeline` - Calls planner agent
- `generate_s3_resource_config` - Calls S3 specialist
- `generate_route_resource_config` - Calls route specialist
- `assemble_pipeline_json` - Combines all resources
- `save_pipeline_to_file` - Saves to disk

**Workflow**:
1. **Planning**: Use `plan_new_pipeline` to get resource plan
2. **Resource Generation**: For each S3 resource, use `generate_s3_resource_config`
3. **Route Generation**: For each connection, use `generate_route_resource_config`
4. **Assembly**: Use `assemble_pipeline_json` to combine resources
5. **Save**: Use `save_pipeline_to_file` to write to disk

**Key Features**:
- ✅ **Real Strands Agent** - Uses LLM to make intelligent decisions
- ✅ **Multi-Provider** - Supports OpenAI (gpt-4o) and Anthropic (Claude)
- ✅ **Retry Logic** - Automatic retry with exponential backoff on API errors
- ✅ **Tool-Based** - Modular architecture, easy to extend
- ✅ **Future-Proof** - Designed for UPDATE workflow (to be added)

**Example Usage**:
```python
from gc2_copilot_strands.agents import generate_gc2_pipeline

# Simple usage
pipeline = generate_gc2_pipeline(
    "Move CSV files from S3 to another S3 bucket"
)

# With output file
pipeline = generate_gc2_pipeline(
    "Transfer encrypted files from S3, decrypt them",
    output_file="tmp/my-pipeline.json"
)
```

**Future Capability** (not yet implemented):
```python
# UPDATE workflow (coming soon)
pipeline = generate_gc2_pipeline(
    "Add virus scanning before the destination",
    existing_file="tmp/my-pipeline.json",
    output_file="tmp/my-pipeline-v2.json"
)
```

### 2. Planner Agent (`agents/planner.py`)

**Purpose**: Analyze user intent and create resource plan

**Input**:
- User request (natural language)

**Tools**:
- `query_rag_context` - Queries 4 ChromaDB collections

**Output**:
- `PipelinePlan` with:
  - `pattern_type` - Description of the data flow
  - `resources` - List of `ResourceSpec` (id, name, type, role, description)
  - `connections` - List of `ConnectionSpec` (from, to, route_name, file_filter, actions)

**Example Output**:
```python
PipelinePlan(
    pattern_type="S3-to-S3 transfer with PGP decryption",
    resources=[
        ResourceSpec(id=0, name="source-encrypted-s3", type="aws-s3", role="source", ...),
        ResourceSpec(id=1, name="destination-decrypted-s3", type="aws-s3", role="destination", ...)
    ],
    connections=[
        ConnectionSpec(from_resource=0, to_resource=1, route_name="route-decrypt-csv",
                      file_filter=".+\\.pgp", actions=["pgp-decrypt"])
    ]
)
```

### 3. S3 Specialist Agent (`agents/s3_specialist.py`)

**Purpose**: Generate complete AWS S3 resource configurations

**Input**:
- `ResourceSpec` from planner
- User request (for context)
- Optional RAG context

**Process**:
1. Queries ChromaDB for S3 schemas and templates
2. Generates S3 properties using structured output
3. Validates against Pydantic `S3Properties` model

**Output**:
- `S3Resource` with validated properties

**Example Output**:
```json
{
  "resourceName": "source-encrypted-s3",
  "type": "aws-s3",
  "properties": {
    "awsRegion": "us-east-1",
    "s3Path": "source-bucket/encrypted/csv-files",
    "awsAccountName": "prod-account",
    "kmsKey": "alias/aws/s3",
    "isEnabled": true,
    "description": "Source S3 bucket containing PGP encrypted CSV files"
  }
}
```

### 4. Route Specialist Agent (`agents/route_specialist.py`)

**Purpose**: Generate complete route resource configurations

**Input**:
- `ConnectionSpec` from planner
- List of all `ResourceSpec` (to resolve refs)
- User request (for context)
- Optional RAG context

**Process**:
1. Resolves source/destination resource names from IDs
2. Queries ChromaDB for route schemas and templates
3. Generates route properties using structured output
4. Validates against Pydantic `RouteProperties` model

**Output**:
- `RouteResource` with validated properties

**Example Output**:
```json
{
  "resourceName": "route-decrypt-csv",
  "type": "route",
  "properties": {
    "description": "Move PGP encrypted files from source, decrypt, save to destination",
    "fileFilter": ".+\\.pgp",
    "isEnabled": true,
    "source": { "ref": "source-encrypted-s3" },
    "destination": { "ref": "destination-decrypted-s3" },
    "actions": ["pgp-decrypt"],
    "failureEmail": "gc2-team@troweprice.com",
    "successEmail": "gc2-team@troweprice.com",
    "disableFailureEmail": true,
    "disableSuccessEmail": false
  }
}
```

## Complete Workflow Example

### Input
```
User Request: "Move PGP encrypted CSV files from S3, decrypt them, and save to another S3 bucket"
```

### Step 1: Orchestrator Agent Starts
```
🤖 Orchestrator Agent starting workflow...
```

### Step 2: Planning Phase (via tool)
```
Tool: plan_new_pipeline

✅ Plan Created
   Pattern: S3-to-S3 transfer with PGP decryption
   Resources: 2
     - [0] data-input-s3 (aws-s3, source)
     - [1] data-output-s3 (aws-s3, destination)
   Connections: 1
     - route-csv-decrypt: .+\.pgp, actions: [pgp-decrypt]
```

### Step 3: Resource Generation Phase (via tools)
```
Tool: generate_s3_resource_config (data-input-s3)
Tool: generate_s3_resource_config (data-output-s3)

✅ Generated 2 S3 resources
   - data-input-s3: source-bucket/pgp-encrypted/csv
   - data-output-s3: output-bucket/decrypted-csv
```

### Step 4: Route Generation Phase (via tool)
```
Tool: generate_route_resource_config (route-csv-decrypt)

✅ Generated 1 route resource
   - route-csv-decrypt: data-input-s3 → data-output-s3
     Filter: .+\.pgp
     Actions: pgp-decrypt
```

### Step 5: Assembly Phase (via tool)
```
Tool: assemble_pipeline_json

✅ Assembled pipeline with 3 resources
```

### Step 6: Save Phase (via tool)
```
Tool: save_pipeline_to_file

✅ Successfully saved pipeline to tmp/pipeline-s3-decrypt.json
```

### Final Output
```json
{
  "resources": [
    {
      "resourceName": "data-input-s3",
      "type": "aws-s3",
      "properties": {
        "awsRegion": "us-east-1",
        "s3Path": "source-bucket/pgp-encrypted/csv",
        "awsAccountName": "prod-account",
        "kmsKey": "alias/aws/s3",
        "isEnabled": true,
        "description": "Source S3 bucket containing PGP encrypted CSV files"
      }
    },
    {
      "resourceName": "data-output-s3",
      "type": "aws-s3",
      "properties": {
        "awsRegion": "us-east-1",
        "s3Path": "output-bucket/decrypted-csv",
        "awsAccountName": "prod-account",
        "kmsKey": "alias/aws/s3",
        "isEnabled": true,
        "description": "Destination S3 bucket for decrypted CSV files"
      }
    },
    {
      "resourceName": "route-csv-decrypt",
      "type": "route",
      "properties": {
        "description": "Move PGP encrypted CSV files, decrypt them, and save to destination",
        "fileFilter": ".+\\.pgp",
        "isEnabled": true,
        "source": { "ref": "data-input-s3" },
        "destination": { "ref": "data-output-s3" },
        "actions": ["pgp-decrypt"],
        "failureEmail": "gc2-team@troweprice.com",
        "successEmail": "gc2-team@troweprice.com",
        "disableFailureEmail": true,
        "disableSuccessEmail": false
      }
    }
  ]
}
```

## Tools Architecture

### Orchestrator Tools (`tools/orchestrator_tools.py`)

**Purpose**: Tools that the Orchestrator Agent uses to coordinate the workflow

#### `plan_new_pipeline(user_request: str) -> str`
- Calls the Planner Agent
- Returns JSON string with resource plan
- Used in Planning Phase

#### `generate_s3_resource_config(resource_name, role, description, user_request) -> str`
- Calls S3 Specialist Agent
- Returns JSON string with S3 resource configuration
- Used in Resource Generation Phase

#### `generate_route_resource_config(route_name, source, dest, file_filter, actions, user_request) -> str`
- Calls Route Specialist Agent
- Returns JSON string with route resource configuration
- Used in Route Generation Phase

#### `assemble_pipeline_json(resources_json_list: List[str]) -> str`
- Combines all resource JSONs into complete pipeline
- Returns JSON string with complete pipeline
- Used in Assembly Phase

#### `save_pipeline_to_file(pipeline_json: str, output_file: str) -> str`
- Writes pipeline JSON to file
- Returns success/error message
- Used in Save Phase

### Future Tools (Placeholder - Not Yet Implemented)

```python
# For UPDATE workflow (coming soon)
load_existing_pipeline(file_path: str) -> str
plan_pipeline_update(existing_pipeline: str, user_request: str) -> str
merge_pipelines(existing_pipeline: str, new_resources: List[str]) -> str
```

## Configuration

### Multi-Provider Support

The system supports both OpenAI and Anthropic LLM providers:

**`.env` Configuration**:
```bash
# LLM Provider Selection
LLM_PROVIDER=openai  # or "anthropic"

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o  # or gpt-4o-mini

# Anthropic Configuration
ANTHROPIC_API_KEY=sk-ant-your-key-here
CLAUDE_MODEL=claude-sonnet-4-5-20250929

# Retry Configuration
MAX_RETRIES=3
INITIAL_RETRY_DELAY=2.0
MAX_RETRY_DELAY=60.0
```

### Retry Logic

All agents include automatic retry logic with exponential backoff:
- Handles API rate limits and overload errors
- Configurable max retries and delays
- Works with both OpenAI and Anthropic
- Automatic detection of transient vs permanent errors

## Key Benefits

### ✅ Intelligent Orchestration
- **Orchestrator Agent** makes decisions using LLM intelligence
- Can adapt to different request types
- Will support both CREATE and UPDATE workflows
- Flexible tool-based architecture

### ✅ Separation of Concerns
- **Orchestrator**: Coordinates workflow, decides which tools to use
- **Planner**: Focus on architecture and connections
- **S3 Specialist**: Focus on S3-specific properties and validation
- **Route Specialist**: Focus on routing logic and transformations

### ✅ RAG-Enhanced Context
- Each specialist queries relevant ChromaDB collections
- Planner gets patterns and templates
- Specialists get schema constraints and examples

### ✅ Type-Safe Validation
- Structured output with Pydantic models
- Automatic validation during generation
- Prevents invalid configurations

### ✅ Multi-Provider Support
- Works with OpenAI (gpt-4o, gpt-4o-mini)
- Works with Anthropic (Claude Sonnet, Opus)
- Easy to switch providers via configuration
- Cost optimization through model selection

### ✅ API Resilience
- Automatic retry on transient errors
- Exponential backoff for rate limits
- Handles overload gracefully
- Configurable retry parameters

### ✅ Testable Components
- Each agent can be tested independently
- Easy to debug specific parts of the pipeline
- Clear separation of responsibilities

### ✅ Extensible Architecture
- Easy to add new specialist agents (Partners, Schedules)
- Easy to add new tools for new workflows (UPDATE)
- Can upgrade individual agents without affecting others
- Follows single responsibility principle

## Testing

### Test Individual Agents
```bash
# Test planner
uv run python -m src.gc2_copilot_strands.agents.planner

# Test S3 specialist
uv run python -m src.gc2_copilot_strands.agents.s3_specialist

# Test route specialist
uv run python -m src.gc2_copilot_strands.agents.route_specialist
```

### Test Orchestrator
```bash
# Test orchestrator with built-in test cases
uv run python -m src.gc2_copilot_strands.agents.orchestrator

# Test complete workflow
uv run python test_complete_workflow.py
```

### Quick Test
```python
from src.gc2_copilot_strands.agents import generate_gc2_pipeline

pipeline = generate_gc2_pipeline(
    "Move CSV files from S3 to another S3 bucket",
    output_file="tmp/test-pipeline.json"
)

print(f"Generated {len(pipeline['resources'])} resources")
```

## Deployment Status

### ✅ Completed Phases

#### Phase 1: Planner Agent ✅
- [x] Create planner agent with RAG integration
- [x] Define PipelinePlan, ResourceSpec, ConnectionSpec models
- [x] Query ChromaDB for patterns, templates, schemas
- [x] Structured output with Pydantic validation

#### Phase 2: Specialist Agents ✅
- [x] Create S3 Specialist for aws-s3 resources
- [x] Create Route Specialist for route resources
- [x] RAG integration for each specialist
- [x] Pydantic model validation

#### Phase 3: Multi-Provider Support ✅
- [x] Support OpenAI (gpt-4o, gpt-4o-mini)
- [x] Support Anthropic (Claude Sonnet, Opus)
- [x] Configuration-driven provider selection
- [x] Retry logic with exponential backoff

#### Phase 4: Orchestrator Agent ✅
- [x] Create Orchestrator as real Strands Agent
- [x] Tool-based architecture for coordination
- [x] CREATE workflow implementation
- [x] Error handling and resilience
- [x] Simple public API (`generate_gc2_pipeline()`)

### 🚧 Future Phases

#### Phase 5: UPDATE Workflow 🔜
- [ ] Create UpdatePlanner Agent to analyze diffs
- [ ] Implement `load_existing_pipeline` tool
- [ ] Implement `plan_pipeline_update` tool
- [ ] Implement `merge_pipelines` tool
- [ ] Add UPDATE workflow to Orchestrator system prompt
- [ ] Support: `generate_gc2_pipeline(request, existing_file="...")`

#### Phase 6: Partner Specialist Agents 🔜
- [ ] Create ExternalPartnerSpecialist for external-partner resources
- [ ] Create InternalPartnerSpecialist for internal-partner resources
- [ ] Add partner tools to Orchestrator

#### Phase 7: Production Deployment 🔜
- [ ] Deploy to AgentCore Runtime
- [ ] Add observability and logging
- [ ] Performance optimization
- [ ] Load testing and optimization

## Files

### Models
- `models/plan.py` - ResourceSpec, ConnectionSpec, PipelinePlan
- `models/s3_resource.py` - S3Properties, S3Resource
- `models/route_resource.py` - RouteProperties, RouteResource

### Agents
- `agents/orchestrator.py` - **Orchestrator agent (Strands Agent)** ⭐
- `agents/planner.py` - Planner agent
- `agents/s3_specialist.py` - S3 specialist agent
- `agents/route_specialist.py` - Route specialist agent

### Tools
- `tools/orchestrator_tools.py` - Tools for orchestrator ⭐
- `tools/rag_tools.py` - RAG query tools

### Utilities
- `utils/retry.py` - Retry logic with exponential backoff ⭐
- `config.py` - Multi-provider configuration ⭐

### Tests
- `test_complete_workflow.py` - Complete orchestrated workflow
- `verify_rag.py` - RAG integration verification

## Agent Communication Pattern

This follows the **"Tool-Based Orchestration"** pattern from Strands:
1. **Orchestrator** is a Strands Agent with LLM intelligence
2. **Specialists** are independent agents (Planner, S3, Route)
3. **Tools** wrap specialist calls for the orchestrator
4. Orchestrator makes intelligent decisions about which tools to call
5. All agents return structured, validated outputs
6. No shared state between agents
7. Each agent is stateless and reusable

### Example Tool Flow

```
User → Orchestrator Agent
  ├─→ Tool: plan_new_pipeline
  │     └─→ Planner Agent → PipelinePlan
  │
  ├─→ Tool: generate_s3_resource_config (source)
  │     └─→ S3 Specialist → S3Resource
  │
  ├─→ Tool: generate_s3_resource_config (destination)
  │     └─→ S3 Specialist → S3Resource
  │
  ├─→ Tool: generate_route_resource_config
  │     └─→ Route Specialist → RouteResource
  │
  ├─→ Tool: assemble_pipeline_json
  │     └─→ Combined JSON
  │
  └─→ Tool: save_pipeline_to_file
        └─→ File saved → Complete Pipeline
```

## Performance & Cost Optimization

### Model Selection
- **Development/Testing**: Use `gpt-4o-mini` or `claude-sonnet` (lower cost)
- **Production**: Use `gpt-4o` or `claude-sonnet` (higher quality)

### Retry Configuration
- **High traffic**: Increase `MAX_RETRIES` and `MAX_RETRY_DELAY`
- **Fast failure**: Decrease `INITIAL_RETRY_DELAY`
- **Development**: Lower retries for faster feedback

### Cost per Pipeline (Approximate)
- OpenAI gpt-4o: ~$0.02 - $0.05 per pipeline
- OpenAI gpt-4o-mini: ~$0.002 - $0.005 per pipeline
- Anthropic Claude Sonnet: ~$0.01 - $0.03 per pipeline

*Actual costs depend on complexity of user request and number of resources*
