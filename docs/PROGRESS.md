# Progress

> Read this first at the start of every session.

## Status
| Phase | Status | Branch | Tag |
|---|---|---|---|
| 0. Project skeleton | ✅ Done | `phase-0-skeleton` | — |
| 1. Source discovery + ingestion | ⏭️ Next | `phase-1-ingestion` | — |
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

## Blockers / open questions
- None for Phase 1. Java 17 must be installed before Phase 2.
