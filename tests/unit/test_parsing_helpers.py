"""Tests for format-agnostic parsing helpers.

REAL cases: strings and headers copied from NPCI's published UPI statistics as seen on
2026-11-07 (product statistics and P2P/P2M, Apr-Oct 2026). Marked ``# real``.
SYNTHETIC cases: hand-made edge cases for formats we expect but haven't seen yet. Marked
``# synthetic``. None of these values reach the lake, dashboard or README.
"""

from decimal import Decimal

import pytest

from upi_pulse.normalisation.units import UnitInfo, detect_unit, to_standard
from upi_pulse.parsing.numbers import parse_number
from upi_pulse.parsing.tidy import TIDY_COLUMNS, TidyRow, is_total_label


@pytest.mark.parametrize(
    ("raw", "value", "grouping"),
    [
        ("31,52,929.46", "3152929.46", "indian"),  # real
        ("8,86,987.14", "886987.14", "indian"),  # real
        ("25,466.70", "25466.70", "indian"),  # real (also valid western)
        ("22716.07", "22716.07", "none"),  # real
        ("22,346.8", "22346.8", "indian"),  # real
        ("29,029,88.05", "2902988.05", "irregular"),  # real: mis-grouped April 2026 value
        ("1,234,567.5", "1234567.5", "western"),  # synthetic
        ("758", "758", "none"),  # real (banks live)
    ],
)
def test_parse_number_real_npci_strings(raw, value, grouping):
    parsed = parse_number(raw)
    assert parsed.value == Decimal(value)
    assert parsed.grouping == grouping
    assert parsed.error is None
    assert parsed.needs_review is (grouping == "irregular")


@pytest.mark.parametrize("raw", [None, "", "  ", "-", "NA", "n.a.", "–", float("nan")])
def test_missing_markers(raw):  # synthetic
    parsed = parse_number(raw)
    assert parsed.value is None and parsed.is_missing and parsed.error is None


@pytest.mark.parametrize(
    ("raw", "value"),
    [
        ("1,234.5*", "1234.5"),  # synthetic footnote
        ("(12.5)", "-12.5"),  # synthetic accounting negative
        ("-3", "-3"),
        (" 1 234 ", "1234"),  # synthetic non-breaking space
        (42, "42"),
        (3.25, "3.25"),
    ],
)
def test_footnotes_negatives_and_numeric_cells(raw, value):
    assert parse_number(raw).value == Decimal(value)


def test_footnote_flag():
    assert parse_number("1,234.5#").had_footnote


@pytest.mark.parametrize("raw", ["abc", "12.3.4", "1,2a", True])
def test_unparseable_values_report_an_error(raw):  # synthetic
    parsed = parse_number(raw)
    assert parsed.value is None and not parsed.is_missing and parsed.error


@pytest.mark.parametrize(
    ("header", "measure", "unit"),
    [
        ("Volume (In Mn.)", "volume", "million"),  # real
        ("Value (In Cr.)", "value", "crore"),  # real
        ("Value (Cr)", "value", "crore"),  # real
        ("No. of Banks live on UPI", None, None),  # real
        ("Volume (Lakh)", "volume", "lakh"),  # synthetic (RBI style, unverified)
        ("Value (₹ Crore)", "value", "crore"),  # synthetic
        ("No. of transactions (in lakh)", "volume", "lakh"),  # synthetic
        ("Amount (Rs. billion)", "value", "billion"),  # synthetic
        ("Value (Lakh / Crore)", "value", None),  # synthetic: ambiguous, two units
    ],
)
def test_detect_unit(header, measure, unit):
    info = detect_unit(header)
    assert (info.measure, info.unit) == (measure, unit)


@pytest.mark.parametrize(
    ("header", "raw", "expected"),
    [
        ("Volume (In Mn.)", "24068.38", "24068.38"),
        ("Volume (Lakh)", "240683.8", "24068.38"),  # 10 lakh = 1 million
        ("Value (In Cr.)", "2937396.67", "2937396.67"),
        ("Value (Rs. Lakh)", "100", "1.00"),  # 100 lakh = 1 crore
        ("Value (Rs. billion)", "29373.9667", "2937396.6700"),
    ],
)
def test_to_standard(header, raw, expected):  # synthetic arithmetic checks
    assert to_standard(Decimal(raw), detect_unit(header)) == Decimal(expected)


def test_to_standard_rejects_unknown_units():
    with pytest.raises(ValueError, match="unrecognised unit"):
        to_standard(Decimal(1), UnitInfo("Mystery", None, None))


@pytest.mark.parametrize(
    ("label", "is_total"),
    [
        ("Total", True),
        ("Grand Total", True),
        ("Sub-total", True),
        (" TOTAL ", True),
        ("All Apps", True),
        ("PhonePe #", False),  # real app label
        ("Other Apps", False),
        ("Totally Bank", False),
        (None, False),
    ],
)
def test_is_total_label(label, is_total):
    assert is_total_label(label) is is_total


def test_tidy_row_columns_and_dict():
    row = TidyRow(
        "2026-09", "npci_p2p_p2m", "segment", "P2P", "volume", "8,839.27", "Volume (In Mn.)",
        "detail", "source=npci_p2p_p2m/period=2026-09/sha256=x/f.xlsx", "x", "npci_p2p_p2m.v1",
    )  # fmt: skip
    assert TIDY_COLUMNS[:5] == ("period", "source", "entity_type", "entity_name_raw", "metric")
    assert row.as_dict()["value_raw"] == "8,839.27"
    assert list(row.as_dict()) == list(TIDY_COLUMNS)
