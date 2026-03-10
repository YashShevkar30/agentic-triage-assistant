"""
Tests for Agentic Triage Assistant modules.
"""

import pytest
from agent.guardrails import Guardrails
from agent.validator import GroundingValidator
from agent.orchestrator import TriageAgent

def test_guardrails_pii_redaction():
    guard = Guardrails()
    
    # SSN
    text1 = "User 123-45-6789 reported an issue."
    assert guard.redact_pii(text1) == "User [REDACTED_PII] reported an issue."
    
    # Email
    text2 = "Contact admin@company.com for access."
    assert guard.redact_pii(text2) == "Contact [REDACTED_PII] for access."

def test_guardrails_sql_validation():
    guard = Guardrails()
    
    assert guard.validate_sql_query("SELECT * FROM metrics") is True
    assert guard.validate_sql_query("DELETE FROM metrics") is False
    assert guard.validate_sql_query("select * from drop_table") is True # Table name with drop is ok
    assert guard.validate_sql_query("drop table metrics") is False

def test_guardrails_rate_limits():
    guard = Guardrails()
    
    tool = "search_logs"
    for _ in range(5):
        assert guard.check_rate_limit(tool, max_calls=5) is True
        
    assert guard.check_rate_limit(tool, max_calls=5) is False

def test_grounding_validator():
    validator = GroundingValidator()
    
    context = ["Found logs indicating 500 error in payment service."]
    
    # Grounded answer
    assert validator.validate("The payment service threw a 500 error.", context)[0] is True
    
    # Ungrounded recommendation
    ans, reason = validator.validate("The payment service threw a 500 error. Restart the database.", context)
    assert ans is False
    assert "restart" in reason.lower()

def test_agent_orchestrator_demo():
    agent = TriageAgent()
    
    # Test checkout latency incident
    res = agent.triage("High latency on checkout endpoint")
    assert "checkout" in res["incident"].lower()
    assert res["is_safe"] is True
    assert "Redis" in res["triage_result"]
    assert len(res["observations"]) == 3
