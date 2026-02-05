FROM python:3.11-slim-bookworm
WORKDIR /app
# --- System Dependencies ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential git openjdk-17-jdk maven \
    && rm -rf /var/lib/apt/lists/*
# --- Rust Setup ---
ENV RUSTUP_HOME=/usr/local/rustup CARGO_HOME=/usr/local/cargo PATH=/usr/local/cargo/bin:$PATH
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
# --- Go Setup ---
COPY --from=golang:1.21 /usr/local/go /usr/local/go
ENV PATH=$PATH:/usr/local/go/bin
# --- Node.js Setup ---
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs
# --- Qyro Library ---
# Build context is qyro_dist, so paths are relative to that directory
COPY qyro /app/qyro
ENV PYTHONPATH=/app
# Build Java Client
WORKDIR /app/qyro/adapters/language_adapters/java
RUN mvn install -q
WORKDIR /app
# --- Python Dependencies ---
COPY requirements.txt .
RUN pip install -r requirements.txt
# --- Application Source ---
COPY modules /app/modules
# --- Entrypoint ---
CMD ["python", "-m", "qyro.cli.cli", "run-internal"]