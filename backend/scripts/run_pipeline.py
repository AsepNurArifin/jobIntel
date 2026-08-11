"""Manually trigger the pipeline. Usage:

    python -m scripts.run_pipeline                 # all steps, all sources
    python -m scripts.run_pipeline --step fetch    # only fetch
    python -m scripts.run_pipeline --source wwr    # only wwr source (fetch)
"""

from __future__ import annotations

import argparse
import asyncio

from app.pipeline.orchestrator import run_pipeline


async def _main(args: argparse.Namespace) -> None:
    stats = await run_pipeline(step=args.step, source=args.source)
    print(f"\nPipeline selesai. Ringkasan: {stats}")


def main() -> None:
    parser = argparse.ArgumentParser(description="JobIntel pipeline manual trigger")
    parser.add_argument("--step", choices=["fetch", "dedup", "extract", "normalize", "embed", "all"], default="all")
    parser.add_argument("--source", choices=["remoteok", "wwr", "adzuna", "all"], default="all")
    args = parser.parse_args()
    asyncio.run(_main(args))


if __name__ == "__main__":
    main()
