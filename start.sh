#!/bin/bash
#
# Voice Generator Launcher for macOS
# Builds and starts the voice cloning web server
#

set -e  # Exit on error

# Parse arguments
REBUILD=false
NO_BROWSER=false

for arg in "$@"; do
    case $arg in
        --rebuild)
            REBUILD=true
            shift
            ;;
        --no-browser)
            NO_BROWSER=true
            shift
            ;;
        --help)
            echo "Voice Generator Launcher"
            echo ""
            echo "Usage: ./start.sh [options]"
            echo ""
            echo "Options:"
            echo "  --rebuild      Force rebuild Docker image"
            echo "  --no-browser   Don't auto-open browser"
            echo "  --help         Show this help message"
            exit 0
            ;;
    esac
done

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Emojis
CHECK="✓"
ROCKET="🚀"
MIC="🎤"
LINK="🔗"

echo ""
echo -e "${BLUE}${MIC} Voice Generator Launcher${NC}"
echo "========================================"
echo ""

# Function: Check if Docker is running
check_docker() {
    echo -n "Checking Docker... "
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}✗${NC}"
        echo ""
        echo -e "${RED}Error: Docker is not running${NC}"
        echo "Please start Docker Desktop and try again."
        echo ""
        exit 1
    fi
    echo -e "${GREEN}${CHECK}${NC}"
}

# Function: Check if image exists
check_image() {
    if [ "$REBUILD" = true ]; then
        return 1  # Force rebuild
    fi

    echo -n "Checking for existing image... "
    if docker images | grep -q "speech_generator-voice-generator"; then
        echo -e "${GREEN}${CHECK}${NC}"
        return 0
    else
        echo "not found"
        return 1
    fi
}

# Function: Build image
build_image() {
    echo ""
    echo -e "${YELLOW}Building Docker image (this may take a few minutes)...${NC}"
    echo ""
    docker compose build
    echo ""
    echo -e "${GREEN}${CHECK} Build complete${NC}"
}

# Function: Open browser
open_browser() {
    if [ "$NO_BROWSER" = false ]; then
        # Wait a moment for server to be ready
        sleep 3
        # Check if 'open' command exists (macOS)
        if command -v open > /dev/null 2>&1; then
            open "http://localhost:5002" > /dev/null 2>&1 &
        fi
    fi
}

# Function: Start server
start_server() {
    echo ""
    echo -e "${YELLOW}Starting Voice Generator web server...${NC}"
    echo ""
    echo -e "${GREEN}${ROCKET} Server starting!${NC}"
    echo ""
    echo -e "${GREEN}${LINK} Open in browser:${NC} ${BLUE}http://localhost:5002${NC}"
    echo ""
    echo "Press ${YELLOW}Ctrl+C${NC} to stop the server"
    echo ""
    echo "========================================"
    echo ""

    # Open browser in background
    open_browser

    # Start the server (this blocks until Ctrl+C)
    docker compose run --rm voice-generator python web_server.py
}

# Trap Ctrl+C for clean shutdown
trap 'echo ""; echo "Shutting down..."; docker compose down > /dev/null 2>&1; echo "Done."; exit 0' INT

# Main execution
check_docker

if ! check_image; then
    build_image
fi

start_server
