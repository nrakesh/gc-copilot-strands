# GC2 Copilot - Strands

AI-powered GrandCentral (GC2) pipeline generator using AWS Strands multi-agent framework.

## 🎯 What is This?

GC2 Copilot transforms natural language requests into complete, validated GC2 pipeline configurations using intelligent multi-agent orchestration:

1. **Orchestrator Agent** coordinates the entire workflow using LLM-powered decision making
2. **Planner Agent** analyzes user intent and creates resource plans with RAG context
3. **Specialist Agents** (S3, Route) generate type-specific configurations with validation
4. **Tool-Based Architecture** enables modular, extensible workflows

## ✨ Latest Features

- ✅ **Complete Multi-Agent Orchestration** - Intelligent workflow coordination
- ✅ **Multi-Provider Support** - OpenAI (GPT-4o) and Anthropic (Claude Sonnet)
- ✅ **Comprehensive Logging** - Full visibility into agent and tool execution
- ✅ **API Resilience** - Automatic retry with exponential backoff
- ✅ **Clean JSON Output** - Null properties automatically excluded
- ✅ **Type-Safe Validation** - Pydantic models prevent invalid configurations

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install uv package manager if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your API key (OpenAI or Anthropic)
```

**`.env` Configuration:**
```bash
# LLM Provider (choose one)
LLM_PROVIDER=openai  # or "anthropic"

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o-mini  # or gpt-4o

# Anthropic Configuration (alternative)
ANTHROPIC_API_KEY=sk-ant-your-key-here
CLAUDE_MODEL=claude-sonnet-4-5-20250929

# Retry Configuration
MAX_RETRIES=3
INITIAL_RETRY_DELAY=2.0
MAX_RETRY_DELAY=60.0
```

### 3. Generate Your First Pipeline

```bash
# Using shell script (easiest)
./bin/gc2 "Move CSV files from S3 to another S3 bucket" -o tmp/my-pipeline.json

# Or using Python directly
uv run python main.py "Move CSV files from S3 to another S3 bucket" -o tmp/pipeline.json

# Or using Python API
uv run python -c "
from src.gc2_copilot_strands.agents import generate_gc2_pipeline
pipeline = generate_gc2_pipeline('Move CSV files from S3 to S3', 'tmp/test.json')
print(f'Generated {len(pipeline[\"resources\"])} resources')
"
```

### 4. Run Demo

```bash
# See the system in action with example pipelines
./bin/gc2-demo
```

## 📁 Project Structure

```
gc2-copilot-strands/
├── bin/                        # Shell scripts
│   ├── gc2                     # Main CLI command
│   ├── gc2-demo                # Run demo examples
│   └── gc2-test                # Run tests
│
├── src/gc2_copilot_strands/
│   ├── agents/                 # Multi-agent system
│   │   ├── orchestrator.py     # ⭐ Orchestrator agent (coordinator)
│   │   ├── planner.py          # Planner agent (with RAG)
│   │   ├── s3_specialist.py    # S3 resource specialist
│   │   └── route_specialist.py # Route resource specialist
│   │
│   ├── tools/                  # Agent tools
│   │   ├── orchestrator_tools.py  # ⭐ Orchestrator coordination tools
│   │   └── rag_tools.py        # RAG context query tools
│   │
│   ├── models/                 # Pydantic data models
│   │   ├── plan.py             # ResourceSpec, ConnectionSpec, PipelinePlan
│   │   ├── s3_resource.py      # S3Properties, S3Resource
│   │   └── route_resource.py   # RouteProperties, RouteResource
│   │
│   ├── utils/                  # Utilities
│   │   ├── logger.py           # ⭐ Centralized logging (NEW)
│   │   └── retry.py            # Retry logic with exponential backoff
│   │
│   ├── vectorstore/            # ChromaDB integration
│   │   └── chroma_client.py    # Vector store client for RAG
│   │
│   └── config.py               # Multi-provider configuration
│
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md         # Multi-agent architecture guide
│   ├── MULTI_AGENT_WORKFLOW.md # Complete workflow documentation
│   └── S3_SPECIALIST.md        # S3 specialist guide
│
├── scripts/                    # Utility scripts
│   ├── debug_route_issue.py    # Debug route generation
│   ├── run_planner.py          # Test planner agent
│   └── test_complete_workflow.py  # End-to-end tests
│
├── terraform/                  # Infrastructure as code
│   ├── main.tf                 # Infrastructure (ECR, IAM, logs)
│   ├── agentcore.tf            # AgentCore runtime deployment
│   └── DEPLOY.md               # Deployment guide
│
└── main.py                     # CLI entry point
```

## 🏗️ Architecture

### Current Implementation: Complete Multi-Agent Orchestration ✅

```
┌─────────────────────────────────────────────────────────────┐
│ USER REQUEST (Natural Language)                             │
│ "Move PGP encrypted CSV files from S3, decrypt them"        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR AGENT (Strands Agent) ⭐                        │
│ - LLM-powered intelligent coordination                      │
│ - Decides which tools to call and when                      │
│ - Multi-provider support (OpenAI/Anthropic)                 │
│ - Automatic retry logic                                     │
│ - Comprehensive logging                                     │
│                                                             │
│ Tools Available:                                            │
│   • plan_new_pipeline                                       │
│   • generate_s3_resource_config                             │
│   • generate_route_resource_config                          │
│   • assemble_pipeline_json                                  │
│   • save_pipeline_to_file                                   │
└────────┬────────────────────────────────────────────────────┘
         │
         ├──► PHASE 1: Planning
         │    └──► Planner Agent (with RAG)
         │         - Queries ChromaDB for patterns
         │         - Creates ResourceSpecs & ConnectionSpecs
         │         - Returns: PipelinePlan
         │
         ├──► PHASE 2: Resource Generation
         │    ├──► S3 Specialist (source)
         │    │    - Queries RAG for S3 schemas
         │    │    - Generates S3Properties
         │    │    - Validates with Pydantic
         │    │
         │    └──► S3 Specialist (destination)
         │         - Same process for destination
         │
         ├──► PHASE 3: Route Generation
         │    └──► Route Specialist
         │         - Queries RAG for route schemas
         │         - Generates RouteProperties
         │         - Handles actions (pgp-decrypt, etc.)
         │         - Validates with Pydantic
         │
         ├──► PHASE 4: Assembly
         │    └──► Combines all resources into pipeline JSON
         │
         └──► PHASE 5: Save
              └──► Writes to output file

┌─────────────────────────────────────────────────────────────┐
│ COMPLETE GC2 PIPELINE JSON ✅                                │
│ {                                                           │
│   "resources": [                                            │
│     { S3 source }, { S3 destination }, { route }           │
│   ]                                                         │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
```

**For detailed architecture patterns, see [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)**

## 📊 Multi-Agent Workflow

### Example: Simple S3-to-S3 Transfer

**Input:**
```
"Move CSV files from S3 to another S3 bucket"
```

**Orchestrator Workflow:**

1. **Planning Phase** → Calls `plan_new_pipeline` tool
   - Planner Agent analyzes request with RAG context
   - Returns: 2 S3 resources + 1 route connection

2. **Resource Generation** → Calls `generate_s3_resource_config` twice
   - S3 Specialist generates source config
   - S3 Specialist generates destination config

3. **Route Generation** → Calls `generate_route_resource_config`
   - Route Specialist generates route with file filter `.+\.csv`
   - No actions needed (simple transfer)

4. **Assembly** → Calls `assemble_pipeline_json`
   - Combines 3 resources into complete pipeline

5. **Save** → Calls `save_pipeline_to_file`
   - Writes to `tmp/pipeline.json`

**Output:**
```json
{
  "resources": [
    {
      "resourceName": "data-source-s3",
      "type": "aws-s3",
      "properties": {
        "awsRegion": "us-east-1",
        "s3Path": "source-bucket/input/csv",
        "awsAccountName": "prod-account",
        "kmsKey": "alias/aws/s3",
        "isEnabled": true,
        "description": "Source S3 bucket for CSV files"
      }
    },
    {
      "resourceName": "data-destination-s3",
      "type": "aws-s3",
      "properties": {
        "awsRegion": "us-east-1",
        "s3Path": "output-bucket/processed/csv",
        "awsAccountName": "prod-account",
        "kmsKey": "alias/aws/s3",
        "isEnabled": true,
        "description": "Destination S3 bucket for CSV files"
      }
    },
    {
      "resourceName": "route-csv",
      "type": "route",
      "properties": {
        "description": "Route CSV files from source to destination",
        "fileFilter": ".+\\.csv",
        "isEnabled": true,
        "source": { "ref": "data-source-s3" },
        "destination": { "ref": "data-destination-s3" },
        "failureEmail": "gc2-team@troweprice.com",
        "successEmail": "gc2-team@troweprice.com",
        "disableFailureEmail": true,
        "disableSuccessEmail": false
      }
    }
  ]
}
```

**Note:** `actions` field is excluded when null (clean JSON output ✨)

**For complete workflow details, see [docs/MULTI_AGENT_WORKFLOW.md](./docs/MULTI_AGENT_WORKFLOW.md)**

## 🛠️ Key Features

### ✅ Intelligent Orchestration
- **LLM-Powered Decision Making**: Orchestrator uses LLM to intelligently decide which tools to call
- **Adaptive Workflow**: Can handle various request types and complexities
- **Tool-Based Architecture**: Modular, extensible design for adding new capabilities

### ✅ Multi-Provider Support
- **OpenAI**: gpt-4o (production), gpt-4o-mini (development/testing)
- **Anthropic**: Claude Sonnet, Claude Opus
- **Easy Switching**: Configure via `.env` file
- **Cost Optimization**: Choose model based on quality/cost needs

### ✅ API Resilience
- **Automatic Retry**: Exponential backoff on transient errors
- **Rate Limit Handling**: Graceful handling of API rate limits
- **Configurable**: Adjust retry parameters via `.env`
- **Error Detection**: Distinguishes transient vs permanent errors

### ✅ Comprehensive Logging
- **Tool Call Tracking**: See every tool invocation with arguments
- **Agent Execution**: Track agent reasoning and decision-making
- **Debug-Friendly**: Detailed logs for troubleshooting
- **Structured Format**: Clear, parseable log output

### ✅ RAG-Enhanced Generation
- **ChromaDB Vector Store**: 4 collections (schemas, templates, connectivity, guide)
- **Context-Aware**: Each agent queries relevant context
- **Schema Validation**: Generates configs matching GC2 requirements
- **Template Examples**: Learns from existing pipeline patterns

### ✅ Type-Safe Validation
- **Pydantic Models**: Strict type checking for all resources
- **Structured Output**: LLM generates validated JSON directly
- **Error Prevention**: Invalid configs caught before assembly
- **Clean JSON**: Null properties automatically excluded

## 🧪 Testing

### Quick Tests

```bash
# Run demo with examples
./bin/gc2-demo

# Test complete workflow
./bin/gc2-test

# Generate custom pipeline
./bin/gc2 "Your request here" -o tmp/test-pipeline.json
```

### Test Individual Components

```bash
# Test planner agent
uv run python -m src.gc2_copilot_strands.agents.planner

# Test S3 specialist
uv run python -m src.gc2_copilot_strands.agents.s3_specialist

# Test route specialist
uv run python -m src.gc2_copilot_strands.agents.route_specialist

# Test orchestrator
uv run python -m src.gc2_copilot_strands.agents.orchestrator
```

### Debug Route Generation

```bash
# Run debug script with detailed logging
uv run python scripts/debug_route_issue.py
```

## 📚 Documentation

### Core Documentation
- **[QUICKSTART.md](./QUICKSTART.md)** - Get started in 5 minutes
- **[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)** - Multi-agent patterns and best practices
- **[docs/MULTI_AGENT_WORKFLOW.md](./docs/MULTI_AGENT_WORKFLOW.md)** - Complete workflow guide
- **[docs/S3_SPECIALIST.md](./docs/S3_SPECIALIST.md)** - S3 specialist deep dive

### Deployment
- **[terraform/DEPLOY.md](./terraform/DEPLOY.md)** - Deploy to AWS AgentCore
- **[terraform/README.md](./terraform/README.md)** - Infrastructure overview

## 🗺️ Roadmap

### Phase 1: Foundation ✅ COMPLETE
- [x] Set up Strands framework
- [x] Create planner agent with RAG
- [x] Define Pydantic models
- [x] Configure ChromaDB vector store

### Phase 2: Specialist Agents ✅ COMPLETE
- [x] S3 Specialist with structured output
- [x] Route Specialist with action detection
- [x] Pydantic validation for all resources
- [x] RAG integration for each specialist

### Phase 3: Orchestration ✅ COMPLETE
- [x] Build orchestrator as real Strands Agent
- [x] Implement tool-based workflow
- [x] Multi-provider support (OpenAI + Anthropic)
- [x] Retry logic with exponential backoff
- [x] Comprehensive logging system
- [x] Clean JSON output (exclude null properties)
- [x] End-to-end pipeline generation

### Phase 4: Production Readiness 🎯 IN PROGRESS
- [ ] Partner specialist agents (external, internal)
- [ ] Deploy to AWS AgentCore Runtime
- [ ] Add observability and metrics
- [ ] Performance optimization
- [ ] Load testing

### Phase 5: Advanced Features 🔜 PLANNED
- [ ] UPDATE workflow (modify existing pipelines)
- [ ] MCP servers for shared services
- [ ] Multi-region deployment
- [ ] CI/CD pipeline
- [ ] Advanced error recovery

## 💡 Example Use Cases

### Simple Transfer
```bash
./bin/gc2 "Move CSV files from S3 to another S3 bucket" -o pipeline.json
```

### With Decryption
```bash
./bin/gc2 "Transfer PGP encrypted files, decrypt them" -o decrypt-pipeline.json
```

### Multiple File Types
```bash
./bin/gc2 "Copy CSV and TXT files from source to destination S3" -o multi-type.json
```

### With Actions
```bash
./bin/gc2 "Move JSON files from S3, zip them, send to destination" -o zip-pipeline.json
```

## ⚙️ Configuration

### LLM Provider Selection

Choose your LLM provider in `.env`:

```bash
# For OpenAI (recommended for cost)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-your-key
OPENAI_MODEL=gpt-4o-mini  # or gpt-4o for production

# For Anthropic (recommended for quality)
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
CLAUDE_MODEL=claude-sonnet-4-5-20250929
```

### Retry Configuration

Adjust API retry behavior:

```bash
MAX_RETRIES=3              # Number of retries
INITIAL_RETRY_DELAY=2.0    # First retry delay (seconds)
MAX_RETRY_DELAY=60.0       # Max delay between retries
```

## 💰 Cost Estimates

Approximate cost per pipeline generation:

- **OpenAI gpt-4o-mini**: $0.002 - $0.005 (recommended for development)
- **OpenAI gpt-4o**: $0.02 - $0.05 (recommended for production)
- **Anthropic Claude Sonnet**: $0.01 - $0.03

*Actual costs vary based on request complexity and number of resources*

## 🤝 Contributing

This is an internal project for GC2 pipeline generation. For questions or suggestions, reach out to the team.

## 📄 License

Internal use only.
