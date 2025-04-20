import logging
from pathlib import Path
from datetime import datetime, timezone
import paramiko
from routeros_backup.config import Settings

logger = logging.getLogger(__name__)
settings = Settings()


def generate_backup_name() -> str:
    """Generate a backup filename based on current date."""
    return f"routeros-{datetime.now(timezone.utc).date()}.backup"


def create_ssh_client() -> paramiko.SSHClient:
    """Create and return a configured SSH client."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(
        hostname=settings.router_host,
        username=settings.router_user,
        key_filename=str(settings.ssh_key_path),
        look_for_keys=False,
        allow_agent=False,
    )

    return ssh


def run_backup_command(ssh: paramiko.SSHClient, backup_name: str):
    """Run the MikroTik backup command."""
    command = f'/system backup save name={backup_name} password="{settings.backup_password}"'
    logger.info("Running backup command: %s", command)
    stdin, stdout, stderr = ssh.exec_command(command)
    stdout.channel.recv_exit_status()

    err_output = stderr.read().decode()
    if err_output:
        raise RuntimeError(f"RouterOS backup command failed: {err_output.strip()}")


def download_backup_file(ssh: paramiko.SSHClient, backup_name: str) -> Path:
    """Download the .backup file from the router to the local /tmp/ folder."""
    sftp = ssh.open_sftp()
    remote_path = f"/{backup_name}"
    local_path = Path(f"/tmp/{backup_name}")

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


def perform_backup() -> Path:
    """Main entrypoint to create and download a MikroTik backup."""
    backup_name = generate_backup_name()

    logger.info("Connecting to MikroTik at %s...", settings.router_host)
    ssh = create_ssh_client()

    try:
        run_backup_command(ssh, backup_name)
        local_backup_path = download_backup_file(ssh, backup_name)
    finally:
        ssh.close()

    logger.info("Backup completed: %s", local_backup_path)
    return local_backup_path
