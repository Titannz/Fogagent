"""Unit tests for DataCleaner and Quality Gate."""
import unittest
from knowledge.data_cleaner import DataCleaner


class TestDataCleaner(unittest.TestCase):

    def setUp(self):
        self.cleaner = DataCleaner(min_confidence=0.85, min_words=4)

    def test_noise_detection_greetings_and_chatter(self):
        self.assertTrue(self.cleaner.is_noise_or_trivial("chào bạn"))
        self.assertTrue(self.cleaner.is_noise_or_trivial("hello there"))
        self.assertTrue(self.cleaner.is_noise_or_trivial("alo"))
        self.assertTrue(self.cleaner.is_noise_or_trivial("ok bạn"))
        self.assertTrue(self.cleaner.is_noise_or_trivial("cảm ơn nhiều"))
        self.assertTrue(self.cleaner.is_noise_or_trivial("thời tiết hôm nay thế nào"))

    def test_valid_technical_content_not_noise(self):
        text = "Transformer architecture relies on self-attention mechanisms to process sequential data in parallel."
        self.assertFalse(self.cleaner.is_noise_or_trivial(text))

    def test_validate_candidate_confidence_threshold(self):
        candidate_low = {
            "topic": "LoRA",
            "content": "Low Rank Adaptation fine-tunes models efficiently.",
            "confidence": 0.70
        }
        valid, reason = self.cleaner.validate_candidate(candidate_low)
        self.assertFalse(valid)
        self.assertIn("below the required threshold", reason)

        candidate_high = {
            "topic": "LoRA",
            "content": "Low Rank Adaptation fine-tunes models efficiently.",
            "confidence": 0.92
        }
        valid, reason = self.cleaner.validate_candidate(candidate_high)
        self.assertTrue(valid)
        self.assertEqual(reason, "Valid")

    def test_check_duplicate_detection(self):
        existing = [
            {
                "id": 1,
                "topic": "FlashAttention",
                "content": "An IO-aware exact attention algorithm that accelerates Transformer execution."
            }
        ]
        # Near duplicate
        result = self.cleaner.check_duplicate_or_conflict(
            "FlashAttention",
            "An IO-aware exact attention algorithm that accelerates Transformer training and inference.",
            existing
        )
        self.assertEqual(result["status"], "DUPLICATE")
        self.assertEqual(result["existing_id"], 1)

        # New topic
        new_result = self.cleaner.check_duplicate_or_conflict(
            "DeepSeek V3",
            "A Multi-Head Latent Attention model with Mixture of Experts architecture.",
            existing
        )
        self.assertEqual(new_result["status"], "NEW")


if __name__ == "__main__":
    unittest.main()
