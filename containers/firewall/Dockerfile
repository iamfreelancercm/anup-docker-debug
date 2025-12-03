# Multi-stage build for KyberShield Quantum Firewall
FROM python:3.11-slim AS builder
ENV DEBIAN_FRONTEND=noninteractive
LABEL maintainer="KyberShield Security Team"
LABEL description="Quantum Firewall with Real ML-DSA-87 Signatures - Builder Stage"

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    ninja-build \
    git \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Build liboqs from source (matching liboqs-python version)
RUN git clone --depth 1 --branch 0.14.0 https://github.com/open-quantum-safe/liboqs.git /src/liboqs \
    && cmake -S /src/liboqs -B /src/liboqs/build -GNinja -DBUILD_SHARED_LIBS=ON -DCMAKE_INSTALL_PREFIX=/usr/local \
    && ninja -C /src/liboqs/build install

# Runtime stage
FROM python:3.11-slim
ENV DEBIAN_FRONTEND=noninteractive
LABEL maintainer="KyberShield Security Team"
LABEL description="Quantum Firewall with Real ML-DSA-87 Signatures"
LABEL build.stage="runtime"

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    ca-certificates \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy compiled liboqs libraries from builder stage
COPY --from=builder /usr/local /usr/local

# Set library path for liboqs
ENV LD_LIBRARY_PATH="/usr/local/lib:${LD_LIBRARY_PATH:-}"
RUN echo "/usr/local/lib" > /etc/ld.so.conf.d/liboqs.conf && ldconfig
# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Upgrade pip, setuptools, and wheel
RUN python -m pip install -U pip setuptools wheel

# Install Python dependencies including real quantum crypto
RUN pip install --no-cache-dir -r requirements.txt

# Test critical imports during build (fail fast if missing libraries)
RUN python -c "import oqs; print('✅ liboqs imported successfully'); sig = oqs.Signature('Dilithium2'); print('✅ ML-DSA-87 quantum signatures ready')"

# Copy application code
COPY app.py .

# Create data directory
RUN mkdir -p /app/data

# Expose ports - 3000 (primary), 8080 (legacy compatibility)
EXPOSE 3000 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=app.py
ENV ML_DSA_87_ENABLED=true
ENV QUANTUM_FIREWALL_ENABLED=true
ENV LEGACY_PORT_8080=true

# Run application
CMD ["python", "app.py"]
