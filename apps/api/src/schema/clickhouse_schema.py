class ClickHouseSchemas:
    @staticmethod
    def get_events_schema() -> str:
        """Schema for experiment events table"""
        return """
        CREATE TABLE IF NOT EXISTS {database}.{table_name} (
            event_id String,
            experiment_id String,
            timestamp DateTime64(3),
            user_id String,
            variant_id String,
            event_type String,
            event_value Nullable(Float64),
            client_id Nullable(String),
            metadata Map(String, String)
        ) ENGINE = MergeTree()
        PARTITION BY (experiment_id, toYYYYMMDD(timestamp))
        ORDER BY (experiment_id, timestamp, user_id)
        SETTINGS index_granularity = 8192
        """

    @staticmethod
    def get_metrics_schema() -> str:
        """Schema for experiment metrics table"""
        return """
        CREATE TABLE IF NOT EXISTS {database}.{table_name} (
            metric_id String,
            experiment_id String,
            variant_id String,
            timestamp DateTime64(3),
            metric_name String,
            metric_value Float64,
            segment Nullable(String),
            metadata Map(String, String)
        ) ENGINE = MergeTree()
        PARTITION BY (experiment_id, toYYYYMM(timestamp))
        ORDER BY (experiment_id, metric_name, timestamp)
        SETTINGS index_granularity = 8192
        """

    @staticmethod
    def get_assignments_schema() -> str:
        """Schema for user-variant assignments table"""
        return """
        CREATE TABLE IF NOT EXISTS {database}.{table_name} (
            assignment_id String,
            experiment_id String,
            user_id String,
            variant_id String,
            timestamp DateTime64(3),
            context Map(String, String)
        ) ENGINE = MergeTree()
        PARTITION BY experiment_id
        ORDER BY (experiment_id, user_id, timestamp)
        SETTINGS index_granularity = 8192
        """

    @staticmethod
    def get_results_schema() -> str:
        """Schema for experiment results table"""
        return """
        CREATE TABLE IF NOT EXISTS {database}.{table_name} (
            result_id String,
            experiment_id String,
            variant_id String,
            metric_name String,
            timestamp DateTime64(3),
            sample_size Int64,
            mean Float64,
            variance Float64,
            confidence_level Nullable(Float64),
            p_value Nullable(Float64),
            metadata Map(String, String)
        ) ENGINE = MergeTree()
        PARTITION BY (experiment_id, metric_name)
        ORDER BY (experiment_id, metric_name, timestamp)
        SETTINGS index_granularity = 8192
        """ 