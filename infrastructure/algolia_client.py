import logging
from datetime import date, datetime, time, timezone
from typing import Any

import httpx

from domain.entities import Article
from domain.services import HackerNewsPort


logger = logging.getLogger(__name__)

ALGOLIA_BASE_URL = "https://hn.algolia.com"
HITS_PER_PAGE = 1_000


class AlgoliaClient(HackerNewsPort):
    """Retrieves stories submitted to Hacker News on one UTC calendar day."""

    def __init__(
        self, story_date: date, client: httpx.AsyncClient | None = None
    ) -> None:
        self._story_date = story_date
        self._client = client or httpx.AsyncClient(
            base_url=ALGOLIA_BASE_URL,
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AlgoliaClient":
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        await self.close()

    async def get_top_stories(self, limit: int = 10) -> list[Article]:
        start, end = self._day_bounds()
        articles: dict[int, Article] = {}
        page = 0
        page_count: int | None = None

        while page_count is None or page < page_count:
            response = await self._client.get(
                "/api/v1/search",
                params={
                    "tags": "story",
                    "numericFilters": (
                        f"created_at_i>={start},created_at_i<{end}"
                    ),
                    "hitsPerPage": HITS_PER_PAGE,
                    "page": page,
                },
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("Invalid search response from Algolia")

            hits = data.get("hits")
            response_page_count = data.get("nbPages")
            if (
                not isinstance(hits, list)
                or not isinstance(response_page_count, int)
                or isinstance(response_page_count, bool)
                or response_page_count < 0
            ):
                raise ValueError("Invalid search response from Algolia")
            if page_count is None:
                page_count = response_page_count
            elif response_page_count != page_count:
                raise ValueError("Algolia page count changed during search")

            for hit in hits:
                article = self._article_from_hit(hit, start, end)
                if article is not None:
                    articles[article.id] = article
            page += 1

        ranked = sorted(
            articles.values(),
            key=lambda article: (-article.score, -article.descendants, article.id),
        )
        return ranked[:limit]

    def _day_bounds(self) -> tuple[int, int]:
        start = datetime.combine(self._story_date, time.min, tzinfo=timezone.utc)
        end = datetime.combine(
            self._story_date.fromordinal(self._story_date.toordinal() + 1),
            time.min,
            tzinfo=timezone.utc,
        )
        return int(start.timestamp()), int(end.timestamp())

    def _article_from_hit(
        self, hit: object, start: int, end: int
    ) -> Article | None:
        if not isinstance(hit, dict):
            logger.warning("Ignoring invalid Algolia hit")
            return None

        article_id = self._integer(hit.get("objectID"))
        created_at = self._integer(hit.get("created_at_i"))
        title = hit.get("title")
        if article_id is None or created_at is None or not isinstance(title, str):
            logger.warning("Ignoring incomplete Algolia story")
            return None
        if not start <= created_at < end:
            logger.warning("Ignoring Algolia story outside requested day: %d", article_id)
            return None

        url = hit.get("url")
        author = hit.get("author")
        return Article(
            id=article_id,
            title=title,
            url=url if isinstance(url, str) else None,
            by=author if isinstance(author, str) else "",
            score=self._integer(hit.get("points")) or 0,
            time=created_at,
            descendants=self._integer(hit.get("num_comments")) or 0,
        )

    @staticmethod
    def _integer(value: Any) -> int | None:
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return None
