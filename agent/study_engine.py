"""Study Mode Learning Engine with Quality Gate & Workload Estimator."""
import json
import logging
from typing import Optional, Dict, Any, List
from models.ollama_model import OllamaModel
from knowledge.knowledge_manager import KnowledgeManager
from knowledge.data_cleaner import DataCleaner

logger = logging.getLogger(__name__)


class StudyEngine:
    """Evaluates, sanitizes, and extracts structured knowledge with human approval gating."""

    def __init__(
        self,
        llm: OllamaModel,
        knowledge_mgr: KnowledgeManager,
        cleaner: Optional[DataCleaner] = None
    ):
        self.llm = llm
        self.knowledge_mgr = knowledge_mgr
        self.cleaner = cleaner or DataCleaner(min_confidence=0.85)

    def estimate_workload(self, text: str) -> Dict[str, Any]:
        """
        Estimate workload and processing time for a text/document.
        Assumes ~13 tokens/sec generation speed on local AMD Radeon 780M.
        """
        word_count = len(text.split())
        # Roughly 1.3 tokens per word
        est_tokens = int(word_count * 1.3)
        # Baseline overhead ~10s, plus processing tokens
        est_seconds = max(5, int(est_tokens / 30) + 10)
        is_long_task = word_count > 300 or est_seconds > 45

        return {
            "word_count": word_count,
            "estimated_tokens": est_tokens,
            "estimated_seconds": est_seconds,
            "is_long_task": is_long_task
        }

    def evaluate_and_extract(
        self,
        user_input: str,
        source: str = "user_study"
    ) -> Optional[Dict[str, Any]]:
        """
        Sanitizes input, checks for noise, extracts structured knowledge,
        and returns a candidate for human approval (DOES NOT commit directly).
        """
        # 1. Noise and trivial chatter filtering
        if self.cleaner.is_noise_or_trivial(user_input):
            logger.info("Input filtered out by NoiseFilter (casual/trivial).")
            return None

        prompt = f"""You are a Knowledge Extraction and Evaluation module for FogAgent.
Analyze the following text provided by the user.

Text:
\"\"\"{user_input}\"\"\"

Determine whether this text contains factual, general domain knowledge (e.g., technical concepts, definitions, algorithms, rules, science, architectures, or specific facts) that is worth saving permanently into the Knowledge Base.

Do NOT save:
- Casual greetings, chatter, subjective opinions
- Questions, ephemeral instructions, or trivial chatter
- Dubious or unverified speculation

Respond ONLY with a valid JSON object in this exact schema:
{{
  "is_knowledge": true or false,
  "topic": "Concise topic title (e.g., Transformer Attention, LoRA, Docker Networking)",
  "content": "A clear, well-formulated factual summary of what was learned",
  "tags": ["tag1", "tag2"],
  "confidence": 0.0 to 1.0
}}
Do NOT output any markdown formatting around the JSON. Output pure raw JSON only.
"""
        messages = [
            {"role": "system", "content": "You are a strict JSON-only knowledge extractor."},
            {"role": "user", "content": prompt}
        ]

        try:
            raw_response = self.llm.generate(messages, temperature=0.1)
            raw_response = raw_response.strip()

            # Strip possible markdown code fence ```json ... ```
            if raw_response.startswith("```"):
                lines = raw_response.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_response = "\n".join(lines).strip()

            data = json.loads(raw_response)

            if data.get("is_knowledge") is True and data.get("topic") and data.get("content"):
                candidate = {
                    "topic": str(data["topic"]).strip(),
                    "content": str(data["content"]).strip(),
                    "tags": data.get("tags", []),
                    "confidence": float(data.get("confidence", 0.0)),
                    "source": source
                }
                if isinstance(candidate["tags"], str):
                    candidate["tags"] = [t.strip() for t in candidate["tags"].split(",")]

                # 2. Quality Validation
                is_valid, reason = self.cleaner.validate_candidate(candidate)
                if not is_valid:
                    logger.info(f"Candidate rejected by DataCleaner: {reason}")
                    return None

                # 3. Duplicate and conflict check
                existing = self.knowledge_mgr.list_all(limit=200)
                dup_info = self.cleaner.check_duplicate_or_conflict(
                    candidate["topic"],
                    candidate["content"],
                    existing
                )

                candidate["duplicate_status"] = dup_info["status"]
                candidate["duplicate_msg"] = dup_info["message"]

                return candidate

        except Exception as e:
            logger.warning(f"Study evaluation failed: {e}")

        return None

    def commit_knowledge(self, candidate: Dict[str, Any]) -> int:
        """Commit an approved knowledge candidate into KnowledgeManager."""
        return self.knowledge_mgr.add_knowledge(
            topic=candidate["topic"],
            content=candidate["content"],
            source=candidate.get("source", "user_study"),
            confidence=candidate.get("confidence", 1.0),
            tags=candidate.get("tags", [])
        )
