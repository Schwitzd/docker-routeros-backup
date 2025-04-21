# docker-routeros-backup

A Docker-based tool to automate MikroTik RouterOS binary backup over SSH and support for uploading to external storage.

Backups can be **encrypted** (strongly suggested) or **unencrypted**, and are uploaded to a **configurable destination**. The image is structured to support multiple backends, currently only **S3-compatible storage** is implemented.

This image is intended to be run by an external scheduler such as **Kubernetes CronJob** or **Docker Cron**, as it does not include a built-in scheduling mechanism.

## Prerequisites

- **SSH access must be configured using a public key** (password authentication is not supported).
- A dedicated backup user should be created with **least-privilege access** for security. The **minimum required policies** are:
  - `ftp`  
  - `policy`  
  - `read`  
  - `ssh`
  - `sensitive` (only required for encrypted backup)
  - `test`  
  - `write`

## Environment Variables

| Name                | Default       | Description                                                                |
|---------------------|---------------|----------------------------------------------------------------------------|
| `ROUTER_HOST`       | *(required)*  | IP or hostname of the MikroTik router                                      |
| `ROUTER_USER`       | *(required)*  | SSH username for connecting to the router                                  |
| `SSH_KEY_PATH`      | *(required)*  | Path to the private SSH key used for authentication                        |
| `BACKUPNAME_PREFIX` | `routeros`    | Prefix for the backup file name (e.g. `routeros-YYYY-MM-DD.backup`)        |
| `BACKUP_PASSWORD`   | *(required)*  | Password used to encrypt the RouterOS `.backup` file                       |
| `S3_ENDPOINT`       | *(required)*  | Endpoint URL of the S3-compatible storage (e.g. MinIO, AWS S3)             |
| `S3_ACCESS_KEY`     | *(required)*  | Access key for the S3-compatible storage                                   |
| `S3_SECRET_KEY`     | *(required)*  | Secret key for the S3-compatible storage                                   |
| `S3_BUCKET`         | *(required)*  | Name of the target S3 bucket                                               |
| `S3_PREFIX`         | `""`          | Optional path/prefix inside the bucket (e.g. `backups/`)                   |
| `BACKUP_DEST_TYPE`  | `s3`          | Destination backend type. Currently only `s3` is supported                 |
| `RETENTION_DAYS`    | *(optional)*  | Number of days to keep backups in S3. If unset, no pruning is performed    |

## Destination Backends

This image is designed to support multiple backup destinations. Currently, only **S3-compatible storage** is implemented.

### S3-compatible

Backups are uploaded using the official [`boto3`](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) library, which supports most S3-compatible.

> 💡 This project currently uses and has been tested only with **MinIO**. Other endpoints should work as long as their S3 interface is compatible with Boto3.

## To Do

- Implement support for unencrypted `.backup` file exports
- Implement support for more backends (SMB, NFS, Local, etc)
