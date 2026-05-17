# Streaming RAG Pro

A professional, full-stack real-time streaming RAG (Retrieval-Augmented Generation) system.

## Tech Stack
- **LLM**: xAI Grok (via OpenAI-compatible API)
- **Framework**: LlamaIndex
- **Backend**: FastAPI
- **Vector Database**: Qdrant (Hybrid Search)
- **Embeddings**: BGE Base v1.5
- **Reranker**: BGE Reranker Base
- **Caching**: Redis
- **Frontend**: Next.js 14 (App Router)
- **Live Data**: yfinance + MarketAux API (100% Live Ingestion)
- **Styling**: Premium Vanilla CSS

## Prerequisites
- Docker & Docker Compose
- Python 3.10+
- Node.js 18+
- xAI API Key (Grok)

## Getting Started

### One-Command Setup (Recommended)
You can launch the entire stack (Docker, Backend, and Frontend) with a single command using Git Bash or any Unix-like terminal:

```bash
./run.sh
```

This script automatically:
1. Starts the Docker containers (Qdrant & Redis)
2. Sets up the Python virtual environment and installs backend dependencies
3. Installs Node modules for the frontend
4. Starts both the FastAPI backend and Next.js frontend in parallel
5. Gracefully handles shutdown of all services when you press `Ctrl+C`

### Manual Setup
If you prefer to start services individually:

#### 1. Infrastructure
Spin up Qdrant and Redis using Docker:
```bash
docker-compose -f docker/docker-compose.yml up -d
```

#### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows Git Bash: source venv/Scripts/activate
pip install -r requirements.txt
```

Create a `.env` file in the root (see `.env` template) and add your API keys.

Run the backend:
```bash
python main.py
```

#### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to start chatting.

### 4. Document Ingestion
Place your documents in `backend/data` and run the ingestion script:
```bash
cd backend
python -m app.services.ingestion ./data
```

## Architecture
- **100% Live Ingestion**: The system operates without static documents. A background orchestrator in FastAPI concurrently fetches:
    - **Prices**: Real-time ticker data from `yfinance`.
    - **Global News**: High-fidelity market news from `MarketAux`.
- **SSE (Server-Sent Events)**: Used for real-time token streaming from the LLM.
- **Hybrid Search**: Combines dense (vector) and sparse (keyword) search for better retrieval.
- **Reranking**: Uses BGE Reranker to prioritize the most relevant chunks before generation.
- **Premium UI**: Dark mode, glassmorphism, and smooth animations using Framer Motion.