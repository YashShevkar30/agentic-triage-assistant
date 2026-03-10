"""
Tool for checking recent log entries.
"""

import json
from typing import Dict, Any

import structlog
from agent.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

class LogTool:
    """Tool to search recent service logs."""
    
    name = "search_logs"
    description = "Search recent application logs by service name, error level, or keyword."
    
    def execute(self, service: str, error_level: str = "ERROR", limit: int = 10) -> str:
        """Search logs based on criteria."""
        if settings.demo_mode:
            logger.info("log_tool_demo", service=service, error_level=error_level)
            if service.lower() == "checkout":
                return json.dumps([
                    {"timestamp": "2023-10-27T10:05:00Z", "level": "WARN", "msg": "Redis connection timeout, falling back to DB"},
                    {"timestamp": "2023-10-27T10:05:05Z", "level": "ERROR", "msg": "DB connection pool exhausted"}
                ])
            elif service.lower() == "payment":
                return json.dumps([
                    {"timestamp": "2023-10-27T10:10:00Z", "level": "ERROR", "msg": "Upstream Stripe API returned 503 Service Unavailable"},
                    {"timestamp": "2023-10-27T10:10:01Z", "level": "ERROR", "msg": "Payment failed for order ***, reason: provider_down"}
                ])
            return json.dumps([])

        return json.dumps({"error": "Not implemented. Use demo_mode=True."})
