import asyncio
import hashlib
import httpx
import time
import yfinance as yf
from app.services.telemetry_state import record_ingestion_cycle
from llama_index.core import Document
from app.engine.index import get_engine
from app.core.config import settings
from app.services.news_utils import analyze_sentiment, extract_yahoo_articles
from app.services.yfinance_snapshot import build_market_snapshot
from datetime import datetime
from app.services.stocks import STOCK_MAP


async def fetch_yfinance_data(index) -> tuple[int, int, list[str], float]:
    market_docs = 0
    news_docs = 0
    errors: list[str] = []
    embed_ms = 0.0

    for symbol, name in STOCK_MAP.items():
        try:
            ticker = yf.Ticker(symbol)
            combined_text = build_market_snapshot(symbol, ticker)

            price_doc = Document(
                text=combined_text,
                id_=f"yf_price_{symbol}",
                metadata={
                    "symbol": symbol,
                    "type": "PRICE_UPDATE",
                    "timestamp": datetime.now().isoformat(),
                    "source": "YahooFinance",
                },
            )
            t0 = time.perf_counter()
            index.insert(price_doc)
            embed_ms += (time.perf_counter() - t0) * 1000
            market_docs += 1

            articles = extract_yahoo_articles(ticker.news or [], limit=5)
            if articles:
                for article in articles:
                    body = article["title"]
                    if article["summary"]:
                        body += f"\nSummary: {article['summary']}"
                    news_text = f"LATEST NEWS for {name} ({symbol}): {body}"
                    sentiment, score = analyze_sentiment(news_text)

                    doc = Document(
                        text=f"[{sentiment}] {news_text}",
                        id_=f"yf_news_{symbol}_{article['id']}",
                        metadata={
                            "symbol": symbol,
                            "type": "NEWS_ARTICLE",
                            "sentiment": sentiment,
                            "sentiment_score": score,
                            "timestamp": article.get("pub_date")
                            or datetime.now().isoformat(),
                            "source": "YahooFinance-News",
                            "publisher": article.get("publisher", "Unknown"),
                            "url": article.get("link", ""),
                        },
                    )
                    t0 = time.perf_counter()
                    index.insert(doc)
                    embed_ms += (time.perf_counter() - t0) * 1000
                    news_docs += 1
                print(f"✅ Indexed price + {len(articles)} news articles for {symbol}")
            else:
                print(f"✅ Indexed price data for {symbol} (no Yahoo news available)")

        except Exception as e:
            errors.append(f"{symbol}: {e}")
            print(f"❌ Error fetching YF for {symbol}: {e}")
        await asyncio.sleep(0.5)

    return market_docs, news_docs, errors, embed_ms


async def fetch_marketaux_news(index) -> tuple[int, list[str], float]:
    if not settings.MARKETAUX_API_KEY or settings.MARKETAUX_API_KEY == "your_marketaux_api_key":
        print("⚠️ MarketAux API Key not configured. Skipping...")
        return 0, [], 0.0

    url = "https://api.marketaux.com/v1/news/all"
    symbols = [s for s in STOCK_MAP.keys() if "-" not in s]
    params = {
        "api_token": settings.MARKETAUX_API_KEY,
        "symbols": ",".join(symbols),
        "filter_entities": "true",
        "language": "en",
        "limit": 20,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                print(f"❌ MarketAux API Error: {response.status_code} - {response.text}")
                return 0, [f"MarketAux HTTP {response.status_code}"], 0.0

            articles = response.json().get("data", [])
            indexed = 0
            embed_ms = 0.0
            for article in articles:
                title = article.get("title", "")
                description = article.get("description", "") or ""
                if not title:
                    continue

                entity_symbols = []
                for entity in article.get("entities", []):
                    sym = entity.get("symbol")
                    if sym and sym in STOCK_MAP:
                        entity_symbols.append(sym)

                news_text = f"MarketAux News: {title}. {description}"
                sentiment, score = analyze_sentiment(news_text)

                stable_id = article.get("uuid") or hashlib.md5(
                    f"{title}{article.get('published_at', '')}".encode()
                ).hexdigest()[:16]

                doc = Document(
                    text=f"[{sentiment}] {news_text}",
                    id_=f"marketaux_{stable_id}",
                    metadata={
                        "type": "MARKET_NEWS",
                        "symbols": ",".join(entity_symbols) if entity_symbols else "",
                        "symbol": entity_symbols[0] if entity_symbols else "",
                        "sentiment": sentiment,
                        "sentiment_score": score,
                        "timestamp": article.get(
                            "published_at", datetime.now().isoformat()
                        ),
                        "source": "MarketAux",
                        "url": article.get("url", ""),
                    },
                )
                t0 = time.perf_counter()
                index.insert(doc)
                embed_ms += (time.perf_counter() - t0) * 1000
                indexed += 1

            print(f"✅ Indexed {indexed} articles from MarketAux")
            return indexed, [], embed_ms

    except Exception as e:
        print(f"❌ MarketAux Request Failed: {e}")
        return 0, [str(e)], 0.0


async def live_ingestion_loop():
    index, _ = get_engine()

    while True:
        print(
            f"\n--- Starting Live Ingestion Cycle [{datetime.now().strftime('%H:%M:%S')}] ---"
        )

        started = time.perf_counter()
        errors: list[str] = []
        market_docs = 0
        news_docs = 0
        embed_ms = 0.0
        status = "success"

        try:
            yf_result, ma_result = await asyncio.gather(
                fetch_yfinance_data(index),
                fetch_marketaux_news(index),
            )
            market_docs = yf_result[0]
            news_docs = yf_result[1] + ma_result[0]
            errors = yf_result[2] + ma_result[1]
            embed_ms = yf_result[3] + ma_result[2]
            if errors:
                status = "partial"
        except Exception as e:
            status = "error"
            errors.append(str(e))

        record_ingestion_cycle(
            duration_ms=(time.perf_counter() - started) * 1000,
            embed_ms=embed_ms,
            status=status,
            market_docs=market_docs,
            news_docs=news_docs,
            errors=errors,
        )

        print("--- Cycle Completed. Next in 30 seconds ---")
        await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(live_ingestion_loop())
