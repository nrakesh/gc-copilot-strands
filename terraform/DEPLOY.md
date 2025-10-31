# Terraform Deployment Guide - GC2 Copilot Strands

Complete infrastructure and agent deployment using Terraform.

## Prerequisites

- AWS CLI configured with credentials
- Terraform >= 1.0
- Docker with buildx support
- Python 3.12+

## Quick Start

```bash
# 1. Initialize Terraform
cd terraform
terraform init

# 2. Create terraform.tfvars
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your settings

# 3. Deploy everything
terraform apply

# 4. Store your Anthropic API key
SECRET_ARN=$(terraform output -raw anthropic_secret_arn)
aws secretsmanager put-secret-value \
  --secret-id $SECRET_ARN \
  --secret-string "your-anthropic-api-key-here"

# 5. Test your agent
AGENT_ARN=$(terraform output -raw agentcore_agent_runtime_arn)
aws bedrock-agentcore invoke-agent-runtime \
  --agent-runtime-arn $AGENT_ARN \
  --runtime-session-id "test-$(date +%s)" \
  --payload '{"prompt":"Hello! Introduce yourself."}' \
  --qualifier DEFAULT \
  --region us-east-1 \
  /dev/stdout
```

## What Terraform Deploys

### Infrastructure (main.tf)
- ✅ **ECR Repository** - Stores your Docker container image
- ✅ **IAM Role** - Permissions for AgentCore runtime
- ✅ **CloudWatch Log Group** - Agent execution logs
- ✅ **Secrets Manager** - Secure storage for API keys

### Agent Runtime (agentcore.tf)
- ✅ **Docker Build** - Builds ARM64 container via `null_resource`
- ✅ **ECR Push** - Pushes image to ECR repository
- ✅ **AgentCore Runtime** - Deploys agent using `aws_bedrockagentcore_agent_runtime`

## Terraform Outputs

After `terraform apply`, you'll get:

```bash
# Infrastructure
ecr_repository_url              # Where your Docker image is stored
agentcore_runtime_role_arn      # IAM role for the agent
cloudwatch_log_group_name       # Where logs are written
anthropic_secret_arn            # Where to store API key

# Agent Runtime
agentcore_agent_runtime_arn     # ARN to invoke your agent
agentcore_agent_runtime_name    # Human-readable name
agentcore_invoke_example        # Example invocation commands
```

## Update Agent Code

When you modify agent code:

```bash
# Terraform detects changes automatically via file hashes
cd terraform
terraform apply

# This will:
# 1. Rebuild Docker image
# 2. Push to ECR
# 3. Update AgentCore runtime
```

## Configuration Variables

Edit `terraform.tfvars`:

```hcl
aws_region   = "us-east-1"     # AWS region
environment  = "dev"           # dev, staging, or prod
project_name = "gc2-copilot-strands"
```

## Architecture

```
┌──────────────────────────────────────────────────┐
│ terraform apply                                  │
└──────────────────────────────────────────────────┘
           │
           ├─► main.tf
           │   ├── ECR Repository
           │   ├── IAM Role
           │   ├── CloudWatch Logs
           │   └── Secrets Manager
           │
           └─► agentcore.tf
               ├── null_resource (Docker build/push)
               └── aws_bedrockagentcore_agent_runtime
                   └─► Deployed to AgentCore
```

## View Logs

```bash
LOG_GROUP=$(terraform output -raw cloudwatch_log_group_name)
aws logs tail $LOG_GROUP --follow
```

## Invoke Agent (Python)

```python
import boto3
import json

# Get ARN from Terraform output
# AGENT_ARN = "arn:aws:bedrock-agentcore:..."

client = boto3.client('bedrock-agentcore', region_name='us-east-1')

response = client.invoke_agent_runtime(
    agentRuntimeArn=AGENT_ARN,
    runtimeSessionId='my-session-123',
    payload=json.dumps({
        "prompt": "Plan a pipeline to move CSV files from S3 to another S3 bucket"
    }),
    qualifier='DEFAULT'
)

# Parse response
result = json.loads(response['payload'].read())
print(result)
```

## Troubleshooting

### Docker build fails

```bash
# Ensure buildx is set up
docker buildx create --use --name gc2-builder
docker buildx ls
```

### AgentCore deployment fails

```bash
# Check AWS provider version (must support bedrockagentcore resources)
terraform version

# Check IAM permissions
aws sts get-caller-identity
```

### Agent returns authentication errors

```bash
# Verify API key is stored
SECRET_ARN=$(terraform output -raw anthropic_secret_arn)
aws secretsmanager get-secret-value --secret-id $SECRET_ARN

# Update if needed
aws secretsmanager put-secret-value \
  --secret-id $SECRET_ARN \
  --secret-string "sk-ant-your-key"
```

### Check agent status

```bash
AGENT_NAME=$(terraform output -raw agentcore_agent_runtime_name)
aws bedrock-agentcore-control describe-agent-runtime \
  --agent-runtime-name $AGENT_NAME \
  --region us-east-1
```

## Cleanup

```bash
# Destroy everything
cd terraform
terraform destroy

# Manual cleanup if needed
aws ecr delete-repository \
  --repository-name gc2-copilot-strands-planner \
  --force \
  --region us-east-1
```

## Cost Estimate

- **AgentCore Runtime**: ~$0.05-0.15 per invocation (varies by execution time)
- **ECR Storage**: ~$0.10/GB/month
- **CloudWatch Logs**: ~$0.50/GB ingested
- **Secrets Manager**: $0.40/month per secret

**Free Tier**: AgentCore is free to try until September 16, 2025

## Next Steps

1. **Add Tools**: Create Strands tools in `src/gc2_copilot_strands/tools/`
2. **Add Models**: Define Pydantic models in `src/gc2_copilot_strands/models/`
3. **Customize Agent**: Modify `agent_deploy.py` with your logic
4. **CI/CD**: Integrate Terraform into your deployment pipeline

## References

- [Terraform Resource Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/bedrockagentcore_agent_runtime)
- [AgentCore Documentation](https://strandsagents.com/latest/documentation/docs/user-guide/deploy/deploy_to_bedrock_agentcore/)
- [AWS AgentCore API Reference](https://docs.aws.amazon.com/bedrock-agentcore-control/latest/APIReference/Welcome.html)
