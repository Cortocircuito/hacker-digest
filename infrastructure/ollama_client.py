import asyncio
import logging
import shutil
import subprocess
import sys

import httpx

from domain.entities import Article
from domain.services import SummarizerPort

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "gemma2:2b"


def check_ollama_installed() -> None:
    """Check if Ollama is installed on the system. Exits with an error if not."""
    if shutil.which("ollama") is None:
        print(
            "Error: Ollama is not installed or not found in PATH.\n"
            "Please install it from https://ollama.com and try again."
        )
        sys.exit(1)


class OllamaClient(SummarizerPort):
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._model = model
        self._client = client or httpx.AsyncClient(
            base_url=OLLAMA_BASE_URL,
            timeout=120.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "OllamaClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def ensure_model(self) -> None:
        """Check if the model exists locally; pull it if it does not."""
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("Failed to connect to Ollama: %s", e)
            print(
                "Error: Could not connect to Ollama. Is it running?\n"
                "Start it with: ollama serve"
            )
            sys.exit(1)

        data = response.json()
        if not isinstance(data, dict) or not isinstance(data.get("models"), list):
            raise ValueError("Invalid model list response from Ollama")
        available = {
            name
            for model in data["models"]
            if isinstance(model, dict)
            if isinstance(name := model.get("name"), str)
        }

        if not self._is_model_available(available):
            print(f"Model '{self._model}' not found locally. Pulling it now...")
            try:
                await asyncio.to_thread(
                    subprocess.run,
                    ["ollama", "pull", self._model],
                    check=True,
                )
                print(f"Model '{self._model}' pulled successfully.")
            except subprocess.CalledProcessError as e:
                logger.error("Failed to pull model '%s': %s", self._model, e)
                print(f"Error: Failed to pull model '{self._model}'")
                sys.exit(1)

    def _is_model_available(self, available: set[str]) -> bool:
        if self._model in available:
            return True
        return ":" not in self._model and f"{self._model}:latest" in available

    async def summarize(self, article: Article, content: str | None = None) -> str:
        system_prompt = self._build_system_prompt(article)
        user_prompt = self._build_user_prompt(article, content)
        payload = {
            "model": self._model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "stop": ["## FORMATO", "FORMATO:", "## RULES", "RULES:", "## FORMAT", "FORMAT:"],
        }
        response = await self._client.post("/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()

    def _build_system_prompt(self, article: Article) -> str:
        return f"""Eres un resumidor experto. Resume el siguiente artículo siguiendo exactamente este formato:

ESPAÑOL:
[resumen conciso en español]

ENGLISH:
[concise summary in english]

REGLAS:
- 2-3 oraciones por idioma (aprox 20-40 palabras)
- No incluyas palabras como "Este artículo trata de..." o "In summary..."
- Usa solo información del artículo proporcionado
- Si se proporciona contenido del artículo, úsalo para hacer el resumen más específico
- Si solo tienes el título, basa tu resumen únicamente en él
- NO agregues información externa ni conclusiones
- Responde ÚNICAMENTE con el formato de arriba, nada más"""

    def _build_user_prompt(self, article: Article, content: str | None = None) -> str:
        content_section = f"\n\n{content}" if content else ""
        return f"""Title: {article.title}{content_section}"""
