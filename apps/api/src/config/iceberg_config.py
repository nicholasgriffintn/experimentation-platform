from pydantic_settings import BaseSettings, SettingsConfigDict
from pyiceberg.catalog.hive import HiveCatalog


class IcebergConfig(BaseSettings):
    warehouse_location: str = "s3://your-bucket/warehouse"
    catalog_name: str = "experiment_catalog"
    catalog_type: str = "hive"

    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "us-east-1"

    hive_metastore_uris: str = "thrift://localhost:9083"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


def create_catalog(config: IcebergConfig):
    """Create and configure Iceberg catalog"""
    return HiveCatalog(
        name="default",
        uri=config.hive_metastore_uris,
        warehouse=config.warehouse_location,
        s3=dict(
            access_key_id=config.aws_access_key_id,
            secret_access_key=config.aws_secret_access_key,
            region=config.aws_region,
        ),
    )
