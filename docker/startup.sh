#!/bin/bash

# DataPilotFlow Docker Management Script
# Usage: ./startup.sh [command] [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Docker compose files
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
DEV_COMPOSE_FILE="$SCRIPT_DIR/docker-compose.dev.yml"

# Functions
print_usage() {
    echo -e "${BLUE}DataPilotFlow Docker Management Script${NC}"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  start           Start all services with Milvus (recommended)"
    echo "  dev             Start only infrastructure services for development"
    echo "  deploy          Deploy all services including API"
    echo "  stop            Stop all services"
    echo "  restart         Restart all services"
    echo "  status          Show status of all services"
    echo "  logs [service]  Show logs (optionally for specific service)"
    echo "  shell [service] Open shell in service container"
    echo "  build           Build API server image"
    echo "  clean           Remove all containers, volumes, and images"
    echo "  backup          Backup data volumes"
    echo "  restore [file]  Restore data from backup"
    echo "  reset           Reset all volume data (WARNING: destroys all data)"
    echo "  health          Check health of all services"
    echo "  setup           Initial setup (copy env, create directories)"
    echo ""
    echo "Examples:"
    echo "  $0 dev          # Start only infrastructure for development"
    echo "  $0 start        # Start all services including API"
    echo "  $0 stop         # Stop all services"
    echo "  $0 logs mongodb # View MongoDB logs"
    echo "  $0 health       # Check service health"
}

print_status() {
    echo -e "${BLUE}=== DataPilotFlow Services Status ===${NC}"
    docker-compose -f "$COMPOSE_FILE" ps
}

check_health() {
    echo -e "${BLUE}=== Health Check ===${NC}"
    
    # Check API server
    if curl -s http://localhost:8800/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API Server (8800)${NC}"
    else
        echo -e "${RED}✗ API Server (8800)${NC}"
    fi
    
    # Check MongoDB
    if docker exec datapilotflow-mongodb mongosh --eval "db.runCommand('ping')" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ MongoDB (27020)${NC}"
    else
        echo -e "${RED}✗ MongoDB (27020)${NC}"
    fi
    
    # Check Milvus
    if curl -s http://localhost:9091/webui/ > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Milvus WebUI (9091)${NC}"
    else
        echo -e "${RED}✗ Milvus WebUI (9091)${NC}"
    fi
    
    # Check RabbitMQ
    if curl -s http://localhost:15675/api/overview > /dev/null 2>&1; then
        echo -e "${GREEN}✓ RabbitMQ (15675)${NC}"
    else
        echo -e "${RED}✗ RabbitMQ (15675)${NC}"
    fi
}

setup_environment() {
    echo -e "${BLUE}=== Initial Setup ===${NC}"
    
    # Copy environment file if it doesn't exist
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        if [ -f "$SCRIPT_DIR/env.example" ]; then
            cp "$SCRIPT_DIR/env.example" "$PROJECT_ROOT/.env"
            echo -e "${GREEN}✓ Created .env file from template${NC}"
            echo -e "${YELLOW}⚠️  Please edit .env file with your API keys before deploying${NC}"
        else
            echo -e "${RED}✗ env.example not found${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ .env file already exists${NC}"
    fi
    
    # Create necessary directories
    mkdir -p "$PROJECT_ROOT/backend/upload/inbound"
    mkdir -p "$PROJECT_ROOT/backend/upload/archive"
    mkdir -p "$PROJECT_ROOT/backend/upload/failed"
    mkdir -p "$PROJECT_ROOT/backend/upload/interview"
    mkdir -p "$PROJECT_ROOT/backend/logs"
    mkdir -p "$PROJECT_ROOT/data/datapilotflow-milvus"
    mkdir -p "$PROJECT_ROOT/data/datapilotflow-mongodb"
    mkdir -p "$PROJECT_ROOT/data/datapilotflow-rabbitmq"
    echo -e "${GREEN}✓ Created upload, log, and data directories${NC}"
    
    echo -e "${GREEN}Setup complete!${NC}"
}

start_services() {
    echo -e "${BLUE}=== Starting DataPilotFlow with Milvus ===${NC}"
    
    # Create data directories if they don't exist
    mkdir -p "$PROJECT_ROOT/data/datapilotflow-milvus"
    mkdir -p "$PROJECT_ROOT/data/datapilotflow-mongodb"
    mkdir -p "$PROJECT_ROOT/data/datapilotflow-rabbitmq"
    
    echo -e "${YELLOW}📦 Building and starting all services...${NC}"
    # Build and start services with proper dependency order
    docker-compose -f "$COMPOSE_FILE" up -d --build
    
    echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
    # Wait for services to be ready
    echo "  • Waiting for MongoDB..."
    sleep 5
    while ! docker-compose -f "$COMPOSE_FILE" exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; do
        sleep 2
    done
    
    echo "  • Waiting for RabbitMQ..."
    while ! docker-compose -f "$COMPOSE_FILE" exec -T rabbitmq rabbitmq-diagnostics ping > /dev/null 2>&1; do
        sleep 2
    done
    
    echo "  • Waiting for Milvus..."
    sleep 10  # Give Milvus time to start
    
    echo "  • Waiting for API Server..."
    sleep 15  # Give API server time to start
    
    echo ""
    echo -e "${GREEN}✅ All DataPilotFlow services are running!${NC}"
    echo ""
    echo -e "${BLUE}📊 Service URLs:${NC}"
    echo "  • API Server: http://localhost:8800"
    echo "  • Milvus WebUI: http://localhost:9091/webui/"
    echo "  • MongoDB: localhost:27020"
    echo "  • RabbitMQ Management: http://localhost:15675"
    echo "    - Username: datapilotflow"
    echo "    - Password: datapilotflow123"
    echo ""
    echo -e "${BLUE}🔧 Management Commands:${NC}"
    echo "  • Stop services: $0 stop"
    echo "  • View logs: $0 logs [service-name]"
    echo "  • Restart: $0 restart [service-name]"
    echo "  • Status: $0 status"
    echo ""
    echo -e "${GREEN}🎯 DataPilotFlow is ready for knowledge processing!${NC}"
}

deploy_services() {
    echo -e "${BLUE}=== Deploying DataPilotFlow Services ===${NC}"
    
    # Check if .env exists
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        echo -e "${RED}✗ .env file not found. Run '$0 setup' first${NC}"
        exit 1
    fi
    
    # Build and start services
    docker-compose -f "$COMPOSE_FILE" up -d --build
    
    echo -e "${GREEN}✓ Services deployed successfully${NC}"
    echo ""
    print_status
    echo ""
    echo -e "${BLUE}Management URLs:${NC}"
    echo "  API Documentation: http://localhost:8800/docs"
    echo "  Milvus WebUI: http://localhost:9091/webui/"
    echo "  RabbitMQ Management: http://localhost:15675 (datapilotflow/datapilotflow123)"
    echo "  MongoDB: localhost:27020"
}

stop_services() {
    echo -e "${BLUE}=== Stopping DataPilotFlow Services ===${NC}"
    
    docker-compose -f "$COMPOSE_FILE" down
    
    echo -e "${GREEN}✅ All DataPilotFlow services stopped!${NC}"
    echo ""
    echo -e "${BLUE}💡 To start services again: $0 start${NC}"
    echo -e "${BLUE}🗑️  To remove all data: $0 reset${NC}"
}

undeploy_services() {
    echo -e "${BLUE}=== Undeploying DataPilotFlow Services ===${NC}"
    
    docker-compose -f "$COMPOSE_FILE" down
    
    echo -e "${GREEN}✓ Services stopped and removed${NC}"
}

restart_services() {
    echo -e "${BLUE}=== Restarting DataPilotFlow Services ===${NC}"
    
    docker-compose -f "$COMPOSE_FILE" restart
    
    echo -e "${GREEN}✓ Services restarted${NC}"
}

show_logs() {
    local service="$1"
    
    if [ -n "$service" ]; then
        echo -e "${BLUE}=== Logs for $service ===${NC}"
        docker-compose -f "$COMPOSE_FILE" logs -f "$service"
    else
        echo -e "${BLUE}=== All Services Logs ===${NC}"
        docker-compose -f "$COMPOSE_FILE" logs -f
    fi
}

open_shell() {
    local service="$1"
    
    if [ -z "$service" ]; then
        echo -e "${RED}Please specify a service name${NC}"
        echo "Available services: api, mongodb, milvus, rabbitmq"
        exit 1
    fi
    
    echo -e "${BLUE}=== Opening shell in $service ===${NC}"
    docker exec -it "$service" bash
}

build_image() {
    echo -e "${BLUE}=== Building API Server Image ===${NC}"
    
    docker-compose -f "$COMPOSE_FILE" build api
    
    echo -e "${GREEN}✓ API server image built${NC}"
}

dev_mode() {
    echo -e "${BLUE}=== Starting Development Mode (Infrastructure Only) ===${NC}"
    
    # Create data directories if they don't exist
    mkdir -p "$PROJECT_ROOT/data/datapilotflow-milvus"
    mkdir -p "$PROJECT_ROOT/data/datapilotflow-mongodb"
    mkdir -p "$PROJECT_ROOT/data/datapilotflow-rabbitmq"
    
    echo -e "${YELLOW}📦 Starting infrastructure services only...${NC}"
    # Start only infrastructure services (no API server)
    docker-compose -f "$COMPOSE_FILE" up -d mongodb milvus rabbitmq
    
    echo -e "${YELLOW}⏳ Waiting for infrastructure services to be healthy...${NC}"
    # Wait for services to be ready
    echo "  • Waiting for MongoDB..."
    sleep 5
    while ! docker-compose -f "$COMPOSE_FILE" exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; do
        sleep 2
    done
    
    echo "  • Waiting for RabbitMQ..."
    while ! docker-compose -f "$COMPOSE_FILE" exec -T rabbitmq rabbitmq-diagnostics ping > /dev/null 2>&1; do
        sleep 2
    done
    
    echo "  • Waiting for Milvus..."
    sleep 10  # Give Milvus time to start
    
    echo ""
    echo -e "${GREEN}✅ Infrastructure services are running!${NC}"
    echo ""
    echo -e "${BLUE}📊 Service URLs:${NC}"
    echo "  • Milvus WebUI: http://localhost:9091/webui/"
    echo "  • MongoDB: localhost:27020"
    echo "  • RabbitMQ Management: http://localhost:15675"
    echo "    - Username: datapilotflow"
    echo "    - Password: datapilotflow123"
    echo ""
    echo -e "${BLUE}🔧 Development Commands:${NC}"
    echo "  • Run backend locally: cd ../backend && python run_api_server.py"
    echo "  • Stop services: $0 stop"
    echo "  • View logs: $0 logs [service-name]"
    echo "  • Status: $0 status"
    echo ""
    echo -e "${GREEN}🎯 Ready for backend development!${NC}"
}

clean_all() {
    echo -e "${YELLOW}⚠️  This will remove ALL containers, volumes, and images. Are you sure? (y/N)${NC}"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}=== Cleaning All Docker Resources ===${NC}"
        
        # Stop and remove containers
        docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans
        
        # Remove images
        docker rmi $(docker images "datapilotflow*" -q) 2>/dev/null || true
        docker rmi $(docker images "milvus*" -q) 2>/dev/null || true
        
        # Clean up unused resources
        docker system prune -f
        
        echo -e "${GREEN}✓ All Docker resources cleaned${NC}"
    else
        echo -e "${YELLOW}Clean operation cancelled${NC}"
    fi
}

backup_data() {
    local backup_dir="$PROJECT_ROOT/backups"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="$backup_dir/datapilotflow_backup_$timestamp.tar.gz"
    
    echo -e "${BLUE}=== Creating Backup ===${NC}"
    
    mkdir -p "$backup_dir"
    
    # Create backup of volumes
    docker run --rm -v datapilotflow-mongodb-data:/data -v datapilotflow-milvus-data:/milvus -v datapilotflow-rabbitmq-data:/rabbitmq -v "$backup_dir":/backup alpine tar czf "/backup/datapilotflow_backup_$timestamp.tar.gz" /data /milvus /rabbitmq
    
    echo -e "${GREEN}✓ Backup created: $backup_file${NC}"
}

restore_data() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        echo -e "${RED}Please specify backup file path${NC}"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        echo -e "${RED}Backup file not found: $backup_file${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}⚠️  This will restore data from backup. Are you sure? (y/N)${NC}"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}=== Restoring from Backup ===${NC}"
        
        # Stop services
        docker-compose -f "$COMPOSE_FILE" down
        
        # Restore volumes
        docker run --rm -v datapilotflow-mongodb-data:/data -v datapilotflow-milvus-data:/milvus -v datapilotflow-rabbitmq-data:/rabbitmq -v "$(dirname "$backup_file")":/backup alpine tar xzf "/backup/$(basename "$backup_file")" -C /
        
        echo -e "${GREEN}✓ Data restored from backup${NC}"
    else
        echo -e "${YELLOW}Restore operation cancelled${NC}"
    fi
}

reset_volumes() {
    echo -e "${RED}⚠️  WARNING: This will permanently delete ALL data in volumes!${NC}"
    echo -e "${RED}This includes:${NC}"
    echo -e "${RED}  - All MongoDB data (users, roles, notifications, etc.)${NC}"
    echo -e "${RED}  - All Milvus vector data${NC}"
    echo -e "${RED}  - All RabbitMQ queues and messages${NC}"
    echo -e "${RED}  - All uploaded files and processing results${NC}"
    echo ""
    echo -e "${YELLOW}Are you absolutely sure you want to reset all data? (yes/NO)${NC}"
    read -r response
    
    if [[ "$response" == "yes" ]]; then
        echo -e "${BLUE}=== Resetting All Volume Data ===${NC}"
        
        # Stop services
        echo -e "${YELLOW}Stopping services...${NC}"
        docker-compose -f "$COMPOSE_FILE" down
        
        # Remove volumes
        echo -e "${YELLOW}Removing volumes...${NC}"
        docker volume rm datapilotflow-mongodb-data 2>/dev/null || true
        docker volume rm datapilotflow-milvus-data 2>/dev/null || true
        docker volume rm datapilotflow-rabbitmq-data 2>/dev/null || true
        
        # Remove local data directories if they exist
        echo -e "${YELLOW}Cleaning local data directories...${NC}"
        rm -rf "$PROJECT_ROOT/data/datapilotflow-mongodb" 2>/dev/null || true
        rm -rf "$PROJECT_ROOT/data/datapilotflow-rabbitmq" 2>/dev/null || true
        rm -rf "$PROJECT_ROOT/data/datapilotflow-milvus" 2>/dev/null || true
        
        # Clean up upload directories
        echo -e "${YELLOW}Cleaning upload directories...${NC}"
        rm -rf "$PROJECT_ROOT/backend/upload/inbound/*" 2>/dev/null || true
        rm -rf "$PROJECT_ROOT/backend/upload/archive/*" 2>/dev/null || true
        rm -rf "$PROJECT_ROOT/backend/upload/failed/*" 2>/dev/null || true
        rm -rf "$PROJECT_ROOT/backend/upload/interview/*" 2>/dev/null || true
        
        # Clean up logs
        echo -e "${YELLOW}Cleaning log files...${NC}"
        rm -rf "$PROJECT_ROOT/backend/logs/*" 2>/dev/null || true
        
        echo -e "${GREEN}✓ All volume data has been reset${NC}"
        echo -e "${BLUE}You can now run '$0 deploy' to start fresh${NC}"
    else
        echo -e "${YELLOW}Reset operation cancelled${NC}"
    fi
}

# Main script logic
case "${1:-}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    deploy)
        deploy_services
        ;;
    undeploy)
        undeploy_services
        ;;
    restart)
        restart_services
        ;;
    status)
        print_status
        ;;
    logs)
        show_logs "$2"
        ;;
    shell)
        open_shell "$2"
        ;;
    build)
        build_image
        ;;
    dev)
        dev_mode
        ;;
    clean)
        clean_all
        ;;
    backup)
        backup_data
        ;;
    restore)
        restore_data "$2"
        ;;
    reset)
        reset_volumes
        ;;
    health)
        check_health
        ;;
    setup)
        setup_environment
        ;;
    *)
        print_usage
        exit 1
        ;;
esac
