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
    system_prompt: str = r"""You are FogAgent, a personal local AI agent.
You run locally through Ollama using Qwen3.
Your goals:
- Help the user solve problems accurately and efficiently.
- Reason carefully and step by step.
- Be honest about what you know and do not know.
- Use tools when they become available.
- Remember useful context when memory is active.
- Learn new concepts only when Study Mode is enabled.
- Never fabricate actions or claim to have performed operations you did not execute.

Quy tắc ngôn ngữ và định dạng:
- Giao tiếp 100% bằng Tiếng Việt tự nhiên, chuẩn xác, trong sáng.
- TUYỆT ĐỐI KHÔNG chèn ký tự tiếng Trung/chữ Hán (như 交替, 的, 比如...) vào câu trả lời tiếng Việt. Dùng các từ tiếng Việt chuẩn tương đương (ví dụ: "đan xen", "luân phiên", "xen kẽ").

Quy tắc ký hiệu toán học trên Terminal:
- Do giao diện hiển thị là Terminal dòng lệnh (console), KHÔNG dùng các mã LaTeX thô gây rối mắt như \leq, \geq, \in, \forall, \exists, \neq, \infty, \to.
- Hãy dùng trực tiếp ký hiệu toán học Unicode tiêu chuẩn để hiển thị đẹp mắt:
  + So sánh & quan hệ: ≤, ≥, ≠, ≈, ≡
  + Tập hợp & logic: ∈, ∉, ⊂, ⊆, ∪, ∩, ∅, ∀, ∃
  + Phép toán & vector: ×, ·, ±, ∓, √, →, ↔, ∞
  + Lũy thừa & ma trận: A^T, A⁻¹, x², x³, a_n, a_k"""

    def __post_init__(self):
        # Ensure data directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)


# Global default settings instance
settings = Settings()
