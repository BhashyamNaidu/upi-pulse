import pytest

from upi_pulse.ingestion.sources import (
    SOURCES,
    expected_periods,
    fiscal_year_of,
    is_valid_period,
    months_between,
    parse_month,
)


def test_parse_month():
    assert parse_month("2026-09") == (2026, 9)


@pytest.mark.parametrize("bad", ["2026-13", "2026-00", "2026-9", "Sep-26", "FY2025-26"])
def test_parse_month_rejects_bad_labels(bad):
    with pytest.raises(ValueError):
        parse_month(bad)


@pytest.mark.parametrize(
    ("year", "month", "fy"),
    [
        (2026, 3, "FY2025-26"),
        (2026, 4, "FY2026-27"),
        (2024, 10, "FY2024-25"),
        (2099, 12, "FY2099-00"),
    ],
)
def test_fiscal_year_starts_in_april(year, month, fy):
    assert fiscal_year_of(year, month) == fy


def test_period_validation_depends_on_cadence():
    monthly, fiscal = SOURCES["npci_apps"], SOURCES["npci_product"]
    assert is_valid_period(monthly, "2026-09")
    assert not is_valid_period(monthly, "FY2025-26")
    assert is_valid_period(fiscal, "FY2025-26")
    assert not is_valid_period(fiscal, "FY2025-27")
    assert not is_valid_period(fiscal, "2026-09")


def test_months_between_wraps_year():
    assert months_between("2025-11", "2026-02") == ["2025-11", "2025-12", "2026-01", "2026-02"]


def test_months_between_rejects_reversed_range():
    with pytest.raises(ValueError, match="after"):
        months_between("2026-02", "2025-11")


def test_target_window_is_24_months_and_3_fiscal_years():
    assert len(expected_periods(SOURCES["rbi_psi"], "2024-10", "2026-09")) == 24
    assert expected_periods(SOURCES["npci_product"], "2024-10", "2026-09") == [
        "FY2024-25",
        "FY2025-26",
        "FY2026-27",
    ]
