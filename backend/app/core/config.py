from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://klosado:klosado@localhost:5432/klosado"
    redis_url: str = "redis://localhost:6379/0"

    hcnsec_model_volume: str = "DeepSeek-V4.1-Flash"
    hcnsec_model_smart: str = "DeepSeek-V4-Pro"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"

    default_monthly_token_budget: int = 2_000_000

    class Config:
        env_file = ".env"


settings = Settings()
