import json
import re
from pathlib import Path

import pytest

from knowledge.articles import load_articles

INTENT_MAP_PATH = Path(__file__).parent.parent / "evals" / "intent_map.json"
FORBIDDEN_TOPICS = re.compile(
    r"exchange rate|\bATMs?\b|cash withdrawal|virtual card|age limit|minimum age",
    re.IGNORECASE,
)
REFUND_PROMISES = re.compile(
    r"will be refunded|we will refund|we'll refund|refund you|get a refund",
    re.IGNORECASE,
)


@pytest.fixture(scope="module")
def articles():
    return load_articles()


@pytest.fixture(scope="module")
def intent_map() -> dict:
    return json.loads(INTENT_MAP_PATH.read_text(encoding="utf-8"))


def test_knowledge_base_has_all_articles(articles):
    assert len(articles) == 17


def test_article_ids_are_unique(articles):
    ids = [article.id for article in articles]
    assert len(ids) == len(set(ids))


def test_file_names_start_with_article_id(articles):
    for article in articles:
        assert article.path.name.startswith(article.id), article.path.name


def test_categories_are_allowed(articles, intent_map):
    allowed = set(intent_map["categories"])
    for article in articles:
        assert article.category in allowed, f"{article.id}: {article.category}"


def test_article_length(articles):
    for article in articles:
        words = len(article.body.split())
        assert 80 <= words <= 250, f"{article.id}: {words} words"


def test_no_forbidden_topics(articles):
    for article in articles:
        match = FORBIDDEN_TOPICS.search(article.body)
        assert match is None, f"{article.id} mentions {match.group()!r}"


def test_no_refund_promises(articles):
    for article in articles:
        match = REFUND_PROMISES.search(article.body)
        assert match is None, f"{article.id} contains {match.group()!r}"


def test_intent_map_points_to_existing_articles(articles, intent_map):
    known_ids = {article.id for article in articles}
    for intent, labels in intent_map["intents"].items():
        if labels["action"] == "answer":
            assert labels["articles"], f"{intent}: answer without articles"
            unknown = set(labels["articles"]) - known_ids
            assert not unknown, f"{intent}: unknown articles {sorted(unknown)}"
        else:
            assert labels["articles"] == [], f"{intent}: handoff with articles"