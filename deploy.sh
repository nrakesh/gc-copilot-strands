#!/bin/bash
set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGION="${AWS_REGION:-us-east-1}"
AGENT_NAME="gc2-copilot-strands-planner"
TERRAFORM_DIR="terraform"

echo "=========================================="
echo "GC2 Copilot Strands - AgentCore Deployment"
echo "=========================================="
echo ""

# Step 1: Get Terraform outputs
echo -e "${BLUE}📋 Step 1: Getting Terraform outputs...${NC}"
cd $TERRAFORM_DIR

ECR_URL=$(terraform output -raw ecr_repository_url 2>/dev/null)
ROLE_ARN=$(terraform output -raw agentcore_runtime_role_arn 2>/dev/null)
LOG_GROUP=$(terraform output -raw cloudwatch_log_group_name 2>/dev/null)

if [ -z "$ECR_URL" ] || [ -z "$ROLE_ARN" ]; then
    echo -e "${RED}❌ Failed to get Terraform outputs${NC}"
    echo "   Make sure you've run 'terraform apply' first"
    exit 1
fi

echo -e "${GREEN}✓${NC} ECR Repository: $ECR_URL"
echo -e "${GREEN}✓${NC} IAM Role: $ROLE_ARN"
echo -e "${GREEN}✓${NC} Log Group: $LOG_GROUP"
cd ..

# Step 2: Build Docker image
echo ""
echo -e "${BLUE}🐳 Step 2: Building Docker image (ARM64)...${NC}"

# Check if buildx is available
if ! docker buildx version &> /dev/null; then
    echo -e "${YELLOW}⚠️  Setting up docker buildx...${NC}"
    docker buildx create --use
fi

docker buildx build \
    --platform linux/arm64 \
    -t $ECR_URL:latest \
    -t $ECR_URL:$(date +%Y%m%d-%H%M%S) \
    --load \
    .

echo -e "${GREEN}✓${NC} Docker image built successfully"

# Step 3: Push to ECR
echo ""
echo -e "${BLUE}📤 Step 3: Pushing image to ECR...${NC}"

# Login to ECR
aws ecr get-login-password --region $REGION | \
    docker login --username AWS --password-stdin $ECR_URL

# Push image
docker buildx build \
    --platform linux/arm64 \
    -t $ECR_URL:latest \
    --push \
    .

echo -e "${GREEN}✓${NC} Image pushed to ECR"

# Step 4: Deploy to AgentCore
echo ""
echo -e "${BLUE}🚀 Step 4: Deploying to AgentCore...${NC}"

# Create agent runtime
DEPLOY_OUTPUT=$(aws bedrock-agentcore-control create-agent-runtime \
    --agent-runtime-name $AGENT_NAME \
    --agent-runtime-artifact "{
        \"containerConfiguration\": {
            \"containerUri\": \"$ECR_URL:latest\"
        }
    }" \
    --network-configuration "{
        \"networkMode\": \"PUBLIC\"
    }" \
    --role-arn $ROLE_ARN \
    --region $REGION \
    2>&1) || true

# Check if deployment succeeded or already exists
if echo "$DEPLOY_OUTPUT" | grep -q "ConflictException"; then
    echo -e "${YELLOW}⚠️  Agent runtime already exists${NC}"
    echo "   To redeploy, first delete the existing runtime:"
    echo "   aws bedrock-agentcore-control delete-agent-runtime --agent-runtime-name $AGENT_NAME --region $REGION"
    exit 1
elif echo "$DEPLOY_OUTPUT" | grep -q "agentRuntimeArn"; then
    AGENT_ARN=$(echo "$DEPLOY_OUTPUT" | grep -o 'arn:aws:bedrock-agentcore:[^"]*')
    echo -e "${GREEN}✓${NC} Agent deployed successfully!"
    echo "   ARN: $AGENT_ARN"
else
    echo -e "${RED}❌ Deployment failed${NC}"
    echo "$DEPLOY_OUTPUT"
    exit 1
fi

# Step 5: Test invocation
echo ""
echo -e "${BLUE}🧪 Step 5: Testing agent invocation...${NC}"

TEST_PAYLOAD='{"prompt":"Say hello and introduce yourself briefly."}'

TEST_OUTPUT=$(aws bedrock-agentcore invoke-agent-runtime \
    --agent-runtime-arn $AGENT_ARN \
    --runtime-session-id "test-$(date +%s)" \
    --payload "$TEST_PAYLOAD" \
    --qualifier DEFAULT \
    --region $REGION \
    /dev/stdout 2>&1) || true

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Test invocation successful!"
    echo "   Response: $TEST_OUTPUT"
else
    echo -e "${YELLOW}⚠️  Test invocation failed (agent may still be initializing)${NC}"
fi

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "Agent ARN: $AGENT_ARN"
echo ""
echo "To invoke your agent:"
echo "  aws bedrock-agentcore invoke-agent-runtime \\"
echo "    --agent-runtime-arn $AGENT_ARN \\"
echo "    --runtime-session-id my-session \\"
echo "    --payload '{\"prompt\":\"Your message\"}' \\"
echo "    --qualifier DEFAULT \\"
echo "    --region $REGION \\"
echo "    /dev/stdout"
echo ""
echo "To view logs:"
echo "  aws logs tail $LOG_GROUP --follow"
echo ""
