"""FogAgent Core Implementation with Quality Control, Study Queue, and Human-in-the-Loop."""
from typing import Generator, List, Dict, Optional, Any
import logging
from config.settings import settings, Settings
from models.ollama_model import OllamaModel
from memory.memory_manager import MemoryManager
from knowledge.knowledge_manager import KnowledgeManager
from knowledge.study_queue import StudyQueue
from knowledge.math_formatter import format_math_symbols
from agent.study_engine import StudyEngine

logger = logging.getLogger(__name__)


class Agent:
    """Core AI Agent managing state, Memory, Knowledge, Study Queue, and controlled LLM execution."""

    def __init__(
        self,
        llm: Optional[OllamaModel] = None,
        memory_mgr: Optional[MemoryManager] = None,
        knowledge_mgr: Optional[KnowledgeManager] = None,
        study_queue: Optional[StudyQueue] = None,
        app_settings: Optional[Settings] = None
    ):
        self.settings = app_settings or settings
        self.llm = llm or OllamaModel(app_settings=self.settings)
        self.memory_mgr = memory_mgr or MemoryManager(db_path=self.settings.memory_db_path)
        self.knowledge_mgr = knowledge_mgr or KnowledgeManager(db_path=self.settings.knowledge_db_path)
        self.study_queue = study_queue or StudyQueue(db_path=(self.settings.knowledge_dir / "study_queue.db"))
        self.study_engine = StudyEngine(llm=self.llm, knowledge_mgr=self.knowledge_mgr)

        self.study_mode: bool = False
        self.system_prompt: str = self.settings.system_prompt

    def enable_study(self) -> str:
        """Enable Study Mode (allows agent to learn new knowledge)."""
        self.study_mode = True
        logger.info("Study Mode enabled.")
        return "Study Mode: ON"

    def disable_study(self) -> str:
        """Disable Study Mode (disables learning, retains stored knowledge)."""
        self.study_mode = False
        logger.info("Study Mode disabled.")
        return "Study Mode: OFF"

    def get_status(self) -> Dict[str, Any]:
        """Return current status dictionary of the agent."""
        return {
            "model": self.llm.model,
            "study_mode": self.study_mode,
            "context_length": self.settings.context_length,
            "ollama_host": self.settings.ollama_host,
            "total_memories": self.memory_mgr.count_memories(),
            "total_knowledge": self.knowledge_mgr.count_knowledge(),
            "pending_study_queue": self.study_queue.count_pending()
        }

    def estimate_workload(self, text: str) -> Dict[str, Any]:
        """Estimate workload and processing time for input."""
        return self.study_engine.estimate_workload(text)

    def extract_study_candidate(self, text: str, source: str = "user_study") -> Optional[Dict[str, Any]]:
        """Extract and clean a knowledge candidate (requires human approval before commit)."""
        if not self.study_mode:
            return None
        return self.study_engine.evaluate_and_extract(text, source=source)

    def commit_study_candidate(self, candidate: Dict[str, Any]) -> int:
        """Commit an approved candidate into the Knowledge Base."""
        return self.study_engine.commit_knowledge(candidate)

    def queue_study_item(self, title: str, content: str, estimated_seconds: int = 60) -> int:
        """Save study material into the deferred queue for later processing."""
        return self.study_queue.add_item(title=title, content=content, estimated_seconds=estimated_seconds)

    def build_context_prompt(self, user_input: str) -> str:
        """Retrieve relevant memories and knowledge to augment the system prompt."""
        context_parts = [self.system_prompt]

        # 1. Retrieve relevant memories (facts/preferences/profile)
        relevant_memories = self.memory_mgr.search_memories(user_input, limit=3)
        if relevant_memories:
            mem_text = "\n".join([f"- {m['key']}: {m['value']}" for m in relevant_memories])
            context_parts.append(f"\n[Relevant User Context/Memory]:\n{mem_text}")

        # 2. Retrieve relevant knowledge
        relevant_knowledge = self.knowledge_mgr.search_knowledge(user_input, limit=3)
        if relevant_knowledge:
            know_text = "\n".join([f"- [{k['topic']}]: {k['content']}" for k in relevant_knowledge])
            context_parts.append(f"\n[Relevant Learned Knowledge]:\n{know_text}")

        # 3. Add Study Mode status instruction
        if self.study_mode:
            context_parts.append("\n[Study Mode: ON] You are currently permitted to study and learn new factual information.")
        else:
            context_parts.append("\n[Study Mode: OFF] Learning is currently disabled. Answer using existing knowledge.")

        return "\n".join(context_parts)

    def build_messages(self, user_input: str) -> List[Dict[str, str]]:
        """Construct prompt messages including system prompt, augmented context, and recent history."""
        system_content = self.build_context_prompt(user_input)
        messages = [{"role": "system", "content": system_content}]

        # Inject recent conversation turns (short-term memory)
        recent_history = self.memory_mgr.get_recent_history(limit=6)
        messages.extend(recent_history)

        # Add the current user query
        messages.append({"role": "user", "content": user_input})
        return messages

    def run(self, user_input: str) -> str:
        """Execute a synchronous prompt through the Agent."""
        messages = self.build_messages(user_input)
        response = self.llm.generate(messages)
        response = format_math_symbols(response)

        # Persist conversation turn in short-term history
        self.memory_mgr.save_message("user", user_input)
        self.memory_mgr.save_message("assistant", response)
        return response

    def run_stream(self, user_input: str) -> Generator[str, None, None]:
        """Execute a streaming prompt yielding response tokens with formatted math symbols."""
        messages = self.build_messages(user_input)
        full_response = []
        buffer = ""

        for chunk in self.llm.generate_stream(messages):
            buffer += chunk
            # If buffer contains backslash command, wait for word boundary before yielding
            if "\\" in buffer:
                # If command terminated by space, newline, or punctuation, format & yield
                if any(c in buffer.split("\\")[-1] for c in (" ", "\n", "$", "{", "}", "(", ")", ",", ".")):
                    formatted = format_math_symbols(buffer)
                    yield formatted
                    full_response.append(formatted)
                    buffer = ""
            else:
                yield buffer
                full_response.append(buffer)
                buffer = ""

        if buffer:
            formatted = format_math_symbols(buffer)
            yield formatted
            full_response.append(formatted)

        # Persist conversation turn in short-term history
        full_text = "".join(full_response)
        self.memory_mgr.save_message("user", user_input)
        self.memory_mgr.save_message("assistant", full_text)
