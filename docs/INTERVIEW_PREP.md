# Interview prep

Likely questions per phase, with short model answers.

## Phase 0: Project skeleton

**Q1. Why did you build it local-first instead of directly on Databricks?**
So anyone can verify it: `git clone` plus `make demo`, with no cloud account. It also lets CI run
the real pipeline on every PR and keeps cloud cost near zero. The cloud is a deployment target;
only config (`UPI_PULSE_LAKE_ROOT`) changes between laptop and Azure.

**Q2. Why keep Spark code in a Python package instead of notebooks?**
Notebooks are hard to unit test, review and reuse. A package can be imported by pytest, Airflow
and Databricks (as a wheel). Notebooks in this repo are thin wrappers that call the package.

**Q3. What does your CI pipeline check, and why does it matter?**
On every PR: ruff lint and format check, a detect-secrets scan, and pytest with coverage (fails
under 80%). Later phases add an end-to-end fixture run, dbt build and terraform validate. Nothing
is merged into `main` unless it's green, so `main` is always deployable.

**Q4. How do you stop secrets leaking into a public repo?**
Three layers: `.env` is gitignored and only `.env.example` with empty values is committed; a
detect-secrets pre-commit hook blocks commits that look like they contain keys; CI runs the same
scan in case a hook was skipped.

**Q5. What is a lockfile and why does CI use `uv sync --locked`?**
The lockfile pins exact versions of every dependency, including transitive ones. `--locked` fails
if `pyproject.toml` and `uv.lock` disagree, so CI and my laptop can't silently drift apart.
