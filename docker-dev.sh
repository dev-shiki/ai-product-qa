#!/bin/bash

# Product Assistant Docker Development Script

set -e

echo "🚀 Product Assistant Docker Development Script"
echo "=============================================="

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build     - Build the Docker image"
    echo "  start     - Start the application"
    echo "  stop      - Stop the application"
    echo "  restart   - Restart the application"
    echo "  logs      - Show application logs"
    echo "  shell     - Open shell in running container"
    echo "  clean     - Clean up Docker resources"
    echo "  test      - Run tests in Docker container"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build"
    echo "  $0 start"
    echo "  $0 logs"
}

# Function to build Docker image
build_image() {
    echo "🔨 Building Docker image..."
    docker-compose build
    echo "✅ Build completed!"
}

# Function to start application
start_app() {
    echo "🚀 Starting Product Assistant..."
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        echo "⚠️  No .env file found. Creating one with dummy API key..."
        echo "GOOGLE_API_KEY=dummy-key-for-testing" > .env
        echo "✅ Created .env file with dummy API key"
    fi
    
    docker-compose up -d
    echo "✅ Application started!"
    echo ""
    echo "🌐 Access your application:"
    echo "   Frontend: http://localhost:8501"
    echo "   Backend API: http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
    echo ""
    echo "📊 Check status: $0 logs"
}

# Function to stop application
stop_app() {
    echo "🛑 Stopping Product Assistant..."
    docker-compose down
    echo "✅ Application stopped!"
}

# Function to restart application
restart_app() {
    echo "🔄 Restarting Product Assistant..."
    docker-compose restart
    echo "✅ Application restarted!"
}

# Function to show logs
show_logs() {
    echo "📋 Showing application logs..."
    docker-compose logs -f
}

# Function to open shell
open_shell() {
    echo "🐚 Opening shell in container..."
    docker-compose exec ai-product-qa /bin/bash
}

# Function to clean up
clean_up() {
    echo "🧹 Cleaning up Docker resources..."
    docker-compose down -v --remove-orphans
    docker system prune -f
    echo "✅ Cleanup completed!"
}

# Function to run tests
run_tests() {
    echo "🧪 Running tests in Docker container..."
    docker-compose exec ai-product-qa python -m pytest tests/ -v --cov=app --cov-report=term-missing
}

# Main script logic
case "${1:-help}" in
    build)
        build_image
        ;;
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        restart_app
        ;;
    logs)
        show_logs
        ;;
    shell)
        open_shell
        ;;
    clean)
        clean_up
        ;;
    test)
        run_tests
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac 