from pathlib import Path
from routeros_backup.destinations.s3 import S3Uploader
from routeros_backup.config import Settings

settings = Settings()
uploader = S3Uploader(settings)
uploader.connect()
uploader.upload(Path("/tmp/routeros-2025-04-21.backup"))
