from typing import Dict

DOCKERFILE_PYTHON = """
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies if any
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev \\
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
CMD ["python", "{filename}"]
"""

DOCKERFILE_NODE = """
FROM node:18-alpine

WORKDIR /app

COPY package.json .
RUN npm install

# Copy adapters
COPY qyro_adapters /app/qyro_adapters

COPY . .

CMD ["npm", "start"]
"""

DOCKERFILE_RUST = """
FROM rust:1.75 as builder
WORKDIR /usr/src/app
COPY . .
RUN cargo install --path .

FROM debian:bookworm-slim
COPY --from=builder /usr/local/cargo/bin/{bin_name} /usr/local/bin/{bin_name}
CMD ["{bin_name}"]
"""

DOCKERFILE_JAVA = """
FROM maven:3.9-eclipse-temurin-17 as builder
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn package -DskipTests

FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar
CMD ["java", "-jar", "app.jar"]
"""

# Simple setup for development SaaS style
DOCKER_COMPOSE_TEMPLATE = """
version: '3.8'

services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    networks:
      - qyro-net

  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:29092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    networks:
      - qyro-net

  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    networks:
      - qyro-net

{services}

networks:
  qyro-net:
    driver: bridge
"""
