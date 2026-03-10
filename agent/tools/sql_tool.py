"""
Tool for executing SQL queries against a SQLite metrics database.
"""

import sqlite3
import json
from typing import Dict, Any

import structlog
from agent.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

class SQLTool:
    """Tool to query the metrics database."""
    
    name = "query_metrics_db"
    description = "Execute a SQL query against the metrics database to check throughput, latency, or error rates."
    
    def __init__(self):
        self.db_path = settings.db_path
        
    def get_schema(self) -> str:
        return """
        Table: service_metrics
        Columns:
        - timestamp (datetime)
        - service_name (varchar)
        - endpoint (varchar)
        - latency_ms (integer)
        - status_code (integer)
        """

    def execute(self, query: str) -> str:
        """Execute a full SQL query."""
        if settings.demo_mode:
            logger.info("sql_tool_demo", query=query)
            if "latency" in query.lower() and "checkout" in query.lower():
                return json.dumps([{"service_name": "checkout", "avg_latency_ms": 1450, "status_code": 200}])
            elif "500" in query.lower():
                return json.dumps([{"service_name": "payment", "error_count": 45, "status_code": 500}])
            return json.dumps([{"result": "No data found"}])

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                return json.dumps([dict(row) for row in rows])
        except Exception as e:
            logger.error("sql_execution_failed", error=str(e), query=query)
            return json.dumps({"error": str(e)})
