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
            if params:
                result = self.client.execute(query, params, with_column_types=True)
            else:
                result = self.client.execute(query, with_column_types=True)
                
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
            .options(joinedload(DBExperiment.metrics))
            .first()
        )
        if not experiment:
            return {}
        
        metrics = []
        for metric in experiment.metrics:
            metrics.append({
                "metric_name": metric.metric_name,
                "name": metric.metric_name,
                "type": getattr(metric, "type", "continuous")
            })
        
        return {
            "id": experiment.id,
            "name": experiment.name,
            "type": experiment.type.value if hasattr(experiment.type, "value") else experiment.type,
            "status": experiment.status.value if hasattr(experiment.status, "value") else experiment.status,
            "start_time": experiment.start_time,
            "end_time": experiment.end_time,
            "variants": [
                {
                    "id": variant.id,
                    "name": variant.name,
                    "type": variant.type.value if hasattr(variant.type, "value") else variant.type,
                    "config": variant.config,
                    "traffic_percentage": variant.traffic_percentage,
                }
                for variant in experiment.variants
            ],
            "metrics": metrics,
            "analysis_config": getattr(experiment, "analysis_config", {}),
            "targeting_rules": getattr(experiment, "targeting_rules", {}),
            "traffic_allocation": getattr(experiment, "traffic_allocation", 100.0),
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
        values = ", ".join([f"'{v}'" if isinstance(v, (str, datetime)) else str(v) for v in event_data.values()])
        
        query = f"INSERT INTO {self.database}.{table_name} ({columns}) VALUES ({values})"
        self._execute_query(query)

    async def record_metric(self, experiment_id: str, metric_data: Dict) -> None:
        """Record a metric measurement for an experiment
        
        Args:
            experiment_id: ID of the experiment
            metric_data: Metric data to record
        """
        table_name = "metrics"
        metric_data["experiment_id"] = experiment_id
        metric_data["timestamp"] = metric_data.get("timestamp", datetime.utcnow())
        
        columns = ", ".join(metric_data.keys())
        values = ", ".join([f"'{v}'" if isinstance(v, (str, datetime)) else str(v) for v in metric_data.values()])
        
        query = f"INSERT INTO {self.database}.{table_name} ({columns}) VALUES ({values})"
        self._execute_query(query)

    async def assign_variant(self, experiment_id: str, user_id: str, variant_id: str, context: Dict) -> None:
        """Record a variant assignment for a user
        
        Args:
            experiment_id: ID of the experiment
            user_id: ID of the user
            variant_id: ID of the assigned variant
            context: User context data
        """
        table_name = "assignments"
        record = {
            "experiment_id": experiment_id,
            "user_id": user_id,
            "variant_id": variant_id,
            "timestamp": datetime.utcnow(),
            "context": str(context),
        }
        
        columns = ", ".join(record.keys())
        values = ", ".join([f"'{v}'" if isinstance(v, (str, datetime)) else str(v) for v in record.values()])
        
        query = f"INSERT INTO {self.database}.{table_name} ({columns}) VALUES ({values})"
        self._execute_query(query)

    async def record_results(self, experiment_id: str, results_data: Dict) -> None:
        """Record analysis results for an experiment
        
        Args:
            experiment_id: ID of the experiment
            results_data: Results data to record
        """
        logger.info(f"Recording results for experiment {experiment_id}")
        table_name = "results"
        timestamp = datetime.utcnow()
        
        for metric_name, variants_results in results_data.get("metrics", {}).items():
            for variant_id, result in variants_results.items():
                record = {
                    "experiment_id": experiment_id,
                    "metric_name": metric_name,
                    "variant_id": variant_id,
                    "timestamp": timestamp,
                    "sample_size": result.get("sample_size", 0),
                    "mean": result.get("mean", 0),
                    "p_value": result.get("p_value", 1),
                    "is_significant": result.get("is_significant", False),
                }
                
                columns = ", ".join(record.keys())
                values = ", ".join([f"'{v}'" if isinstance(v, (str, datetime)) else str(v) for v in record.values()])
                
                query = f"INSERT INTO {self.database}.{table_name} ({columns}) VALUES ({values})"
                self._execute_query(query)

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
        WHERE experiment_id = '{experiment_id}'
          AND timestamp >= '{start_time}'
          AND timestamp <= '{end_time}'
        ORDER BY timestamp
        """
        
        return self._execute_query(query)

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
        WHERE experiment_id = '{experiment_id}'
          AND metric_name = '{metric_name}'
        ORDER BY timestamp
        """
        
        return self._execute_query(query)

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
        WHERE experiment_id = '{experiment_id}'
        GROUP BY variant_id
        """
        
        return self._execute_query(query)

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
        WHERE experiment_id = '{experiment_id}'
          AND metric_name = '{metric_name}'
        """
        
        results = self._execute_query(query)
        
        grouped_data = {}
        for row in results:
            variant_id = row.get("variant_id")
            metric_value = row.get("metric_value")
            
            if not variant_id or metric_value is None:
                continue
                
            if variant_id not in grouped_data:
                grouped_data[variant_id] = []
                
            grouped_data[variant_id].append(float(metric_value))
            
        return grouped_data

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
        WHERE experiment_id = '{experiment_id}'
          AND timestamp <= '{timestamp}'
        GROUP BY variant_id
        """
        
        assignments = self._execute_query(assignments_query)
        
        events_table = "events"
        events_query = f"""
        SELECT variant_id, event_type, count() as count
        FROM {self.database}.{events_table}
        WHERE experiment_id = '{experiment_id}'
          AND timestamp <= '{timestamp}'
        GROUP BY variant_id, event_type
        """
        
        events = self._execute_query(events_query)
        
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