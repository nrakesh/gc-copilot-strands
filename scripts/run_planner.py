"""Run the GC2 pipeline planner agent locally."""

from src.gc2_copilot_strands.agents.planner import plan_pipeline, display_plan

if __name__ == "__main__":
    print("=" * 60)
    print("GC2 Copilot - Strands Pipeline Planner")
    print("=" * 60)

    # Example request
    user_request = """
    Move CSV files from an S3 bucket to another S3 bucket.
    The files are PGP encrypted and need to be decrypted during transfer.
    """

    print(f"\nUser Request:")
    print(user_request.strip())

    print("\n🤖 Agent is analyzing the request and planning resources...")
    print("(This may take a few seconds)")

    # Generate plan
    plan = plan_pipeline(user_request)

    if plan:
        # Display the plan
        display_plan(plan)

        print("\n✅ Plan generated successfully!")
        print("\nNext steps:")
        print("  1. Add specialist agents for each resource type")
        print("  2. Implement DAG assembly")
        print("  3. Add validation")
    else:
        print("\n❌ Failed to generate plan")
