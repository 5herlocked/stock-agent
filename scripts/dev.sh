#!/bin/bash

# Stock Agent Development Script
# Convenient wrapper for starting the development server

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory (go up one level from scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}🚀 Stock Agent Development Server${NC}"
echo -e "${BLUE}=================================${NC}"

# Check if Python 3.12+ is available
check_python() {
    if command -v python3.12 &> /dev/null; then
        PYTHON_CMD="python3.12"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}❌ Error: Python not found${NC}"
        exit 1
    fi

    # Check Python version
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ $(echo "$PYTHON_VERSION >= 3.12" | bc -l) -eq 0 ]]; then
        echo -e "${YELLOW}⚠️  Warning: Python $PYTHON_VERSION detected. Python 3.12+ recommended.${NC}"
    fi

    echo -e "${GREEN}✅ Using Python: $PYTHON_CMD ($PYTHON_VERSION)${NC}"
}

# Check for and activate virtual environment
setup_venv() {
    if [[ -d ".venv" ]]; then
        echo -e "${GREEN}📁 Found virtual environment${NC}"

        # Activate virtual environment
        if [[ -f ".venv/bin/activate" ]]; then
            source .venv/bin/activate
            echo -e "${GREEN}✅ Virtual environment activated${NC}"
        elif [[ -f ".venv/Scripts/activate" ]]; then
            source .venv/Scripts/activate
            echo -e "${GREEN}✅ Virtual environment activated (Windows)${NC}"
        else
            echo -e "${YELLOW}⚠️  Virtual environment found but activation script missing${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  No virtual environment found (.venv)${NC}"
        echo -e "${YELLOW}   Consider running: python -m venv .venv${NC}"
    fi
}

# Check for environment file
check_env() {
    if [[ -f ".dev.env" ]]; then
        echo -e "${GREEN}✅ Development environment file found (.dev.env)${NC}"
    else
        echo -e "${RED}❌ Warning: .dev.env file not found${NC}"
        echo -e "${YELLOW}   Create .dev.env with required environment variables${NC}"
    fi
}

# Install dependencies if needed
check_dependencies() {
    if command -v uv &> /dev/null; then
        echo -e "${GREEN}📦 Using UV package manager${NC}"
        if [[ ! -f "uv.lock" ]] || [[ "pyproject.toml" -nt "uv.lock" ]]; then
            echo -e "${YELLOW}🔄 Syncing dependencies with UV...${NC}"
            uv sync
        fi
    else
        echo -e "${YELLOW}📦 UV not found, checking pip installation...${NC}"
        if ! $PYTHON_CMD -c "import robyn" &> /dev/null; then
            echo -e "${YELLOW}🔄 Installing dependencies with pip...${NC}"
            pip install -e .
        fi
    fi
    echo -e "${GREEN}✅ Dependencies ready${NC}"
}

# Kill any existing server on port 8080
kill_existing_server() {
    local port=${1:-8080}
    if command -v lsof &> /dev/null; then
        local pids=$(lsof -ti:$port 2>/dev/null || true)
        if [[ -n "$pids" ]]; then
            echo -e "${YELLOW}🔄 Killing existing server on port $port...${NC}"
            echo "$pids" | xargs kill -9 2>/dev/null || true
            sleep 1
        fi
    fi
}

# Start the development server
start_server() {
    echo -e "${BLUE}🔥 Starting development server...${NC}"
    echo ""

    # Kill any existing server
    kill_existing_server 8080

    # Start the development server
    exec $PYTHON_CMD -m robyn scripts/dev_server.py --dev"$@"
}

# Show help
show_help() {
    echo -e "${BLUE}Usage: ./dev.sh [options]${NC}"
    echo ""
    echo "Options:"
    echo "  --help, -h     Show this help message"
    echo "  --port PORT    Use custom port (default: 8080)"
    echo "  --host HOST    Use custom host (default: 127.0.0.1)"
    echo "  --summary      Generate market summary on startup"
    echo "  --no-summary   Skip market summary generation"
    echo ""
    echo "Environment variables (set in .dev.env):"
    echo "  DEV_HOST       Development host (default: 127.0.0.1)"
    echo "  DEV_PORT       Development port (default: 8080)"
    echo "  DEV_GENERATE_SUMMARY  Generate market summary (default: false)"
    echo ""
    echo "Examples:"
    echo "  ./dev.sh                    # Start with default settings"
    echo "  ./dev.sh --port 3000        # Start on port 3000"
    echo "  ./dev.sh --summary          # Start with market summary"
}

# Handle cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}👋 Shutting down development server...${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --port)
            export DEV_PORT="$2"
            shift 2
            ;;
        --host)
            export DEV_HOST="$2"
            shift 2
            ;;
        --summary)
            export DEV_GENERATE_SUMMARY="true"
            shift
            ;;
        --no-summary)
            export DEV_GENERATE_SUMMARY="false"
            shift
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
main() {
    check_python
    setup_venv
    check_env
    check_dependencies
    start_server
}

# Run main function
main "$@"
