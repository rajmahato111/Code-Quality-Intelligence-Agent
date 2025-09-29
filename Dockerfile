# Multi-stage build for Code Quality Intelligence Agent
FROM node:18-alpine AS frontend-builder

# Build frontend
WORKDIR /app/frontend
COPY code_quality_agent/web/frontend/package*.json ./
RUN npm ci --only=production

COPY code_quality_agent/web/frontend/ ./
RUN npm run build

# Main application image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    tree-sitter-cli \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r cqa && useradd -r -g cqa cqa

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt pyproject.toml ./
COPY setup.py ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install -e .

# Copy application code
COPY code_quality_agent/ ./code_quality_agent/
COPY tests/ ./tests/
COPY docs/ ./docs/
COPY README.md LICENSE ./

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/dist ./code_quality_agent/web/frontend/dist/

# Create necessary directories
RUN mkdir -p /app/cache /app/logs /app/data && \
    chown -R cqa:cqa /app

# Switch to non-root user
USER cqa

# Set default environment variables
ENV CQA_CACHE_DIR=/app/cache \
    CQA_LOG_DIR=/app/logs \
    CQA_DATA_DIR=/app/data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD cqa --version || exit 1

# Expose port for web interface
EXPOSE 8000

# Default command
CMD ["cqa", "serve", "--host", "0.0.0.0", "--port", "8000"]