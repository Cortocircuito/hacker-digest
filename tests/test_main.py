import sys
from datetime import date
from pathlib import Path

import main
import pytest
from infrastructure.algolia_client import AlgoliaClient
from infrastructure.hn_client import HNClient


def test_parse_args_uses_no_limit_until_the_output_format_is_known(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["main.py", "--markdown", "--date", "2026-09-10"])

    args = main.parse_args()

    assert args.limit is None
    assert args.markdown is True
    assert args.date == date(2026, 9, 10)


def test_markdown_filename_contains_requested_and_generated_dates() -> None:
    output_dir = Path("digests")
    filename = main._markdown_filename(output_dir, date(2026, 9, 10))

    assert filename.name.startswith("hacker-digest-2026-09-10-generated-")
    assert filename.suffix == ".md"


def test_archive_previous_markdown_digests_keeps_current_month_in_root(tmp_path) -> None:
    previous_month = tmp_path / "hacker-digest-2026-08-31.md"
    current_month = tmp_path / "hacker-digest-2026-09-01.md"
    historical_current_month = (
        tmp_path / "hacker-digest-2026-08-26-generated-2026-09-17.md"
    )
    unrelated_file = tmp_path / "notes.md"
    for digest in (previous_month, current_month, historical_current_month, unrelated_file):
        digest.touch()

    main._archive_previous_markdown_digests(tmp_path, date(2026, 9, 22))

    assert not previous_month.exists()
    assert (tmp_path / "2026" / "08" / previous_month.name).exists()
    assert current_month.exists()
    assert historical_current_month.exists()
    assert unrelated_file.exists()


def test_archive_previous_markdown_digests_uses_generation_date(tmp_path) -> None:
    digest = tmp_path / "hacker-digest-2026-08-26-generated-2026-09-17.md"
    digest.touch()

    main._archive_previous_markdown_digests(tmp_path, date(2026, 10, 1))

    assert not digest.exists()
    assert (tmp_path / "2026" / "09" / digest.name).exists()


def test_resolve_limit_keeps_explicit_limit_in_markdown_mode() -> None:
    assert main._resolve_limit(None, markdown=False) == 10
    assert main._resolve_limit(None, markdown=True) == 30
    assert main._resolve_limit(10, markdown=True) == 10


@pytest.mark.asyncio
async def test_story_client_uses_algolia_only_when_a_date_is_requested() -> None:
    current_client = main._story_client(None)
    historical_client = main._story_client(date(2026, 9, 10))

    assert isinstance(current_client, HNClient)
    assert isinstance(historical_client, AlgoliaClient)

    await current_client.close()
    await historical_client.close()
