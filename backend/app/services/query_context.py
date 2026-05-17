"""Query understanding: ticker detection, intent, and retrieval query expansion."""

from enum import Enum

from app.services.stocks import STOCK_MAP

TRACKED_SYMBOLS = set(STOCK_MAP.keys())

STOCK_ALIASES: dict[str, str] = {
    "apple": "AAPL",
    "aapl": "AAPL",
    "microsoft": "MSFT",
    "msft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "googl": "GOOGL",
    "amazon": "AMZN",
    "amzn": "AMZN",
    "nvidia": "NVDA",
    "nvda": "NVDA",
    "meta": "META",
    "facebook": "META",
    "tesla": "TSLA",
    "tsla": "TSLA",
    "netflix": "NFLX",
    "nflx": "NFLX",
    "amd": "AMD",
    "intel": "INTC",
    "intc": "INTC",
    "bitcoin": "BTC-USD",
    "btc": "BTC-USD",
}

CAUSAL_KEYWORDS = (
    "why",
    "reason",
    "cause",
    "because",
    "explain",
    "decline",
    "declining",
    "fall",
    "falling",
    "drop",
    "dropping",
    "crash",
    "selloff",
    "sell-off",
    "plunge",
    "tumble",
    "weakness",
    "underperform",
    "downgrade",
    "miss",
    "warning",
    "concern",
    "headwind",
    "what happened",
    "what's driving",
    "what is driving",
)

COMPARISON_KEYWORDS = (
    "compare",
    "comparison",
    " versus ",
    " vs ",
    " vs.",
    "difference between",
    "differences between",
    "better than",
    "worse than",
    "outperform",
    "underperform",
    "which is better",
    "which one is better",
    "head to head",
    "side by side",
)

RECOMMENDATION_KEYWORDS = (
    "should i buy",
    "should i sell",
    "should i invest",
    "worth buying",
    "worth investing",
    "good investment",
    "bad investment",
    "recommend",
    "buy or sell",
    "hold or sell",
)

OUTLOOK_KEYWORDS = (
    "outlook",
    "forecast",
    "prediction",
    "going forward",
    "future of",
    "where is",
    "headed",
    "direction",
    "momentum",
    "trend",
)

FACTUAL_KEYWORDS = (
    "current price",
    "stock price",
    "trading at",
    "how much is",
    "what is the price",
    "what's the price",
    "market cap",
    "share price",
)


class QueryIntent(str, Enum):
    COMPARISON = "comparison"
    CAUSAL = "causal"
    RECOMMENDATION = "recommendation"
    OUTLOOK = "outlook"
    FACTUAL = "factual"
    GENERAL = "general"


def detect_tickers(query: str) -> list[str]:
    """Return unique tickers mentioned in the query."""
    q = query.lower()
    found: list[str] = []

    for alias, symbol in STOCK_ALIASES.items():
        if alias in q and symbol not in found:
            found.append(symbol)

    for symbol in TRACKED_SYMBOLS:
        if symbol.lower() in q and symbol not in found:
            found.append(symbol)

    return found


def is_causal_query(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in CAUSAL_KEYWORDS)


def is_comparison_query(query: str) -> bool:
    q = f" {query.lower()} "
    return any(kw in q for kw in COMPARISON_KEYWORDS) or (
        len(detect_tickers(query)) >= 2 and any(w in q for w in ("better", "stronger", "weaker"))
    )


def is_recommendation_query(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in RECOMMENDATION_KEYWORDS)


def is_outlook_query(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in OUTLOOK_KEYWORDS) and not is_causal_query(query)


def is_factual_query(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in FACTUAL_KEYWORDS) and not is_comparison_query(query)


def classify_intent(query: str) -> QueryIntent:
    """Pick the best response mode for this question (first match wins)."""
    if is_comparison_query(query):
        return QueryIntent.COMPARISON
    if is_causal_query(query):
        return QueryIntent.CAUSAL
    if is_recommendation_query(query):
        return QueryIntent.RECOMMENDATION
    if is_outlook_query(query):
        return QueryIntent.OUTLOOK
    if is_factual_query(query):
        return QueryIntent.FACTUAL
    return QueryIntent.GENERAL


def build_search_queries(
    user_query: str,
    tickers: list[str] | None = None,
    intent: QueryIntent | None = None,
) -> list[str]:
    tickers = tickers if tickers is not None else detect_tickers(user_query)
    intent = intent or classify_intent(user_query)
    queries = [user_query]

    for symbol in tickers:
        queries.append(f"{symbol} stock price market cap 1 month return")
        queries.append(f"{symbol} recent news headlines sentiment")

        if intent == QueryIntent.CAUSAL:
            queries.append(f"{symbol} stock decline fall reasons news")
            queries.append(f"{symbol} earnings guidance analyst downgrade")
        elif intent == QueryIntent.COMPARISON:
            queries.append(f"{symbol} performance momentum valuation")
        elif intent == QueryIntent.OUTLOOK:
            queries.append(f"{symbol} outlook trend analyst forecast")
        elif intent == QueryIntent.RECOMMENDATION:
            queries.append(f"{symbol} investment risk reward news")

    if intent == QueryIntent.COMPARISON and len(tickers) >= 2:
        pair = " vs ".join(tickers)
        queries.append(f"{pair} stock comparison performance")

    if intent == QueryIntent.CAUSAL and not tickers:
        queries.append("market news stock decline reasons sentiment")

    seen: set[str] = set()
    unique: list[str] = []
    for q in queries:
        key = q.lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(q)
    return unique
