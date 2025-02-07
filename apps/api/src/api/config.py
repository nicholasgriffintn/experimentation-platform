from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    api_name: str = "Experimentation Platform API"
    debug_mode: bool = False
    
    database_url: str = "postgresql://postgres:postgres@localhost:5432/experiments"
    
    secret_key: str = "CHANGE_ME"
    
    cors_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings() 