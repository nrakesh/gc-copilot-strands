"""Tools for the Orchestrator Agent to coordinate pipeline generation."""

from typing import Dict, Any, List, Optional
import json
from strands import tool
from ..models.plan import ResourceSpec, ConnectionSpec
from ..utils.logger import setup_logger, log_tool_call, log_tool_result, log_error

# Set up logger
logger = setup_logger("gc2_copilot.orchestrator_tools", level=20)  # INFO level


@tool
def plan_new_pipeline(user_request: str) -> str:
    """
    Create a resource plan for a new GC2 pipeline.

    Use this tool to analyze the user's request and create a detailed plan
    of all resources and connections needed.

    Args:
        user_request: Natural language description of pipeline requirements

    Returns:
        JSON string containing the pipeline plan with resources and connections
    """
    log_tool_call("plan_new_pipeline", {"user_request": user_request[:100] + "..."}, logger)

    # Import here to avoid circular dependency
    from ..agents.planner import plan_pipeline

    logger.info("   Calling planner agent...")
    plan = plan_pipeline(user_request)

    if not plan:
        logger.error("   Planning failed - no plan returned")
        return json.dumps({"error": "Planning failed"})

    # Convert to dict for JSON serialization
    result = {
        "pattern_type": plan.pattern_type,
        "resources": [r.model_dump(exclude_none=True) for r in plan.resources],
        "connections": [c.model_dump(exclude_none=True) for c in plan.connections],
        "explanation": plan.explanation
    }

    logger.info(f"   Plan created: {plan.pattern_type}")
    logger.info(f"   Resources: {len(plan.resources)}, Connections: {len(plan.connections)}")

    result_json = json.dumps(result, indent=2)
    log_tool_result("plan_new_pipeline", result_json[:300] + "...", logger)

    return result_json


@tool
def generate_s3_resource_config(
    resource_name: str,
    resource_role: str,
    resource_description: str,
    user_request: str
) -> str:
    """
    Generate AWS S3 resource configuration.

    Use this tool to create a complete S3 resource configuration with all
    required properties (region, path, account, KMS key, etc.).

    Args:
        resource_name: Name for the S3 resource (max 50 chars)
        resource_role: Role of the resource (source, destination, processor)
        resource_description: Description of what this S3 resource does
        user_request: Original user request for context

    Returns:
        JSON string containing complete S3 resource configuration
    """
    # Import here to avoid circular dependency
    from ..agents.s3_specialist import generate_s3_resource

    # Create ResourceSpec from parameters
    spec = ResourceSpec(
        id=0,  # ID doesn't matter for individual generation
        name=resource_name,
        type="aws-s3",
        role=resource_role,
        description=resource_description
    )

    try:
        s3_resource = generate_s3_resource(spec, user_request)
        return json.dumps(s3_resource.model_dump(exclude_none=True), indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to generate S3 resource: {str(e)}"})


@tool
def generate_route_resource_config(
    route_name: str,
    source_resource_name: str,
    destination_resource_name: str,
    file_filter: str,
    actions: Optional[List[str]],
    user_request: str
) -> str:
    """
    Generate route resource configuration.

    Use this tool to create a complete route configuration that connects
    two resources with file filtering and optional actions.

    Args:
        route_name: Name for the route (max 50 chars)
        source_resource_name: Name of the source resource
        destination_resource_name: Name of the destination resource
        file_filter: File filter regex pattern (e.g., ".+\\.csv")
        actions: Optional list of actions (e.g., ["pgp-decrypt"]) or None for no actions
        user_request: Original user request for context

    Returns:
        JSON string containing complete route resource configuration
    """
    # Log the tool call
    log_tool_call("generate_route_resource_config", {
        "route_name": route_name,
        "source_resource_name": source_resource_name,
        "destination_resource_name": destination_resource_name,
        "file_filter": file_filter,
        "actions": actions,
        "actions_type": type(actions).__name__,
        "actions_value": repr(actions),
        "user_request": user_request[:100] + "..."
    }, logger)

    # Import here to avoid circular dependency
    from ..agents.route_specialist import generate_route_resource

    # Handle actions: empty list should become None for Pydantic
    # The issue: LLM may pass [] but ConnectionSpec expects None for no actions
    processed_actions = None
    if actions and len(actions) > 0:
        processed_actions = actions
        logger.info(f"   Actions provided: {processed_actions}")
    else:
        logger.info(f"   No actions (empty list or None) - setting to None")

    # Create ConnectionSpec
    connection = ConnectionSpec(
        from_resource=0,  # Will be resolved by route specialist
        to_resource=1,
        via="route",
        route_name=route_name,
        file_filter=file_filter,
        actions=processed_actions
    )

    logger.debug(f"   Created ConnectionSpec: {connection}")

    # Create dummy resource specs for the route specialist
    source_spec = ResourceSpec(
        id=0,
        name=source_resource_name,
        type="aws-s3",
        role="source",
        description="Source resource"
    )

    dest_spec = ResourceSpec(
        id=1,
        name=destination_resource_name,
        type="aws-s3",
        role="destination",
        description="Destination resource"
    )

    try:
        logger.info(f"   Calling route_specialist for {route_name}...")
        route_resource = generate_route_resource(
            connection,
            [source_spec, dest_spec],
            user_request
        )
        result = json.dumps(route_resource.model_dump(exclude_none=True), indent=2)
        log_tool_result("generate_route_resource_config", result[:200] + "...", logger)
        return result
    except Exception as e:
        log_error(e, "generate_route_resource_config", logger)
        error_result = json.dumps({"error": f"Failed to generate route resource: {str(e)}"})
        return error_result


@tool
def save_pipeline_to_file(pipeline_json: str, output_file: str) -> str:
    """
    Save the complete pipeline JSON to a file.

    Use this tool to write the final pipeline configuration to disk.

    Args:
        pipeline_json: Complete pipeline JSON string
        output_file: Path where to save the file (e.g., "tmp/my-pipeline.json")

    Returns:
        Success or error message
    """
    try:
        pipeline = json.loads(pipeline_json)

        with open(output_file, 'w') as f:
            json.dump(pipeline, f, indent=2)

        resource_count = len(pipeline.get("resources", []))
        return f"✅ Successfully saved pipeline with {resource_count} resources to {output_file}"

    except Exception as e:
        return f"❌ Failed to save pipeline: {str(e)}"


@tool
def assemble_pipeline_json(resources_json_list: List[str]) -> str:
    """
    Assemble multiple resource JSONs into a complete pipeline.

    Use this tool to combine all generated resources (S3, routes, etc.)
    into a single pipeline JSON.

    Args:
        resources_json_list: List of resource JSON strings to combine

    Returns:
        Complete pipeline JSON string with all resources
    """
    try:
        resources = []

        for resource_json in resources_json_list:
            resource = json.loads(resource_json)
            # Skip error responses
            if "error" not in resource:
                resources.append(resource)

        pipeline = {
            "resources": resources
        }

        return json.dumps(pipeline, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Failed to assemble pipeline: {str(e)}"})


# Future tools for UPDATE workflow (not implemented yet)
# These are placeholders showing what would be added later

def load_existing_pipeline(file_path: str) -> str:
    """
    Load an existing pipeline from file.

    TODO: Implement for UPDATE workflow.
    """
    raise NotImplementedError("UPDATE workflow not yet implemented")


def plan_pipeline_update(existing_pipeline: str, user_request: str) -> str:
    """
    Plan updates to an existing pipeline.

    TODO: Implement for UPDATE workflow.
    """
    raise NotImplementedError("UPDATE workflow not yet implemented")


def merge_pipelines(existing_pipeline: str, new_resources: List[str]) -> str:
    """
    Merge existing pipeline with new/modified resources.

    TODO: Implement for UPDATE workflow.
    """
    raise NotImplementedError("UPDATE workflow not yet implemented")
