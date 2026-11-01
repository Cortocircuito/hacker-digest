# HackerDigest

HackerDigest is an asynchronous CLI that retrieves Hacker News stories, extracts linked article content, and generates concise Spanish/English summaries with a local Ollama model.

[Installation](#installation) · [Usage](#usage) · [Markdown exports](#markdown-exports) ·
[Limitations](#current-limitations) · [Troubleshooting](#troubleshooting) ·
[Development](#development)

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

Make sure Ollama is running before using HackerDigest. If it is not already running,
start it in a separate terminal:

```bash
ollama serve
```

The default model is `gemma2:2b`. HackerDigest checks for the selected model and pulls
it automatically when absent. To download the default model ahead of time, run
`ollama pull gemma2:2b`.

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

### Current versus date-based queries

Without `--date`, HackerDigest uses Hacker News' current `topstories` ranking. With
`--date`, it uses Algolia's index, fetches all stories submitted during that UTC day,
and ranks them by their current score. Date queries do not recreate the Hacker News
front page or score at the end of that day.

## Markdown exports

Exports include the article URL when available and a link to its Hacker News
discussion. Files are written in UTF-8 under `--output-dir` (default: `digests/`).

| Query | Filename |
| --- | --- |
| Current top stories | `hacker-digest-YYYY-MM-DD.md` |
| With `--date` | `hacker-digest-YYYY-MM-DD-generated-YYYY-MM-DD.md` |

For date-based exports, the first date is the story date and the second is the
generation date. All filename dates use UTC.

Before each Markdown batch, recognized root digests generated in earlier months
are moved to `YYYY/MM` subdirectories, for example `digests/2026/09/`. Archiving
uses the generation month, not the story month. Current/future-month digests and
unrecognized filenames stay in place. An existing archive destination causes an
error rather than being overwritten.

**Export safety:** generating the same output filename again overwrites that file.
Exports are written directly, not atomically, and only after processing the batch;
there is no incremental save or resume. Use a separate `--output-dir` to keep another
copy of a digest.

## Current limitations

- **Partial article input:** only the first 3,000 characters of extracted article
  text are sent to the model. Important information later in an article may be missed.
- **Unavailable article content:** stories without a URL, or whose extracted content
  cannot be extracted or is missing, empty, or whitespace-only, keep their available links but
  are not sent to the model. Both output modes show
  `Resumen no disponible: no se pudo obtener el contenido` instead of a summary.
  Titles alone are never used to generate summaries; skipped stories still complete
  progress. See [content extraction failures](#content-extraction-fails).
- **Unverified generated text:** bilingual formatting and factual accuracy are
  requested in the prompt, not validated. Generation is capped at 160 tokens across
  both languages, so responses may be incomplete. Check the linked source before
  relying on a summary.
- **Local Ollama configuration:** the server address and HTTP timeout are currently
  fixed in code; there are no CLI options for a remote server or a different timeout.
- **No result cache:** running the same query again fetches and summarizes it again.

## Troubleshooting

### Ollama is unavailable

Check that Ollama is installed and available on `PATH`, then start the server with
`ollama serve` if needed. HackerDigest expects it at `http://localhost:11434`.

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

Some sites block automated extraction or respond too slowly. Check the logged
failure and open the article link directly. The story remains in the digest with
the [unavailable-content notice](#current-limitations); retrying does not guarantee
that the site will permit extraction.

### Invalid arguments

`--limit` must be a positive integer. `--date` must use `YYYY-MM-DD` and cannot be
later than the current UTC date. See the [options table](#options) for defaults.

## Development

Follow [Installation](#installation) to create and activate `venv`, then install
development dependencies and run the checks:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
python -m compileall -q domain infrastructure interface usecases main.py
```

Run one test module with `python -m pytest tests/test_algolia_client.py`. Tests mock
HTTP and Newspaper4k calls, so they do not require a running Ollama instance or live
Hacker News requests. They verify application behavior, not real-model summary
quality or hardware performance.

See [AGENTS.md](AGENTS.md) for architecture boundaries, runtime contracts, and
change-specific verification requirements. Keep user-facing instructions in this
README and contributor/agent constraints in AGENTS.md.

## License

[MIT](LICENSE.txt)
