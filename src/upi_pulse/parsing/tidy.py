"""The tidy long-table contract every parser produces.

One row = one number from one cell: ``(period, source, entity_type, entity_name_raw, metric)``
identifies it, ``value_raw`` and ``unit_raw`` keep the original text, and the ``_`` columns trace
it back to the exact landed file and parser version. Everything stays a string until silver.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, fields
from typing import Literal

EntityType = Literal["ecosystem", "app", "bank", "segment"]
RowKind = Literal["detail", "total"]

_TOTAL_RE = re.compile(
    r"^\s*(grand\s+)?(sub[\s-]?)?total\b|^\s*all\s+(apps|banks|members)\s*$", re.I
)


@dataclass(frozen=True)
class TidyRow:
    """One parsed value. Field names match the bronze schema."""

    period: str
    source: str
    entity_type: EntityType
    entity_name_raw: str
    metric: str
    value_raw: str
    unit_raw: str
    row_kind: RowKind
    _source_file: str
    _sha256: str
    _parser_version: str

    def as_dict(self) -> dict[str, str]:
        """Return the row as a plain dict of strings (bronze stores everything as text)."""
        return {k: str(v) for k, v in asdict(self).items()}


TIDY_COLUMNS: tuple[str, ...] = tuple(f.name for f in fields(TidyRow))


def is_total_label(label: object) -> bool:
    """Return whether a row label marks a totals row (``Total``, ``Grand Total``, ``Sub-total``).

    Totals are kept but tagged ``row_kind="total"``, so marts never double count them and
    reconciliation can check that details sum to the published total.
    """
    return isinstance(label, str) and bool(_TOTAL_RE.search(label))
