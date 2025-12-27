FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=2.2.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_VIRTUALENVS_CREATE=false
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install "poetry==$POETRY_VERSION"

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies with Poetry
RUN --mount=type=cache,target=/root/.cache/pypoetry \
    poetry install --only main --no-root --no-interaction --no-ansi

# Copy application files
COPY app.py .
COPY src/ ./src/

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8002/ || exit 1

# Run application with hypercorn (ASGI server for Quart)
CMD ["hypercorn", "app:app", "--bind", "0.0.0.0:8002", "--workers", "4", "--access-logfile", "-", "--error-logfile", "-"]
