
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies if any
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy adapters
COPY qyro_adapters /app/qyro_adapters
ENV PYTHONPATH=/app

# Copy application code
COPY . .

# Run command
CMD ["python", "main.py"]
