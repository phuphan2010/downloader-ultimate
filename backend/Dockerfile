FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry and build dependencies
RUN pip install "setuptools>=68.0" poetry==1.8.3

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --without dev

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /data/jobs

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
