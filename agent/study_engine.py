"""Study Mode Learning Engine for FogAgent."""
import json
import logging
from typing import Optional, Dict, Any, List
from models.ollama_model import OllamaModel
from knowledge.knowledge_manager import KnowledgeManager

logger = logging.getLogger(__name__)


class StudyEngine:
    """Evaluates and extracts structured factual knowledge during Study Mode."""

    def __init__(self, llm: OllamaModel, knowledge_mgr: KnowledgeManager):
        self.llm = llm
        self.knowledge_mgr = knowledge_mgr

    def evaluate_and_extract(self, user_input: str, context: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Analyze user input to determine if it contains new, structured factual knowledge to learn.
        Returns a dict of extracted knowledge or None if not suitable for permanent knowledge storage.
        """
        prompt = f"""You are a Knowledge Extraction and Evaluation module for FogAgent.
Analyze the following text provided by the user.

Text:
\"\"\"{user_input}\"\"\"

Determine whether this text contains factual, general domain knowledge (e.g., technical concepts, definitions, algorithms, rules, science, architectures, or specific facts) that is worth saving permanently into the Knowledge Base.

Do NOT save:
- Casual greetings (e.g. "hi", "how are you")
- Ephemeral instructions or casual questions (e.g. "what time is it", "tell me a joke")
- Trivial opinions or meaningless noise

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
                topic = str(data["topic"]).strip()
                content = str(data["content"]).strip()
                tags = data.get("tags", [])
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(",")]
                confidence = float(data.get("confidence", 0.9))

                # Store into KnowledgeManager
                record_id = self.knowledge_mgr.add_knowledge(
                    topic=topic,
                    content=content,
                    source="study_mode",
                    confidence=confidence,
                    tags=tags
                )

                return {
                    "id": record_id,
                    "topic": topic,
                    "content": content,
                    "tags": tags,
                    "confidence": confidence
                }

        except Exception as e:
            logger.warning(f"Study evaluation failed: {e}")

        return None
