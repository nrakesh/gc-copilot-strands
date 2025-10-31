"""GC2 Pipeline Planner Agent using Strands framework."""

from strands import Agent
from strands.models.anthropic import AnthropicModel
from strands.models.openai import OpenAIModel
from typing import Optional
from ..config import Config
from ..models.plan import PipelinePlan
from ..tools.rag_tools import query_rag_context
from ..utils.retry import with_retry


# System prompt for the planner agent
PLANNER_SYSTEM_PROMPT = """You are an expert GrandCentral (GC2) pipeline architect.

Your role is to analyze user requests and create detailed resource plans for data pipelines.

IMPORTANT: Before creating the plan, ALWAYS use the query_rag_context tool to get relevant context from:
- Connectivity patterns (how resources connect)
- Template examples (sample pipelines)
- Configuration guidance (best practices)
- Schema definitions (required properties)

Use this context to inform your resource plan.

CRITICAL ROUTING RULES:
- Consider the pipeline to be Graph Data Type, where sources and destinations are nodes and routes are edges.
- Each Route is one and only one connection
- Each source-to-destination connection requires a separate route resource
- If 1 source connects to 2 destinations, you need 2 route resources
- If 2 sources connect to 1 destination, you need 2 route resources
- 
- Routes handle file filtering, transformations, and data flow between resources
- For file type filtering each file type needs its own route with specific fileFilter. For example csv file must match .+\\.csv
- If file type cannot be identified use .+ as fileFilter
- If a file need to be decrypted, the fileFilter MUST be .+\\.pgp
- IMPORTANT: Include route resources in the resources array AND define their connections

CRITICAL ACTION DETECTION: Analyze the user request for these patterns:
- "pgp encrypted" OR "encrypted files" OR ".pgp files" → MUST add "pgp-decrypt" action
- "encrypt" OR "encryption" (without "encrypted") → add "pgp-encrypt" action
- "zip" OR "compress" → add "zip" action
- "unzip" OR "decompress" → add "unzip" action
- "virus scan" OR "security check" → add "virus-check" action

RESOURCE NAMING RULES:
- Maximum 50 characters
- Use hyphens (-) as separators, no underscores
- internal-partner resources MUST start with "TRP_"
- Use descriptive names based on purpose (e.g., "data-input-s3", "finance-partner", "TRP_hr-system")

RESOURCE TYPES:
Use GrandCentral resource types: aws-s3, external-partner, internal-partner, route, aws-s3-shared

FILE FILTER PATTERNS:
- If user mentions specific file types (csv, txt, json, etc.): Use ".+\\.<extension>"
- If no specific file type mentioned: Use ".+" for all files
- Examples: ".+\\.csv" for CSV files, ".+\\.txt" for text files

RESPONSE FORMAT:
You must respond with structured JSON in this exact format:
{
  "pattern_type": "brief description of the data flow pattern",
  "resources": [
    {
      "id": 0,
      "name": "descriptive-resource-name",
      "type": "resource_type",
      "role": "source|destination|processor",
      "description": "what this resource does in the pipeline",
    }
  ],
  "connections": [
    {
      "from_resource": 0,
      "to_resource": 1,
      "via": "route",
      "route_name": "descriptive-route-name",
      "file_filter": "regex_pattern",
      "actions": ["only_include_if_needed"]
    }
  ],
  "explanation": "your reasoning for this architecture"
}

KEY POINTS:
- Each resource must have a unique id starting from 0
- Connections use array indices (0, 1, 2...) to reference resources by their id field
- Include actions in connections only if the user request indicates processing is needed
- Route names should be descriptive (e.g., "route-csv", "route-txt")
- Each connection represents a complete route specification"""


def create_planner_agent() -> Agent:
    """
    Create the GC2 pipeline planner agent.

    Returns:
        Strands Agent configured for pipeline planning with structured output
    """
    Config.validate()

    # Create model based on configured provider
    if Config.LLM_PROVIDER == "openai":
        model = OpenAIModel(
            model_id=Config.OPENAI_MODEL,
            params={"max_tokens": 2000},
            client_args={"api_key": Config.OPENAI_API_KEY},
        )
    else:  # anthropic
        model = AnthropicModel(
            model_id=Config.CLAUDE_MODEL,
            max_tokens=2000,
            client_args={"api_key": Config.ANTHROPIC_API_KEY},
        )

    agent = Agent(
        name="gc2_pipeline_planner",
        model=model,
        system_prompt=PLANNER_SYSTEM_PROMPT,
        structured_output_model=PipelinePlan,  # Returns Pydantic model
        tools=[query_rag_context],  # RAG tool for querying vector store
    )

    return agent


def plan_pipeline(user_request: str) -> Optional[PipelinePlan]:
    """
    Generate a pipeline resource plan from a user request.

    Args:
        user_request: Natural language description of the pipeline needs

    Returns:
        PipelinePlan with resources and connections, or None if planning fails

    Example:
        >>> plan = plan_pipeline("Move CSV files from S3 to another S3 bucket")
        >>> print(plan.pattern_type)
        'S3 to S3 data transfer'
        >>> print(len(plan.resources))
        3  # source S3, destination S3, route
    """
    agent = create_planner_agent()

    @with_retry(
        max_retries=Config.MAX_RETRIES,
        initial_delay=Config.INITIAL_RETRY_DELAY,
        max_delay=Config.MAX_RETRY_DELAY
    )
    def _call_agent():
        """Wrapper function for retry logic."""
        return agent(f"Analyze this request and create a resource plan:\n\n{user_request}")

    try:
        # Call agent with retry logic
        result = _call_agent()

        # Extract the actual PipelinePlan from AgentResult.structured_output
        if hasattr(result, 'structured_output'):
            return result.structured_output
        else:
            # Fallback: result might be the plan directly
            return result
    except Exception as e:
        print(f"\n❌ Error planning pipeline: {e}")
        import traceback
        traceback.print_exc()
        return None


def display_plan(plan: PipelinePlan) -> None:
    """
    Display a pipeline plan in a readable format.

    Args:
        plan: The PipelinePlan to display
    """
    print("\n" + "="*60)
    print("PIPELINE RESOURCE PLAN")
    print("="*60)

    print(f"\nPattern Type: {plan.pattern_type}")
    print(f"\nExplanation: {plan.explanation}")

    print(f"\nResources ({len(plan.resources)}):")
    for resource in plan.resources:
        print(f"\n  [{resource.id}] {resource.name}")
        print(f"      Type: {resource.type}")
        print(f"      Role: {resource.role}")
        print(f"      Description: {resource.description}")

    print(f"\nConnections ({len(plan.connections)}):")
    for conn in plan.connections:
        from_resource = next(r for r in plan.resources if r.id == conn.from_resource)
        to_resource = next(r for r in plan.resources if r.id == conn.to_resource)

        print(f"\n  {from_resource.name} → {to_resource.name}")
        print(f"      Via: {conn.via}")
        if conn.route_name:
            print(f"      Route Name: {conn.route_name}")
        print(f"      File Filter: {conn.file_filter}")
        if conn.actions:
            print(f"      Actions: {', '.join(conn.actions)}")

    print("\n" + "="*60)


def test_planner():
    """Test the planner with sample requests."""
    test_cases = [
        "Move CSV files from an S3 bucket to another S3 bucket",
        "Transfer encrypted files from S3 to an SFTP partner, decrypt them during transfer",
        "Move JSON files from S3 to two destinations: another S3 bucket and an internal partner"
    ]

    for i, request in enumerate(test_cases, 1):
        print(f"\n\n{'='*60}")
        print(f"TEST CASE {i}")
        print(f"{'='*60}")
        print(f"\nUser Request:\n{request}")

        plan = plan_pipeline(request)

        if plan:
            display_plan(plan)
        else:
            print("\n❌ Failed to create plan")


if __name__ == "__main__":
    test_planner()
