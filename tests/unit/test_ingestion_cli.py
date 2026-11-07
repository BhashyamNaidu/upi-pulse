"""CLI tests. File contents are SYNTHETIC placeholder bytes in a temp folder."""

import json

import pytest

from upi_pulse.ingestion.__main__ import main


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("UPI_PULSE_ENV", "local")
    monkeypatch.setenv("UPI_PULSE_LAKE_ROOT", (tmp_path / "lake").as_posix())
    monkeypatch.setenv("UPI_PULSE_DROP_DIR", (tmp_path / "drop").as_posix())
    monkeypatch.setenv("UPI_PULSE_METRICS_PATH", (tmp_path / "metrics.json").as_posix())
    return tmp_path


def _put(root, rel, content=b"SYNTHETIC"):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_ingest_lands_and_records_metrics(env, capsys):
    _put(env / "drop", "npci_apps/2026-09/apps.xlsx")

    assert main(["ingest"]) == 0
    assert "1 landed, 0 already present, 0 rejected" in capsys.readouterr().out
    metrics = json.loads((env / "metrics.json").read_text())["steps"]["ingest"]
    assert metrics["files_landed"] == 1 and metrics["bytes_landed"] == len(b"SYNTHETIC")

    assert main(["ingest", "--no-metrics"]) == 0
    assert "0 landed, 1 already present" in capsys.readouterr().out


def test_ingest_fails_on_rejections(env, capsys):
    _put(env / "drop", "npci_apps/2026-09/report.pdf")
    assert main(["ingest", "--no-metrics"]) == 1
    assert "REJECTED npci_apps/2026-09/report.pdf" in capsys.readouterr().out


def test_ingest_refuses_cloud_env_for_now(env, monkeypatch):
    monkeypatch.setenv("UPI_PULSE_ENV", "cloud")
    assert main(["ingest"]) == 2


def test_status_lists_missing_then_passes(env, capsys):
    assert main(["status", "--from", "2026-09", "--to", "2026-09"]) == 1
    out = capsys.readouterr().out
    assert "4 file(s) still missing" in out and "rbi_psi" in out

    for rel in (
        "npci_apps/2026-09/a.xlsx",
        "npci_p2p_p2m/2026-09/b.xlsx",
        "rbi_psi/2026-09/c.xlsx",
        "npci_product/FY2026-27/d.xlsx",
    ):
        _put(env / "drop", rel, rel.encode())
    assert main(["status", "--from", "2026-09", "--to", "2026-09"]) == 0
    assert "All required files present" in capsys.readouterr().out
