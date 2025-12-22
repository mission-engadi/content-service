#!/bin/bash

# Content Service Status Script
# This script checks the status of the Content Service and its dependencies

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
PID_FILE=".content_service.pid"
LOG_FILE="content_service.log"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  ${SERVICE_NAME} Status${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check service process
echo -e "${BLUE}🔍 Service Process:${NC}"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ Running (PID: $PID)${NC}"
        
        # Get process info
        MEM=$(ps -p "$PID" -o %mem --no-headers | xargs)
        CPU=$(ps -p "$PID" -o %cpu --no-headers | xargs)
        UPTIME=$(ps -p "$PID" -o etime --no-headers | xargs)
        
        echo -e "  ${BLUE}  Memory: ${MEM}%${NC}"
        echo -e "  ${BLUE}  CPU: ${CPU}%${NC}"
        echo -e "  ${BLUE}  Uptime: ${UPTIME}${NC}"
    else
        echo -e "  ${RED}✗ Not running (stale PID file)${NC}"
    fi
else
    echo -e "  ${RED}✗ Not running (no PID file)${NC}"
fi
echo ""

# Check HTTP endpoint
echo -e "${BLUE}🌐 HTTP Endpoint:${NC}"
if curl -s -o /dev/null -w "%{http_code}" "http://localhost:${SERVICE_PORT}/api/v1/health" | grep -q "200"; then
    echo -e "  ${GREEN}✓ Responding on port ${SERVICE_PORT}${NC}"
    
    # Get health status
    HEALTH=$(curl -s "http://localhost:${SERVICE_PORT}/api/v1/health" 2>/dev/null)
    if [ -n "$HEALTH" ]; then
        echo -e "  ${GREEN}✓ Health check passed${NC}"
    fi
else
    echo -e "  ${RED}✗ Not responding on port ${SERVICE_PORT}${NC}"
fi
echo ""

# Check PostgreSQL
echo -e "${BLUE}🗄️  PostgreSQL:${NC}"
if systemctl is-active --quiet postgresql; then
    echo -e "  ${GREEN}✓ Running${NC}"
    
    # Check database connection
    if sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='content_db'" 2>/dev/null | grep -q "1"; then
        echo -e "  ${GREEN}✓ Database 'content_db' exists${NC}"
    else
        echo -e "  ${YELLOW}⚠ Database 'content_db' not found${NC}"
    fi
else
    echo -e "  ${RED}✗ Not running${NC}"
fi
echo ""

# Check Redis
echo -e "${BLUE}💾 Redis:${NC}"
if systemctl is-active --quiet redis-server || systemctl is-active --quiet redis; then
    echo -e "  ${GREEN}✓ Running${NC}"
    
    # Check Redis connection
    if redis-cli ping 2>/dev/null | grep -q "PONG"; then
        echo -e "  ${GREEN}✓ Responding to ping${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ Not running (optional)${NC}"
fi
echo ""

# Check virtual environment
echo -e "${BLUE}🐍 Virtual Environment:${NC}"
if [ -d "venv" ]; then
    echo -e "  ${GREEN}✓ Exists${NC}"
else
    echo -e "  ${RED}✗ Not found${NC}"
fi
echo ""

# Check log file
echo -e "${BLUE}📝 Log File:${NC}"
if [ -f "$LOG_FILE" ]; then
    SIZE=$(du -h "$LOG_FILE" | cut -f1)
    LINES=$(wc -l < "$LOG_FILE")
    echo -e "  ${GREEN}✓ ${LOG_FILE} (${SIZE}, ${LINES} lines)${NC}"
    
    # Show last few log entries
    echo -e "  ${BLUE}Recent logs:${NC}"
    tail -n 5 "$LOG_FILE" | sed 's/^/    /'
else
    echo -e "  ${YELLOW}⚠ Log file not found${NC}"
fi
echo ""

# Service URLs
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}📋 Service URLs${NC}"
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
