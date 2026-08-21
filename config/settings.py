"""Configuration settings for FogAgent."""
from dataclasses import dataclass, field
from pathlib import Path
import os


@dataclass
class Settings:
    # Project Paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data")
    memory_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "memory")
    knowledge_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "knowledge")

    # Database Paths
    memory_db_path: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "memory" / "memory.db")
    knowledge_db_path: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "knowledge" / "knowledge.db")

    # Ollama / Model Configuration
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    model_name: str = os.getenv("FOGAGENT_MODEL", "qwen3:8b")
    context_length: int = int(os.getenv("FOGAGENT_NUM_CTX", "8192"))
    temperature: float = float(os.getenv("FOGAGENT_TEMPERATURE", "0.7"))
    request_timeout: float = float(os.getenv("FOGAGENT_TIMEOUT", "120.0"))

    # System Prompts
    system_prompt: str = """You are FogAgent, a personal local AI agent.
You run locally through Ollama using Qwen3.
Your goals:
- Help the user solve problems accurately and efficiently.
- Reason carefully and step by step.
- Be honest about what you know and do not know.
- Use tools when they become available.
- Remember useful context when memory is active.
- Learn new concepts only when Study Mode is enabled.
- Never fabricate actions or claim to have performed operations you did not execute."""

    def __post_init__(self):
        # Ensure data directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)


# Global default settings instance
settings = Settings()
