# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# - build-essential: needed for building Python packages
# - curl: for downloading/checking dependencies
# - git: may be needed for some packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required for MCP servers via npx)
# Using NodeSource repository for latest LTS version
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Verify Node.js installation
RUN node --version && npm --version

# Copy dependency files and source code
COPY pyproject.toml ./
COPY src/ ./src/
COPY README.md ./

# Install Python build tools and project dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir hatchling \
    && pip install --no-cache-dir -e .

# Create logs directory
RUN mkdir -p logs

# Expose the port that FastAPI runs on
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# Run the application using uvicorn
CMD ["uvicorn", "ai_orchestrator.infra.app:app", "--host", "0.0.0.0", "--port", "8000"]

