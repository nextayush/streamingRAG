from datetime import datetime
from typing import Any


def _extract_yahoo_article(article: dict[str, Any]) -> dict[str, Any] | None:
    title = article.get("title")
    summary = article.get("summary") or article.get("description")
    link = article.get("link")
    pub_date = article.get("providerPublishTime") or article.get("published_at")
    publisher = article.get("publisher")

    content = article.get("content")
    if isinstance(content, dict):
        title = title or content.get("title")
        summary = (
            summary
            or content.get("summary")
            or content.get("description")
            or content.get("snippet")
        )
        link = (
            link
            or content.get("canonicalUrl")
            or content.get("clickThroughUrl")
            or content.get("url")
        )
        pub_date = pub_date or content.get("pubDate") or content.get("displayTime")
        publisher = publisher or content.get("provider", {}).get("displayName")

    if not title:
        return None

    if isinstance(pub_date, (int, float)):
        try:
            pub_date = datetime.fromtimestamp(pub_date).isoformat()
        except (OSError, ValueError):
            pub_date = str(pub_date)
    elif pub_date is not None:
        pub_date = str(pub_date)

    article_id = (
        article.get("uuid")
        or article.get("id")
        or article.get("guid")
        or hash(f"{title}{link or ''}")
    )

    return {
        "id": str(article_id),
        "title": title,
        "summary": (summary or "").strip(),
        "link": link or "",
        "pub_date": pub_date,
        "publisher": publisher or "Unknown",
    }


def extract_yahoo_articles(news: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    articles = []
    for raw in (news or [])[:limit]:
        parsed = _extract_yahoo_article(raw)
        if parsed:
            articles.append(parsed)
    return articles


def analyze_sentiment(text: str) -> tuple[str, float]:
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

        scores = SentimentIntensityAnalyzer().polarity_scores(text)
        compound = scores["compound"]
        if compound >= 0.05:
            return "POSITIVE", compound
        if compound <= -0.05:
            return "NEGATIVE", compound
        return "NEUTRAL", compound
    except ImportError:
        return "NEUTRAL", 0.0
