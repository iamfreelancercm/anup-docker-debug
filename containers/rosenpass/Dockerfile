# Multi-stage build for KyberShield Rosenpass VPN
FROM python:3.11-slim AS builder

LABEL maintainer="KyberShield Security Team"
LABEL description="Rosenpass VPN Builder with liboqs compilation"

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    ninja-build \
    git \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Build liboqs from source
RUN git clone --depth 1 --branch 0.14.0 https://github.com/open-quantum-safe/liboqs.git /src/liboqs \
    && cmake -S /src/liboqs -B /src/liboqs/build -GNinja -DBUILD_SHARED_LIBS=ON -DCMAKE_INSTALL_PREFIX=/usr/local \
    && ninja -C /src/liboqs/build install

# Runtime stage
FROM python:3.11-slim

LABEL maintainer="KyberShield Security Team"
LABEL description="Rosenpass VPN with Real ML-KEM-768 Key Encapsulation"

# Install runtime dependencies
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
RUN python -c "import oqs; print('✅ liboqs imported successfully'); kem = oqs.KeyEncapsulation('Kyber768'); print('✅ ML-KEM-768 quantum VPN ready')"

# Copy application code
COPY app.py .

# Create data directory for tunnel state
RUN mkdir -p /app/data

# Expose ports
EXPOSE 8080 9000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=app.py
ENV ROSENPASS_INTERNAL_MODE=true
ENV QUANTUM_TUNNEL_ENABLED=true

# Run application
CMD ["python", "app.py"]
