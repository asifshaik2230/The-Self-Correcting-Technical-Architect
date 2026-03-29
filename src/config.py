import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Bulletproof Configuration for The Self-Correcting Technical Architect.
    Maps .env variables to both uppercase and lowercase attributes to support
    varying naming conventions across different agent nodes.
    """
    # OpenAI Configuration
    OPENAI_API_KEY: str
    openai_api_key: str = "" # Alias for lowercase calls

    OPENAI_MODEL: str = "gpt-4-turbo"
    openai_model: str = "gpt-4-turbo" # Fixes the Researcher node error

    # E2B Configuration
    E2B_API_KEY: str
    e2b_api_key: str = ""

    # Tavily for Phase 2
    TAVILY_API_KEY: str = ""
    tavily_api_key: str = ""

    # Memory Configuration for Phase 3
    MEMORY_FILE_PATH: str = "logs/experience_memory.json"
    memory_file_path: str = "logs/experience_memory.json"

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
        # Ensure aliases are populated if only uppercase exists in .env
        self.openai_api_key = self.OPENAI_API_KEY
        self.openai_model = self.OPENAI_MODEL
        self.e2b_api_key = self.E2B_API_KEY
        self.tavily_api_key = self.TAVILY_API_KEY
        self.memory_file_path = self.MEMORY_FILE_PATH

# Global settings instance
settings = Settings()