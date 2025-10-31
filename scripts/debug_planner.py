"""Debug script to see what Strands returns."""

from src.gc2_copilot_strands.agents.planner import create_planner_agent

agent = create_planner_agent()

request = "Move CSV files from S3 to S3"

print("Calling agent...")
result = agent(f"Analyze this request and create a resource plan:\n\n{request}")

print("\n" + "="*60)
print("DEBUG: What Strands Returned")
print("="*60)
print(f"\nType: {type(result)}")
print(f"\nDir: {dir(result)}")
print(f"\nResult: {result}")

if hasattr(result, 'message'):
    print(f"\nHas 'message' attribute!")
    print(f"Message type: {type(result.message)}")
    print(f"Message: {result.message}")

if hasattr(result, '__dict__'):
    print(f"\n__dict__: {result.__dict__}")
