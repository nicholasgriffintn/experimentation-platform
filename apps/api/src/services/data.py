import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

import clickhouse_driver
from sqlalchemy.orm import Session, joinedload

from ..db.base import Experiment as DBExperiment
from ..schema.clickhouse_schema import ClickHouseSchemas
from ..utils.logger import logger


class DataService:
    def __init__(self,
                 metadata_db: Session,
                 host: str,
                 port: int,
                 user: str,
                 password: str,
                 database: str = "experiments",
        ):
        """Initialize ClickHouse data service
        
        Args:
            host: ClickHouse server host
            port: ClickHouse server port
            user: ClickHouse username
            password: ClickHouse password
            database: ClickHouse database name
        """
        self.metadata_db = metadata_db
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

    async def get_experiment_config(self, experiment_id: str) -> Dict:
        """Get experiment configuration from database"""
        experiment = (
            self.metadata_db.query(DBExperiment)
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
    
    async def set_experiment_config(self, experiment_id: str, config: Dict) -> None:
        """Set experiment configuration in database"""
        experiment = (
            self.metadata_db.query(DBExperiment)
            .filter(DBExperiment.id == experiment_id)
            .first()
        )
        if not experiment:
            return
        
        for key, value in config.items():
            setattr(experiment, key, value)
            
        self.metadata_db.commit()

    async def record_event(self, experiment_id: str, event_data: Dict) -> None:
        """Record an experiment event in ClickHouse
        
        Args:
            experiment_id: ID of the experiment
            event_data: Event data to record
        """
        table_name = "events"
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
        table_name = "metrics"
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
        table_name = "assignments"
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
        table_name = "results"
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
        table_name = "events"
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
        table_name = "metrics"
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
        table_name = "assignments"
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
        table_name = "metrics"
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
        assignments_table = "assignments"
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
        
        events_table = "events"
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