"""GC2 Copilot - CLI for generating GrandCentral pipelines using AI agents."""

import argparse
import sys
from pathlib import Path
from src.gc2_copilot_strands.agents import generate_gc2_pipeline, display_pipeline_summary


def main():
    """Main CLI entry point for GC2 Copilot."""
    parser = argparse.ArgumentParser(
        description="Generate GrandCentral pipelines using AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate pipeline and display to console
  python main.py "Move CSV files from S3 to another S3 bucket"

  # Generate and save to file
  python main.py "Transfer encrypted files from S3, decrypt them" -o output/my-pipeline.json

  # Run demo with examples
  python main.py --demo

  # Run tests
  python main.py --test
        """
    )

    parser.add_argument(
        "request",
        nargs="?",
        help="Natural language description of the pipeline (e.g., 'Move CSV files from S3 to S3')"
    )

    parser.add_argument(
        "-o", "--output",
        help="Output file path for the generated pipeline JSON (e.g., output/pipeline.json)"
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demo with example pipelines"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test suite"
    )

    args = parser.parse_args()

    # Handle demo mode
    if args.demo:
        run_demo()
        return 0

    # Handle test mode
    if args.test:
        run_tests()
        return 0

    # Require request if not demo/test
    if not args.request:
        parser.print_help()
        print("\nError: Please provide a pipeline request or use --demo/--test")
        return 1

    # Generate pipeline
    try:
        pipeline = generate_gc2_pipeline(
            user_request=args.request,
            output_file=args.output
        )

        # Display summary
        if pipeline and "resources" in pipeline:
            display_pipeline_summary(pipeline)
            print(f"\n✅ Successfully generated pipeline with {len(pipeline['resources'])} resources")

            if args.output:
                print(f"📄 Saved to: {args.output}")
            else:
                print("\n💡 Tip: Use -o <file> to save the pipeline to a file")

        return 0

    except Exception as e:
        print(f"\n❌ Error generating pipeline: {e}")
        return 1


def run_demo():
    """Run demo with example pipelines."""
    print("\n" + "="*60)
    print("GC2 COPILOT DEMO")
    print("="*60)

    examples = [
        {
            "name": "Simple S3 Transfer",
            "request": "Move CSV files from S3 to another S3 bucket",
            "output": "tmp/demo-simple-transfer.json"
        },
        {
            "name": "S3 Transfer with PGP Decryption",
            "request": "Transfer PGP encrypted CSV files from S3, decrypt them, and save to another S3 bucket",
            "output": "tmp/demo-decrypt-transfer.json"
        }
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n\n{'='*60}")
        print(f"DEMO {i}: {example['name']}")
        print(f"{'='*60}")
        print(f"Request: {example['request']}")

        try:
            pipeline = generate_gc2_pipeline(
                user_request=example['request'],
                output_file=example['output']
            )

            if pipeline and "resources" in pipeline:
                display_pipeline_summary(pipeline)
                print(f"\n✅ Demo {i} complete - {len(pipeline['resources'])} resources generated")
        except Exception as e:
            print(f"\n❌ Demo {i} failed: {e}")

    print("\n\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print("\nGenerated files:")
    for example in examples:
        print(f"  - {example['output']}")

    print("\n💡 Try your own: python main.py 'Your pipeline request here' -o output.json")


def run_tests():
    """Run test suite."""
    print("\n" + "="*60)
    print("RUNNING TEST SUITE")
    print("="*60)

    import subprocess
    import os

    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    # Run scripts/test_complete_workflow.py
    try:
        result = subprocess.run(
            ["uv", "run", "python", "scripts/test_complete_workflow.py"],
            capture_output=False,
            text=True
        )
        return result.returncode
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
