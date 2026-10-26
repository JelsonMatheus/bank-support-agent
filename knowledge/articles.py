"""Load knowledge base articles from Markdown files with a small front matter."""

from dataclasses import dataclass
from pathlib import Path

ARTICLES_DIR = Path(__file__).parent / "articles"
REQUIRED_FIELDS = ("id", "title", "category")


class ArticleFormatError(ValueError):
    """Raised when an article file doesn't follow the expected format."""


@dataclass(frozen=True)
class Article:
    id: str
    title: str
    category: str
    body: str
    path: Path


def parse_article(path: Path) -> Article:
    text = path.read_text(encoding="utf-8")
    before, separator, rest = text.partition("---")
    front_matter, separator_end, body = rest.partition("---")
    if before.strip() or not separator or not separator_end:
        raise ArticleFormatError(f"{path.name}: missing front matter")

    metadata = {}
    for line in front_matter.strip().splitlines():
        key, colon, value = line.partition(":")
        if not colon:
            raise ArticleFormatError(f"{path.name}: invalid front matter line {line!r}")
        metadata[key.strip()] = value.strip()

    missing = [field for field in REQUIRED_FIELDS if not metadata.get(field)]
    if missing:
        raise ArticleFormatError(f"{path.name}: missing fields {missing}")

    return Article(
        id=metadata["id"],
        title=metadata["title"],
        category=metadata["category"],
        body=body.strip(),
        path=path,
    )


def load_articles(directory: Path = ARTICLES_DIR) -> list[Article]:
    return [parse_article(path) for path in sorted(directory.glob("*.md"))]