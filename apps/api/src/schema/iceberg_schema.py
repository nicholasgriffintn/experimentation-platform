from pyiceberg.schema import Schema
from pyiceberg.types import (
    DoubleType,
    LongType,
    MapType,
    NestedField,
    StringType,
    TimestampType,
)


class IcebergSchemas:
    @staticmethod
    def get_events_schema() -> Schema:
        """Schema for experiment events table"""
        schema = Schema(
            NestedField(1, "event_id", StringType(), required=True),
            NestedField(2, "experiment_id", StringType(), required=True),
            NestedField(3, "timestamp", TimestampType(), required=True),
            NestedField(4, "user_id", StringType(), required=True),
            NestedField(5, "variant_id", StringType(), required=True),
            NestedField(6, "event_type", StringType(), required=True),
            NestedField(7, "event_value", DoubleType(), required=False),
            NestedField(8, "client_id", StringType(), required=False),
            NestedField(9, "metadata", MapType(key_type=StringType(), value_type=StringType()), required=False),
        )
        return schema

    @staticmethod
    def get_metrics_schema() -> Schema:
        """Schema for experiment metrics table"""
        schema = Schema(
            NestedField(1, "metric_id", StringType(), required=True),
            NestedField(2, "experiment_id", StringType(), required=True),
            NestedField(3, "variant_id", StringType(), required=True),
            NestedField(4, "timestamp", TimestampType(), required=True),
            NestedField(5, "metric_name", StringType(), required=True),
            NestedField(6, "metric_value", DoubleType(), required=True),
            NestedField(7, "segment", StringType(), required=False),
            NestedField(8, "metadata", MapType(key_type=StringType(), value_type=StringType()), required=False),
        )
        return schema

    @staticmethod
    def get_assignments_schema() -> Schema:
        """Schema for user-variant assignments table"""
        schema = Schema(
            NestedField(1, "assignment_id", StringType(), required=True),
            NestedField(2, "experiment_id", StringType(), required=True),
            NestedField(3, "user_id", StringType(), required=True),
            NestedField(4, "variant_id", StringType(), required=True),
            NestedField(5, "timestamp", TimestampType(), required=True),
            NestedField(6, "context", MapType(key_type=StringType(), value_type=StringType()), required=False),
        )
        return schema

    @staticmethod
    def get_results_schema() -> Schema:
        """Schema for experiment results table"""
        schema = Schema(
            NestedField(1, "result_id", StringType(), required=True),
            NestedField(2, "experiment_id", StringType(), required=True),
            NestedField(3, "variant_id", StringType(), required=True),
            NestedField(4, "metric_name", StringType(), required=True),
            NestedField(5, "timestamp", TimestampType(), required=True),
            NestedField(6, "sample_size", LongType(), required=True),
            NestedField(7, "mean", DoubleType(), required=True),
            NestedField(8, "variance", DoubleType(), required=True),
            NestedField(9, "confidence_level", DoubleType(), required=False),
            NestedField(10, "p_value", DoubleType(), required=False),
            NestedField(11, "metadata", MapType(key_type=StringType(), value_type=StringType()), required=False),
        )
        return schema
