"""Land hand-downloaded files from ``manual_drop/`` into ``landing/`` (see ADR-0002).

Layout in:  ``manual_drop/<source>/<period>/<original file name>``
Layout out: ``landing/source=<source>/period=<period>/sha256=<12 hex>/<original file name>``

Putting the checksum in the path means a revised file never overwrites an earlier one, and the
same bytes always land in the same place. That makes re-runs idempotent.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from upi_pulse.ingestion.manifest import ManifestEntry, append_entries, read_manifest, sha256_file
from upi_pulse.ingestion.sources import (
    DATA_EXTENSIONS,
    SOURCES,
    expected_periods,
    is_valid_period,
)

_IGNORED_NAMES = frozenset({".gitkeep", ".DS_Store", "Thumbs.db", "desktop.ini"})


@dataclass(frozen=True)
class DropFile:
    """A candidate data file found in the drop folder."""

    source: str
    period: str
    path: Path


@dataclass(frozen=True)
class Rejection:
    """Something in the drop folder that could not be landed, and why."""

    path: str
    reason: str


@dataclass
class ScanResult:
    """Valid candidates plus everything rejected during the scan."""

    files: list[DropFile] = field(default_factory=list)
    rejected: list[Rejection] = field(default_factory=list)


@dataclass
class LandingResult:
    """Outcome of one ingest run. Every input file ends up in exactly one list."""

    landed: list[ManifestEntry] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    rejected: list[Rejection] = field(default_factory=list)


def _is_ignored(path: Path) -> bool:
    return path.name in _IGNORED_NAMES or path.name.startswith((".", "~$"))


def scan_drop(drop_dir: Path) -> ScanResult:
    """Walk the drop folder and sort files into valid candidates and rejections.

    Nothing is silently skipped: unknown source folders, malformed period folders, misplaced files
    and unsupported file types are all reported as rejections with a reason.
    """
    result = ScanResult()
    if not drop_dir.exists():
        return result
    for source_dir in sorted(p for p in drop_dir.iterdir() if not _is_ignored(p)):
        rel = source_dir.relative_to(drop_dir).as_posix()
        if not source_dir.is_dir():
            result.rejected.append(Rejection(rel, "file is not inside a <source>/<period>/ folder"))
            continue
        source = SOURCES.get(source_dir.name)
        if source is None:
            result.rejected.append(
                Rejection(rel, f"unknown source; expected one of {sorted(SOURCES)}")
            )
            continue
        for period_dir in sorted(p for p in source_dir.iterdir() if not _is_ignored(p)):
            prel = period_dir.relative_to(drop_dir).as_posix()
            if not period_dir.is_dir():
                result.rejected.append(Rejection(prel, "file is not inside a <period>/ folder"))
                continue
            if not is_valid_period(source, period_dir.name):
                expected = "YYYY-MM" if source.cadence == "monthly" else "FYYYYY-YY"
                result.rejected.append(
                    Rejection(prel, f"invalid period folder; expected {expected}")
                )
                continue
            for path in sorted(p for p in period_dir.iterdir() if not _is_ignored(p)):
                frel = path.relative_to(drop_dir).as_posix()
                if path.is_dir():
                    result.rejected.append(Rejection(frel, "unexpected sub-folder"))
                elif path.suffix.lower() not in DATA_EXTENSIONS:
                    allowed = ", ".join(sorted(DATA_EXTENSIONS))
                    result.rejected.append(
                        Rejection(frel, f"unsupported file type; allowed: {allowed}")
                    )
                else:
                    result.files.append(DropFile(source.name, period_dir.name, path))
    return result


def _iso(ts: datetime) -> str:
    return ts.astimezone(UTC).isoformat(timespec="seconds")


def land_drop(
    drop_dir: Path,
    landing_root: Path,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> LandingResult:
    """Copy new files from the drop folder into landing and record them in the manifest.

    Idempotent: a file whose (source, period, sha256) is already in the manifest is skipped, so
    running this twice lands nothing new the second time. Identical bytes appearing under two
    different periods are rejected, because that almost always means a file was saved into the
    wrong month folder.

    Args:
        drop_dir: Root of the manual-drop folder.
        landing_root: Root of the landing layer.
        now: Clock, injectable for deterministic tests.

    Returns:
        What was landed, skipped (already present) and rejected (with reasons).
    """
    scan = scan_drop(drop_dir)
    result = LandingResult(rejected=list(scan.rejected))
    existing = read_manifest(landing_root)
    seen = {(e.source, e.period, e.sha256) for e in existing}
    period_by_checksum = {(e.source, e.sha256): e.period for e in existing}

    for drop in scan.files:
        rel = drop.path.relative_to(drop_dir).as_posix()
        checksum = sha256_file(drop.path)
        if (drop.source, drop.period, checksum) in seen:
            result.skipped.append(rel)
            continue
        other_period = period_by_checksum.get((drop.source, checksum))
        if other_period is not None and other_period != drop.period:
            result.rejected.append(
                Rejection(rel, f"identical file already landed for period {other_period}")
            )
            continue

        target_rel = (
            f"source={drop.source}/period={drop.period}/sha256={checksum[:12]}/{drop.path.name}"
        )
        target = landing_root / target_rel
        if not (target.exists() and sha256_file(target) == checksum):
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_name(target.name + ".partial")
            shutil.copy2(drop.path, tmp)
            tmp.replace(target)  # atomic rename: readers never see half-copied files

        entry = ManifestEntry(
            source=drop.source,
            period=drop.period,
            file_name=drop.path.name,
            landed_path=target_rel,
            sha256=checksum,
            size_bytes=drop.path.stat().st_size,
            method="manual_drop",
            origin_url=SOURCES[drop.source].origin_url,
            file_modified_at=_iso(datetime.fromtimestamp(drop.path.stat().st_mtime, UTC)),
            landed_at=_iso(now()),
        )
        append_entries(landing_root, [entry])
        result.landed.append(entry)
        seen.add((drop.source, drop.period, checksum))
        period_by_checksum[(drop.source, checksum)] = drop.period
    return result


def missing_periods(drop_dir: Path, start: str, end: str) -> dict[str, list[str]]:
    """Return, per required source, the periods in ``start``..``end`` with no valid file yet."""
    present = {(f.source, f.period) for f in scan_drop(drop_dir).files}
    missing: dict[str, list[str]] = {}
    for source in SOURCES.values():
        if not source.required:
            continue
        gaps = [p for p in expected_periods(source, start, end) if (source.name, p) not in present]
        if gaps:
            missing[source.name] = gaps
    return missing
