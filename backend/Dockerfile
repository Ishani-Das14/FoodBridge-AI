# Stage 1: Build dependencies
FROM python:3.11-slim as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /install
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Final image
FROM python:3.11-slim

# Install runtime dependencies for psycopg2 and xgboost
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . /app

# Change ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8000

# We assume standard module paths
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
