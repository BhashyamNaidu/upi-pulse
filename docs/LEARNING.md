# Learning log

Plain-language notes on every concept used, phase by phase, so I can explain any line of this repo.

## Phase 0: Project skeleton

**Lakehouse and medallion layers.** A lakehouse stores data as files in cheap storage (a folder,
or Azure Data Lake) but adds database features on top (transactions, schemas, MERGE) using a
table format like Delta Lake. "Medallion" means data moves through layers: *landing* (raw files
exactly as downloaded), *bronze* (parsed but untouched), *silver* (cleaned, typed, deduplicated),
*gold* (business-ready tables for dashboards). Each layer can be rebuilt from the one before it.

**Local-first.** The whole pipeline runs on my laptop; the cloud is just another place to run the
same code. Only configuration changes, never the code (ADR-0001). That's why `config.py` reads the
lake root from an environment variable instead of hard-coding a path.

**`src/` layout.** The package lives in `src/upi_pulse/`, not the repo root. Tests then import the
*installed* package, which catches packaging mistakes early and keeps Spark logic importable from
Airflow, Databricks and tests alike.

**uv and the lockfile.** `pyproject.toml` lists the dependencies I asked for; `uv.lock` records
the exact version of every package, including sub-dependencies. CI runs `uv sync --locked`, so it
fails if the lock is out of date, and everyone gets identical versions.

**ruff.** One fast tool that does both linting (finding bugs and bad patterns, such as unused
imports and missing docstrings) and formatting (consistent code style). Rules are in `pyproject.toml`.

**pre-commit hooks.** Scripts git runs before each commit. If ruff, the whitespace fixers or
detect-secrets fail, the commit is blocked, so problems get caught on my machine, not in review.

**detect-secrets and the baseline.** Scans files for things that look like passwords, keys or
tokens. `.secrets.baseline` records known false positives so they don't block every commit; a
*new* finding fails both the hook and the CI step.

**CI (GitHub Actions).** Every pull request automatically runs lint, the secret scan and tests on
a clean Ubuntu machine. A PR is merged only when CI is green, so `main` always works.

**Test coverage.** Coverage measures which lines and branches of `src/upi_pulse/` the tests ran.
`--cov-fail-under=80` makes the test run fail if coverage drops below 80%.

**Conventional Commits.** Commit messages start with a type (`feat:`, `fix:`, `test:`, `docs:`,
`ci:`, `chore:`, `refactor:`), so history is readable and release notes can be built from it.

**ADR (Architecture Decision Record).** A short note per important choice: context, decision,
alternatives, consequences. It answers "why did you do it this way?" months later.
