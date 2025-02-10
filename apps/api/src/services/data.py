import uuid
from datetime import datetime
from typing import Dict, List, Optional

from pyiceberg.catalog import Catalog
from pyiceberg.expressions import (
    And,
    EqualTo,
    GreaterThanOrEqual,
    LessThanOrEqual,
    Reference,
)
from pyiceberg.partitioning import PartitionField, PartitionSpec
from pyiceberg.schema import Schema
from pyiceberg.table import Table
from pyiceberg.transforms import DayTransform, IdentityTransform, MonthTransform

from ..schema.iceberg_schema import IcebergSchemas
from ..utils.logger import logger


class IcebergDataService:
    def __init__(self, catalog: Catalog):
        self.catalog = catalog
        self.schemas = IcebergSchemas()

    async def initialize_experiment_tables(self, experiment_id: str) -> bool:
        """Initialize all required tables for a new experiment
        
        Returns:
            bool: True if all tables were created successfully or already exist, False otherwise
        """
        namespace = "experiments"
        tables_to_create = []

        events_spec = PartitionSpec(
            PartitionField(
                source_id=2, field_id=1000, transform=IdentityTransform(), name="experiment_id"
            ),
            PartitionField(source_id=3, field_id=1001, transform=DayTransform(), name="timestamp"),
        )
        tables_to_create.append((
            f"{namespace}.{experiment_id}_events",
            self.schemas.get_events_schema(),
            events_spec
        ))

        metrics_spec = PartitionSpec(
            PartitionField(
                source_id=2, field_id=1000, transform=IdentityTransform(), name="experiment_id"
            ),
            PartitionField(
                source_id=4, field_id=1001, transform=MonthTransform(), name="timestamp"
            ),
        )
        tables_to_create.append((
            f"{namespace}.{experiment_id}_metrics",
            self.schemas.get_metrics_schema(),
            metrics_spec
        ))

        assignments_spec = PartitionSpec(
            PartitionField(
                source_id=2, field_id=1000, transform=IdentityTransform(), name="experiment_id"
            )
        )
        tables_to_create.append((
            f"{namespace}.{experiment_id}_assignments",
            self.schemas.get_assignments_schema(),
            assignments_spec
        ))

        results_spec = PartitionSpec(
            PartitionField(
                source_id=2, field_id=1000, transform=IdentityTransform(), name="experiment_id"
            ),
            PartitionField(
                source_id=4, field_id=1001, transform=IdentityTransform(), name="metric_name"
            ),
        )
        tables_to_create.append((
            f"{namespace}.{experiment_id}_results",
            self.schemas.get_results_schema(),
            results_spec
        ))

        success = True
        for table_name, schema, partition_spec in tables_to_create:
            if not self.create_table(table_name, schema, partition_spec):
                success = False
                logger.error(f"Failed to create or verify table {table_name}")
                break

        return success

    def create_table(self, table_name: str, schema: Schema, partition_spec: PartitionSpec) -> bool:
        """Create a new Iceberg table"""
        try:
            try:
                self.catalog.load_table(table_name)
                logger.info(f"Table {table_name} already exists")
                return True
            except Exception:
                pass

            namespace, table = table_name.split(".")

            self.catalog.create_table(
                identifier=(namespace, table),
                schema=schema,
                partition_spec=partition_spec,
                properties={
                    "write.format.default": "parquet",
                    "write.parquet.compression-codec": "snappy",
                    "format-version": "2",
                    "write.metadata.compression-codec": "gzip",
                    "write.metadata.metrics.default": "full",
                    "write.metadata.metrics.column.default": "full",
                    "write.object-storage.enabled": "true",
                    "write.delete.mode": "merge-on-read",
                    "write.update.mode": "merge-on-read",
                    "write.merge.mode": "merge-on-read",
                    "write.distribution-mode": "hash",
                    "write.target-file-size-bytes": "536870912",  # 512MB
                    "read.split.target-size": "134217728",  # 128MB
                    "read.split.planning-lookback": "10",
                    "read.split.open-file-cost": "4194304",  # 4MB
                },
            )
            logger.info(f"Successfully created table {table_name}")
            return True
        except Exception as e:
            error_msg = str(e)
            if "Table already exists" in error_msg:
                logger.info(f"Table {table_name} already exists (concurrent creation)")
            elif "Namespace does not exist" in error_msg:
                logger.error(f"Namespace does not exist for table {table_name}")
            else:
                logger.error(f"Failed to create table {table_name}: {error_msg}")
            return False

    async def get_experiment_config(self, experiment_id: str) -> Dict:
        """Get experiment configuration from database"""
        assignments_table = self.load_table(f"experiments.{experiment_id}_assignments")

        snapshot = assignments_table.current_snapshot()
        if not snapshot:
            return {"id": experiment_id, "metrics": {}, "variants": []}

        scanner = assignments_table.scan()
        if snapshot and hasattr(snapshot, "snapshot_id"):
            scanner = scanner.use_ref(str(snapshot.snapshot_id))

        scanner = scanner.filter(EqualTo(Reference("experiment_id"), experiment_id))
        scanner = scanner.select("variant_id", "context")

        assignments = list(scanner.to_arrow())

        variants = list(
            {
                assignment["variant_id"]: {
                    "id": assignment["variant_id"],
                    "context": assignment["context"],
                }
                for assignment in assignments
            }.values()
        )

        metrics_table = self.load_table(f"experiments.{experiment_id}_metrics")
        metrics_snapshot = metrics_table.current_snapshot()

        if metrics_snapshot and hasattr(metrics_snapshot, "snapshot_id"):
            metrics_scanner = metrics_table.scan()
            metrics_scanner = metrics_scanner.use_ref(str(metrics_snapshot.snapshot_id))
            metrics_scanner = metrics_scanner.filter(
                EqualTo(Reference("experiment_id"), experiment_id)
            )
            metrics_scanner = metrics_scanner.select("metric_name", "metadata")

            metrics = list(metrics_scanner.to_arrow())
            metrics_config = {metric["metric_name"]: metric["metadata"] for metric in metrics}
        else:
            metrics_config = {}

        return {"id": experiment_id, "metrics": metrics_config, "variants": variants}

    async def record_event(self, experiment_id: str, event_data: Dict) -> None:
        """Record an event for the experiment"""
        table = self.load_table(f"experiments.{experiment_id}_events")

        data = {
            "event_id": str(uuid.uuid4()),
            "experiment_id": experiment_id,
            "timestamp": datetime.utcnow(),
            "user_id": event_data.get("user_id"),
            "variant_id": event_data.get("variant_id"),
            "event_type": event_data.get("event_type"),
            "event_value": event_data.get("value"),
            "client_id": event_data.get("client_id"),
            "metadata": event_data.get("metadata", {}),
        }
        table.append([data])

    async def record_metric(self, experiment_id: str, metric_data: Dict) -> None:
        """Record a metric measurement"""
        table = self.load_table(f"experiments.{experiment_id}_metrics")

        data = {
            "metric_id": str(uuid.uuid4()),
            "experiment_id": experiment_id,
            "variant_id": metric_data.get("variant_id"),
            "timestamp": datetime.utcnow(),
            "metric_name": metric_data.get("metric_name"),
            "metric_value": metric_data.get("metric_value"),
            "segment": metric_data.get("segment"),
            "metadata": metric_data.get("metadata", {}),
        }
        table.append([data])

    async def assign_variant(
        self, experiment_id: str, user_id: str, variant_id: str, context: Optional[Dict] = None
    ) -> None:
        """Record a user-variant assignment"""
        table = self.load_table(f"experiments.{experiment_id}_assignments")

        data = {
            "assignment_id": str(uuid.uuid4()),
            "experiment_id": experiment_id,
            "user_id": user_id,
            "variant_id": variant_id,
            "timestamp": datetime.utcnow(),
            "context": context or {},
        }
        table.append([data])

    async def record_results(self, experiment_id: str, results_data: Dict) -> None:
        """Record analysis results"""
        table = self.load_table(f"experiments.{experiment_id}_results")

        metrics_results = results_data.get("metrics", {})
        timestamp = datetime.utcnow()
        rows = []

        for metric_name, metric_results in metrics_results.items():
            for variant_id, result in metric_results.items():
                rows.append(
                    {
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
                            "correction_method": results_data.get("correction_method"),
                        },
                    }
                )

        table.append(rows)

    def load_table(self, table_name: str) -> Table:
        """Load an Iceberg table"""
        return self.catalog.load_table(table_name)

    async def query_events(
        self, experiment_id: str, start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """Query events within a time range"""
        table = self.load_table(f"experiments.{experiment_id}_events")

        scanner = table.scan()
        scanner = scanner.filter(
            And(
                EqualTo(Reference("experiment_id"), experiment_id),
                And(
                    GreaterThanOrEqual(Reference("timestamp"), start_time.timestamp()),
                    LessThanOrEqual(Reference("timestamp"), end_time.timestamp()),
                ),
            )
        )

        return list(scanner.to_arrow())

    async def get_metric_history(self, experiment_id: str, metric_name: str) -> List[Dict]:
        """Get historical metric data"""
        table = self.load_table(f"experiments.{experiment_id}_metrics")

        scanner = table.scan()
        scanner = scanner.filter(
            And(
                EqualTo(Reference("experiment_id"), experiment_id),
                EqualTo(Reference("metric_name"), metric_name),
            )
        )

        return list(scanner.to_arrow())

    async def get_exposure_data(self, experiment_id: str) -> List[Dict]:
        """Get exposure data for an experiment"""
        table = self.load_table(f"experiments.{experiment_id}_events")

        scanner = table.scan()
        scanner = scanner.filter(
            And(
                EqualTo(Reference("experiment_id"), experiment_id),
                EqualTo(Reference("event_type"), "exposure"),
            )
        )

        return list(scanner.to_arrow())

    async def get_metric_data(self, experiment_id: str, metric_name: str) -> Dict[str, List[float]]:
        """Get metric data grouped by variant"""
        table = self.load_table(f"experiments.{experiment_id}_metrics")

        scanner = table.scan()
        scanner = scanner.filter(
            And(
                EqualTo(Reference("experiment_id"), experiment_id),
                EqualTo(Reference("metric_name"), metric_name),
            )
        )

        data = list(scanner.to_arrow())
        grouped_data: Dict[str, List[float]] = {}

        for row in data:
            variant_id = row["variant_id"]
            if variant_id not in grouped_data:
                grouped_data[variant_id] = []
            grouped_data[variant_id].append(row["metric_value"])

        return grouped_data

    async def get_experiment_snapshot(self, experiment_id: str, timestamp: datetime) -> Dict:
        """Get experiment state at a specific point in time"""
        events_table = self.load_table(f"experiments.{experiment_id}_events")
        metrics_table = self.load_table(f"experiments.{experiment_id}_metrics")

        events_scanner = events_table.scan()
        events_scanner = events_scanner.filter(
            And(
                EqualTo(Reference("experiment_id"), experiment_id),
                LessThanOrEqual(Reference("timestamp"), timestamp.timestamp()),
            )
        )

        metrics_scanner = metrics_table.scan()
        metrics_scanner = metrics_scanner.filter(
            And(
                EqualTo(Reference("experiment_id"), experiment_id),
                LessThanOrEqual(Reference("timestamp"), timestamp.timestamp()),
            )
        )

        events = list(events_scanner.to_arrow())
        metrics = list(metrics_scanner.to_arrow())

        return {
            "events": events,
            "metrics": metrics,
        }
