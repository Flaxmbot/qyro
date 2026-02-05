# Qyro Docker Configuration

This directory contains Docker configuration for running .qyro files with hot reload support.

## Files

- `qyro_runner.Dockerfile` - Base Docker image for running qyro files
- `docker-compose.qyro.yml` - Docker Compose file with services for all .qyro projects
- `run_chat.sh` - Runner script for chat_app.qyro
- `run_aiml.sh` - Runner script for aiml.qyro
- `run_ecommerce.sh` - Runner script for ecommerce.qyro

## Prerequisites

- Docker Engine 20.10+
- Docker Compose V2
- 4GB+ RAM available for containers

## Quick Start

### Chat App (Polyglot: Python, React, Rust, Java)

```bash
# Run with hot reload (Linux/macOS/Git Bash)
./run_chat.sh

# Windows PowerShell
docker-compose -f docker-compose.qyro.yml up --watch qyro-chat

# Commands
./run_chat.sh --build   # Rebuild and run
./run_chat.sh down      # Stop services
./run_chat.sh logs -f   # Follow logs
```

**Ports:**
- 3000: React dev server
- 8000: Python/FastAPI server
- 8080: Rust service
- 8081: Java service

### AI/ML Pipeline (Python)

```bash
# Run with hot reload (Linux/macOS/Git Bash)
./run_aiml.sh

# Windows PowerShell
docker-compose -f docker-compose.qyro.yml up --watch qyro-aiml

# Commands
./run_aiml.sh --build   # Rebuild and run
./run_aiml.sh down      # Stop services
./run_aiml.sh logs -f   # Follow logs
```

**Ports:**
- 5000: ML API (model training/predictions)
- 5001: Data ingestion service
- 5002: Analytics service

### E-commerce API (Python + Node.js)

```bash
# Run with hot reload (Linux/macOS/Git Bash)
./run_ecommerce.sh

# Windows PowerShell
docker-compose -f docker-compose.qyro.yml up --watch qyro-ecommerce

# Commands
./run_ecommerce.sh --build   # Rebuild and run
./run_ecommerce.sh down      # Stop services
./run_ecommerce.sh logs -f   # Follow logs
```

**Ports:**
- 4000: FastAPI (order/product services)
- 4001: Node.js payment service
- 4002: Inventory service

## Infrastructure Services

All projects use the following shared infrastructure:

- **Redis** (port 6379) - Cache and pub/sub
- **Kafka** (port 9092) - Event streaming
- **Zookeeper** (port 2181) - Kafka coordination

## Docker Compose Commands

```bash
# Start all services (blocking, with watch)
docker-compose -f docker-compose.qyro.yml up

# Start specific service
docker-compose -f docker-compose.qyro.yml up qyro-chat

# Start with rebuild
docker-compose -f docker-compose.qyro.yml up --build

# Start in detached mode
docker-compose -f docker-compose.qyro.yml up -d

# Stop all services
docker-compose -f docker-compose.qyro.yml down

# View logs
docker-compose -f docker-compose.qyro.yml logs -f

# View status
docker-compose -f docker-compose.qyro.yml ps
```

## Hot Reload

The `--watch` flag enables automatic hot reload when source files change:

- Changes to `.qyro` files trigger automatic restart
- Changes to mounted modules trigger automatic restart
- Changes to source code require container rebuild for some languages (Rust, Java)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `QYRO_PROJECT` | Project name | (service-specific) |
| `QYRO_REDIS_URL` | Redis connection URL | `redis://redis:6379` |
| `QYRO_KAFKA_URL` | Kafka connection URL | `kafka://kafka:9092` |
| `QYRO_MODE` | Runtime mode | `polyglot` or `python` |

## Building the Runner Image Manually

```bash
docker build -t qyro-runner:latest -f qyro_runner.Dockerfile .
```

## Troubleshooting

### Port Already in Use

If you get port conflicts, stop existing containers:

```bash
docker-compose -f docker-compose.qyro.yml down
```

### Out of Memory

Reduce container memory usage by editing `docker-compose.qyro.yml` and adding:

```yaml
services:
  qyro-chat:
    deploy:
      resources:
        limits:
          memory: 1G
```

### Kafka Connection Issues

Ensure Zookeeper is running before Kafka:

```bash
docker-compose -f docker-compose.qyro.yml up -d zookeeper
sleep 5
docker-compose -f docker-compose.qyro.yml up -d kafka
```
