# Strands Multi-Agent Architecture Guide

A comprehensive guide to understanding agents, tools, and multi-agent patterns in AWS Strands.

---

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Pattern 1: Agent with Tools](#pattern-1-agent-with-tools)
3. [Pattern 2: Agent as Tool](#pattern-2-agent-as-tool)
4. [Pattern 3: MCP Tools](#pattern-3-mcp-tools)
5. [Pattern 4: Combining Everything](#pattern-4-combining-everything)
6. [GC2 Copilot Architecture](#gc2-copilot-architecture)
7. [Implementation Guide](#implementation-guide)

---

## Core Concepts

### What is an Agent?

An **Agent** = LLM + Tools + System Prompt + Reasoning Loop

```python
agent = Agent(
    model=llm_model,           # The brain (Claude, GPT, etc.)
    tools=[tool1, tool2],      # Actions it can take
    system_prompt="You are..." # Instructions & personality
)

response = agent("User request")  # Agent thinks → uses tools → responds
```

### What is a Tool?

A **Tool** is a Python function that the agent framework can execute on behalf of the LLM:

```python
@tool
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    # Your code here
    return f"Weather in {city}: Sunny, 72°F"
```

**Key Point**: The LLM sees the function signature and docstring, then decides when to REQUEST tool use. The Strands framework intercepts this request, executes the Python function, and sends the result back to the LLM.

### How Tool Execution Works

```
1. LLM responds with tool use request:
   {"type": "tool_use", "name": "get_weather", "args": {"city": "NYC"}}

2. Strands framework intercepts the request

3. Strands executes: result = get_weather("NYC")  # In YOUR container

4. Strands sends result back to LLM:
   {"type": "tool_result", "content": "Weather in NYC: Sunny, 72°F"}

5. LLM continues reasoning with the result
```

**Important**: The LLM never directly executes code. It only requests tool use through structured output, and the framework handles execution.

### What Runs Where?

```
┌────────────────────────────────────────────────────┐
│ YOUR Container (AgentCore)                         │
│                                                    │
│  ┌──────────────────────────────────────┐          │
│  │ Strands Framework                    │          │
│  │                                      │          │
│  │  1. Sends message to LLM ──────────────────┐    │
│  │  3. Intercepts tool_use response     │     │    │
│  │  4. Executes Python function:        │     │    │
│  │     result = my_tool()               │     │    │
│  │  5. Sends result back to LLM ─────────────┐│    │
│  │                                      │    ││    │
│  │  @tool functions (YOUR CODE)         │    ││    │
│  └──────────────────────────────────────┘    ││    │
│                                              ││    │
└──────────────────────────────────────────────┼┼────┘
                                               ││
                                               ││
                                               ▼│
                                    ┌────────────▼──────┐
                                    │ Anthropic API     │
                                    │ (Claude LLM)      │
                                    │                   │
                                    │ 2. Returns:       │
                                    │    "use tool X"   │
                                    │ 6. Continues      │
                                    │    reasoning      │
                                    └───────────────────┘
```

**Key Insight**:
- **LLM** (at Anthropic): Thinks and requests tool use
- **Strands Framework** (in your container): Executes tools
- **@tool Functions** (in your container): Your Python code

---

## Pattern 1: Agent with Tools

### Concept

The agent has access to tools and decides when to use them.

### Simple Example

```python
from strands import Agent, tool
from strands.models.anthropic import AnthropicModel

# Define tools
@tool
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

@tool
def multiply_numbers(a: int, b: int) -> int:
    """Multiply two numbers together."""
    return a * b

# Create agent with tools
model = AnthropicModel(model_id="claude-sonnet-4-5-20250929", max_tokens=1024)
calculator = Agent(
    model=model,
    tools=[add_numbers, multiply_numbers],
    system_prompt="You are a helpful calculator assistant."
)

# Use the agent
response = calculator("What is (5 + 3) * 2?")
```

### What Happens

```
1. User: "What is (5 + 3) * 2?"

2. LLM thinks: "I need to add 5 and 3 first"
   Calls: add_numbers(5, 3)
   Result: 8

3. LLM thinks: "Now multiply 8 by 2"
   Calls: multiply_numbers(8, 2)
   Result: 16

4. LLM responds: "The answer is 16"
```

### GC2 Example: Schema Query Tools

```python
from strands import Agent, tool

@tool
def query_schema(resource_type: str) -> str:
    """Get JSON schema for a GC2 resource type."""
    return chroma_client.query_collection(
        collection_name="gc2_schemas",
        query_text=f"{resource_type} schema",
        n_results=2
    )

@tool
def query_templates(resource_type: str) -> str:
    """Get example templates for a resource type."""
    return chroma_client.query_collection(
        collection_name="gc2_templates",
        query_text=f"{resource_type} examples",
        n_results=3
    )

@tool
def validate_config(config: dict, resource_type: str) -> dict:
    """Validate a resource configuration."""
    model_class = RESOURCE_MODEL_MAP[resource_type]
    try:
        model_class.model_validate(config)
        return {"valid": True}
    except ValidationError as e:
        return {"valid": False, "errors": str(e)}

# Agent uses these tools
planner = Agent(
    model=model,
    tools=[query_schema, query_templates, validate_config],
    system_prompt="You create GC2 pipeline configurations."
)

response = planner("Create an S3 source configuration")
# LLM will:
# 1. Call query_schema("aws-s3")
# 2. Call query_templates("aws-s3")
# 3. Generate config
# 4. Call validate_config(config, "aws-s3")
# 5. Fix if invalid, retry
```

---

## Pattern 2: Agent as Tool

### Concept

Wrap an entire agent as a tool for another agent to use. The wrapped agent gets its own independent LLM reasoning session.

### Why Do This?

**Without wrapping (orchestrator does everything):**
```python
orchestrator("Create S3 config")
  → query_schema()
  → generate config
  → validate config
  → fix errors
  → validate again
  → ... orchestrator managing all the complexity
```

**With wrapping (specialist handles it):**
```python
orchestrator("Create S3 config")
  → create_s3_resource()
    [S3 agent handles everything internally with its own LLM session]
  → Returns: valid config

# Orchestrator doesn't see the complexity!
```

### Simple Example

```python
from strands import Agent, tool

# ============================================
# Specialist Agent (has its own tools)
# ============================================
@tool
def get_math_rules() -> str:
    """Get mathematical rules."""
    return "Follow order of operations: PEMDAS"

math_specialist = Agent(
    model=model,
    tools=[get_math_rules],
    system_prompt="""You are a math expert.
    Always get the rules first, then solve step-by-step."""
)

# ============================================
# Wrap specialist as a tool
# ============================================
@tool
def solve_math_problem(problem: str) -> str:
    """Solve a math problem using expert mathematician.

    Args:
        problem: The math problem to solve

    Returns:
        Detailed solution
    """
    # Math specialist does independent reasoning here
    return math_specialist(f"Solve: {problem}")

# ============================================
# Orchestrator uses wrapped agent
# ============================================
orchestrator = Agent(
    model=model,
    tools=[solve_math_problem],  # Wrapped agent as tool
    system_prompt="You help users by delegating to specialists."
)

response = orchestrator("What is (10 + 5) * 3 - 8?")
# Orchestrator delegates to math specialist
# Math specialist:
#   1. Calls get_math_rules()
#   2. Solves step by step
#   3. Returns answer
# Orchestrator receives answer and responds to user
```

### Execution Flow

```
┌─────────────────────────────────────────┐
│ Orchestrator Agent                      │
│ "User needs math help"                  │
│ → Calls: solve_math_problem()          │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ Math Specialist Agent                   │
│ (Independent LLM session)               │
│                                         │
│ 1. "I need rules first"                 │
│    → Calls: get_math_rules()           │
│    ← Returns: "PEMDAS"                 │
│                                         │
│ 2. "Now I solve: (10+5)*3-8"           │
│    → Calculates: 15*3-8 = 45-8 = 37    │
│                                         │
│ 3. Returns: "37"                        │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ Orchestrator Agent                      │
│ Receives: "37"                          │
│ Responds: "The answer is 37"           │
└─────────────────────────────────────────┘
```

### GC2 Example: S3 Specialist Agent

```python
from strands import Agent, tool

# ============================================
# S3 Specialist Agent
# ============================================
@tool
def get_s3_schema() -> str:
    """Get S3 schema requirements."""
    return chroma_client.query_collection(
        collection_name="gc2_schemas",
        query_text="aws-s3 properties constraints",
        n_results=3
    )

@tool
def get_s3_examples() -> str:
    """Get S3 configuration examples."""
    return chroma_client.query_collection(
        collection_name="gc2_templates",
        query_text="aws-s3 configurations",
        n_results=2
    )

@tool
def validate_s3(config: dict) -> dict:
    """Validate S3 configuration."""
    from gc2_copilot_strands.models.dag import AwsS3PropertiesMinimal
    try:
        AwsS3PropertiesMinimal.model_validate(config)
        return {"valid": True}
    except Exception as e:
        return {"valid": False, "error": str(e)}

# S3 specialist with its own brain and tools
s3_specialist = Agent(
    model=model,
    tools=[get_s3_schema, get_s3_examples, validate_s3],
    system_prompt="""You are an AWS S3 configuration expert.

    Your process:
    1. Get schema requirements using get_s3_schema()
    2. Review examples using get_s3_examples()
    3. Generate a configuration following constraints:
       - s3Path: max 319 chars
       - kmsKey: max 50 chars (use alias format)
       - description: max 100 chars
       - awsRegion: use "us-east-1"
       - isEnabled: always true
    4. Validate using validate_s3()
    5. If invalid, fix and retry
    6. Return only when validation passes

    IMPORTANT: Extract specific paths from user request and use appropriate
    source/destination paths based on role."""
)

# ============================================
# Wrap S3 specialist as a tool
# ============================================
@tool
def create_s3_resource(user_request: str, role: str) -> dict:
    """Generate AWS S3 resource configuration.

    Args:
        user_request: The user's pipeline request
        role: Either 'source' or 'destination'

    Returns:
        Valid S3 configuration dict
    """
    prompt = f"""Create an S3 {role} configuration.

    User request: {user_request}
    Role: {role}

    Generate a complete, valid S3 configuration."""

    # S3 specialist handles everything independently
    result = s3_specialist(prompt)
    return result

# ============================================
# Pipeline Orchestrator
# ============================================
orchestrator = Agent(
    model=model,
    tools=[create_s3_resource],  # Wrapped S3 specialist
    system_prompt="""You orchestrate GC2 pipeline creation.

    Delegate resource creation to specialist agents.
    You don't need to know HOW they work, just WHEN to use them."""
)

# Usage
response = orchestrator("Create a pipeline to move CSV files from S3 to S3")
# Orchestrator will call:
#   create_s3_resource(request, "source")
#   create_s3_resource(request, "destination")
```

---

## Pattern 3: MCP Tools

### Concept

**MCP (Model Context Protocol)** allows agents to use tools from external servers.

### Simple Example

```python
from strands import Agent

# Agent uses MCP tools (from external server)
agent = Agent(
    model=model,
    tools=[
        "mcp://filesystem-server/read_file",      # MCP tool
        "mcp://database-server/query_database",   # MCP tool
        "mcp://api-server/call_external_api",     # MCP tool
    ],
    system_prompt="You can access files, databases, and APIs"
)

response = agent("Read the config file and query the database")
# Agent will:
# 1. Call MCP tool: read_file("config.json")
# 2. Call MCP tool: query_database("SELECT * FROM users")
```

### MCP Architecture

```
┌─────────────────────────────────────┐
│ Your Agent (in AgentCore)           │
│                                     │
│ "I need to read a file"             │
│ → Calls: mcp://filesystem/read_file│
└──────────────┬──────────────────────┘
               │
               │ (MCP Protocol)
               │
               ▼
┌─────────────────────────────────────┐
│ MCP Server (separate process)       │
│                                     │
│ Receives: read_file("config.json") │
│ Executes: with open(...) ...       │
│ Returns: file contents              │
└─────────────────────────────────────┘
```

### GC2 Example: ChromaDB MCP Server

```python
# ============================================
# MCP Server for ChromaDB
# mcp_chroma_server.py
# ============================================
from mcp.server import Server
from mcp.server.stdio import stdio_server
import chromadb

app = Server("gc2-vectorstore")
client = chromadb.PersistentClient(path="./data/chroma_db")

@app.call_tool()
async def query_schemas(query: str, n_results: int = 3) -> list:
    """Query GC2 schemas collection."""
    collection = client.get_collection("gc2_schemas")
    results = collection.query(query_texts=[query], n_results=n_results)
    return results["documents"][0]

@app.call_tool()
async def query_templates(query: str, n_results: int = 3) -> list:
    """Query GC2 templates collection."""
    collection = client.get_collection("gc2_templates")
    results = collection.query(query_texts=[query], n_results=n_results)
    return results["documents"][0]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

# Run: python mcp_chroma_server.py

# ============================================
# Agent uses MCP ChromaDB tools
# ============================================
from strands import Agent

planner = Agent(
    model=model,
    tools=[
        "mcp://gc2-vectorstore/query_schemas",    # MCP tool
        "mcp://gc2-vectorstore/query_templates",  # MCP tool
    ],
    system_prompt="You create GC2 configurations using vector store"
)

response = planner("Create an S3 configuration")
# Agent calls MCP server for schema and templates
```

---

## Pattern 4: Combining Everything

### The Ultimate Architecture

**Local tools + Wrapped agents + MCP tools = Powerful multi-agent system**

### Example: Complete GC2 System

```python
from strands import Agent, tool

# ============================================
# Layer 1: MCP Tools (External Services)
# ============================================
# These run as separate MCP servers

# mcp_validation_server.py
from mcp.server import Server

app = Server("gc2-validator")

@app.call_tool()
async def validate_resource(config: dict, resource_type: str) -> dict:
    """Validate GC2 resource configuration."""
    # Validation logic here
    pass

# ============================================
# Layer 2: Local Tools (In Your Container)
# ============================================
@tool
def assemble_dag(resources: list) -> dict:
    """Assemble complete DAG from resources."""
    return {
        "templateName": "Generated Pipeline",
        "resources": resources
    }

# ============================================
# Layer 3: Specialist Agents (with their own tools)
# ============================================

# S3 Specialist
@tool
def query_s3_schema() -> str:
    """Query S3 schema."""
    return "S3 schema requirements..."

s3_agent = Agent(
    model=model,
    tools=[
        query_s3_schema,  # Local tool
        "mcp://gc2-validator/validate_resource",  # MCP tool
    ],
    system_prompt="You create S3 configurations"
)

# Route Specialist
@tool
def query_route_schema() -> str:
    """Query route schema."""
    return "Route schema requirements..."

route_agent = Agent(
    model=model,
    tools=[
        query_route_schema,  # Local tool
        "mcp://gc2-validator/validate_resource",  # MCP tool
    ],
    system_prompt="You create route configurations"
)

# Partner Specialist
@tool
def query_partner_schema() -> str:
    """Query partner schema."""
    return "Partner schema requirements..."

partner_agent = Agent(
    model=model,
    tools=[
        query_partner_schema,  # Local tool
        "mcp://gc2-validator/validate_resource",  # MCP tool
    ],
    system_prompt="You create partner configurations"
)

# ============================================
# Layer 4: Wrapped Specialist Agents
# ============================================
@tool
def create_s3_resource(user_request: str, role: str) -> dict:
    """Create S3 resource using specialist agent."""
    return s3_agent(f"Create {role} S3 for: {user_request}")

@tool
def create_route_resource(source: str, destination: str, file_filter: str) -> dict:
    """Create route resource using specialist agent."""
    return route_agent(f"Create route from {source} to {destination} filtering {file_filter}")

@tool
def create_partner_resource(user_request: str, partner_type: str) -> dict:
    """Create partner resource using specialist agent."""
    return partner_agent(f"Create {partner_type} partner for: {user_request}")

# ============================================
# Layer 5: Master Orchestrator
# ============================================
orchestrator = Agent(
    model=model,
    tools=[
        # Wrapped specialist agents
        create_s3_resource,
        create_route_resource,
        create_partner_resource,
        # Local tools
        assemble_dag,
    ],
    system_prompt="""You are the GC2 pipeline orchestrator.

    Your job:
    1. Analyze user request to determine needed resources
    2. Delegate to specialist agents:
       - create_s3_resource() for S3 buckets
       - create_route_resource() for routes
       - create_partner_resource() for partners
    3. Assemble complete DAG using assemble_dag()

    Key rules:
    - Each source-to-destination needs a route
    - 1 source → 2 destinations = 2 routes
    - Detect actions (pgp-decrypt, zip, etc.) from user request
    """
)

# ============================================
# Usage
# ============================================
response = orchestrator("""
Create a pipeline to move encrypted CSV files from an S3 bucket
to two destinations: another S3 bucket and an SFTP partner.
Decrypt the files during transfer.
""")
```

### Complete Flow

```
User Request
    ↓
┌────────────────────────────────────────┐
│ Master Orchestrator                    │
│ "I need: S3 source, S3 dest, partner, │
│  and 2 routes with pgp-decrypt"       │
└─┬──────────────────────────────────────┘
  │
  ├─► create_s3_resource(request, "source")
  │   └─► S3 Agent (independent LLM session)
  │       ├─► query_s3_schema() [local]
  │       ├─► generate config
  │       └─► mcp://validate [MCP]
  │       Returns: {s3 source config}
  │
  ├─► create_s3_resource(request, "destination")
  │   └─► S3 Agent (independent LLM session)
  │       └─► ... same process
  │       Returns: {s3 dest config}
  │
  ├─► create_partner_resource(request, "external")
  │   └─► Partner Agent (independent LLM session)
  │       ├─► query_partner_schema() [local]
  │       └─► mcp://validate [MCP]
  │       Returns: {partner config}
  │
  ├─► create_route_resource(source, s3_dest, ".+\\.csv")
  │   └─► Route Agent (independent LLM session)
  │       └─► Actions: ["pgp-decrypt"]
  │       Returns: {route config}
  │
  ├─► create_route_resource(source, partner, ".+\\.csv")
  │   └─► Route Agent (independent LLM session)
  │       └─► Actions: ["pgp-decrypt"]
  │       Returns: {route config}
  │
  └─► assemble_dag([configs...]) [local tool]
      Returns: {complete DAG}
```

---

## GC2 Copilot Architecture

### Recommended Architecture

```
┌─────────────────────────────────────────────────┐
│ Pipeline Orchestrator Agent                     │
│                                                 │
│ Responsibilities:                               │
│ - Analyze user intent                           │
│ - Determine required resources                  │
│ - Delegate to specialists                       │
│ - Assemble final DAG                            │
│                                                 │
│ Tools:                                          │
│ - create_s3_resource (wrapped agent)            │
│ - create_route_resource (wrapped agent)         │
│ - create_partner_resource (wrapped agent)       │
│ - assemble_dag (local function)                 │
└──┬──────────────────────────────────────────────┘
   │
   ├─────────────────────────────────────┐
   │                                     │
   ▼                                     ▼
┌─────────────────┐              ┌─────────────────┐
│ S3 Agent        │              │ Route Agent     │
│                 │              │                 │
│ Tools:          │              │ Tools:          │
│ - query_schema  │              │ - query_schema  │
│ - query_examples│              │ - detect_actions│
│ - validate      │              │ - validate      │
└─────────────────┘              └─────────────────┘
   │                                     │
   └─────────────┬───────────────────────┘
                 ▼
┌─────────────────────────────────────────────────┐
│ MCP Servers (Optional)                          │
│                                                 │
│ - gc2-vectorstore (ChromaDB)                    │
│ - gc2-validator (Pydantic models)               │
│ - gc2-schema-registry                           │
└─────────────────────────────────────────────────┘
```

### Decision Tree: When to Use Each Pattern

```
Question: Does the task need LLM reasoning?
│
├─ NO → Use plain @tool function
│   Example: query_database(), calculate_total()
│
└─ YES → Does it need MULTI-STEP reasoning?
    │
    ├─ NO → Use plain @tool with LLM call
    │   Example: simple config generation
    │
    └─ YES → Use wrapped agent
        │
        └─ Question: Should it be in a separate service?
            │
            ├─ NO → Local wrapped agent
            │   Example: S3 specialist in same container
            │
            └─ YES → Wrapped agent exposed via MCP
                Example: Validation service used by multiple systems
```

---

## Implementation Guide

### Step 1: Start Simple (Agent with Local Tools)

```python
# agent_deploy.py
from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp

@tool
def get_current_time() -> str:
    """Get current timestamp."""
    from datetime import datetime
    return datetime.now().isoformat()

model = AnthropicModel(model_id="claude-sonnet-4-5-20250929", max_tokens=1024)
agent = Agent(
    model=model,
    tools=[get_current_time],
    system_prompt="You're a helpful assistant"
)

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload: dict) -> dict:
    return {"result": agent(payload["prompt"])}

if __name__ == "__main__":
    app.run()
```

### Step 2: Add Specialist Agents

```python
# src/gc2_copilot_strands/agents/specialists.py
from strands import Agent, tool

# S3 Specialist
@tool
def get_s3_requirements() -> str:
    """Get S3 requirements."""
    return "s3Path max 319 chars, kmsKey max 50 chars"

s3_specialist = Agent(
    model=model,
    tools=[get_s3_requirements],
    system_prompt="You create S3 configs"
)

# Wrap as tool
@tool
def create_s3(request: str, role: str) -> dict:
    """Create S3 configuration."""
    return s3_specialist(f"Create {role} S3 for: {request}")
```

### Step 3: Build Orchestrator

```python
# agent_deploy.py
from src.gc2_copilot_strands.agents.specialists import create_s3

orchestrator = Agent(
    model=model,
    tools=[create_s3],
    system_prompt="You orchestrate pipeline creation"
)

@app.entrypoint
def invoke(payload: dict) -> dict:
    return {"result": orchestrator(payload["prompt"])}
```

### Step 4: Add MCP (Optional)

```python
# mcp_server.py
from mcp.server import Server

app = Server("gc2-tools")

@app.call_tool()
async def validate(config: dict, type: str) -> dict:
    """Validate configuration."""
    # Validation logic
    pass

# In agent_deploy.py
orchestrator = Agent(
    model=model,
    tools=[
        create_s3,
        "mcp://gc2-tools/validate",  # MCP tool
    ],
    system_prompt="You orchestrate with validation"
)
```

---

## Best Practices

### 1. Start Simple, Add Complexity
- Begin with one agent and local tools
- Add specialists when you have repeated patterns
- Add MCP when you need service isolation

### 2. Clear Responsibilities
```python
# Good: Clear, focused agents
s3_agent = Agent(tools=[...], system_prompt="You ONLY create S3 configs")
route_agent = Agent(tools=[...], system_prompt="You ONLY create routes")

# Bad: One agent does everything
god_agent = Agent(tools=[...], system_prompt="You do everything")
```

### 3. Tool Naming
```python
# Good: Descriptive, verb-based
@tool
def validate_s3_configuration(config: dict) -> dict:
    """Validate an S3 configuration against schema."""

# Bad: Vague
@tool
def check(thing: Any) -> Any:
    """Check something."""
```

### 4. Docstrings Matter
The LLM reads docstrings to decide when to use tools:

```python
# Good
@tool
def create_s3_resource(user_request: str, role: str) -> dict:
    """Generate AWS S3 resource configuration.

    Args:
        user_request: The user's complete pipeline request
        role: Must be either 'source' or 'destination'

    Returns:
        Valid S3 configuration dict with all required fields

    Example:
        create_s3_resource("move CSV files", "source")
    """

# Bad
@tool
def s3(r: str, x: str) -> dict:
    """S3 stuff."""
```

### 5. Error Handling in Tools
```python
@tool
def validate_config(config: dict, resource_type: str) -> dict:
    """Validate resource configuration."""
    try:
        model = RESOURCE_MAP[resource_type]
        model.model_validate(config)
        return {"valid": True, "message": "Configuration is valid"}
    except ValidationError as e:
        # Return structured errors the LLM can understand
        return {
            "valid": False,
            "errors": [{"field": err["loc"], "message": err["msg"]}
                      for err in e.errors()]
        }
    except Exception as e:
        return {"valid": False, "message": f"Validation failed: {str(e)}"}
```

---

## Quick Reference

### Agent Creation
```python
agent = Agent(
    model=anthropic_model,
    tools=[tool1, tool2],
    system_prompt="Instructions"
)
```

### Tool Definition
```python
@tool
def tool_name(arg: type) -> return_type:
    """Clear description of what this does."""
    return result
```

### Wrapped Agent
```python
specialist = Agent(model=model, tools=[...])

@tool
def use_specialist(request: str) -> result:
    """Use specialist agent."""
    return specialist(request)

orchestrator = Agent(tools=[use_specialist])
```

### MCP Tool
```python
# In agent
agent = Agent(
    tools=["mcp://server-name/tool-name"]
)
```

---

## Summary

| Pattern | When to Use | Example |
|---------|-------------|---------|
| **Agent with Tools** | Agent needs to perform actions | Calculator with math operations |
| **Agent as Tool** | Task needs multi-step reasoning | S3 config creation with validation loop |
| **MCP Tools** | Tool in separate service | Database queries, file operations |
| **Combined** | Complex multi-agent system | GC2 pipeline orchestration |

**Key Insight**:
- **Tools** = Actions the agent can take (run in your container)
- **Agents** = Reasoning + Tools (LLM decides what to do)
- **Wrapped Agents** = Independent reasoning sessions
- **MCP** = Tools from other services

---

## Next Steps for GC2 Copilot

1. ✅ Hello world agent (completed)
2. 📝 Add local tools for vector store queries
3. 🤖 Create S3 specialist agent
4. 🤖 Create Route specialist agent
5. 🤖 Create Partner specialist agent
6. 🎯 Build orchestrator with wrapped specialists
7. 🔧 Add validation and error handling
8. 🚀 Deploy to AgentCore
9. 📊 Add observability and logging
10. 🔌 (Optional) Add MCP servers for shared services

---

**Questions or need clarification on any section?**
