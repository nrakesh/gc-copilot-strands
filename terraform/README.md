# Terraform Deployment Guide for GC2 Copilot Strands

This guide shows how to use Terraform to provision AWS infrastructure and deploy your Strands agent to Amazon Bedrock AgentCore.

## Overview

Since Terraform doesn't yet support AgentCore resources directly, we use a **hybrid approach**:

1. **Terraform** provisions supporting infrastructure (ECR, IAM, CloudWatch, Secrets)
2. **Python script** deploys the agent runtime to AgentCore using boto3
3. **Docker** containerizes the agent for deployment

## Prerequisites

- AWS CLI configured with credentials
- Terraform >= 1.0
- Docker or Finch (for ARM64 builds)
- Python 3.12+ with boto3

## Step 1: Provision Infrastructure with Terraform

```bash
cd terraform

# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply infrastructure
terraform apply
```

**What Terraform Creates:**
- ✅ ECR repository for container images
- ✅ IAM role for AgentCore runtime
- ✅ CloudWatch log group
- ✅ Secrets Manager secret for API key

**Outputs:**
- `ecr_repository_url` - Where to push your Docker image
- `agentcore_runtime_role_arn` - IAM role for the agent
- `cloudwatch_log_group_name` - For logs
- `anthropic_secret_arn` - Store your Anthropic API key here

## Step 2: Store Anthropic API Key

```bash
# Get the secret ARN from Terraform output
SECRET_ARN=$(terraform output -raw anthropic_secret_arn)

# Store your API key
aws secretsmanager put-secret-value \
  --secret-id $SECRET_ARN \
  --secret-string "your-anthropic-api-key"
```

## Step 3: Build and Push Docker Image

```bash
cd ..  # Back to project root

# Get ECR URL from Terraform
ECR_URL=$(cd terraform && terraform output -raw ecr_repository_url)

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_URL

# Build for ARM64 (required by AgentCore)
docker buildx create --use
docker buildx build --platform linux/arm64 \
  -t $ECR_URL:latest \
  --push .
```

## Step 4: Deploy Agent Runtime to AgentCore

Create a deployment script:

```bash
# deploy_to_agentcore.py
```

```python
#!/usr/bin/env python3
"""Deploy GC2 Planner Agent to Amazon Bedrock AgentCore."""

import boto3
import json
import sys

# Get Terraform outputs
def get_terraform_output(key):
    import subprocess
    result = subprocess.run(
        ["terraform", "output", "-raw", key],
        cwd="terraform",
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

# Initialize clients
region = "us-east-1"
agentcore_control = boto3.client('bedrock-agentcore-control', region_name=region)
agentcore_runtime = boto3.client('bedrock-agentcore', region_name=region)

# Get infrastructure details
ecr_url = get_terraform_output("ecr_repository_url")
role_arn = get_terraform_output("agentcore_runtime_role_arn")

print(f"Deploying agent with:")
print(f"  ECR Image: {ecr_url}:latest")
print(f"  IAM Role: {role_arn}")

# Create Agent Runtime
try:
    response = agentcore_control.create_agent_runtime(
        agentRuntimeName='gc2-copilot-strands-planner',
        agentRuntimeArtifact={
            'containerConfiguration': {
                'containerUri': f'{ecr_url}:latest'
            }
        },
        networkConfiguration={
            'networkMode': 'PUBLIC'
        },
        roleArn=role_arn
    )

    agent_runtime_arn = response['agentRuntimeArn']
    print(f"\n✅ Agent deployed successfully!")
    print(f"   ARN: {agent_runtime_arn}")

    # Test invocation
    print("\n🧪 Testing agent invocation...")
    test_payload = json.dumps({"prompt": "Say hello!"})

    invoke_response = agentcore_runtime.invoke_agent_runtime(
        agentRuntimeArn=agent_runtime_arn,
        runtimeSessionId='test-session-123',
        payload=test_payload,
        qualifier='DEFAULT'
    )

    print("✅ Test invocation successful!")
    print(f"   Response: {invoke_response}")

except Exception as e:
    print(f"❌ Deployment failed: {e}")
    sys.exit(1)
```

Run the deployment:

```bash
chmod +x deploy_to_agentcore.py
python deploy_to_agentcore.py
```

## Step 5: Invoke Your Deployed Agent

```python
import boto3
import json

client = boto3.client('bedrock-agentcore', region_name='us-east-1')

response = client.invoke_agent_runtime(
    agentRuntimeArn='arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/gc2-copilot-strands-planner-abc123',
    runtimeSessionId='my-session-id',
    payload=json.dumps({
        "prompt": "Plan a pipeline to move CSV files from S3 to S3"
    }),
    qualifier='DEFAULT'
)

print(response)
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│ Terraform Infrastructure                                │
├─────────────────────────────────────────────────────────┤
│  • ECR Repository (stores container image)              │
│  • IAM Role (permissions for agent)                     │
│  • CloudWatch Logs (agent logs)                         │
│  • Secrets Manager (API keys)                           │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Docker Build & Push                                     │
├─────────────────────────────────────────────────────────┤
│  • Build ARM64 container                                │
│  • Push to ECR                                          │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ boto3 Deployment Script                                 │
├─────────────────────────────────────────────────────────┤
│  • create_agent_runtime()                               │
│  • Links ECR image + IAM role                           │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Amazon Bedrock AgentCore Runtime                        │
├─────────────────────────────────────────────────────────┤
│  • Serverless agent execution                           │
│  • Session isolation                                    │
│  • Auto-scaling                                         │
└─────────────────────────────────────────────────────────┘
```

## Update Agent (Redeploy)

To update the agent with new code:

```bash
# 1. Rebuild and push new image
docker buildx build --platform linux/arm64 -t $ECR_URL:latest --push .

# 2. Update agent runtime
python update_agentcore.py  # Creates new version with updated image

# 3. Test new version
python test_agent.py
```

## Teardown

```bash
# 1. Delete AgentCore runtime (manual or via script)
aws bedrock-agentcore-control delete-agent-runtime \
  --agent-runtime-arn <your-runtime-arn>

# 2. Destroy Terraform infrastructure
cd terraform
terraform destroy
```

## Cost Considerations

- **AgentCore Runtime**: Pay per invocation + execution time
- **ECR Storage**: ~$0.10/GB/month
- **CloudWatch Logs**: Pay for storage and queries
- **Free tier**: AgentCore is free to try until September 16, 2025

## Troubleshooting

### Issue: Agent runtime fails to start
- Check CloudWatch logs: `aws logs tail /aws/bedrock/agentcore/gc2-planner-dev --follow`
- Verify IAM role permissions
- Ensure container exposes port 8080

### Issue: Authentication errors
- Verify Anthropic API key in Secrets Manager
- Check IAM role has `secretsmanager:GetSecretValue` permission

### Issue: Container build fails
- Ensure Docker buildx is installed: `docker buildx create --use`
- ARM64 platform is required: `--platform linux/arm64`

## References

- [AgentCore Documentation](https://strandsagents.com/latest/documentation/docs/user-guide/deploy/deploy_to_bedrock_agentcore/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AgentCore GitHub Issue](https://github.com/hashicorp/terraform-provider-aws/issues/43424)
