"""Route Specialist Agent for generating route resource configurations."""

from strands import Agent
from strands.models.anthropic import AnthropicModel
from strands.models.openai import OpenAIModel
from typing import Optional, List
from ..config import Config
from ..models.route_resource import RouteProperties, RouteResource, SourceDestinationRef
from ..models.plan import ResourceSpec, ConnectionSpec
from ..utils.retry import with_retry


# System prompt for Route specialist
ROUTE_SPECIALIST_PROMPT = """You are an expert GrandCentral route configuration specialist.

Your role is to generate complete and valid route resource configurations based on:
1. The connection specification from the pipeline planner
2. Source and destination resource names
3. The original user request context
4. Route schema requirements and constraints

IMPORTANT RULES FOR ROUTE CONFIGURATION:

**Source & Destination**:
- Use the exact resource names provided
- Format: {"ref": "resource-name"}

**File Filter** (max 200 chars):
- Use the file filter pattern from the connection spec
- Common patterns:
  - CSV files: .+\\.csv
  - TXT files: .+\\.txt
  - JSON files: .+\\.json
  - PGP encrypted: .+\\.pgp
  - All files: .+

**Actions** (optional):
- ONLY include if specified in the connection spec
- Valid actions: pgp-decrypt, pgp-encrypt, zip, gzip, unzip, validate-inline, validate-offline, virus-check, batch
- If actions list is empty in connection spec, set to null (omit the field)

**Emails**:
- failureEmail: Use format "team-name@troweprice.com" (max 200 chars)
- successEmail: Use format "team-name@troweprice.com" (max 200 chars)
- Default to "gc2-team@troweprice.com" if not specified

**Email Flags**:
- disableFailureEmail: Always true
- disableSuccessEmail: Always false

**isEnabled**:
- Always set to true

**Description** (max 200 chars):
- Clear description of what this route does
- Mention source → destination flow
- Include file type and any actions

Generate valid route properties that match the Pydantic schema exactly.
"""


def create_route_specialist() -> Agent:
    """
    Create the Route specialist agent.

    Returns:
        Strands Agent configured for route resource generation with structured output
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
        name="route_specialist",
        model=model,
        system_prompt=ROUTE_SPECIALIST_PROMPT,
        structured_output_model=RouteProperties,
        tools=[],  # No tools needed for now
    )

    return agent


def generate_route_resource(
    connection_spec: ConnectionSpec,
    all_resources: List[ResourceSpec],
    user_request: str,
    rag_context: Optional[str] = None
) -> RouteResource:
    """
    Generate a complete route resource configuration.

    Args:
        connection_spec: Connection specification from the planner
        all_resources: All resources in the plan to resolve refs
        user_request: Original user request for context
        rag_context: Optional RAG context about route schemas

    Returns:
        Complete RouteResource with validated properties

    Raises:
        Exception: If route resource generation or validation fails
    """
    agent = create_route_specialist()

    # Find source and destination resource names
    source_resource = next((r for r in all_resources if r.id == connection_spec.from_resource), None)
    dest_resource = next((r for r in all_resources if r.id == connection_spec.to_resource), None)

    if not source_resource or not dest_resource:
        raise Exception(f"Could not find source or destination resource for connection")

    # Get RAG context if not provided
    if rag_context is None:
        chroma_client = Config.get_chroma_client()
        schema_results = chroma_client.query_collection(
            collection_name="gc2_schemas",
            query_text=f"route schema properties constraints",
            n_results=2
        )

        template_results = chroma_client.query_collection(
            collection_name="gc2_templates",
            query_text=f"route {connection_spec.file_filter} example",
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
    actions_info = f"Actions: {connection_spec.actions}" if connection_spec.actions else "No actions (set to null)"

    prompt = f"""
Generate route properties for this connection:

CONNECTION SPECIFICATION:
- Route Name: {connection_spec.route_name}
- Source Resource: {source_resource.name}
- Destination Resource: {dest_resource.name}
- File Filter: {connection_spec.file_filter}
- {actions_info}

USER REQUEST:
{user_request}

RAG CONTEXT:
{rag_context}

Generate the route properties (description, fileFilter, isEnabled, source, destination, actions,
failureEmail, successEmail, disableFailureEmail, disableSuccessEmail) following the rules
in the system prompt.

IMPORTANT:
- source must be: {{"ref": "{source_resource.name}"}}
- destination must be: {{"ref": "{dest_resource.name}"}}
- fileFilter must be: "{connection_spec.file_filter}"
- actions: {connection_spec.actions if connection_spec.actions else "null (omit this field)"}
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
        # Call the agent to generate route properties with retry logic
        result = _call_agent()

        # Extract structured output
        if hasattr(result, 'structured_output'):
            route_properties = result.structured_output
        else:
            raise Exception("Agent did not return structured output")

        # Create complete route resource
        route_resource = RouteResource(
            resourceName=connection_spec.route_name,
            type="route",
            properties=route_properties
        )

        return route_resource

    except Exception as e:
        raise Exception(f"Failed to generate route resource: {e}")


# Convenience function for testing
def test_route_specialist():
    """Test the route specialist with sample data."""
    from ..models.plan import ResourceSpec, ConnectionSpec

    # Sample resources
    resources = [
        ResourceSpec(
            id=0,
            name="source-s3-bucket",
            type="aws-s3",
            role="source",
            description="Source S3 bucket containing CSV files"
        ),
        ResourceSpec(
            id=1,
            name="destination-s3-bucket",
            type="aws-s3",
            role="destination",
            description="Destination S3 bucket for CSV files"
        )
    ]

    # Sample connection
    connection = ConnectionSpec(
        from_resource=0,
        to_resource=1,
        via="route",
        route_name="route-csv-transfer",
        file_filter=".+\\.csv",
        actions=[]
    )

    user_request = "Move CSV files from S3 to another S3 bucket"

    print("=" * 60)
    print("Testing Route Specialist Agent")
    print("=" * 60)
    print(f"\nConnection: {resources[0].name} → {resources[1].name}")
    print(f"File Filter: {connection.file_filter}")
    print(f"Actions: {connection.actions if connection.actions else 'None'}")
    print("\nGenerating route configuration...")

    try:
        route_resource = generate_route_resource(connection, resources, user_request)

        print("\n" + "=" * 60)
        print("Route Resource Generated Successfully")
        print("=" * 60)
        print(f"\nResource Name: {route_resource.resourceName}")
        print(f"Type: {route_resource.type}")
        print(f"\nProperties:")
        print(f"  Source: {route_resource.properties.source.ref}")
        print(f"  Destination: {route_resource.properties.destination.ref}")
        print(f"  File Filter: {route_resource.properties.fileFilter}")
        print(f"  Actions: {route_resource.properties.actions}")
        print(f"  Enabled: {route_resource.properties.isEnabled}")
        print(f"  Description: {route_resource.properties.description}")
        print(f"  Failure Email: {route_resource.properties.failureEmail}")
        print(f"  Success Email: {route_resource.properties.successEmail}")

        # Show JSON
        print(f"\n" + "=" * 60)
        print("JSON Output:")
        print("=" * 60)
        import json
        print(json.dumps(route_resource.model_dump(exclude_none=True), indent=2))

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_route_specialist()
