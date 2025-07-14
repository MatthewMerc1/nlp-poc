#!/bin/bash

# Stop OpenSearch Local Access Script
# This script stops the SSH port forwarding for OpenSearch

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping OpenSearch local access...${NC}"

# Kill any existing port forwarding
pkill -f "ssh.*8443.*opensearch" || true

echo -e "${GREEN}✅ OpenSearch local access stopped!${NC}"
echo -e "${YELLOW}Port forwarding on localhost:8443 has been terminated.${NC}" 