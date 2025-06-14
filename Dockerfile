# --- Stage 1: Build Dependencies ---
FROM python:3.13-slim-bookworm AS builder

WORKDIR /app

# Install build dependencies for cryptography and wheels
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc libffi-dev libssl-dev build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY requirements.txt .

# Install dependencies into a clean directory
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# --- Stage 2: Final Runtime Image ---
FROM python:3.13-slim-bookworm

# Create a non-root user for security
RUN useradd -r -s /usr/sbin/nologin backupuser

WORKDIR /app

# Install only the required runtime libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends libssl3 && \
    rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application source code
COPY . .

# Set permissions for the non-root user
RUN chown -R backupuser:backupuser /app

USER backupuser

# Environment setup
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Default command
CMD ["python", "-m", "routeros_backup.main"]