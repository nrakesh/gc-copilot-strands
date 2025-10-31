"""Deploy GC2 Planner using Bedrock AgentCore Starter Toolkit."""

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from src.gc2_copilot_strands.agents.planner import create_planner_agent

# Create the AgentCore app wrapper
app = BedrockAgentCoreApp()

# Create your Strands agent once at startup
agent = create_planner_agent()


@app.entrypoint
def invoke(payload: dict) -> dict:
    """
    AgentCore entrypoint - automatically handles /ping and /invocations.

    Args:
        payload: Request from AgentCore with format:
                 {"prompt": "user message"}

    Returns:
        Response dict: {"result": "agent response"}
    """
    user_message = payload.get("prompt", "")

    if not user_message:
        return {"error": "No prompt provided"}

    try:
        # Invoke your Strands agent
        result = agent(user_message)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Run locally for testing on http://localhost:8080
    app.run()
