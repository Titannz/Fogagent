"""Unit tests for StudyEngine, Quality Gate, and controlled Study Mode learning."""
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

    def test_evaluate_and_extract_candidate_for_approval(self):
        self.mock_llm.generate.return_value = """
        {
            "is_knowledge": true,
            "topic": "FlashAttention",
            "content": "FlashAttention is an IO-aware exact attention algorithm that accelerates Transformer training and inference.",
            "tags": ["transformer", "attention", "gpu"],
            "confidence": 0.95
        }
        """
        # 1. Extraction generates a candidate but DOES NOT commit without human approval
        candidate = self.engine.evaluate_and_extract("FlashAttention is an exact attention algorithm.")
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["topic"], "FlashAttention")
        self.assertEqual(candidate["confidence"], 0.95)
        self.assertEqual(self.knowledge_mgr.count_knowledge(), 0)

        # 2. Human approves and commits
        rec_id = self.engine.commit_knowledge(candidate)
        self.assertGreater(rec_id, 0)
        self.assertEqual(self.knowledge_mgr.count_knowledge(), 1)

    def test_evaluate_ignores_casual_chat_via_noise_filter(self):
        # Noise filter catches this upfront without even calling the LLM
        result = self.engine.evaluate_and_extract("Hello, how are you today?")
        self.assertIsNone(result)
        self.assertEqual(self.knowledge_mgr.count_knowledge(), 0)

    def test_workload_estimation(self):
        short_text = "Python is great."
        short_est = self.engine.estimate_workload(short_text)
        self.assertFalse(short_est["is_long_task"])

        long_text = "word " * 400
        long_est = self.engine.estimate_workload(long_text)
        self.assertTrue(long_est["is_long_task"])
        self.assertGreater(long_est["estimated_seconds"], 10)


if __name__ == "__main__":
    unittest.main()
