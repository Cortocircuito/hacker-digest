import asyncio

import httpx

from domain.entities import Article
from domain.services import HackerNewsPort


HN_BASE_URL = "https://hacker-news.firebaseio.com/v0"


class HNClient(HackerNewsPort):
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(
            base_url=HN_BASE_URL,
            timeout=30.0,
        )

    async def get_top_stories(self, limit: int = 10) -> list[Article]:
        response = await self._client.get("/topstories.json")
        response.raise_for_status()
        story_ids: list[int] = response.json()[:limit]

        tasks = [self.get_article(story_id) for story_id in story_ids]
        articles = await asyncio.gather(*tasks, return_exceptions=True)
        return [a for a in articles if isinstance(a, Article)]

    async def get_article(self, article_id: int) -> Article:
        response = await self._client.get(f"/item/{article_id}.json")
        response.raise_for_status()
        data = response.json()
        return Article(
            id=data["id"],
            title=data.get("title", ""),
            url=data.get("url"),
            by=data.get("by", ""),
            score=data.get("score", 0),
            time=data.get("time", 0),
            descendants=data.get("descendants", 0),
        )
