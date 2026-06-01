# ==============================================================================
# FoodBridge AI - Backend Dockerfile
# Multi-stage build for a slim, secure, and production-ready FastAPI image
# ==============================================================================

# --- BUILD STAGE ---
FROM python:3.11-slim AS builder

WORKDIR /build

# Install compilation dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies to a temporary folder
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- RUN STAGE ---
FROM python:3.11-slim AS final

WORKDIR /app

# Install system dependencies, including PostGIS client libraries (GDAL, GEOS, Proj, Pg_Isready)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    binutils \
    libproj-dev \
    gdal-bin \
    libgeos-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code and entrypoint scripts
COPY ./app /app/app
COPY ./docker/entrypoint.sh /app/entrypoint.sh

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
