FROM python:3.12-slim AS base

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[all]"

# Application
COPY . .
RUN pip install --no-cache-dir -e ".[all]"

EXPOSE 8000

CMD ["python", "-m", "ncp.cli.main", "--serve"]
