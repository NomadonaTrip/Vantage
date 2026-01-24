# =============================================================================
# Vantage API - FastAPI Dockerfile
# =============================================================================
# Multi-stage build for efficient production images

# -----------------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.14-slim as builder

WORKDIR /app

# Install Poetry
ENV POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

RUN pip install poetry==${POETRY_VERSION}

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies (without dev dependencies for production)
RUN poetry install --no-dev --no-root

# -----------------------------------------------------------------------------
# Stage 2: Runtime
# -----------------------------------------------------------------------------
FROM python:3.14-slim as runtime

WORKDIR /app

# Create non-root user for security
RUN addgroup --system --gid 1001 vantage && \
    adduser --system --uid 1001 --gid 1001 vantage

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Set PATH to use virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY --chown=vantage:vantage src/ /app/src/

# Switch to non-root user
USER vantage

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health/live')" || exit 1

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
