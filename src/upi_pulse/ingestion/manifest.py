"""The landing manifest: an append-only audit log of every file that entered the lake.

Stored as JSON Lines (one JSON object per line) at ``landing/_manifest.jsonl``. Appending is
safe and cheap, and the file is easy to diff, grep and load into Spark.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

MANIFEST_NAME = "_manifest.jsonl"
_CHUNK = 1024 * 1024


@dataclass(frozen=True)
class ManifestEntry:
    """One landed file.

    Attributes:
        source: Source name, e.g. ``npci_apps``.
        period: Period label, e.g. ``2026-09`` or ``FY2025-26``.
        file_name: Original file name, unchanged.
        landed_path: Path relative to the landing root (POSIX style).
        sha256: Hex SHA-256 of the file's bytes.
        size_bytes: File size.
        method: How the file arrived (``manual_drop`` or ``http``).
        origin_url: Page the file was published on.
        file_modified_at: UTC ISO time the original file was last modified (≈ download time).
        landed_at: UTC ISO time it was copied into landing.
        http_status: HTTP status for downloaded files; ``None`` for manual drops.
    """

    source: str
    period: str
    file_name: str
    landed_path: str
    sha256: str
    size_bytes: int
    method: str
    origin_url: str
    file_modified_at: str
    landed_at: str
    http_status: int | None = None


def sha256_file(path: Path) -> str:
    """Return the hex SHA-256 of a file, read in 1 MiB chunks (memory-safe for big files)."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def read_manifest(landing_root: Path) -> list[ManifestEntry]:
    """Load all manifest entries; returns an empty list if nothing has landed yet."""
    path = landing_root / MANIFEST_NAME
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return [ManifestEntry(**json.loads(line)) for line in handle if line.strip()]


def append_entries(landing_root: Path, entries: list[ManifestEntry]) -> None:
    """Append entries to the manifest, creating it if needed."""
    if not entries:
        return
    landing_root.mkdir(parents=True, exist_ok=True)
    with (landing_root / MANIFEST_NAME).open("a", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(asdict(entry), sort_keys=True) + "\n")
