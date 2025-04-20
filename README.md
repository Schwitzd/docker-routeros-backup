# docker-routeros-backup

Automated MikroTik RouterOS backup over SSH with secure S3 storage and retention support

## Prerequisites

- **SSH access must be configured using a public key** (password authentication is not supported).
- A dedicated backup user should be created with **least-privilege access** for security. The **minimum required policies** are:
  - `ftp`  
  - `policy`  
  - `read`  
  - `ssh`
  - `sensitive`
  - `test`  
  - `write`
