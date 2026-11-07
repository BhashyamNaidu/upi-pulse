# Data sources

Verified on **2026-11-07** from a Windows laptop on an Indian residential connection.
Automated probes used `curl` with the honest User-Agent
`upi-pulse-portfolio-project (+https://github.com/BhashyamNaidu/upi-pulse)` and ≥2 s between requests.
Page structure was also inspected read-only in a normal browser, the way a person would look at it.

## Summary

| # | Source | Reachable by script? | Format | History | Use in project |
|---|---|---|---|---|---|
| 1 | NPCI UPI Product Statistics | ❌ Akamai 403 (pages + JSON API) | Web table, Excel download per FY | FY 2016-17 → Oct 2026 | Monthly UPI totals (NPCI side of reconciliation) |
| 2 | NPCI UPI Ecosystem Statistics | ❌ Akamai 403 | Web table, one `.xlsx` per month per tab | 2022 → Sep 2026 | App market share, P2P/P2M, bank performance |
| 3 | RBI Payment System Indicators (PSI) | ⚠️ Listing page 200, **files behind JS bot challenge** | One `.XLSX` + `.PDF` per month | 12 months on page; older via yearly archive | RBI side of reconciliation |
| 4 | RBI DBIE | ❌ TLS name mismatch from this machine | Web app | — | Not used (PSI covers the need) |
| 5 | data.gov.in | ❌ Akamai 403 on website; API needs key | CSV/JSON API | Unverified | Optional, not used for now |

**Conclusion:** none of the sources allow honest automated downloads of the data files, and the
brief says not to get around bot protection. Ingestion therefore reads from
`data/manual_drop/` (see [ADR-0002](adr/0002-manual-drop-ingestion.md)).

## 1. NPCI UPI Product Statistics

- **URL:** https://www.npci.org.in/product/upi/product-statistics (the old
  `/what-we-do/upi/product-statistics` URL now returns a 404 because the site was restructured)
- **Access:** `robots.txt`, the page and its JSON API (`/api/product-statistic/tab/detail?...`)
  all return **HTTP 403 (Akamai "Access Denied")** to a script. They load normally in a browser.
- **Format:** monthly table, selectable by financial year (`2016-17` … `2026-27`), with a
  **Download** button (Excel).
- **Columns:** `Month` (e.g. `October-2026`), `No. of Banks live on UPI`, `Volume (In Mn.)`,
  `Value (In Cr.)`.
- **Update frequency:** monthly, first days of the next month (October 2026 was created on 2026-11-02).
- **Quirks seen:**
  - Numbers are strings with **inconsistent digit grouping**: Indian (`31,52,929.46`), no commas
    (`22716.07`), and mis-grouped (`29,029,88.05` for April 2026). The parser must strip all
    separators and validate, not trust the grouping.
  - Footnote: *data excludes transactions with debit/credit to the same account from August 2018 onwards*.
  - Units are already millions (volume) and ₹ crore (value), the same as our silver standard.

## 2. NPCI UPI Ecosystem Statistics

- **URL:** https://www.npci.org.in/product/ecosystem-statistics/upi
- **Access:** same Akamai 403 for scripts.
- **Tabs:** Chargeback, Top 50 Member Performance, **UPI Applications**, **P2P and P2M
  Transactions**, Top 15 PSPs, Merchant Category Classification, UPI Statewise Statistics,
  Top 50 Member Vol & Val. Month + year pickers; year options **2022–2026**.
- **Format:** each tab/month has a downloadable `.xlsx`, e.g. `/uploads/upi_p2p_p2m_Sep26_<hash>.xlsx`.
  File names contain a random hash, so they can't be predicted.
- **UPI Applications columns:** Sr.No., Application Name, then Volume (Mn) and Value (Cr) for each of
  *Customer Initiated*, *B2C*, *B2B* and *Total*.
- **P2P and P2M columns:** Month (`Sep-26`), Total volume/value, P2P volume/value, P2M volume/value.
- **Top 50 Member Performance (banks):** the tab exists; its columns (remitter/beneficiary,
  technical decline %) are **still to be confirmed** from a downloaded file.
- **Publication lag:** September 2026 was available on 2026-11-07; October 2026 was not.
- **Quirks seen / documented by NPCI:**
  - App names carry a `#` suffix marking third-party apps (`PhonePe #`, `Google Pay #`); others
    don't (`BHIM`). Names also change over time (`FamApp by Trio #`, `super.money #`).
  - App volume follows **payer-app logic** (credited to the payer's PSP).
  - Apps with < 20,000 transactions are lumped into **"Other Apps"**.
  - From **January 2021** "On-us" transactions not settled via the UPI central system are shown separately.
  - BHIM includes *99# volume. TPAP share excludes cross-border and some new features.
  - Airtel Payments Bank on-us transactions are included in B2B.

## 3. RBI Payment System Indicators

- **URL:** https://www.rbi.org.in/Scripts/PSIUserView.aspx (NPCI's own site links here)
- **Access:** the listing page returns **HTTP 200** to our honest User-Agent and links 12 monthly
  reports (Oct 2025 → Sep 2026). The files live on `rbidocs.rbi.org.in`, which serves a **JavaScript
  bot challenge** (F5 "TSPD") instead of the file, so scripts can't download them.
  `www.rbi.org.in/robots.txt` returns **HTTP 418**, so the crawl policy can't be read.
- **Format:** one `.XLSX` and one `.PDF` per month, with hashed file names
  (e.g. `PSI0920261A41E53EAAEF41EDA7FCB4049F0055DF.XLSX`). Older months are under the page's yearly archive.
- **Columns:** to be confirmed from a downloaded file (expected: UPI volume in lakh and value in ₹ crore,
  per RBI convention, so a **lakh → million conversion** will be needed).
- **Terms:** RBI's Disclaimer page says caching and framing of the site's contents are prohibited
  except as RBI allows, and that the print versions are authoritative. We use the published figures with
  attribution and don't mirror the site.

## 4. RBI DBIE

- **URL:** https://dbie.rbi.org.in/
- **Access:** TLS handshake fails from this machine (`SEC_E_WRONG_PRINCIPAL`, certificate name mismatch).
  We won't disable certificate checks. PSI already gives RBI's monthly UPI totals, so DBIE isn't needed.

## 5. data.gov.in (optional)

- **Access:** website returns Akamai 403 to scripts. The API host (`api.data.gov.in`) needs a free API
  key and a resource ID; no UPI dataset was confirmed. Not used unless we find a dataset that adds something.

## Licence / terms status

| Source | Status |
|---|---|
| NPCI | Terms page (`/terms-and-condition`) rendered **empty** on 2026-11-07; not verified. Data is publicly published official statistics; we cite NPCI as the source. |
| RBI | Disclaimer read (see above). Public statistics, cited; site not mirrored. |
| data.gov.in | Government Open Data Licence – India (not yet used). |

Raw downloaded files are **never committed** (`data/` is gitignored). Only small excerpts used as
test fixtures go in `tests/fixtures/`, each with its source and date in a README.
