import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import yfinance as yf
from llama_index.core import Document
from llama_index.core.schema import NodeWithScore, TextNode

from app.services.news_utils import analyze_sentiment, extract_yahoo_articles
from app.services.stocks import STOCK_MAP
from app.services.yfinance_snapshot import build_market_snapshot

logger = logging.getLogger(__name__)

LIVE_MARKET_SCORE = 0.99
LIVE_NEWS_SCORE = 0.95

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="yfinance-live")


def _build_market_node(symbol: str, text: str, fetched_at: str) -> NodeWithScore:
    node = TextNode(
        text=text,
        id_=f"ondemand_yf_price_{symbol}",
        metadata={
            "symbol": symbol,
            "type": "PRICE_UPDATE",
            "timestamp": fetched_at,
            "fetched_at": fetched_at,
            "source": "YahooFinance",
            "live": True,
        },
    )
    return NodeWithScore(node=node, score=LIVE_MARKET_SCORE)


def _build_news_node(symbol: str, article: dict, fetched_at: str) -> NodeWithScore:
    name = STOCK_MAP.get(symbol, symbol)
    body = article["title"]
    if article["summary"]:
        body += f"\nSummary: {article['summary']}"

    news_text = f"LATEST NEWS for {name} ({symbol}) [LIVE]: {body}"
    sentiment, score = analyze_sentiment(news_text)

    node = TextNode(
        text=f"[{sentiment}] {news_text}",
        id_=f"ondemand_yf_news_{symbol}_{article['id']}",
        metadata={
            "symbol": symbol,
            "type": "NEWS_ARTICLE",
            "sentiment": sentiment,
            "sentiment_score": score,
            "timestamp": article.get("pub_date") or fetched_at,
            "fetched_at": fetched_at,
            "source": "YahooFinance-News",
            "publisher": article.get("publisher", "Unknown"),
            "url": article.get("link", ""),
            "live": True,
        },
    )
    return NodeWithScore(node=node, score=LIVE_NEWS_SCORE)


def fetch_live_context_for_tickers(
    tickers: list[str],
    limit_news: int = 5,
) -> tuple[list[NodeWithScore], list[NodeWithScore]]:
    if not tickers:
        return [], []

    fetched_at = datetime.now().isoformat()
    market_nodes: list[NodeWithScore] = []
    news_nodes: list[NodeWithScore] = []

    for symbol in tickers:
        if symbol not in STOCK_MAP:
            continue
        try:
            ticker = yf.Ticker(symbol)

            snapshot = build_market_snapshot(symbol, ticker)
            market_nodes.append(_build_market_node(symbol, snapshot, fetched_at))
            logger.info("Live market snapshot for %s", symbol)

            articles = extract_yahoo_articles(ticker.news or [], limit=limit_news)
            for article in articles:
                news_nodes.append(_build_news_node(symbol, article, fetched_at))
            if articles:
                logger.info("Live Yahoo news: %d articles for %s", len(articles), symbol)

        except Exception as e:
            logger.warning("On-demand fetch failed for %s: %s", symbol, e)

    return market_nodes, news_nodes


def fetch_live_context_async(
    tickers: list[str],
    timeout: float = 15.0,
) -> tuple[list[NodeWithScore], list[NodeWithScore]]:
    if not tickers:
        return [], []
    future = _executor.submit(fetch_live_context_for_tickers, tickers)
    try:
        return future.result(timeout=timeout)
    except Exception as e:
        logger.warning("On-demand fetch timed out or failed: %s", e)
        return [], []


def persist_live_nodes(nodes: list[NodeWithScore]) -> None:
    if not nodes:
        return
    try:
        from app.engine.index import get_engine

        index, _ = get_engine()
        for nws in nodes:
            index.insert(
                Document(
                    text=nws.node.get_content(),
                    id_=nws.node.node_id,
                    metadata=nws.node.metadata,
                )
            )
    except Exception as e:
        logger.debug("Could not persist on-demand nodes: %s", e)


def persist_live_nodes_async(nodes: list[NodeWithScore]) -> None:
    if nodes:
        _executor.submit(persist_live_nodes, nodes)
