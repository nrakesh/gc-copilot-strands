# GC2 Copilot - Strands

AI-powered GrandCentral (GC2) pipeline generator using AWS Strands Agents framework.

## 🎯 What is This?

GC2 Copilot analyzes natural language requests and automatically generates valid GC2 pipeline configurations (JSON DAGs) by:

1. Understanding user intent through an orchestrator agent
2. Delegating to specialized agents for each resource type (S3, routes, partners)
3. Validating configurations against Pydantic models
4. Deploying to Amazon Bedrock AgentCore for production use

## 📚 Documentation

- **[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)** - **START HERE!** Complete guide to agents, tools, and multi-agent patterns
- **[docs/MULTI_AGENT_WORKFLOW.md](./docs/MULTI_AGENT_WORKFLOW.md)** - Multi-agent pipeline generation workflow
- **[docs/S3_SPECIALIST.md](./docs/S3_SPECIALIST.md)** - S3 specialist agent guide
- **[terraform/DEPLOY.md](./terraform/DEPLOY.md)** - Terraform deployment guide for AWS
- **[terraform/README.md](./terraform/README.md)** - Infrastructure setup and deployment workflow

## 🚀 Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 3. Run Hello World

```bash
uv run python run_planner.py
```

Expected output:
```
Hello! I'm a GC2 pipeline planner assistant...
```

### 4. Deploy to AgentCore (Optional)

```bash
cd terraform
terraform init
terraform apply

# Store API key
aws secretsmanager put-secret-value \
  --secret-id $(terraform output -raw anthropic_secret_arn) \
  --secret-string "your-key"
```

## 📁 Project Structure

```
gc2-copilot-strands/
├── docs/                        # Documentation
│   ├── ARCHITECTURE.md          # Multi-agent architecture guide
│   ├── MULTI_AGENT_WORKFLOW.md  # Complete workflow documentation
│   └── S3_SPECIALIST.md         # S3 specialist guide
│
├── src/gc2_copilot_strands/
│   ├── agents/                  # Specialist agents
│   │   ├── planner.py           # ✅ Planner agent (with RAG)
│   │   ├── s3_specialist.py     # ✅ S3 specialist agent
│   │   └── route_specialist.py  # ✅ Route specialist agent
│   ├── tools/                   # Strands tools
│   │   └── rag_tools.py         # ✅ RAG context query tool
│   ├── models/                  # Pydantic models
│   │   ├── plan.py              # ResourceSpec, ConnectionSpec, PipelinePlan
│   │   ├── s3_resource.py       # S3Properties, S3Resource
│   │   └── route_resource.py    # RouteProperties, RouteResource
│   ├── vectorstore/             # ChromaDB integration
│   │   └── chroma_client.py     # Vector store client
│   └── config.py                # Configuration management
│
├── terraform/                   # Infrastructure as code
│   ├── main.tf                  # Infrastructure (ECR, IAM, logs)
│   ├── agentcore.tf             # AgentCore runtime deployment
│   ├── DEPLOY.md                # Deployment guide
│   └── README.md                # Infrastructure details
│
├── agent_deploy.py              # AgentCore deployment entrypoint
├── run_planner.py               # Local testing script
├── test_s3_specialist.py        # S3 specialist workflow test
├── test_complete_workflow.py    # Complete multi-agent test
├── verify_rag.py                # RAG integration verification
└── Dockerfile                   # ARM64 container for AgentCore
```

## 🏗️ Architecture

### Current Status: Multi-Agent Pipeline Generation ✅

```
┌────────────────────────────────────┐
│ Planner Agent (with RAG)           │
│ - Analyzes user intent             │
│ - Creates resource plan            │
│ - Queries ChromaDB                 │
└───────────┬────────────────────────┘
            │
    ┌───────┴────────┐
    │                │
    ▼                ▼
┌─────────┐    ┌──────────┐
│   S3    │    │  Route   │
│Specialist│   │Specialist│
└─────────┘    └──────────┘
```

### Target Architecture (from docs/ARCHITECTURE.md)

```
┌─────────────────────────────────────────────┐
│ Pipeline Orchestrator Agent                 │
│ - Analyzes user intent                      │
│ - Delegates to specialists                  │
│ - Assembles final DAG                       │
└───┬─────────────────────────────────────────┘
    │
    ├─► S3 Specialist Agent (wrapped tool)
    ├─► Route Specialist Agent (wrapped tool)
    └─► Partner Specialist Agent (wrapped tool)
```

**See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) for complete details on:**
- Agent with tools pattern
- Agent as tool (wrapped agents)
- MCP tools integration
- Multi-agent orchestration

## 🛠️ Development

### Run Tests

```bash
pytest
```

### Local Testing

```bash
# Test agent directly
uv run python run_planner.py

# Test with AgentCore wrapper (local server)
uv run python agent_deploy.py

# Test with curl
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Plan a pipeline to move CSV files from S3"}'
```

### Build Docker Image

```bash
docker buildx build --platform linux/arm64 -t gc2-planner:latest .
```

## 🎓 Learning Resources

### New to Strands?
1. Read [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) - Start with "Core Concepts"
2. Review the simple examples in each pattern section
3. Try the hello world agent: `run_planner.py`
4. Add your first tool (see docs/ARCHITECTURE.md Pattern 1)

### Ready to Deploy?
1. Review [terraform/DEPLOY.md](./terraform/DEPLOY.md)
2. Set up AWS credentials
3. Run `terraform apply`
4. Test your deployed agent

## 🗺️ Roadmap

### Phase 1: Foundation ✅
- [x] Set up Strands framework
- [x] Create hello world agent
- [x] Configure Terraform deployment
- [x] Write architecture documentation

### Phase 2: Specialist Agents ✅
- [x] Add RAG tools for vector store queries
- [x] Create S3 specialist agent with validation
- [x] Create Route specialist agent
- [ ] Create Partner specialist agents (optional)

### Phase 3: Orchestration 🎯
- [ ] Build orchestrator with wrapped specialists
- [ ] Implement resource planning logic
- [ ] Add DAG assembly and validation
- [ ] End-to-end pipeline generation

### Phase 4: Production 🚀
- [ ] Deploy to AgentCore Runtime
- [ ] Add observability and logging
- [ ] Performance optimization
- [ ] Error handling and retries

### Phase 5: Advanced (Optional) 🔌
- [ ] MCP servers for shared services
- [ ] Multi-region deployment
- [ ] CI/CD pipeline
- [ ] Monitoring and alerting

## 📖 Key Concepts

**Agent**: LLM + Tools + System Prompt + Reasoning Loop

**Tool**: Python function the LLM can call (decorated with `@tool`)

**Wrapped Agent**: An agent that acts as a tool for another agent (gets independent reasoning)

**MCP**: Model Context Protocol for accessing external tool servers

**See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) for detailed explanations and examples!**

## 🤝 Contributing

This is an internal project for GC2 pipeline generation. For questions or suggestions, reach out to the team.

## 📄 License

Internal use only.
