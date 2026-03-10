"""
Orchestrates the ReAct-style agent loop.
"""

import json
from typing import Dict, Any, List

import structlog

from agent.config import get_settings
from agent.tools.sql_tool import SQLTool
from agent.tools.search_tool import SearchTool
from agent.tools.log_tool import LogTool
from agent.guardrails import Guardrails
from agent.validator import GroundingValidator

logger = structlog.get_logger()
settings = get_settings()


class TriageAgent:
    """Main Orchestrator for the Agentic Triage Assistant."""
    
    def __init__(self):
        self.tools = {
            "query_metrics_db": SQLTool(),
            "search_knowledge_base": SearchTool(),
            "search_logs": LogTool()
        }
        self.guardrails = Guardrails()
        self.validator = GroundingValidator()
        self.demo_mode = settings.demo_mode
        self._client = None
        
        if not self.demo_mode:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=settings.openai_api_key)
            except Exception:
                self.demo_mode = True

    def triage(self, incident_description: str) -> Dict[str, Any]:
        """
        Main entrypoint to triage an incident.
        Takes a user description, routes to tools, collects evidence, and composes an answer.
        """
        # Redact initial input
        safe_input = self.guardrails.redact_pii(incident_description)
        logger.info("triage_started", input=safe_input[:50])
        
        self.guardrails.reset_limits()
        
        # 1. Planner: Decide which tools to run based on the input
        tool_plan = self._plan_tools(safe_input)
        
        # 2. Execution Loop
        observations = []
        for step in tool_plan:
            tool_name = step["tool"]
            args = step["args"]
            
            # Guardrails check
            if not self.guardrails.check_tool_allowed(tool_name):
                continue
            if not self.guardrails.check_rate_limit(tool_name, settings.max_tool_calls_per_session):
                break
                
            # Extra guardrails for specific tools
            if tool_name == "query_metrics_db" and not self.guardrails.validate_sql_query(args.get("query", "")):
                observations.append(f"Observation ({tool_name}): Blocked dangerous SQL query.")
                continue
                
            # Execute
            try:
                tool = self.tools[tool_name]
                if tool_name == "query_metrics_db":
                    raw_obs = tool.execute(args.get("query", ""))
                elif tool_name == "search_knowledge_base":
                    raw_obs = tool.execute(args.get("query", ""))
                elif tool_name == "search_logs":
                    raw_obs = tool.execute(
                        service=args.get("service", ""),
                        error_level=args.get("error_level", "ERROR")
                    )
                else:
                    raw_obs = f"Error: unknown tool {tool_name}"
                    
                # Redact PII from output
                safe_obs = self.guardrails.redact_pii(raw_obs)
                observations.append(f"Observation ({tool_name}): {safe_obs}")
                logger.debug("tool_executed", tool=tool_name, success=True)
                
            except Exception as e:
                observations.append(f"Observation ({tool_name}): Error executing tool - {str(e)}")
                logger.error("tool_execution_failed", tool=tool_name, error=str(e))
                
        # 3. Composition
        final_answer = self._compose_answer(safe_input, observations)
        
        # 4. Validation (Grounding Check)
        is_grounded, failure_reason = self.validator.validate(final_answer, observations)
        
        if not is_grounded:
            final_answer += f"\n\n[WARNING: Guardrails detected an unverified recommendation: {failure_reason}]"
            
        return {
            "incident": safe_input,
            "observations": observations,
            "triage_result": final_answer,
            "is_safe": is_grounded
        }

    def _plan_tools(self, incident_description: str) -> List[Dict[str, Any]]:
        """Determine which tools to call (Planner)."""
        if self.demo_mode:
            # Hardcoded logic for demo purposes
            desc = incident_description.lower()
            plan = []
            
            if "latency" in desc or "slow" in desc:
                plan.append({"tool": "search_knowledge_base", "args": {"query": incident_description}})
                plan.append({"tool": "query_metrics_db", "args": {"query": "SELECT service_name, avg_latency_ms FROM service_metrics WHERE endpoint='checkout';"}})
                plan.append({"tool": "search_logs", "args": {"service": "checkout", "error_level": "WARN"}})
            elif "500" in desc or "payment" in desc:
                plan.append({"tool": "search_logs", "args": {"service": "payment", "error_level": "ERROR"}})
                plan.append({"tool": "search_knowledge_base", "args": {"query": incident_description}})
            else:
                plan.append({"tool": "search_knowledge_base", "args": {"query": incident_description}})
                
            return plan
            
        # Real LLM implementation would use function calling here
        return []

    def _compose_answer(self, input_desc: str, observations: List[str]) -> str:
        """Combine observations into a final answer (Composer)."""
        if self.demo_mode:
            # Mock composer based on observations
            obs_text = " ".join(observations).lower()
            
            answer = "## Triage Summary\n"
            
            if "checkout" in input_desc.lower() and "redis" in obs_text:
                answer += "**Root Cause**: High latency on checkout due to Redis connection exhaustion.\n\n"
                answer += "**Evidence**:\n"
                answer += "- Logs show 'Redis connection timeout, falling back to DB'\n"
                answer += "- DB connection pool subsequently exhausted\n\n"
                answer += "**Recommended Action**:\n"
                answer += "1. Scale up Redis cache nodes.\n"
                answer += "2. Investigate potential payment gateway slow down as per runbook."
            elif "payment" in input_desc.lower() and "503" in obs_text:
                answer += "**Root Cause**: Upstream payment provider Stripe is returning 503 Service Unavailable.\n\n"
                answer += "**Evidence**:\n"
                answer += "- Logs show 'Upstream Stripe API returned 503 Service Unavailable'\n"
                answer += "- Runbook indicates this is likely an upstream provider issue.\n\n"
                answer += "**Recommended Action**:\n"
                answer += "1. Check provider status page.\n"
                answer += "2. Enable standard fallback mechanism by flipping feature flag `use_secondary_payment`."
            else:
                answer += "**Analysis**: Insufficient evidence to determine root cause.\n\n"
                answer += "**Recommended Action**: Manually investigate using standard dashboarding tools."
                
            return answer
            
        return "Not implemented."
