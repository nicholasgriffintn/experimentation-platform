from pydantic import BaseSettings
from pyiceberg.catalog import Catalog, Catalogs

class IcebergConfig(BaseSettings):
    warehouse_location: str = "s3://your-bucket/warehouse"
    catalog_name: str = "experiment_catalog"
    catalog_type: str = "hive"
    
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "us-east-1"
    
    hive_metastore_uris: str = "thrift://localhost:9083"
    
    class Config:
        env_file = ".env"

def create_catalog(config: IcebergConfig) -> Catalog:
    """Create and configure Iceberg catalog"""
    catalog_properties = {
        "warehouse": config.warehouse_location,
        "uri": config.hive_metastore_uris,
        "client.id": "experiment-platform",
        
        "aws.access.key-id": config.aws_access_key_id,
        "aws.secret.access-key": config.aws_secret_access_key,
        "aws.region": config.aws_region,
        
        "catalog-impl": "org.apache.iceberg.aws.glue.GlueCatalog",
        "io-impl": "org.apache.iceberg.aws.s3.S3FileIO",
    }
    
    return Catalogs.load(config.catalog_name, catalog_properties)