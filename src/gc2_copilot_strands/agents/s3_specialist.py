"""S3 Specialist Agent for generating AWS S3 resource configurations."""

from strands import Agent
from strands.models.anthropic import AnthropicModel
from strands.models.openai import OpenAIModel
from typing import Optional
from ..config import Config
from ..models.s3_resource import S3Properties, S3Resource
from ..models.plan import ResourceSpec
from ..utils.retry import with_retry


# System prompt for S3 specialist
S3_SPECIALIST_PROMPT = """You are an expert AWS S3 resource configuration specialist.

Your role is to generate complete and valid AWS S3 resource configurations based on:
1. The resource specification from the pipeline planner
2. The original user request context
3. S3 schema requirements and constraints

IMPORTANT RULES FOR S3 CONFIGURATION:

**Region**:
- Always use "us-east-1" as the default region

**S3 Path** (bucket-name/path/to/folder, max 319 chars):
- For SOURCE resources: Use paths where files originate
  Examples: "source-bucket/input/csv", "data-lake/raw/files"
- For DESTINATION resources: Use paths where processed files go
  Examples: "output-bucket/processed", "archive-bucket/final"
- Create logical folder structure based on file types and purpose
- Extract specific paths from user request if mentioned

**AWS Account Name** (max 100 chars):
- Use descriptive account names like "prod-data-account", "dev-analytics"
- Default to "prod-account" if not specified

**KMS Key** (max 50 chars):
- ALWAYS use alias format: "alias/aws/s3" or "alias/my-key-name"
- NEVER use full ARNs or key IDs (they exceed 50 char limit)

**isEnabled**:
- Always set to true

**Description** (max 100 chars):
- Clear, concise description of what this S3 resource does
- Mention role (source/destination) and purpose

Generate valid S3 properties that match the Pydantic schema exactly.
"""


def create_s3_specialist() -> Agent:
    """
    Create the S3 specialist agent.

    Returns:
        Strands Agent configured for S3 resource generation with structured output
    """
    Config.validate()

    # Create model based on configured provider
    if Config.LLM_PROVIDER == "openai":
        model = OpenAIModel(
            model_id=Config.OPENAI_MODEL,
            params={"max_tokens": 1000},
            client_args={"api_key": Config.OPENAI_API_KEY},
        )
    else:  # anthropic
        model = AnthropicModel(
            model_id=Config.CLAUDE_MODEL,
            max_tokens=1000,
            client_args={"api_key": Config.ANTHROPIC_API_KEY},
        )

    agent = Agent(
        name="s3_specialist",
        model=model,
        system_prompt=S3_SPECIALIST_PROMPT,
        structured_output_model=S3Properties,
        tools=[],  # No tools needed for now
    )

    return agent


def generate_s3_resource(
    resource_spec: ResourceSpec,
    user_request: str,
    rag_context: Optional[str] = None
) -> S3Resource:
    """
    Generate a complete S3 resource configuration.

    Args:
        resource_spec: Resource specification from the planner
        user_request: Original user request for context
        rag_context: Optional RAG context about S3 schemas and templates

    Returns:
        Complete S3Resource with validated properties

    Raises:
        Exception: If S3 resource generation or validation fails
    """
    agent = create_s3_specialist()

    # Get RAG context if not provided
    if rag_context is None:
        chroma_client = Config.get_chroma_client()
        schema_results = chroma_client.query_collection(
            collection_name="gc2_schemas",
            query_text=f"aws-s3 schema properties constraints",
            n_results=2
        )

        template_results = chroma_client.query_collection(
            collection_name="gc2_templates",
            query_text=f"aws-s3 {resource_spec.role} example",
            n_results=2
        )

        context_parts = []
        if schema_results and schema_results.get("documents"):
            context_parts.append("SCHEMA CONTEXT:")
            for doc in schema_results["documents"][0][:1]:
                context_parts.append(f"- {doc}")

        if template_results and template_results.get("documents"):
            context_parts.append("\nTEMPLATE EXAMPLES:")
            for doc in template_results["documents"][0][:1]:
                context_parts.append(f"- {doc}")

        rag_context = "\n".join(context_parts) if context_parts else "No RAG context available"

    # Build the prompt for the agent
    prompt = f"""
Generate S3 properties for this resource:

RESOURCE SPECIFICATION:
- Name: {resource_spec.name}
- Role: {resource_spec.role}
- Description: {resource_spec.description}

USER REQUEST:
{user_request}

RAG CONTEXT:
{rag_context}

Generate the S3 properties (awsRegion, s3Path, awsAccountName, kmsKey, isEnabled, description)
following the rules in the system prompt.
"""

    @with_retry(
        max_retries=Config.MAX_RETRIES,
        initial_delay=Config.INITIAL_RETRY_DELAY,
        max_delay=Config.MAX_RETRY_DELAY
    )
    def _call_agent():
        """Wrapper function for retry logic."""
        return agent(prompt)

    try:
        # Call the agent to generate S3 properties with retry logic
        result = _call_agent()

        # Extract structured output
        if hasattr(result, 'structured_output'):
            s3_properties = result.structured_output
        else:
            raise Exception("Agent did not return structured output")

        # Create complete S3 resource
        s3_resource = S3Resource(
            resourceName=resource_spec.name,
            type="aws-s3",
            properties=s3_properties
        )

        return s3_resource

    except Exception as e:
        raise Exception(f"Failed to generate S3 resource: {e}")


# Convenience function for testing
def test_s3_specialist():
    """Test the S3 specialist with a sample resource spec."""
    from ..models.plan import ResourceSpec

    # Sample resource spec from planner
    spec = ResourceSpec(
        id=0,
        name="source-s3-bucket",
        type="aws-s3",
        role="source",
        description="Source S3 bucket containing CSV files"
    )

    user_request = "Move CSV files from S3 to another S3 bucket"

    print("=" * 60)
    print("Testing S3 Specialist Agent")
    print("=" * 60)
    print(f"\nResource Spec: {spec.name} ({spec.role})")
    print(f"User Request: {user_request}")
    print("\nGenerating S3 configuration...")

    try:
        s3_resource = generate_s3_resource(spec, user_request)

        print("\n" + "=" * 60)
        print("S3 Resource Generated Successfully")
        print("=" * 60)
        print(f"\nResource Name: {s3_resource.resourceName}")
        print(f"Type: {s3_resource.type}")
        print(f"\nProperties:")
        print(f"  Region: {s3_resource.properties.awsRegion}")
        print(f"  S3 Path: {s3_resource.properties.s3Path}")
        print(f"  Account: {s3_resource.properties.awsAccountName}")
        print(f"  KMS Key: {s3_resource.properties.kmsKey}")
        print(f"  Enabled: {s3_resource.properties.isEnabled}")
        print(f"  Description: {s3_resource.properties.description}")

        # Show JSON
        print(f"\n" + "=" * 60)
        print("JSON Output:")
        print("=" * 60)
        import json
        print(json.dumps(s3_resource.model_dump(exclude_none=True), indent=2))

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_s3_specialist()
