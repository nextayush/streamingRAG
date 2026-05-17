import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    GROK_API_KEY: str = os.getenv("GROK_API_KEY", "")
    GROK_API_BASE: str = os.getenv("GROK_API_BASE", "https://api.x.ai/v1")
    GROK_MODEL: str = os.getenv("GROK_MODEL", "grok-beta")
    
    MARKETAUX_API_KEY: str = os.getenv("MARKETAUX_API_KEY", "")
    
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    PROJECT_NAME: str = "Streaming RAG Pro"
    VERSION: str = "1.0.0"

settings = Settings()
