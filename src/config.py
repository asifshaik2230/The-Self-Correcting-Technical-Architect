import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Bulletproof Configuration for The Self-Correcting Technical Architect.
    Maps .env variables to both uppercase and lowercase attributes to support
    varying naming conventions across different agent nodes.
    """
    # Google Gemini Configuration
    GOOGLE_API_KEY: str
    google_api_key: str = ""

    GEMINI_MODEL: str = "gemini-1.5-pro"
    gemini_model: str = "gemini-1.5-pro"

    # E2B Configuration
    E2B_API_KEY: str
    e2b_api_key: str = ""

    # Tavily for Phase 2
    TAVILY_API_KEY: str = ""
    tavily_api_key: str = ""

    # Memory Configuration for Phase 3
    MEMORY_FILE_PATH: str = "logs/experience_memory.json"
    memory_file_path: str = "logs/experience_memory.json"

    # ChromaDB Configuration for Docker
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000

    # PostgreSQL Configuration for LangGraph Persistence
    POSTGRES_URI: str = "postgresql://postgres:postgres@localhost:5432/architect_memory"

    # Agent Configuration
    max_retries: int = 3
    MAX_RETRIES: int = 3
    code_execution_timeout: int = 30
    CODE_EXECUTION_TIMEOUT: int = 30

    # Project Configuration
    PROJECT_NAME: str = "Self-Correcting Technical Architect"
    ENVIRONMENT: str = "development"
    DEBUG_MODE: bool = False

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    def __init__(self, **values):
        super().__init__(**values)
        self.google_api_key = self.GOOGLE_API_KEY
        self.gemini_model = self.GEMINI_MODEL
        self.e2b_api_key = self.E2B_API_KEY
        self.tavily_api_key = self.TAVILY_API_KEY
        self.memory_file_path = self.MEMORY_FILE_PATH

# Global settings instance
settings = Settings()