"""Multi-query retrieval with intent-aware boosting."""

import logging

from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle
from app.services.on_demand_fetch import (
    LIVE_MARKET_SCORE,
    LIVE_NEWS_SCORE,
    fetch_live_context_async,
    persist_live_nodes_async,
)
from app.services.query_context import (
    QueryIntent,
    build_search_queries,
    classify_intent,
    detect_tickers,
)

logger = logging.getLogger(__name__)

NEWS_TYPES = frozenset({"NEWS_ARTICLE", "MARKET_NEWS"})


class EnrichedRetriever(BaseRetriever):
    """Intent-aware retrieval with live yfinance injection per ticker."""

    def __init__(self, index, reranker, similarity_top_k: int = 6):
        self._base = index.as_retriever(similarity_top_k=similarity_top_k)
        self._reranker = reranker
        super().__init__()

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        user_query = query_bundle.query_str
        tickers = detect_tickers(user_query)
        intent = classify_intent(user_query)
        search_queries = build_search_queries(user_query, tickers, intent)

        merged: dict[str, NodeWithScore] = {}
        for sq in search_queries:
            for node in self._base.retrieve(QueryBundle(sq)):
                nid = node.node.node_id
                score = node.score or 0.0
                if nid not in merged or score > (merged[nid].score or 0.0):
                    merged[nid] = node

        market_nodes: list[NodeWithScore] = []
        if tickers:
            market_nodes, news_nodes = fetch_live_context_async(tickers)

            for node in market_nodes:
                node.score = LIVE_MARKET_SCORE
                merged[node.node.node_id] = node

            for node in news_nodes:
                node.score = LIVE_NEWS_SCORE
                merged[node.node.node_id] = node

            if market_nodes or news_nodes:
                logger.info(
                    "Intent=%s | Merged %d market + %d news for %s",
                    intent.value,
                    len(market_nodes),
                    len(news_nodes),
                    tickers,
                )
                persist_live_nodes_async(market_nodes + news_nodes)

        nodes = list(merged.values())

        # Intent-specific score boosts before rerank
        for node in nodes:
            meta = node.node.metadata or {}
            sym = meta.get("symbol")
            ntype = meta.get("type")

            if tickers and sym in tickers:
                node.score = (node.score or 0.0) + 0.1

            if intent == QueryIntent.CAUSAL and ntype in NEWS_TYPES:
                node.score = (node.score or 0.0) + 0.2
            elif intent == QueryIntent.COMPARISON and ntype in NEWS_TYPES:
                node.score = (node.score or 0.0) + 0.05
            elif intent in (QueryIntent.OUTLOOK, QueryIntent.RECOMMENDATION):
                if ntype in NEWS_TYPES:
                    node.score = (node.score or 0.0) + 0.1

        nodes.sort(key=lambda n: n.score or 0.0, reverse=True)
        cap = 28 if intent == QueryIntent.COMPARISON else 20
        nodes = nodes[:cap]

        reranked = self._reranker.postprocess_nodes(nodes, query_bundle=query_bundle)

        # Always pin live market snapshots for every detected ticker
        if market_nodes and tickers:
            by_symbol = {n.node.metadata.get("symbol"): n for n in market_nodes}
            pinned = [by_symbol[s] for s in tickers if s in by_symbol]
            pinned_ids = {n.node.node_id for n in pinned}
            rest = [n for n in reranked if n.node.node_id not in pinned_ids]
            reranked = pinned + rest
            reranked = reranked[:cap]

        return reranked
