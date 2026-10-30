from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table

from domain.entities import Article
from usecases.summarize_article import SUMMARY_UNAVAILABLE, SummarizeArticle


console = Console()


async def run_cli(
    summarize_article: SummarizeArticle, limit: int, source_label: str
) -> None:
    console.print(f"[bold cyan]HackerDigest[/bold cyan] - {source_label}\n")

    results = await _execute_with_progress(summarize_article, limit)

    console.print(f"\n[green]Loaded {len(results)} stories[/green]\n")

    for idx, (article, summary) in enumerate(results, 1):
        _display_article(idx, article, summary)
        console.print()


async def _execute_with_progress(
    summarize_article: SummarizeArticle, limit: int
) -> list[tuple[Article, str]]:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Loading stories...", total=None)

        def update_progress(phase: str, completed: int, total: int) -> None:
            if phase == "Summarizing" and completed < total:
                description = (
                    f"Summarizing story {completed + 1} of {total} ({completed} completed)"
                )
            else:
                description = f"{phase} stories ({completed}/{total} completed)"
            progress.update(
                task,
                completed=completed,
                total=total,
                description=description,
                refresh=True,
            )

        return await summarize_article.execute(limit, progress_callback=update_progress)


async def run_markdown(
    summarize_article: SummarizeArticle,
    limit: int,
    filename: str,
    source_label: str,
) -> None:
    results = await _execute_with_progress(summarize_article, limit)

    lines = ["# HackerDigest\n"]
    lines.append(f"*{source_label}; {len(results)} stories*\n\n---\n")

    for idx, (article, summary) in enumerate(results, 1):
        lines.append(f"## {idx}. {article.title}\n")
        lines.append(f"- **Score:** {article.score} | **Comments:** {article.descendants}\n")
        lines.append(f"- **By:** {article.by}\n")
        if article.url:
            lines.append(f"- **Link:** [Read Full Article]({article.url})\n")
        lines.append(
            "- **Discussion:** "
            f"[View on Hacker News](https://news.ycombinator.com/item?id={article.id})\n"
        )
        lines.append("\n")

        if summary and summary != SUMMARY_UNAVAILABLE and not summary.startswith("["):
            lines.append(f"### Summary\n\n{summary}\n\n")
        else:
            lines.append(f"*{summary}*\n\n")

        lines.append("---\n")

    with open(filename, "w", encoding="utf-8") as f:
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

    if summary == SUMMARY_UNAVAILABLE:
        console.print(summary)
    elif summary and not summary.startswith("["):
        console.print(Panel(Markdown(summary), border_style="cyan", padding=(1, 2)))
    else:
        console.print(f"[red]{summary}[/red]")
