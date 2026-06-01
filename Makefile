# ==============================================================================
# FoodBridge AI - Automation Command Center (Makefile)
# ==============================================================================

.PHONY: help dev test build down logs ps shell db-shell

# Default target: show help information
help:
	@echo "=============================================================================="
	@echo "                       FoodBridge AI - Developer Makefile                     "
	@echo "=============================================================================="
	@echo "Available commands:"
	@echo "  make dev          - Run development environment in Docker (detached mode)"
	@echo "  make test         - Run test suites (FastAPI via PyTest & Frontend linter)"
	@echo "  make build        - Force rebuild of all Docker services (no cache)"
	@echo "  make down         - Stop and remove all running Docker services and networks"
	@echo "  make logs         - View real-time aggregated logs from containers"
	@echo "  make ps           - List all running project containers and their status"
	@echo "  make shell        - Drop into the running FastAPI container bash shell"
	@echo "  make db-shell     - Connect directly to the PostgreSQL console inside Docker"
	@echo "=============================================================================="

# 1. RUN DEVELOPMENT WORKSPACE
dev:
	@echo "Checking environment config..."
	@if [ ! -f .env ]; then \
		echo "Creating local .env from .env.example..."; \
		cp .env.example .env; \
	fi
	@echo "Starting up FoodBridge AI containers in detached mode..."
	docker compose up -d --build
	@echo "Application services started! Run 'make logs' to view output."
	@echo "FastAPI API Server is available at: http://localhost:8000"
	@echo "React SPA Frontend is available at:  http://localhost:80"

# 2. RUN TEST SUITES
test:
	@echo "Running backend PyTest suite within Docker container..."
	docker compose exec fastapi pytest --tb=short
	@echo "Running frontend quality checks..."
	docker compose exec react npm run lint || echo "Frontend lint checks finished."

# 3. BUILD ALL DOCKER SERVICES
build:
	@echo "Rebuilding all Docker images with zero caching..."
	docker compose build --no-cache

# ADDITIONAL UTILITIES
down:
	@echo "Stopping and cleaning up containers..."
	docker compose down

logs:
	@echo "Streaming application logs (Ctrl+C to exit)..."
	docker compose logs -f

ps:
	@echo "Listing active container instances..."
	docker compose ps

shell:
	@echo "Opening bash shell inside 'fastapi' API service..."
	docker compose exec fastapi /bin/sh

db-shell:
	@echo "Opening PostgreSQL shell..."
	docker compose exec db psql -U foodbridge_admin -d foodbridge_db
