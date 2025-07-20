"""S3Manager class to handle uploading and managing backups in S3-compatible storage."""

import logging
from pathlib import Path
import boto3
from botocore.config import Config
from botocore.exceptions import (
    ClientError,
    NoCredentialsError,
    EndpointConnectionError
)
from routeros_backup.config import Settings

logger = logging.getLogger(__name__)


class S3Manager:
    """S3-compatible storage management class."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None

    def connect(self):
        """Initialize the S3 client with proper error handling."""
        try:
            is_custom_endpoint = "amazonaws.com" not in self.settings.s3_endpoint

            config = Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"} if is_custom_endpoint else {}
            )

            self.client = boto3.client(
                "s3",
                endpoint_url=self.settings.s3_endpoint,
                aws_access_key_id=self.settings.s3_access_key,
                aws_secret_access_key=self.settings.s3_secret_key,
                region_name=self.settings.s3_region,
                config=config,
            )

            # Trigger a lightweight call to validate connection
            self.client.list_buckets()
            logger.debug("S3 client initialized and verified.")

        except NoCredentialsError:
            logger.error("Missing or invalid S3 credentials.")
            raise RuntimeError("S3 credentials not found or invalid.") from None

        except EndpointConnectionError as err:
            logger.error("Cannot connect to the S3 endpoint: %s", self.settings.s3_endpoint)
            logger.debug("Underlying error: %s", err)
            raise RuntimeError("Failed to connect to the S3 endpoint. Check DNS and port.") from err

        except ClientError as err:
            self._handle_client_error(err, "connect")
            raise RuntimeError(
                f"S3 connection failed: {err.response['Error'].get('Message', 'Unknown error')}"
            ) from err

        except Exception as err:
            logger.exception("Unexpected error during S3 client initialization.")
            raise RuntimeError("Unexpected error during S3 connection setup.") from err

    def upload(self, file_path: Path):
        """Upload the given backup file to S3-compatible storage using put_object."""
        if self.client is None:
            raise RuntimeError("S3 client not initialized. Call connect() first.")

        key = f"{self.settings.s3_prefix}{file_path.name}"

        try:
            logger.info("Uploading %s to s3://%s/%s", file_path, self.settings.s3_bucket, key)

            with open(file_path, "rb") as f:
                self.client.put_object(
                    Bucket=self.settings.s3_bucket,
                    Key=key,
                    Body=f,
                )

            logger.info("Upload complete.")

        except Exception as err:
            logger.exception("Unexpected error during S3 upload.")
            raise RuntimeError("Unexpected error during S3 upload") from err

    def apply_retention_policy(self):
        """Apply retention policy by keeping only the latest N backup files."""
        if not self.settings.retention_points:
            logger.info("No retention policy configured, skipping cleanup.")
            return

        retention_points = self.settings.retention_points

        logger.info(
            "Applying retention policy: keeping the latest %d backup(s)", retention_points
        )

        try:
            response = self.client.list_objects_v2(
                Bucket=self.settings.s3_bucket,
                Prefix=self.settings.s3_prefix
            )

            backups = response.get("Contents", [])
            if not backups:
                logger.info("No backups found in bucket, skipping cleanup.")
                return

            # Sort backups by LastModified descending (newest first)
            backups.sort(key=lambda obj: obj["LastModified"], reverse=True)

            # Determine old backups to delete
            old_backups = backups[retention_points:]

            for backup in old_backups:
                key = backup["Key"]
                logger.info("Deleting old backup: %s (last modified %s)", key, backup["LastModified"])
                self.client.delete_object(
                    Bucket=self.settings.s3_bucket,
                    Key=key
                )

        except ClientError as err:
            self._handle_client_error(err, "retention")
            raise RuntimeError(
                f"S3 retention failed: {err.response['Error'].get('Message', 'Unknown error')}"
            ) from err

        except Exception as err:
            logger.exception("Failed to apply retention policy.")
            raise RuntimeError("Retention policy application failed.") from err

    def _handle_client_error(self, err: ClientError, context: str):
        """Handle S3 ClientError with detailed logging."""
        code = err.response["Error"].get("Code", "Unknown")
        message = err.response["Error"].get("Message", "Unknown error")
        request_id = err.response.get("ResponseMetadata", {}).get("RequestId", "N/A")
        http_code = err.response.get("ResponseMetadata", {}).get("HTTPStatusCode", "N/A")

        logger.error("[%s] S3 ClientError %s: %s", context, code, message)
        logger.error("[%s] Request ID: %s | HTTP Status Code: %s", context, request_id, http_code)

        if code == "AccessDenied":
            logger.error("[%s] Access denied: check your S3 credentials and bucket policy.", context)
        elif code == "InvalidArgument":
            logger.error("[%s] Invalid argument: possibly using console/UI port instead of API port.", context)
        elif code == "InvalidAccessKeyId":
            logger.error("[%s] InvalidAccessKeyId: the S3 access key is incorrect or does not exist.", context)
