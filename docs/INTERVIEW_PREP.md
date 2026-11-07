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

## Phase 1: Source discovery + ingestion

**Q1. The sources blocked your scraper. Why not just spoof a browser User-Agent?**
Because that's getting around the publisher's access control on purpose. Akamai returned 403 and RBI
serves a JavaScript bot challenge, which is a clear "no" to automated access. I documented it in
ADR-0002 and switched to a manual-drop folder. From there the pipeline is fully automated. In
production I'd ask for a data feed or an API key.

**Q2. How is your ingestion idempotent?**
Each file is identified by (source, period, SHA-256). Before landing, I check the manifest; if that
key exists, the file is skipped. Landed paths include the checksum, so re-landing the same bytes goes
to the same place, and a revised file lands next to the old one instead of overwriting it. There's a
test that runs ingest twice and asserts the manifest is unchanged.

**Q3. What happens if the job crashes halfway through copying a file?**
It copies to a `.partial` file and then does an atomic rename, so readers never see a half file. If it
crashes after the copy but before the manifest write, the next run finds the target already has the
right checksum and just writes the manifest entry. Both cases are covered by tests.

**Q4. How do you make sure no data is silently lost?**
Every file found in the drop folder is put in exactly one bucket: landed, skipped or rejected with a
reason (wrong folder, bad period name, unsupported type, same file in two months). The CLI prints
every rejection and exits non-zero, and the counts go to `run_metrics.json`.

**Q5. Why keep raw files untouched in a landing zone instead of parsing on download?**
So parsing is replayable. If I find a parser bug, like NPCI's mis-grouped number `29,029,88.05`,
I fix the parser and re-run from landing without re-downloading. The checksum also proves the file is
exactly what the publisher released.
