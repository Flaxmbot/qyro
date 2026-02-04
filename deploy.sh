#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Qyro Production Deployment${NC}"
echo "================================"

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Determine docker compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# Function to display usage
usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start     Start all services"
    echo "  stop     Stop all services"
    echo "  restart  Restart all services"
    echo "  rebuild  Rebuild and restart all services"
    echo "  logs     Show logs for all services"
    echo "  status   Show status of all services"
    echo "  clean    Stop and remove all data"
    echo ""
}

# Parse command
case "${1:-start}" in
    start)
        echo -e "${YELLOW}📦 Starting Qyro services...${NC}"
        $COMPOSE_CMD up -d
        echo -e "${GREEN}✅ All services started!${NC}"
        echo ""
        echo "Services:"
        $COMPOSE_CMD ps
        ;;
    stop)
        echo -e "${YELLOW}🛑 Stopping Qyro services...${NC}"
        $COMPOSE_CMD stop
        echo -e "${GREEN}✅ All services stopped!${NC}"
        ;;
    restart)
        echo -e "${YELLOW}🔄 Restarting Qyro services...${NC}"
        $COMPOSE_CMD restart
        echo -e "${GREEN}✅ All services restarted!${NC}"
        ;;
    rebuild)
        echo -e "${YELLOW}🔨 Rebuilding and restarting Qyro services...${NC}"
        $COMPOSE_CMD down
        $COMPOSE_CMD up -d --build
        echo -e "${GREEN}✅ All services rebuilt and started!${NC}"
        ;;
    logs)
        echo -e "${YELLOW}📋 Showing logs...${NC}"
        $COMPOSE_CMD logs -f
        ;;
    status)
        echo -e "${YELLOW}📊 Service status:${NC}"
        $COMPOSE_CMD ps
        ;;
    clean)
        echo -e "${YELLOW}🧹 Cleaning up all data...${NC}"
        $COMPOSE_CMD down -v
        echo -e "${GREEN}✅ All data cleaned!${NC}"
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        usage
        exit 1
        ;;
esac
