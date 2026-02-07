from typing import Dict

# Common base image with shared tools for all languages
DOCKERFILE_COMMON_BASE = """
FROM alpine:3.18

# Install minimal system dependencies
RUN apk add --no-cache \
    curl \
    ca-certificates

# Create app directory
RUN mkdir -p /app
WORKDIR /app

# Create non-root user for security
RUN addgroup -g 1001 -S qyro && \
    adduser -u 1001 -S qyro -G qyro

# Set environment variables for consistency
ENV APP_HOME=/app \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Copy Qyro adapters (shared across all languages)
COPY qyro_adapters /app/qyro_adapters

# Change ownership to non-root user
RUN chown -R qyro:qyro /app

# Switch to non-root user
USER qyro
"""

# Language-specific base images that extend the common base
DOCKERFILE_PYTHON_BASE = """
FROM qyro/common-base:latest

# Install Python runtime and dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip

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
COPY package*.json ./
RUN npm ci --only=production

# Set Node.js environment variables
ENV NODE_ENV=production
"""

DOCKERFILE_JAVA_BASE = """
FROM eclipse-temurin:17-jre-alpine AS java-base

# Install minimal tools
RUN apk add --no-cache ca-certificates maven

WORKDIR /app

# Create non-root user for security
RUN addgroup -g 1001 -S qyro && \
    adduser -u 1001 -S qyro -G qyro

# Pre-download common Maven dependencies for Kafka/Redis
RUN mkdir -p /tmp/warmup && cd /tmp/warmup && \
    echo '<project><modelVersion>4.0.0</modelVersion><groupId>w</groupId><artifactId>w</artifactId><version>1</version><dependencies><dependency><groupId>redis.clients</groupId><artifactId>jedis</artifactId><version>5.1.0</version></dependency><dependency><groupId>org.apache.kafka</groupId><artifactId>kafka-clients</artifactId><version>3.6.1</version></dependency><dependency><groupId>com.fasterxml.jackson.core</groupId><artifactId>jackson-databind</artifactId><version>2.16.1</version></dependency></dependencies></project>' > pom.xml && \
    mvn dependency:go-offline -q && rm -rf /tmp/warmup

ENV APP_HOME=/app LANG=C.UTF-8

# Copy Qyro adapters
COPY qyro_adapters /app/qyro_adapters

# Change ownership to non-root user
RUN chown -R qyro:qyro /app

# Switch to non-root user
USER qyro
"""

DOCKERFILE_RUST_BASE = """
FROM rust:1.83-slim AS rust-base

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create non-root user for security
RUN groupadd -g 1001 qyro && \
    useradd -u 1001 -g qyro -m -s /bin/bash qyro

# Pre-compile common crates (cached in image)
RUN mkdir -p /tmp/warmup && cd /tmp/warmup && \
    echo '[package]\nname = "warmup"\nversion = "0.1.0"\nedition = "2021"\n[dependencies]\nredis = "0.24"\nserde = { version = "1.0", features = ["derive"] }\nserde_json = "1.0"\ntokio = { version = "1.35", features = ["full"] }\nuuid = { version = "1.6", features = ["v4"] }' > Cargo.toml && \
    mkdir src && echo 'fn main() {}' > src/main.rs && \
    cargo build --release 2>/dev/null || true && \
    rm -rf /tmp/warmup

ENV APP_HOME=/app LANG=C.UTF-8 CARGO_HOME=/home/qyro/.cargo

# Copy Qyro adapters
COPY qyro_adapters /app/qyro_adapters

# Change ownership to non-root user
RUN chown -R qyro:qyro /app

# Switch to non-root user
USER qyro
"""

# Service-specific Dockerfile templates that use language-specific bases
DOCKERFILE_PYTHON = """
FROM qyro/python-base:latest

WORKDIR /app

# Copy requirements and install service-specific dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --user -r requirements.txt

# Copy application code
COPY . .

# Run command
CMD ["python3", "{filename}"]
"""

DOCKERFILE_UNIVERSAL_PYTHON = """
FROM python:3.11-slim

# Install minimal system dependencies if any
RUN apt-get update && apt-get install -y --no-install-recommends \\
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -g 1001 qyro && \\
    useradd -u 1001 -g qyro -m -s /bin/bash qyro

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy application code
COPY . .

# Change ownership to non-root user
RUN chown -R qyro:qyro /app

# Switch to non-root user
USER qyro

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
COPY package*.json ./
RUN npm ci --only=production

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

# Run command - use exec form to avoid shell process
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

# Run command - executable is already owned by qyro user
CMD ["./target/release/{bin_name}"]
"""

DOCKERFILE_UNIVERSAL_RUST = """
FROM rust:1.83-slim

# Install minimal system dependencies for compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -g 1001 qyro && \
    useradd -u 1001 -g qyro -m -s /bin/bash qyro

WORKDIR /app

# Copy and build - dependencies come from Cargo.toml
COPY Cargo.toml .
COPY src ./src
COPY qyro_adapters ./src/qyro_adapters
RUN cargo build --release

# Change ownership to non-root user
RUN chown -R qyro:qyro /app

# Switch to non-root user
USER qyro

CMD ["./target/release/{bin_name}"]
"""


DOCKERFILE_PYTHON_PROD = """
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc libc-dev libffi-dev \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runner
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

# Avoid running as root
RUN useradd -m qyro && chown -R qyro:qyro /app
USER qyro

CMD ["python", "{filename}"]
"""

DOCKERFILE_WEB_PROD = """
# Stage 1: Builder
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Serve
FROM node:18-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/build ./build
CMD ["serve", "-s", "build", "-l", "3000"]
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
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - qyro-net
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  kafka:
    image: apache/kafka:3.7.0
    restart: unless-stopped
    ports:
      - "9092:9092"
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_LOG_DIRS: /tmp/kraft-combined-logs
    volumes:
      - kafka_data:/tmp/kraft-combined-logs
    networks:
      - qyro-net
    healthcheck:
      test: ["CMD-SHELL", "kafka-topics.sh --bootstrap-server localhost:9092 --list"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s

{services}

volumes:
  redis_data:
  kafka_data:

networks:
  qyro-net:
    driver: bridge
"""

