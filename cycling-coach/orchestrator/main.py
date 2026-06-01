"""CLI entry point for the cycling-coach pipeline.

Usage:
    python -m orchestrator.main
    python -m orchestrator.main --goals "race a century" "improve climbing" \\
                                 --bikes "Canyon Aeroad CF SLX 8" "Trek Madone SLR 7"
"""

import argparse
import asyncio
import json
import logging
import time

from orchestrator.orchestrator import CyclingCoachOrchestrator

_DEFAULT_GOALS = [
    "Build endurance for a century ride",
    "Improve climbing ability",
    "Lose weight while maintaining power",
]

_DEFAULT_BIKES = [
    "Canyon Aeroad CF SLX 8",
    "Trek Madone SLR 7 Gen 8",
    "Specialized Tarmac SL8",
    "Cervelo Caledonia",
]


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed namespace with ``goals`` and ``bikes`` lists.
    """
    parser = argparse.ArgumentParser(
        description="Run the cycling-coach multi-agent pipeline.",
    )
    parser.add_argument(
        "--goals",
        nargs="+",
        metavar="GOAL",
        default=_DEFAULT_GOALS,
        help="Athlete goal strings (space-separated, quote multi-word goals).",
    )
    parser.add_argument(
        "--bikes",
        nargs="+",
        metavar="BIKE",
        default=_DEFAULT_BIKES,
        help="Bike model names to evaluate (space-separated, quote multi-word names).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO).",
    )
    return parser.parse_args()


async def _main() -> None:
    """Run the pipeline, print the report as formatted JSON, and show timing."""
    args = _parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    print("\n" + "=" * 60)
    print("  Cycling Coach — Multi-Agent Pipeline")
    print("=" * 60)
    print(f"  Goals : {args.goals}")
    print(f"  Bikes : {args.bikes}")
    print("=" * 60 + "\n")

    orchestrator = CyclingCoachOrchestrator()
    wall_start = time.perf_counter()

    report = await orchestrator.run(
        athlete_goals=args.goals,
        bikes_under_consideration=args.bikes,
    )

    wall_elapsed = time.perf_counter() - wall_start

    print("\n" + "=" * 60)
    print("  REPORT")
    print("=" * 60)
    print(json.dumps(report, indent=2, default=str))
    print("\n" + "=" * 60)
    print(f"  Pipeline status  : {report['status'].upper()}")
    print(f"  Errors           : {len(report['errors'])}")
    print(f"  Wall-clock time  : {wall_elapsed:.2f}s")
    print("=" * 60 + "\n")


def main() -> None:
    """Synchronous entry point for ``pyproject.toml`` scripts."""
    asyncio.run(_main())


if __name__ == "__main__":
    main()
