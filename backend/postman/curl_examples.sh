#!/bin/bash

# Knowledge Source Management API - cURL Examples
# 
# This script provides cURL examples for testing the Knowledge Source Management API
# Make sure to replace the variables with actual values from your environment

# Configuration
BASE_URL="http://localhost:8000"
USERNAME="admin"
PASSWORD="admin123"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Knowledge Source Management API - cURL Examples${NC}"
echo "=================================================="

# Step 1: Login and get access token
echo -e "\n${YELLOW}1. Login and get access token${NC}"
echo "curl -X POST \"$BASE_URL/api/v1/auth/login\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\"}'"
echo ""

# Execute login and extract token
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\"}")

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | grep -o '[^"]*$')

if [ -z "$ACCESS_TOKEN" ]; then
    echo -e "${RED}❌ Failed to get access token. Please check your credentials and server status.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Access token obtained: ${ACCESS_TOKEN:0:20}...${NC}"

# Step 2: Create MuleSoft knowledge source configuration
echo -e "\n${YELLOW}2. Create MuleSoft knowledge source configuration${NC}"
echo "curl -X POST \"$BASE_URL/api/v1/knowledge-sources/\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -H \"Authorization: Bearer \$ACCESS_TOKEN\" \\"
echo "  -d '{...}'"
echo ""

MULESOFT_CONFIG=$(curl -s -X POST "$BASE_URL/api/v1/knowledge-sources/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "name": "MuleSoft",
    "description": "MuleSoft documentation provides comprehensive information about API development, integration, and DataWeave transformations.",
    "url": "https://docs.mulesoft.com",
    "enabled": false,
    "scraping_mode": "crawl",
    "allowed_subdomains": ["docs.mulesoft.com"],
    "blocked_subdomains": ["old.docs.mulesoft.com", "archive.docs.mulesoft.com"],
    "crawl_depth": 6,
    "css_selector": "main > article",
    "content_filter_threshold": 0.6,
    "allowed_nodes": ["Platform", "Product", "Component"],
    "allowed_relationships": ["HAS_CHUNK", "RELATED_TO", "USES"]
  }')

CONFIG_ID=$(echo $MULESOFT_CONFIG | grep -o '"id":"[^"]*' | grep -o '[^"]*$')

if [ -z "$CONFIG_ID" ]; then
    echo -e "${RED}❌ Failed to create configuration${NC}"
    echo "Response: $MULESOFT_CONFIG"
else
    echo -e "${GREEN}✅ Configuration created with ID: $CONFIG_ID${NC}"
fi

# Step 3: List all knowledge source configurations
echo -e "\n${YELLOW}3. List all knowledge source configurations${NC}"
echo "curl -X GET \"$BASE_URL/api/v1/knowledge-sources/\" \\"
echo "  -H \"Authorization: Bearer \$ACCESS_TOKEN\""
echo ""

curl -s -X GET "$BASE_URL/api/v1/knowledge-sources/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.[] | {id: .id, name: .name, enabled: .enabled}'

# Step 4: Create a knowledge processing job
if [ ! -z "$CONFIG_ID" ]; then
    echo -e "\n${YELLOW}4. Create knowledge processing job${NC}"
    echo "curl -X POST \"$BASE_URL/api/v1/knowledge-sources/$CONFIG_ID/jobs\" \\"
    echo "  -H \"Content-Type: application/json\" \\"
    echo "  -H \"Authorization: Bearer \$ACCESS_TOKEN\" \\"
    echo "  -d '{\"name\": \"MuleSoft Processing Job\", \"description\": \"Process MuleSoft documentation\"}'"
    echo ""

    JOB_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/knowledge-sources/$CONFIG_ID/jobs" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -d '{
        "name": "MuleSoft Processing Job",
        "description": "Process MuleSoft documentation"
      }')

    JOB_ID=$(echo $JOB_RESPONSE | grep -o '"id":"[^"]*' | grep -o '[^"]*$')

    if [ -z "$JOB_ID" ]; then
        echo -e "${RED}❌ Failed to create job${NC}"
        echo "Response: $JOB_RESPONSE"
    else
        echo -e "${GREEN}✅ Job created with ID: $JOB_ID${NC}"
    fi

    # Step 5: Get job details
    if [ ! -z "$JOB_ID" ]; then
        echo -e "\n${YELLOW}5. Get job details${NC}"
        echo "curl -X GET \"$BASE_URL/api/v1/knowledge-sources/jobs/$JOB_ID\" \\"
        echo "  -H \"Authorization: Bearer \$ACCESS_TOKEN\""
        echo ""

        curl -s -X GET "$BASE_URL/api/v1/knowledge-sources/jobs/$JOB_ID" \
          -H "Authorization: Bearer $ACCESS_TOKEN" | jq '{id: .id, name: .name, status: .status, created_at: .created_at}'
    fi
fi

echo -e "\n${GREEN}✅ cURL examples completed!${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Use the Postman collection for more comprehensive testing"
echo "2. Check the API documentation at $BASE_URL/docs"
echo "3. Monitor job status and results through the API"
