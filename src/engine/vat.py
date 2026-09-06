#!/usr/bin/env python3
"""TakaBooks — মূসক / VAT position from the journal (spec §4.6).

Computes, for a chosen period, every figure a মূসক-registered (VAT-registered)
business needs in order to fill its monthly return:

* **উৎপাদ কর / output VAT** — total taxable supply value and the VAT charged on it,
  broken down by the rate written on each posting.
* **রেয়াতযোগ্য উপকরণ কর / rebateable input VAT** — purchase value and the input tax
  claimed against it, broken down by rate.
* **নিট অবস্থান / net position** — output tax less rebateable input tax, presented as
  either net VAT payable or excess input tax carried forward.
* **উৎসে মূসক কর্তন / VDS** — VAT deducted at source and withheld from suppliers.
* **input / output reconciliation** — every VAT control account's opening balance,
  the movement explained by tagged postings, the movement that is *not* explained,
  and the closing balance.

Where the numbers come from
---------------------------
1. **The journal.**  Amounts are the amounts posted in ``books/journal/YYYY-MM.csv``.
2. **The ``tax_tag`` on each posting.**  The percentage in ``VAT:OUT:<rate>``,
   ``VAT:IN:<rate>`` and ``VDS:<rate>`` is the rate the bookkeeper recorded for that
   transaction.  TakaBooks uses it as written.
3. **The rates TOML** (``src/data/rates-AY<year>.toml``, read through
   :class:`takabooks.RatesTable`) for every *statutory* figure.  The dotted keys this
   module reads, and nothing else, are:

   ================================================  =========  ==============================
   key                                               required   used for
   ================================================  =========  ==============================
   ``vat.rates.standard``                            always     every tagged rate is checked
                                                                against the declared rates
   ``deadlines.vat_return_monthly``                  always     when the return is due
   ``vds.deposit.deadline``                          with VDS   when withheld VDS is due
   ``vat.rates.zero_rated``                          optional   declared rate
   ``vat.rates.reduced.<key>``                       optional   declared rates (one per node)
   ``vds.services.<key>``                            optional   declared VDS rates
   ``vat.thresholds.registration``                   optional   reference
   ``vat.thresholds.turnover_tax_enlistment``        optional   reference
   ``vat.turnover_tax.rate``                         optional   reference
   ``vat.return_form.line``                          optional   NBR form line map (array)
   ================================================  =========  ==============================

**This module hardcodes no Bangladeshi rate, threshold or deadline** (spec §4.5, §6.2).

* A **required** key that is absent from the rates file is a :class:`takabooks.RatesError`
  (exit 8) naming the key and the file.  TakaBooks never fills it in.
* An **optional** key that is absent is reported as ``not in rates file`` on every output
  format, and never guessed.
* A figure present but not ``verified = true`` carries a visible **UNVERIFIED** warning;
  a figure carrying ``placeholder = true`` (schema awaiting research) is reported as
  **PLACEHOLDER** and is never compared against the journal.
* When the file itself is a placeholder (``[meta] placeholder = true``), or any figure
  read is unverified or missing, or any entry fails to reconcile, the whole output is
  stamped **PROVISIONAL / অস্থায়ী — not for filing**.

``--strict`` turns every warning, and any reconciliation difference, into a non-zero
exit (7) so that an unconfirmed figure set can never be mistaken for a filing-ready one.

Tagging convention this module reads
------------------------------------
A VAT-bearing journal entry has two kinds of tagged line, and TakaBooks tells them apart
by the **role** declared on the account in ``accounts.toml`` (spec §4.4), never by
guessing:

* a line hitting the account with ``role = "vat_output"`` / ``"vat_input"`` /
  ``"vds_payable"`` is the **tax line** — its amount *is* the VAT;
* any other line carrying the same tag is a **value line** — its amount is the taxable
  value the VAT was computed on.

So a 15% sale is written::

    2026-07-05,S-001,Sale to Rahim Traders,1210,11500.00,,Rahim Traders,INV-1,NONE,
    2026-07-05,S-001,Sale to Rahim Traders,4100,,10000.00,Rahim Traders,INV-1,VAT:OUT:15,
    2026-07-05,S-001,Sale to Rahim Traders,2310,,1500.00,Rahim Traders,INV-1,VAT:OUT:15,

``4100`` (income) is the value line, ``2310`` (``role = "vat_output"``) is the tax line.
Both sides are then cross-checked: value × rate must equal the tax posted, and every
entry where it does not is reported by ``entry_id``, with its file and line.

Usage::

    python3 vat.py --books books --period 2026-07
    python3 vat.py --books books --since 2026-07-01 --until 2026-09-30 --format csv
    python3 vat.py --books books --json
    python3 vat.py --books books --period 2026-07 --strict

TakaBooks — Moshiur Rahman (@bemoshiur) · Ticon Sys — https://ticonsys.com
"""

from __future__ import annotations

import argparse
import calendar
import csv
import datetime
import io
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

_ENGINE_DIR = Path(__file__).resolve().parent
if str(_ENGINE_DIR) not in sys.path:  # pragma: no cover - import plumbing
    sys.path.insert(0, str(_ENGINE_DIR))

import takabooks as tb  # noqa: E402

__all__ = [
    "TOOL_NAME",
    "DATA_DIRNAME",
    "RATES_GLOB",
    "KIND_LABELS",
    "KIND_ROLE",
    "REQUIRED_ALWAYS",
    "REQUIRED_WITH_VDS",
    "OPTIONAL",
    "ReferenceSpec",
    "REFERENCE_SPECS",
    "VAT_RATE_NODES",
    "VAT_RATE_SECTIONS",
    "VDS_RATE_SECTIONS",
    "RETURN_FORM_KEY",
    "STATUS_PROVISIONAL",
    "STATUS_RECONCILED",
    "AccountMovement",
    "RateBucket",
    "ReconciliationIssue",
    "ControlAccount",
    "ReferenceFigure",
    "DeclaredRate",
    "ReturnFigure",
    "ReturnFormLine",
    "VatPosition",
    "rate_text",
    "resolve_period",
    "resolve_rates_path",
    "load_rates",
    "rates_file_is_placeholder",
    "reference_figures",
    "declared_rates",
    "compute_vat_position",
    "render_markdown",
    "render_csv",
    "position_payload",
    "render_json",
    "build_parser",
    "run",
    "main",
]

TOOL_NAME = "vat.py"
DATA_DIRNAME = "data"
RATES_GLOB = "rates-AY*.toml"

#: ``src/data`` — the sibling of ``src/engine`` where the rates TOMLs live (spec §3).
DATA_DIR = _ENGINE_DIR.parent / DATA_DIRNAME

_MONTH_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")

#: Bangla / English label pair per tax-tag kind handled here.
KIND_LABELS: dict[str, tuple[str, str]] = {
    tb.TAG_VAT_OUT: ("উৎপাদ কর", "output VAT"),
    tb.TAG_VAT_IN: ("রেয়াতযোগ্য উপকরণ কর", "rebateable input VAT"),
    tb.TAG_VDS: ("উৎসে মূসক কর্তন", "VAT deducted at source (VDS)"),
}

#: The chart-of-accounts role that identifies the *tax line* for each kind.
KIND_ROLE: dict[str, str] = {
    tb.TAG_VAT_OUT: tb.ROLE_VAT_OUTPUT,
    tb.TAG_VAT_IN: tb.ROLE_VAT_INPUT,
    tb.TAG_VDS: tb.ROLE_VDS_PAYABLE,
}

_KIND_ORDER: tuple[str, ...] = (tb.TAG_VAT_OUT, tb.TAG_VAT_IN, tb.TAG_VDS)


def rate_text(rate: Decimal) -> str:
    """``Decimal('15.00')`` -> ``'15'``; ``Decimal('7.50')`` -> ``'7.5'``."""
    normalised = Decimal(rate).normalize()
    if normalised == normalised.to_integral_value():
        normalised = normalised.quantize(Decimal(1))
    return format(normalised, "f")


# ======================================================================================
# Reference figures read from the rates TOML
# ======================================================================================


#: ``ReferenceSpec.required`` values.
REQUIRED_ALWAYS = "always"
REQUIRED_WITH_VDS = "with_vds"
OPTIONAL = "optional"


@dataclass(frozen=True)
class ReferenceSpec:
    """A statutory figure this module reads from the rates TOML, and where it lives.

    ``rates_key`` is the *one* dotted key the figure is read from — the key paths are
    documented in the rates file itself, so there is nothing to search for.  Nothing here
    asserts a value, only where a value would live and why the return preparer needs it.
    """

    key: str
    rates_key: str
    label_bn: str
    label_en: str
    kind: str  # "percent" | "money" | "text"
    required: str  # REQUIRED_ALWAYS | REQUIRED_WITH_VDS | OPTIONAL
    why: str

    @property
    def label(self) -> str:
        return f"{self.label_bn} / {self.label_en}"


#: Every figure vat.py reads from the rates file.  A required figure that is absent is a
#: hard RatesError; an optional one is reported as ``not in rates file``.  TakaBooks never
#: fills one in.
REFERENCE_SPECS: tuple[ReferenceSpec, ...] = (
    ReferenceSpec(
        "standard_rate",
        "vat.rates.standard",
        "প্রমিত মূসক হার",
        "Standard VAT rate",
        "percent",
        REQUIRED_ALWAYS,
        "every rate written in a tax_tag is checked against the rates the file declares",
    ),
    ReferenceSpec(
        "zero_rate",
        "vat.rates.zero_rated",
        "শূন্যহার সরবরাহ",
        "Zero-rated supplies",
        "percent",
        OPTIONAL,
        "a declared rate; zero-rated output keeps input VAT rebateable",
    ),
    ReferenceSpec(
        "registration_threshold",
        "vat.thresholds.registration",
        "মূসক নিবন্ধনের সীমা",
        "VAT registration threshold (annual turnover)",
        "money",
        OPTIONAL,
        "context for whether registration is obligatory",
    ),
    ReferenceSpec(
        "turnover_tax_enlistment_threshold",
        "vat.thresholds.turnover_tax_enlistment",
        "টার্নওভার কর তালিকাভুক্তির সীমা",
        "Turnover tax enlistment threshold (annual turnover)",
        "money",
        OPTIONAL,
        "context for enlisted (not registered) persons",
    ),
    ReferenceSpec(
        "turnover_tax_rate",
        "vat.turnover_tax.rate",
        "টার্নওভার করের হার",
        "Turnover tax rate",
        "percent",
        OPTIONAL,
        "context for enlisted (not registered) persons",
    ),
    ReferenceSpec(
        "return_deadline",
        "deadlines.vat_return_monthly",
        "মাসিক মূসক দাখিলপত্র জমার সময়সীমা",
        "Monthly VAT return filing deadline",
        "text",
        REQUIRED_ALWAYS,
        "a return figure set must say when the return is due",
    ),
    ReferenceSpec(
        "vds_deposit_deadline",
        "vds.deposit.deadline",
        "উৎসে কর্তিত মূসক জমার সময়সীমা",
        "Deadline to deposit VDS withheld from suppliers",
        "text",
        REQUIRED_WITH_VDS,
        "withheld VDS is a deposit obligation with its own deadline",
    ),
)

#: Single rate nodes that declare a VAT rate for the assessment year.
VAT_RATE_NODES: tuple[str, ...] = ("vat.rates.standard", "vat.rates.zero_rated")
#: Sections whose child tables (each carrying ``value``) each declare one VAT rate.
VAT_RATE_SECTIONS: tuple[str, ...] = ("vat.rates.reduced",)
#: Sections whose child tables each declare one VDS withholding rate.
VDS_RATE_SECTIONS: tuple[str, ...] = ("vds.services",)

#: Optional section carrying an NBR return-form line map as ``[[vat.return_form.line]]``
#: tables (``line``, ``figure``, ``label_en``, ``label_bn``).  TakaBooks does not assert
#: any form line number of its own (content rule §6.2).
RETURN_FORM_KEY = "vat.return_form"

#: Filing status stamped on every output format.
STATUS_PROVISIONAL = "PROVISIONAL / অস্থায়ী — not for filing"
STATUS_RECONCILED = "reconciled — every figure read is verified; confirm with an ITP/CA"


# ======================================================================================
# Value objects
# ======================================================================================


@dataclass(frozen=True)
class AccountMovement:
    """What one account contributed to one bucket, in its own natural direction."""

    code: str
    name: str
    name_bn: str
    debit: tb.Money
    credit: tb.Money
    natural: tb.Money

    @property
    def label(self) -> str:
        return f"{self.code} {self.name}" + (f" ({self.name_bn})" if self.name_bn else "")


@dataclass(frozen=True)
class RateBucket:
    """Every posting of one kind carrying one rate, split into value and tax lines."""

    kind: str
    rate: Decimal
    taxable_value: tb.Money
    posted_tax: tb.Money
    expected_tax: tb.Money
    tax_source: str  # "posted" (a tax-account line exists) | "derived" (from the tag rate)
    entry_ids: tuple[str, ...]
    value_accounts: tuple[AccountMovement, ...]
    tax_accounts: tuple[AccountMovement, ...]

    @property
    def vat_amount(self) -> tb.Money:
        """The VAT for this bucket: what was posted, or — when nothing was posted to the
        control account — what the tag rate implies."""
        return self.posted_tax if self.tax_source == "posted" else self.expected_tax

    @property
    def variance(self) -> tb.Money:
        """Posted tax minus the tax the tagged value and rate imply."""
        return self.posted_tax - self.expected_tax

    @property
    def rate_text(self) -> str:
        return rate_text(self.rate)

    @property
    def tag_text(self) -> str:
        if self.kind == tb.TAG_VAT_OUT:
            return f"VAT:OUT:{self.rate_text}"
        if self.kind == tb.TAG_VAT_IN:
            return f"VAT:IN:{self.rate_text}"
        return f"VDS:{self.rate_text}"


@dataclass(frozen=True)
class ReconciliationIssue:
    """One entry whose posted VAT does not equal value × the rate on its own tag."""

    entry_id: str
    kind: str
    rate: Decimal
    taxable_value: tb.Money
    expected_tax: tb.Money
    posted_tax: tb.Money
    location: str

    @property
    def difference(self) -> tb.Money:
        return self.posted_tax - self.expected_tax

    @property
    def rate_text(self) -> str:
        return rate_text(self.rate)

    def message(self) -> str:
        bn, en = KIND_LABELS[self.kind]
        where = f" [{self.location}]" if self.location else ""
        return (
            f"entry {self.entry_id}: {bn} / {en} at {self.rate_text}% — taxable value "
            f"{tb.format_bdt(self.taxable_value, symbol=True)} implies "
            f"{tb.format_bdt(self.expected_tax, symbol=True)}, but "
            f"{tb.format_bdt(self.posted_tax, symbol=True)} is posted to the control "
            f"account (difference {tb.format_bdt(self.difference, symbol=True)}){where}"
        )


@dataclass(frozen=True)
class ControlAccount:
    """A VAT control account's opening balance, period movement and closing balance."""

    role: str
    code: str
    name: str
    name_bn: str
    opening: tb.Money
    movement: tb.Money
    closing: tb.Money
    tagged: tb.Money

    @property
    def untagged(self) -> tb.Money:
        """Movement not explained by a tagged posting — payments, adjustments, errors."""
        return self.movement - self.tagged

    @property
    def label(self) -> str:
        return f"{self.code} {self.name}" + (f" ({self.name_bn})" if self.name_bn else "")


@dataclass(frozen=True)
class ReferenceFigure:
    """A statutory figure quoted from the rates TOML — or its documented absence."""

    key: str
    label_bn: str
    label_en: str
    kind: str
    available: bool
    rates_key: str = ""
    required: str = OPTIONAL
    raw_value: Any = None
    display: str = ""
    verified: bool = False
    placeholder: bool = False
    source: str = ""
    as_of: str = ""
    note: str = ""
    money: tb.Money | None = None
    problem: str = ""

    @property
    def label(self) -> str:
        return f"{self.label_bn} / {self.label_en}"

    @property
    def usable(self) -> bool:
        """Present, readable, and not a placeholder — safe to compare the journal against."""
        return self.available and not self.problem and not self.placeholder

    @property
    def status(self) -> str:
        if not self.available:
            return "not in rates file"
        if self.placeholder:
            return "PLACEHOLDER"
        return "verified" if self.verified else "UNVERIFIED"


@dataclass(frozen=True)
class DeclaredRate:
    """One rate the rates file declares for this assessment year (never one TakaBooks
    asserts).  Tagged journal rates are checked against the set of these."""

    scope: str  # "vat" | "vds"
    rates_key: str
    label_bn: str
    label_en: str
    rate: Decimal | None
    verified: bool = False
    placeholder: bool = False
    problem: str = ""

    @property
    def label(self) -> str:
        return f"{self.label_bn} / {self.label_en}".strip(" /")

    @property
    def usable(self) -> bool:
        return self.rate is not None and not self.problem and not self.placeholder

    @property
    def status(self) -> str:
        if self.problem:
            return "UNREADABLE"
        if self.placeholder:
            return "PLACEHOLDER"
        return "verified" if self.verified else "UNVERIFIED"

    @property
    def rate_text(self) -> str:
        return rate_text(self.rate) + "%" if self.rate is not None else "—"


@dataclass(frozen=True)
class ReturnFigure:
    """One line of the figure set the monthly return asks for."""

    key: str
    label_bn: str
    label_en: str
    amount: tb.Money
    note: str = ""

    @property
    def label(self) -> str:
        return f"{self.label_bn} / {self.label_en}"


@dataclass(frozen=True)
class ReturnFormLine:
    """A form line declared by the rates file, mapped onto a computed figure."""

    line: str
    label_bn: str
    label_en: str
    figure_key: str
    amount: tb.Money | None
    problem: str = ""


@dataclass(frozen=True)
class VatPosition:
    """Everything ``vat.py`` computed, in one immutable object."""

    config: tb.Config | None
    books_dir: Path | None
    assessment_year: str
    period_start: datetime.date | None
    period_end: datetime.date | None
    period_label: str
    rates_path: Path | None
    rates_assessment_year: str | None
    rates_provenance: str
    rates_caveats: tuple[str, ...]
    rates_file_placeholder: bool
    rates_unverified_in_file: int
    buckets: Mapping[str, tuple[RateBucket, ...]]
    issues: tuple[ReconciliationIssue, ...]
    controls: tuple[ControlAccount, ...]
    references: tuple[ReferenceFigure, ...]
    declared: tuple[DeclaredRate, ...]
    return_form: tuple[ReturnFormLine, ...]
    warnings: tuple[str, ...]
    notes: tuple[str, ...]
    posting_count: int
    entry_count: int
    tds_posting_count: int

    # -- filing status -------------------------------------------------------------------

    @property
    def provisional(self) -> bool:
        """True when anything stops this figure set from being filing-ready."""
        return self.rates_file_placeholder or bool(self.warnings) or bool(self.issues)

    @property
    def filing_status(self) -> str:
        return STATUS_PROVISIONAL if self.provisional else STATUS_RECONCILED

    # -- totals ------------------------------------------------------------------------

    def _sum(self, kind: str, attr: str) -> tb.Money:
        return tb.Money.sum(getattr(bucket, attr) for bucket in self.buckets.get(kind, ()))

    @property
    def output_taxable_value(self) -> tb.Money:
        return self._sum(tb.TAG_VAT_OUT, "taxable_value")

    @property
    def output_tax(self) -> tb.Money:
        return self._sum(tb.TAG_VAT_OUT, "vat_amount")

    @property
    def input_taxable_value(self) -> tb.Money:
        return self._sum(tb.TAG_VAT_IN, "taxable_value")

    @property
    def input_tax(self) -> tb.Money:
        return self._sum(tb.TAG_VAT_IN, "vat_amount")

    @property
    def vds_supply_value(self) -> tb.Money:
        return self._sum(tb.TAG_VDS, "taxable_value")

    @property
    def vds_withheld(self) -> tb.Money:
        return self._sum(tb.TAG_VDS, "vat_amount")

    @property
    def net(self) -> tb.Money:
        """Output tax less rebateable input tax.  Positive means payable."""
        return self.output_tax - self.input_tax

    @property
    def net_payable(self) -> tb.Money:
        net = self.net
        return net if net.is_positive() else tb.Money.zero()

    @property
    def carry_forward(self) -> tb.Money:
        net = self.net
        return -net if net.is_negative() else tb.Money.zero()

    # -- derived views -------------------------------------------------------------------

    def return_figures(self) -> tuple[ReturnFigure, ...]:
        """The figure set the monthly return asks for, in filing order."""
        carry = self.carry_forward
        payable = self.net_payable
        return (
            ReturnFigure(
                "output.taxable_value",
                "করযোগ্য সরবরাহের মোট মূল্য",
                "Total value of taxable supplies",
                self.output_taxable_value,
            ),
            ReturnFigure(
                "output.tax",
                "প্রদেয় উৎপাদ কর",
                "Output VAT charged on those supplies",
                self.output_tax,
            ),
            ReturnFigure(
                "input.taxable_value",
                "রেয়াতযোগ্য উপকরণের মোট মূল্য",
                "Total value of purchases carrying rebateable input VAT",
                self.input_taxable_value,
            ),
            ReturnFigure(
                "input.tax",
                "রেয়াতযোগ্য উপকরণ কর",
                "Rebateable input VAT on those purchases",
                self.input_tax,
            ),
            ReturnFigure(
                "net.output_less_input",
                "উৎপাদ কর বাদ উপকরণ কর",
                "Output VAT less rebateable input VAT",
                self.net,
                note="negative means input VAT exceeded output VAT",
            ),
            ReturnFigure(
                "net.payable",
                "নিট প্রদেয় মূসক",
                "Net VAT payable for the period",
                payable,
                note="zero when rebateable input VAT exceeds output VAT",
            ),
            ReturnFigure(
                "net.carry_forward",
                "জের টানা উদ্বৃত্ত উপকরণ কর",
                "Excess input VAT carried forward",
                carry,
                note="zero when output VAT exceeds rebateable input VAT",
            ),
            ReturnFigure(
                "vds.supply_value",
                "উৎসে কর্তনের আওতাধীন সরবরাহের মূল্য",
                "Value of supplies on which VDS was applied",
                self.vds_supply_value,
            ),
            ReturnFigure(
                "vds.withheld",
                "উৎসে কর্তিত মূসক",
                "VDS withheld from suppliers and payable to the treasury",
                self.vds_withheld,
                note="a separate deposit obligation; not netted against the figure above",
            ),
        )

    def figure_map(self) -> dict[str, ReturnFigure]:
        return {figure.key: figure for figure in self.return_figures()}

    def blocking_problems(self) -> tuple[str, ...]:
        """Everything ``--strict`` refuses to produce a filing-ready figure set over."""
        return tuple([issue.message() for issue in self.issues] + list(self.warnings))


# ======================================================================================
# Period, rates file and chart plumbing
# ======================================================================================


def resolve_period(
    *,
    period: str | None = None,
    since: str | datetime.date | None = None,
    until: str | datetime.date | None = None,
) -> tuple[datetime.date | None, datetime.date | None, str]:
    """Turn CLI period arguments into an inclusive ``(start, end, label)`` window."""
    if period and (since or until):
        raise tb.ConfigError(
            "--period cannot be combined with --since/--until.",
            hint="Use --period YYYY-MM for one month, or --since/--until for a range.",
        )
    if period:
        match = _MONTH_RE.match(str(period).strip())
        if not match:
            raise tb.ConfigError(
                f"--period {period!r} must be written YYYY-MM, e.g. 2026-07.",
                hint="A VAT return period is one calendar month.",
            )
        year, month = int(match.group(1)), int(match.group(2))
        last_day = calendar.monthrange(year, month)[1]
        start = datetime.date(year, month, 1)
        end = datetime.date(year, month, last_day)
        return start, end, f"{year:04d}-{month:02d}"

    start_date = tb.parse_date(since, field_name="--since") if since else None
    end_date = tb.parse_date(until, field_name="--until") if until else None
    if start_date and end_date and end_date < start_date:
        raise tb.ConfigError(
            f"--until {end_date.isoformat()} is before --since {start_date.isoformat()}."
        )
    if start_date and end_date:
        label = f"{start_date.isoformat()} to {end_date.isoformat()}"
    elif start_date:
        label = f"from {start_date.isoformat()}"
    elif end_date:
        label = f"up to {end_date.isoformat()}"
    else:
        label = "every posting in the books"
    return start_date, end_date, label


def resolve_rates_path(
    *,
    explicit: str | Path | None = None,
    config: tb.Config | None = None,
    books_dir: Path | str | None = None,
    data_dir: Path | str | None = None,
) -> Path:
    """Find the rates TOML to read, without ever guessing a figure.

    Order: ``--rates`` · ``books.rates_file`` from ``config.toml`` · the
    ``rates-AY<assessment year>.toml`` in ``src/data`` · the single ``rates-AY*.toml``
    in ``src/data`` when there is exactly one.  Anything else is a loud
    :class:`takabooks.RatesError`.
    """
    data_root = Path(data_dir) if data_dir is not None else DATA_DIR
    if explicit:
        return Path(explicit)

    tried: list[Path] = []
    if config is not None and config.rates_file:
        candidates: list[Path] = []
        if books_dir is not None:
            candidates.append(Path(books_dir) / config.rates_file)
        candidates.append(Path(config.rates_file))
        candidates.append(data_root / Path(config.rates_file).name)
        for candidate in candidates:
            if candidate.is_file():
                return candidate
            tried.append(candidate)
        raise tb.RatesError(
            f"books.rates_file = {config.rates_file!r} was not found. Tried: "
            + ", ".join(str(path) for path in tried)
            + ".",
            hint="Fix books.rates_file in config.toml, or pass --rates <path>.",
        )

    year = config.assessment_year if config is not None else None
    if year:
        candidate = data_root / f"rates-AY{year}.toml"
        if candidate.is_file():
            return candidate
        tried.append(candidate)

    found = sorted(data_root.glob(RATES_GLOB)) if data_root.is_dir() else []
    if len(found) == 1:
        return found[0]
    if len(found) > 1:
        raise tb.RatesError(
            f"{data_root} holds several rates files "
            f"({', '.join(path.name for path in found)}); TakaBooks will not choose one "
            "for you.",
            hint="Pass --rates <path>, or set books.rates_file in config.toml.",
        )
    attempted = ", ".join(str(path) for path in tried) if tried else str(data_root / RATES_GLOB)
    raise tb.RatesError(
        f"No rates file found (looked for {attempted}). TakaBooks computes no "
        f"{tb.term('vat')} figure without the rates file for the {tb.term('assessment_year')}.",
        hint="Pass --rates <path>, set books.rates_file in config.toml, or add "
        f"{DATA_DIRNAME}/rates-AY<year>.toml to the source tree.",
    )


def load_rates(
    *,
    explicit: str | Path | None = None,
    config: tb.Config | None = None,
    books_dir: Path | str | None = None,
    data_dir: Path | str | None = None,
    allow_ay_mismatch: bool = False,
) -> tuple[tb.RatesTable, list[str]]:
    """Load the rates table and check its assessment year against ``config.toml``."""
    path = resolve_rates_path(
        explicit=explicit, config=config, books_dir=books_dir, data_dir=data_dir
    )
    rates = tb.RatesTable.from_toml_path(path)
    warnings: list[str] = []

    config_year = config.assessment_year if config is not None else None
    if rates.assessment_year is None:
        warnings.append(
            f"NO ASSESSMENT YEAR: {path.name} does not declare an assessment year "
            "(expected [meta] assessment_year, or a rates-AY<year>.toml filename). "
            "Confirm which করবর্ষ / assessment year its figures belong to."
        )
    elif config_year and rates.assessment_year != config_year:
        message = (
            f"Assessment year mismatch: config.toml says {config_year}, but "
            f"{path.name} carries {rates.assessment_year}."
        )
        if not allow_ay_mismatch:
            raise tb.RatesError(
                message,
                hint="Point --rates at the file for this করবর্ষ / assessment year, fix "
                "books.assessment_year in config.toml, or pass --allow-ay-mismatch if "
                "you really mean to read another year's figures.",
            )
        warnings.append(
            "ASSESSMENT YEAR MISMATCH (allowed by --allow-ay-mismatch): "
            + message
            + " Every reference figure below is from the wrong year unless you verified "
            "otherwise."
        )
    return rates, warnings


def _require_chart(ledger: tb.Ledger) -> tb.ChartOfAccounts:
    if ledger.chart is None:
        raise tb.LedgerError(
            "vat.py needs the chart of accounts to tell a VAT control account from a "
            "taxable-value account.",
            hint="Load the books with Ledger.load(<books dir>) so accounts.toml is read.",
        )
    return ledger.chart


def _role_account(chart: tb.ChartOfAccounts, kind: str, *, required: bool) -> tb.Account | None:
    role = KIND_ROLE[kind]
    try:
        return chart.account_for_role(role)
    except tb.UnknownAccountError:
        if not required:
            return None
        bn, en = KIND_LABELS[kind]
        raise tb.AccountError(
            f"Postings carry a {bn} / {en} tax_tag, but no account in "
            f"{chart.source_path or tb.ACCOUNTS_FILENAME} declares role = {role!r}. "
            "TakaBooks will not guess which account holds the VAT.",
            hint=f'Add role = "{role}" to the [[account]] table for that control account '
            "(spec §4.4 lists the Bangladesh-specific accounts that must exist).",
        ) from None


def _natural(posting: tb.Posting, chart: tb.ChartOfAccounts) -> tb.Money:
    """The posting's amount in its account's normal direction (spec §4.4)."""
    account = chart.get(posting.account)
    if account.is_credit_normal:
        return posting.credit - posting.debit
    return posting.debit - posting.credit


def _movements(
    postings: Sequence[tb.Posting], chart: tb.ChartOfAccounts
) -> tuple[AccountMovement, ...]:
    grouped: dict[str, list[tb.Posting]] = {}
    for posting in postings:
        grouped.setdefault(posting.account, []).append(posting)
    movements: list[AccountMovement] = []
    for code in sorted(grouped):
        rows = grouped[code]
        account = chart.get(code)
        debit = tb.Money.sum(row.debit for row in rows)
        credit = tb.Money.sum(row.credit for row in rows)
        natural = (credit - debit) if account.is_credit_normal else (debit - credit)
        movements.append(
            AccountMovement(
                code=code,
                name=account.name,
                name_bn=account.name_bn,
                debit=debit,
                credit=credit,
                natural=natural,
            )
        )
    return tuple(movements)


# ======================================================================================
# The computation
# ======================================================================================


def _buckets_for_kind(
    postings: Sequence[tb.Posting],
    chart: tb.ChartOfAccounts,
    kind: str,
    tax_code: str | None,
) -> tuple[RateBucket, ...]:
    by_rate: dict[Decimal, dict[str, Any]] = {}
    for posting in postings:
        if posting.tax_tag.kind != kind:
            continue
        rate = posting.tax_tag.rate if posting.tax_tag.rate is not None else Decimal(0)
        slot = by_rate.setdefault(rate, {"value": [], "tax": [], "entries": []})
        if tax_code is not None and posting.account == tax_code:
            slot["tax"].append(posting)
        else:
            slot["value"].append(posting)
        if posting.entry_id not in slot["entries"]:
            slot["entries"].append(posting.entry_id)

    buckets: list[RateBucket] = []
    for rate in sorted(by_rate):
        slot = by_rate[rate]
        value_lines: list[tb.Posting] = slot["value"]
        tax_lines: list[tb.Posting] = slot["tax"]
        taxable_value = tb.Money.sum(_natural(p, chart) for p in value_lines)
        posted_tax = tb.Money.sum(_natural(p, chart) for p in tax_lines)
        expected_tax = taxable_value.percent(rate)
        buckets.append(
            RateBucket(
                kind=kind,
                rate=rate,
                taxable_value=taxable_value,
                posted_tax=posted_tax,
                expected_tax=expected_tax,
                tax_source="posted" if tax_lines else "derived",
                entry_ids=tuple(slot["entries"]),
                value_accounts=_movements(value_lines, chart),
                tax_accounts=_movements(tax_lines, chart),
            )
        )
    return tuple(buckets)


def _issues_for_kind(
    postings: Sequence[tb.Posting],
    chart: tb.ChartOfAccounts,
    kind: str,
    tax_code: str | None,
    posted_rates: set[Decimal],
) -> list[ReconciliationIssue]:
    """Per-entry cross-check of value × rate against the VAT actually posted.

    Only rates whose bucket has at least one tax-account line are checked: where a book
    never posts the tax line at all, the tax is derived from the tag rate instead and
    flagging every entry would be noise, not information.
    """
    grouped: dict[tuple[str, Decimal], dict[str, Any]] = {}
    for posting in postings:
        if posting.tax_tag.kind != kind:
            continue
        rate = posting.tax_tag.rate if posting.tax_tag.rate is not None else Decimal(0)
        if rate not in posted_rates:
            continue
        slot = grouped.setdefault(
            (posting.entry_id, rate), {"value": [], "tax": [], "locations": []}
        )
        if tax_code is not None and posting.account == tax_code:
            slot["tax"].append(posting)
        else:
            slot["value"].append(posting)
        if posting.location and posting.location not in slot["locations"]:
            slot["locations"].append(posting.location)

    issues: list[ReconciliationIssue] = []
    for (entry_id, rate) in sorted(grouped, key=lambda key: (key[0], key[1])):
        slot = grouped[(entry_id, rate)]
        taxable_value = tb.Money.sum(_natural(p, chart) for p in slot["value"])
        posted_tax = tb.Money.sum(_natural(p, chart) for p in slot["tax"])
        expected_tax = taxable_value.percent(rate)
        if posted_tax == expected_tax:
            continue
        issues.append(
            ReconciliationIssue(
                entry_id=entry_id,
                kind=kind,
                rate=rate,
                taxable_value=taxable_value,
                expected_tax=expected_tax,
                posted_tax=posted_tax,
                location="; ".join(slot["locations"]),
            )
        )
    return issues


def _control_account(
    full: tb.Ledger,
    account: tb.Account,
    role: str,
    since: datetime.date | None,
    until: datetime.date | None,
    tagged: tb.Money,
) -> ControlAccount:
    if since is not None:
        before = full.filter(until=since - datetime.timedelta(days=1))
        opening = before.natural_balance(account.code)
    else:
        opening = tb.Money.zero()
    closing = (
        full.filter(until=until).natural_balance(account.code)
        if until is not None
        else full.natural_balance(account.code)
    )
    return ControlAccount(
        role=role,
        code=account.code,
        name=account.name,
        name_bn=account.name_bn,
        opening=opening,
        movement=closing - opening,
        closing=closing,
        tagged=tagged,
    )


def _rates_file_name(rates: tb.RatesTable) -> str:
    return rates.source_path.name if rates.source_path else "the rates file"


def _node_table(rates: tb.RatesTable, key: str) -> Mapping[str, Any] | None:
    """The raw TOML table at ``key`` (so ``placeholder`` and labels can be read), or None
    when the key is absent or is a bare scalar."""
    try:
        return rates.section(key)
    except tb.RatesError:
        return None


def _is_placeholder(table: Mapping[str, Any] | None) -> bool:
    """``placeholder = true`` on a node: schema awaiting research, not a figure."""
    return table is not None and table.get("placeholder") is True


def rates_file_is_placeholder(rates: tb.RatesTable) -> bool:
    """True when ``[meta]`` declares the whole file to be unlanded schema."""
    meta = rates.raw.get("meta")
    if not isinstance(meta, Mapping):
        return False
    if meta.get("placeholder") is True:
        return True
    return str(meta.get("status", "")).strip().lower() == "placeholder"


def _read_value(
    rate: tb.Rate, kind: str, file_name: str, *, placeholder: bool
) -> tuple[str, tb.Money | None, Decimal | None, str, str]:
    """Render one :class:`takabooks.Rate` as ``(display, money, decimal, problem, warning)``.

    ``kind`` is ``"percent"``, ``"money"`` or ``"text"``.  A TOML float is refused
    outright (spec §4.2); a percentage outside 0–100 is a fraction/percent mix-up.
    """
    if isinstance(rate.value, float):
        problem = (
            "written as a TOML float, which cannot hold an exact decimal; "
            "write it as a quoted string or an integer"
        )
        warning = (
            f"UNUSABLE RATE: {rate.key} in {file_name} is a TOML float ({rate.value!r}). "
            'TakaBooks refuses float money and rates — rewrite it as a string (value = "15") '
            "or an integer."
        )
        return repr(rate.value), None, None, problem, warning
    if isinstance(rate.value, bool):
        problem = "a boolean is not a figure"
        return repr(rate.value), None, None, problem, f"UNREADABLE: {rate.key} in {file_name}: {problem}."
    if kind == "percent":
        try:
            dec = rate.as_decimal()
        except tb.TakaBooksError as exc:
            return (
                str(rate.value),
                None,
                None,
                exc.message,
                f"UNREADABLE RATE: {rate.key} in {file_name}: {exc.message}",
            )
        if dec < 0 or dec > 100:
            problem = f"{rate_text(dec)} is not a percentage between 0 and 100"
            return (
                rate_text(dec),
                None,
                None,
                problem,
                f"UNUSABLE RATE: {rate.key} in {file_name}: {problem} (write 15 for 15%, "
                "never 0.15).",
            )
        return rate_text(dec) + "%", None, dec, "", ""
    if kind == "money":
        try:
            money = rate.as_money()
        except tb.TakaBooksError as exc:
            return (
                str(rate.value),
                None,
                None,
                exc.message,
                f"UNREADABLE AMOUNT: {rate.key} in {file_name}: {exc.message}",
            )
        return tb.format_bdt(money, symbol=True), money, None, "", ""
    text = str(rate.value).strip()
    if not text:
        if placeholder:
            return "(blank placeholder)", None, None, "", ""
        problem = "blank"
        return (
            "(blank)",
            None,
            None,
            problem,
            f"BLANK: {rate.key} in {file_name} carries an empty value. State it as prose "
            "with its source URL, or mark the node placeholder = true.",
        )
    return text, None, None, "", ""


def reference_figures(
    rates: tb.RatesTable, *, vds_present: bool = False
) -> tuple[tuple[ReferenceFigure, ...], list[str]]:
    """Read every :data:`REFERENCE_SPECS` figure from the rates file.

    Returns the figures and the warnings they raise.  A **required** figure that is absent
    raises :class:`takabooks.RatesError` naming every missing key — after the whole file
    has been read, so one run reports everything that is wrong with it.
    """
    figures: list[ReferenceFigure] = []
    warnings: list[str] = []
    missing_required: list[ReferenceSpec] = []
    file_name = _rates_file_name(rates)

    for spec in REFERENCE_SPECS:
        needed = spec.required == REQUIRED_ALWAYS or (
            spec.required == REQUIRED_WITH_VDS and vds_present
        )
        if not rates.has(spec.rates_key):
            figures.append(
                ReferenceFigure(
                    key=spec.key,
                    label_bn=spec.label_bn,
                    label_en=spec.label_en,
                    kind=spec.kind,
                    available=False,
                    rates_key=spec.rates_key,
                    required=spec.required,
                    display="not in rates file",
                )
            )
            if needed:
                missing_required.append(spec)
            else:
                warnings.append(
                    f"NOT IN RATES FILE: {spec.label} is absent from {file_name} "
                    f"(key {spec.rates_key}). TakaBooks will not supply a figure — obtain "
                    "it from the National Board of Revenue (NBR) before filing."
                )
            continue

        table = _node_table(rates, spec.rates_key)
        try:
            rate = rates.rate(spec.rates_key)
        except tb.RatesError as exc:
            figures.append(
                ReferenceFigure(
                    key=spec.key,
                    label_bn=spec.label_bn,
                    label_en=spec.label_en,
                    kind=spec.kind,
                    available=True,
                    rates_key=spec.rates_key,
                    required=spec.required,
                    display="unreadable",
                    problem=exc.message,
                )
            )
            warnings.append(f"UNREADABLE: {spec.rates_key} in {file_name}: {exc.message}")
            continue

        placeholder = _is_placeholder(table)
        display, money, _dec, problem, warning = _read_value(
            rate, spec.kind, file_name, placeholder=placeholder
        )
        if warning:
            warnings.append(warning)
        figures.append(
            ReferenceFigure(
                key=spec.key,
                label_bn=spec.label_bn,
                label_en=spec.label_en,
                kind=spec.kind,
                available=True,
                rates_key=spec.rates_key,
                required=spec.required,
                raw_value=rate.value,
                display=display,
                verified=rate.is_verified,
                placeholder=placeholder,
                source=rate.source,
                as_of=rate.as_of,
                note=rate.note,
                money=money,
                problem=problem,
            )
        )
        if placeholder:
            warnings.append(
                f"PLACEHOLDER: {spec.rates_key} ({spec.label}) in {file_name} is schema "
                "awaiting research (placeholder = true), not a figure. Nothing may be filed "
                "on it — obtain the real figure from the National Board of Revenue (NBR)."
            )
        elif not rate.is_verified:
            warnings.append(
                f"UNVERIFIED: {spec.rates_key} ({spec.label}) in {file_name} is not marked "
                "verified = true. It is unconfirmed against a primary NBR source and must be "
                "checked with the National Board of Revenue (NBR) before you file."
            )

    if missing_required:
        count = len(missing_required)
        listing = "; ".join(
            f"{spec.rates_key} ({spec.label}) — {spec.why}" for spec in missing_required
        )
        raise tb.RatesError(
            f"{file_name} is missing {'a figure' if count == 1 else f'{count} figures'} that "
            f"a {tb.term('vat')} return needs: {listing}. TakaBooks will not assume a value.",
            hint="Add each key to the rates TOML as a table with value, source, as_of and "
            "verified (= false with a note if unconfirmed), or pass --rates <path> to a "
            "file that carries it.",
        )
    return tuple(figures), warnings


def declared_rates(rates: tb.RatesTable) -> tuple[tuple[DeclaredRate, ...], list[str]]:
    """Every VAT and VDS rate the rates file declares for its assessment year.

    Single nodes come from :data:`VAT_RATE_NODES`; one rate per child table under each of
    :data:`VAT_RATE_SECTIONS` and :data:`VDS_RATE_SECTIONS`.  Warnings are raised only for
    keys :func:`reference_figures` does not already report, so nothing is said twice.
    """
    file_name = _rates_file_name(rates)
    already_reported = {spec.rates_key for spec in REFERENCE_SPECS}
    declared: list[DeclaredRate] = []
    warnings: list[str] = []

    def add(scope: str, key: str) -> None:
        table = _node_table(rates, key)
        if table is None or "value" not in table:
            return
        rate = rates.rate(key)
        placeholder = _is_placeholder(table)
        _display, _money, dec, problem, warning = _read_value(
            rate, "percent", file_name, placeholder=placeholder
        )
        label_bn = str(table.get("label_bn", "")).strip()
        label_en = str(table.get("label_en", "")).strip()
        declared.append(
            DeclaredRate(
                scope=scope,
                rates_key=key,
                label_bn=label_bn,
                label_en=label_en,
                rate=dec,
                verified=rate.is_verified,
                placeholder=placeholder,
                problem=problem,
            )
        )
        if key in already_reported:
            return
        label = f"{label_bn} / {label_en}".strip(" /") or key
        if warning:
            warnings.append(warning)
        if placeholder:
            warnings.append(
                f"PLACEHOLDER: {key} ({label}) in {file_name} is schema awaiting research "
                "(placeholder = true), not a declared rate."
            )
        elif not rate.is_verified:
            warnings.append(
                f"UNVERIFIED: {key} ({label}) in {file_name} is not marked verified = true "
                "— confirm it with the National Board of Revenue (NBR) before you file."
            )

    for key in VAT_RATE_NODES:
        add("vat", key)
    for scope, sections in (("vat", VAT_RATE_SECTIONS), ("vds", VDS_RATE_SECTIONS)):
        for section_key in sections:
            table = _node_table(rates, section_key)
            if table is None:
                continue
            for child, node in table.items():
                if isinstance(node, Mapping) and "value" in node:
                    add(scope, f"{section_key}.{child}")
    return tuple(declared), warnings


def _tag_rate_warnings(
    buckets: Mapping[str, tuple[RateBucket, ...]],
    declared: Sequence[DeclaredRate],
    file_name: str,
) -> list[str]:
    """Check every rate written in a tax_tag against the rates the file declares.

    TakaBooks asserts no rate of its own: a tagged rate is fine when the file declares it,
    a warning when the file declares something else, and *uncheckable* — said out loud —
    when the file declares nothing usable (every node a placeholder).
    """
    warnings: list[str] = []
    vat_usable = {d.rate for d in declared if d.scope == "vat" and d.usable}
    vds_usable = {d.rate for d in declared if d.scope == "vds" and d.usable} | vat_usable
    checks = (
        ("VAT", (tb.TAG_VAT_OUT, tb.TAG_VAT_IN), vat_usable, "vat.rates"),
        ("VDS", (tb.TAG_VDS,), vds_usable, "vds.services or vat.rates"),
    )
    for name, kinds, usable, where in checks:
        tagged = sorted({bucket.rate for kind in kinds for bucket in buckets.get(kind, ())})
        if not tagged:
            continue
        tagged_text = ", ".join(f"{rate_text(rate)}%" for rate in tagged)
        if not usable:
            warnings.append(
                f"RATE CHECK SKIPPED: {file_name} declares no usable {name} rate under "
                f"{where} (every node is a placeholder or unreadable), so the {name} rates "
                f"tagged in the journal ({tagged_text}) could not be checked against the "
                "statutory table. Confirm each with the National Board of Revenue (NBR)."
            )
            continue
        undeclared = [rate for rate in tagged if rate not in usable]
        if undeclared:
            declared_text = ", ".join(f"{rate_text(rate)}%" for rate in sorted(usable))
            warnings.append(
                f"RATE NOT DECLARED: postings are tagged at {name} "
                + ", ".join(f"{rate_text(rate)}%" for rate in undeclared)
                + f", but {file_name} declares only {declared_text} under {where}. Confirm "
                "the reduced, truncated or special rate applies before filing."
            )
    return warnings


def _return_form(rates: tb.RatesTable, figures: Mapping[str, ReturnFigure]) -> tuple[
    tuple[ReturnFormLine, ...], list[str]
]:
    """Read an optional NBR form line map from the rates file.

    TakaBooks asserts no form line number of its own; if the rates file carries none,
    this returns nothing and the caller says so.
    """
    notes: list[str] = []
    section = _node_table(rates, RETURN_FORM_KEY)
    if section is None or not isinstance(section.get("line"), list):
        return (), notes

    lines: list[ReturnFormLine] = []
    for raw in section["line"]:
        if not isinstance(raw, Mapping):
            continue
        line_no = str(raw.get("line", raw.get("code", ""))).strip()
        figure_key = str(raw.get("figure", "")).strip()
        figure = figures.get(figure_key)
        lines.append(
            ReturnFormLine(
                line=line_no,
                label_bn=str(raw.get("label_bn", "")).strip(),
                label_en=str(raw.get("label_en", "")).strip(),
                figure_key=figure_key,
                amount=figure.amount if figure is not None else None,
                problem=""
                if figure is not None
                else f"no TakaBooks figure named {figure_key!r}",
            )
        )
    return tuple(lines), notes


def compute_vat_position(
    ledger: tb.Ledger,
    *,
    rates: tb.RatesTable,
    since: datetime.date | None = None,
    until: datetime.date | None = None,
    period_label: str = "",
    extra_warnings: Sequence[str] = (),
) -> VatPosition:
    """Compute the whole VAT position for a period from a loaded, balanced ledger."""
    chart = _require_chart(ledger)
    config = ledger.config
    if config is None:
        raise tb.ConfigError(
            "vat.py needs books/config.toml — every tax output must state the "
            f"{tb.term('assessment_year')} it used (spec §6.3)."
        )
    assessment_year = config.require_assessment_year()

    period = ledger.filter(since=since, until=until)
    kinds_present = {posting.tax_tag.kind for posting in period}

    warnings: list[str] = list(extra_warnings)
    notes: list[str] = []

    tax_accounts: dict[str, tb.Account | None] = {}
    for kind in _KIND_ORDER:
        tax_accounts[kind] = _role_account(chart, kind, required=kind in kinds_present)

    buckets: dict[str, tuple[RateBucket, ...]] = {}
    issues: list[ReconciliationIssue] = []
    for kind in _KIND_ORDER:
        account = tax_accounts[kind]
        code = account.code if account is not None else None
        kind_buckets = _buckets_for_kind(tuple(period), chart, kind, code)
        buckets[kind] = kind_buckets
        posted_rates = {b.rate for b in kind_buckets if b.tax_source == "posted"}
        issues.extend(_issues_for_kind(tuple(period), chart, kind, code, posted_rates))
        for bucket in kind_buckets:
            if bucket.tax_source != "derived":
                continue
            bn, en = KIND_LABELS[kind]
            control = account.code if account is not None else f'role "{KIND_ROLE[kind]}"'
            notes.append(
                f"DERIVED: no posting in this period touches {control} with a "
                f"{bucket.tag_text} tag, so the {bn} / {en} at {bucket.rate_text}% shown "
                f"({tb.format_bdt(bucket.vat_amount, symbol=True)}) is computed from the "
                "rate written on the tagged value lines, not read from the control "
                "account."
            )

    controls: list[ControlAccount] = []
    for kind in _KIND_ORDER:
        account = tax_accounts[kind]
        if account is None:
            continue
        tagged = tb.Money.sum(bucket.posted_tax for bucket in buckets[kind])
        controls.append(
            _control_account(ledger, account, KIND_ROLE[kind], since, until, tagged)
        )

    # -- the rates file: every statutory figure, none of it asserted here -------------
    file_name = _rates_file_name(rates)
    rate_caveats: list[str] = []
    file_placeholder = rates_file_is_placeholder(rates)
    if file_placeholder:
        rate_caveats.append(
            f"PLACEHOLDER RATES FILE: {file_name} declares itself a schema awaiting "
            "verified data ([meta] placeholder = true). Every figure quoted from it is "
            "unlanded, and nothing computed with it may be filed with the NBR."
        )
    references, reference_warnings = reference_figures(
        rates, vds_present=tb.TAG_VDS in kinds_present
    )
    rate_caveats.extend(reference_warnings)
    declared, declared_warnings = declared_rates(rates)
    rate_caveats.extend(declared_warnings)
    rate_caveats.extend(_tag_rate_warnings(buckets, declared, file_name))
    warnings.extend(rate_caveats)

    position = VatPosition(
        config=config,
        books_dir=ledger.books_dir,
        assessment_year=assessment_year,
        period_start=since,
        period_end=until,
        period_label=period_label or "every posting in the books",
        rates_path=rates.source_path,
        rates_assessment_year=rates.assessment_year,
        rates_provenance=rates.provenance(),
        rates_caveats=tuple(rate_caveats),
        rates_file_placeholder=file_placeholder,
        rates_unverified_in_file=len(rates.unverified_keys()),
        buckets=buckets,
        issues=tuple(issues),
        controls=tuple(controls),
        references=references,
        declared=declared,
        return_form=(),
        warnings=(),
        notes=(),
        posting_count=len(period),
        entry_count=len(period.entries),
        tds_posting_count=sum(1 for p in period if p.tax_tag.is_tds),
    )
    return_form, form_notes = _return_form(rates, position.figure_map())
    notes.extend(form_notes)

    if not return_form:
        notes.append(
            "FORM MAP: the rates file carries no NBR return-form line map "
            f"([[{RETURN_FORM_KEY}.line]] tables). TakaBooks does not assert মূসক-৯.১ / "
            "Mushak 9.1 line numbers — map the figures above onto the current NBR form "
            "yourself."
        )

    # Observations that help the preparer, drawn only from the data at hand.
    if position.tds_posting_count:
        notes.append(
            f"OUT OF SCOPE: {position.tds_posting_count} posting(s) in this period "
            f"carry a {tb.term('tds')} tag. Withholding tax is reported by tax.py, not "
            "here."
        )
    if not any(buckets[kind] for kind in _KIND_ORDER):
        notes.append(
            "NO VAT POSTINGS: no posting in this period carries a VAT:OUT, VAT:IN or VDS "
            "tax_tag, so every figure below is ৳0.00. Check the period and the tax_tag "
            "column before filing a nil return."
        )
    if issues:
        warnings.append(
            f"RECONCILIATION: {len(issues)} entr{'y' if len(issues) == 1 else 'ies'} do "
            "not tie: the VAT posted differs from the taxable value times the rate on the "
            "entry's own tax_tag. See the reconciliation section."
        )
    unexplained = [c for c in controls if not c.untagged.is_zero()]
    if unexplained:
        notes.append(
            "CONTROL MOVEMENT: "
            + "; ".join(
                f"{c.code} {c.name} moved {tb.format_bdt(c.untagged, symbol=True)} on "
                "postings that carry no VAT tax_tag (treasury deposits and adjustments "
                "look like this)"
                for c in unexplained
            )
            + "."
        )

    return replace(
        position,
        return_form=return_form,
        warnings=tuple(warnings),
        notes=tuple(notes),
    )


# ======================================================================================
# Rendering — Markdown
# ======================================================================================


def _money(position: VatPosition, amount: tb.Money) -> str:
    if position.config is not None:
        return position.config.format_money(amount, symbol=True)
    return tb.format_bdt(amount, symbol=True)


def _bilingual_disclaimer(position: VatPosition) -> list[str]:
    lines = [tb.DISCLAIMER_EN]
    language = position.config.language if position.config is not None else "en"
    if language in ("bn", "bn-en"):
        lines.append(tb.DISCLAIMER_BN)
    return lines


def _bucket_table(position: VatPosition, kind: str) -> str:
    buckets = position.buckets.get(kind, ())
    headers = [
        "হার / Rate",
        "tax_tag",
        "করযোগ্য মূল্য / Taxable value",
        "মূসক / VAT",
        "Source",
        "Entries",
    ]
    aligns = ["r", "l", "r", "r", "l", "r"]
    if not buckets:
        return tb.markdown_table(headers, [["—", "—", _money(position, tb.Money.zero()),
                                            _money(position, tb.Money.zero()), "—", "0"]],
                                 aligns=aligns)
    rows = [
        [
            f"{bucket.rate_text}%",
            bucket.tag_text,
            _money(position, bucket.taxable_value),
            _money(position, bucket.vat_amount),
            "posted" if bucket.tax_source == "posted" else "derived from tag rate",
            str(len(bucket.entry_ids)),
        ]
        for bucket in buckets
    ]
    total_value = tb.Money.sum(bucket.taxable_value for bucket in buckets)
    total_tax = tb.Money.sum(bucket.vat_amount for bucket in buckets)
    rows.append(
        [
            "**Total**",
            "",
            f"**{_money(position, total_value)}**",
            f"**{_money(position, total_tax)}**",
            "",
            str(len({eid for bucket in buckets for eid in bucket.entry_ids})),
        ]
    )
    return tb.markdown_table(headers, rows, aligns=aligns)


def _accounts_table(position: VatPosition, kind: str) -> str:
    buckets = position.buckets.get(kind, ())
    rows: list[list[str]] = []
    for bucket in buckets:
        for movement in bucket.value_accounts:
            rows.append(
                [
                    "value",
                    f"{bucket.rate_text}%",
                    movement.code,
                    movement.label.split(" ", 1)[1] if " " in movement.label else movement.name,
                    _money(position, movement.debit),
                    _money(position, movement.credit),
                    _money(position, movement.natural),
                ]
            )
        for movement in bucket.tax_accounts:
            rows.append(
                [
                    "tax",
                    f"{bucket.rate_text}%",
                    movement.code,
                    movement.label.split(" ", 1)[1] if " " in movement.label else movement.name,
                    _money(position, movement.debit),
                    _money(position, movement.credit),
                    _money(position, movement.natural),
                ]
            )
    if not rows:
        rows = [["—", "—", "—", "—", "", "", ""]]
    return tb.markdown_table(
        ["Line", "Rate", "Code", "হিসাব / Account", "ডেবিট / Debit", "ক্রেডিট / Credit", "Natural"],
        rows,
        aligns=["l", "r", "l", "l", "r", "r", "r"],
    )


def render_markdown(position: VatPosition) -> str:
    """The human-readable report (spec §4.6: Markdown and CSV from one computation)."""
    config = position.config
    out: list[str] = []
    add = out.append

    business = config.display_name if config is not None else "(unnamed business)"
    add(f"# {tb.term('vat')} position — {business}")
    add("")
    add(f"- **Period:** {position.period_label}")
    if position.period_start or position.period_end:
        start = position.period_start.isoformat() if position.period_start else "start of books"
        end = position.period_end.isoformat() if position.period_end else "end of books"
        add(f"- **Dates covered:** {start} → {end} (inclusive)")
    add(f"- **{tb.term('assessment_year')}:** {position.assessment_year}")
    if config is not None:
        if config.bin:
            add(f"- **BIN (মূসক নিবন্ধন নম্বর):** {config.bin}")
        if config.tin:
            add(f"- **TIN (কর শনাক্তকরণ নম্বর):** {config.tin}")
    if position.books_dir is not None:
        add(f"- **Books:** `{position.books_dir}`")
    add(f"- **{position.rates_provenance}**")
    add(f"- **Postings read:** {position.posting_count} in {position.entry_count} entries")
    add(f"- **Filing status:** {position.filing_status}")
    add("")
    add(f"_{tb.ATTRIBUTION}_")
    add("")

    if position.provisional:
        if position.rates_file_placeholder:
            reason = (
                "The rates file is a placeholder schema awaiting verified data, so every "
                "statutory figure quoted below is unlanded."
            )
        elif position.issues:
            reason = (
                "At least one entry does not reconcile, or a figure read from the rates "
                "file is unverified or missing — see the warnings."
            )
        else:
            reason = (
                "A figure read from the rates file is unverified, a placeholder, or "
                "missing — see the warnings."
            )
        add(
            f"> **PROVISIONAL / অস্থায়ী — NOT FOR FILING.** {reason} Confirm every flagged "
            "item with the National Board of Revenue (NBR) before this figure set is used."
        )
        add("")

    if position.warnings:
        add("## সতর্কতা / Warnings")
        add("")
        add(
            "> Every line below is unconfirmed or does not tie. Resolve each one, or "
            "confirm it with the National Board of Revenue (NBR), before this figure set "
            "is used to file."
        )
        add("")
        for warning in position.warnings:
            add(f"- **{warning}**")
        add("")

    add("## 1. দাখিলপত্রের অঙ্ক / Return figures")
    add("")
    add(
        "The figure set a VAT-registered business needs to complete its monthly return. "
        "The `Ref` column is a TakaBooks reference, **not** an NBR form line number."
    )
    add("")
    rows = []
    for index, figure in enumerate(position.return_figures(), start=1):
        rows.append(
            [
                str(index),
                figure.label,
                f"`{figure.key}`",
                _money(position, figure.amount),
                figure.note,
            ]
        )
    add(
        tb.markdown_table(
            ["Ref", "অঙ্ক / Figure", "Key", "পরিমাণ / Amount", "Note"],
            rows,
            aligns=["r", "l", "l", "r", "l"],
        )
    )
    add("")

    if position.return_form:
        add("### NBR form line map (from the rates file)")
        add("")
        form_rows = [
            [
                line.line,
                f"{line.label_bn} / {line.label_en}".strip(" /"),
                f"`{line.figure_key}`",
                _money(position, line.amount) if line.amount is not None else "—",
                line.problem,
            ]
            for line in position.return_form
        ]
        add(
            tb.markdown_table(
                ["Line", "Label", "Figure", "পরিমাণ / Amount", "Problem"],
                form_rows,
                aligns=["l", "l", "l", "r", "l"],
            )
        )
        add("")

    section_number = 2
    for kind in _KIND_ORDER:
        bn, en = KIND_LABELS[kind]
        add(f"## {section_number}. {bn} / {en}")
        add("")
        add(_bucket_table(position, kind))
        add("")
        add("<details><summary>Accounts touched</summary>")
        add("")
        add(_accounts_table(position, kind))
        add("")
        add("</details>")
        add("")
        section_number += 1

    add(f"## {section_number}. নিট অবস্থান / Net position")
    add("")
    net_rows = [
        ["উৎপাদ কর / Output VAT", _money(position, position.output_tax)],
        [
            "বাদ: রেয়াতযোগ্য উপকরণ কর / Less: rebateable input VAT",
            _money(position, position.input_tax),
        ],
        [
            "= উৎপাদ কর বাদ উপকরণ কর / = Output less input",
            _money(position, position.net),
        ],
        ["নিট প্রদেয় মূসক / Net VAT payable", _money(position, position.net_payable)],
        [
            "জের টানা উদ্বৃত্ত উপকরণ কর / Excess input VAT carried forward",
            _money(position, position.carry_forward),
        ],
        [
            "উৎসে কর্তিত মূসক / VDS withheld (separate deposit)",
            _money(position, position.vds_withheld),
        ],
    ]
    add(tb.markdown_table(["অঙ্ক / Figure", "পরিমাণ / Amount"], net_rows, aligns=["l", "r"]))
    add("")
    if position.net.is_positive():
        add(
            f"**{_money(position, position.net_payable)} is payable** for this period "
            "before any adjustment, decreasing adjustment or opening balance the return "
            "itself provides for."
        )
    elif position.net.is_negative():
        add(
            f"**{_money(position, position.carry_forward)} of input VAT exceeds output "
            "VAT** for this period. Whether that excess is carried forward or refunded is "
            "a statutory question — TakaBooks does not decide it; confirm the treatment "
            "with the NBR."
        )
    else:
        add("**Output VAT and rebateable input VAT are equal for this period.**")
    add("")
    add(
        "VDS withheld from suppliers is shown separately and is **not** netted against "
        "the VAT payable above; it is money withheld on a supplier's behalf. Confirm how "
        "the current NBR return treats it."
    )
    add("")
    section_number += 1

    add(f"## {section_number}. খতিয়ান মিলকরণ / Control account reconciliation")
    add("")
    if position.controls:
        add(
            "Balances are shown in each account's natural direction. **Tagged** is the "
            "movement explained by VAT tax_tags; **other** is everything else that moved "
            "the account — treasury deposits, adjustments, or mistakes."
        )
        add("")
        control_rows = [
            [
                control.role,
                control.code,
                control.name + (f" ({control.name_bn})" if control.name_bn else ""),
                _money(position, control.opening),
                _money(position, control.tagged),
                _money(position, control.untagged),
                _money(position, control.closing),
            ]
            for control in position.controls
        ]
        add(
            tb.markdown_table(
                [
                    "Role",
                    "Code",
                    "হিসাব / Account",
                    "প্রারম্ভিক / Opening",
                    "Tagged",
                    "Other",
                    "সমাপনী / Closing",
                ],
                control_rows,
                aligns=["l", "l", "l", "r", "r", "r", "r"],
            )
        )
    else:
        add(
            "_No VAT control account is declared in the chart of accounts, and no posting "
            "in this period carries a VAT tax_tag._"
        )
    add("")
    section_number += 1

    add(f"## {section_number}. উপকরণ-উৎপাদ মিলকরণ / Input-output reconciliation")
    add("")
    if position.issues:
        add(
            f"**{len(position.issues)} entr{'y' if len(position.issues) == 1 else 'ies'} "
            "do not tie.** For each, the VAT posted to the control account differs from "
            "the taxable value multiplied by the rate on the entry's own `tax_tag`."
        )
        add("")
        issue_rows = [
            [
                issue.entry_id,
                f"{issue.rate_text}%",
                _money(position, issue.taxable_value),
                _money(position, issue.expected_tax),
                _money(position, issue.posted_tax),
                _money(position, issue.difference),
                issue.location,
            ]
            for issue in position.issues
        ]
        add(
            tb.markdown_table(
                [
                    "entry_id",
                    "Rate",
                    "করযোগ্য মূল্য / Taxable value",
                    "Expected VAT",
                    "Posted VAT",
                    "Difference",
                    "Where",
                ],
                issue_rows,
                aligns=["l", "r", "r", "r", "r", "r", "l"],
            )
        )
    else:
        add("Every tagged entry ties: posted VAT equals taxable value times its tag rate.")
    add("")
    section_number += 1

    add(f"## {section_number}. রেফারেন্স অঙ্ক / Reference figures from the rates file")
    add("")
    add(f"Source: `{position.rates_path}`" if position.rates_path else "Source: rates file")
    add("")
    ref_rows = [
        [
            f"{figure.label_bn} / {figure.label_en}",
            figure.display,
            figure.status,
            f"`{figure.rates_key}`" if figure.rates_key else "—",
            figure.source or "—",
            figure.as_of or "—",
        ]
        for figure in position.references
    ]
    add(
        tb.markdown_table(
            ["অঙ্ক / Figure", "মান / Value", "Status", "Key", "Source", "As of"],
            ref_rows,
            aligns=["l", "r", "l", "l", "l", "l"],
        )
    )
    add("")
    add(
        "TakaBooks hardcodes no Bangladeshi rate, threshold or deadline. Anything marked "
        "`PLACEHOLDER`, `UNVERIFIED` or `not in rates file` must be confirmed with the NBR "
        "before you rely on it."
    )
    add("")
    add("### হার তালিকা / Rates declared in the rates file")
    add("")
    if position.declared:
        add(
            "Every rate written in a `tax_tag` is checked against this set. A tagged rate "
            "the file does not declare is flagged under warnings."
        )
        add("")
        declared_rows = [
            [
                declared.scope.upper(),
                declared.rate_text,
                declared.label or "—",
                declared.status,
                f"`{declared.rates_key}`",
            ]
            for declared in position.declared
        ]
        add(
            tb.markdown_table(
                ["Scope", "হার / Rate", "Label", "Status", "Key"],
                declared_rows,
                aligns=["l", "r", "l", "l", "l"],
            )
        )
    else:
        add(
            "_The rates file declares no VAT or VDS rate "
            f"({', '.join(VAT_RATE_NODES + VAT_RATE_SECTIONS + VDS_RATE_SECTIONS)}), so "
            "tagged rates could not be checked._"
        )
    add("")
    section_number += 1

    if position.notes:
        add(f"## {section_number}. নোট / Notes")
        add("")
        for note in position.notes:
            add(f"- {note}")
        add("")
        section_number += 1

    add("---")
    add("")
    for line in _bilingual_disclaimer(position):
        add(f"> {line}")
        add(">")
    if out[-1] == ">":
        out.pop()
    add("")
    add(f"_{tb.ATTRIBUTION}_")
    add("")
    return "\n".join(out)


# ======================================================================================
# Rendering — CSV
# ======================================================================================

CSV_COLUMNS: tuple[str, ...] = (
    "section",
    "key",
    "label_bn",
    "label_en",
    "rate_percent",
    "amount",
    "detail",
)


def render_csv(position: VatPosition) -> str:
    """A tidy long-format CSV: one amount per row, always ungrouped (spec §4.2)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)

    def row(
        section: str,
        key: str,
        label_bn: str = "",
        label_en: str = "",
        rate: str = "",
        amount: tb.Money | None = None,
        detail: str = "",
    ) -> None:
        writer.writerow(
            [
                section,
                key,
                label_bn,
                label_en,
                rate,
                tb.format_amount_for_csv(amount) if amount is not None else "",
                detail,
            ]
        )

    config = position.config
    row("meta", "tool", "", "TakaBooks vat.py", detail=tb.__version__)
    row("meta", "attribution", detail=tb.ATTRIBUTION)
    if config is not None:
        row("meta", "business_name", detail=config.business_name)
        row("meta", "business_name_bn", detail=config.business_name_bn)
        row("meta", "bin", "মূসক নিবন্ধন নম্বর", "BIN", detail=config.bin)
        row("meta", "tin", "কর শনাক্তকরণ নম্বর", "TIN", detail=config.tin)
    row("meta", "assessment_year", "করবর্ষ", "assessment year", detail=position.assessment_year)
    row("meta", "period_label", detail=position.period_label)
    row(
        "meta",
        "period_start",
        detail=position.period_start.isoformat() if position.period_start else "",
    )
    row(
        "meta",
        "period_end",
        detail=position.period_end.isoformat() if position.period_end else "",
    )
    row("meta", "books_dir", detail=str(position.books_dir) if position.books_dir else "")
    row("meta", "rates_file", detail=str(position.rates_path) if position.rates_path else "")
    row("meta", "rates_assessment_year", detail=position.rates_assessment_year or "")
    row("meta", "rates_provenance", detail=position.rates_provenance)
    row("meta", "postings", detail=str(position.posting_count))
    row("meta", "entries", detail=str(position.entry_count))
    row("meta", "filing_status", detail=position.filing_status)
    row("meta", "provisional", detail="true" if position.provisional else "false")
    row(
        "meta",
        "rates_file_placeholder",
        detail="true" if position.rates_file_placeholder else "false",
    )
    row("meta", "rates_unverified_keys_in_file", detail=str(position.rates_unverified_in_file))

    for figure in position.return_figures():
        row("figure", figure.key, figure.label_bn, figure.label_en,
            amount=figure.amount, detail=figure.note)

    for kind in _KIND_ORDER:
        bn, en = KIND_LABELS[kind]
        prefix = {
            tb.TAG_VAT_OUT: "output",
            tb.TAG_VAT_IN: "input",
            tb.TAG_VDS: "vds",
        }[kind]
        for bucket in position.buckets.get(kind, ()):
            rate = bucket.rate_text
            row(f"{prefix}_by_rate", f"{prefix}.taxable_value@{rate}", bn, en, rate,
                bucket.taxable_value, bucket.tag_text)
            row(f"{prefix}_by_rate", f"{prefix}.vat_amount@{rate}", bn, en, rate,
                bucket.vat_amount, f"source={bucket.tax_source}")
            row(f"{prefix}_by_rate", f"{prefix}.posted_tax@{rate}", bn, en, rate,
                bucket.posted_tax, "posted to the control account")
            row(f"{prefix}_by_rate", f"{prefix}.expected_tax@{rate}", bn, en, rate,
                bucket.expected_tax, "taxable value x tag rate")
            row(f"{prefix}_by_rate", f"{prefix}.variance@{rate}", bn, en, rate,
                bucket.variance, "posted minus expected")
            for movement in bucket.value_accounts:
                row(f"{prefix}_accounts", f"{prefix}.value.{movement.code}@{rate}",
                    movement.name_bn, movement.name, rate, movement.natural,
                    "value line")
            for movement in bucket.tax_accounts:
                row(f"{prefix}_accounts", f"{prefix}.tax.{movement.code}@{rate}",
                    movement.name_bn, movement.name, rate, movement.natural,
                    "tax line")

    for control in position.controls:
        row("control", f"opening.{control.code}", control.name_bn, control.name,
            amount=control.opening, detail=control.role)
        row("control", f"tagged.{control.code}", control.name_bn, control.name,
            amount=control.tagged, detail=control.role)
        row("control", f"other.{control.code}", control.name_bn, control.name,
            amount=control.untagged, detail=control.role)
        row("control", f"closing.{control.code}", control.name_bn, control.name,
            amount=control.closing, detail=control.role)

    for issue in position.issues:
        row("reconciliation", issue.entry_id, *KIND_LABELS[issue.kind],
            issue.rate_text, issue.difference, issue.message())

    for figure in position.references:
        row("reference", figure.key, figure.label_bn, figure.label_en,
            amount=figure.money,
            detail=f"{figure.display} | status={figure.status} | required={figure.required} | "
            f"key={figure.rates_key} | source={figure.source} | as_of={figure.as_of}")

    for declared in position.declared:
        row("declared_rate", declared.rates_key, declared.label_bn, declared.label_en,
            rate_text(declared.rate) if declared.rate is not None else "",
            detail=f"scope={declared.scope} | status={declared.status}")

    for line in position.return_form:
        row("return_form", line.line or line.figure_key, line.label_bn, line.label_en,
            amount=line.amount, detail=line.problem or line.figure_key)

    for index, warning in enumerate(position.warnings, start=1):
        row("warning", str(index), detail=warning)
    for index, note in enumerate(position.notes, start=1):
        row("note", str(index), detail=note)

    for line in _bilingual_disclaimer(position):
        row("disclaimer", "disclaimer", detail=line)

    return buffer.getvalue()


# ======================================================================================
# Rendering — JSON
# ======================================================================================


def _bucket_payload(bucket: RateBucket) -> dict[str, Any]:
    return {
        "rate_percent": bucket.rate_text,
        "tax_tag": bucket.tag_text,
        "taxable_value": bucket.taxable_value,
        "vat_amount": bucket.vat_amount,
        "posted_tax": bucket.posted_tax,
        "expected_tax": bucket.expected_tax,
        "variance": bucket.variance,
        "tax_source": bucket.tax_source,
        "entry_ids": list(bucket.entry_ids),
        "value_accounts": [
            {
                "code": m.code,
                "name": m.name,
                "name_bn": m.name_bn,
                "debit": m.debit,
                "credit": m.credit,
                "natural": m.natural,
            }
            for m in bucket.value_accounts
        ],
        "tax_accounts": [
            {
                "code": m.code,
                "name": m.name,
                "name_bn": m.name_bn,
                "debit": m.debit,
                "credit": m.credit,
                "natural": m.natural,
            }
            for m in bucket.tax_accounts
        ],
    }


def position_payload(position: VatPosition) -> dict[str, Any]:
    """The ``--json`` document, built explicitly so computed properties are included."""
    config = position.config
    return {
        "ok": True,
        "tool": TOOL_NAME,
        "project": tb.PROJECT_NAME,
        "version": tb.__version__,
        "attribution": tb.ATTRIBUTION,
        "business": {
            "name": config.business_name if config else "",
            "name_bn": config.business_name_bn if config else "",
            "bin": config.bin if config else "",
            "tin": config.tin if config else "",
        },
        "books_dir": str(position.books_dir) if position.books_dir else None,
        "assessment_year": position.assessment_year,
        "period": {
            "label": position.period_label,
            "start": position.period_start,
            "end": position.period_end,
        },
        "filing_status": position.filing_status,
        "provisional": position.provisional,
        "rates": {
            "path": str(position.rates_path) if position.rates_path else None,
            "file": position.rates_path.name if position.rates_path else None,
            "assessment_year": position.rates_assessment_year,
            "provenance": position.rates_provenance,
            "file_placeholder": position.rates_file_placeholder,
            "unverified_keys_in_file": position.rates_unverified_in_file,
            "caveats": list(position.rates_caveats),
        },
        "counts": {
            "postings": position.posting_count,
            "entries": position.entry_count,
            "tds_postings_out_of_scope": position.tds_posting_count,
        },
        "figures": [
            {
                "key": figure.key,
                "label_bn": figure.label_bn,
                "label_en": figure.label_en,
                "amount": figure.amount,
                "note": figure.note,
            }
            for figure in position.return_figures()
        ],
        "output": {
            "taxable_value": position.output_taxable_value,
            "tax": position.output_tax,
            "by_rate": [_bucket_payload(b) for b in position.buckets.get(tb.TAG_VAT_OUT, ())],
        },
        "input": {
            "taxable_value": position.input_taxable_value,
            "tax": position.input_tax,
            "by_rate": [_bucket_payload(b) for b in position.buckets.get(tb.TAG_VAT_IN, ())],
        },
        "vds": {
            "supply_value": position.vds_supply_value,
            "withheld": position.vds_withheld,
            "by_rate": [_bucket_payload(b) for b in position.buckets.get(tb.TAG_VDS, ())],
            "note": "VDS withheld is a separate deposit obligation and is not netted "
            "against the VAT payable.",
        },
        "net": {
            "output_less_input": position.net,
            "payable": position.net_payable,
            "carry_forward": position.carry_forward,
        },
        "control_accounts": [
            {
                "role": c.role,
                "code": c.code,
                "name": c.name,
                "name_bn": c.name_bn,
                "opening": c.opening,
                "tagged": c.tagged,
                "other": c.untagged,
                "movement": c.movement,
                "closing": c.closing,
            }
            for c in position.controls
        ],
        "reconciliation": [
            {
                "entry_id": i.entry_id,
                "kind": i.kind,
                "rate_percent": i.rate_text,
                "taxable_value": i.taxable_value,
                "expected_tax": i.expected_tax,
                "posted_tax": i.posted_tax,
                "difference": i.difference,
                "location": i.location,
                "message": i.message(),
            }
            for i in position.issues
        ],
        "reference_figures": [
            {
                "key": f.key,
                "label_bn": f.label_bn,
                "label_en": f.label_en,
                "kind": f.kind,
                "available": f.available,
                "required": f.required,
                "rates_key": f.rates_key,
                "value": f.raw_value if not isinstance(f.raw_value, float) else str(f.raw_value),
                "display": f.display,
                "verified": f.verified,
                "placeholder": f.placeholder,
                "usable": f.usable,
                "status": f.status,
                "source": f.source,
                "as_of": f.as_of,
                "note": f.note,
                "problem": f.problem,
            }
            for f in position.references
        ],
        "declared_rates": [
            {
                "scope": d.scope,
                "rates_key": d.rates_key,
                "label_bn": d.label_bn,
                "label_en": d.label_en,
                "rate_percent": rate_text(d.rate) if d.rate is not None else None,
                "verified": d.verified,
                "placeholder": d.placeholder,
                "usable": d.usable,
                "status": d.status,
                "problem": d.problem,
            }
            for d in position.declared
        ],
        "return_form": [
            {
                "line": line.line,
                "label_bn": line.label_bn,
                "label_en": line.label_en,
                "figure": line.figure_key,
                "amount": line.amount,
                "problem": line.problem,
            }
            for line in position.return_form
        ],
        "warnings": list(position.warnings),
        "notes": list(position.notes),
        "disclaimer_en": tb.DISCLAIMER_EN,
        "disclaimer_bn": tb.DISCLAIMER_BN,
    }


def render_json(position: VatPosition) -> str:
    return tb.json_dumps(position_payload(position)) + "\n"


# ======================================================================================
# CLI
# ======================================================================================

_EPILOG = f"""\
tax_tag convention
  A line hitting the account whose accounts.toml role is "vat_output", "vat_input" or
  "vds_payable" is the tax line (its amount IS the VAT). Any other line carrying the
  same tag is the taxable-value line. Both sides are cross-checked per entry.

rates
  Every statutory figure is read from the rates TOML for the assessment year; none is
  hardcoded here. Keys read: vat.rates.standard and deadlines.vat_return_monthly
  (required), vds.deposit.deadline (required when VDS postings exist),
  vat.rates.zero_rated, vat.rates.reduced.<key>, vds.services.<key>,
  vat.thresholds.registration, vat.thresholds.turnover_tax_enlistment and
  vat.turnover_tax.rate (optional), and an optional [[vat.return_form.line]] map.
  A missing required key exits 8. Optional keys that are missing are reported as
  "not in rates file"; figures not verified = true are reported as UNVERIFIED, and
  placeholder = true nodes as PLACEHOLDER. Any of those stamps the output PROVISIONAL;
  --strict makes them fatal (exit 7).

{tb.ATTRIBUTION}
"""


def build_parser() -> argparse.ArgumentParser:
    parser = tb.common_parser(
        TOOL_NAME,
        f"{tb.term('vat')} position for a period: output tax, rebateable input tax, "
        f"net payable or carry-forward, and {tb.term('vds')} withheld.",
        epilog=_EPILOG,
    )
    parser.add_argument(
        "--period",
        metavar="YYYY-MM",
        help="one calendar month, e.g. 2026-07 (a monthly return period)",
    )
    parser.add_argument("--since", metavar="YYYY-MM-DD", help="inclusive start of the period")
    parser.add_argument("--until", metavar="YYYY-MM-DD", help="inclusive end of the period")
    parser.add_argument(
        "--rates",
        metavar="PATH",
        help="rates TOML to read (default: books.rates_file, else "
        f"src/{DATA_DIRNAME}/{RATES_GLOB})",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "csv", "json"),
        default=None,
        help="stdout format (default: markdown)",
    )
    parser.add_argument("--out", metavar="PATH", help="write the chosen format to a file")
    parser.add_argument(
        "--csv-out", metavar="PATH", help="also write the CSV to a file, whatever --format says"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero if any figure is unverified, missing, or does not reconcile",
    )
    parser.add_argument(
        "--allow-ay-mismatch",
        action="store_true",
        help="permit a rates file whose assessment year differs from config.toml",
    )
    parser.add_argument(
        "--all-caveats",
        action="store_true",
        help="list every unverified figure in the rates file, not only the ones read here",
    )
    return parser


def run(args: argparse.Namespace, *, stdout: Any = None) -> VatPosition:
    """Do the work.  Raises :class:`takabooks.TakaBooksError` on any integrity failure."""
    out = stdout if stdout is not None else sys.stdout
    fmt = "json" if getattr(args, "json", False) else (args.format or "markdown")

    ledger = tb.Ledger.load(args.books)  # require_balanced=True — never report broken books
    since, until, label = resolve_period(
        period=args.period, since=args.since, until=args.until
    )
    rates, rate_warnings = load_rates(
        explicit=args.rates,
        config=ledger.config,
        books_dir=ledger.books_dir,
        allow_ay_mismatch=args.allow_ay_mismatch,
    )
    extra = list(rate_warnings)
    if args.all_caveats:
        extra.extend(rates.caveats())

    position = compute_vat_position(
        ledger, rates=rates, since=since, until=until, period_label=label, extra_warnings=extra
    )

    text = {
        "markdown": render_markdown,
        "csv": render_csv,
        "json": render_json,
    }[fmt](position)

    if args.out:
        tb.write_text_atomic(args.out, text)
    else:
        out.write(text)
    if args.csv_out:
        tb.write_text_atomic(args.csv_out, render_csv(position))

    if args.strict:
        problems = position.blocking_problems()
        if problems:
            raise tb.ValidationError(
                f"--strict: this {tb.term('vat')} figure set is not ready to file — "
                f"{len(problems)} problem(s) must be resolved first:\n  - "
                + "\n  - ".join(problems),
                problems=problems,
                hint="Confirm each unverified figure with the NBR, add the missing ones "
                "to the rates TOML with a source URL, and correct any entry that does "
                "not reconcile.",
            )
    return position


def main(argv: Sequence[str] | None = None) -> int:
    tb.check_python_or_exit()
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "json", False) and args.format not in (None, "json"):
        parser.error("--json cannot be combined with --format " + str(args.format))
    json_output = bool(getattr(args, "json", False)) or args.format == "json"
    with tb.cli_guard(json_output=json_output):
        run(args)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
