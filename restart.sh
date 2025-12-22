#!/bin/bash

# Content Service Restart Script
# This script restarts the Content Service

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service configuration
SERVICE_NAME="Content Service"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Restarting ${SERVICE_NAME}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Stop the service
echo -e "${BLUE}📍 Step 1: Stopping service...${NC}"
./stop.sh
echo ""

# Wait a moment
echo -e "${BLUE}⏳ Waiting 2 seconds...${NC}"
sleep 2
echo ""

# Start the service
echo -e "${BLUE}📍 Step 2: Starting service...${NC}"
./start.sh
