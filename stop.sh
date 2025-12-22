#!/bin/bash

# Content Service Stop Script
# This script stops the Content Service

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service configuration
SERVICE_NAME="Content Service"
PID_FILE=".content_service.pid"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Stopping ${SERVICE_NAME}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠ Service is not running (no PID file found)${NC}"
    exit 0
fi

# Read PID
PID=$(cat "$PID_FILE")

# Check if process is running
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Service is not running (process not found)${NC}"
    echo -e "${YELLOW}  Removing stale PID file${NC}"
    rm -f "$PID_FILE"
    exit 0
fi

# Stop the service
echo -e "${BLUE}🛑 Stopping ${SERVICE_NAME} (PID: $PID)...${NC}"
kill "$PID"

# Wait for process to stop
for i in {1..10}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ ${SERVICE_NAME} stopped successfully${NC}"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# Force kill if still running
if ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Process did not stop gracefully, forcing...${NC}"
    kill -9 "$PID"
    sleep 1
    
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ ${SERVICE_NAME} stopped (forced)${NC}"
        rm -f "$PID_FILE"
        exit 0
    else
        echo -e "${RED}✗ Failed to stop ${SERVICE_NAME}${NC}"
        exit 1
    fi
fi
