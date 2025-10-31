"""Orchestrator Agent for coordinating the complete pipeline generation workflow."""

from typing import Dict, Optional
import json
from strands import Agent
from strands.models.anthropic import AnthropicModel
from strands.models.openai import OpenAIModel
from ..config import Config
from ..tools import (
    plan_new_pipeline,
    generate_s3_resource_config,
    generate_route_resource_config,
    save_pipeline_to_file,
    assemble_pipeline_json
)
from ..utils.retry import with_retry
from ..utils.logger import setup_logger, log_agent_call

# Set up logger for orchestrator
logger = setup_logger("gc2_copilot.orchestrator", level=20)  # INFO level


# System prompt for the orchestrator agent
ORCHESTRATOR_SYSTEM_PROMPT = """You are the GC2 Pipeline Orchestrator Agent.

Your role is to coordinate the complete workflow for generating GC2 data pipelines.

WORKFLOW FOR CREATING NEW PIPELINES:

1. **Planning Phase**
   - Use the `plan_new_pipeline` tool with the user's request
   - This returns a plan with resources and connections
   - Extract the resource list and connection list from the plan

2. **Resource Generation Phase**
   - For each resource in the plan (EXCEPT routes):
     - If type is "aws-s3" or "aws-s3-shared":
       → Use `generate_s3_resource_config` tool
       → Provide: resource name, role, description, and user request
     - For other types (partners, etc.):
       → Skip for now (not yet implemented)
   - Collect all generated resource JSONs in a list

3. **Route Generation Phase**
   - For each connection in the plan:
     - Use `generate_route_resource_config` tool
     - Provide: route_name, source name, destination name, file_filter, actions, user request
   - Add generated route JSONs to the resource list

4. **Assembly Phase**
   - Use `assemble_pipeline_json` tool
   - Pass the complete list of resource JSONs (S3 + routes)
   - This creates the final pipeline JSON

5. **Save Phase** (if output_file provided)
   - Use `save_pipeline_to_file` tool
   - Pass the pipeline JSON and output file path

IMPORTANT RULES:

- Always start with `plan_new_pipeline` to understand what resources are needed
- Generate S3 resources BEFORE routes (routes reference S3 resources by name)
- Skip unsupported resource types gracefully (partners not yet implemented)
- Use the EXACT resource names from the plan when generating routes
- The file_filter and actions come from the connection spec in the plan
- Always provide the original user_request context to generation tools

RESPONSE FORMAT:

At the end, respond with a summary including:
- Number of resources generated
- Resource types and names
- Save location (if applicable)

FUTURE CAPABILITY (not yet implemented):
- UPDATE workflow: Modifying existing pipelines
- This will be added later with additional tools
"""


def create_orchestrator_agent() -> Agent:
    """
    Create the GC2 pipeline orchestrator agent.

    Returns:
        Strands Agent configured for pipeline orchestration with tools
    """
    Config.validate()

    # Create model based on configured provider
    if Config.LLM_PROVIDER == "openai":
        model = OpenAIModel(
            model_id=Config.OPENAI_MODEL,
            params={"max_tokens": 4000},  # Higher limit for orchestration
            client_args={"api_key": Config.OPENAI_API_KEY},
        )
    else:  # anthropic
        model = AnthropicModel(
            model_id=Config.CLAUDE_MODEL,
            max_tokens=4000,
            client_args={"api_key": Config.ANTHROPIC_API_KEY},
        )

    agent = Agent(
        name="gc2_orchestrator",
        model=model,
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        tools=[
            plan_new_pipeline,
            generate_s3_resource_config,
            generate_route_resource_config,
            assemble_pipeline_json,
            save_pipeline_to_file
        ]
    )

    return agent


@with_retry(
    max_retries=Config.MAX_RETRIES,
    initial_delay=Config.INITIAL_RETRY_DELAY,
    max_delay=Config.MAX_RETRY_DELAY
)
def _call_orchestrator(agent: Agent, prompt: str):
    """Wrapper for calling orchestrator with retry logic."""
    log_agent_call("orchestrator", prompt, logger)
    result = agent(prompt)

    # Log the agent response details
    logger.info("🎯 Orchestrator completed execution")
    if hasattr(result, 'content'):
        logger.debug(f"   Response content: {str(result.content)[:200]}...")
    if hasattr(result, 'tool_calls'):
        logger.info(f"   Total tool calls made: {len(result.tool_calls) if result.tool_calls else 0}")

    return result


def generate_gc2_pipeline(
    user_request: str,
    output_file: Optional[str] = None
) -> Dict:
    """
    Generate a GC2 pipeline from a natural language request.

    This is the main entry point for pipeline generation. It creates an
    orchestrator agent and coordinates the complete workflow.

    Args:
        user_request: Natural language description of pipeline requirements
        output_file: Optional file path to save the generated pipeline JSON

    Returns:
        Complete pipeline configuration as dictionary

    Example:
        >>> pipeline = generate_gc2_pipeline(
        ...     "Move CSV files from S3 to another S3 bucket",
        ...     output_file="tmp/my-pipeline.json"
        ... )
        >>> print(len(pipeline["resources"]))
        3

    Future Usage (when UPDATE is implemented):
        >>> pipeline = generate_gc2_pipeline(
        ...     "Add virus scanning before the destination",
        ...     existing_file="tmp/my-pipeline.json",
        ...     output_file="tmp/my-pipeline-v2.json"
        ... )
    """
    print("\n" + "="*60)
    print("GC2 PIPELINE ORCHESTRATOR")
    print("="*60)
    print(f"\nUser Request: {user_request}\n")

    # Create orchestrator agent
    agent = create_orchestrator_agent()

    # Build prompt for the agent
    prompt = f"""Generate a complete GC2 pipeline for this request:

USER REQUEST:
{user_request}

"""

    if output_file:
        prompt += f"""
SAVE LOCATION:
Save the final pipeline to: {output_file}
"""

    prompt += """
Follow the workflow steps in your system prompt:
1. Plan the pipeline
2. Generate S3 resources
3. Generate route resources
4. Assemble pipeline JSON
5. Save to file (if requested)

Provide a summary when complete.
"""

    try:
        # Call orchestrator agent with retry logic
        print("🤖 Orchestrator Agent starting workflow...\n")
        result = _call_orchestrator(agent, prompt)

        # The agent's tool calls have already generated the pipeline
        # Extract the pipeline from save_pipeline_to_file result or assemble_pipeline_json result
        # For now, we'll parse it from the conversation

        print("\n" + "="*60)
        print("✅ ORCHESTRATOR COMPLETE")
        print("="*60)

        # If a file was saved, load and return it
        if output_file:
            try:
                with open(output_file, 'r') as f:
                    pipeline = json.load(f)
                print(f"\n📄 Pipeline loaded from: {output_file}")
                return pipeline
            except Exception as e:
                print(f"\n⚠️  Could not load saved file: {e}")

        # Otherwise, return a placeholder
        # (In practice, the agent should save the file)
        return {"resources": [], "note": "Check orchestrator output above"}

    except Exception as e:
        print(f"\n❌ Pipeline generation failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def display_pipeline_summary(pipeline: Dict) -> None:
    """
    Display a human-readable summary of the generated pipeline.

    Args:
        pipeline: Generated pipeline configuration
    """
    print("\n" + "="*60)
    print("PIPELINE SUMMARY")
    print("="*60)

    resources = pipeline.get("resources", [])

    # Group by type
    by_type = {}
    for resource in resources:
        resource_type = resource.get("type", "unknown")
        if resource_type not in by_type:
            by_type[resource_type] = []
        by_type[resource_type].append(resource)

    print(f"\nTotal Resources: {len(resources)}\n")

    for resource_type, items in sorted(by_type.items()):
        print(f"{resource_type}: {len(items)}")
        for item in items:
            name = item.get("resourceName", "unknown")
            print(f"  - {name}")

    print("\n" + "="*60)


# Convenience function for testing
def test_orchestrator():
    """Test the orchestrator agent with sample requests."""
    test_cases = [
        {
            "request": "Move CSV files from S3 to another S3 bucket",
            "output": "tmp/pipeline-s3-to-s3.json"
        },
        {
            "request": "Transfer PGP encrypted CSV files from S3, decrypt them, and save to another S3 bucket",
            "output": "tmp/pipeline-s3-decrypt.json"
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n\n{'='*60}")
        print(f"TEST CASE {i}")
        print(f"{'='*60}")

        try:
            pipeline = generate_gc2_pipeline(
                user_request=test["request"],
                output_file=test["output"]
            )

            if pipeline and "resources" in pipeline:
                display_pipeline_summary(pipeline)
                print(f"\n✅ Test {i} passed - {len(pipeline['resources'])} resources")
            else:
                print(f"\n⚠️  Test {i} completed - check output file")

        except Exception as e:
            print(f"\n❌ Test {i} failed: {e}")


if __name__ == "__main__":
    test_orchestrator()
