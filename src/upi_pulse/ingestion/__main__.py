"""Command line: ``python -m upi_pulse.ingestion {ingest,status}``.

Exit codes are meaningful so Airflow and Make can react: ``ingest`` exits 1 if any file was
rejected, ``status`` exits 1 if any required file is missing.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from upi_pulse.config import load_settings
from upi_pulse.ingestion.manual_drop import land_drop, missing_periods
from upi_pulse.metrics import record_step

DEFAULT_FROM = "2024-10"
DEFAULT_TO = "2026-09"


def _cmd_ingest(args: argparse.Namespace) -> int:
    settings = load_settings()
    if settings.env != "local":
        print("Landing to cloud storage arrives in Phase 5; set UPI_PULSE_ENV=local.")
        return 2
    drop_dir = Path(settings.drop_dir)
    result = land_drop(drop_dir, Path(settings.layer_path("landing")))
    for entry in result.landed:
        print(
            f"landed   {entry.source}/{entry.period}/{entry.file_name}  sha256={entry.sha256[:12]}"
        )
    for rejection in result.rejected:
        print(f"REJECTED {rejection.path}: {rejection.reason}")
    print(
        f"\n{len(result.landed)} landed, {len(result.skipped)} already present, "
        f"{len(result.rejected)} rejected (drop folder: {drop_dir})"
    )
    if not args.no_metrics:
        record_step(
            Path(settings.metrics_path),
            "ingest",
            {
                "files_landed": len(result.landed),
                "files_already_present": len(result.skipped),
                "files_rejected": len(result.rejected),
                "bytes_landed": sum(e.size_bytes for e in result.landed),
            },
        )
    return 1 if result.rejected else 0


def _cmd_status(args: argparse.Namespace) -> int:
    settings = load_settings()
    missing = missing_periods(Path(settings.drop_dir), args.from_month, args.to_month)
    if not missing:
        print(f"All required files present for {args.from_month} to {args.to_month}.")
        return 0
    total = sum(len(v) for v in missing.values())
    print(f"{total} file(s) still missing for {args.from_month} to {args.to_month}:")
    for source, periods in missing.items():
        print(f"  {source:<13} {len(periods):>2}: {', '.join(periods)}")
    return 1


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and run a sub-command; returns the process exit code."""
    # Windows consoles default to cp1252; never crash on a non-ASCII file name.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(prog="python -m upi_pulse.ingestion")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="land new files from the manual-drop folder")
    ingest.add_argument("--no-metrics", action="store_true", help="don't write run_metrics.json")
    ingest.set_defaults(func=_cmd_ingest)

    status = sub.add_parser("status", help="list files still missing from the drop folder")
    status.add_argument("--from", dest="from_month", default=DEFAULT_FROM, help="YYYY-MM")
    status.add_argument("--to", dest="to_month", default=DEFAULT_TO, help="YYYY-MM")
    status.set_defaults(func=_cmd_status)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
