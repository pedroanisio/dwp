#!/bin/bash

# Docker Build Script for Neural Plugin System with Pandoc from Source
# This script provides different build options for development and production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --prod, -p          Build production image with Pandoc from source"
    echo "  --dev, -d           Build development image with system Pandoc"
    echo "  --both, -b          Build both production and development images"
    echo "  --run-prod, -rp     Build and run production container"
    echo "  --run-dev, -rd      Build and run development container"
    echo "  --clean, -c         Clean up Docker images and containers"
    echo "  --help, -h          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --prod           # Build production image with custom Pandoc"
    echo "  $0 --dev            # Build development image with system Pandoc"
    echo "  $0 --run-prod       # Build and run production container"
    echo "  $0 --clean          # Clean up Docker resources"
}

# Function to build production image (with Pandoc from source)
build_production() {
    print_info "Building production image with Pandoc from source..."
    print_warning "This may take 10-20 minutes depending on your system"
    
    # Enable BuildKit for better caching
    export DOCKER_BUILDKIT=1
    
    # Build with cache optimization
    docker build \
        --tag neural-plugin-system:prod \
        --file Dockerfile \
        --cache-from neural-plugin-system:prod \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        .
    
    print_success "Production image built successfully!"
    print_info "Pandoc version in production image:"
    docker run --rm neural-plugin-system:prod pandoc --version
}

# Function to build development image (with system Pandoc)
build_development() {
    print_info "Building development image with system Pandoc..."
    
    export DOCKER_BUILDKIT=1
    
    docker build \
        --tag neural-plugin-system:dev \
        --file Dockerfile.dev \
        --cache-from neural-plugin-system:dev \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        .
    
    print_success "Development image built successfully!"
    print_info "Pandoc version in development image:"
    docker run --rm neural-plugin-system:dev pandoc --version
}

# Function to run production container
run_production() {
    print_info "Building and running production container..."
    build_production
    
    print_info "Starting production container on port 8000..."
    docker-compose up -d web
    
    print_success "Production container is running!"
    print_info "Access the application at: http://localhost:8000"
    print_info "Check container logs: docker-compose logs -f web"
}

# Function to run development container
run_development() {
    print_info "Building and running development container..."
    build_development
    
    print_info "Starting development container on port 8001..."
    docker-compose --profile dev up -d web-dev
    
    print_success "Development container is running!"
    print_info "Access the application at: http://localhost:8001"
    print_info "Check container logs: docker-compose logs -f web-dev"
}

# Function to clean up Docker resources
cleanup() {
    print_info "Cleaning up Docker resources..."
    
    # Stop and remove containers
    docker-compose down || true
    docker-compose --profile dev down || true
    
    # Remove images
    docker rmi neural-plugin-system:prod 2>/dev/null || true
    docker rmi neural-plugin-system:dev 2>/dev/null || true
    
    # Remove dangling images
    docker image prune -f
    
    # Remove build cache (optional)
    read -p "Do you want to remove Docker build cache? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker builder prune -f
        print_info "Build cache removed"
    fi
    
    print_success "Cleanup completed!"
}

# Function to check Docker and docker-compose
check_prerequisites() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
}

# Main script logic
main() {
    check_prerequisites
    
    if [ $# -eq 0 ]; then
        show_usage
        exit 1
    fi
    
    case "$1" in
        --prod|-p)
            build_production
            ;;
        --dev|-d)
            build_development
            ;;
        --both|-b)
            build_development
            build_production
            ;;
        --run-prod|-rp)
            run_production
            ;;
        --run-dev|-rd)
            run_development
            ;;
        --clean|-c)
            cleanup
            ;;
        --help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 