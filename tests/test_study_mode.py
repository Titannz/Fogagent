"""Unit tests for StudyEngine and controlled Study Mode learning."""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from knowledge.knowledge_manager import KnowledgeManager
from models.ollama_model import OllamaModel
from agent.study_engine import StudyEngine


class TestStudyEngine(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_study.db"
        self.knowledge_mgr = KnowledgeManager(db_path=self.db_path)
        self.mock_llm = MagicMock(spec=OllamaModel)
        self.engine = StudyEngine(llm=self.mock_llm, knowledge_mgr=self.knowledge_mgr)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_evaluate_and_extract_valid_knowledge(self):
        self.mock_llm.generate.return_value = """
        {
            "is_knowledge": true,
            "topic": "FlashAttention",
            "content": "FlashAttention is an IO-aware exact attention algorithm that accelerates Transformer training and inference.",
            "tags": ["transformer", "attention", "gpu"],
            "confidence": 0.95
        }
        """
        result = self.engine.evaluate_and_extract("FlashAttention is an exact attention algorithm.")
        self.assertIsNotNone(result)
        self.assertEqual(result["topic"], "FlashAttention")
        self.assertEqual(self.knowledge_mgr.count_knowledge(), 1)

    def test_evaluate_ignores_casual_chat(self):
        self.mock_llm.generate.return_value = """
        {
            "is_knowledge": false,
            "topic": "",
            "content": "",
            "tags": [],
            "confidence": 0.0
        }
        """
        result = self.engine.evaluate_and_extract("Hello, how are you today?")
        self.assertIsNone(result)
        self.assertEqual(self.knowledge_mgr.count_knowledge(), 0)


if __name__ == "__main__":
    unittest.main()
