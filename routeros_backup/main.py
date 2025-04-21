"""Main entry point for RouterOS backup and upload"""

import logging
from routeros_backup.config import Settings
from routeros_backup.logger import configure_logging
from routeros_backup.backup.ssh import perform_backup
from routeros_backup.destinations.s3 import S3Uploader

logger = logging.getLogger(__name__)


def main():
    """Run the backup and upload workflow."""
    settings = Settings()
    configure_logging()

    backup_path = perform_backup()

    if settings.backup_dest_type == "s3":
        logger.info("Uploading backup to S3-compatible storage...")
        uploader = S3Uploader(settings)
        uploader.connect()
        uploader.upload(backup_path)
    else:
        raise ValueError(f"Unsupported backup_dest_type: {settings.backup_dest_type}")


if __name__ == "__main__":
    main()
