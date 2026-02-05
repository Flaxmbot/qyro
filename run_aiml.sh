#!/bin/bash

# Qyro AI/ML Pipeline Runner Script
# Supports hot reload and easy Docker management

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="docker-compose.qyro.yml"
PROJECT_NAME="qyro-aiml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  (none)     Run AI/ML pipeline with hot reload (default)"
    echo "  --build    Rebuild Docker image and run"
    echo "  up         Start services without hot reload"
    echo "  down       Stop all services"
    echo "  logs       Show service logs"
    echo "  status     Show service status"
    echo "  restart    Restart services"
    echo "  --help     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                  # Run with hot reload"
    echo "  $0 --build          # Rebuild and run"
    echo "  $0 down             # Stop containers"
    echo "  $0 logs -f          # Follow logs"
}

build_image() {
    print_info "Building Qyro Runner Docker image..."
    docker build -t qyro-runner:latest -f qyro_runner.Dockerfile .
    print_success "Image built successfully"
}

start_services() {
    print_info "Starting Qyro AI/ML services..."
    docker-compose -f "$COMPOSE_FILE" up -d "$PROJECT_NAME"
    print_success "Services started. Use '$0 logs -f' to see output."
}

stop_services() {
    print_info "Stopping Qyro AI/ML services..."
    docker-compose -f "$COMPOSE_FILE" stop "$PROJECT_NAME"
    print_success "Services stopped"
}

show_logs() {
    docker-compose -f "$COMPOSE_FILE" logs -f "$PROJECT_NAME"
}

show_status() {
    print_info "Qyro AI/ML Status:"
    docker-compose -f "$COMPOSE_FILE" ps "$PROJECT_NAME"
}

restart_services() {
    print_info "Restarting Qyro AI/ML services..."
    docker-compose -f "$COMPOSE_FILE" restart "$PROJECT_NAME"
    print_success "Services restarted"
}

run_with_hot_reload() {
    print_info "Building Qyro Runner Docker image..."
    docker build -t qyro-runner:latest -f qyro_runner.Dockerfile .
    
    print_info "Starting Qyro AI/ML Pipeline with hot reload..."
    print_info "Watching for changes in: aiml.qyro"
    print_info "Ports:"
    print_info "  - 5000: ML API (model training/predictions)"
    print_info "  - 5001: Data ingestion service"
    print_info "  - 5002: Analytics service"
    print_info ""
    print_info "Press Ctrl+C to stop"
    print_info "----------------------------------------"
    
    # Start Redis, Kafka first
    docker-compose -f "$COMPOSE_FILE" up -d redis kafka
    
    # Run AI/ML app with hot reload (blocking)
    docker-compose -f "$COMPOSE_FILE" up --watch qyro-aiml
}

# Main script logic
case "${1:-}" in
    --help|-h)
        usage
        exit 0
        ;;
    --build|-b)
        build_image
        start_services
        ;;
    up)
        start_services
        ;;
    down|stop)
        stop_services
        ;;
    logs)
        shift
        docker-compose -f "$COMPOSE_FILE" logs -f "$PROJECT_NAME" "$@"
        ;;
    status|ps)
        show_status
        ;;
    restart)
        restart_services
        ;;
    "")
        run_with_hot_reload
        ;;
    *)
        print_error "Unknown command: $1"
        usage
        exit 1
        ;;
esac
