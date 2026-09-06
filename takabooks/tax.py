"""Bangladesh individual income tax computation.

Rates per the Finance Ordinance 2025, applicable for FY 2025-26
(assessment year 2026-27). Source: NBR / PwC Worldwide Tax Summaries.
"""

from dataclasses import dataclass, field

TAX_YEAR = "2025-26"

# Tax-free (basic exemption) limits by taxpayer category, in BDT.
TAX_FREE_THRESHOLDS = {
    "general": 400_000,
    "female-senior": 450_000,  # women and senior citizens (65+)
    "disabled": 525_000,  # persons with physical challenges
    "third-gender": 525_000,
    "freedom-fighter": 550_000,  # war-wounded gazetted freedom fighters
}

# Extra exemption for a parent/legal guardian of a physically challenged person.
GUARDIAN_EXTRA = 50_000

# Progressive slabs applied to income above the tax-free threshold.
# (slab width in BDT, rate); width None means "the rest".
SLABS = [
    (300_000, 0.10),
    (400_000, 0.15),
    (500_000, 0.20),
    (2_000_000, 0.25),
    (None, 0.30),
]

# Minimum tax when total income exceeds the tax-free threshold.
MINIMUM_TAX = 5_000
MINIMUM_TAX_NEW_TAXPAYER = 1_000

# Flat rate for non-resident individuals who are not Bangladeshi citizens.
NON_RESIDENT_FLAT_RATE = 0.30


@dataclass
class SlabEntry:
    """Tax charged within one slab."""

    lower: int  # first taka of the slab (inclusive)
    upper: int | None  # last taka of the slab (inclusive); None = open-ended
    rate: float
    taxable: float  # income falling inside this slab
    tax: float


@dataclass
class TaxResult:
    total_income: float
    tax_free_threshold: int
    taxable_income: float
    slabs: list[SlabEntry] = field(default_factory=list)
    slab_tax: float = 0.0
    minimum_tax: int = 0
    total_tax: float = 0.0


def tax_free_threshold(category: str = "general", guardian_of_disabled: bool = False) -> int:
    """Return the basic exemption limit for a taxpayer category."""
    try:
        threshold = TAX_FREE_THRESHOLDS[category]
    except KeyError:
        valid = ", ".join(sorted(TAX_FREE_THRESHOLDS))
        raise ValueError(f"unknown taxpayer category {category!r}; expected one of: {valid}") from None
    if guardian_of_disabled:
        threshold += GUARDIAN_EXTRA
    return threshold


def compute_tax(
    income: float,
    category: str = "general",
    guardian_of_disabled: bool = False,
    new_taxpayer: bool = False,
    non_resident: bool = False,
) -> TaxResult:
    """Compute income tax on total annual income (BDT).

    - category: one of TAX_FREE_THRESHOLDS keys.
    - guardian_of_disabled: adds BDT 50,000 to the exemption limit.
    - new_taxpayer: lowers the minimum tax from 5,000 to 1,000.
    - non_resident: flat 30% (non-resident, non-Bangladeshi citizen);
      slabs and exemption do not apply.
    """
    if income < 0:
        raise ValueError("income cannot be negative")

    if non_resident:
        total = round(income * NON_RESIDENT_FLAT_RATE)
        return TaxResult(
            total_income=income,
            tax_free_threshold=0,
            taxable_income=income,
            slabs=[SlabEntry(lower=0, upper=None, rate=NON_RESIDENT_FLAT_RATE, taxable=income, tax=total)],
            slab_tax=total,
            minimum_tax=0,
            total_tax=total,
        )

    threshold = tax_free_threshold(category, guardian_of_disabled)
    taxable = max(0.0, income - threshold)

    result = TaxResult(
        total_income=income,
        tax_free_threshold=threshold,
        taxable_income=taxable,
    )

    if taxable <= 0:
        return result

    remaining = taxable
    lower = threshold
    for width, rate in SLABS:
        if remaining <= 0:
            break
        in_slab = remaining if width is None else min(remaining, width)
        result.slabs.append(
            SlabEntry(
                lower=lower,
                upper=None if width is None else lower + width - 1,
                rate=rate,
                taxable=in_slab,
                tax=round(in_slab * rate),
            )
        )
        remaining -= in_slab
        lower += in_slab

    result.slab_tax = sum(entry.tax for entry in result.slabs)
    result.minimum_tax = MINIMUM_TAX_NEW_TAXPAYER if new_taxpayer else MINIMUM_TAX
    result.total_tax = max(result.slab_tax, result.minimum_tax)
    return result
