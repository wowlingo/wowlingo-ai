import logging
import logging.handlers
import os
from pathlib import Path
from app.config import settings


def setup_logging():
    """Setup logging configuration based on settings"""

    # Create logs directory if it doesn't exist
    log_file_path = Path(settings.logging.file)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Parse log level
    log_level = getattr(logging, settings.logging.level.upper(), logging.INFO)

    # Parse max file size
    max_bytes = parse_file_size(settings.logging.max_file_size)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Add file handler with rotation
    if settings.logging.rotation == "daily":
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=settings.logging.file,
            when='midnight',
            interval=1,
            backupCount=settings.logging.backup_count,
            encoding='utf-8'
        )
    else:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=settings.logging.file,
            maxBytes=max_bytes,
            backupCount=settings.logging.backup_count,
            encoding='utf-8'
        )

    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    return root_logger


def parse_file_size(size_str: str) -> int:
    """Parse file size string like '10MB' to bytes"""
    size_str = size_str.upper().strip()

    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        # Assume bytes
        return int(size_str)


def get_logger(name: str):
    """Get logger with proper configuration"""
    return logging.getLogger(name)