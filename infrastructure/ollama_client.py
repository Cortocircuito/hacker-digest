import httpx

from domain.entities import Article
from domain.services import SummarizerPort


OLLAMA_BASE_URL = "http://localhost:11434"


class OllamaClient(SummarizerPort):
    def __init__(
        self,
        model: str = "llama3:8b",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._model = model
        self._client = client or httpx.AsyncClient(
            base_url=OLLAMA_BASE_URL,
            timeout=120.0,
        )

    async def summarize(self, article: Article, content: str | None = None) -> str:
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(article, content)
        payload = {
            "model": self._model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
        }
        response = await self._client.post("/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()

    def _build_system_prompt(self) -> str:
        return """Eres un asistente que resume artículos en exactamente 3 puntos clave, primero en español y luego en inglés.

## FORMATO OBLIGATORIO (responde SOLO esto, sin introducir ni concluir):

## Categories
category 1, category 2

## English
- point 1 in English (máximo 15 palabras)
- point 2 in English (máximo 15 palabras)
- point 3 in English (máximo 15 palabras)

## Español
- punto 1 en español (máximo 15 palabras)
- punto 2 en español (máximo 15 palabras)
- punto 3 en español (máximo 15 palabras)

## REGLAS:
- MAXIMO 2 categorías, diferentes entre sí
- MAXIMO 3 puntos por sección
- MAXIMO 15 palabras por punto
- NO escribas nada después del último punto en español
- NO repitas el contenido en otro idioma
- NO agregues introducciones ni conclusiones"""

    def _build_user_prompt(self, article: Article, content: str | None = None) -> str:
        url_info = f"\nURL: {article.url}" if article.url else ""
        content_section = f"\n\nContenido del artículo:\n{content}" if content else ""
        return f"""Título: {article.title}{url_info}
Autor: {article.by}
Puntos: {article.score}
Comentarios: {article.descendants}{content_section}"""