import argparse
import asyncio
import sys
from datetime import date
from pathlib import Path

from infrastructure.content_extractor import NewspaperExtractor
from infrastructure.hn_client import HNClient
from infrastructure.ollama_client import OllamaClient
from interface.cli import run_cli, run_markdown
from usecases.summarize_article import SummarizeArticle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="hacker-digest",
        description="Fetch top Hacker News stories and summarize them with Ollama",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of stories to fetch (default: 10, 30 for markdown)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="llama3:8b",
        help="Ollama model to use (default: llama3:8b)",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Output in markdown format to a file with today's date",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="digests",
        help="Directory to save markdown files (default: digests)",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    limit = args.limit if args.limit != 10 else 30 if args.markdown else 10

    hn_client = HNClient()
    ollama_client = OllamaClient(model=args.model)
    content_extractor = NewspaperExtractor()
    summarize_article = SummarizeArticle(
        hn_client, ollama_client, content_extractor
    )

    try:
        if args.markdown:
            output_dir = Path(args.output_dir)
            output_dir.mkdir(exist_ok=True)
            filename = output_dir / f"hacker-digest-{date.today()}.md"
            await run_markdown(summarize_article, limit, str(filename))
            print(f"Saved to {filename}")
        else:
            await run_cli(summarize_article, limit)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
