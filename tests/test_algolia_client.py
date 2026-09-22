from datetime import date, datetime, time, timezone

import httpx
import pytest

from infrastructure.algolia_client import ALGOLIA_BASE_URL, AlgoliaClient


def _timestamp(story_date: date) -> int:
    return int(datetime.combine(story_date, time.min, tzinfo=timezone.utc).timestamp())


def _hit(article_id: int, created_at: int, points: int) -> dict[str, object]:
    return {
        "objectID": str(article_id),
        "title": f"Story {article_id}",
        "url": f"https://example.com/{article_id}",
        "author": "tester",
        "points": points,
        "created_at_i": created_at,
        "num_comments": article_id,
    }


@pytest.mark.asyncio
async def test_algolia_client_fetches_all_pages_and_ranks_stories() -> None:
    story_date = date(2026, 9, 10)
    start = _timestamp(story_date)
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        page = request.url.params["page"]
        if page == "0":
            return httpx.Response(
                200,
                json={
                    "nbPages": 2,
                    "hits": [
                        _hit(1, start, 5),
                        _hit(2, start + 60, 20),
                        _hit(99, start - 1, 100),
                    ],
                },
            )
        return httpx.Response(
            200,
            json={
                "nbPages": 2,
                "hits": [
                    _hit(3, start + 120, 20),
                    _hit(1, start, 10),
                ],
            },
        )

    async with httpx.AsyncClient(
        base_url=ALGOLIA_BASE_URL,
        transport=httpx.MockTransport(handler),
    ) as http_client:
        client = AlgoliaClient(story_date, http_client)
        articles = await client.get_top_stories(limit=3)

    assert [article.id for article in articles] == [3, 2, 1]
    assert articles[-1].score == 10
    assert len(requests) == 2
    assert requests[0].url.path == "/api/v1/search"
    assert requests[0].url.params["tags"] == "story"
    assert requests[0].url.params["numericFilters"] == (
        f"created_at_i>={start},created_at_i<{start + 86_400}"
    )


@pytest.mark.asyncio
async def test_algolia_client_rejects_invalid_response() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"hits": "not a list"})

    async with httpx.AsyncClient(
        base_url=ALGOLIA_BASE_URL,
        transport=httpx.MockTransport(handler),
    ) as http_client:
        client = AlgoliaClient(date(2026, 9, 10), http_client)
        with pytest.raises(ValueError, match="Invalid search response"):
            await client.get_top_stories()


@pytest.mark.asyncio
async def test_algolia_client_context_manager_closes_owned_client() -> None:
    async with AlgoliaClient(date(2026, 9, 10)) as client:
        http_client = client._client

    assert http_client.is_closed
