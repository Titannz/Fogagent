"""Ollama Model Client Wrapper."""
from typing import Generator, List, Dict, Any, Optional
import logging
import ollama
from config.settings import settings, Settings

logger = logging.getLogger(__name__)


class OllamaModel:
    """Wrapper for Ollama LLM interactions with streaming and options support."""

    def __init__(self, model: Optional[str] = None, app_settings: Optional[Settings] = None):
        self.settings = app_settings or settings
        self.model = model or self.settings.model_name
        self.client = ollama.Client(host=self.settings.ollama_host, timeout=self.settings.request_timeout)

    def _build_options(self, num_ctx: Optional[int] = None, temperature: Optional[float] = None) -> Dict[str, Any]:
        """Build options dictionary for Ollama inference."""
        return {
            "num_ctx": num_ctx if num_ctx is not None else self.settings.context_length,
            "temperature": temperature if temperature is not None else self.settings.temperature,
        }

    def generate(
        self,
        messages: List[Dict[str, str]],
        num_ctx: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Synchronously generate a complete response from Ollama."""
        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options=self._build_options(num_ctx=num_ctx, temperature=temperature),
                stream=False
            )
            return response.message.content
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise

    def generate_stream(
        self,
        messages: List[Dict[str, str]],
        num_ctx: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Generator[str, None, None]:
        """Stream response tokens chunk-by-chunk from Ollama."""
        try:
            stream = self.client.chat(
                model=self.model,
                messages=messages,
                options=self._build_options(num_ctx=num_ctx, temperature=temperature),
                stream=True
            )
            for chunk in stream:
                content = chunk.message.content
                if content:
                    yield content
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise
