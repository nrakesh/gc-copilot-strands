# Dockerfile for GC2 Copilot Strands Agent
# Platform: ARM64 (required for AgentCore Runtime)

FROM --platform=linux/arm64 python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml ./
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy application code
COPY src/ ./src/
COPY agent_deploy.py ./
COPY .env .env

# Expose port 8080 (required by AgentCore)
EXPOSE 8080

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/ping')"

# Run the agent using AgentCore toolkit
CMD ["python", "agent_deploy.py"]
