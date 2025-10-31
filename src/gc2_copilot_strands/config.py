"""Configuration management for GC2 Copilot Strands."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""

    # LLM Provider Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai").strip().lower()  # "openai" or "anthropic"

    # Anthropic Configuration
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "").strip()
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929").strip()

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o").strip()

    # Project paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"

    # ChromaDB Configuration
    CHROMA_DIR: Path = DATA_DIR / os.getenv("CHROMA_DIR", "chroma_db")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2").strip()

    # Retry Configuration
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    INITIAL_RETRY_DELAY: float = float(os.getenv("INITIAL_RETRY_DELAY", "2.0"))
    MAX_RETRY_DELAY: float = float(os.getenv("MAX_RETRY_DELAY", "60.0"))

    # ChromaDB singleton instance
    _chroma_client = None

    @classmethod
    def get_chroma_client(cls):
        """Get the singleton ChromaClient instance."""
        if cls._chroma_client is None:
            from .vectorstore import ChromaClient
            cls._chroma_client = ChromaClient.get_instance(
                persist_directory=str(cls.CHROMA_DIR),
                embedding_model=cls.EMBEDDING_MODEL
            )
        return cls._chroma_client

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration based on selected provider."""
        if cls.LLM_PROVIDER == "anthropic":
            if not cls.ANTHROPIC_API_KEY:
                raise ValueError(
                    "ANTHROPIC_API_KEY not found. Please set it in .env file or environment."
                )
        elif cls.LLM_PROVIDER == "openai":
            if not cls.OPENAI_API_KEY:
                raise ValueError(
                    "OPENAI_API_KEY not found. Please set it in .env file or environment."
                )
        else:
            raise ValueError(
                f"Invalid LLM_PROVIDER: {cls.LLM_PROVIDER}. Must be 'openai' or 'anthropic'."
            )
