# GC2 Copilot Strands - Documentation

This directory contains comprehensive documentation for the GC2 Copilot Strands project.

## 📚 Documentation Index

### Getting Started

1. **[ARCHITECTURE.md](./ARCHITECTURE.md)** - **START HERE!**
   - Core Strands concepts (Agent, Tool, MCP)
   - Multi-agent patterns and examples
   - Agent with tools pattern
   - Agent as tool (wrapped agents)
   - How LLMs request tools and frameworks execute them
   - Best practices for Strands development

### Multi-Agent Workflow

2. **[MULTI_AGENT_WORKFLOW.md](./MULTI_AGENT_WORKFLOW.md)** - **Complete System Overview**
   - End-to-end pipeline generation workflow
   - Planner → S3 Specialist → Route Specialist flow
   - Agent communication patterns
   - Type-safe validation with Pydantic
   - RAG integration for all agents
   - Testing strategies

### Specialist Agents

3. **[S3_SPECIALIST.md](./S3_SPECIALIST.md)** - **S3 Resource Generation**
   - S3 specialist agent details
   - Generation rules (region, paths, KMS keys)
   - Pydantic model validation
   - RAG context usage
   - Testing examples

## 🚀 Quick Navigation

### For New Developers
1. Read [ARCHITECTURE.md](./ARCHITECTURE.md) sections 1-3 for core concepts
2. Review [MULTI_AGENT_WORKFLOW.md](./MULTI_AGENT_WORKFLOW.md) for the complete system
3. Try the examples in [S3_SPECIALIST.md](./S3_SPECIALIST.md)

### For Understanding the System
- **What is Strands?** → [ARCHITECTURE.md](./ARCHITECTURE.md) - Core Concepts
- **How does the workflow work?** → [MULTI_AGENT_WORKFLOW.md](./MULTI_AGENT_WORKFLOW.md)
- **How do I add a new specialist?** → [S3_SPECIALIST.md](./S3_SPECIALIST.md) as a template

### For Implementation Details
- **Planner Agent**: [MULTI_AGENT_WORKFLOW.md](./MULTI_AGENT_WORKFLOW.md#1-planner-agent)
- **S3 Specialist**: [S3_SPECIALIST.md](./S3_SPECIALIST.md#agent)
- **Route Specialist**: [MULTI_AGENT_WORKFLOW.md](./MULTI_AGENT_WORKFLOW.md#3-route-specialist-agent)
- **RAG Integration**: [MULTI_AGENT_WORKFLOW.md](./MULTI_AGENT_WORKFLOW.md#rag-enhanced-context)

## 🏗️ System Architecture

```
User Request
     │
     ▼
Planner Agent (with RAG)
     │
     ├─► S3 Specialist Agent
     └─► Route Specialist Agent
          │
          ▼
     Complete GC2 Pipeline JSON
```

## 📖 Key Features

✅ **Multi-Agent Architecture** - Specialized agents for each resource type
✅ **RAG-Enhanced** - ChromaDB vector store for context
✅ **Type-Safe** - Pydantic model validation
✅ **Testable** - Each agent can be tested independently
✅ **Extensible** - Easy to add new specialist agents

## 🔗 External Documentation

- **AWS Strands**: [GitHub Repository](https://github.com/awslabs/strands)
- **Pydantic**: [Documentation](https://docs.pydantic.dev/)
- **ChromaDB**: [Documentation](https://docs.trychroma.com/)
- **Terraform AWS**: [Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

## 🤝 Contributing

When adding new documentation:
1. Follow the existing structure and style
2. Include code examples with comments
3. Add diagrams for complex concepts
4. Update this index with new documents
5. Link to related documentation

## 📝 Documentation Standards

- Use clear, concise language
- Include practical examples
- Explain the "why" not just the "what"
- Use diagrams for architecture
- Keep code snippets focused and minimal
- Add navigation links between related docs
