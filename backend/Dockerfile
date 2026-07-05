FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.8.3

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --without dev

# Always upgrade yt-dlp and install curl-cffi for browser impersonation (BUG-18)
RUN pip install -U yt-dlp "curl-cffi>=0.7.0"

# Copy application code
COPY . .

# Create data and cookies directory
RUN mkdir -p /data/jobs /app/cookies

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
