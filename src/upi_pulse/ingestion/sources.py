"""Registry of data sources and the period labels each one uses.

Monthly sources use ``YYYY-MM`` periods. NPCI's product statistics are published as one file per
Indian financial year (April-March), so that source uses ``FYYYYY-YY`` periods, e.g. ``FY2025-26``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

Cadence = Literal["monthly", "fiscal_year"]

_MONTH_RE = re.compile(r"^(?P<year>\d{4})-(?P<month>\d{2})$")
_FY_RE = re.compile(r"^FY(?P<start>\d{4})-(?P<end>\d{2})$")

DATA_EXTENSIONS: frozenset[str] = frozenset({".xlsx", ".xls", ".csv"})


@dataclass(frozen=True)
class Source:
    """One upstream dataset.

    Attributes:
        name: Folder name under ``manual_drop/`` and ``landing/source=<name>``.
        description: Human-readable description.
        origin_url: Page the file is downloaded from (recorded in the manifest).
        cadence: Whether periods are months or financial years.
        required: Whether ``status`` should demand every period in the target window.
    """

    name: str
    description: str
    origin_url: str
    cadence: Cadence
    required: bool = True


_NPCI_ECOSYSTEM = "https://www.npci.org.in/product/ecosystem-statistics/upi"

SOURCES: dict[str, Source] = {
    s.name: s
    for s in (
        Source(
            "npci_product",
            "NPCI UPI product statistics (monthly totals, one file per FY)",
            "https://www.npci.org.in/product/upi/product-statistics",
            "fiscal_year",
        ),
        Source("npci_apps", "NPCI UPI Applications (app-wise)", _NPCI_ECOSYSTEM, "monthly"),
        Source("npci_p2p_p2m", "NPCI P2P and P2M transactions", _NPCI_ECOSYSTEM, "monthly"),
        Source(
            "npci_banks",
            "NPCI Top 50 member performance (bank-wise)",
            _NPCI_ECOSYSTEM,
            "monthly",
            required=False,
        ),
        Source(
            "rbi_psi",
            "RBI Payment System Indicators",
            "https://www.rbi.org.in/Scripts/PSIUserView.aspx",
            "monthly",
        ),
    )
}


def parse_month(label: str) -> tuple[int, int]:
    """Parse a ``YYYY-MM`` label into ``(year, month)``.

    Raises:
        ValueError: If the label is malformed or the month is out of range.
    """
    match = _MONTH_RE.match(label)
    if not match or not 1 <= int(match["month"]) <= 12:
        raise ValueError(f"Expected a YYYY-MM month, got {label!r}")
    return int(match["year"]), int(match["month"])


def fiscal_year_of(year: int, month: int) -> str:
    """Return the Indian financial-year label (April-March) containing a month.

    >>> fiscal_year_of(2026, 3)
    'FY2025-26'
    >>> fiscal_year_of(2026, 4)
    'FY2026-27'
    """
    start = year if month >= 4 else year - 1
    return f"FY{start}-{(start + 1) % 100:02d}"


def is_valid_period(source: Source, label: str) -> bool:
    """Return whether ``label`` is a well-formed period for this source's cadence."""
    if source.cadence == "monthly":
        try:
            parse_month(label)
        except ValueError:
            return False
        return True
    match = _FY_RE.match(label)
    return bool(match) and (int(match["start"]) + 1) % 100 == int(match["end"])


def months_between(start: str, end: str) -> list[str]:
    """List every ``YYYY-MM`` month from ``start`` to ``end`` inclusive.

    Raises:
        ValueError: If either label is malformed or ``start`` is after ``end``.
    """
    year, month = parse_month(start)
    end_key = parse_month(end)
    if (year, month) > end_key:
        raise ValueError(f"start {start} is after end {end}")
    months: list[str] = []
    while (year, month) <= end_key:
        months.append(f"{year:04d}-{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return months


def expected_periods(source: Source, start: str, end: str) -> list[str]:
    """Return the period labels a source needs to cover the months ``start``..``end``."""
    months = months_between(start, end)
    if source.cadence == "monthly":
        return months
    fiscal_years = (fiscal_year_of(*parse_month(m)) for m in months)
    return list(dict.fromkeys(fiscal_years))
