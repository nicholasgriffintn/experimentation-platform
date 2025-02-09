from pyiceberg.schema import Schema
from pyiceberg.types import (
    DoubleType,
    LongType,
    MapType,
    StringType,
    TimestampType,
)


class IcebergSchemas:
    @staticmethod
    def get_events_schema() -> Schema:
        """Schema for experiment events table"""
        return Schema(
            Schema.NestedField.required(1, "event_id", StringType()),
            Schema.NestedField.required(2, "experiment_id", StringType()),
            Schema.NestedField.required(3, "timestamp", TimestampType()),
            Schema.NestedField.required(4, "user_id", StringType()),
            Schema.NestedField.required(5, "variant_id", StringType()),
            Schema.NestedField.required(6, "event_type", StringType()),
            Schema.NestedField.optional(7, "event_value", DoubleType()),
            Schema.NestedField.optional(8, "client_id", StringType()),
            Schema.NestedField.optional(9, "metadata", MapType(StringType(), StringType())),
        )

    @staticmethod
    def get_metrics_schema() -> Schema:
        """Schema for experiment metrics table"""
        return Schema(
            Schema.NestedField.required(1, "metric_id", StringType()),
            Schema.NestedField.required(2, "experiment_id", StringType()),
            Schema.NestedField.required(3, "variant_id", StringType()),
            Schema.NestedField.required(4, "timestamp", TimestampType()),
            Schema.NestedField.required(5, "metric_name", StringType()),
            Schema.NestedField.required(6, "metric_value", DoubleType()),
            Schema.NestedField.optional(7, "segment", StringType()),
            Schema.NestedField.optional(8, "metadata", MapType(StringType(), StringType())),
        )

    @staticmethod
    def get_assignments_schema() -> Schema:
        """Schema for user-variant assignments table"""
        return Schema(
            Schema.NestedField.required(1, "assignment_id", StringType()),
            Schema.NestedField.required(2, "experiment_id", StringType()),
            Schema.NestedField.required(3, "user_id", StringType()),
            Schema.NestedField.required(4, "variant_id", StringType()),
            Schema.NestedField.required(5, "timestamp", TimestampType()),
            Schema.NestedField.optional(6, "context", MapType(StringType(), StringType())),
        )

    @staticmethod
    def get_results_schema() -> Schema:
        """Schema for experiment results table"""
        return Schema(
            Schema.NestedField.required(1, "result_id", StringType()),
            Schema.NestedField.required(2, "experiment_id", StringType()),
            Schema.NestedField.required(3, "variant_id", StringType()),
            Schema.NestedField.required(4, "metric_name", StringType()),
            Schema.NestedField.required(5, "timestamp", TimestampType()),
            Schema.NestedField.required(6, "sample_size", LongType()),
            Schema.NestedField.required(7, "mean", DoubleType()),
            Schema.NestedField.required(8, "variance", DoubleType()),
            Schema.NestedField.optional(9, "confidence_level", DoubleType()),
            Schema.NestedField.optional(10, "p_value", DoubleType()),
            Schema.NestedField.optional(11, "metadata", MapType(StringType(), StringType())),
        )
