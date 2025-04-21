"""Logging configuration with automatic redaction of sensitive values"""

import logging
import sys
import re
from typing import List
from routeros_backup.config import Settings


class RedactingFormatter(logging.Formatter):
    """Custom formatter that redacts sensitive values from log messages"""

    def __init__(self, secrets: List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.secrets = secrets

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        for secret in self.secrets:
            if secret:
                message = re.sub(re.escape(secret), "***", message)
        return message


def extract_secrets_from_settings() -> List[str]:
    """Extract sensitive string values from the Settings model"""
    settings = Settings()
    sensitive_keys = ("key", "secret", "password")

    return [
        str(value)
        for field, value in settings.model_dump().items()
        if isinstance(value, str) and any(k in field.lower() for k in sensitive_keys)
    ]


def configure_logging(secrets: List[str] = None):
    """Configure global logging with redaction support for sensitive data"""
    if secrets is None:
        secrets = extract_secrets_from_settings()

    handler = logging.StreamHandler(sys.stdout)
    formatter = RedactingFormatter(
        secrets,
        fmt="%(asctime)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
