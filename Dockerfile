# --- Stage 1: Build Dependencies ---
FROM python:3.13-alpine AS builder

WORKDIR /app

# Install build tools for cryptographic dependencies
RUN apk add --no-cache --virtual .build-deps \
    gcc musl-dev libffi-dev openssl-dev

# Copy Python dependencies
COPY requirements.txt .

# Install Python packages into a clean directory
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt && \
    apk del .build-deps

# --- Stage 2: Final Runtime Image ---
FROM python:3.13-alpine

# Create non-root user for security
RUN addgroup -S backupgroup && adduser -S backupuser -G backupgroup

# Install runtime libraries needed by paramiko + boto3
RUN apk add --no-cache libffi libgcc libcrypto3 zlib

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy app source
COPY . .

# Set proper permissions
RUN chown -R backupuser:backupgroup /app

# Switch to non-root user
USER backupuser

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Default execution
CMD ["python", "-m", "routeros_backup.main"]
