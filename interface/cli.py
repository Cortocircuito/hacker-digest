from typing import Callable

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TaskID, TextColumn
from rich.table import Table

from domain.entities import Article
from usecases.summarize_article import SummarizeArticle


console = Console()


async def run_cli(summarize_article: SummarizeArticle, limit: int) -> None:
    console.print("[bold cyan]HackerDigest[/bold cyan] - Fetching top stories...\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Loading from Hacker News...", total=None)
        results = await summarize_article.execute(limit)
        progress.update(task, completed=True)

    console.print(f"\n[green]Loaded {len(results)} stories[/green]\n")

    for idx, (article, summary) in enumerate(results, 1):
        _display_article(idx, article, summary)
        console.print()


async def run_markdown(
    summarize_article: SummarizeArticle, limit: int, filename: str
) -> None:
    results = await summarize_article.execute(limit)

    lines = ["# HackerDigest\n"]
    lines.append(f"*{limit} top stories*\n\n---\n")

    for idx, (article, summary) in enumerate(results, 1):
        lines.append(f"## {idx}. [{article.title}]({article.url})\n")
        lines.append(f"- **Score:** {article.score} | **Comments:** {article.descendants}\n")
        lines.append(f"- **By:** {article.by}\n")
        if article.url:
            lines.append(f"- **Link:** [Read Full Article]({article.url})\n")
        lines.append("\n")

        if summary and not summary.startswith("["):
            lines.append(f"### Summary\n\n{summary}\n\n")
        else:
            lines.append(f"*{summary}*\n\n")

        lines.append("---\n")

    with open(filename, "w") as f:
        f.writelines(lines)


def _display_article(idx: int, article: Article, summary: str) -> None:
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column(style="bold cyan", width=4)
    table.add_column(style="white")

    score_label = f"[yellow]▲{article.score}[/yellow]"
    comments_label = f"[blue]💬 {article.descendants}[/blue]"
    table.add_row(f"{idx}.", f"{article.title} {score_label} {comments_label}")

    domain = article.domain or "news.ycombinator.com"
    table.add_row("", f"[dim]{domain} by {article.by}[/dim]")

    console.print(table)

    if summary and not summary.startswith("["):
        console.print(Panel(Markdown(summary), border_style="cyan", padding=(1, 2)))
    else:
        console.print(f"[red]{summary}[/red]")


def create_progress_callback(progress: Progress, task_id: TaskID) -> Callable[[str], None]:
    def callback(description: str) -> None:
        progress.update(task_id, description=description)
    return callback
