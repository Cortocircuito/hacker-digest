import httpx

from domain.entities import Article
from domain.services import SummarizerPort


OLLAMA_BASE_URL = "http://localhost:11434"


class OllamaClient(SummarizerPort):
    def __init__(
        self,
        model: str = "gemma2:2b",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._model = model
        self._client = client or httpx.AsyncClient(
            base_url=OLLAMA_BASE_URL,
            timeout=120.0,
        )

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