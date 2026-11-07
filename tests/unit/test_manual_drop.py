"""Landing tests.

All file contents here are SYNTHETIC placeholder bytes written to a temp folder. They test file
handling only (paths, checksums, idempotency) and never reach the lake, dashboard or README.
"""

from datetime import UTC, datetime
from pathlib import Path

from upi_pulse.ingestion.manifest import MANIFEST_NAME, read_manifest, sha256_file
from upi_pulse.ingestion.manual_drop import land_drop, missing_periods, scan_drop

FIXED_NOW = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)


def _clock() -> datetime:
    return FIXED_NOW


def _put(root: Path, rel: str, content: bytes = b"SYNTHETIC test bytes") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _reasons(result) -> dict[str, str]:
    return {r.path: r.reason for r in result.rejected}


def test_missing_drop_dir_is_empty(tmp_path):
    scan = scan_drop(tmp_path / "nope")
    assert scan.files == [] and scan.rejected == []


def test_scan_reports_every_problem_instead_of_dropping_it(tmp_path):
    _put(tmp_path, "stray.xlsx")
    _put(tmp_path, "unknown_src/2026-09/a.xlsx")
    _put(tmp_path, "npci_apps/loose.xlsx")
    _put(tmp_path, "npci_apps/Sep-26/a.xlsx")
    _put(tmp_path, "npci_apps/2026-09/report.pdf")
    _put(tmp_path, "npci_apps/2026-09/nested/a.xlsx")
    _put(tmp_path, "npci_apps/2026-09/good.xlsx")
    _put(tmp_path, "npci_apps/2026-09/~$good.xlsx")  # Excel lock file: ignored
    _put(tmp_path, "npci_apps/.gitkeep")  # ignored

    scan = scan_drop(tmp_path)

    assert [(f.source, f.period, f.path.name) for f in scan.files] == [
        ("npci_apps", "2026-09", "good.xlsx")
    ]
    reasons = _reasons(scan)
    assert "not inside" in reasons["stray.xlsx"]
    assert "unknown source" in reasons["unknown_src"]
    assert "not inside" in reasons["npci_apps/loose.xlsx"]
    assert "invalid period" in reasons["npci_apps/Sep-26"]
    assert "unsupported file type" in reasons["npci_apps/2026-09/report.pdf"]
    assert "sub-folder" in reasons["npci_apps/2026-09/nested"]
    assert len(reasons) == 6


def test_landing_copies_bytes_untouched_and_writes_manifest(tmp_path):
    drop, landing = tmp_path / "drop", tmp_path / "landing"
    original = _put(drop, "rbi_psi/2026-09/PSI092026.XLSX", b"SYNTHETIC psi bytes")

    result = land_drop(drop, landing, now=_clock)

    assert len(result.landed) == 1
    entry = result.landed[0]
    landed_file = landing / entry.landed_path
    assert landed_file.read_bytes() == original.read_bytes()
    assert entry.sha256 == sha256_file(original)
    assert entry.landed_path.startswith("source=rbi_psi/period=2026-09/sha256=")
    assert entry.method == "manual_drop" and entry.http_status is None
    assert entry.origin_url.startswith("https://www.rbi.org.in/")
    assert entry.landed_at == "2026-11-07T12:00:00+00:00"
    assert read_manifest(landing) == [entry]
    assert not list(landing.rglob("*.partial"))


def test_rerun_is_idempotent(tmp_path):
    drop, landing = tmp_path / "drop", tmp_path / "landing"
    _put(drop, "npci_apps/2026-09/apps.xlsx")
    _put(drop, "npci_product/FY2026-27/product.xlsx", b"SYNTHETIC other bytes")

    first = land_drop(drop, landing, now=_clock)
    manifest_after_first = (landing / MANIFEST_NAME).read_text()
    second = land_drop(drop, landing, now=_clock)

    assert len(first.landed) == 2
    assert second.landed == [] and len(second.skipped) == 2 and second.rejected == []
    assert (landing / MANIFEST_NAME).read_text() == manifest_after_first
    assert len([p for p in landing.rglob("*") if p.is_file()]) == 3  # 2 files + manifest


def test_revised_file_lands_alongside_previous_version(tmp_path):
    drop, landing = tmp_path / "drop", tmp_path / "landing"
    path = _put(drop, "npci_apps/2026-09/apps.xlsx", b"SYNTHETIC v1")
    land_drop(drop, landing, now=_clock)
    path.write_bytes(b"SYNTHETIC v2 revised")

    result = land_drop(drop, landing, now=_clock)

    assert len(result.landed) == 1
    entries = read_manifest(landing)
    assert len({e.sha256 for e in entries}) == 2
    assert all((landing / e.landed_path).exists() for e in entries)


def test_same_file_in_two_months_is_rejected(tmp_path):
    drop, landing = tmp_path / "drop", tmp_path / "landing"
    _put(drop, "npci_apps/2026-08/apps.xlsx", b"SYNTHETIC same bytes")
    _put(drop, "npci_apps/2026-09/apps.xlsx", b"SYNTHETIC same bytes")

    result = land_drop(drop, landing, now=_clock)

    assert [(e.period) for e in result.landed] == ["2026-08"]
    assert "already landed for period 2026-08" in _reasons(result)["npci_apps/2026-09/apps.xlsx"]


def test_recovers_when_copy_finished_but_manifest_was_not_written(tmp_path):
    drop, landing = tmp_path / "drop", tmp_path / "landing"
    _put(drop, "npci_apps/2026-09/apps.xlsx")
    land_drop(drop, landing, now=_clock)
    (landing / MANIFEST_NAME).unlink()  # simulate a crash right after the copy

    result = land_drop(drop, landing, now=_clock)

    assert len(result.landed) == 1
    assert len(read_manifest(landing)) == 1


def test_missing_periods_ignores_optional_sources(tmp_path):
    _put(tmp_path, "npci_apps/2026-08/a.xlsx")
    _put(tmp_path, "npci_product/FY2026-27/p.xlsx", b"SYNTHETIC p")

    missing = missing_periods(tmp_path, "2026-08", "2026-09")

    assert missing == {
        "npci_apps": ["2026-09"],
        "npci_p2p_p2m": ["2026-08", "2026-09"],
        "rbi_psi": ["2026-08", "2026-09"],
    }
    assert "npci_banks" not in missing
