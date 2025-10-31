terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ECR Repository for Strands Agent Container
resource "aws_ecr_repository" "gc2_planner_agent" {
  name                 = "gc2-copilot-strands-planner"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "GC2 Copilot Strands Planner"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# ECR Lifecycle Policy
resource "aws_ecr_lifecycle_policy" "gc2_planner_policy" {
  repository = aws_ecr_repository.gc2_planner_agent.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus     = "any"
        countType     = "imageCountMoreThan"
        countNumber   = 10
      }
      action = {
        type = "expire"
      }
    }]
  })
}

# IAM Role for AgentCore Runtime
resource "aws_iam_role" "agentcore_runtime_role" {
  name = "gc2-agentcore-runtime-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "bedrock.amazonaws.com"
      }
    }]
  })

  tags = {
    Name        = "GC2 AgentCore Runtime Role"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# IAM Policy for AgentCore Runtime
resource "aws_iam_role_policy" "agentcore_runtime_policy" {
  name = "gc2-agentcore-runtime-policy"
  role = aws_iam_role.agentcore_runtime_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      }
    ]
  })
}

# CloudWatch Log Group for Agent Logs
resource "aws_cloudwatch_log_group" "agent_logs" {
  name              = "/aws/bedrock/agentcore/gc2-planner-${var.environment}"
  retention_in_days = 7

  tags = {
    Name        = "GC2 Planner Agent Logs"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Secrets Manager for Anthropic API Key
resource "aws_secretsmanager_secret" "anthropic_api_key" {
  name        = "gc2-copilot/anthropic-api-key-${var.environment}"
  description = "Anthropic API key for GC2 Copilot Strands Agent"

  tags = {
    Name        = "GC2 Anthropic API Key"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Note: Secret value should be set manually or via separate process
# terraform does not manage secret values for security reasons

# Outputs
output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.gc2_planner_agent.repository_url
}

output "agentcore_runtime_role_arn" {
  description = "ARN of the IAM role for AgentCore Runtime"
  value       = aws_iam_role.agentcore_runtime_role.arn
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.agent_logs.name
}

output "anthropic_secret_arn" {
  description = "ARN of the Anthropic API key secret"
  value       = aws_secretsmanager_secret.anthropic_api_key.arn
}
