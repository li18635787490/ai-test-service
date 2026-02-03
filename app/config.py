from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # AI Provider
    default_ai_provider: str = "openai"

    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-turbo-preview"
    openai_base_url: str = "https://api.openai.com/v1"

    # Anthropic
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-opus-20240229"

    # 通义千问
    qwen_api_key: Optional[str] = None
    qwen_model: str = "qwen-max"

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True

    # Storage
    upload_dir: str = "./uploads"
    report_dir: str = "./reports"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
