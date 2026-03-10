"""
Guardrails and safety validations to prevent the agent from executing
banned commands, leaking PII, or hallucinating data.
"""

import re
import structlog
from typing import List, Dict, Any

logger = structlog.get_logger()

class Guardrails:
    """Safety and security layer for the agent."""
    
    ALLOWED_TOOLS = ["query_metrics_db", "search_knowledge_base", "search_logs"]
    
    PII_PATTERNS = [
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b(?:\d{4}[ -]?){3}\d{4}\b',  # Credit Card
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'  # Email
    ]

    def __init__(self):
        self._tool_usage: Dict[str, int] = {}
        
    def reset_limits(self):
        self._tool_usage.clear()

    def check_tool_allowed(self, tool_name: str) -> bool:
        """Verify the tool is in the allowlist."""
        allowed = tool_name in self.ALLOWED_TOOLS
        if not allowed:
            logger.warning("blocked_unapproved_tool", tool=tool_name)
        return allowed

    def check_rate_limit(self, tool_name: str, max_calls: int = 5) -> bool:
        """Prevent runaway agent loops on a single tool."""
        current = self._tool_usage.get(tool_name, 0)
        if current >= max_calls:
            logger.warning("tool_rate_limit_exceeded", tool=tool_name, limit=max_calls)
            return False
        
        self._tool_usage[tool_name] = current + 1
        return True

    def redact_pii(self, text: str) -> str:
        """Redact sensitive information from text."""
        if not text:
            return text
            
        redacted = text
        for pattern in self.PII_PATTERNS:
            redacted = re.sub(pattern, "[REDACTED_PII]", redacted)
            
        if redacted != text:
            logger.info("pii_redacted_from_payload")
            
        return redacted

    def validate_sql_query(self, query: str) -> bool:
        """Prevent DROP/DELETE/UPDATE commands in SQL."""
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
        query_upper = query.upper()
        
        for kw in dangerous_keywords:
            # Check for keyword surrounded by word boundaries to avoid matching substrings
            if re.search(rf'\b{kw}\b', query_upper):
                logger.warning("blocked_dangerous_sql", keyword=kw, query=query)
                return False
                
        return True
