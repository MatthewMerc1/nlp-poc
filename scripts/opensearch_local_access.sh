#!/bin/bash

# OpenSearch Local Access Script
# This script sets up SSH port forwarding to access OpenSearch from your local machine

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up local OpenSearch access...${NC}"

# Get the bastion host IP from Terraform
cd infrastructure/terraform/environments/dev
BASTION_IP=$(terraform output -raw bastion_public_ip 2>/dev/null || echo "")
OPENSEARCH_ENDPOINT=$(terraform output -raw opensearch_endpoint 2>/dev/null || echo "")

if [ -z "$BASTION_IP" ]; then
    echo -e "${RED}Error: Could not get bastion IP from Terraform. Make sure you're in the dev environment directory.${NC}"
    exit 1
fi

if [ -z "$OPENSEARCH_ENDPOINT" ]; then
    echo -e "${RED}Error: Could not get OpenSearch endpoint from Terraform.${NC}"
    exit 1
fi

echo -e "${GREEN}Bastion IP: ${BASTION_IP}${NC}"
echo -e "${GREEN}OpenSearch Endpoint: ${OPENSEARCH_ENDPOINT}${NC}"

# Check if SSH key exists
SSH_KEY="$HOME/.ssh/nlp-poc-bastion"
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}Error: SSH key not found at $SSH_KEY${NC}"
    exit 1
fi

# Kill any existing port forwarding
echo -e "${YELLOW}Stopping any existing port forwarding...${NC}"
pkill -f "ssh.*8443.*opensearch" || true

# Start port forwarding
echo -e "${GREEN}Starting SSH port forwarding...${NC}"
ssh -i "$SSH_KEY" -L 8443:${OPENSEARCH_ENDPOINT}:443 -N ec2-user@${BASTION_IP} &
SSH_PID=$!

# Wait a moment for the connection to establish
sleep 3

# Test the connection
echo -e "${YELLOW}Testing OpenSearch connection...${NC}"
if curl -k -s -o /dev/null -w "%{http_code}" https://localhost:8443/_dashboards/ | grep -q "302\|200"; then
    echo -e "${GREEN}✅ OpenSearch is accessible via localhost:8443${NC}"
else
    echo -e "${RED}❌ Failed to connect to OpenSearch${NC}"
    kill $SSH_PID 2>/dev/null || true
    exit 1
fi

# Set environment variables for local development
export OPENSEARCH_ENDPOINT="localhost:8443"
export OPENSEARCH_ENDPOINT_HTTPS="https://localhost:8443"

echo -e "${GREEN}✅ OpenSearch local access configured!${NC}"
echo -e "${YELLOW}Dashboard URL: https://localhost:8443/_dashboards/${NC}"
echo -e "${YELLOW}Local Endpoint: localhost:8443${NC}"
echo -e "${YELLOW}SSH Process ID: $SSH_PID${NC}"
echo ""
echo -e "${GREEN}Environment variables set:${NC}"
echo -e "  OPENSEARCH_ENDPOINT=$OPENSEARCH_ENDPOINT"
echo -e "  OPENSEARCH_ENDPOINT_HTTPS=$OPENSEARCH_ENDPOINT_HTTPS"
echo ""
echo -e "${YELLOW}To stop port forwarding, run: kill $SSH_PID${NC}"
echo -e "${YELLOW}To run your scripts with local access, use:${NC}"
echo -e "  OPENSEARCH_ENDPOINT=localhost:8443 your-script.sh" 