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
            "stop": ["PROHIBIDO", "SEÑAL", "REGLAS", "máximo", "máxima", "maximo", "punto", "palabras", "words"],
        }
        response = await self._client.post("/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()

    def _build_system_prompt(self) -> str:
        return """Eres un asistente que resume artículos en exactamente 3 puntos clave, primero en español y luego en inglés.

## FORMATO DE RESPUESTA (responde SOLO esto):

## Categories
CATEGORIA1, CATEGORIA2

## English
- [point 1]
- [point 2]
- [point 3]

## Español
- [punto 1]
- [punto 2]
- [punto 3]

## REGLAS
- 2 categorías separadas por coma (ejemplos válidos: AI, Security, Web, Hardware, DevOps, Data, Cloud, Gaming, Mobile, Open Source)
- 3 puntos en inglés
- 3 puntos en español
- Máximo 25 palabras por punto
- No repitas el contenido entre idiomas
- No escribas después del último punto en español
- Sin introducciones ni conclusiones"""

    def _build_user_prompt(self, article: Article, content: str | None = None) -> str:
        url_info = f"\nURL: {article.url}" if article.url else ""
        content_section = f"\n\nContenido del artículo:\n{content}" if content else ""
        return f"""Título: {article.title}{url_info}
Autor: {article.by}
Puntos: {article.score}
Comentarios: {article.descendants}{content_section}"""