FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for qyro
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install watchgod for hot reload
RUN pip install --no-cache-dir watchgod

# Install qyro from local source in editable mode
COPY . .
RUN pip install --no-cache-dir -e .

# Create volume mount points
VOLUME ["/app/project", "/app/modules"]

# Default command - will be overridden by compose
CMD ["sh", "-c", "echo 'Qyro Runner ready. Use docker-compose to run specific projects.'"]
