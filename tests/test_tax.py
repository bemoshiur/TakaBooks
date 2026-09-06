import pytest

from takabooks.tax import (
    MINIMUM_TAX,
    MINIMUM_TAX_NEW_TAXPAYER,
    compute_tax,
    tax_free_threshold,
)


def test_below_threshold_pays_nothing():
    result = compute_tax(400_000)
    assert result.total_tax == 0
    assert result.slabs == []
    assert result.taxable_income == 0


def test_first_slab_only():
    # 500,000 income: 100,000 taxable at 10% -> 10,000
    result = compute_tax(500_000)
    assert result.taxable_income == 100_000
    assert len(result.slabs) == 1
    assert result.slabs[0].tax == 10_000
    assert result.total_tax == 10_000


def test_multiple_slabs():
    # 1,000,000 income, general: taxable 600,000
    # 300k @10% = 30,000; 300k of the 400k slab @15% = 45,000 -> 75,000
    result = compute_tax(1_000_000)
    assert result.taxable_income == 600_000
    assert [s.rate for s in result.slabs] == [0.10, 0.15]
    assert result.slabs[0].taxable == 300_000
    assert result.slabs[1].taxable == 300_000
    assert result.total_tax == 75_000


def test_top_slab():
    # taxable above 3.2M over threshold hits 30%
    # income = 400k + 300k + 400k + 500k + 2M + 1M = 4,600,000
    result = compute_tax(4_600_000)
    expected = 300_000 * 0.10 + 400_000 * 0.15 + 500_000 * 0.20 + 2_000_000 * 0.25 + 1_000_000 * 0.30
    assert result.total_tax == expected
    assert result.slabs[-1].rate == 0.30
    assert result.slabs[-1].upper is None


def test_category_thresholds():
    assert tax_free_threshold("general") == 400_000
    assert tax_free_threshold("female-senior") == 450_000
    assert tax_free_threshold("disabled") == 525_000
    assert tax_free_threshold("third-gender") == 525_000
    assert tax_free_threshold("freedom-fighter") == 550_000
    assert tax_free_threshold("general", guardian_of_disabled=True) == 450_000


def test_unknown_category_raises():
    with pytest.raises(ValueError, match="unknown taxpayer category"):
        compute_tax(1_000_000, category="bogus")


def test_minimum_tax_applies():
    # income just over threshold: slab tax < 5,000 -> minimum tax
    result = compute_tax(410_000)
    assert result.slab_tax == 1_000  # 10,000 @ 10%
    assert result.minimum_tax == MINIMUM_TAX
    assert result.total_tax == MINIMUM_TAX


def test_minimum_tax_new_taxpayer():
    result = compute_tax(410_000, new_taxpayer=True)
    assert result.minimum_tax == MINIMUM_TAX_NEW_TAXPAYER
    assert result.total_tax == MINIMUM_TAX_NEW_TAXPAYER


def test_non_resident_flat_rate():
    result = compute_tax(2_000_000, non_resident=True)
    assert result.total_tax == 600_000
    assert result.tax_free_threshold == 0


def test_negative_income_raises():
    with pytest.raises(ValueError, match="negative"):
        compute_tax(-1)
