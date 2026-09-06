#!/usr/bin/env python3
"""TakaBooks — individual income tax (আয়কর) computation.

Computes the liability of an individual taxpayer (ব্যক্তি করদাতা) for one assessment year
(করবর্ষ), step by step, so that a user can check every figure by hand:

1. **Progressive slabs / করহার ধাপ** — the tax-free threshold depends on the taxpayer's
   category; the slab widths and rates above it come from the rates file.
2. **Investment rebate / বিনিয়োগজনিত কর রেয়াত** — eligible investment is capped, then a
   percentage of it comes off the gross tax.
3. **Minimum tax / ন্যূনতম কর** — a flat floor by location tier, and a floor on gross
   receipts for taxpayers with turnover; the greater floor wins.
4. **Surcharge / সারচার্জ** — a percentage of the tax, chosen by net-wealth band.
5. **Summary** — total liability, less tax already paid.

Every rate, threshold, band and policy switch is read from ``src/data/rates-AY<year>.toml``
through :mod:`rates`.  **This module defines no Bangladeshi figure of its own** (spec §4.5):
no threshold, no slab, no rate, no band.  It only knows the *shape* of the computation.  If
the rates file is missing a figure, the run fails; nothing is defaulted.

Money is :class:`takabooks.Money` (int paisa).  Each slab's tax is rounded ROUND_HALF_UP
exactly once (``Money.percent``) so the printed rows sum to the printed total — the same
arithmetic a person does with a calculator.

Output is Markdown (default) or ``--json``.  Both state the assessment year, print which
rates file was used, list every rate that touched the answer with its verification state,
and end with the not-professional-advice disclaimer.

Posture towards unlanded data — identical to :mod:`vat`
------------------------------------------------------
Both TakaBooks tax engines take the *same* three-step position, through the same reader
(:class:`rates.RateSet`), with the same flags and the same exit codes.
``tests/test_tax.py::TestEnginePostureSymmetry`` asserts they stay in step, because two
engines that disagree about whether a figure has landed are two answers to one question.

=========================  ================================  ==============================
state of a figure          default posture                   with ``--allow-placeholder-rates``
=========================  ================================  ==============================
absent                     refuse, exit 8, key named         refuse, exit 8, key named
``placeholder = true``     **refuse** the moment the         computed, and the output is
                           computation asks for it           stamped ``PLACEHOLDER``
                           (exit 8, key named)
``verified = false``       computed, ``UNVERIFIED`` caveat,  same
                           output stamped ``PROVISIONAL``
``verified = true``        computed, no caveat               same
=========================  ================================  ==============================

The gate is **per figure, not per file**: a mixed rates file — some nodes landed and
verified, some landed but resting on a secondary source, some still placeholders —
computes normally right up to the moment the working needs an unlanded node, and refuses
then, naming it.  So ``--gross-receipts`` can be refused while the same file happily
produces a slab-and-rebate computation.

The one rule both engines apply is *refuse when the answer depends on it; withhold the
value when it does not*.  ``tax.py`` only ever reads a figure the working actually needs,
so here that rule always comes out as a refusal.  ``vat.py`` also quotes reference figures
the return preparer merely reads, and for those the same rule comes out as withholding the
value while still naming the key and its state.  One rule, two domains.

``--strict`` refuses anything short of fully verified (exit 7), which is how a caller asks
for "final or nothing".

TakaBooks — Moshiur Rahman (@bemoshiur) · TICON SYSTEM LTD — https://ticonsys.com
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rates as rt  # noqa: E402  (path must be set first)
import takabooks as tb  # noqa: E402

__all__ = [
    "KEY_INDIVIDUAL",
    "KEY_THRESHOLDS",
    "KEY_SLABS",
    "KEY_REBATE",
    "KEY_REBATE_RATE",
    "KEY_REBATE_INCOME_CAP_PERCENT",
    "KEY_REBATE_ABSOLUTE_CAP",
    "KEY_MINIMUM_TAX_APPLIES_WHEN",
    "KEY_MINIMUM_TAX_BY_LOCATION",
    "KEY_MINIMUM_TAX_RECEIPTS_RATE",
    "KEY_MINIMUM_TAX_RECEIPTS_ABOVE",
    "KEY_SURCHARGE",
    "KEY_SURCHARGE_BASE",
    "KEY_SURCHARGE_MINIMUM",
    "KEY_SURCHARGE_BANDS",
    "REBATE_FORMULAS",
    "MINIMUM_TAX_POLICIES",
    "SURCHARGE_BASES",
    "WIDTH_SOURCE_CATEGORY_THRESHOLD",
    "ALLOW_PLACEHOLDERS_FLAG",
    "PLACEHOLDER_STATUS_TEXT",
    "GRADE_FINAL",
    "GRADE_UNVERIFIED",
    "GRADE_PLACEHOLDER",
    "STATUS_PLACEHOLDER",
    "STATUS_PROVISIONAL",
    "STATUS_VERIFIED",
    "rates_file_is_placeholder",
    "require_landed_rates",
    "TaxInputs",
    "SlabLine",
    "RebateWorking",
    "MinimumTaxWorking",
    "SurchargeWorking",
    "TaxComputation",
    "available_categories",
    "available_locations",
    "category_threshold",
    "build_slabs",
    "apply_slabs",
    "compute_rebate",
    "compute_minimum_tax",
    "compute_surcharge",
    "compute_income_tax",
    "render_markdown",
    "to_json_dict",
    "load_config_if_present",
    "build_parser",
    "main",
]

# --------------------------------------------------------------------------------------
# Rates-file key map (documented in the header of rates-AY<year>.toml)
# --------------------------------------------------------------------------------------

KEY_INDIVIDUAL = "income_tax.individual"
KEY_THRESHOLDS = "income_tax.individual.thresholds"
KEY_SLABS = "income_tax.individual.slabs"
KEY_REBATE = "income_tax.individual.rebate"
KEY_REBATE_RATE = "income_tax.individual.rebate.rate"
KEY_REBATE_INCOME_CAP_PERCENT = "income_tax.individual.rebate.income_cap_percent"
KEY_REBATE_ABSOLUTE_CAP = "income_tax.individual.rebate.absolute_cap"
KEY_MINIMUM_TAX_APPLIES_WHEN = "income_tax.individual.minimum_tax.applies_when"
KEY_MINIMUM_TAX_BY_LOCATION = "income_tax.individual.minimum_tax.by_location"
KEY_MINIMUM_TAX_RECEIPTS_RATE = "income_tax.individual.minimum_tax.on_gross_receipts.rate"
KEY_MINIMUM_TAX_RECEIPTS_ABOVE = "income_tax.individual.minimum_tax.on_gross_receipts.applies_above"
KEY_SURCHARGE = "income_tax.individual.surcharge"
KEY_SURCHARGE_BASE = "income_tax.individual.surcharge.base"
KEY_SURCHARGE_MINIMUM = "income_tax.individual.surcharge.minimum"
KEY_SURCHARGE_BANDS = "income_tax.individual.surcharge.bands"

#: Rebate constructions this module implements.  A rates file naming any other ``formula``
#: is refused rather than computed wrongly.
REBATE_FORMULAS: tuple[str, ...] = ("min_of_three_caps",)

#: Values the ``minimum_tax.applies_when`` policy switch may take.
MINIMUM_TAX_POLICIES: tuple[str, ...] = ("always", "taxable_income_above_threshold", "never")

#: Values the ``surcharge.base`` policy switch may take.
SURCHARGE_BASES: tuple[str, ...] = ("tax_before_rebate", "tax_after_rebate", "tax_after_minimum")

#: The only ``width_source`` a slab may declare: its width is the category threshold.
WIDTH_SOURCE_CATEGORY_THRESHOLD = "category_threshold"

_LANGUAGES = ("en", "bn", "bn-en")


# --------------------------------------------------------------------------------------
# Verification posture — the vocabulary tax.py and vat.py share
#
# These strings and grades are duplicated verbatim in vat.py so that the two engines stamp
# the same words on the same situation.  They are constants, not figures, so duplicating
# them asserts nothing about Bangladeshi law; the *decisions* that use them all come from
# one reader, rates.RateSet.  Keep the twins in step —
# tests/test_tax.py::TestEnginePostureSymmetry fails if they drift apart.
# --------------------------------------------------------------------------------------

#: The opt-in every TakaBooks calculator uses to compute from unlanded data.
ALLOW_PLACEHOLDERS_FLAG = "--allow-placeholder-rates"

#: How far the data behind an answer can be trusted.  Worst grade of any figure wins.
GRADE_FINAL = "final"
GRADE_UNVERIFIED = "unverified"
GRADE_PLACEHOLDER = "placeholder"

#: ``[meta] status`` text that declares a file unlanded even without ``placeholder = true``.
PLACEHOLDER_STATUS_TEXT = "placeholder"

#: Filing status stamped on every output format.
STATUS_PLACEHOLDER = (
    "PLACEHOLDER / অস্থায়ী — computed from unlanded data, NOT FOR FILING"
)
STATUS_PROVISIONAL = "PROVISIONAL / অস্থায়ী — not for filing"
STATUS_VERIFIED = "every rate used is verified; confirm with an ITP/CA before filing"


def rates_file_is_placeholder(rates: rt.RateSet) -> bool:
    """True when ``[meta]`` declares the whole file to be unlanded schema.

    The contract flag is ``[meta] placeholder``, and it is read by exactly one piece of
    code — :attr:`rates.RateSet.file_is_placeholder`.  ``[meta] status = "placeholder"``
    is honoured as well, as a belt-and-braces for a file that writes the prose key and
    forgets the flag; that is a *widening*, never a second opinion, so the two can never
    disagree about a file that sets the flag.

    ``vat.py`` carries the identical twin of this function.  The single home for it would
    be ``rates.py``, which neither engine owns;
    ``tests/test_tax.py::TestEnginePostureSymmetry`` asserts the twins agree over a matrix
    of ``[meta]`` shapes so they cannot drift.
    """
    if rates.file_is_placeholder:
        return True
    return str(rates.meta.get("status", "")).strip().lower() == PLACEHOLDER_STATUS_TEXT


def require_landed_rates(
    rates: rt.RateSet, *, allow_placeholders: bool | None = None
) -> None:
    """Refuse a rates file that declares itself unlanded, unless the caller opted in.

    :meth:`rates.RateSet.require_usable` widened by the ``[meta] status`` check above and
    worded the same way, so ``tax.py`` and ``vat.py`` refuse the same file with the same
    exit code (8) and offer the same remedy.  ``vat.require_landed_rates`` has this exact
    signature and behaviour, and ``tests/test_vat.py::TestEnginePostureSymmetry`` calls
    both over one matrix.

    ``allow_placeholders`` left at ``None`` reads the posture off the ``RateSet`` itself,
    so the opt-in travels from the command line to the last figure read on one object
    rather than being passed hand to hand.
    """
    if allow_placeholders is None:
        allow_placeholders = bool(getattr(rates, "allow_placeholders", False))
    if not allow_placeholders:
        rates.require_usable()
    if allow_placeholders or not rates_file_is_placeholder(rates):
        return
    raise tb.RatesError(
        f"{rates.filename} is a schema awaiting verified data — every figure in it is a "
        "placeholder.",
        hint="No Bangladeshi rate has been landed for this assessment year yet. Fill the "
        "file in (its header documents the procedure), or pass "
        f"{ALLOW_PLACEHOLDERS_FLAG} to compute a clearly-marked PROVISIONAL result that "
        "must never be filed.",
    )


# --------------------------------------------------------------------------------------
# Inputs and results
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class TaxInputs:
    """What the taxpayer tells us.  Everything statutory comes from the rates file."""

    income: tb.Money
    category: str
    location: str
    investment: tb.Money = tb.Money.zero()
    net_wealth: tb.Money | None = None
    gross_receipts: tb.Money | None = None
    tax_paid: tb.Money = tb.Money.zero()

    def __post_init__(self) -> None:
        problems: list[str] = []
        for name in ("income", "investment", "tax_paid"):
            value = getattr(self, name)
            if not isinstance(value, tb.Money):
                problems.append(f"{name} must be Money, not {type(value).__name__}.")
            elif value.is_negative():
                problems.append(f"{name} cannot be negative ({value.bdt}).")
        for name in ("net_wealth", "gross_receipts"):
            value = getattr(self, name)
            if value is None:
                continue
            if not isinstance(value, tb.Money):
                problems.append(f"{name} must be Money or None, not {type(value).__name__}.")
            elif value.is_negative():
                problems.append(f"{name} cannot be negative ({value.bdt}).")
        if not str(self.category).strip():
            problems.append("category is blank.")
        if not str(self.location).strip():
            problems.append("location is blank.")
        if problems:
            raise tb.ValidationError(
                "Invalid tax inputs: " + " ".join(problems),
                problems=tuple(problems),
                hint="Amounts are taka (BDT) and must be zero or positive; enter 0 for a "
                "loss year rather than a negative income.",
            )


@dataclass(frozen=True)
class SlabLine:
    """One row of the slab-by-slab working."""

    order: int
    label_en: str
    label_bn: str
    lower: tb.Money
    upper: tb.Money | None          # None for the open-ended top slab
    width: tb.Money | None          # None for the open-ended top slab
    taxable: tb.Money
    rate: Decimal                   # percent
    tax: tb.Money
    width_key: str = ""             # rates key the width came from (threshold or slab width)
    rate_key: str = ""

    @property
    def is_open_ended(self) -> bool:
        return self.width is None

    @property
    def label(self) -> str:
        if self.label_bn and self.label_en:
            return f"{self.label_bn} / {self.label_en}"
        return self.label_en or self.label_bn or f"Slab {self.order}"


@dataclass(frozen=True)
class RebateWorking:
    """Step 2: investment rebate."""

    claimed: bool
    investment: tb.Money
    gross_tax: tb.Money
    formula: str = ""
    rate: Decimal = Decimal(0)                  # percent of eligible investment
    income_cap_percent: Decimal = Decimal(0)    # percent of taxable income
    income_cap_amount: tb.Money = tb.Money.zero()
    absolute_cap: tb.Money = tb.Money.zero()
    eligible: tb.Money = tb.Money.zero()
    rebate_computed: tb.Money = tb.Money.zero()
    rebate: tb.Money = tb.Money.zero()
    #: How the STATUTE words the same limits, quoted from the rates file.  ``income_cap_percent``
    #: and ``absolute_cap`` are engine parameters that cap the *investment*; the law caps the
    #: *rebate*.  Empty when the rates file does not state it — never reconstructed here.
    statutory_formulation_en: str = ""
    statutory_formulation_bn: str = ""

    @property
    def tax_after_rebate(self) -> tb.Money:
        return self.gross_tax - self.rebate

    @property
    def capped_by_gross_tax(self) -> bool:
        return self.rebate_computed > self.rebate


@dataclass(frozen=True)
class MinimumTaxWorking:
    """Step 3: minimum tax floors."""

    policy: str
    tax_before: tb.Money
    location: str
    location_label: str = ""
    location_floor: tb.Money | None = None      # None when the policy is "never"
    location_floor_applies: bool = False
    gross_receipts: tb.Money | None = None
    receipts_applies_above: tb.Money | None = None
    receipts_rate: Decimal | None = None        # percent
    receipts_floor: tb.Money | None = None      # None when not computed
    receipts_floor_applies: bool = False
    floor: tb.Money = tb.Money.zero()

    @property
    def tax_after(self) -> tb.Money:
        return max(self.tax_before, self.floor)

    @property
    def adjustment(self) -> tb.Money:
        return self.tax_after - self.tax_before

    @property
    def floor_bites(self) -> bool:
        return self.floor > self.tax_before


@dataclass(frozen=True)
class SurchargeWorking:
    """Step 4: surcharge on net wealth band."""

    assessed: bool
    net_wealth: tb.Money | None = None
    band_order: int = 0
    band_label_en: str = ""
    band_label_bn: str = ""
    wealth_above: tb.Money | None = None        # None for the first band (starts at zero)
    rate: Decimal = Decimal(0)                  # percent
    base: str = ""
    base_amount: tb.Money = tb.Money.zero()
    computed: tb.Money = tb.Money.zero()
    minimum: tb.Money | None = None             # None when it could not bite / not read
    surcharge: tb.Money = tb.Money.zero()

    @property
    def band_label(self) -> str:
        if self.band_label_bn and self.band_label_en:
            return f"{self.band_label_bn} / {self.band_label_en}"
        return self.band_label_en or self.band_label_bn or f"Band {self.band_order}"

    @property
    def lifted_to_minimum(self) -> bool:
        return self.minimum is not None and self.surcharge > self.computed


@dataclass(frozen=True)
class TaxComputation:
    """The complete working, from inputs to net payable."""

    assessment_year: str
    rates_source: str
    rates_path: Path | None
    inputs: TaxInputs
    category_label: str
    threshold: tb.Money
    threshold_key: str
    slabs: tuple[SlabLine, ...]
    rebate: RebateWorking
    minimum_tax: MinimumTaxWorking
    surcharge: SurchargeWorking
    provisional: bool
    caveats: tuple[str, ...]
    rates_used: tuple[rt.RateEntry, ...]
    warnings: tuple[str, ...] = ()
    business_name: str = ""
    tin: str = ""
    rates_file_placeholder: bool = False
    allow_placeholders: bool = False
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    # -- how far this answer can be trusted ----------------------------------------------

    @property
    def unverified_used(self) -> tuple[rt.RateEntry, ...]:
        """Every figure the working touched that is not ``verified = true``."""
        return tuple(e for e in self.rates_used if not e.is_verified)

    @property
    def placeholders_used(self) -> tuple[rt.RateEntry, ...]:
        """Every *unlanded* figure the working touched — the worst kind of caveat."""
        return tuple(e for e in self.rates_used if e.is_placeholder)

    @property
    def placeholder_figures(self) -> tuple[str, ...]:
        """Dotted keys of the unlanded figures behind this answer, in key order."""
        return tuple(sorted({e.key for e in self.placeholders_used}))

    @property
    def placeholder_data_used(self) -> bool:
        return self.rates_file_placeholder or bool(self.placeholders_used)

    @property
    def data_grade(self) -> str:
        """The worst verification grade behind this answer (see :data:`GRADE_FINAL`)."""
        if self.placeholder_data_used:
            return GRADE_PLACEHOLDER
        if self.provisional:
            return GRADE_UNVERIFIED
        return GRADE_FINAL

    @property
    def filing_status(self) -> str:
        if self.placeholder_data_used:
            return STATUS_PLACEHOLDER
        return STATUS_PROVISIONAL if self.provisional else STATUS_VERIFIED

    def blocking_problems(self) -> tuple[str, ...]:
        """Everything ``--strict`` refuses to produce a filing-ready computation over.

        The twin of :meth:`vat.VatPosition.blocking_problems`: the caveats that name an
        unverified or unlanded figure, plus any warning raised about the run itself.
        """
        return tuple(list(self.caveats) + list(self.warnings))

    @property
    def gross_tax(self) -> tb.Money:
        return tb.Money.sum(line.tax for line in self.slabs)

    @property
    def tax_after_rebate(self) -> tb.Money:
        return self.rebate.tax_after_rebate

    @property
    def tax_after_minimum(self) -> tb.Money:
        return self.minimum_tax.tax_after

    @property
    def total_tax(self) -> tb.Money:
        return self.tax_after_minimum + self.surcharge.surcharge

    @property
    def net_payable(self) -> tb.Money:
        """Positive: pay this much.  Negative: refundable / adjustable."""
        return self.total_tax - self.inputs.tax_paid

    @property
    def is_above_threshold(self) -> bool:
        return self.inputs.income > self.threshold


# --------------------------------------------------------------------------------------
# Reading the rates file — structure only, never a figure
# --------------------------------------------------------------------------------------


def available_categories(rates: rt.RateSet) -> list[str]:
    """Taxpayer categories the rates file defines (the ids ``--category`` accepts)."""
    return rates.option_keys(KEY_THRESHOLDS)


def available_locations(rates: rt.RateSet) -> list[str]:
    """Minimum-tax location tiers the rates file defines (the ids ``--location`` accepts)."""
    return rates.option_keys(KEY_MINIMUM_TAX_BY_LOCATION)


def _labelled_options(rates: rt.RateSet, section_key: str) -> list[tuple[str, str]]:
    """``(id, "বাংলা / English")`` pairs for every option under ``section_key``.

    Read straight from the raw section so listing options never trips the placeholder
    gate — a user must be able to see which categories exist before choosing one.
    """
    options: list[tuple[str, str]] = []
    for key, node in rates.section(section_key).items():
        if isinstance(node, Mapping) and "value" in node:
            bn = str(node.get("label_bn", "")).strip()
            en = str(node.get("label_en", "")).strip()
            label = f"{bn} / {en}" if bn and en else (en or bn or str(key))
            options.append((str(key), label))
    return options


def _default_option(rates: rt.RateSet, field_name: str, flag: str, section_key: str) -> str:
    """The rates file's stated default for a category or location — or a clear refusal."""
    node = rates.section(KEY_INDIVIDUAL).get(field_name)
    text = str(node).strip() if isinstance(node, str) else ""
    if not text:
        raise tb.RatesError(
            f"{rates.filename} names no {field_name}; pass {flag}.",
            hint="Available: " + ", ".join(rates.option_keys(section_key)) + ".",
        )
    return text


def category_threshold(rates: rt.RateSet, category: str) -> tuple[tb.Money, rt.RateEntry]:
    """The tax-free threshold for ``category`` and the entry it was read from."""
    key = f"{KEY_THRESHOLDS}.{category}"
    if not rates.has(key):
        raise tb.RatesError(
            f"{rates.filename} defines no taxpayer category {category!r}.",
            hint="Available categories: " + ", ".join(available_categories(rates)) + ".",
        )
    entry = rates.rate(key)
    return entry.as_money(), entry


@dataclass(frozen=True)
class _SlabSpec:
    order: int
    label_en: str
    label_bn: str
    width: tb.Money | None
    width_key: str
    rate: Decimal
    rate_key: str


def _build_slab_specs(rates: rt.RateSet, threshold: tb.Money, threshold_key: str) -> list[_SlabSpec]:
    slabs = rates.items(KEY_SLABS)
    specs: list[_SlabSpec] = []
    last_index = len(slabs) - 1
    for index, slab in enumerate(slabs):
        prefix = f"{KEY_SLABS}[{index}]"
        order = slab.get("order", index + 1)
        if isinstance(order, bool) or not isinstance(order, int):
            order = index + 1
        label_en = str(slab.get("label_en", "")).strip()
        label_bn = str(slab.get("label_bn", "")).strip()

        if "rate" not in slab:
            raise tb.RatesError(
                f"{rates.filename}: {prefix} has no 'rate' node.",
                hint="Every slab needs a [income_tax.individual.slabs.rate] table with a "
                "value in percent.",
            )
        rate_entry = rates.entry_from_node(slab["rate"], f"{prefix}.rate")
        rate = rate_entry.as_percent()

        has_source = "width_source" in slab
        has_width = "width" in slab
        if has_source and has_width:
            raise tb.RatesError(
                f"{rates.filename}: {prefix} declares both 'width' and 'width_source'.",
                hint="A slab takes its width from exactly one place.",
            )
        width: tb.Money | None
        width_key = ""
        if has_source:
            source = str(slab["width_source"]).strip()
            if source != WIDTH_SOURCE_CATEGORY_THRESHOLD:
                raise tb.RatesError(
                    f"{rates.filename}: {prefix} has width_source = {source!r}, which "
                    "TakaBooks does not implement.",
                    hint=f'The only width_source is "{WIDTH_SOURCE_CATEGORY_THRESHOLD}".',
                )
            width = threshold
            width_key = threshold_key
        elif has_width:
            width_entry = rates.entry_from_node(slab["width"], f"{prefix}.width")
            width = width_entry.as_money()
            width_key = width_entry.key
        else:
            width = None

        if width is None and index != last_index:
            raise tb.RatesError(
                f"{rates.filename}: {prefix} is open-ended (no width) but is not the last slab.",
                hint="Only the top slab may omit 'width'; every slab below it needs one.",
            )
        if width is not None and index == last_index:
            raise tb.RatesError(
                f"{rates.filename}: the last slab {prefix} has a width; the top slab must be "
                "open-ended.",
                hint="Remove 'width' from the top slab so it takes the balance of income, "
                "or add the missing open-ended slab after it.",
            )
        specs.append(_SlabSpec(order, label_en, label_bn, width, width_key, rate, rate_entry.key))
    return specs


def build_slabs(
    rates: rt.RateSet, threshold: tb.Money, *, threshold_key: str = ""
) -> list[SlabLine]:
    """The slab table for a given category threshold, with nothing applied yet.

    Validates the shape the rates file promises: the first slab may take its width from the
    category threshold, every middle slab carries its own width, and exactly one open-ended
    slab closes the list.  Any other shape is refused.
    """
    lines: list[SlabLine] = []
    lower = tb.Money.zero()
    for spec in _build_slab_specs(rates, threshold, threshold_key):
        upper = None if spec.width is None else lower + spec.width
        lines.append(
            SlabLine(
                order=spec.order,
                label_en=spec.label_en,
                label_bn=spec.label_bn,
                lower=lower,
                upper=upper,
                width=spec.width,
                taxable=tb.Money.zero(),
                rate=spec.rate,
                tax=tb.Money.zero(),
                width_key=spec.width_key,
                rate_key=spec.rate_key,
            )
        )
        if upper is not None:
            lower = upper
    return lines


def apply_slabs(slabs: Sequence[SlabLine], income: tb.Money) -> list[SlabLine]:
    """Spread ``income`` across the slabs, taxing each portion at its rate.

    Each slab's tax is ``portion.percent(rate)`` — one ROUND_HALF_UP per row — so the
    rows a reader sees add up exactly to the total they see.
    """
    if income.is_negative():
        raise tb.ValidationError("Taxable income cannot be negative.", problems=("income < 0",))
    remaining = income
    applied: list[SlabLine] = []
    for line in slabs:
        if line.width is None:
            taxable = remaining
        else:
            taxable = min(line.width, remaining)
        tax = taxable.percent(line.rate)
        applied.append(
            SlabLine(
                order=line.order,
                label_en=line.label_en,
                label_bn=line.label_bn,
                lower=line.lower,
                upper=line.upper,
                width=line.width,
                taxable=taxable,
                rate=line.rate,
                tax=tax,
                width_key=line.width_key,
                rate_key=line.rate_key,
            )
        )
        remaining = remaining - taxable
    if not remaining.is_zero():  # pragma: no cover - impossible once build_slabs validated
        raise tb.RatesError(
            f"Slab table did not absorb all income ({remaining.bdt} left over).",
            hint="The top slab must be open-ended.",
        )
    return applied


def compute_rebate(
    rates: rt.RateSet, income: tb.Money, investment: tb.Money, gross_tax: tb.Money
) -> RebateWorking:
    """Step 2.  Reads the rebate nodes only when an investment is actually claimed, so an
    unverified rebate rate cannot make a no-investment result provisional."""
    if investment.is_zero():
        return RebateWorking(claimed=False, investment=investment, gross_tax=gross_tax)

    section = rates.section(KEY_REBATE)
    formula = section.get("formula")
    formula = str(formula).strip() if isinstance(formula, str) else ""
    if not formula:
        raise tb.RatesError(
            f"{rates.filename}: [{KEY_REBATE}] names no 'formula'.",
            hint="Implemented: " + ", ".join(REBATE_FORMULAS) + ". TakaBooks will not guess "
            "how the rebate is constructed for this assessment year.",
        )
    if formula not in REBATE_FORMULAS:
        raise tb.RatesError(
            f"{rates.filename}: rebate formula {formula!r} is not implemented by TakaBooks.",
            hint="Implemented: " + ", ".join(REBATE_FORMULAS) + ".",
        )

    def _statutory(name: str) -> str:
        value = section.get(name)
        return value.strip() if isinstance(value, str) else ""

    rate = rates.percent(KEY_REBATE_RATE)
    income_cap_percent = rates.percent(KEY_REBATE_INCOME_CAP_PERCENT)
    absolute_cap = rates.money(KEY_REBATE_ABSOLUTE_CAP)
    income_cap_amount = income.percent(income_cap_percent)
    eligible = min(investment, income_cap_amount, absolute_cap)
    rebate_computed = eligible.percent(rate)
    rebate = min(rebate_computed, gross_tax)  # a rebate never turns tax negative
    return RebateWorking(
        claimed=True,
        investment=investment,
        gross_tax=gross_tax,
        formula=formula,
        rate=rate,
        income_cap_percent=income_cap_percent,
        income_cap_amount=income_cap_amount,
        absolute_cap=absolute_cap,
        eligible=eligible,
        rebate_computed=rebate_computed,
        rebate=rebate,
        statutory_formulation_en=_statutory("statutory_formulation_en"),
        statutory_formulation_bn=_statutory("statutory_formulation_bn"),
    )


def compute_minimum_tax(
    rates: rt.RateSet,
    *,
    tax_before: tb.Money,
    income: tb.Money,
    threshold: tb.Money,
    location: str,
    gross_receipts: tb.Money | None,
) -> MinimumTaxWorking:
    """Step 3.  The location floor is gated by the ``applies_when`` policy; the gross
    receipts floor engages only when receipts were supplied and exceed ``applies_above``."""
    policy = rates.choice(KEY_MINIMUM_TAX_APPLIES_WHEN, MINIMUM_TAX_POLICIES)

    location_floor: tb.Money | None = None
    location_label = ""
    location_applies = False
    if policy != "never":
        key = f"{KEY_MINIMUM_TAX_BY_LOCATION}.{location}"
        if not rates.has(key):
            raise tb.RatesError(
                f"{rates.filename} defines no location tier {location!r}.",
                hint="Available tiers: " + ", ".join(available_locations(rates)) + ".",
            )
        entry = rates.rate(key)
        location_floor = entry.as_money()
        location_label = entry.label
        location_applies = policy == "always" or (
            policy == "taxable_income_above_threshold" and income > threshold
        )
    else:
        # Even with no floor to read, an unknown tier is still a typo worth refusing.
        if location not in available_locations(rates):
            raise tb.RatesError(
                f"{rates.filename} defines no location tier {location!r}.",
                hint="Available tiers: " + ", ".join(available_locations(rates)) + ".",
            )

    receipts_above: tb.Money | None = None
    receipts_rate: Decimal | None = None
    receipts_floor: tb.Money | None = None
    receipts_applies = False
    if gross_receipts is not None:
        receipts_above = rates.money(KEY_MINIMUM_TAX_RECEIPTS_ABOVE)
        if gross_receipts > receipts_above:
            receipts_rate = rates.percent(KEY_MINIMUM_TAX_RECEIPTS_RATE)
            receipts_floor = gross_receipts.percent(receipts_rate)
            receipts_applies = True

    floors = [tb.Money.zero()]
    if location_applies and location_floor is not None:
        floors.append(location_floor)
    if receipts_applies and receipts_floor is not None:
        floors.append(receipts_floor)
    return MinimumTaxWorking(
        policy=policy,
        tax_before=tax_before,
        location=location,
        location_label=location_label,
        location_floor=location_floor,
        location_floor_applies=location_applies,
        gross_receipts=gross_receipts,
        receipts_applies_above=receipts_above,
        receipts_rate=receipts_rate,
        receipts_floor=receipts_floor,
        receipts_floor_applies=receipts_applies,
        floor=max(floors),
    )


@dataclass(frozen=True)
class _BandSpec:
    order: int
    label_en: str
    label_bn: str
    wealth_above: tb.Money | None
    rate: Decimal


def _build_band_specs(rates: rt.RateSet) -> list[_BandSpec]:
    bands = rates.items(KEY_SURCHARGE_BANDS)
    specs: list[_BandSpec] = []
    previous: tb.Money | None = None
    previous_is_placeholder = False
    for index, band in enumerate(bands):
        prefix = f"{KEY_SURCHARGE_BANDS}[{index}]"
        order = band.get("order", index + 1)
        if isinstance(order, bool) or not isinstance(order, int):
            order = index + 1
        if "rate" not in band:
            raise tb.RatesError(f"{rates.filename}: {prefix} has no 'rate' node.")
        rate = rates.entry_from_node(band["rate"], f"{prefix}.rate").as_percent()
        has_above = "wealth_above" in band
        if index == 0 and has_above:
            raise tb.RatesError(
                f"{rates.filename}: the first surcharge band {prefix} must start at zero — "
                "remove its 'wealth_above'.",
            )
        if index > 0 and not has_above:
            raise tb.RatesError(
                f"{rates.filename}: {prefix} has no 'wealth_above' node.",
                hint="Every band after the first must say the net wealth it starts above.",
            )
        wealth_above: tb.Money | None = None
        if has_above:
            above_entry = rates.entry_from_node(band["wealth_above"], f"{prefix}.wealth_above")
            wealth_above = above_entry.as_money()
            # Real figures must strictly ascend; a placeholder carries nothing to order.
            if (
                previous is not None
                and not previous_is_placeholder
                and not above_entry.is_placeholder
                and wealth_above <= previous
            ):
                raise tb.RatesError(
                    f"{rates.filename}: surcharge bands are not in ascending order at {prefix} "
                    f"({wealth_above.bdt} after {previous.bdt}).",
                )
            previous = wealth_above
            previous_is_placeholder = above_entry.is_placeholder
        specs.append(
            _BandSpec(
                order=order,
                label_en=str(band.get("label_en", "")).strip(),
                label_bn=str(band.get("label_bn", "")).strip(),
                wealth_above=wealth_above,
                rate=rate,
            )
        )
    return specs


def compute_surcharge(
    rates: rt.RateSet,
    *,
    net_wealth: tb.Money | None,
    tax_before_rebate: tb.Money,
    tax_after_rebate: tb.Money,
    tax_after_minimum: tb.Money,
) -> SurchargeWorking:
    """Step 4.  Without a net-wealth figure the surcharge is *not assessed* — reported as
    such, never assumed to be zero."""
    if net_wealth is None:
        return SurchargeWorking(assessed=False)

    specs = _build_band_specs(rates)
    chosen = specs[0]
    for spec in specs[1:]:
        if spec.wealth_above is not None and net_wealth > spec.wealth_above:
            chosen = spec
        else:
            break

    base = rates.choice(KEY_SURCHARGE_BASE, SURCHARGE_BASES)
    base_amount = {
        "tax_before_rebate": tax_before_rebate,
        "tax_after_rebate": tax_after_rebate,
        "tax_after_minimum": tax_after_minimum,
    }[base]
    computed = base_amount.percent(chosen.rate)
    minimum: tb.Money | None = None
    surcharge = computed
    if computed.is_positive():
        minimum = rates.money(KEY_SURCHARGE_MINIMUM)
        if computed < minimum:
            surcharge = minimum
    return SurchargeWorking(
        assessed=True,
        net_wealth=net_wealth,
        band_order=chosen.order,
        band_label_en=chosen.label_en,
        band_label_bn=chosen.label_bn,
        wealth_above=chosen.wealth_above,
        rate=chosen.rate,
        base=base,
        base_amount=base_amount,
        computed=computed,
        minimum=minimum,
        surcharge=surcharge,
    )


# --------------------------------------------------------------------------------------
# The whole computation
# --------------------------------------------------------------------------------------


def compute_income_tax(
    rates: rt.RateSet,
    inputs: TaxInputs,
    *,
    config: tb.Config | None = None,
    warnings: Sequence[str] = (),
) -> TaxComputation:
    """Run every step against ``rates`` and return the full working.

    ``rates`` is consulted for every figure.  If the file declares itself unlanded and the
    caller did not opt in (``RateSet.allow_placeholders``), this raises before computing
    anything; and any *individual* node marked ``placeholder = true`` raises the moment
    the working asks for it, naming that key.  Per figure, not per file.
    """
    require_landed_rates(rates)
    assessment_year = rates.require_assessment_year()

    threshold, threshold_entry = category_threshold(rates, inputs.category)
    slabs = apply_slabs(build_slabs(rates, threshold, threshold_key=threshold_entry.key), inputs.income)
    gross_tax = tb.Money.sum(line.tax for line in slabs)

    rebate = compute_rebate(rates, inputs.income, inputs.investment, gross_tax)
    minimum = compute_minimum_tax(
        rates,
        tax_before=rebate.tax_after_rebate,
        income=inputs.income,
        threshold=threshold,
        location=inputs.location,
        gross_receipts=inputs.gross_receipts,
    )
    surcharge = compute_surcharge(
        rates,
        net_wealth=inputs.net_wealth,
        tax_before_rebate=gross_tax,
        tax_after_rebate=rebate.tax_after_rebate,
        tax_after_minimum=minimum.tax_after,
    )

    return TaxComputation(
        assessment_year=assessment_year,
        rates_source=rates.provenance(),
        rates_path=rates.path,
        inputs=inputs,
        category_label=threshold_entry.label,
        threshold=threshold,
        threshold_key=threshold_entry.key,
        slabs=tuple(slabs),
        rebate=rebate,
        minimum_tax=minimum,
        surcharge=surcharge,
        provisional=rates.is_provisional or rates_file_is_placeholder(rates),
        caveats=tuple(rates.caveats()),
        rates_used=rates.used(),
        warnings=tuple(warnings),
        business_name=config.display_name if config and config.business_name else "",
        tin=config.tin if config else "",
        rates_file_placeholder=rates_file_is_placeholder(rates),
        allow_placeholders=bool(rates.allow_placeholders),
    )


# --------------------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------------------


def _pct(value: Decimal | None) -> str:
    if value is None:
        return "—"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return f"{text}%"


def _money_formatter(config: tb.Config | None):
    def fmt(amount: tb.Money | None) -> str:
        if amount is None:
            return "—"
        if config is not None:
            return config.format_money(amount, symbol=True)
        return tb.format_bdt(amount, symbol=True)

    return fmt


def render_markdown(
    result: TaxComputation, *, language: str = "en", config: tb.Config | None = None
) -> str:
    """The human-readable working.  Every number a hand check would need is on the page."""
    if language not in _LANGUAGES:
        raise ValueError(f"language must be one of {_LANGUAGES}, not {language!r}.")
    fmt = _money_formatter(config)
    inp = result.inputs
    lines: list[str] = []

    lines.append(f"# {tb.term('income_tax')} — {tb.term('taxpayer')} (individual)")
    lines.append("")
    lines.append(f"**{tb.term('assessment_year')}:** {result.assessment_year}")
    lines.append(f"**{result.rates_source}**")
    if result.rates_path:
        lines.append(f"Rates file: `{result.rates_path}`")
    if result.business_name:
        tin = f" · TIN {result.tin}" if result.tin else ""
        lines.append(f"Taxpayer: {result.business_name}{tin}")
    lines.append("")

    lines.append(f"**Filing status:** {result.filing_status}")
    lines.append("")

    if result.placeholder_data_used:
        keys = result.placeholder_figures
        if result.rates_file_placeholder:
            what = (
                "The rates file declares itself a placeholder schema awaiting verified "
                "data, so every figure below is unlanded."
            )
        else:
            plural = "figure" if len(keys) == 1 else "figures"
            verb = "has" if len(keys) == 1 else "have"
            what = (
                f"{len(keys)} of the {len(result.rates_used)} {plural} this working used "
                f"{verb} no landed value: "
                + ", ".join(f"`{key}`" for key in keys)
                + "."
            )
        lines += [
            "> **PLACEHOLDER DATA / অস্থায়ী উপাত্ত — NOT FOR FILING.**  "
            f"{what} A placeholder is not a figure — it is schema awaiting research — and "
            f"it was read only because {ALLOW_PLACEHOLDERS_FLAG} was given. What follows "
            "is a walkthrough of the method, not a tax liability. Obtain each figure from "
            "the National Board of Revenue (NBR). See *Caveats* at the end.",
            "",
        ]
    elif result.provisional:
        unverified = result.unverified_used
        lines += [
            "> **PROVISIONAL / অস্থায়ী — NOT FOR FILING.**  "
            f"{len(unverified)} of the {len(result.rates_used)} rates used below are not "
            "confirmed against a primary NBR source. The arithmetic is right; the figures "
            "it rests on are not yet final. See *Caveats* at the end.",
            "",
        ]
    for warning in result.warnings:
        lines += [f"> **WARNING.** {warning}", ""]

    # -- inputs ------------------------------------------------------------------------
    lines.append("## Inputs / প্রদত্ত তথ্য")
    lines.append("")
    lines.append(
        tb.markdown_table(
            ["Item", "Value"],
            [
                ["Taxpayer category / করদাতার শ্রেণি", f"{result.category_label} (`{inp.category}`)"],
                [
                    "Location tier / এলাকা (minimum tax)",
                    f"{result.minimum_tax.location_label} (`{inp.location}`)"
                    if result.minimum_tax.location_label
                    else f"`{inp.location}`",
                ],
                ["Total taxable income / মোট করযোগ্য আয়", fmt(inp.income)],
                ["Investment claimed for rebate / রেয়াতযোগ্য বিনিয়োগ", fmt(inp.investment)],
                ["Net wealth / নিট সম্পদ (surcharge)", fmt(inp.net_wealth) if inp.net_wealth is not None else "not given"],
                ["Gross receipts / মোট প্রাপ্তি (minimum tax)", fmt(inp.gross_receipts) if inp.gross_receipts is not None else "not given"],
                ["Tax already paid / পরিশোধিত কর (advance tax, TDS)", fmt(inp.tax_paid)],
            ],
        )
    )
    lines.append("")

    # -- step 1: slabs -----------------------------------------------------------------
    lines.append("## Step 1 · ধাপভিত্তিক কর / Tax by slab")
    lines.append("")
    lines.append(
        f"Tax-free threshold (করমুক্ত আয়সীমা) for {result.category_label}: "
        f"**{fmt(result.threshold)}**. Income is filled into the slabs from the bottom; "
        "each slab is taxed at its own rate."
    )
    lines.append("")
    rows: list[list[str]] = []
    for line in result.slabs:
        rows.append(
            [
                str(line.order),
                line.label,
                fmt(line.lower),
                "and above" if line.upper is None else fmt(line.upper),
                "balance" if line.width is None else fmt(line.width),
                fmt(line.taxable),
                _pct(line.rate),
                fmt(line.tax),
            ]
        )
    rows.append(
        ["", "**Total / মোট**", "", "", "", f"**{fmt(inp.income)}**", "", f"**{fmt(result.gross_tax)}**"]
    )
    lines.append(
        tb.markdown_table(
            ["#", "Slab / ধাপ", "From", "To", "Width", "Taxable in slab", "Rate", "Tax"],
            rows,
            aligns=["r", "l", "r", "r", "r", "r", "r", "r"],
        )
    )
    lines.append("")
    lines.append(
        f"**Gross tax / মোট কর: {fmt(result.gross_tax)}.** Hand check: the *Taxable in slab* "
        "column sums to the total income; the *Tax* column sums to the gross tax."
    )
    lines.append("")

    # -- step 2: rebate ----------------------------------------------------------------
    reb = result.rebate
    lines.append("## Step 2 · বিনিয়োগজনিত কর রেয়াত / Investment rebate")
    lines.append("")
    if not reb.claimed:
        lines.append("No investment was claimed, so no rebate is computed. Tax after rebate = gross tax = "
                     f"**{fmt(reb.tax_after_rebate)}**.")
    else:
        lines.append(
            tb.markdown_table(
                ["Line", "Amount"],
                [
                    ["Investment claimed", fmt(reb.investment)],
                    [f"Cap (a): {_pct(reb.income_cap_percent)} of taxable income {fmt(inp.income)}", fmt(reb.income_cap_amount)],
                    ["Cap (b): absolute ceiling on eligible investment", fmt(reb.absolute_cap)],
                    ["Eligible investment — least of the amount claimed, cap (a) and cap (b)", fmt(reb.eligible)],
                    [f"Rebate at {_pct(reb.rate)} of eligible investment", fmt(reb.rebate_computed)],
                    ["Rebate allowed (cannot exceed gross tax)", fmt(reb.rebate)],
                    ["Gross tax", fmt(reb.gross_tax)],
                    ["**Tax after rebate / রেয়াত-পরবর্তী কর**", f"**{fmt(reb.tax_after_rebate)}**"],
                ],
                aligns=["l", "r"],
            )
        )
        if reb.statutory_formulation_en or reb.statutory_formulation_bn:
            lines.append("")
            lines.append(
                "> ⚠️ **Caps (a) and (b) above are engine parameters that limit the *investment*. "
                "The statute states the same limits as caps on the *rebate*, and those are the "
                "figures to quote — do not quote the two cap figures above to a taxpayer or on a "
                "return.**"
            )
            if reb.statutory_formulation_en:
                lines.append(">")
                lines.append(f"> Statutory wording: {reb.statutory_formulation_en}")
            if reb.statutory_formulation_bn:
                lines.append(">")
                lines.append(f"> আইনের ভাষায়: {reb.statutory_formulation_bn}")
        if reb.capped_by_gross_tax:
            lines.append("")
            lines.append("The computed rebate exceeded the gross tax, so it is limited to the gross tax; "
                         "a rebate never produces a negative liability.")
    lines.append("")

    # -- step 3: minimum tax -----------------------------------------------------------
    mt = result.minimum_tax
    lines.append("## Step 3 · ন্যূনতম কর / Minimum tax")
    lines.append("")
    policy_text = {
        "always": "the location floor always applies",
        "taxable_income_above_threshold": "the location floor applies only when taxable income exceeds the tax-free threshold",
        "never": "no location floor applies for this assessment year",
    }[mt.policy]
    mt_rows: list[list[str]] = [["Policy (`applies_when`)", f"`{mt.policy}` — {policy_text}"]]
    if mt.location_floor is None:
        mt_rows.append(["Location floor", "not applicable"])
    else:
        state = "applies" if mt.location_floor_applies else (
            "does not apply — taxable income is not above the threshold"
        )
        mt_rows.append([f"Location floor — {mt.location_label} (`{mt.location}`)", f"{fmt(mt.location_floor)} — {state}"])
    if mt.gross_receipts is None:
        mt_rows.append(["Gross-receipts floor", "not assessed — no gross receipts were given"])
    elif not mt.receipts_floor_applies:
        mt_rows.append([
            "Gross-receipts floor",
            f"does not apply — receipts {fmt(mt.gross_receipts)} are not above {fmt(mt.receipts_applies_above)}",
        ])
    else:
        mt_rows.append([
            f"Gross-receipts floor — {_pct(mt.receipts_rate)} of {fmt(mt.gross_receipts)} "
            f"(receipts above {fmt(mt.receipts_applies_above)})",
            f"{fmt(mt.receipts_floor)} — applies",
        ])
    mt_rows += [
        ["Minimum tax floor (greater of the applicable floors)", fmt(mt.floor)],
        ["Tax after rebate", fmt(mt.tax_before)],
        ["**Tax after minimum tax / ন্যূনতম কর-পরবর্তী কর (the greater of the two)**", f"**{fmt(mt.tax_after)}**"],
    ]
    lines.append(tb.markdown_table(["Line", "Amount"], mt_rows, aligns=["l", "r"]))
    if mt.floor_bites:
        lines.append("")
        lines.append(f"The minimum tax floor exceeds the tax after rebate, so the liability is lifted by {fmt(mt.adjustment)}.")
    lines.append("")

    # -- step 4: surcharge -------------------------------------------------------------
    sc = result.surcharge
    lines.append("## Step 4 · সারচার্জ / Surcharge")
    lines.append("")
    if not sc.assessed:
        lines.append("Not assessed: no net wealth (নিট সম্পদ) was given. Pass --net-wealth to compute the "
                     "surcharge; it is **not** assumed to be zero.")
    else:
        band_from = "zero" if sc.wealth_above is None else f"above {fmt(sc.wealth_above)}"
        base_text = {
            "tax_before_rebate": "tax on taxable income, before the investment rebate",
            "tax_after_rebate": "tax after rebate",
            "tax_after_minimum": "tax after minimum tax",
        }.get(sc.base, sc.base)
        sc_rows = [
            ["Net wealth", fmt(sc.net_wealth)],
            ["Band", f"{sc.band_order} — {sc.band_label} (net wealth {band_from}) at {_pct(sc.rate)}"],
            [f"Base (`{sc.base}` — {base_text})", fmt(sc.base_amount)],
            [f"Surcharge computed at {_pct(sc.rate)} of the base", fmt(sc.computed)],
        ]
        if sc.minimum is not None:
            sc_rows.append(["Surcharge minimum (applies to a non-zero surcharge)", fmt(sc.minimum)])
        sc_rows.append(["**Surcharge / সারচার্জ**", f"**{fmt(sc.surcharge)}**"])
        lines.append(tb.markdown_table(["Line", "Amount"], sc_rows, aligns=["l", "r"]))
        if sc.lifted_to_minimum:
            lines.append("")
            lines.append("The computed surcharge is below the minimum surcharge, so the minimum applies.")
    lines.append("")

    # -- step 5: summary ---------------------------------------------------------------
    lines.append("## Step 5 · সারসংক্ষেপ / Summary")
    lines.append("")
    net = result.net_payable
    summary_rows = [
        ["Gross tax by slab", fmt(result.gross_tax)],
        ["less: investment rebate", f"({fmt(reb.rebate)})" if reb.rebate.is_positive() else fmt(reb.rebate)],
        ["Tax after rebate", fmt(result.tax_after_rebate)],
        ["add: minimum tax adjustment", fmt(mt.adjustment)],
        ["Tax after minimum tax", fmt(result.tax_after_minimum)],
        ["add: surcharge", fmt(sc.surcharge) if sc.assessed else "not assessed"],
        ["**Total tax liability / মোট করদায়**", f"**{fmt(result.total_tax)}**"],
        ["less: tax already paid (advance tax, TDS)", f"({fmt(inp.tax_paid)})" if inp.tax_paid.is_positive() else fmt(inp.tax_paid)],
    ]
    if net.is_negative():
        summary_rows.append(["**Net position / নিট অবস্থান**", f"**{fmt(-net)} paid in excess (refundable / adjustable)**"])
    else:
        summary_rows.append(["**Net tax payable / নিট প্রদেয় কর**", f"**{fmt(net)}**"])
    lines.append(tb.markdown_table(["Line", "Amount"], summary_rows, aligns=["l", "r"]))
    lines.append("")
    lines.append("All amounts in taka (৳ / BDT), Bangladeshi লাখ/কোটি grouping. Each slab's tax is rounded "
                 "ROUND_HALF_UP to the paisa once, so the rows add up exactly.")
    lines.append("")

    # -- rates used --------------------------------------------------------------------
    lines.append("## Rates used / ব্যবহৃত হার")
    lines.append("")
    rate_rows = []
    for entry in result.rates_used:
        state = "verified" if entry.is_verified else ("PLACEHOLDER" if entry.is_placeholder else "UNVERIFIED")
        rate_rows.append([
            f"`{entry.key}`",
            str(entry.value),
            entry.unit or "—",
            state,
            entry.as_of or "—",
            entry.source or "—",
        ])
    lines.append(tb.markdown_table(["Key", "Value", "Unit", "Status", "As of", "Source"], rate_rows))
    lines.append("")

    # -- caveats -----------------------------------------------------------------------
    lines.append("## Caveats / সতর্কতা")
    lines.append("")
    if result.caveats:
        lines += [f"- {caveat}" for caveat in result.caveats]
    else:
        lines.append("- Every rate used in this computation is marked verified in the rates file.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(tb.DISCLAIMER_EN)
    if language in ("bn", "bn-en"):
        lines.append("")
        lines.append(tb.DISCLAIMER_BN)
    lines.append("")
    lines.append(tb.ATTRIBUTION)
    return "\n".join(lines) + "\n"


def _entry_dict(entry: rt.RateEntry) -> dict[str, Any]:
    return {
        "key": entry.key,
        "value": entry.value,
        "unit": entry.unit,
        "verified": entry.is_verified,
        "placeholder": entry.is_placeholder,
        "source": entry.source,
        "as_of": entry.as_of,
        "label": entry.label,
    }


def to_json_dict(result: TaxComputation) -> dict[str, Any]:
    """An explicit, stable JSON shape (properties are not dataclass fields, so build it)."""
    inp = result.inputs
    reb = result.rebate
    mt = result.minimum_tax
    sc = result.surcharge
    net = result.net_payable
    return {
        "ok": True,
        "tool": "tax.py",
        "version": tb.__version__,
        "assessment_year": result.assessment_year,
        "rates_source": result.rates_source,
        "rates_file": result.rates_path,
        "provisional": result.provisional,
        "filing_status": result.filing_status,
        "data_grade": result.data_grade,
        "placeholder_data_used": result.placeholder_data_used,
        "rates_file_placeholder": result.rates_file_placeholder,
        "allow_placeholder_rates": result.allow_placeholders,
        "placeholder_figures_used": list(result.placeholder_figures),
        "currency": tb.CURRENCY_CODE,
        "amounts": "taka (BDT) as decimal strings; percentages as decimal strings",
        "taxpayer": {"name": result.business_name, "tin": result.tin},
        "inputs": {
            "category": inp.category,
            "category_label": result.category_label,
            "location": inp.location,
            "location_label": mt.location_label,
            "income": inp.income,
            "investment": inp.investment,
            "net_wealth": inp.net_wealth,
            "gross_receipts": inp.gross_receipts,
            "tax_paid": inp.tax_paid,
        },
        "threshold": {"key": result.threshold_key, "amount": result.threshold,
                      "income_above_threshold": result.is_above_threshold},
        "slabs": [
            {
                "order": line.order,
                "label_en": line.label_en,
                "label_bn": line.label_bn,
                "from": line.lower,
                "to": line.upper,
                "width": line.width,
                "open_ended": line.is_open_ended,
                "taxable": line.taxable,
                "rate_percent": line.rate,
                "tax": line.tax,
                "rate_key": line.rate_key,
                "width_key": line.width_key,
            }
            for line in result.slabs
        ],
        "gross_tax": result.gross_tax,
        "rebate": {
            "claimed": reb.claimed,
            "formula": reb.formula,
            "investment": reb.investment,
            "rate_percent": reb.rate,
            "income_cap_percent": reb.income_cap_percent,
            "income_cap_amount": reb.income_cap_amount,
            "absolute_cap": reb.absolute_cap,
            "eligible": reb.eligible,
            "rebate_computed": reb.rebate_computed,
            "rebate": reb.rebate,
            "capped_by_gross_tax": reb.capped_by_gross_tax,
            "tax_after_rebate": reb.tax_after_rebate,
            # income_cap_percent and absolute_cap above cap the INVESTMENT; these two strings
            # are how the statute words the same limits (as caps on the REBATE).  Quote these.
            "statutory_formulation_en": reb.statutory_formulation_en,
            "statutory_formulation_bn": reb.statutory_formulation_bn,
        },
        "minimum_tax": {
            "policy": mt.policy,
            "location": mt.location,
            "location_label": mt.location_label,
            "location_floor": mt.location_floor,
            "location_floor_applies": mt.location_floor_applies,
            "gross_receipts": mt.gross_receipts,
            "receipts_applies_above": mt.receipts_applies_above,
            "receipts_rate_percent": mt.receipts_rate,
            "receipts_floor": mt.receipts_floor,
            "receipts_floor_applies": mt.receipts_floor_applies,
            "floor": mt.floor,
            "tax_before": mt.tax_before,
            "adjustment": mt.adjustment,
            "tax_after": mt.tax_after,
        },
        "surcharge": {
            "assessed": sc.assessed,
            "net_wealth": sc.net_wealth,
            "band_order": sc.band_order,
            "band_label_en": sc.band_label_en,
            "band_label_bn": sc.band_label_bn,
            "wealth_above": sc.wealth_above,
            "rate_percent": sc.rate,
            "base": sc.base,
            "base_amount": sc.base_amount,
            "computed": sc.computed,
            "minimum": sc.minimum,
            "lifted_to_minimum": sc.lifted_to_minimum,
            "surcharge": sc.surcharge,
        },
        "summary": {
            "gross_tax": result.gross_tax,
            "rebate": reb.rebate,
            "tax_after_rebate": result.tax_after_rebate,
            "minimum_tax_adjustment": mt.adjustment,
            "tax_after_minimum": result.tax_after_minimum,
            "surcharge": sc.surcharge,
            "surcharge_assessed": sc.assessed,
            "total_tax": result.total_tax,
            "tax_paid": inp.tax_paid,
            "net_payable": net,
            "refundable": (-net) if net.is_negative() else tb.Money.zero(),
        },
        "rates_used": [_entry_dict(e) for e in result.rates_used],
        "caveats": list(result.caveats),
        "warnings": list(result.warnings),
        "blocking_problems": list(result.blocking_problems()),
        "disclaimer": {"en": tb.DISCLAIMER_EN, "bn": tb.DISCLAIMER_BN},
        "attribution": tb.ATTRIBUTION,
    }


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------


def load_config_if_present(books_dir: "Path | str") -> tb.Config | None:
    """``books/config.toml`` when it exists.  A calculator may run without books, but a
    config that *exists* and is broken is an error, not something to skip past."""
    if not tb.config_path(books_dir).is_file():
        return None
    return tb.Config.load(books_dir)


def _parse_money(text: str | None, *, flag: str) -> tb.Money | None:
    if text is None:
        return None
    try:
        amount = tb.Money.from_str(text, what=flag)
    except tb.MoneyError as exc:
        # Money.from_str already names the flag in its message.
        raise tb.ValidationError(
            exc.message, problems=(f"{flag}={text!r}",), hint=exc.hint
        ) from None
    if amount.is_negative():
        raise tb.ValidationError(
            f"{flag} cannot be negative ({amount.bdt}).",
            problems=(f"{flag}={text!r}",),
            hint="Enter 0 for a loss year; TakaBooks does not compute a negative income.",
        )
    return amount


def _check_assessment_year(
    rates: rt.RateSet, config: tb.Config | None, *, explicit: bool
) -> list[str]:
    """Cross-check the rates file's করবর্ষ against config.toml.

    A mismatch is an error unless the user chose the rates explicitly (``--rates`` or
    ``--assessment-year``), in which case it is a loud warning in the output.
    """
    if config is None or not config.assessment_year:
        return []
    wanted = rt.normalise_assessment_year(config.assessment_year)
    got = rates.require_assessment_year()
    if rt.normalise_assessment_year(got) == wanted:
        return []
    message = (
        f"config.toml states {tb.term('assessment_year')} {wanted}, but the rates file "
        f"{rates.filename} is for {got}."
    )
    if explicit:
        return [message + " The explicitly chosen rates file was used."]
    raise tb.RatesError(
        message,
        hint="Fix books.assessment_year or books.rates_file in config.toml, or pass "
        "--assessment-year / --rates to choose the file deliberately.",
    )


def build_parser() -> "tb.argparse.ArgumentParser":  # type: ignore[name-defined]
    parser = tb.common_parser(
        "tax.py",
        f"{tb.term('income_tax')} for an individual {tb.term('taxpayer')}: progressive "
        "slabs, investment rebate, minimum tax and surcharge, with the full working.\n"
        "Every figure comes from the rates file for the assessment year; nothing is "
        "hardcoded.",
    )
    money = parser.add_argument_group("taxpayer figures (taka / BDT)")
    money.add_argument("--income", metavar="BDT", default=None,
                       help="total taxable income for the income year (required)")
    money.add_argument("--investment", metavar="BDT", default="0",
                       help="allowable investment claimed for the rebate (default 0)")
    money.add_argument("--net-wealth", metavar="BDT", default=None,
                       help="net wealth for the surcharge; omit and the surcharge is not assessed")
    money.add_argument("--gross-receipts", metavar="BDT", default=None,
                       help="gross receipts / turnover, for the minimum tax on receipts")
    money.add_argument("--tax-paid", metavar="BDT", default="0",
                       help="tax already paid: advance tax and TDS (default 0)")
    who = parser.add_argument_group("taxpayer profile")
    who.add_argument("--category", metavar="ID", default=None,
                     help="taxpayer category id from the rates file (see --list-options); "
                          "default: the rates file's default_category")
    who.add_argument("--location", metavar="TIER", default=None,
                     help="minimum-tax location tier id (see --list-options); "
                          "default: the rates file's default_location")
    which = parser.add_argument_group("rates file")
    which.add_argument("--assessment-year", metavar="AY", default=None,
                       help='assessment year / করবর্ষ, e.g. "2026-27" (default: config.toml)')
    which.add_argument("--rates", metavar="PATH", default=None,
                       help="use this rates TOML directly")
    which.add_argument("--data-dir", metavar="DIR", default=None,
                       help="directory holding rates-AY<year>.toml (default: src/data)")
    which.add_argument(ALLOW_PLACEHOLDERS_FLAG, dest="allow_placeholder_rates",
                       action="store_true",
                       help="compute from placeholder (unlanded) rates; the output is "
                            "stamped PLACEHOLDER and must not be filed")
    which.add_argument("--strict", action="store_true",
                       help="exit non-zero if any figure used is unverified, a placeholder, "
                            "or missing (the same posture as vat.py --strict)")
    out = parser.add_argument_group("output")
    out.add_argument("--language", choices=_LANGUAGES, default=None,
                     help="add the Bangla disclaimer (bn, bn-en); default: config.toml locale")
    out.add_argument("--list-options", action="store_true",
                     help="list the taxpayer categories and location tiers the rates file "
                          "defines, then exit")
    return parser


def main(argv: "Sequence[str] | None" = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    with tb.cli_guard(json_output=args.json):
        config = load_config_if_present(args.books)
        explicit = bool(args.rates) or bool(args.assessment_year)
        rates = rt.resolve_rates(
            path=args.rates,
            assessment_year=args.assessment_year,
            config=config,
            data_dir=args.data_dir,
            allow_placeholders=args.allow_placeholder_rates,
        )

        if args.list_options:
            categories = _labelled_options(rates, KEY_THRESHOLDS)
            locations = _labelled_options(rates, KEY_MINIMUM_TAX_BY_LOCATION)
            individual = rates.section(KEY_INDIVIDUAL)
            if args.json:
                print(tb.json_dumps({
                    "ok": True,
                    "assessment_year": rates.assessment_year,
                    "rates_source": rates.provenance(),
                    "default_category": individual.get("default_category"),
                    "default_location": individual.get("default_location"),
                    "categories": [{"id": k, "label": v} for k, v in categories],
                    "locations": [{"id": k, "label": v} for k, v in locations],
                }))
            else:
                print(rates.provenance())
                print()
                print("Taxpayer categories / করদাতার শ্রেণি (--category):")
                for key, label in categories:
                    print(f"  {key:<48} {label}")
                print()
                print("Location tiers / এলাকা (--location):")
                for key, label in locations:
                    print(f"  {key:<48} {label}")
                print()
                print(f"Defaults: --category {individual.get('default_category') or '(none)'}"
                      f" --location {individual.get('default_location') or '(none)'}")
            return 0

        if args.income is None:
            parser.error("--income is required (or use --list-options)")

        warnings = _check_assessment_year(rates, config, explicit=explicit)
        category = args.category or _default_option(rates, "default_category", "--category", KEY_THRESHOLDS)
        location = args.location or _default_option(
            rates, "default_location", "--location", KEY_MINIMUM_TAX_BY_LOCATION
        )
        inputs = TaxInputs(
            income=_parse_money(args.income, flag="--income"),
            category=category,
            location=location,
            investment=_parse_money(args.investment, flag="--investment"),
            net_wealth=_parse_money(args.net_wealth, flag="--net-wealth"),
            gross_receipts=_parse_money(args.gross_receipts, flag="--gross-receipts"),
            tax_paid=_parse_money(args.tax_paid, flag="--tax-paid"),
        )
        result = compute_income_tax(rates, inputs, config=config, warnings=warnings)

        if args.json:
            print(tb.json_dumps(to_json_dict(result)))
        else:
            language = args.language or (config.language if config else "en")
            sys.stdout.write(render_markdown(result, language=language, config=config))

        # --strict runs AFTER the output so the user still sees the working they asked
        # for, then the refusal — the same order vat.py --strict uses.
        if args.strict:
            problems = result.blocking_problems()
            if problems:
                raise tb.ValidationError(
                    f"--strict: this {tb.term('income_tax')} computation is not ready to "
                    f"file — {len(problems)} problem(s) must be resolved first:\n  - "
                    + "\n  - ".join(problems),
                    problems=problems,
                    hint="Confirm each unverified figure with the NBR and land every "
                    "placeholder in the rates TOML with its source URL.",
                )
        return 0


if __name__ == "__main__":  # pragma: no cover - exercised via subprocess in tests
    tb.check_python_or_exit()
    raise SystemExit(main())
