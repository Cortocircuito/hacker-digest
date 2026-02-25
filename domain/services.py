from typing import Protocol

from domain.entities import Article


class HackerNewsPort(Protocol):
    async def get_top_stories(self, limit: int = 10) -> list[Article]: ...


class ArticleContentPort(Protocol):
    async def extract_content(self, url: str) -> str | None: ...


class SummarizerPort(Protocol):
    async def summarize(self, article: Article, content: str | None = None) -> str: ...
