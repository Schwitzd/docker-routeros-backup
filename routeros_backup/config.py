from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # MikroTik SSH access
    router_host: str = Field(..., env="ROUTER_HOST")
    router_user: str = Field(..., env="ROUTER_USER")
    ssh_key_path: Path = Field(..., env="SSH_KEY_PATH")
    backupname_prefix: str = Field(default="routeros", env="BACKUPNAME_PREFIX")
    backup_password: str = Field(..., env="BACKUP_PASSWORD")

    # S3-compatible storage
    s3_endpoint: str = Field(..., env="S3_ENDPOINT")
    s3_access_key: str = Field(..., env="S3_ACCESS_KEY")
    s3_secret_key: str = Field(..., env="S3_SECRET_KEY")
    s3_bucket: str = Field(..., env="S3_BUCKET")
    s3_prefix: str = Field(default="", env="S3_PREFIX")

    # General settings
    backup_dest_type: str = Field(default="s3", env="BACKUP_DEST_TYPE")
    retention_days: Optional[int] = Field(default=None, env="RETENTION_DAYS")

    class Config:
        env_file = ".env"
