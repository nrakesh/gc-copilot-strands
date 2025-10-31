# Amazon Bedrock AgentCore Runtime Resource
# Documentation: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/bedrockagentcore_agent_runtime

# Build and push Docker image (prerequisite for agent runtime)
resource "null_resource" "docker_build_push" {
  triggers = {
    # Rebuild when source code changes
    src_hash = sha256(join("", [
      for f in fileset("${path.module}/../src", "**/*.py") : filesha256("${path.module}/../src/${f}")
    ]))
    agent_deploy_hash = filesha256("${path.module}/../agent_deploy.py")
    dockerfile_hash   = filesha256("${path.module}/../Dockerfile")
    ecr_url          = aws_ecr_repository.gc2_planner_agent.repository_url
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -e
      echo "Building and pushing Docker image..."

      # Login to ECR
      aws ecr get-login-password --region ${var.aws_region} | \
        docker login --username AWS --password-stdin ${aws_ecr_repository.gc2_planner_agent.repository_url}

      # Build and push for ARM64
      cd ${path.module}/..
      docker buildx create --use --name gc2-builder 2>/dev/null || docker buildx use gc2-builder
      docker buildx build \
        --platform linux/arm64 \
        -t ${aws_ecr_repository.gc2_planner_agent.repository_url}:latest \
        --push \
        .

      echo "✓ Docker image pushed to ECR"
    EOT
  }

  depends_on = [aws_ecr_repository.gc2_planner_agent]
}

# AgentCore Agent Runtime
resource "aws_bedrockagentcore_agent_runtime" "gc2_planner" {
  agent_runtime_name = "gc2-copilot-strands-${var.environment}"

  agent_runtime_artifact {
    container_configuration {
      container_uri = "${aws_ecr_repository.gc2_planner_agent.repository_url}:latest"
    }
  }

  network_configuration {
    network_mode = "PUBLIC"
  }

  role_arn = aws_iam_role.agentcore_runtime_role.arn

  tags = {
    Name        = "GC2 Copilot Strands Planner"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  depends_on = [
    null_resource.docker_build_push,
    aws_iam_role.agentcore_runtime_role
  ]
}

# Outputs for the AgentCore runtime
output "agentcore_agent_runtime_arn" {
  description = "ARN of the AgentCore agent runtime"
  value       = aws_bedrockagentcore_agent_runtime.gc2_planner.arn
}

output "agentcore_agent_runtime_name" {
  description = "Name of the AgentCore agent runtime"
  value       = aws_bedrockagentcore_agent_runtime.gc2_planner.agent_runtime_name
}

output "agentcore_invoke_example" {
  description = "Example command to invoke the agent"
  value = <<-EOT
    # Using AWS CLI
    aws bedrock-agentcore invoke-agent-runtime \
      --agent-runtime-arn ${aws_bedrockagentcore_agent_runtime.gc2_planner.arn} \
      --runtime-session-id "session-$(date +%s)" \
      --payload '{"prompt":"Plan a pipeline to move CSV files from S3 to S3"}' \
      --qualifier DEFAULT \
      --region ${var.aws_region} \
      /dev/stdout

    # Using boto3 Python
    import boto3
    import json

    client = boto3.client('bedrock-agentcore', region_name='${var.aws_region}')
    response = client.invoke_agent_runtime(
        agentRuntimeArn='${aws_bedrockagentcore_agent_runtime.gc2_planner.arn}',
        runtimeSessionId='my-session',
        payload=json.dumps({"prompt": "Your message"}),
        qualifier='DEFAULT'
    )
  EOT
}
