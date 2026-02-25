# HackerDigest - Specification Document

## 1. Project Overview

**Project Name:** HackerDigest  
**Type:** CLI Application  
**Core Functionality:** Fetch top stories from Hacker News and generate bilingual summaries (Spanish/English) using a local Ollama model  
**Target Users:** Developers and tech enthusiasts who want quick, bilingual summaries of HN top stories

---

## 2. Architecture

### Clean Architecture Layers

```
hacker_digest/
├── domain/           # Enterprise Business Rules
│   ├── entities.py   # Article entity
│   └── services.py  # Abstract interfaces (ports)
├── infrastructure/  # Frameworks & Drivers
│   ├── hn_client.py  # Hacker News API client
│   └── ollama_client.py
├── usecases/         # Application Business Rules
│   └── summarize_article.py
├── interface/        # Interface Adapters
│   └── cli.py       # Rich CLI
└── main.py          # Entry point
```

### SOLID Principles
- **S**ingle Responsibility: Each layer has one job
- **O**pen/Closed: Extend behavior without modifying existing code
- **L**iskov Substitution: Interfaces allow swapping implementations
- **I**nterface Segregation: Small, focused interfaces
- **D**ependency Inversion: High-level modules don't depend on low-level modules

### KISS
- Avoid over-engineering
- Simple functions over complex patterns
- One concept per file

---

## 3. Domain Layer

### Entities

**Article**
```python
@dataclass
class Article:
    id: int
    title: str
    url: str | None
    by: str
    score: int
    time: int  # Unix timestamp
    descendants: int  # comment count
```

### Service Interfaces (Ports)

**HackerNewsPort**
```python
class HackerNewsPort(Protocol):
    async def get_top_stories(self, limit: int = 10) -> list[Article]: ...
    async def get_article(self, article_id: int) -> Article: ...
```

**SummarizerPort**
```python
class SummarizerPort(Protocol):
    async def summarize(self, article: Article) -> str: ...
```

---

## 4. Infrastructure Layer

### HNClient
- Uses `https://hacker-news.firebaseio.com/v0/` API
- Fetches top stories IDs, then article details
- Returns `Article` domain entities

### OllamaClient
- Connects to `http://localhost:11434/api/generate`
- Model: `llama3:8b` or `mistral` (configurable)
- Prompt template:
  ```
  Resume el siguiente artículo en 3 puntos clave, primero en español y luego en inglés. Formato: Markdown.
  
  Título: {title}
  URL: {url}
  ```

---

## 5. Use Cases

### SummarizeArticle
```python
class SummarizeArticle:
    def __init__(
        self,
        hn_client: HackerNewsPort,
        summarizer: SummarizerPort
    ): ...
    
    async def execute(self, limit: int = 10) -> list[tuple[Article, str]]:
        # 1. Get top stories
        # 2. For each article, generate summary
        # 3. Return list of (article, summary)
```

---

## 6. Interface Layer (CLI)

### Using `rich` library

**Features:**
- Table display for articles
- Color-coded output
- Progress indicators during API calls
- Error handling with styled messages

**Commands:**
```bash
python main.py                    # Show top 10 stories with summaries
python main.py --limit 20        # Custom number of stories
python main.py --model mistral   # Use different Ollama model
python main.py --help            # Show help
```

---

## 7. Technical Requirements

### Dependencies
```
requests>=2.31.0
rich>=13.7.0
httpx>=0.26.0  # For async HTTP
pydantic>=2.5.0
```

### Type Checking
- Strict type hints throughout
- Run: `mypy . --strict`

### Error Handling
- Custom exceptions in domain layer
- Graceful degradation if Ollama unavailable
- Retry logic for API calls

---

## 8. Implementation Order

1. **domain/entities.py** - Define Article dataclass
2. **domain/services.py** - Define protocol interfaces
3. **infrastructure/hn_client.py** - Implement HN API client
4. **infrastructure/ollama_client.py** - Implement Ollama client
5. **usecases/summarize_article.py** - Implement use case
6. **interface/cli.py** - Build Rich CLI
7. **main.py** - Entry point with argparse

---

## 9. Future Extensibility

- Add caching layer (Redis/File)
- Add GUI interface (replace `interface/cli.py`)
- Add export to Markdown/HTML
- Add filtering by score/comments
- Add "save for later" feature
