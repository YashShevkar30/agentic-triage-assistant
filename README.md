# Agentic Triage Assistant

A ReAct-style autonomous agent for investigating production incidents. It uses tools to query live metrics databases, search system logs, and look up engineering runbooks, then synthesizes the evidence into actionable triage reports.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?logo=openai&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite&logoColor=white)
![Guardrails](https://img.shields.io/badge/Safety-Guardrails-green)

---

## Features

- **Tool Routing**: Agent dynamically plans and executes tools (`query_metrics_db`, `search_knowledge_base`, `search_logs`) based on the incident description.
- **Evidence Composition**: Synthesizes structured triage reports detailing **Root Cause**, **Evidence**, and **Recommended Actions**.
- **PII Redaction Engine**: Automatically redacts SSNs, credit cards, and emails from incident descriptions before they are processed by the LLM or embedded in logs.
- **SQL Injection Defense**: Intercepts, logs, and blocks unsafe SQL queries (`DROP`, `DELETE`, `UPDATE`) attempted by the agent against the metrics schema.
- **Runaway Agent Limits**: Implements per-session tool execution rate-limiting to prevent infinite ReAct loops.
- **Grounding Validation**: Validates the agent's final answer against the retrieved context to detect and flag hallucinated recommendations (e.g., suggesting a server restart when not present in runbooks).

---

## Quick Start

### Installation

```bash
git clone https://github.com/YashShevkar30/agentic-triage-assistant.git
cd agentic-triage-assistant
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Try the CLI (Demo Mode)

Run the interactive triage shell. Demo mode uses hardcoded simulation logic, so no API keys or live databases are needed.

```bash
python -m agent.main triage --demo
```

Try entering incidents like:
- `"High latency on checkout endpoint"`
- `"Payment API returning 500 errors"`

### Run Tests

```bash
pytest tests/ -v
```

---

## Architecture Overview

**1. Orchestrator (`TriageAgent`)**: Manages the core ReAct loop (Thought -> Action -> Observation).
**2. Tools**:
   - `SQLTool`: Executes `.execute("SELECT...")` against metrics.
   - `LogTool`: Searches recent logs for a given service.
   - `SearchTool`: Retrieves text chunks from known runbooks constraints.
**3. Guardrails**: Redacts inputs and sanitizes SQL queries mid-flight.
**4. Validator**: Final heuristic check of generated recommendations before returning to the user.
