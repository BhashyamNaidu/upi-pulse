import json
from datetime import UTC, datetime

from upi_pulse.ingestion.manifest import (
    MANIFEST_NAME,
    ManifestEntry,
    append_entries,
    read_manifest,
    sha256_file,
)
from upi_pulse.metrics import record_step


def test_sha256_matches_known_digest(tmp_path):
    path = tmp_path / "abc.bin"
    path.write_bytes(b"abc")
    # Published NIST FIPS 180-2 test vector for SHA-256("abc"), not a secret.
    expected = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"  # noqa: E501  # pragma: allowlist secret
    assert sha256_file(path) == expected


def test_manifest_round_trip(tmp_path):
    assert read_manifest(tmp_path) == []
    append_entries(tmp_path, [])
    assert not (tmp_path / MANIFEST_NAME).exists()

    entry = ManifestEntry(
        "npci_apps", "2026-09", "a.xlsx", "source=npci_apps/x/a.xlsx", "0" * 64, 3,
        "manual_drop", "https://example.org", "2026-11-01T00:00:00+00:00",
        "2026-11-07T00:00:00+00:00",
    )  # fmt: skip
    append_entries(tmp_path, [entry])
    append_entries(tmp_path, [entry])
    assert read_manifest(tmp_path) == [entry, entry]


def test_record_step_merges_steps(tmp_path):
    path = tmp_path / "metrics" / "run_metrics.json"
    when = datetime(2026, 11, 7, tzinfo=UTC)
    record_step(path, "ingest", {"files_landed": 2}, now=when)
    doc = record_step(path, "silver", {"rows_out": 10}, now=when)

    assert doc == json.loads(path.read_text())
    assert doc["steps"]["ingest"] == {"files_landed": 2, "recorded_at": "2026-11-07T00:00:00+00:00"}
    assert doc["steps"]["silver"]["rows_out"] == 10
