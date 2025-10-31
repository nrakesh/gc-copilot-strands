# GC2 Copilot - Quick Start Guide

Get started with GC2 Copilot in 5 minutes!

## Prerequisites

1. **uv package manager** (install if needed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **API Key** - Set up your `.env` file:
   ```bash
   cd /Users/rakeshnair/develop/ai-agents/gc2-copilot-strands
   cp .env.example .env
   # Edit .env and add your API key
   ```

## Three Ways to Use GC2 Copilot

### 🚀 Option 1: Shell Scripts (Easiest)

Use the convenient shell scripts in `bin/` directory:

```bash
cd /Users/rakeshnair/develop/ai-agents/gc2-copilot-strands

# Run demo to see examples
./bin/gc2-demo

# Generate a pipeline
./bin/gc2 "Move CSV files from S3 to another S3 bucket" -o tmp/my-pipeline.json

# Run tests
./bin/gc2-test
```

**Tip**: Add `bin/` to your PATH to use from anywhere:
```bash
export PATH="/Users/rakeshnair/develop/ai-agents/gc2-copilot-strands/bin:$PATH"
gc2 "Your request here" -o output.json
```

---

### 💻 Option 2: Python CLI (Flexible)

Use the main CLI directly:

```bash
cd /Users/rakeshnair/develop/ai-agents/gc2-copilot-strands

# Generate pipeline
uv run python main.py "Move CSV files from S3 to S3" -o tmp/pipeline.json

# Run demo
uv run python main.py --demo

# Run tests
uv run python main.py --test

# Get help
uv run python main.py --help
```

---

### 🐍 Option 3: Python API (Programmatic)

Use directly in your Python code:

```python
from src.gc2_copilot_strands.agents import generate_gc2_pipeline

# Generate pipeline
pipeline = generate_gc2_pipeline(
    "Move CSV files from S3 to another S3 bucket",
    output_file="output/my-pipeline.json"
)

# Check results
print(f"Generated {len(pipeline['resources'])} resources")
```

---

## Your First Pipeline

### Step 1: Run the Demo

```bash
./bin/gc2-demo
```

This shows you how it works with 2 examples.

### Step 2: Generate Your Own

```bash
./bin/gc2 "Move CSV files from S3 to another S3 bucket" -o tmp/my-first-pipeline.json
```

### Step 3: Check the Output

```bash
cat tmp/my-first-pipeline.json | python -m json.tool
```

You should see a JSON file with 3 resources:
- Source S3 bucket
- Destination S3 bucket
- Route connecting them

---

## Common Pipeline Requests

### Simple File Transfer
```bash
./bin/gc2 "Move CSV files from S3 to S3" -o pipelines/csv-transfer.json
```

### With Encryption
```bash
./bin/gc2 "Transfer PGP encrypted files, decrypt them" -o pipelines/decrypt.json
```

### Multiple File Types
```bash
./bin/gc2 "Copy CSV and TXT files from source to destination S3" -o pipelines/multi.json
```

### JSON Files
```bash
./bin/gc2 "Move JSON files from one S3 bucket to another" -o pipelines/json.json
```

---

## Project Structure

```
gc2-copilot-strands/
├── bin/                    # ⭐ Shell scripts (easiest way)
│   ├── gc2                # Main command
│   ├── gc2-demo          # Run demo
│   └── gc2-test          # Run tests
├── main.py               # Python CLI
├── scripts/              # Test & utility scripts
├── src/                  # Source code
│   └── gc2_copilot_strands/
│       ├── agents/       # AI agents
│       ├── models/       # Data models
│       └── tools/        # Agent tools
├── docs/                 # Documentation
└── tmp/                  # Generated pipelines
```

---

## Configuration

### LLM Provider

Choose between OpenAI (default) or Anthropic in `.env`:

```bash
# Use OpenAI (recommended for cost)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-your-key
OPENAI_MODEL=gpt-4o-mini

# Or use Anthropic
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
CLAUDE_MODEL=claude-sonnet-4-5-20250929
```

### Retry Settings

Adjust API retry behavior:

```bash
MAX_RETRIES=3              # Number of retries
INITIAL_RETRY_DELAY=2.0    # First retry delay (seconds)
MAX_RETRY_DELAY=60.0       # Max delay between retries
```

---

## Troubleshooting

### "Permission denied" when running bin scripts
```bash
chmod +x bin/*
```

### "No module named 'src'"
```bash
# Make sure you're in the project directory
cd /Users/rakeshnair/develop/ai-agents/gc2-copilot-strands
```

### API rate limit errors
```bash
# Use gpt-4o-mini for lower rate limits
export OPENAI_MODEL=gpt-4o-mini
```

### Empty actions list error
This is a known issue being fixed. The pipeline should still generate on retry.

---

## Next Steps

1. **Read the full documentation**: See `docs/MULTI_AGENT_WORKFLOW.md`
2. **Explore agents**: Check `src/gc2_copilot_strands/agents/`
3. **Run tests**: `./bin/gc2-test`
4. **Add to PATH**: Make `gc2` available everywhere
5. **Try UPDATE workflow**: Coming soon!

---

## Getting Help

```bash
# Show help
./bin/gc2 --help

# See examples
./bin/gc2-demo

# Read documentation
cat docs/MULTI_AGENT_WORKFLOW.md

# Check bin scripts
cat bin/README.md
```

---

## Cost Estimates

Approximate cost per pipeline generation:

- **OpenAI gpt-4o-mini**: $0.002 - $0.005 (recommended for development)
- **OpenAI gpt-4o**: $0.02 - $0.05 (production quality)
- **Anthropic Claude Sonnet**: $0.01 - $0.03

---

## Development Workflow

### For Testing
```bash
# 1. Run demo
./bin/gc2-demo

# 2. Run tests
./bin/gc2-test

# 3. Check config
uv run python scripts/check_config.py

# 4. Verify RAG
uv run python scripts/verify_rag.py
```

### For Production
```bash
# Generate pipeline
./bin/gc2 "Your production request" -o output/prod-pipeline.json

# Validate output
python -m json.tool < output/prod-pipeline.json

# Deploy (when ready)
# Deploy to GrandCentral...
```

---

## Support

- **Documentation**: `docs/` directory
- **Examples**: Run `./bin/gc2-demo`
- **Issues**: Check error messages and logs
- **Configuration**: See `.env.example`

Happy pipeline generating! 🚀
