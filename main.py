import argparse
import asyncio
import logging
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from infrastructure.algolia_client import AlgoliaClient
from infrastructure.content_extractor import NewspaperExtractor
from infrastructure.hn_client import HNClient
from infrastructure.ollama_client import OllamaClient, check_ollama_installed
from interface.cli import run_cli, run_markdown
from usecases.summarize_article import SummarizeArticle


_DIGEST_FILENAME = re.compile(
    r"^hacker-digest-(?P<story_date>\d{4}-\d{2}-\d{2})"
    r"(?:-generated-(?P<generated_on>\d{4}-\d{2}-\d{2}))?\.md$"
)


def _today_utc() -> date:
    return datetime.now(timezone.utc).date()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="hacker-digest",
        description="Fetch top Hacker News stories and summarize them with Ollama",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Number of stories to fetch (default: 10, 30 for markdown)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemma2:2b",
        help="Ollama model to use (default: gemma2:2b)",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Write a dated Markdown digest",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="digests",
        help="Directory to save markdown files (default: digests)",
    )
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        help="UTC date to query in YYYY-MM-DD format (uses Algolia)",
    )
    return parser.parse_args()


def _markdown_filename(output_dir: Path, story_date: date | None) -> Path:
    generated_on = _today_utc().isoformat()
    if story_date is None:
        return output_dir / f"hacker-digest-{generated_on}.md"
    return output_dir / (
        f"hacker-digest-{story_date.isoformat()}-generated-{generated_on}.md"
    )


def _digest_generation_date(filename: Path) -> date | None:
    match = _DIGEST_FILENAME.fullmatch(filename.name)
    if match is None:
        return None

    try:
        return date.fromisoformat(match.group("generated_on") or match.group("story_date"))
    except ValueError:
        return None


def _archive_previous_markdown_digests(output_dir: Path, current_date: date) -> None:
    """Move prior-month root digests into year/month archive directories."""
    current_month = (current_date.year, current_date.month)

    for digest in output_dir.glob("*.md"):
        generated_on = _digest_generation_date(digest)
        if generated_on is None or (generated_on.year, generated_on.month) >= current_month:
            continue

        archive_dir = output_dir / f"{generated_on.year:04d}" / f"{generated_on.month:02d}"
        archive_dir.mkdir(exist_ok=True, parents=True)
        destination = archive_dir / digest.name
        if destination.exists():
            raise FileExistsError(f"Cannot archive {digest}: {destination} already exists")
        digest.rename(destination)


def _resolve_limit(requested_limit: int | None, markdown: bool) -> int:
    if requested_limit is not None:
        return requested_limit
    return 30 if markdown else 10


def _story_client(story_date: date | None) -> HNClient | AlgoliaClient:
    if story_date is None:
        return HNClient()
    return AlgoliaClient(story_date)


async def main() -> None:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    args = parse_args()

    if args.limit is not None and args.limit <= 0:
        print("Error: --limit must be a positive integer")
        sys.exit(1)
    if args.date is not None and args.date > _today_utc():
        print("Error: --date cannot be in the future")
        sys.exit(1)

    check_ollama_installed()

    limit = _resolve_limit(args.limit, args.markdown)
    source_label = (
        f"Stories submitted on {args.date.isoformat()} (UTC)"
        if args.date is not None
        else "Current top stories"
    )
    client = _story_client(args.date)

    async with client as hn_client, OllamaClient(model=args.model) as ollama_client:
        await ollama_client.ensure_model()
        content_extractor = NewspaperExtractor()
        summarize_article = SummarizeArticle(
            hn_client, ollama_client, content_extractor
        )

        try:
            if args.markdown:
                output_dir = Path(args.output_dir)
                output_dir.mkdir(exist_ok=True, parents=True)
                _archive_previous_markdown_digests(output_dir, _today_utc())
                filename = _markdown_filename(output_dir, args.date)
                await run_markdown(
                    summarize_article, limit, str(filename), source_label
                )
                print(f"Saved to {filename}")
            else:
                await run_cli(summarize_article, limit, source_label)
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
