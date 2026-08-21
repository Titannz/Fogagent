"""Unit tests for Agent state, context augmentation, and message building."""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from agent.agent import Agent
from models.ollama_model import OllamaModel
from memory.memory_manager import MemoryManager
from knowledge.knowledge_manager import KnowledgeManager


class TestAgent(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.mem_db = Path(self.temp_dir.name) / "test_mem.db"
        self.know_db = Path(self.temp_dir.name) / "test_know.db"

        self.mock_llm = MagicMock(spec=OllamaModel)
        self.mock_llm.model = "qwen3:8b"

        self.memory_mgr = MemoryManager(db_path=self.mem_db)
        self.knowledge_mgr = KnowledgeManager(db_path=self.know_db)

        self.agent = Agent(
            llm=self.mock_llm,
            memory_mgr=self.memory_mgr,
            knowledge_mgr=self.knowledge_mgr
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_initial_state(self):
        self.assertFalse(self.agent.study_mode)
        status = self.agent.get_status()
        self.assertFalse(status["study_mode"])
        self.assertEqual(status["model"], "qwen3:8b")
        self.assertEqual(status["total_memories"], 0)
        self.assertEqual(status["total_knowledge"], 0)

    def test_study_mode_toggle(self):
        enable_msg = self.agent.enable_study()
        self.assertTrue(self.agent.study_mode)
        self.assertEqual(enable_msg, "Study Mode: ON")

        disable_msg = self.agent.disable_study()
        self.assertFalse(self.agent.study_mode)
        self.assertEqual(disable_msg, "Study Mode: OFF")

    def test_build_messages_with_context(self):
        self.memory_mgr.remember_fact("user_role", "Developer")
        self.knowledge_mgr.add_knowledge(topic="Python", content="Python is a dynamic programming language.")

        messages = self.agent.build_messages("What is my user_role and what do you know about Python?")
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("Developer", messages[0]["content"])
        self.assertIn("Python is a dynamic programming language", messages[0]["content"])
        self.assertEqual(messages[-1]["role"], "user")

    def test_run_saves_conversation_history(self):
        self.mock_llm.generate.return_value = "Mock answer"
        result = self.agent.run("Test question")
        self.assertEqual(result, "Mock answer")

        history = self.memory_mgr.get_recent_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[1]["role"], "assistant")


if __name__ == "__main__":
    unittest.main()
