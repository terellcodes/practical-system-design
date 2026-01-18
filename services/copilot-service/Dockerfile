FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy common package first (for layer caching)
COPY common/ /app/common/

# Install common package
RUN pip install --no-cache-dir /app/common/

# Copy pyproject.toml and install dependencies
COPY services/copilot-service/pyproject.toml .
RUN pip install --no-cache-dir .

# Copy service code
COPY services/copilot-service/src/ ./src/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8003

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"]
