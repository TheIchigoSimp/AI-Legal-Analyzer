FROM python:3.11-slim

WORKDIR /app

# Install system deps for faiss
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (for caching)
COPY pyproject.toml ./

# Install Python deps
RUN pip install --no-cache-dir .

# Copy application code
COPY . .

# Create data and upload directories
RUN mkdir -p data uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
