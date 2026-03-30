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
            "stop": ["## RULES", "RULES:", "CATEGORIES:", "## FORMAT", "FORMAT:"],
        }
        response = await self._client.post("/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()

    def _build_system_prompt(self, article: Article) -> str:
        url_info = article.url if article.url else "N/A"
        return f"""You are a concise summarizer. Extract exactly 3 key points from the article below.

First list 3 points in ENGLISH, then repeat 3 points in SPANISH.
End with a short 1-sentence conclusion in both languages.

## FORMAT:
ENGLISH:
- 
- 
- 
Conclusion: 

ESPAÑOL:
- 
- 
- 
Conclusión: 

## CATEGORIES:
Choose 2: AI, Security, Web, Hardware, DevOps, Data, Cloud, Gaming, Mobile, Open Source, Privacy, APIs, Tools, Learning

## CONTEXT:
Title: {article.title}
Author: {article.by} | Score: {article.score} | Comments: {article.descendants}
URL: {url_info}

## RULES:
- Each bullet max 20 words
- No repetition between languages
- No intro text, start directly with bullets
- Output only the format above"""

    def _build_user_prompt(self, article: Article, content: str | None = None) -> str:
        content_section = f"\n\n{content}" if content else ""
        return f"""Title: {article.title}{content_section}"""