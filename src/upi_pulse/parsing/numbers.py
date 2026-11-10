"""Parse numbers as NPCI and RBI actually publish them.

Seen in real NPCI data (2026-11-07): Indian grouping ``31,52,929.46``, no grouping ``22716.07``
and mis-grouped ``29,029,88.05``. Separators can't be trusted, so we strip them and keep the digits,
but record *how* the raw value looked. A mis-grouped value is parsed and flagged for review,
never silently "fixed" or dropped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Literal

Grouping = Literal["none", "indian", "western", "irregular"]

_INDIAN = re.compile(r"^\d{1,2}(,\d{2})*,\d{3}(\.\d+)?$")
_WESTERN = re.compile(r"^\d{1,3}(,\d{3})+(\.\d+)?$")
_PLAIN = re.compile(r"^\d+(\.\d+)?$")
_DIGITS_ONLY = re.compile(r"^\d[\d,]*(\.\d+)?$")
# Footnote markers that publishers glue onto numbers, e.g. "1,234.5*" or "1,234.5#".
_FOOTNOTE = re.compile(r"[*#†‡^@]+$")
_MISSING = frozenset({"", "-", "--", "–", "—", "na", "n.a.", "n/a", "nil", "..."})


@dataclass(frozen=True)
class ParsedNumber:
    """Result of parsing one raw cell.

    Attributes:
        value: Parsed value, or ``None`` if the cell is a missing-value marker or unparseable.
        grouping: How thousands separators were laid out in the raw text.
        is_missing: True when the cell was an explicit missing marker (``-``, ``NA``, blank).
        had_footnote: True when a footnote marker such as ``*`` was stripped.
        error: Why parsing failed, if it did (the row should go to quarantine).
    """

    value: Decimal | None
    grouping: Grouping = "none"
    is_missing: bool = False
    had_footnote: bool = False
    error: str | None = None

    @property
    def needs_review(self) -> bool:
        """True when the value parsed but its layout was suspicious."""
        return self.grouping == "irregular"


def _classify(text: str) -> Grouping:
    if "," not in text:
        return "none"
    if _INDIAN.match(text):
        return "indian"
    if _WESTERN.match(text):
        return "western"
    return "irregular"


def parse_number(raw: object) -> ParsedNumber:
    """Parse a raw cell (str, int, float or None) into a :class:`ParsedNumber`.

    Negative numbers are written either as ``-12.5`` or in accounting style ``(12.5)``.

    >>> parse_number("31,52,929.46").value
    Decimal('3152929.46')
    >>> parse_number("29,029,88.05").grouping
    'irregular'
    """
    if raw is None:
        return ParsedNumber(None, is_missing=True)
    if isinstance(raw, bool):
        return ParsedNumber(None, error=f"boolean is not a number: {raw!r}")
    if isinstance(raw, int | float):
        if raw != raw:  # NaN, as pandas reads empty cells
            return ParsedNumber(None, is_missing=True)
        return ParsedNumber(Decimal(str(raw)))

    text = str(raw).strip().replace(" ", "").replace(" ", "")
    if text.lower() in _MISSING:
        return ParsedNumber(None, is_missing=True)

    had_footnote = bool(_FOOTNOTE.search(text))
    text = _FOOTNOTE.sub("", text)

    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative, text = True, text[1:-1]
    elif text.startswith("-"):
        negative, text = True, text[1:]

    if not (_PLAIN.match(text) or _DIGITS_ONLY.match(text)):
        return ParsedNumber(None, had_footnote=had_footnote, error=f"not a number: {raw!r}")

    grouping = _classify(text)
    try:
        value = Decimal(text.replace(",", ""))
    except InvalidOperation:  # pragma: no cover - regex above already guarantees digits
        return ParsedNumber(None, error=f"not a number: {raw!r}")
    return ParsedNumber(-value if negative else value, grouping, False, had_footnote)
