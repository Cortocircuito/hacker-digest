import argparse
import asyncio
import sys

from infrastructure.content_extractor import NewspaperExtractor
from infrastructure.hn_client import HNClient
from infrastructure.ollama_client import OllamaClient
from interface.cli import run_cli
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
        help="Number of stories to fetch (default: 10)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="llama3:8b",
        help="Ollama model to use (default: llama3:8b)",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    hn_client = HNClient()
    ollama_client = OllamaClient(model=args.model)
    content_extractor = NewspaperExtractor()
    summarize_article = SummarizeArticle(
        hn_client, ollama_client, content_extractor
    )

    try:
        await run_cli(summarize_article, args.limit)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
