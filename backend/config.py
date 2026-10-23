import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "EventPilot AI"
    APP_VERSION: str = "1.1.0"
    
    # AI Provider & Gemma Configuration
    # Supported providers: "ollama", "openai_compatible", "demo"
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "ollama")
    GEMMA_MODEL: str = os.getenv("GEMMA_MODEL", "gemma2:2b")
    INFERENCE_BASE_URL: str = os.getenv("INFERENCE_BASE_URL", "http://localhost:11434")
    INFERENCE_API_KEY: Optional[str] = os.getenv("INFERENCE_API_KEY", None)
    INFERENCE_TIMEOUT_SECONDS: int = int(os.getenv("INFERENCE_TIMEOUT_SECONDS", "60"))
    
    # Sentry Observability & Agent Tracing
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", None)
    SENTRY_ENVIRONMENT: str = os.getenv("SENTRY_ENVIRONMENT", "development")
    SENTRY_TRACES_SAMPLE_RATE: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "1.0"))
    SENTRY_PROFILES_SAMPLE_RATE: float = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "1.0"))
    
    # Database (SQLite default with repository pattern)
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "eventpilot.db")
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL", None)
    
    # Server / Render Deployment
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
