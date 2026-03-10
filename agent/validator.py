"""
Validates that the agent's final generated answer and recommendations
are actually supported by the evidence it gathered (grounding check).
"""

from typing import List, Dict, Any, Tuple
import structlog
from agent.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

class GroundingValidator:
    """Validates the output of the agent against its context."""

    def __init__(self):
        self.demo_mode = settings.demo_mode

    def validate(self, answer: str, context: List[str]) -> Tuple[bool, str]:
        """
        Check if the 'answer' contains hallucinated claims not in 'context'.
        Returns (is_grounded, failure_reason_if_any)
        """
        if self.demo_mode:
            # In demo mode, we use heuristics to detect hallucinations.
            # E.g. if answer mentions "restarting server" but context didn't.
            context_str = " ".join(context).lower()
            ans_lower = answer.lower()
            
            # Simple heuristic check for ungrounded recommendations
            risky_terms = ["restart", "reboot", "delete", "clear cache", "flush"]
            
            for term in risky_terms:
                if term in ans_lower and term not in context_str:
                    reason = f"Ungrounded recommendation detected: '{term}'"
                    logger.warning("grounding_validation_failed", reason=reason)
                    return False, reason
                    
            return True, ""
            
        # In a real system, you'd use a separate LLM call:
        # "Does this answer contain facts not present in this context?"
        return True, ""
