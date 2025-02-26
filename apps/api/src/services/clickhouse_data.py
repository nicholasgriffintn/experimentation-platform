import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

import clickhouse_driver
from sqlalchemy.orm import Session, joinedload

from ..db.base import Experiment as DBExperiment
from ..schema.clickhouse_schema import ClickHouseSchemas
from ..utils.logger import logger


class ClickHouseDataService:
    def __init__(self, host: str, port: int, user: str, password: str, database: str = "experiments"):
        """Initialize ClickHouse data service
        
        Args:
            host: ClickHouse server host
            port: ClickHouse server port
            user: ClickHouse username
            password: ClickHouse password
            database: ClickHouse database name
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.schemas = ClickHouseSchemas()
        self.client = clickhouse_driver.Client(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            settings={'use_numpy': True}
        )
        
    def _execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """Execute a query against ClickHouse
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            List of dictionaries with query results
        """
        try:
            result = self.client.execute(query, params or {}, with_column_types=True)
            rows, columns = result
            column_names = [col[0] for col in columns]
            return [dict(zip(column_names, row)) for row in rows]
        except Exception as e:
            logger.error(f"Error executing ClickHouse query: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise

    async def initialize_experiment_tables(self, experiment_id: str) -> bool:
        """Initialize all required tables for a new experiment

        Returns:
            bool: True if all tables were created successfully or already exist, False otherwise
        """
        tables_to_create = [
            (f"{experiment_id}_events", self.schemas.get_events_schema()),
            (f"{experiment_id}_metrics", self.schemas.get_metrics_schema()),
            (f"{experiment_id}_assignments", self.schemas.get_assignments_schema()),
            (f"{experiment_id}_results", self.schemas.get_results_schema()),
        ]

        success = True
        for table_name, schema_template in tables_to_create:
            if not self.create_table(table_name, schema_template):
                success = False
                logger.error(f"Failed to create or verify table {table_name}")
                break

        return success

    def create_table(self, table_name: str, schema_template: str) -> bool:
        """Create a new ClickHouse table
        
        Args:
            table_name: Name of the table to create
            schema_template: SQL schema template for the table
            
        Returns:
            bool: True if table was created successfully or already exists, False otherwise
        """
        try:
            check_query = f"SHOW TABLES LIKE '{table_name}'"
            result = self._execute_query(check_query)
            
            if result:
                logger.info(f"Table {table_name} already exists")
                return True

            create_query = schema_template.format(database=self.database, table_name=table_name)
            self._execute_query(create_query)
            logger.info(f"Successfully created table {table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {str(e)}")
            return False

    async def get_experiment_config(self, experiment_id: str, db: Session) -> Dict:
        """Get experiment configuration from database"""
        experiment = (
            db.query(DBExperiment)
            .filter(DBExperiment.id == experiment_id)
            .options(joinedload(DBExperiment.variants))
            .first()
        )
        if not experiment:
            return {}
        
        return {
            "id": experiment.id,
            "name": experiment.name,
            "type": experiment.type.value,
            "status": experiment.status.value,
            "variants": [
                {
                    "id": variant.id,
                    "name": variant.name,
                    "type": variant.type,
                    "traffic_percentage": variant.traffic_percentage,
                }
                for variant in experiment.variants
            ],
        }

    async def record_event(self, experiment_id: str, event_data: Dict) -> None:
        """Record an experiment event in ClickHouse
        
        Args:
            experiment_id: ID of the experiment
            event_data: Event data to record
        """
        table_name = f"{experiment_id}_events"
        event_data["event_id"] = event_data.get("event_id", str(uuid.uuid4()))
        event_data["experiment_id"] = experiment_id
        event_data["timestamp"] = event_data.get("timestamp", datetime.utcnow())
        
        columns = ", ".join(event_data.keys())
        placeholders = ", ".join([f":{key}" for key in event_data.keys()])
        
        query = f"INSERT INTO {self.database}.{table_name} ({columns}) VALUES ({placeholders})"
        self._execute_query(query, event_data)

    async def record_metric(self, experiment_id: str, metric_data: Dict) -> None:
        """Record a metric value in ClickHouse
        
        Args:
            experiment_id: ID of the experiment
            metric_data: Metric data to record
        """
        table_name = f"{experiment_id}_metrics"
        metric_data["metric_id"] = metric_data.get("metric_id", str(uuid.uuid4()))
        metric_data["experiment_id"] = experiment_id
        metric_data["timestamp"] = metric_data.get("timestamp", datetime.utcnow())
        
        columns = ", ".join(metric_data.keys())
        placeholders = ", ".join([f":{key}" for key in metric_data.keys()])
        
        query = f"INSERT INTO {self.database}.{table_name} ({columns}) VALUES ({placeholders})"
        self._execute_query(query, metric_data)

    async def assign_variant(
        self, experiment_id: str, user_id: str, variant_id: str, context: Optional[Dict] = None
    ) -> None:
        """Record a user-variant assignment in ClickHouse
        
        Args:
            experiment_id: ID of the experiment
            user_id: ID of the user
            variant_id: ID of the variant
            context: Additional context data
        """
        table_name = f"{experiment_id}_assignments"
        assignment_data = {
            "assignment_id": str(uuid.uuid4()),
            "experiment_id": experiment_id,
            "user_id": user_id,
            "variant_id": variant_id,
            "timestamp": datetime.utcnow(),
            "context": context or {},
        }
        
        columns = ", ".join(assignment_data.keys())
        placeholders = ", ".join([f":{key}" for key in assignment_data.keys()])
        
        query = f"INSERT INTO {self.database}.{table_name} ({columns}) VALUES ({placeholders})"
        self._execute_query(query, assignment_data)

    async def record_results(self, experiment_id: str, results_data: Dict) -> None:
        """Record experiment results in ClickHouse
        
        Args:
            experiment_id: ID of the experiment
            results_data: Results data to record
        """
        table_name = f"{experiment_id}_results"
        results_data["result_id"] = results_data.get("result_id", str(uuid.uuid4()))
        results_data["experiment_id"] = experiment_id
        results_data["timestamp"] = results_data.get("timestamp", datetime.utcnow())
        
        columns = ", ".join(results_data.keys())
        placeholders = ", ".join([f":{key}" for key in results_data.keys()])
        
        query = f"INSERT INTO {self.database}.{table_name} ({columns}) VALUES ({placeholders})"
        self._execute_query(query, results_data)

    async def query_events(
        self, experiment_id: str, start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """Query events for an experiment within a time range
        
        Args:
            experiment_id: ID of the experiment
            start_time: Start time for the query
            end_time: End time for the query
            
        Returns:
            List of event dictionaries
        """
        table_name = f"{experiment_id}_events"
        query = f"""
        SELECT *
        FROM {self.database}.{table_name}
        WHERE experiment_id = :experiment_id
          AND timestamp >= :start_time
          AND timestamp <= :end_time
        ORDER BY timestamp
        """
        
        params = {
            "experiment_id": experiment_id,
            "start_time": start_time,
            "end_time": end_time,
        }
        
        return self._execute_query(query, params)

    async def get_metric_history(self, experiment_id: str, metric_name: str) -> List[Dict]:
        """Get historical metric values for an experiment
        
        Args:
            experiment_id: ID of the experiment
            metric_name: Name of the metric
            
        Returns:
            List of metric value dictionaries
        """
        table_name = f"{experiment_id}_metrics"
        query = f"""
        SELECT *
        FROM {self.database}.{table_name}
        WHERE experiment_id = :experiment_id
          AND metric_name = :metric_name
        ORDER BY timestamp
        """
        
        params = {
            "experiment_id": experiment_id,
            "metric_name": metric_name,
        }
        
        return self._execute_query(query, params)

    async def get_exposure_data(self, experiment_id: str) -> List[Dict]:
        """Get exposure data for an experiment
        
        Args:
            experiment_id: ID of the experiment
            
        Returns:
            List of exposure dictionaries
        """
        table_name = f"{experiment_id}_assignments"
        query = f"""
        SELECT variant_id, count() as count
        FROM {self.database}.{table_name}
        WHERE experiment_id = :experiment_id
        GROUP BY variant_id
        """
        
        params = {
            "experiment_id": experiment_id,
        }
        
        return self._execute_query(query, params)

    async def get_metric_data(self, experiment_id: str, metric_name: str) -> Dict[str, List[float]]:
        """Get metric data for an experiment grouped by variant
        
        Args:
            experiment_id: ID of the experiment
            metric_name: Name of the metric
            
        Returns:
            Dictionary mapping variant IDs to lists of metric values
        """
        table_name = f"{experiment_id}_metrics"
        query = f"""
        SELECT variant_id, metric_value
        FROM {self.database}.{table_name}
        WHERE experiment_id = :experiment_id
          AND metric_name = :metric_name
        """
        
        params = {
            "experiment_id": experiment_id,
            "metric_name": metric_name,
        }
        
        results = self._execute_query(query, params)
        
        # Group by variant_id
        data: Dict[str, List[float]] = {}
        for row in results:
            variant_id = row["variant_id"]
            if variant_id not in data:
                data[variant_id] = []
            data[variant_id].append(row["metric_value"])
            
        return data

    async def get_experiment_snapshot(self, experiment_id: str, timestamp: datetime) -> Dict:
        """Get a snapshot of experiment data at a specific time
        
        Args:
            experiment_id: ID of the experiment
            timestamp: Timestamp for the snapshot
            
        Returns:
            Dictionary with experiment snapshot data
        """
        assignments_table = f"{experiment_id}_assignments"
        assignments_query = f"""
        SELECT variant_id, count() as count
        FROM {self.database}.{assignments_table}
        WHERE experiment_id = :experiment_id
          AND timestamp <= :timestamp
        GROUP BY variant_id
        """
        
        assignments_params = {
            "experiment_id": experiment_id,
            "timestamp": timestamp,
        }
        
        assignments = self._execute_query(assignments_query, assignments_params)
        
        events_table = f"{experiment_id}_events"
        events_query = f"""
        SELECT variant_id, event_type, count() as count
        FROM {self.database}.{events_table}
        WHERE experiment_id = :experiment_id
          AND timestamp <= :timestamp
        GROUP BY variant_id, event_type
        """
        
        events_params = {
            "experiment_id": experiment_id,
            "timestamp": timestamp,
        }
        
        events = self._execute_query(events_query, events_params)
        
        result = {
            "assignments": {row["variant_id"]: row["count"] for row in assignments},
            "events": {},
        }
        
        for row in events:
            variant_id = row["variant_id"]
            event_type = row["event_type"]
            if variant_id not in result["events"]:
                result["events"][variant_id] = {}
            result["events"][variant_id][event_type] = row["count"]
            
        return result 