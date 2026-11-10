# Progress

> Read this first at the start of every session.

## Status
| Phase | Status | Branch | Tag |
|---|---|---|---|
| 0. Project skeleton | ✅ Done (PR #1) | `phase-0-skeleton` | — |
| 1. Source discovery + ingestion | 🔄 In progress: discovery done, waiting on manual downloads | `phase-1-ingestion` | — |
| 2. Bronze → Silver (PySpark + Delta) | Not started | | v0.1.0 |
| 3. Gold with dbt + data quality | Not started | | |
| 4. Orchestration + CI | Not started | | v0.2.0 |
| 5. Cloud: Azure ADLS + Databricks | Not started | | |
| 6. Dashboards, polish, write-up | Not started | | v1.0.0 |

## Phase 0: what was done
- Public repo `BhashyamNaidu/upi-pulse`, `.gitignore`, `.gitattributes` (LF line endings).
- `pyproject.toml` managed by **uv**, Python 3.11, ruff (lint + format), pytest + pytest-cov (fails under 80%).
- `upi_pulse.config`: environment-driven lake root (local path or `abfss://`).
- pre-commit: ruff, ruff-format, detect-secrets, end-of-file, trailing-whitespace, yaml/toml checks.
- Makefile with every target from the brief (future ones fail loudly with "not implemented yet").
- GitHub Actions CI: lint, secret scan, tests with coverage report.
- Docs: this file, LEARNING.md, INTERVIEW_PREP.md, ADR template, ADR-0001.

## Next: Phase 1
1. Verify NPCI product stats, NPCI ecosystem stats (app-wise, P2P/P2M, bank-wise), RBI DBIE /
   payment system indicators, data.gov.in. Check robots.txt, terms, formats and history depth.
2. Write `docs/DATA_SOURCES.md` and **report back before writing scrapers** if anything is blocked.

## Local environment (checked 2026-11-07, Windows 11)
| Tool | Status |
|---|---|
| git, gh (authenticated), Python 3.11.9, Terraform 1.15.6, Docker 29.8 | Installed |
| uv 0.13.7 | Installed via `python -m pip install --user uv` |
| Docker daemon | Not running (start Docker Desktop before Phase 4) |
| Java | Only 25 installed; **Spark 3.5 needs Java 17** (needed from Phase 2) |
| GNU make | Missing |
| Azure CLI | Missing (needed in Phase 5) |

## Phase 1: progress so far (2026-11-07)
- ✅ Source discovery written up in `docs/DATA_SOURCES.md`.
- ✅ ADR-0002: every source blocks automated downloads (Akamai 403 / JS bot challenge), so ingestion
  reads from `data/manual_drop/`.
- ✅ Target window agreed: **2024-10 → 2026-09 (24 months)**. Checklist: `docs/MANUAL_DOWNLOAD.md`.
- ✅ Landing code: `upi_pulse.ingestion` (source registry, SHA-256 manifest, idempotent atomic
  landing, `make ingest`, `make drop-status`). 39 unit tests, 99% coverage.
- ⏳ Waiting for Bhashyam to download the 76 files (`make drop-status` lists what's missing).
- ✅ Format-agnostic parsing helpers (2026-11-10): `parse_number` (tested on real NPCI strings),
  unit detection/conversion (`normalisation/units.py`), totals detection and the tidy row contract
  (`parsing/tidy.py`). The tidy table adds `row_kind` (`detail`/`total`) so totals are separated,
  not dropped. 91 tests, 99.4% coverage.
- ⏳ Then: layout-specific parsers per source, tests on real fixture excerpts, Phase 1 PR.

## Blockers / open questions
- **Manual downloads needed** before parsers can be written against real files. On 2026-11-10 the
  drop folder had 0 of 75 required files.
- **pre-commit hooks not installed:** the project path makes a venv file 262 characters long
  (Windows limit 260). Fix: move the project to a short path such as `C:\code\upi-pulse`, or
  enable `LongPathsEnabled` (admin). `git config --global core.longpaths true` is set but only
  affects git.
- Bank performance (Top 50 Member Performance) columns not confirmed yet.
- Java 17 must be installed before Phase 2.
