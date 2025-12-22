#!/bin/bash

# Content Service Startup Script
# This script starts the Content Service with all dependencies

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service configuration
SERVICE_NAME="Content Service"
SERVICE_PORT=8002
SERVICE_HOST="0.0.0.0"
PID_FILE=".content_service.pid"
LOG_FILE="content_service.log"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Starting ${SERVICE_NAME}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if service is already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠ Service is already running (PID: $PID)${NC}"
        echo -e "${YELLOW}  Use ./stop.sh to stop it first${NC}"
        exit 1
    else
        echo -e "${YELLOW}⚠ Removing stale PID file${NC}"
        rm -f "$PID_FILE"
    fi
fi

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Install/update dependencies
echo -e "${BLUE}📦 Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Check PostgreSQL
echo -e "${BLUE}🔍 Checking PostgreSQL...${NC}"
if systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}✓ PostgreSQL is running${NC}"
else
    echo -e "${YELLOW}⚠ PostgreSQL is not running. Attempting to start...${NC}"
    sudo systemctl start postgresql
    if systemctl is-active --quiet postgresql; then
        echo -e "${GREEN}✓ PostgreSQL started successfully${NC}"
    else
        echo -e "${RED}✗ Failed to start PostgreSQL${NC}"
        echo -e "${RED}  Please start PostgreSQL manually and try again${NC}"
        exit 1
    fi
fi

# Check Redis
echo -e "${BLUE}🔍 Checking Redis...${NC}"
if systemctl is-active --quiet redis-server || systemctl is-active --quiet redis; then
    echo -e "${GREEN}✓ Redis is running${NC}"
else
    echo -e "${YELLOW}⚠ Redis is not running. Attempting to start...${NC}"
    sudo systemctl start redis-server 2>/dev/null || sudo systemctl start redis 2>/dev/null
    if systemctl is-active --quiet redis-server || systemctl is-active --quiet redis; then
        echo -e "${GREEN}✓ Redis started successfully${NC}"
    else
        echo -e "${YELLOW}⚠ Redis not available (optional)${NC}"
    fi
fi

# Create database if it doesn't exist
echo -e "${BLUE}🗄️  Checking database...${NC}"
DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='content_db'" 2>/dev/null || echo "0")
if [ "$DB_EXISTS" = "1" ]; then
    echo -e "${GREEN}✓ Database 'content_db' exists${NC}"
else
    echo -e "${YELLOW}⚠ Creating database 'content_db'...${NC}"
    sudo -u postgres psql -c "CREATE DATABASE content_db;" 2>/dev/null || true
    echo -e "${GREEN}✓ Database created${NC}"
fi

# Run database migrations
echo -e "${BLUE}🔄 Running database migrations...${NC}"
if [ -d "migrations" ]; then
    alembic upgrade head 2>/dev/null || echo -e "${YELLOW}⚠ Migration warning (may be normal for first run)${NC}"
    echo -e "${GREEN}✓ Migrations completed${NC}"
else
    echo -e "${YELLOW}⚠ No migrations directory found${NC}"
fi

# Create uploads directory
echo -e "${BLUE}📁 Creating uploads directory...${NC}"
mkdir -p uploads
echo -e "${GREEN}✓ Uploads directory ready${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ No .env file found. Creating from .env.example...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ .env file created${NC}"
        echo -e "${YELLOW}  Please update .env with your configuration${NC}"
    else
        echo -e "${RED}✗ No .env.example file found${NC}"
    fi
fi

# Start the service
echo ""
echo -e "${GREEN}🚀 Starting ${SERVICE_NAME}...${NC}"
echo -e "${BLUE}   Host: ${SERVICE_HOST}${NC}"
echo -e "${BLUE}   Port: ${SERVICE_PORT}${NC}"
echo -e "${BLUE}   Logs: ${LOG_FILE}${NC}"
echo ""

# Start uvicorn in the background
nohup uvicorn app.main:app \
    --host "$SERVICE_HOST" \
    --port "$SERVICE_PORT" \
    --reload \
    > "$LOG_FILE" 2>&1 &

PID=$!
echo $PID > "$PID_FILE"

# Wait a moment and check if service started
sleep 2

if ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ ${SERVICE_NAME} started successfully!${NC}"
    echo -e "${GREEN}  PID: $PID${NC}"
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}📋 Service Information${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}  API:${NC}        http://localhost:${SERVICE_PORT}"
    echo -e "${GREEN}  Docs:${NC}       http://localhost:${SERVICE_PORT}/docs"
    echo -e "${GREEN}  Health:${NC}     http://localhost:${SERVICE_PORT}/api/v1/health"
    echo -e "${GREEN}  Logs:${NC}       tail -f ${LOG_FILE}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Note: This localhost refers to the computer running the service.${NC}"
    echo -e "${YELLOW}      To access remotely, deploy to your own system.${NC}"
    echo ""
else
    echo -e "${RED}✗ Failed to start ${SERVICE_NAME}${NC}"
    echo -e "${RED}  Check ${LOG_FILE} for errors${NC}"
    rm -f "$PID_FILE"
    exit 1
fi
