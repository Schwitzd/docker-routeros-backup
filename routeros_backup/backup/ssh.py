"""SSH-based logic to create and download MikroTik RouterOS backups."""

import logging
from pathlib import Path
from datetime import datetime, timezone
import paramiko
from routeros_backup.config import Settings

logger = logging.getLogger(__name__)


class RouterOSBackup:
    """Handles SSH connection, backup creation, and download from MikroTik RouterOS."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.ssh = None
        self.backup_name = self._generate_backup_name()

    def _generate_backup_name(self) -> str:
        """Generate a backup filename based on current date."""
        return f"{self.settings.backupname_prefix}-{datetime.now(timezone.utc).date()}.backup"

    def connect(self):
        """Establish an SSH connection to the MikroTik router."""
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.ssh.connect(
            hostname=self.settings.router_host,
            username=self.settings.router_user,
            key_filename=str(self.settings.ssh_key_path),
            look_for_keys=False,
            allow_agent=False,
        )
        logger.info("SSH connection established with %s", self.settings.router_host)

    def run_backup_command(self):
        """Execute the RouterOS backup command via SSH."""
        command = f'/system backup save name={self.backup_name} password="{self.settings.backup_password}"'
        logger.info("Running backup command: %s", command)

        stdin, stdout, stderr = self.ssh.exec_command(command)
        stdout.channel.recv_exit_status()

        err_output = stderr.read().decode()
        if err_output:
            raise RuntimeError(f"RouterOS backup command failed: {err_output.strip()}")

    def download_backup_file(self) -> Path:
        """Download the generated .backup file to the local /tmp/ folder."""
        sftp = self.ssh.open_sftp()
        remote_path = f"/{self.backup_name}"
        local_path = Path(f"/tmp/{self.backup_name}")

        logger.info("Attempting to download backup file from %s to %s", remote_path, local_path)

        try:
            sftp.get(remote_path, str(local_path))
            logger.info("Download completed successfully: %s", local_path)
        except FileNotFoundError:
            logger.error("Backup file not found on router: %s", remote_path)
            raise
        except PermissionError:
            logger.error("Permission denied when accessing: %s", remote_path)
            raise
        except Exception as e:
            logger.exception("Unexpected error while downloading backup file: %s", e)
            raise
        finally:
            sftp.close()

        return local_path
    
    def cleanup_remote_backup(self):
        """Remove the backup file from the MikroTik router to free up space."""
        command = f'/file remove {self.backup_name}'
        logger.info("Cleaning up remote backup file: %s", self.backup_name)

        stdin, stdout, stderr = self.ssh.exec_command(command)
        stdout.channel.recv_exit_status()

        err_output = stderr.read().decode()
        if err_output:
            logger.warning("Failed to delete remote backup file: %s", err_output.strip())
        else:
            logger.info("Remote backup file deleted successfully.")

    def perform(self) -> Path:
        """Main entrypoint: connect, create backup, and download it."""
        self.connect()
        try:
            self.run_backup_command()
            local_path = self.download_backup_file()
            self.cleanup_remote_backup()
            return local_path
        finally:
            if self.ssh:
                self.ssh.close()
                logger.info("SSH connection closed")
