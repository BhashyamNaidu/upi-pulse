"""Detect units from column headers and convert to the silver standard.

Silver standard: **volume in millions of transactions**, **value in ₹ crore**.
(1 lakh = 100,000; 1 crore = 10,000,000 = 100 lakh; 1 million = 10 lakh.)

Parsers record the raw header text (``unit_raw``); conversion happens in silver, so a wrong guess
here can be fixed and replayed without touching the parsed data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

Measure = Literal["volume", "value"]
Unit = Literal["thousand", "lakh", "million", "crore", "billion"]

# How many silver-standard units one raw unit is worth.
TO_MILLION_TRANSACTIONS: dict[Unit, Decimal] = {
    "thousand": Decimal("0.001"),
    "lakh": Decimal("0.1"),
    "million": Decimal("1"),
    "crore": Decimal("10"),
    "billion": Decimal("1000"),
}
TO_RUPEE_CRORE: dict[Unit, Decimal] = {
    "thousand": Decimal("0.0001"),
    "lakh": Decimal("0.01"),
    "million": Decimal("0.1"),
    "crore": Decimal("1"),
    "billion": Decimal("100"),
}

_UNIT_PATTERNS: tuple[tuple[Unit, re.Pattern[str]], ...] = (
    ("thousand", re.compile(r"thousand|'000|\b000s?\b")),
    ("lakh", re.compile(r"\blakhs?\b|\blacs?\b|\blkh\b")),
    ("million", re.compile(r"\bmn\b|\bmillions?\b|\bmio\b")),
    ("crore", re.compile(r"\bcr\b|\bcrores?\b")),
    ("billion", re.compile(r"\bbn\b|\bbillions?\b")),
)
_VALUE_HINT = re.compile(r"\bvalue\b|\bamount\b|₹|\brs\b|\binr\b|\brupees?\b")
# Not bare "no"/"number": "No. of Banks live on UPI" is a count of banks, not a volume.
_VOLUME_HINT = re.compile(r"\bvolume\b|\b(no|number)\s+of\s+transactions\b")


@dataclass(frozen=True)
class UnitInfo:
    """What a header says about its column."""

    raw: str
    measure: Measure | None
    unit: Unit | None

    @property
    def is_known(self) -> bool:
        """True when both the measure and the unit were recognised."""
        return self.measure is not None and self.unit is not None


def detect_unit(header: str) -> UnitInfo:
    """Read measure and unit from a header such as ``"Value (In Cr.)"``.

    Value wins over volume when both appear (``"Value of transactions (₹ crore)"``).

    >>> detect_unit("Volume (In Mn.)")
    UnitInfo(raw='Volume (In Mn.)', measure='volume', unit='million')
    """
    text = re.sub(r"[().,\[\]/]", " ", header.lower())
    units = [name for name, pattern in _UNIT_PATTERNS if pattern.search(text)]
    measure: Measure | None
    if _VALUE_HINT.search(text):
        measure = "value"
    elif _VOLUME_HINT.search(text):
        measure = "volume"
    else:
        measure = None
    return UnitInfo(header, measure, units[0] if len(units) == 1 else None)


def to_standard(value: Decimal, info: UnitInfo) -> Decimal:
    """Convert a raw number to the silver standard for its measure.

    Raises:
        ValueError: If the header's measure or unit wasn't recognised; the caller
            quarantines the row.
    """
    if not info.is_known:
        raise ValueError(f"unrecognised unit in header {info.raw!r}")
    table = TO_MILLION_TRANSACTIONS if info.measure == "volume" else TO_RUPEE_CRORE
    return value * table[info.unit]  # type: ignore[index]
