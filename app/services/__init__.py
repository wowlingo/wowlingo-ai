"""External service integrations"""

from app.services.ollama import ollama_client, OllamaClient

__all__ = ["ollama_client", "OllamaClient"]
