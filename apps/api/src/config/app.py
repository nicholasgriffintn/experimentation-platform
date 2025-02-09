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
    cors_origins: List[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:4173",  # Vite preview
        "http://localhost:3000",  # Alternative dev port
    ]
    
    # Iceberg Settings
    iceberg_catalog_name: str = "experimentation"
    iceberg_rest_uri: str = "http://localhost:8181"
    iceberg_warehouse: str = "s3://warehouse/iceberg/"
    iceberg_s3_endpoint: str = "http://localhost:9000"
    iceberg_s3_access_key: str = "admin"
    iceberg_s3_secret_key: str = "password"
    iceberg_catalog_impl: str = "org.apache.iceberg.rest.RESTCatalog"
    iceberg_io_impl: str = "org.apache.iceberg.aws.s3.S3FileIO"
    iceberg_namespace: str = "experiments"
    
    # AWS/Storage Settings
    warehouse_location: str = "s3://warehouse/iceberg/"
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

    @property
    def iceberg_catalog_config(self) -> dict:
        """Get Iceberg catalog configuration."""
        return {
            "type": "rest",
            "uri": self.iceberg_rest_uri,
            "s3.endpoint": self.iceberg_s3_endpoint,
            "s3.access-key-id": self.iceberg_s3_access_key,
            "s3.secret-access-key": self.iceberg_s3_secret_key,
            "warehouse": self.iceberg_warehouse,
            "catalog-impl": self.iceberg_catalog_impl,
            "io-impl": self.iceberg_io_impl,
            "s3.path-style-access": "true",
            "region": self.aws_region
        }

@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

settings = get_settings()