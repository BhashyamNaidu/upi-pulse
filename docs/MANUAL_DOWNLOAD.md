# Manual download checklist

Every source blocks automated downloads ([ADR-0002](adr/0002-manual-drop-ingestion.md)), so the
official files are downloaded by hand. **Target window: 2024-10 → 2026-09 (24 months).**

Run `make drop-status` at any time to see exactly which files are still missing.

## Folder layout

```
data/manual_drop/
├── npci_product/   FY2024-25/  FY2025-26/  FY2026-27/      ← one Excel per financial year
├── npci_apps/      2024-10/ … 2026-09/                      ← one .xlsx per month
├── npci_p2p_p2m/   2024-10/ … 2026-09/                      ← one .xlsx per month
├── npci_banks/     2026-09/   (one month first, to check columns)
└── rbi_psi/        2024-10/ … 2026-09/                      ← one .XLSX per month
```

Rules:
- **Keep the original file name.** Don't rename, open-and-resave, or convert. The pipeline records a
  SHA-256 checksum of the exact bytes.
- One data file per folder. If NPCI or RBI publish a revised file, replace the old one in the folder;
  the old version is already kept in the lake's landing zone as history.
- The `period` folder is the month the **data is about**, not the month you downloaded it.

## Where to click

### `npci_product`: UPI Product Statistics (3 files)
1. Open https://www.npci.org.in/product/upi/product-statistics → **Monthly Statistics** tab.
2. Choose financial year **2024-25** → **Download**. Save into `npci_product/FY2024-25/`.
3. Repeat for **2025-26** and **2026-27**.

### `npci_apps`: UPI Applications (24 files)
1. Open https://www.npci.org.in/product/ecosystem-statistics/upi → **UPI Applications** tab.
2. Pick month + year (start with **Oct 2024**) → **Download**. Save into `npci_apps/2024-10/`.
3. Repeat for every month up to **Sep 2026**.
   If a month has no data in the picker, try **Show archived**, and note any month that's genuinely
   missing in `docs/PROGRESS.md`.

### `npci_p2p_p2m`: P2P and P2M Transactions (24 files)
Same page → **P2P and P2M Transactions** tab → same steps, into `npci_p2p_p2m/<YYYY-MM>/`.

### `npci_banks`: Top 50 Member Performance (1 file for now)
Same page → **Top 50 Member Performance** tab → **Sep 2026** → Download into `npci_banks/2026-09/`.
I'll check the columns (remitter/beneficiary, technical decline %) before asking for the rest.

### `rbi_psi`: RBI Payment System Indicators (24 files)
1. Open https://www.rbi.org.in/Scripts/PSIUserView.aspx.
2. For each month, click the **XLSX** link (not the PDF). Save into `rbi_psi/<YYYY-MM>/`.
   Use the month the report is *for*: the September 2026 report goes in `rbi_psi/2026-09/`.
3. Months before Oct 2025 are under the page's year / archive selector.

## Total
3 + 24 + 24 + 1 + 24 = **76 files**. After that, keeping it current is about 4 files a month.
