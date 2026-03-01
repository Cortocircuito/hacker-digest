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
        prompt = self._build_prompt(article, content)
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }
        response = await self._client.post("/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()

    def _build_prompt(self, article: Article, content: str | None = None) -> str:
        url_info = f"\nURL: {article.url}" if article.url else ""
        content_section = f"\n\nContenido del artículo:\n{content}" if content else ""
        return f"""Resume el siguiente artículo en EXACTAMENTE 3 puntos clave.

## REGLAS ESTRICTAS - OBLIGATORIO SEGUIR AL PIE DE LA LETRA:

### FORMATO REQUERIDO (tu respuesta debe seguir esto exactamente):
## English
- point 1 in English (máximo 15 palabras)
- point 2 in English (máximo 15 palabras)
- point 3 in English (máximo 15 palabras)

## Español
- punto 1 en español (máximo 15 palabras)
- punto 2 en español (máximo 15 palabras)
- punto 3 en español (máximo 15 palabras)

### PROHIBIDO ABSOLUTAMENTE:
- ❌ NO agregues contenido después de ## Español
- ❌ NO repitas el contenido en otro idioma (no pongas "Spanish")
- ❌ NO agregues introducciones como "Here's a summary..." o "En resumen..."
- ❌ NO agregues conclusiones o comentarios adicionales
- ❌ NO escribas más de 3 puntos por sección
- ❌ NO pongas más de 15 palabras por punto

### SEÑAL DE PARADA:
TU RESPUESTA DEBE TERMINAR DESPUÉS DEL ÚLTIMO PUNTO EN ESPAÑOL.
NO ESCRIBAS NADA MÁS.

Título: {article.title}{url_info}
Autor: {article.by}
Puntos: {article.score}
Comentarios: {article.descendants}{content_section}
"""