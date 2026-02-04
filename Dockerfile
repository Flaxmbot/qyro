# ============================================
# Multi-stage Dockerfile for Qyro
# ============================================

# Stage 1: Base image
FROM python:3.11-slim AS base
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libc-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Rust (for Rust modules)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
ENV PATH="/root/.cargo/bin:${PATH}"

# Install Node.js (for React/TypeScript modules)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install Java (for Java modules)
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-21-jdk \
    maven \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Orchestrator builder
FROM base AS orchestrator-builder
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY qyro/ ./qyro/

# Stage 3: Gateway builder  
FROM base AS gateway-builder
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY qyro/ ./qyro/

# Stage 4: Final orchestrator image
FROM python:3.11-slim AS orchestrator
WORKDIR /app

# Copy installed Python packages from builder
COPY --from=orchestrator-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=orchestrator-builder /app /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["python", "-m", "qyro.orchestrator"]

# Stage 5: Final gateway image
FROM python:3.11-slim AS gateway
WORKDIR /app

# Copy installed Python packages from builder
COPY --from=gateway-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=gateway-builder /app /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000 8765
CMD ["python", "-m", "qyro.gateway"]
