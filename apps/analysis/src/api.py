from fastapi import FastAPI, HTTPException
from pyspark.sql import SparkSession
from typing import Dict, Optional
import pandas as pd
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="AB Testing Statistical Service")

# Initialize Spark session with connection to existing Spark master
spark = SparkSession.builder \
    .appName("AB Testing Analysis") \
    .config("spark.master", "spark://iceberg_spark:7077") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.experiments", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.experiments.type", "hadoop") \
    .config("spark.sql.catalog.experiments.warehouse", "/home/iceberg/warehouse") \
    .getOrCreate()

class ExperimentResult(BaseModel):
    experiment_id: str
    variant: str
    user_id: str
    value: float
    metadata: Optional[Dict[str, str]] = None

@app.post("/record-observation")
async def record_observation(result: ExperimentResult):
    """Record a single experiment observation."""
    try:
        # Convert to Spark DataFrame
        pdf = pd.DataFrame([{
            "experiment_id": result.experiment_id,
            "variant": result.variant,
            "user_id": result.user_id,
            "timestamp": datetime.now(),
            "value": result.value,
            "metadata": result.metadata or {}
        }])
        df = spark.createDataFrame(pdf)
        
        # Write to Iceberg table
        df.writeTo("experiments.results").append()
        
        return {"status": "success", "message": "Observation recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/experiment-summary/{experiment_id}")
async def get_experiment_summary(experiment_id: str):
    """Get summary statistics for an experiment."""
    try:
        # Query our pre-created view
        summary = spark.sql(f"""
            SELECT * FROM experiments.results_summary 
            WHERE experiment_id = '{experiment_id}'
        """).toPandas()
        
        return summary.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-experiment/{experiment_id}")
async def analyze_experiment(
    experiment_id: str,
    test_type: str = "frequentist",
    metric: str = "value"
):
    """Run statistical analysis on experiment data."""
    try:
        # Get experiment data
        df = spark.sql(f"""
            SELECT * FROM experiments.results 
            WHERE experiment_id = '{experiment_id}'
        """)
        
        if test_type == "frequentist":
            # Perform t-test using Spark
            stats = df.groupBy("variant").agg({
                metric: "avg",
                metric: "stddev",
                "user_id": "count"
            }).toPandas()
            
            # TODO: Implement actual statistical test
            # For now, return summary stats
            return stats.to_dict(orient="records")
            
        elif test_type == "bayesian":
            # TODO: Implement Bayesian analysis
            return {"status": "error", "message": "Bayesian analysis not yet implemented"}
            
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unknown test type: {test_type}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Try a simple Spark operation
        spark.sql("SELECT 1").collect()
        return {"status": "healthy", "spark": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)} 