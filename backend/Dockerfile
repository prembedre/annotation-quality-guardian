# ==============================================================================
# Annotation Quality Guardian — Backend Dockerfile
# Multi-package Python 3.11 slim image with non-root security & healthcheck
# ==============================================================================

FROM python:3.11-slim

# Prevent writing bytecode and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend:/app:/app/scoring \
    PORT=8000 \
    HOST=0.0.0.0

WORKDIR /app

# Create non-root system group and user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Install system dependencies & clean apt caches
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Layer-cached Python dependency installation
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend application, scoring engine, tests and configurations
COPY backend /app/backend
COPY scoring /app/scoring
COPY pytest.ini /app/pytest.ini
COPY seed_demo_data.py /app/seed_demo_data.py

# Ensure executable permissions on entrypoint script and set directory ownership
RUN chmod +x /app/backend/entrypoint.sh && \
    chown -R appuser:appgroup /app

WORKDIR /app/backend

# Run as non-root user
USER appuser

EXPOSE 8000

# Container healthcheck using Python's standard library
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; sys_exit = 0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).getcode() == 200 else 1; exit(sys_exit)"

ENTRYPOINT ["/app/backend/entrypoint.sh"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
