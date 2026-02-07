
FROM python:3.11-slim

# Install system dependencies if any
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install common Python dependencies
RUN pip install redis kafka-python requests

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run command
CMD ["python", "main.py"]
