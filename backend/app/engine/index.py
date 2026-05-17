import logging
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.llms.openai_like import OpenAILike
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from app.core.config import settings

logger = logging.getLogger(__name__)

_cached_index = None
_cached_reranker = None
_engine_ready = False


def _create_sparse_encoder():
    from fastembed.sparse.sparse_text_embedding import SparseTextEmbedding

    logger.info("Loading Splade sparse model (CPU)...")
    sparse_model = SparseTextEmbedding(
        model_name="prithivida/Splade_PP_en_v1",
        providers=["CPUExecutionProvider"],
    )

    def encode(texts):
        embeddings = sparse_model.embed(texts)
        indices, values = zip(
            *[
                (embedding.indices.tolist(), embedding.values.tolist())
                for embedding in embeddings
            ]
        )
        return list(indices), list(values)

    return encode


def get_engine():
    global _cached_index, _cached_reranker, _engine_ready

    if _engine_ready:
        return _cached_index, _cached_reranker

    logger.info("Initializing RAG engine (first call – models will be downloaded)...")

    llm = OpenAILike(
        model=settings.GROQ_MODEL,
        api_base=settings.GROQ_API_BASE,
        api_key=settings.GROQ_API_KEY,
        is_chat_model=True,
        temperature=0.1,
    )

    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-base-en-v1.5")

    Settings.llm = llm
    Settings.embed_model = embed_model

    sparse_fn = _create_sparse_encoder()

    client = QdrantClient(url=settings.QDRANT_URL)
    vector_store = QdrantVectorStore(
        client=client,
        collection_name="streaming_rag",
        enable_hybrid=True,
        sparse_doc_fn=sparse_fn,
        sparse_query_fn=sparse_fn,
    )

    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    _cached_index = VectorStoreIndex.from_vector_store(
        vector_store, storage_context=storage_context
    )

    _cached_reranker = SentenceTransformerRerank(
        model="cross-encoder/ms-marco-MiniLM-L-6-v2",
        top_n=10,
    )

    _engine_ready = True
    logger.info("✅ RAG engine initialized successfully.")
    return _cached_index, _cached_reranker


def is_engine_ready() -> bool:
    return _engine_ready


from llama_index.core import PromptTemplate
from llama_index.core.query_engine import RetrieverQueryEngine
from app.engine.retrieval import EnrichedRetriever
from app.engine.prompts import prompt_for_query, GENERAL_PROMPT


def get_query_engine(streaming=True, query: str | None = None):
    index, reranker = get_engine()
    retriever = EnrichedRetriever(index, reranker)

    query_engine = RetrieverQueryEngine.from_args(
        retriever=retriever,
        streaming=streaming,
    )

    query_engine.update_prompts(
        {
            "response_synthesizer:text_qa_template": (
                prompt_for_query(query) if query else PromptTemplate(GENERAL_PROMPT)
            )
        }
    )

    return query_engine
