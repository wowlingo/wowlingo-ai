import os
import yaml
from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseModel):
    host: str = "localhost"
    port: int = 5432
    database: str = "onsori_analysis"
    username: str = "postgres"
    password: str = ""

    class Config:
        extra = "ignore"


class OllamaSettings(BaseModel):
    base_url: str = "http://localhost:11434"
    model: str = "gemma"
    timeout: int = 30


class BatchSettings(BaseModel):
    schedule: dict = {"hour": 0, "minute": 0}
    timezone: str = "UTC"


class LoggingSettings(BaseModel):
    level: str = "INFO"
    file: str = "logs/app.log"
    max_file_size: str = "10MB"
    backup_count: int = 5
    rotation: str = "daily"


class APISettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False


class PathSettings(BaseModel):
    static: str = "static"
    templates: str = "templates"


class PromptSettings(BaseModel):
    """AI 프롬프트 설정"""
    daily_learning_feedback: dict = {}
    learning_progress_analysis: dict = {}
    personalized_recommendations: dict = {}


class Settings(BaseSettings):
    database: DatabaseSettings = DatabaseSettings()
    ollama: OllamaSettings = OllamaSettings()
    batch: BatchSettings = BatchSettings()
    logging: LoggingSettings = LoggingSettings()
    api: APISettings = APISettings()
    paths: PathSettings = PathSettings()
    prompts: PromptSettings = PromptSettings()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


def load_settings() -> Settings:
    config_path = Path("config/config.yaml")
    prompts_path = Path("config/prompts.yaml")
    settings_dict = {}

    # Load main config
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
            if config_data:
                settings_dict.update(config_data)

    # Load prompts config
    if prompts_path.exists():
        with open(prompts_path, 'r', encoding='utf-8') as f:
            prompts_data = yaml.safe_load(f)
            if prompts_data:
                settings_dict['prompts'] = prompts_data

    settings = Settings(**settings_dict)

    # Override with environment variables
    if os.getenv('DATABASE_HOST'):
        settings.database.host = os.getenv('DATABASE_HOST')
    if os.getenv('DATABASE_PORT'):
        settings.database.port = int(os.getenv('DATABASE_PORT'))
    if os.getenv('DATABASE_NAME'):
        settings.database.database = os.getenv('DATABASE_NAME')
    if os.getenv('DATABASE_USERNAME'):
        settings.database.username = os.getenv('DATABASE_USERNAME')
    if os.getenv('DATABASE_PASSWORD'):
        settings.database.password = os.getenv('DATABASE_PASSWORD')
    if os.getenv('OLLAMA_BASE_URL'):
        settings.ollama.base_url = os.getenv('OLLAMA_BASE_URL')

    return settings


# Global settings instance
settings = load_settings()