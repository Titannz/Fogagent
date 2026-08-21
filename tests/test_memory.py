"""Unit tests for MemoryManager."""
import unittest
import tempfile
from pathlib import Path
from memory.memory_manager import MemoryManager


class TestMemoryManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_memory.db"
        self.mgr = MemoryManager(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_remember_and_recall_fact(self):
        self.mgr.remember_fact("user_name", "Titannz", category="profile")
        self.assertEqual(self.mgr.recall_fact("user_name"), "Titannz")
        self.assertIsNone(self.mgr.recall_fact("non_existent"))

    def test_update_existing_fact(self):
        self.mgr.remember_fact("favorite_language", "Python")
        self.assertEqual(self.mgr.recall_fact("favorite_language"), "Python")
        self.mgr.remember_fact("favorite_language", "Rust")
        self.assertEqual(self.mgr.recall_fact("favorite_language"), "Rust")
        self.assertEqual(self.mgr.count_memories(), 1)

    def test_forget_fact(self):
        self.mgr.remember_fact("temp_task", "Clean code")
        self.assertTrue(self.mgr.forget_fact("temp_task"))
        self.assertIsNone(self.mgr.recall_fact("temp_task"))
        self.assertFalse(self.mgr.forget_fact("temp_task"))

    def test_search_memories(self):
        self.mgr.remember_fact("gpu_model", "Radeon 780M", category="hardware")
        self.mgr.remember_fact("cpu_model", "Ryzen 7", category="hardware")
        results = self.mgr.search_memories("780M")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["key"], "gpu_model")

    def test_conversation_history(self):
        self.mgr.save_message("user", "Hello")
        self.mgr.save_message("assistant", "Hi there!")
        self.mgr.save_message("user", "How are you?")
        self.mgr.save_message("assistant", "I am good!")

        history = self.mgr.get_recent_history(limit=2)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["content"], "How are you?")
        self.assertEqual(history[1]["content"], "I am good!")

        self.mgr.clear_history()
        self.assertEqual(len(self.mgr.get_recent_history(limit=10)), 0)


if __name__ == "__main__":
    unittest.main()
