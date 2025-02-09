from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
from pyiceberg.catalog import Catalog
from pyiceberg.table import Table
from pyiceberg.schema import Schema
from pyiceberg.partitioning import PartitionSpec

from ..schema.iceberg import IcebergSchemas

class IcebergDataService:
    def __init__(self, catalog: Catalog):
        self.catalog = catalog
        self.schemas = IcebergSchemas()

    async def initialize_experiment_tables(self, experiment_id: str) -> None:
        """Initialize all required tables for a new experiment"""
        namespace = "experiments"
        
        events_spec = PartitionSpec.builder() \
            .identity("experiment_id") \
            .day("timestamp") \
            .build()
            
        self.create_table(
            f"{namespace}.{experiment_id}_events",
            self.schemas.get_events_schema(),
            events_spec
        )

        metrics_spec = PartitionSpec.builder() \
            .identity("experiment_id") \
            .month("timestamp") \
            .build()
            
        self.create_table(
            f"{namespace}.{experiment_id}_metrics",
            self.schemas.get_metrics_schema(),
            metrics_spec
        )

        assignments_spec = PartitionSpec.builder() \
            .identity("experiment_id") \
            .build()
            
        self.create_table(
            f"{namespace}.{experiment_id}_assignments",
            self.schemas.get_assignments_schema(),
            assignments_spec
        )

        results_spec = PartitionSpec.builder() \
            .identity("experiment_id") \
            .identity("metric_name") \
            .build()
            
        self.create_table(
            f"{namespace}.{experiment_id}_results",
            self.schemas.get_results_schema(),
            results_spec
        )

    def create_table(self, table_name: str, schema: Schema, partition_spec: PartitionSpec):
        """Create a new Iceberg table"""
        try:
            self.catalog.create_table(
                table_name,
                schema,
                partition_spec
            )
        except Exception as e:
            raise Exception(f"Failed to create table {table_name}: {str(e)}")

    async def get_experiment_config(self, experiment_id: str) -> Dict:
        """Get experiment configuration from database"""
        assignments_table = self.load_table(f"experiments.{experiment_id}_assignments")
        
        snapshot = assignments_table.current_snapshot()
        if not snapshot:
            return {
                'id': experiment_id,
                'metrics': {},
                'variants': []
            }
            
        scanner = assignments_table.new_scan() \
            .use_snapshot(snapshot.snapshot_id) \
            .filter(
                assignments_table.expr.ref("experiment_id").eq(experiment_id)
            ) \
            .select(
                "variant_id",
                "context"
            )
            
        assignments = list(scanner.plan_scan())
        
        variants = list({
            assignment['variant_id']: {
                'id': assignment['variant_id'],
                'context': assignment['context']
            }
            for assignment in assignments
        }.values())
        
        metrics_table = self.load_table(f"experiments.{experiment_id}_metrics")
        metrics_snapshot = metrics_table.current_snapshot()
        
        if metrics_snapshot:
            metrics_scanner = metrics_table.new_scan() \
                .use_snapshot(metrics_snapshot.snapshot_id) \
                .filter(
                    metrics_table.expr.ref("experiment_id").eq(experiment_id)
                ) \
                .select(
                    "metric_name",
                    "metadata"
                )
                
            metrics = list(metrics_scanner.plan_scan())
            metrics_config = {
                metric['metric_name']: metric['metadata']
                for metric in metrics
            }
        else:
            metrics_config = {}
        
        return {
            'id': experiment_id,
            'metrics': metrics_config,
            'variants': variants
        }

    async def record_event(self, experiment_id: str, event_data: Dict) -> None:
        """Record an event for the experiment"""
        table = self.load_table(f"experiments.{experiment_id}_events")
        
        with table.new_transaction() as transaction:
            transaction.new_append() \
                .add_row({
                    "event_id": str(uuid.uuid4()),
                    "experiment_id": experiment_id,
                    "timestamp": datetime.utcnow(),
                    "user_id": event_data.get("user_id"),
                    "variant_id": event_data.get("variant_id"),
                    "event_type": event_data.get("event_type"),
                    "event_value": event_data.get("value"),
                    "client_id": event_data.get("client_id"),
                    "metadata": event_data.get("metadata", {})
                }) \
                .commit()
            
            transaction.commit()

    async def record_metric(self, experiment_id: str, metric_data: Dict) -> None:
        """Record a metric measurement"""
        table = self.load_table(f"experiments.{experiment_id}_metrics")
        
        with table.new_transaction() as transaction:
            transaction.new_append() \
                .add_row({
                    "metric_id": str(uuid.uuid4()),
                    "experiment_id": experiment_id,
                    "variant_id": metric_data.get("variant_id"),
                    "timestamp": datetime.utcnow(),
                    "metric_name": metric_data.get("metric_name"),
                    "metric_value": metric_data.get("metric_value"),
                    "segment": metric_data.get("segment"),
                    "metadata": metric_data.get("metadata", {})
                }) \
                .commit()
            
            transaction.commit()

    async def assign_variant(self, experiment_id: str, user_id: str, variant_id: str, context: Optional[Dict] = None):
        """Record a user-variant assignment"""
        table = self.load_table(f"experiments.{experiment_id}_assignments")
        
        with table.new_transaction() as transaction:
            transaction.new_append() \
                .add_row({
                    "assignment_id": str(uuid.uuid4()),
                    "experiment_id": experiment_id,
                    "user_id": user_id,
                    "variant_id": variant_id,
                    "timestamp": datetime.utcnow(),
                    "context": context or {}
                }) \
                .commit()
            
            transaction.commit()

    async def record_results(self, experiment_id: str, results_data: Dict) -> None:
        """Record analysis results"""
        table = self.load_table(f"experiments.{experiment_id}_results")
        
        metrics_results = results_data.get("metrics", {})
        timestamp = datetime.utcnow()
        
        with table.new_transaction() as transaction:
            append = transaction.new_append()
            
            for metric_name, metric_results in metrics_results.items():
                for variant_id, result in metric_results.items():
                    append.add_row({
                        "result_id": str(uuid.uuid4()),
                        "experiment_id": experiment_id,
                        "variant_id": variant_id,
                        "metric_name": metric_name,
                        "timestamp": timestamp,
                        "sample_size": result.get("sample_size", 0),
                        "mean": result.get("mean", 0.0),
                        "variance": result.get("variance", 0.0),
                        "confidence_level": result.get("confidence_level"),
                        "p_value": result.get("p_value"),
                        "metadata": {
                            "status": results_data.get("status"),
                            "total_users": results_data.get("total_users"),
                            "correction_method": results_data.get("correction_method")
                        }
                    })
            
            append.commit()
            transaction.commit()

    def load_table(self, table_name: str) -> Table:
        """Load an Iceberg table"""
        return self.catalog.load_table(table_name)

    async def query_events(self, experiment_id: str, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Query events within a time range"""
        table = self.load_table(f"experiments.{experiment_id}_events")
        
        snapshot = table.current_snapshot()
        scanner = table.new_scan() \
            .use_snapshot(snapshot.snapshot_id) \
            .filter(
                table.expr.and_(
                    table.expr.ref("timestamp").gt(start_time),
                    table.expr.ref("timestamp").lt(end_time)
                )
            )
            
        return list(scanner.plan_scan())

    async def get_metric_history(self, experiment_id: str, metric_name: str) -> List[Dict]:
        """Get metric history for an experiment"""
        table = self.load_table(f"experiments.{experiment_id}_metrics")
        
        snapshot = table.current_snapshot()
        scanner = table.new_scan() \
            .use_snapshot(snapshot.snapshot_id) \
            .filter(
                table.expr.and_(
                    table.expr.ref("experiment_id").eq(experiment_id),
                    table.expr.ref("metric_name").eq(metric_name)
                )
            ) \
            .select(
                "metric_id",
                "experiment_id",
                "variant_id",
                "timestamp",
                "metric_name",
                "metric_value",
                "segment",
                "metadata"
            )
            
        return list(scanner.plan_scan())

    async def get_experiment_snapshot(self, experiment_id: str, timestamp: datetime) -> Dict:
        """Get a snapshot of experiment state at a specific time"""
        events_table = self.load_table(f"experiments.{experiment_id}_events")
        metrics_table = self.load_table(f"experiments.{experiment_id}_metrics")
        
        events_snapshot = events_table.snapshot_for_timestamp(int(timestamp.timestamp() * 1000))
        metrics_snapshot = metrics_table.snapshot_for_timestamp(int(timestamp.timestamp() * 1000))
        
        return {
            "events": list(events_table.new_scan().use_snapshot(events_snapshot.snapshot_id).plan_scan()),
            "metrics": list(metrics_table.new_scan().use_snapshot(metrics_snapshot.snapshot_id).plan_scan())
        }