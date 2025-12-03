FROM python:3.11-slim

LABEL maintainer="KyberShield Security Team"
LABEL description="Quantum Security Monitoring Dashboard"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY dashboard.py .

# Create non-root user for security
RUN adduser --disabled-password --gecos '' monitor && \
    chown -R monitor:monitor /app
USER monitor

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8888/health || exit 1

# Expose monitoring port
EXPOSE 8888

# Start monitoring dashboard
CMD ["gunicorn", "--bind", "0.0.0.0:8888", "--workers", "2", "dashboard:app"]