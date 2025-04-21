from routeros_backup.config import Settings
from routeros_backup.backup.ssh import perform_backup
from routeros_backup.destinations.s3 import S3Uploader


def main():
    settings = Settings()
    backup_path = perform_backup()

    uploader = S3Uploader(settings)
    uploader.connect()
    uploader.upload(backup_path)


if __name__ == "__main__":
    main()
