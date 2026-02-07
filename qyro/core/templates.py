from typing import Dict

# Common base image with shared tools for all languages
DOCKERFILE_COMMON_BASE = """
FROM alpine:3.18

# Install common system dependencies
RUN apk add --no-cache \
    curl \
    wget \
    git \
    bash \
    openssh \
    ca-certificates

# Create app directory
RUN mkdir -p /app
WORKDIR /app

# Set environment variables for consistency
ENV APP_HOME=/app \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Copy Qyro adapters (shared across all languages)
COPY qyro_adapters /app/qyro_adapters
"""

# Language-specific base images that extend the common base
DOCKERFILE_PYTHON_BASE = """
FROM qyro/common-base:latest

# Install Python runtime and dependencies
RUN apk add --no-cache \
    python3 \
    python3-dev \
    py3-pip \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev

# Upgrade pip
RUN pip3 install --no-cache-dir --upgrade pip

# Install common Python dependencies (shared across all Python services)
RUN pip3 install --no-cache-dir \
    redis \
    kafka-python \
    requests \
    pydantic

# Set Python environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1
"""

DOCKERFILE_NODE_BASE = """
FROM qyro/common-base:latest

# Install Node.js runtime
RUN apk add --no-cache \
    nodejs \
    npm

# Install common Node.js dependencies (shared across all Node.js services)
RUN npm install -g \
    axios \
    ioredis \
    kafkajs

# Set Node.js environment variables
ENV NODE_ENV=production
"""

DOCKERFILE_JAVA_BASE = """
FROM eclipse-temurin:17-jdk-alpine AS java-base

# Install build tools
RUN apk add --no-cache curl wget git bash ca-certificates maven

WORKDIR /app

# Pre-download common Maven dependencies for Kafka/Redis
RUN mkdir -p /tmp/warmup && cd /tmp/warmup && \
    echo '<project><modelVersion>4.0.0</modelVersion><groupId>w</groupId><artifactId>w</artifactId><version>1</version><dependencies><dependency><groupId>redis.clients</groupId><artifactId>jedis</artifactId><version>5.1.0</version></dependency><dependency><groupId>org.apache.kafka</groupId><artifactId>kafka-clients</artifactId><version>3.6.1</version></dependency><dependency><groupId>com.fasterxml.jackson.core</groupId><artifactId>jackson-databind</artifactId><version>2.16.1</version></dependency></dependencies></project>' > pom.xml && \
    mvn dependency:go-offline -q && rm -rf /tmp/warmup

ENV APP_HOME=/app LANG=C.UTF-8
COPY qyro_adapters /app/qyro_adapters
"""

DOCKERFILE_RUST_BASE = """
FROM rust:1.83 AS rust-base

# Install system dependencies for native compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget git bash ca-certificates \
    build-essential pkg-config cmake \
    libssl-dev libsasl2-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pre-compile common crates (cached in image)
RUN mkdir -p /tmp/warmup && cd /tmp/warmup && \
    echo '[package]\nname = "warmup"\nversion = "0.1.0"\nedition = "2021"\n[dependencies]\nredis = "0.24"\nserde = { version = "1.0", features = ["derive"] }\nserde_json = "1.0"\ntokio = { version = "1.35", features = ["full"] }\nuuid = { version = "1.6", features = ["v4"] }' > Cargo.toml && \
    mkdir src && echo 'fn main() {}' > src/main.rs && \
    cargo build --release 2>/dev/null || true && \
    rm -rf /tmp/warmup

ENV APP_HOME=/app LANG=C.UTF-8 CARGO_HOME=/root/.cargo
COPY qyro_adapters /app/qyro_adapters
"""

# Service-specific Dockerfile templates that use language-specific bases
DOCKERFILE_PYTHON = """
FROM qyro/python-base:latest

WORKDIR /app

# Copy requirements and install service-specific dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run command
CMD ["python3", "{filename}"]
"""

DOCKERFILE_UNIVERSAL_PYTHON = """
FROM python:3.11-slim

# Install system dependencies if any
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev \\
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
CMD ["python", "{filename}"]
"""

DOCKERFILE_NODE = """
FROM qyro/node-base:latest

WORKDIR /app

# Copy package.json and install service-specific dependencies
COPY package.json .
RUN npm install --production

# Copy application code
COPY . .

# Run command
CMD ["npm", "start"]
"""

DOCKERFILE_UNIVERSAL_NODE = """
FROM qyro/node-base:latest

WORKDIR /app

# Copy package.json and install service-specific dependencies
COPY package.json .
RUN npm install --production

# Copy application code
COPY . .

# Run command
CMD ["npm", "start"]
"""

DOCKERFILE_JAVA = """
FROM qyro/java-base:latest

WORKDIR /app

# Copy pom.xml and source code
COPY pom.xml .
COPY src ./src

# Build the application (uses Maven cache from base image)
RUN mvn package -DskipTests

# Run command
CMD ["java", "-jar", "target/*.jar"]
"""

DOCKERFILE_RUST = """
FROM qyro/rust-base:latest

WORKDIR /app

# Copy Cargo.toml and source code
COPY Cargo.toml .
COPY src ./src

# Build the application (uses Cargo cache from base image)
RUN cargo build --release

# Run command
CMD ["./target/release/{bin_name}"]
"""

DOCKERFILE_UNIVERSAL_RUST = """
FROM rust:1.83

# Install common Rust dependencies
RUN cargo install redis rdkafka serde serde_json tokio

WORKDIR /app

COPY Cargo.toml .
COPY src ./src
RUN cargo build --release

CMD ["./target/release/{bin_name}"]
"""

# Base image tags
COMMON_BASE_IMAGE = "qyro/common-base:latest"
PYTHON_BASE_IMAGE = "qyro/python-base:latest"
NODE_BASE_IMAGE = "qyro/node-base:latest"
JAVA_BASE_IMAGE = "qyro/java-base:latest"
RUST_BASE_IMAGE = "qyro/rust-base:latest"

# Docker Compose template with language-specific service configurations
DOCKER_COMPOSE_TEMPLATE = """
version: '3.8'

services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    networks:
      - qyro-net
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  kafka:
    image: apache/kafka:latest
    ports:
      - "9092:9092"
    environment:
      - KAFKA_NODE_ID=1
      - KAFKA_PROCESS_ROLES=broker,controller
      - KAFKA_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093
      - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
      - KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER
      - KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      - KAFKA_CONTROLLER_QUORUM_VOTERS=1@kafka:9093
      - KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1
      - KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1
      - KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1
      - KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS=0
    networks:
      - qyro-net
    healthcheck:
      test: ["CMD-SHELL", "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list || exit 1"]
      interval: 10s
      timeout: 10s
      retries: 10

{services}

networks:
  qyro-net:
    driver: bridge
"""

