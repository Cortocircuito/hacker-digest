import asyncio
import logging

import httpx

from domain.entities import Article
from domain.services import HackerNewsPort

logger = logging.getLogger(__name__)

HN_BASE_URL = "https://hacker-news.firebaseio.com/v0"


class HNClient(HackerNewsPort):
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(
            base_url=HN_BASE_URL,
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "HNClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def get_top_stories(self, limit: int = 10) -> list[Article]:
        response = await self._client.get("/topstories.json")
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list) or not all(
            isinstance(story_id, int) and not isinstance(story_id, bool)
            for story_id in data
        ):
            raise ValueError("Invalid top stories response from Hacker News")
        story_ids = data[:limit]

        tasks = [self.get_article(story_id) for story_id in story_ids]
        articles = await asyncio.gather(*tasks, return_exceptions=True)
        valid: list[Article] = []
        for story_id, result in zip(story_ids, articles):
            if isinstance(result, Article):
                valid.append(result)
            elif isinstance(result, Exception):
                logger.warning("Failed to fetch article %d: %s", story_id, result)
        return valid

    async def get_article(self, article_id: int) -> Article:
        response = await self._client.get(f"/item/{article_id}.json")
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or not isinstance(data.get("id"), int):
            raise ValueError(f"Invalid article data for id {article_id}")
        return Article(
            id=data["id"],
            title=data.get("title", ""),
            url=data.get("url"),
            by=data.get("by", ""),
            score=data.get("score", 0),
            time=data.get("time", 0),
            descendants=data.get("descendants", 0),
        )
