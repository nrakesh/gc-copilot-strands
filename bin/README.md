# GC2 Copilot - Command Line Tools

Convenient shell scripts for running GC2 Copilot pipeline generator.

## Installation (Optional)

To use these commands from anywhere, add this `bin/` directory to your PATH:

```bash
# Add to your ~/.bashrc or ~/.zshrc
export PATH="/Users/rakeshnair/develop/ai-agents/gc2-copilot-strands/bin:$PATH"

# Reload your shell
source ~/.bashrc  # or source ~/.zshrc
```

After this, you can run `gc2` from any directory!

## Commands

### `gc2` - Main Pipeline Generator

Generate GrandCentral pipelines from natural language requests.

**Usage:**
```bash
# Generate pipeline and display to console
./bin/gc2 "Move CSV files from S3 to another S3 bucket"

# Generate and save to file
./bin/gc2 "Transfer encrypted files from S3, decrypt them" -o output/my-pipeline.json

# Get help
./bin/gc2 --help
```

**Examples:**
```bash
# Simple S3 transfer
./bin/gc2 "Move CSV files from S3 to S3"

# With encryption
./bin/gc2 "Transfer PGP encrypted files, decrypt them" -o tmp/pipeline.json

# Multiple file types
./bin/gc2 "Copy CSV and TXT files from source S3 to destination S3" -o pipelines/multi-file.json

# JSON files
./bin/gc2 "Move JSON files from S3 bucket to another S3 bucket"
```

---

### `gc2-demo` - Run Demo

Run demo with example pipelines to see how the system works.

**Usage:**
```bash
./bin/gc2-demo
```

**What it does:**
- Runs 2 example pipeline generations
- Shows complete workflow
- Saves output to `tmp/demo-*.json`
- Great for first-time users

---

### `gc2-test` - Run Tests

Run the complete test suite.

**Usage:**
```bash
./bin/gc2-test
```

**What it does:**
- Runs all end-to-end tests
- Tests CREATE workflow
- Validates generated pipelines
- Saves output to `tmp/`

---

## Quick Start

### First Time Setup

1. **Navigate to project:**
   ```bash
   cd /Users/rakeshnair/develop/ai-agents/gc2-copilot-strands
   ```

2. **Run demo to see it in action:**
   ```bash
   ./bin/gc2-demo
   ```

3. **Generate your first pipeline:**
   ```bash
   ./bin/gc2 "Move CSV files from S3 to another S3 bucket" -o tmp/my-first-pipeline.json
   ```

4. **Check the output:**
   ```bash
   cat tmp/my-first-pipeline.json | python -m json.tool
   ```

### Daily Usage

```bash
# From project directory
./bin/gc2 "Your pipeline request here" -o output/pipeline.json

# Or if added to PATH
gc2 "Your pipeline request here" -o output/pipeline.json
```

## Adding to PATH (Recommended)

For easier access, add the bin directory to your PATH:

**For Bash (~/.bashrc):**
```bash
echo 'export PATH="/Users/rakeshnair/develop/ai-agents/gc2-copilot-strands/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**For Zsh (~/.zshrc):**
```bash
echo 'export PATH="/Users/rakeshnair/develop/ai-agents/gc2-copilot-strands/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Test it works:**
```bash
# Should work from any directory now
cd ~
gc2 "Move CSV files from S3 to S3" -o /tmp/test-pipeline.json
```

## Script Details

### How They Work

All scripts:
1. Find the project root automatically
2. Change to project directory
3. Run `uv run python main.py` with appropriate arguments
4. Work from any directory (if in PATH)

### Exit Codes

- `0` - Success
- `1` - Error (check error message)

### Output Files

By default, pipelines are saved to `tmp/` directory unless you specify `-o`:

```bash
# Saves to tmp/ (default)
./bin/gc2-demo

# Saves to custom location
./bin/gc2 "Your request" -o /path/to/output.json
```

## Troubleshooting

### "Permission denied"

Make scripts executable:
```bash
chmod +x bin/*
```

### "No module named 'src'"

Make sure you're running from the project root or the scripts are finding the project correctly:
```bash
cd /Users/rakeshnair/develop/ai-agents/gc2-copilot-strands
./bin/gc2 "Your request"
```

### "uv: command not found"

Install uv package manager:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Advanced Usage

### Piping Output

```bash
# Generate and pipe to jq for formatting
./bin/gc2 "Move CSV files" -o tmp/p.json && cat tmp/p.json | jq .
```

### Multiple Pipelines

```bash
# Generate multiple pipelines
./bin/gc2 "Move CSV files" -o pipelines/csv-transfer.json
./bin/gc2 "Move JSON files" -o pipelines/json-transfer.json
./bin/gc2 "Transfer encrypted files" -o pipelines/encrypted-transfer.json
```

### Integration with CI/CD

```bash
# Example: Generate pipeline in CI/CD
./bin/gc2 "${PIPELINE_REQUEST}" -o "output/pipeline-${BUILD_ID}.json"

# Validate it was created
if [ -f "output/pipeline-${BUILD_ID}.json" ]; then
    echo "Pipeline generated successfully"
else
    echo "Pipeline generation failed"
    exit 1
fi
```

## Environment Variables

The scripts respect the same environment variables as `main.py`:

- `LLM_PROVIDER` - OpenAI or Anthropic
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `OPENAI_MODEL` - Model to use (gpt-4o, gpt-4o-mini)
- `MAX_RETRIES` - Retry attempts for API calls

See `.env.example` for full configuration options.

## Tips

1. **Start with demo**: Run `./bin/gc2-demo` to see examples first
2. **Use -o flag**: Always save to file with `-o` for production use
3. **Check output**: Validate JSON with `python -m json.tool` or `jq`
4. **Add to PATH**: Makes commands available everywhere
5. **Tab completion**: Some shells support tab completion for these scripts

## Getting Help

```bash
# Show help
./bin/gc2 --help

# Check version info
./bin/gc2 --version  # (if implemented)

# See examples
./bin/gc2-demo
```

## Contributing

To add new scripts to `bin/`:

1. Create script with `#!/usr/bin/env bash` shebang
2. Add `SCRIPT_DIR` and `PROJECT_ROOT` resolution
3. Make executable with `chmod +x`
4. Document in this README
5. Follow naming convention: `gc2-*`
