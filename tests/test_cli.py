from io import StringIO
from unittest.mock import AsyncMock

import pytest
from rich.console import Console

from domain.entities import Article
from interface import cli


def _article(url: str | None = "https://example.com/full") -> Article:
    return Article(
        id=123,
        title="An article",
        url=url,
        by="tester",
        score=10,
        time=0,
        descendants=2,
    )


@pytest.mark.asyncio
async def test_run_markdown_writes_actual_count_and_article_links(tmp_path) -> None:
    summarize_article = AsyncMock()
    summarize_article.execute.return_value = [(_article(), "A bilingual summary")]
    filename = tmp_path / "digest.md"

    await cli.run_markdown(
        summarize_article,
        limit=30,
        filename=str(filename),
        source_label="Stories submitted on 2026-09-10 (UTC)",
    )

    content = filename.read_text(encoding="utf-8")
    assert "Stories submitted on 2026-09-10 (UTC); 1 stories" in content
    assert "[Read Full Article](https://example.com/full)" in content
    assert "https://news.ycombinator.com/item?id=123" in content
    summarize_article.execute.assert_awaited_once_with(30)


@pytest.mark.asyncio
async def test_run_markdown_uses_hacker_news_link_when_article_has_no_url(tmp_path) -> None:
    summarize_article = AsyncMock()
    summarize_article.execute.return_value = [(_article(url=None), "summary")]
    filename = tmp_path / "digest.md"

    await cli.run_markdown(summarize_article, 1, str(filename), "Current top stories")

    content = filename.read_text(encoding="utf-8")
    assert "Read Full Article" not in content
    assert "https://news.ycombinator.com/item?id=123" in content
    assert "(None)" not in content


@pytest.mark.asyncio
async def test_run_cli_displays_query_label(monkeypatch) -> None:
    output = StringIO()
    monkeypatch.setattr(cli, "console", Console(file=output, force_terminal=False))
    summarize_article = AsyncMock()
    summarize_article.execute.return_value = []

    await cli.run_cli(
        summarize_article,
        limit=10,
        source_label="Stories submitted on 2026-09-10 (UTC)",
    )

    assert "Stories submitted on 2026-09-10 (UTC)" in output.getvalue()
