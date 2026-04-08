import shutil
import subprocess
import sys

import httpx

from domain.entities import Article
from domain.services import SummarizerPort


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

    async def ensure_model(self) -> None:
        """Check if the model exists locally; pull it if it does not."""
        response = await self._client.get("/api/tags")
        response.raise_for_status()
        data = response.json()
        available = {m["name"] for m in data.get("models", [])}

        # Normalise: Ollama may store tags as "gemma2:2b" or without tag as "gemma2"
        model_name = self._model
        model_base = model_name.split(":")[0]
        exists = any(
            name == model_name or name.split(":")[0] == model_base
            for name in available
        )

        if not exists:
            print(f"Model '{self._model}' not found locally. Pulling it now…")
            subprocess.run(["ollama", "pull", self._model], check=True)
            print(f"Model '{self._model}' pulled successfully.")

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
        url_info = article.url if article.url else "N/A"
        return f"""Eres un resumidor conciso. Resume el siguiente artículo en un párrafo detallado.

Primero en ESPAÑOL (máximo 30 palabras), luego en ENGLISH (máximo 30 palabras).

## FORMATO:
ESPAÑOL:
[resumen en español]

ENGLISH:
[summary in english]

## CONTEXTO:
Título: {article.title}
Autor: {article.by} | Puntos: {article.score} | Comentarios: {article.descendants}
URL: {url_info}

## REGLAS:
- Máximo 30 palabras por idioma
- Sin conclusiones
- Sin texto introductorio, empieza directamente con el resumen
- Solo el formato de arriba"""

    def _build_user_prompt(self, article: Article, content: str | None = None) -> str:
        content_section = f"\n\n{content}" if content else ""
        return f"""Title: {article.title}{content_section}"""
