"""Configuration for Agentic Triage Assistant."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    openai_api_key: str = "sk-demo"
    openai_model: str = "gpt-4o-mini"
    demo_mode: bool = True
    log_level: str = "INFO"
    
    max_tool_calls_per_session: int = 5
    
    db_path: str = "data/metrics.db"
    kb_path: str = "data/knowledge_base"
    logs_path: str = "data/sample_logs"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
