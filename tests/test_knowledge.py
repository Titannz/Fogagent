"""Unit tests for KnowledgeManager."""
import unittest
import tempfile
from pathlib import Path
from knowledge.knowledge_manager import KnowledgeManager


class TestKnowledgeManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_knowledge.db"
        self.mgr = KnowledgeManager(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_and_get_knowledge(self):
        record_id = self.mgr.add_knowledge(
            topic="LoRA",
            content="Low-Rank Adaptation is a parameter-efficient fine-tuning technique.",
            source="test",
            confidence=0.95,
            tags=["llm", "fine-tuning", "ml"]
        )
        self.assertGreater(record_id, 0)
        item = self.mgr.get_by_id(record_id)
        self.assertIsNotNone(item)
        self.assertEqual(item["topic"], "LoRA")
        self.assertIn("parameter-efficient", item["content"])
        self.assertEqual(item["confidence"], 0.95)

    def test_search_knowledge(self):
        self.mgr.add_knowledge(
            topic="Transformer",
            content="Self-attention mechanism allows parallel processing of sequence data.",
            tags=["deep-learning", "attention"]
        )
        self.mgr.add_knowledge(
            topic="Vulkan",
            content="A cross-platform 3D graphics and compute API.",
            tags=["gpu", "graphics"]
        )

        results = self.mgr.search_knowledge("attention")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["topic"], "Transformer")

        gpu_results = self.mgr.search_knowledge("compute API")
        self.assertEqual(len(gpu_results), 1)
        self.assertEqual(gpu_results[0]["topic"], "Vulkan")

    def test_delete_and_count(self):
        id1 = self.mgr.add_knowledge(topic="T1", content="C1")
        id2 = self.mgr.add_knowledge(topic="T2", content="C2")
        self.assertEqual(self.mgr.count_knowledge(), 2)

        self.assertTrue(self.mgr.delete_knowledge(id1))
        self.assertEqual(self.mgr.count_knowledge(), 1)


if __name__ == "__main__":
    unittest.main()
