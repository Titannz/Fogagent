"""Unit tests for StudyQueue."""
import unittest
import tempfile
from pathlib import Path
from knowledge.study_queue import StudyQueue


class TestStudyQueue(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_queue.db"
        self.queue = StudyQueue(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_and_get_pending(self):
        item_id = self.queue.add_item(
            title="Graph Engineering Paper",
            content="A comprehensive survey on System Intelligence and Graph Engineering.",
            estimated_seconds=180
        )
        self.assertGreater(item_id, 0)
        self.assertEqual(self.queue.count_pending(), 1)

        pending = self.queue.get_pending()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["title"], "Graph Engineering Paper")
        self.assertEqual(pending[0]["status"], "pending")

    def test_mark_completed(self):
        item_id = self.queue.add_item(title="Task A", content="Content A")
        self.assertTrue(self.queue.mark_completed(item_id))
        self.assertEqual(self.queue.count_pending(), 0)

        item = self.queue.get_item(item_id)
        self.assertEqual(item["status"], "completed")

    def test_remove_item(self):
        item_id = self.queue.add_item(title="Task B", content="Content B")
        self.assertTrue(self.queue.remove_item(item_id))
        self.assertEqual(self.queue.count_pending(), 0)
        self.assertIsNone(self.queue.get_item(item_id))


if __name__ == "__main__":
    unittest.main()
