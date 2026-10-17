# HackerDigest

HackerDigest is an asynchronous CLI that retrieves Hacker News stories, extracts linked article content, and generates concise Spanish/English summaries with a local Ollama model.

## Features

- Fetches the current top stories from the Hacker News Firebase API.
- Retrieves stories submitted on a selected UTC day through the Hacker News Algolia Search API.
- Extracts linked article content with Newspaper4k before summarizing.
- Generates bilingual summaries with a local Ollama model.
- Extracts up to three articles concurrently while keeping Ollama summaries sequential for modest hardware.
- Renders results in a Rich-powered terminal UI.
- Exports a daily digest in Markdown.
- Continues when an article cannot be extracted or summarized.

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com/) installed, available on `PATH`, and running at `http://localhost:11434`
- Internet access to fetch stories, article content, and any model not already downloaded.

### Hardware expectations

There is no project-validated minimum hardware specification or performance benchmark.
Model memory usage includes more than its download size. Leave room for the operating
system, Ollama, and article extraction; low-memory machines may swap or fail to load
the model. Older CPUs can make summarization slow even when the model fits in RAM.

Start with `python main.py --limit 1` to check your setup before processing a full
batch. `--model` selects a different model, but smaller models can reduce summary
quality. Check Ollama's hardware support for your machine; installing the Python
application alone does not establish model compatibility or acceptable speed.

## Installation

```bash
git clone https://github.com/Cortocircuito/hacker-digest.git
cd hacker-digest

python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

python -m pip install -r requirements.txt
```

The default model is `gemma2:2b`. HackerDigest checks for it and pulls it automatically when absent. You can also pull it manually:

```bash
ollama pull gemma2:2b
```

## Usage

```bash
# Show the current top 10 stories from Hacker News
python main.py

# Fetch a custom number of stories
python main.py --limit 20

# Use a different local model
python main.py --model mistral

# Write a Markdown digest; defaults to 30 stories
python main.py --markdown

# Choose a destination directory and story limit
python main.py --markdown --limit 20 --output-dir my-digests

# Query stories submitted on a UTC date in the Rich terminal UI
python main.py --date 2026-09-10

# Export a historical date to Markdown
python main.py --date 2026-09-10 --markdown

# Show all options
python main.py --help
```

Both terminal and Markdown modes show live processing progress on screen. Extraction
reports completed totals; sequential summarization shows the current story, for
example, `Summarizing story 3 of 20 (2 completed)`. Counts use the number of stories
actually fetched. Progress is not included in the exported Markdown file.

### Options

| Flag | Default | Description |
| --- | --- | --- |
| `--limit` | `10` | Positive number of stories to fetch. Markdown mode uses `30` when omitted. |
| `--model` | `gemma2:2b` | Local Ollama model to use. |
| `--markdown` | `false` | Write the digest to a dated Markdown file. |
| `--output-dir` | `digests` | Directory for Markdown exports. |
| `--date` | Current top stories | Query stories submitted on this UTC date (`YYYY-MM-DD`) through Algolia. Future dates are rejected. |

Without `--date`, HackerDigest uses Hacker News' current `topstories` ranking. With
`--date`, it uses Algolia's index, fetches all stories submitted during that UTC day,
and ranks them by their current score. Date queries do not recreate the Hacker News
front page or score at the end of that day.

Markdown exports include the article URL when available and a link to its Hacker News
discussion. Historical exports use a filename such as
`hacker-digest-2026-09-10-generated-2026-09-12.md`; current exports retain the
`hacker-digest-YYYY-MM-DD.md` name. The output directory keeps digests generated in
the current UTC month at its root. On the first Markdown export of a new month,
earlier root digests are moved to `YYYY/MM` subdirectories, for example
`digests/2026/09/`. Historical digests are archived by their generation month, not
the month of the stories. An existing archive destination causes an error rather
than being overwritten.

**Export safety:** generating the same output filename again overwrites that file.
Exports are written directly, not atomically, and only after processing the batch;
there is no incremental save or resume. Use a separate `--output-dir` to keep another
copy of a digest.

## Current limitations

- **Partial article input:** only the first 3,000 characters of extracted article
  text are sent to the model. Important information later in an article may be missed.
- **Title-only fallback:** when no article content is available, the model receives
  only the title. The resulting summary is not explicitly labeled as title-only.
- **Unverified generated text:** bilingual formatting and factual accuracy are
  requested in the prompt, not validated. Generation is capped at 160 tokens across
  both languages, so responses may be incomplete. Check the linked source before
  relying on a summary.
- **Local Ollama configuration:** the server address and HTTP timeout are currently
  fixed in code; there are no CLI options for a remote server or a different timeout.
- **No result cache:** running the same query again fetches and summarizes it again.

## Development

Install development dependencies in the activated virtual environment and run the
checks:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
python -m compileall -q domain infrastructure interface usecases main.py
```

Run one test module with `python -m pytest tests/test_algolia_client.py`. Tests mock
HTTP and Newspaper4k calls, so they do not require a running Ollama instance or live
Hacker News requests.

## Troubleshooting

### Ollama is unavailable

Start the Ollama server:

```bash
ollama serve
```

### Summarization is slow or fails

Summaries are generated one at a time without streaming generated text. The progress
indicator shows the current story, not token-level progress. The Ollama HTTP client
uses a 120-second timeout for network operations, including waiting for response data;
this is not a total time limit for the batch. Slow generation can trigger a timeout.
Summary failures are logged and displayed as `[Error generating summary]`, while
processing continues with the next story.

Try one story first and consider a smaller model if your machine is resource-limited.
Reducing `--limit` reduces batch size, not the work needed for each individual summary.

### Content extraction fails

Some sites block automated extraction or respond too slowly. HackerDigest logs the failure and generates a title-based summary instead.

### Invalid limit

`--limit` must be a positive integer:

```bash
python main.py --limit 10
```

### Invalid date

`--date` accepts `YYYY-MM-DD` in UTC and rejects future dates:

```bash
python main.py --date 2026-09-10
```

## License

MIT
