# Dockerfile
FROM python:3.12-slim

# Install system dependencies for Ray dashboard
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home appuser && chown -R appuser:appuser /app

# IMPORTANT: Ray needs to write logs
RUN mkdir -p /tmp/ray && chown -R appuser:appuser /tmp/ray

USER appuser

EXPOSE 8000 8265

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]