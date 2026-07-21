import argparse
import json
import os
import sys

# Add project root to Python search path
sys.path.insert(0, os.path.abspath("."))

from src.tools.benchmark.models import BenchmarkConfig
from src.tools.benchmark.runner import BenchmarkRunner

def main():
    parser = argparse.ArgumentParser(description="HeroEngine Automated Benchmarking & Profiling Tool")
    parser.add_argument("--duration", type=float, default=2.0, help="Measurement phase duration in seconds per scenario")
    parser.add_argument("--warmup", type=float, default=1.0, help="Warm-up phase duration in seconds before measurement")
    parser.add_argument("--particles", type=str, default="1000,5000,10000", help="Comma-separated particle counts for render benchmark")
    parser.add_argument("--scenario", type=str, default=None, help="Specific scenario to run (vision, gesture, render, network, memory)")
    parser.add_argument("--headless", action="store_true", default=True, help="Run benchmarks headlessly without window UI")
    parser.add_argument("--json", type=str, default=None, help="File path to save benchmark JSON results")
    parser.add_argument("--markdown", type=str, default=None, help="File path to save generated Markdown report")
    parser.add_argument("--compare", type=str, default=None, help="Path to baseline benchmark JSON file for regression comparison")

    args = parser.parse_args()

    # Parse particle counts list
    try:
        particle_counts = [int(p.strip()) for p in args.particles.split(",") if p.strip()]
    except Exception:
        print(f"Error: Invalid --particles argument '{args.particles}'. Must be comma-separated integers.")
        sys.exit(1)

    scenarios = [args.scenario] if args.scenario else ["vision", "gesture", "render", "network", "memory"]

    config = BenchmarkConfig(
        duration_seconds=args.duration,
        warmup_seconds=args.warmup,
        particle_counts=particle_counts,
        headless=args.headless,
        scenarios=scenarios
    )

    runner = BenchmarkRunner()
    print("--- Executing HeroEngine Benchmark Suite ---")
    result = runner.run(config)
    print("--- Benchmark Suite Execution Completed ---")

    result_dict = result.to_dict()

    # Handle regression comparison mode
    if args.compare:
        if not os.path.exists(args.compare):
            print(f"Error: Baseline comparison file '{args.compare}' not found.")
            sys.exit(1)
        with open(args.compare, "r", encoding="utf-8") as f:
            baseline_data = json.load(f)
        comparison_report = runner.compare_results(result, baseline_data)
        print("\n" + comparison_report)

    # Print summary Markdown to console if no export file specified
    md_report = runner.generate_markdown_report(result)

    if args.markdown:
        os.makedirs(os.path.dirname(os.path.abspath(args.markdown)), exist_ok=True)
        with open(args.markdown, "w", encoding="utf-8") as f:
            f.write(md_report)
        print(f"Saved Markdown report to: {args.markdown}")
    elif not args.compare:
        print("\n" + md_report)

    if args.json:
        os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2)
        print(f"Saved JSON results to: {args.json}")

    sys.exit(0)

if __name__ == "__main__":
    main()
