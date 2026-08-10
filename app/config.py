import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "ChaosPilot"
    VERSION: str = "2.0.0"
    API_PREFIX: str = "/api"
    
    # Gemini Configuration
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL_FAST: str = "gemini-2.5-flash"
    GEMINI_MODEL_PRO: str = "gemini-2.5-pro"
    
    # MySQL Credentials Configuration
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "root"
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DB: str = "chaospilot"
    
    # Storage Configuration (Defaults to MySQL, configurable via env)
    DATABASE_URL: str = "mysql+aiomysql://root:root@localhost:3306/chaospilot"
    FALLBACK_DATABASE_URL: str = "sqlite+aiosqlite:///./chaospilot.db"
    ARTIFACTS_DIR: str = "./artifacts"
    
    # Exploration Guardrails Defaults
    DEFAULT_MAX_DEPTH: int = 3
    DEFAULT_MAX_PAGES: int = 25
    STEP_TIMEOUT_SECONDS: int = 15
    RUN_TIMEOUT_MINUTES: int = 15
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure artifacts directory exists
os.makedirs(settings.ARTIFACTS_DIR, exist_ok=True)
