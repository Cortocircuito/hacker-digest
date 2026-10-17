from io import StringIO
from unittest.mock import ANY, AsyncMock

import pytest
from rich.console import Console

from domain.entities import Article
from interface import cli


@pytest.mark.asyncio
@pytest.mark.parametrize("markdown", [False, True])
async def test_live_progress_in_both_modes(monkeypatch, tmp_path, markdown) -> None:
    output = StringIO()
    monkeypatch.setattr(
        cli, "console", Console(file=output, force_terminal=True, width=160)
    )

    async def execute(limit, progress_callback=None):
        assert limit == 20
        assert progress_callback is not None
        progress_callback("Extracting", 0, 3)
        assert "Extracting stories (0/3 completed)" in output.getvalue()
        progress_callback("Extracting", 3, 3)
        assert "Extracting stories (3/3 completed)" in output.getvalue()
        progress_callback("Summarizing", 0, 3)
        assert "Summarizing story 1 of 3 (0 completed)" in output.getvalue()
        progress_callback("Summarizing", 2, 3)
        assert "Summarizing story 3 of 3 (2 completed)" in output.getvalue()
        progress_callback("Summarizing", 3, 3)
        assert "Summarizing stories (3/3 completed)" in output.getvalue()
        assert "story 4 of 3" not in output.getvalue()
        return [(_article(), "A bilingual summary")]

    usecase = AsyncMock()
    usecase.execute.side_effect = execute
    filename = tmp_path / "digest.md"
    if markdown:
        await cli.run_markdown(usecase, 20, str(filename), "Current top stories")
        content = filename.read_text(encoding="utf-8")
        assert "Summarizing" not in content
        assert "Extracting" not in content
        assert "A bilingual summary" in content
    else:
        await cli.run_cli(usecase, 20, "Current top stories")
        assert "An article" in output.getvalue()
        assert "A bilingual summary" in output.getvalue()


@pytest.mark.asyncio
@pytest.mark.parametrize("markdown", [False, True])
async def test_empty_progress_reports_completed_totals(monkeypatch, tmp_path, markdown) -> None:
    output = StringIO()
    monkeypatch.setattr(
        cli, "console",
        Console(file=output, force_terminal=True, width=160, color_system=None),
    )

    async def execute(limit, progress_callback=None):
        progress_callback("Extracting", 0, 0)
        assert "Extracting stories (0/0 completed)" in output.getvalue()
        progress_callback("Summarizing", 0, 0)
        assert "Summarizing stories (0/0 completed)" in output.getvalue()
        assert "story 1 of 0" not in output.getvalue()
        return []

    usecase = AsyncMock()
    usecase.execute.side_effect = execute
    if markdown:
        filename = tmp_path / "empty.md"
        await cli.run_markdown(usecase, 20, str(filename), "Current top stories")
        assert filename.read_text(encoding="utf-8") == (
            "# HackerDigest\n*Current top stories; 0 stories*\n\n---\n"
        )
    else:
        await cli.run_cli(usecase, 20, "Current top stories")
        assert "Loaded 0 stories" in output.getvalue()


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
    summarize_article.execute.assert_awaited_once_with(30, progress_callback=ANY)


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
