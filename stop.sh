#!/bin/bash
#
# Voice Generator Stop Script
# Cleanly shuts down running containers
#

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${YELLOW}Stopping Voice Generator...${NC}"
echo ""

# Stop and remove containers
docker compose down

echo ""
echo -e "${GREEN}✓ Voice Generator stopped${NC}"
echo ""
