"""Data Cleaner & Quality Gatekeeper for FogAgent."""
import re
from typing import Dict, Any, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Common casual/chatter or question/command patterns that are not study facts
TRIVIAL_PATTERNS = [
    r"^(xin\s+)?chào(\s+bạn|\s+cậu|\s+nhé|\s+ạ)?$",
    r"^(hi|hello|hey|alo|ê|ơi)(\s+there)?$",
    r"^bạn\s+(là\s+ai|tên\s+gì|khỏe\s+không|làm\s+được\s+gì)\??$",
    r"^cảm\s+ơn(\s+nhé|\s+bạn|\s+nhiều)?$",
    r"^(ok|ừ|ừm|okie|yes|no|được|rồi)(\s+bạn)?$",
    r"^thời\s+tiết.*hôm\s+nay.*$",
    r"^kể\s+cho\s+tôi\s+nghe\s+truyện\s+cười.*$",
    r"^(cho\s+tôi|hãy|tại\s+sao|như\s+thế\s+nào|là\s+gì|có\s+phải|ví\s+dụ|giải\s+thích|chỉ\s+cho|hỏi|xin|làm\s+sao|thế\s+nào|đâu\s+là|bao\s+nhiêu).*",
    r"^.*\?$",
    r"^(what|how|why|can\s+you|could\s+you|please|give\s+me|explain|tell\s+me|show\s+me).*",
]


class DataCleaner:
    """Sanitizes text, filters noise, checks confidence thresholds, and detects duplicates."""

    def __init__(self, min_confidence: float = 0.85, min_words: int = 4):
        self.min_confidence = min_confidence
        self.min_words = min_words

    def is_noise_or_trivial(self, text: str) -> bool:
        """Check if input is trivial chatter, casual greeting, or meaningless noise."""
        clean = text.strip().lower()
        if not clean or len(clean.split()) < self.min_words:
            # Very short text (< 4 words) is rarely a complete domain fact
            for pat in TRIVIAL_PATTERNS:
                if re.match(pat, clean):
                    return True
            if len(clean.split()) <= 2:
                return True

        for pat in TRIVIAL_PATTERNS:
            if re.match(pat, clean):
                return True

        return False

    def validate_candidate(self, candidate: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate an extracted knowledge candidate against quality standards."""
        if not candidate:
            return False, "Candidate is empty."

        topic = candidate.get("topic", "").strip()
        content = candidate.get("content", "").strip()
        confidence = float(candidate.get("confidence", 0.0))

        if not topic or len(topic) < 2:
            return False, "Topic is missing or too short."

        if not content or len(content.split()) < 3:
            return False, "Content is missing or contains insufficient detail."

        if confidence < self.min_confidence:
            return False, f"Confidence score ({confidence:.2f}) is below the required threshold ({self.min_confidence:.2f})."

        return True, "Valid"

    def check_duplicate_or_conflict(
        self,
        topic: str,
        content: str,
        existing_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check whether candidate topic/content already exists or conflicts with stored facts."""
        topic_lower = topic.strip().lower()
        content_lower = content.strip().lower()

        for rec in existing_records:
            rec_topic = rec.get("topic", "").lower()
            rec_content = rec.get("content", "").lower()

            # Exact topic match
            if topic_lower == rec_topic:
                # Check content similarity by word overlap
                words_new = set(content_lower.split())
                words_old = set(rec_content.split())
                if words_new and words_old:
                    overlap = len(words_new & words_old) / min(len(words_new), len(words_old))
                    if overlap > 0.7:
                        return {
                            "status": "DUPLICATE",
                            "existing_id": rec["id"],
                            "message": f"Tri thức này đã tồn tại ở bản ghi #{rec['id']} ({rec['topic']})."
                        }
                    else:
                        return {
                            "status": "POTENTIAL_UPDATE",
                            "existing_id": rec["id"],
                            "message": f"Cùng chủ đề #{rec['id']} nhưng nội dung có chi tiết mới."
                        }

        return {"status": "NEW", "message": "Tri thức hoàn toàn mới."}
