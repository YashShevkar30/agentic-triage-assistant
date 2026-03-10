"""
Tool for searching the knowledge base (runbooks, architecture docs).
"""

import json
import os
from typing import Dict, Any

import structlog
from agent.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

class SearchTool:
    """Tool to search the engineering knowledge base."""
    
    name = "search_knowledge_base"
    description = "Search engineering runbooks, playbooks, and architecture documents for known issues or procedures."
    
    def __init__(self):
        self.kb_path = settings.kb_path

    def execute(self, query: str) -> str:
        """Search for a query in the KB."""
        if settings.demo_mode:
            logger.info("search_tool_demo", query=query)
            if "checkout" in query.lower() or "latency" in query.lower():
                return json.dumps({
                    "source": "runbooks/checkout_latency.md",
                    "content": "If checkout latency exceeds 1000ms, check the Redis cache cluster health. If Redis is evicting keys, scale up the cache nodes. Known issue: Payment gateway timeout can cascade to checkout."
                })
            elif "payment" in query.lower() or "500" in query.lower():
                return json.dumps({
                    "source": "runbooks/payment_errors.md",
                    "content": "Payment API 500 errors usually indicate an upstream provider issue. Check the provider status page. Fallback to secondary provider via feature flag 'use_secondary_payment'."
                })
            return json.dumps({"result": "No matching runbooks found."})

        # In a real implementation, this would use a vector database (like Project 4)
        # For simplicity in this agent framework, we return mock data based on the query.
        return json.dumps({"error": "Not implemented in MVP mode. Use demo_mode=True."})
