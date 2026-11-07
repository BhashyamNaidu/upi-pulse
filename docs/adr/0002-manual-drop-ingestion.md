# ADR-0002: Ingest from a manual-drop folder because sources block automated downloads

- **Status:** Accepted
- **Date:** 2026-11-07
- **Phase:** 1

## Context
Source discovery (docs/DATA_SOURCES.md) found that every data file we need is protected against
automated access:
- NPCI pages and JSON APIs return Akamai HTTP 403 to a script with an honest User-Agent.
- RBI PSI files on `rbidocs.rbi.org.in` sit behind a JavaScript bot challenge.

The project rules forbid getting around this (fake browser headers, headless browsers that solve
challenges, captcha workarounds). Respecting a publisher's bot protection is also the professional
thing to do.

## Decision
A person downloads the official files by hand into
`data/manual_drop/<source>/<YYYY-MM>/<original file name>`. The ingestion step treats that folder as
the "source": it copies each file untouched into `landing/source=<name>/period=<YYYY-MM>/`, computes
SHA-256, and writes the same manifest entry (origin URL, time collected, checksum, size,
`method=manual_drop`) an HTTP download would. Everything after landing stays the same.

The ingestion code keeps a pluggable `Fetcher` interface, so an HTTP fetcher can be added later if a
source opens up (for example an official API) without touching the downstream layers.

## Alternatives considered
- **Spoof a browser User-Agent / use a headless browser:** works technically, but breaks the publisher's
  access controls. Rejected.
- **Copy numbers from the web tables into CSVs:** error-prone and loses the original file, so the
  checksum and audit trail would be meaningless. Rejected.
- **Use third-party mirrors (Kaggle, GitHub datasets):** unknown provenance and freshness, which
  undermines the NPCI-vs-RBI reconciliation. Rejected.

## Consequences
- Good: fully honest provenance. Every landed file is byte-for-byte the official file, with a checksum.
- Good: idempotency is easy. A file with an already-seen checksum is skipped.
- Trade-off: monthly refresh needs a few minutes of human work (about four files a month). In
  production this would be a supplier data feed or an agreed API; we note it under limitations.
- Trade-off: Airflow's "ingest" task becomes "scan manual_drop + land new files", and the freshness
  check flags when nobody has dropped the latest month.
- Revisit if NPCI, RBI or data.gov.in publish an open API that allows automated access.
