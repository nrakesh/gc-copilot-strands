# Scripts Directory

This directory contains test scripts, utilities, and development tools for GC2 Copilot Strands.

## Test Scripts

### `test_complete_workflow.py`
**Purpose**: Test the complete multi-agent orchestration workflow

**What it does**:
- Tests CREATE workflow with the Orchestrator Agent
- Runs 2 test cases:
  1. Simple S3 → S3 CSV transfer
  2. S3 → S3 with PGP decryption

**Run it**:
```bash
uv run python scripts/test_complete_workflow.py
```

**Output**: Generates pipeline JSON files in `tmp/` directory

---

### `test_s3_specialist.py`
**Purpose**: Test the S3 specialist agent in isolation

**What it does**:
- Tests planner → S3 specialist integration
- Validates S3 resource generation
- Verifies Pydantic model validation

**Run it**:
```bash
uv run python scripts/test_s3_specialist.py
```

---

## Development Scripts

### `run_planner.py`
**Purpose**: Run the planner agent with sample requests

**What it does**:
- Tests the planner agent independently
- Shows resource planning output
- Useful for debugging planning logic

**Run it**:
```bash
uv run python scripts/run_planner.py
```

---

### `debug_planner.py`
**Purpose**: Debug planner agent with detailed output

**What it does**:
- Runs planner with verbose output
- Shows RAG query results
- Displays structured output details

**Run it**:
```bash
uv run python scripts/debug_planner.py
```

---

## Utility Scripts

### `verify_rag.py`
**Purpose**: Verify RAG (ChromaDB) integration

**What it does**:
- Checks ChromaDB collections exist
- Tests vector store queries
- Validates embedding retrieval

**Run it**:
```bash
uv run python scripts/verify_rag.py
```

---

### `check_config.py`
**Purpose**: Verify configuration and environment setup

**What it does**:
- Validates `.env` file exists and is correct
- Checks API keys are set
- Verifies ChromaDB paths

**Run it**:
```bash
uv run python scripts/check_config.py
```

---

## Deployment Scripts

### `agent_deploy.py`
**Purpose**: Deploy agents to AgentCore Runtime (when ready)

**What it does**:
- Package agents for deployment
- Upload to AgentCore
- Configure runtime environment

**Status**: Not yet implemented (placeholder)

**Run it**:
```bash
uv run python scripts/agent_deploy.py
```

---

## Quick Reference

### Run All Tests
```bash
# From root directory
uv run python main.py --test

# Or directly
uv run python scripts/test_complete_workflow.py
```

### Debug Workflow
```bash
# 1. Verify RAG
uv run python scripts/verify_rag.py

# 2. Test planner
uv run python scripts/run_planner.py

# 3. Test S3 specialist
uv run python scripts/test_s3_specialist.py

# 4. Test complete workflow
uv run python scripts/test_complete_workflow.py
```

### Check Setup
```bash
# Verify configuration
uv run python scripts/check_config.py

# Verify RAG/ChromaDB
uv run python scripts/verify_rag.py
```

## File Organization

```
scripts/
├── README.md                      # This file
├── test_complete_workflow.py      # End-to-end workflow tests
├── test_s3_specialist.py          # S3 specialist tests
├── run_planner.py                 # Planner demo/test
├── debug_planner.py               # Planner debugging
├── verify_rag.py                  # RAG verification
├── check_config.py                # Config verification
└── agent_deploy.py                # Deployment (future)
```

## Adding New Scripts

When adding new scripts to this directory:

1. **Use descriptive names**: `test_*.py` for tests, `verify_*.py` for verification, etc.
2. **Add documentation**: Update this README with the script's purpose
3. **Include usage**: Show how to run it
4. **Keep it simple**: One clear purpose per script
5. **Use uv run**: Make scripts runnable with `uv run python scripts/your_script.py`

## Best Practices

- **Tests**: Should be idempotent and clean up after themselves
- **Utilities**: Should check prerequisites and give clear error messages
- **Debug scripts**: Should output verbose, human-readable information
- **Deployment**: Should validate before deploying and support rollback
