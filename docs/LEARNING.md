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

## Phase 1: Source discovery + ingestion

**Respecting bot protection.** NPCI's site is behind Akamai, a firewall that returned HTTP 403 to
my script even with an honest User-Agent. RBI's files sit behind an F5 JavaScript challenge. I could
fake a browser, but that's getting around the publisher's access control, so I didn't
(ADR-0002). In a real job the fix is a data-sharing agreement or an official API, not a cleverer
scraper.

**Manual drop.** Instead, a person downloads the official files into
`data/manual_drop/<source>/<period>/`. From that point on the pipeline is fully automated and
treats the folder like any other source. It's a common pattern in real companies too, where partners
drop files on an SFTP server or a shared bucket.

**Landing zone.** The first lake layer holds files *exactly* as received: no renaming, no opening and
re-saving. If a parser bug shows up later, I can re-parse the original bytes without going back to
the source.

**SHA-256 checksum.** A fingerprint of a file's bytes. Change one byte and the checksum changes
completely. I use it to (1) detect a file I've already landed, (2) spot when NPCI or RBI revise a
file, and (3) catch mistakes, like the same file saved into two month folders.

**Content-addressed paths.** Landed files go to `.../sha256=<first 12 hex>/<file name>`. Because the
checksum is in the path, a revised file can never overwrite the earlier version, and the same bytes
always map to the same place.

**Idempotency.** Running a step twice gives the same result as running it once. Here, a file whose
(source, period, checksum) is already in the manifest is skipped, so a second `make ingest` lands
nothing. The `test_rerun_is_idempotent` test checks this, down to the manifest being byte-for-byte unchanged.

**Atomic writes.** Each file is copied to `name.partial` and then renamed. On one filesystem a rename
is all-or-nothing, so no later step ever reads a half-copied file. If the process crashes after the
copy but before the manifest write, the next run sees the file is already correct and just records it.

**Manifest (JSON Lines).** An append-only log with one JSON object per line: source, period, file
name, checksum, size, origin URL and timestamps. It's the audit trail ("where did this number come
from?") and it can be read straight into Spark.

**Financial year periods.** NPCI's product statistics come as one file per Indian financial year
(April to March), so that source uses `FY2025-26` periods. `fiscal_year_of(2026, 3)` is `FY2025-26`,
but April 2026 starts `FY2026-27`.

**No silent drops.** Every file in the drop folder ends up landed, skipped (already present) or
rejected with a reason. `make ingest` exits with code 1 when anything is rejected, so Airflow will
flag it later.

**Parsing numbers you can't trust.** NPCI publishes numbers as text, and the commas are
inconsistent: `31,52,929.46` (Indian grouping), `22716.07` (none), and even `29,029,88.05`
(mis-grouped). `parse_number` strips separators to get the value, but records the *grouping* it
saw, so a mis-grouped value is parsed and flagged `needs_review` rather than silently "fixed".
`Decimal` is used instead of `float` so ₹ crore amounts don't pick up binary rounding errors.

**Units: lakh, crore, million.** 1 lakh = 100,000, 1 crore = 100 lakh = 10 million, 1 million =
10 lakh. Silver stores volume in millions and value in ₹ crore. Parsers only *record* the header
text (`unit_raw`); conversion happens in silver, so a wrong unit guess can be fixed and replayed.
A header with two units, or none, isn't guessed. It's rejected so the row can be quarantined.

**Totals rows.** Tables often end with a "Total" row. If it's treated like any other row, sums
double count. Parsers tag it `row_kind="total"` instead of deleting it, so we can also check that
the detail rows add up to the published total.
