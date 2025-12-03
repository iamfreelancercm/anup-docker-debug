# Multi-stage build for KyberShield Backup Service  
FROM python:3.11-slim AS builder

LABEL maintainer="KyberShield Security Team"
LABEL description="Quantum Backup Builder with liboqs compilation"

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    ninja-build \
    git \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Build liboqs from source (needed for any quantum features)
RUN git clone --depth 1 --branch 0.10.1 https://github.com/open-quantum-safe/liboqs.git /src/liboqs \
    && cmake -S /src/liboqs -B /src/liboqs/build -GNinja -DBUILD_SHARED_LIBS=ON -DCMAKE_INSTALL_PREFIX=/usr/local \
    && ninja -C /src/liboqs/build install

# Runtime stage
FROM python:3.11-slim

LABEL maintainer="KyberShield Security Team"
LABEL description="Quantum Backup with Real ChaCha20-Poly1305 Encryption"
LABEL service.name="kybershield-backup"
LABEL service.type="backup-archival"
LABEL security.quantum="chacha20-poly1305"
LABEL compliance.immutable="true"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy compiled liboqs libraries from builder stage  
COPY --from=builder /usr/local /usr/local

# Set library path for liboqs
ENV LD_LIBRARY_PATH="/usr/local/lib:${LD_LIBRARY_PATH:-}"

# Create app user with minimal privileges
RUN useradd -r -s /bin/false -d /app backupuser

# Create secure directory structure for quantum backups
WORKDIR /app
RUN mkdir -p /app/config /app/logs /app/scripts && \
    mkdir -p /backup/database /backup/config /backup/storage /backup/temp && \
    chown -R backupuser:backupuser /app /backup && \
    chmod 700 /backup/storage /backup/temp

# Copy application files INCLUDING AI defense and quantum modules
COPY --chown=backupuser:backupuser requirements.txt /app/

# Upgrade pip, setuptools, and wheel
RUN python -m pip install -U pip setuptools wheel

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Test critical imports during build (fail fast if missing libraries)
RUN python -c "import cryptography; from Crypto.Cipher import ChaCha20_Poly1305; print('✅ ChaCha20-Poly1305 quantum backup ready')"

COPY --chown=backupuser:backupuser app.py /app/

# Set production environment variables
ENV PYTHONPATH="/app"
ENV BACKUP_DIR="/backup/storage"
ENV CONFIG_DIR="/app/config"
ENV LOG_DIR="/app/logs"
ENV TEMP_DIR="/backup/temp"
ENV ENCRYPTION_ENABLED="true"
ENV QUANTUM_SAFE_BACKUP="true"
ENV CHACHA20_POLY1305_ENCRYPTION="true"
ENV IMMUTABLE_BACKUPS="true"
ENV ROSENPASS_CONFIG_DIR="/app/config/rosenpass"
ENV ROSENPASS_KEY_DIR="/backup/keys"
ENV ROSENPASS_SOCKET="/var/run/rosenpass/rosenpass.sock"
ENV FLASK_ENV="production"
ENV GUNICORN_WORKERS="1"
ENV GUNICORN_THREADS="2"

# Switch to non-root user
USER backupuser

# Enhanced health check for ECS load balancer integration
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=2 \
    CMD python3 -c "import requests, sys; r = requests.get('http://localhost:5000/health', timeout=5); r.raise_for_status(); sys.exit(0)" || exit 1

# Expose backup service port
EXPOSE 5000

# Persistent volumes for backups and configuration
VOLUME ["/backup/storage", "/backup/keys", "/app/config", "/app/logs"]

# Start production backup service with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "120", "--access-logfile", "/app/logs/access.log", "--error-logfile", "/app/logs/error.log", "app:app"]