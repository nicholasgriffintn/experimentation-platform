import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
import json
from pydantic import BaseModel

class LogConfig(BaseModel):
    """Logging configuration"""
    
    LOGGER_NAME: str = "experimentation"
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(message)s"
    LOG_LEVEL: str = "DEBUG"

    version: int = 1
    disable_existing_loggers: bool = False
    formatters: Dict[str, Dict[str, str]] = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "()": "src.utils.logger.JSONFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers: Dict[str, Dict[str, Any]] = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "file": {
            "formatter": "json",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"logs/experimentation_{datetime.now().strftime('%Y%m%d')}.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8",
        },
    }
    loggers: Dict[str, Dict[str, Any]] = {
        LOGGER_NAME: {
            "handlers": ["default", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    }

class JSONFormatter(logging.Formatter):
    """JSON log formatter"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        
        if hasattr(record, "experiment_id"):
            log_data["experiment_id"] = record.experiment_id
            
        if hasattr(record, "metric_name"):
            log_data["metric_name"] = record.metric_name
            
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

Path("logs").mkdir(exist_ok=True)

logger = logging.getLogger("experimentation")