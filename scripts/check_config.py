"""Check if configuration is loading correctly."""

from src.gc2_copilot_strands.config import Config

print("Checking configuration...")
print(f"API Key loaded: {'Yes' if Config.ANTHROPIC_API_KEY else 'No'}")
print(f"API Key length: {len(Config.ANTHROPIC_API_KEY) if Config.ANTHROPIC_API_KEY else 0}")
print(f"API Key starts with: {Config.ANTHROPIC_API_KEY[:7] if Config.ANTHROPIC_API_KEY else 'N/A'}")
print(f"Model: {Config.CLAUDE_MODEL}")
