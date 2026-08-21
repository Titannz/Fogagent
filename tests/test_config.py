"""Unit tests for Settings and Configuration."""
import unittest
from pathlib import Path
from config.settings import Settings, settings


class TestSettings(unittest.TestCase):

    def test_default_paths(self):
        self.assertIsInstance(settings.base_dir, Path)
        self.assertTrue(settings.data_dir.exists())
        self.assertTrue(settings.memory_dir.exists())
        self.assertTrue(settings.knowledge_dir.exists())

    def test_default_model_parameters(self):
        self.assertEqual(settings.model_name, "qwen3:8b")
        self.assertEqual(settings.context_length, 8192)
        self.assertGreater(settings.temperature, 0.0)

    def test_custom_settings(self):
        custom = Settings(model_name="custom:test", context_length=4096)
        self.assertEqual(custom.model_name, "custom:test")
        self.assertEqual(custom.context_length, 4096)


if __name__ == "__main__":
    unittest.main()
