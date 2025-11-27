import os
import re
import yaml
from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


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


class ScheduleJobSettings(BaseModel):
    """개별 스케줄 잡 설정"""
    enabled: bool = True
    hour: int = 0
    minute: int = 0
    day: int = None  # 월별 실행 시 사용
    day_of_week: int = None  # 주별 실행 시 사용 (0=Monday, 6=Sunday)


class BatchSettings(BaseModel):
    timezone: str = "Asia/Seoul"  # 한국 시간대 기본 설정
    
    # 데일리 AI 피드백 생성 스케줄
    daily_feedback: ScheduleJobSettings = ScheduleJobSettings(
        enabled=True,
        hour=22,  # 오후 10시
        minute=0
    )
    
    # 기존 분석 스케줄 (필요시 사용)
    daily_analysis: ScheduleJobSettings = ScheduleJobSettings(
        enabled=False,
        hour=0,
        minute=0
    )
    weekly_report: ScheduleJobSettings = ScheduleJobSettings(
        enabled=False,
        day_of_week=6,  # Sunday
        hour=1,
        minute=0
    )
    monthly_summary: ScheduleJobSettings = ScheduleJobSettings(
        enabled=False,
        day=1,  # 1st day of month
        hour=2,
        minute=0
    )


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


def expand_env_vars(config_str: str) -> str:
    """
    Expand environment variables in config string.
    Supports ${VAR_NAME} and ${VAR_NAME:default_value} syntax.
    """
    def replace_var(match):
        var_expr = match.group(1)
        # Check for default value syntax: ${VAR:default}
        if ':' in var_expr:
            var_name, default_value = var_expr.split(':', 1)
            return os.getenv(var_name.strip(), default_value.strip())
        else:
            # Return environment variable or keep placeholder if not found
            return os.getenv(var_expr.strip(), match.group(0))

    # Replace ${VAR_NAME} or ${VAR_NAME:default}
    return re.sub(r'\$\{([^}]+)\}', replace_var, config_str)


def load_settings() -> Settings:
    """
    Load settings from config files and environment variables.

    Loading order:
    1. Load .env file (if exists)
    2. Load config.yaml with environment variable expansion
    3. Load prompts.yaml
    """
    # Load environment variables from .env file
    # This will load .env if it exists, or .env.example as fallback
    env_file = Path(".env")
    if not env_file.exists():
        env_file = Path(".env.example")

    if env_file.exists():
        load_dotenv(env_file)

    config_path = Path("config/config.yaml")
    prompts_path = Path("config/prompts.yaml")
    settings_dict = {}

    # Load main config with environment variable expansion
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
            # Expand environment variables in the config content
            expanded_content = expand_env_vars(config_content)
            config_data = yaml.safe_load(expanded_content)
            if config_data:
                settings_dict.update(config_data)

    # Load prompts config
    if prompts_path.exists():
        with open(prompts_path, 'r', encoding='utf-8') as f:
            prompts_content = f.read()
            expanded_prompts = expand_env_vars(prompts_content)
            prompts_data = yaml.safe_load(expanded_prompts)
            if prompts_data:
                settings_dict['prompts'] = prompts_data

    settings = Settings(**settings_dict)

    return settings


# Global settings instance
settings = load_settings()