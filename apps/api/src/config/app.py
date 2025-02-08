from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    api_name: str = "Experimentation Platform API"
    api_description: str = "API for managing and analyzing experiments"
    api_version: str = "0.1.0"
    debug_mode: bool = False
    
    # Database Settings
    database_url: str = "postgresql://postgres:postgres@localhost:5432/experiments"
    
    # Security Settings
    secret_key: str = "CHANGE_ME"
    cors_origins: List[str] = ["*"]
    
    # AWS/Storage Settings
    warehouse_location: str = "s3://your-bucket/warehouse"
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "us-east-1"
    
    # Cache Settings
    redis_url: str = "redis://localhost:6379/0"
    
    # Experiment Settings
    default_confidence_level: float = 0.95
    min_sample_size: int = 100
    analysis_check_interval: int = 3600  # 1 hour in seconds
    
    # Scheduler Settings
    scheduler_enabled: bool = True
    scheduler_check_interval: int = 60  # seconds
    
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