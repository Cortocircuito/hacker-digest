from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class Article:
    id: int
    title: str
    url: str | None
    by: str
    score: int
    time: int
    descendants: int

    @property
    def domain(self) -> str | None:
        if self.url:
            return urlparse(self.url).netloc
        return None
