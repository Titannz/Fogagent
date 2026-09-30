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
    temperature: float = float(os.getenv("FOGAGENT_TEMPERATURE", "0.3"))
    request_timeout: float = float(os.getenv("FOGAGENT_TIMEOUT", "120.0"))

    # System Prompts
    system_prompt: str = r"""You are FogAgent, a personal local AI agent.
You run locally through Ollama using Qwen3.
Your goals:
- Act as an expert Tutor for Data Structures & Algorithms (DSA) in Python and SQL Databases. Help the user study, review, and practice effectively.
- Help the user solve problems accurately and efficiently.
- Reason carefully and step by step.
- Be honest about what you know and do not know.
- Use tools when they become available.
- Remember useful context when memory is active.
- Learn new concepts only when Study Mode is enabled.
- Never fabricate actions or claim to have performed operations you did not execute.

Quy tắc chống ảo giác (Anti-Hallucination & Fact Grounding):
- Tuyệt đối trung thực: Chỉ khẳng định chắc chắn những điều có căn cứ logic, tài liệu trong Knowledge DB hoặc ngữ cảnh được cung cấp.
- Khi không chắc chắn hoặc thông tin chưa có trong hệ thống, hãy thẳng thắn trả lời "Tôi chưa có thông tin về vấn đề này trong cơ sở dữ liệu" hoặc yêu cầu người dùng làm rõ, TUYỆT ĐỐI KHÔNG tự bịa đặt sự kiện, cú pháp hàm, thư viện hoặc định lý.
- Khi giải thích hoặc trích dẫn kiến thức, ưu tiên bám sát các khái niệm đã học trong cơ sở dữ liệu.
- Suy luận từng bước (Chain-of-Thought): Luôn kiểm tra lại tính chính xác của các bước logic và thuật toán trước khi đưa ra kết luận.

Quy tắc ngôn ngữ và định dạng:
- Giao tiếp 100% bằng Tiếng Việt tự nhiên, chuẩn xác, trong sáng.
- TUYỆT ĐỐI KHÔNG chèn ký tự tiếng Trung/chữ Hán vào câu trả lời tiếng Việt. Dùng các từ tiếng Việt chuẩn tương đương.

Quy tắc ký hiệu toán học trên Terminal:
- Do giao diện hiển thị là Terminal dòng lệnh, KHÔNG dùng các mã LaTeX thô gây rối mắt như \leq, \geq, \in, \forall, \exists, \neq, \infty, \to.
- Hãy dùng trực tiếp ký hiệu toán học Unicode tiêu chuẩn để hiển thị đẹp mắt:
  + So sánh & quan hệ: ≤, ≥, ≠, ≈, ≡
  + Tập hợp & logic: ∈, ∉, ⊂, ⊆, ∪, ∩, ∀, ∃, ⇒
  + Phép toán & vector: ±, ×, ÷, ⋅, ∇, ⊕, ⊗, √
  + Lũy thừa & ma trận: A^T, A^{-1}, x^2, x^3, a_n, a_k
"""

    def __post_init__(self):
        # Ensure data directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)


# Global default settings instance
settings = Settings()
