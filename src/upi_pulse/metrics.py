"""Write measured run metrics to ``metrics/run_metrics.json``.

Every number quoted in the README is generated from this file, so it must only ever contain
values measured by a real run, never hand-typed ones.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def record_step(
    metrics_path: Path, step: str, values: dict[str, Any], now: datetime | None = None
) -> dict[str, Any]:
    """Store the latest metrics for one pipeline step, keeping other steps intact.

    Args:
        metrics_path: JSON file to update (created if missing).
        step: Step name, e.g. ``"ingest"`` or ``"silver"``.
        values: JSON-serialisable measurements.
        now: Timestamp override for tests.

    Returns:
        The full metrics document after the update.
    """
    doc: dict[str, Any] = {"steps": {}}
    if metrics_path.exists():
        doc = json.loads(metrics_path.read_text(encoding="utf-8"))
        doc.setdefault("steps", {})
    recorded_at = (now or datetime.now(UTC)).astimezone(UTC).isoformat(timespec="seconds")
    doc["steps"][step] = {**values, "recorded_at": recorded_at}
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return doc
