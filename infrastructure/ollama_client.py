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
        system_prompt = self._build_system_prompt(article)
        user_prompt = self._build_user_prompt(article, content)
        payload = {
            "model": self._model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "stop": ["PROHIBIDO", "SEÑAL", "RULES", "máximo", "máxima", "maximo", "punto", "palabras", "words", "CATEGORY", "Categories"],
        }
        response = await self._client.post("/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()

    def _build_system_prompt(self, article: Article) -> str:
        url_info = article.url if article.url else "N/A"
        return f"""Act as an expert in information synthesis.
        
Summarize the following text, extracting the 5 main ideas in bullet points.
You summarize into exactly 5 key points, first show that 5 key points in English then show again that 5 key point in Spanish.
At the end of each language provide a one-paragraph conclusion

## CONTEXT:
Author: {article.by}
Score: {article.score}
Comments: {article.descendants}
URL: {url_info}

## OUTPUT FORMAT (respond ONLY this):

## Categories
CATEGORY1, CATEGORY2

## English
- [point 1]
- [point 2]
- [point 3]

## Español
- [punto 1]
- [punto 2]
- [punto 3]

## RULES
- 2 comma-separated categories from: AI, Security, Web, Hardware, DevOps, Data, Cloud, Gaming, Mobile, Open Source, Privacy, APIs, Tools, Learning
- 3 English points
- 3 Spanish points
- Max 25 words per point
- No content repetition between languages
- Stop after last Spanish conclusion
- No introductions"""

    def _build_user_prompt(self, article: Article, content: str | None = None) -> str:
        content_section = f"\n\n{content}" if content else ""
        return f"""Title: {article.title}{content_section}"""