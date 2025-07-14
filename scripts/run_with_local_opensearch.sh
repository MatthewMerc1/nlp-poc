#!/bin/bash

# Wrapper script to run commands with local OpenSearch access
# Usage: ./scripts/run_with_local_opensearch.sh <your-command>

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [ $# -eq 0 ]; then
    echo -e "${YELLOW}Usage: $0 <command>${NC}"
    echo -e "${YELLOW}Example: $0 'python src/scripts/load_enhanced_summaries_direct.py --bucket my-bucket --opensearch-endpoint localhost:8443'${NC}"
    exit 1
fi

echo -e "${GREEN}Setting up local OpenSearch access...${NC}"

# Source the local access script to set up port forwarding
source ./scripts/opensearch_local_access.sh

echo -e "${GREEN}Running command with local OpenSearch access...${NC}"
echo -e "${YELLOW}Command: $@${NC}"
echo ""

# Run the command with the local OpenSearch endpoint
OPENSEARCH_ENDPOINT="localhost:8443" "$@"

echo ""
echo -e "${GREEN}Command completed. Port forwarding is still active.${NC}"
echo -e "${YELLOW}To stop port forwarding, run: kill $SSH_PID${NC}" 