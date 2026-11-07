# ADR-0001: Local-first architecture, cloud as a deployment target

- **Status:** Accepted
- **Date:** 2026-11-07
- **Phase:** 0

## Context
The project must demonstrate PySpark, Delta Lake, dbt, Airflow, Azure and Databricks. But anyone
reviewing it (a recruiter, an interviewer, CI) usually has no Azure or Databricks account, and
cloud resources cost money and can expire (student credits, free-tier limits). If the pipeline
only runs in the cloud, nobody can verify it by cloning the repo, and CI can't test it.

## Decision
Everything runs on a laptop first: local Spark + delta-spark, a file-system lake under
`./data/lake/` (landing/bronze/silver/gold), dbt against local data, and Airflow in Docker.
Azure ADLS Gen2 and Databricks Free Edition are *deployment targets*: the same `upi_pulse`
package runs there, and only configuration changes (`UPI_PULSE_ENV`, and `UPI_PULSE_LAKE_ROOT`
switching from a local path to an `abfss://` URI). See `src/upi_pulse/config.py`.

## Alternatives considered
- **Cloud-only (Databricks notebooks + ADLS)**: fastest to start, but not reproducible without
  an account, costs money, and notebook-only code is hard to unit test.
- **Local-only**: free and simple, but doesn't show the Azure/Databricks skills the target roles ask for.

## Consequences
- Good: `make demo` works from a fresh clone with no credentials; CI runs the real pipeline on
  fixtures; Spark logic lives in an importable, testable package instead of notebooks.
- Good: cloud cost stays near ₹0 because the cloud is only used for deployment runs.
- Trade-off: local Spark differs from Databricks in a few places (no Photon, no Unity Catalog,
  OPTIMIZE/Z-ORDER behaviour). We keep those differences behind `upi_pulse.spark` and document them.
- Revisit if a feature we need exists only on Databricks and has no local equivalent.
