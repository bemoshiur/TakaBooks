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
3. **The rates TOML** (``src/data/rates-AY<year>.toml``) for every *statutory* figure —
   the standard rate, thresholds and deadlines quoted for reference.

**This module hardcodes no Bangladeshi rate, threshold or deadline** (spec §4.5, §6.2).
If a reference figure is absent from the rates file, the report says so instead of
supplying one; if it is present but ``verified = false``, the report carries a visible
UNVERIFIED warning on every output format.  ``--strict`` turns any such warning, and any
reconciliation difference, into a non-zero exit so that an unconfirmed figure set can
never be mistaken for a filing-ready one.

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
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
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
    "REFERENCE_SPECS",
    "RETURN_FORM_KEYS",
    "AccountMovement",
    "RateBucket",
    "ReconciliationIssue",
    "ControlAccount",
    "ReferenceFigure",
    "ReturnFigure",
    "ReturnFormLine",
    "VatPosition",
    "rate_text",
    "resolve_period",
    "resolve_rates_path",
    "load_rates",
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


@dataclass(frozen=True)
class _RefSpec:
    """A statutory figure quoted for reference, and where to look for it.

    ``candidates`` is searched in order, so a rates file may organise its keys either
    flat (``vat.standard_rate``) or nested (``vat.rates.standard``) without this module
    caring.  Nothing here asserts a value — only where a value would live.
    """

    key: str
    label_bn: str
    label_en: str
    candidates: tuple[str, ...]
    kind: str  # "percent" | "money" | "text"


#: Reference figures a VAT return preparer asks for.  Every one is optional: if the
#: rates file does not carry it, the report says so.  TakaBooks never fills one in.
REFERENCE_SPECS: tuple[_RefSpec, ...] = (
    _RefSpec(
        "standard_rate",
        "মূসক-এর আদর্শ হার",
        "Standard VAT rate",
        (
            "vat.standard_rate",
            "vat.rate.standard",
            "vat.rates.standard",
            "vat.standard.rate",
        ),
        "percent",
    ),
    _RefSpec(
        "registration_threshold",
        "মূসক নিবন্ধনের সীমা",
        "VAT registration threshold (annual turnover)",
        (
            "vat.registration_threshold",
            "vat.thresholds.registration",
            "vat.threshold.registration",
            "vat.registration.threshold",
        ),
        "money",
    ),
    _RefSpec(
        "turnover_tax_threshold",
        "টার্নওভার করের সীমা",
        "Turnover tax threshold",
        (
            "vat.turnover_tax_threshold",
            "vat.thresholds.turnover_tax",
            "vat.turnover_tax.threshold",
        ),
        "money",
    ),
    _RefSpec(
        "turnover_tax_rate",
        "টার্নওভার করের হার",
        "Turnover tax rate",
        (
            "vat.turnover_tax_rate",
            "vat.rates.turnover_tax",
            "vat.turnover_tax.rate",
        ),
        "percent",
    ),
    _RefSpec(
        "return_deadline",
        "দাখিলপত্র জমার সময়সীমা",
        "Monthly VAT return filing deadline",
        (
            "vat.return_deadline",
            "vat.return.deadline",
            "vat.return.due_day",
            "vat.return_due_day",
            "vat.deadlines.return",
            "calendar.vat_return",
        ),
        "text",
    ),
    _RefSpec(
        "input_rebate_time_limit",
        "উপকরণ কর রেয়াতের সময়সীমা",
        "Time limit to claim an input tax rebate",
        (
            "vat.input_rebate_time_limit",
            "vat.rebate.time_limit",
            "vat.input_tax.time_limit",
            "vat.input_rebate.time_limit",
        ),
        "text",
    ),
    _RefSpec(
        "vds_deposit_deadline",
        "উৎসে কর্তিত মূসক জমার সময়সীমা",
        "Deadline to deposit VDS withheld from suppliers",
        (
            "vds.deposit_deadline",
            "vat.vds.deposit_deadline",
            "vat.vds_deposit_deadline",
            "vds.deadline",
            "vat.deadlines.vds_deposit",
        ),
        "text",
    ),
)

#: Sections a rates file may use to carry an NBR return-form line map.  TakaBooks does
#: not assert any form line number of its own (content rule §6.2).
RETURN_FORM_KEYS: tuple[str, ...] = (
    "vat.return_form",
    "vat.mushak_9_1",
    "vat.mushak.9_1",
    "vat.return",
)


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
    raw_value: Any = None
    display: str = ""
    verified: bool = False
    source: str = ""
    as_of: str = ""
    note: str = ""
    money: tb.Money | None = None
    problem: str = ""

    @property
    def label(self) -> str:
        return f"{self.label_bn} / {self.label_en}"

    @property
    def status(self) -> str:
        if not self.available:
            return "not in rates file"
        return "verified" if self.verified else "UNVERIFIED"


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
    buckets: Mapping[str, tuple[RateBucket, ...]]
    issues: tuple[ReconciliationIssue, ...]
    controls: tuple[ControlAccount, ...]
    references: tuple[ReferenceFigure, ...]
    return_form: tuple[ReturnFormLine, ...]
    warnings: tuple[str, ...]
    notes: tuple[str, ...]
    posting_count: int
    entry_count: int
    tds_posting_count: int

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


def _split_lines(
    postings: Iterable[tb.Posting], kind: str, tax_code: str | None
) -> tuple[list[tb.Posting], list[tb.Posting]]:
    """Split same-kind postings into (value lines, tax lines) by the control account."""
    value_lines: list[tb.Posting] = []
    tax_lines: list[tb.Posting] = []
    for posting in postings:
        if posting.tax_tag.kind != kind:
            continue
        if tax_code is not None and posting.account == tax_code:
            tax_lines.append(posting)
        else:
            value_lines.append(posting)
    return value_lines, tax_lines


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


def _reference_figures(rates: tb.RatesTable) -> tuple[tuple[ReferenceFigure, ...], list[str]]:
    figures: list[ReferenceFigure] = []
    warnings: list[str] = []
    file_name = rates.source_path.name if rates.source_path else "the rates file"

    for spec in REFERENCE_SPECS:
        found_key = next((key for key in spec.candidates if rates.has(key)), "")
        if not found_key:
            figures.append(
                ReferenceFigure(
                    key=spec.key,
                    label_bn=spec.label_bn,
                    label_en=spec.label_en,
                    kind=spec.kind,
                    available=False,
                    display="not in rates file",
                )
            )
            warnings.append(
                f"NOT IN RATES FILE: {spec.label_bn} / {spec.label_en} is absent from "
                f"{file_name} (looked for {', '.join(spec.candidates)}). TakaBooks will "
                "not supply a figure — obtain it from the National Board of Revenue (NBR) "
                "before filing."
            )
            continue

        rate = rates.rate(found_key)
        display = ""
        money: tb.Money | None = None
        problem = ""
        if isinstance(rate.value, float):
            problem = (
                "written as a TOML float, which cannot hold an exact decimal; "
                "write it as a quoted string or an integer"
            )
            display = repr(rate.value)
            warnings.append(
                f"UNUSABLE RATE: {found_key} in {file_name} is a TOML float "
                f"({rate.value!r}). TakaBooks refuses float money and rates — rewrite it "
                'as a string (value = "15") or an integer.'
            )
        elif spec.kind == "percent":
            try:
                display = rate_text(rate.as_decimal()) + "%"
            except tb.TakaBooksError as exc:
                problem = exc.message
                display = str(rate.value)
                warnings.append(f"UNREADABLE RATE: {found_key} in {file_name}: {exc.message}")
        elif spec.kind == "money":
            try:
                money = rate.as_money()
                display = tb.format_bdt(money, symbol=True)
            except tb.TakaBooksError as exc:
                problem = exc.message
                display = str(rate.value)
                warnings.append(f"UNREADABLE AMOUNT: {found_key} in {file_name}: {exc.message}")
        else:
            display = str(rate.value)

        figures.append(
            ReferenceFigure(
                key=spec.key,
                label_bn=spec.label_bn,
                label_en=spec.label_en,
                kind=spec.kind,
                available=True,
                rates_key=found_key,
                raw_value=rate.value,
                display=display,
                verified=rate.is_verified,
                source=rate.source,
                as_of=rate.as_of,
                note=rate.note,
                money=money,
                problem=problem,
            )
        )
        if not rate.is_verified:
            warnings.append(
                f"UNVERIFIED: {found_key} ({spec.label_bn} / {spec.label_en}) in "
                f"{file_name} is not marked verified = true. It is unconfirmed against a "
                "primary NBR source and must be checked with the National Board of "
                "Revenue (NBR) before you file."
            )
    return tuple(figures), warnings


def _return_form(rates: tb.RatesTable, figures: Mapping[str, ReturnFigure]) -> tuple[
    tuple[ReturnFormLine, ...], list[str]
]:
    """Read an optional NBR form line map from the rates file.

    TakaBooks asserts no form line number of its own; if the rates file carries none,
    this returns nothing and the caller says so.
    """
    notes: list[str] = []
    section: Mapping[str, Any] | None = None
    for key in RETURN_FORM_KEYS:
        try:
            candidate = rates.section(key)
        except tb.RatesError:
            continue
        if isinstance(candidate.get("line"), list):
            section = candidate
            break
    if section is None:
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

    references, reference_warnings = _reference_figures(rates)
    warnings.extend(reference_warnings)

    position_stub = VatPosition(
        config=config,
        books_dir=ledger.books_dir,
        assessment_year=assessment_year,
        period_start=since,
        period_end=until,
        period_label=period_label or "every posting in the books",
        rates_path=rates.source_path,
        rates_assessment_year=rates.assessment_year,
        rates_provenance=rates.provenance(),
        rates_caveats=tuple(rates.caveats()),
        buckets=buckets,
        issues=tuple(issues),
        controls=tuple(controls),
        references=references,
        return_form=(),
        warnings=(),
        notes=(),
        posting_count=len(period),
        entry_count=len(period.entries),
        tds_posting_count=sum(1 for p in period if p.tax_tag.is_tds),
    )
    return_form, form_notes = _return_form(rates, position_stub.figure_map())
    notes.extend(form_notes)

    if not return_form:
        notes.append(
            "FORM MAP: the rates file carries no NBR return-form line map (looked for "
            f"{', '.join(RETURN_FORM_KEYS)}). TakaBooks does not assert Mushak form line "
            "numbers — map the figures below onto the current NBR form yourself."
        )

    # Observations that help the preparer, drawn only from the data at hand.
    standard = next(
        (
            figure
            for figure in references
            if figure.key == "standard_rate" and figure.available and not figure.problem
        ),
        None,
    )
    if standard is not None:
        try:
            standard_rate = tb.RatesTable(
                {"v": {"value": standard.raw_value}}
            ).rate("v").as_decimal()
        except tb.TakaBooksError:
            standard_rate = None
        if standard_rate is not None:
            odd = sorted(
                {
                    bucket.rate
                    for kind in (tb.TAG_VAT_OUT, tb.TAG_VAT_IN)
                    for bucket in buckets[kind]
                    if bucket.rate != standard_rate
                }
            )
            if odd:
                notes.append(
                    "NON-STANDARD RATE: postings are tagged at "
                    + ", ".join(f"{rate_text(rate)}%" for rate in odd)
                    + f", which differs from the standard rate {standard.display} in "
                    f"{rates.source_path.name if rates.source_path else 'the rates file'}. "
                    "Confirm the reduced, truncated or special rate applies."
                )

    if position_stub.tds_posting_count:
        notes.append(
            f"OUT OF SCOPE: {position_stub.tds_posting_count} posting(s) in this period "
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

    return VatPosition(
        config=config,
        books_dir=ledger.books_dir,
        assessment_year=assessment_year,
        period_start=since,
        period_end=until,
        period_label=period_label or "every posting in the books",
        rates_path=rates.source_path,
        rates_assessment_year=rates.assessment_year,
        rates_provenance=rates.provenance(),
        rates_caveats=tuple(rates.caveats()),
        buckets=buckets,
        issues=tuple(issues),
        controls=tuple(controls),
        references=references,
        return_form=return_form,
        warnings=tuple(warnings),
        notes=tuple(notes),
        posting_count=len(period),
        entry_count=len(period.entries),
        tds_posting_count=position_stub.tds_posting_count,
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
    add("")
    add(f"_{tb.ATTRIBUTION}_")
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
        "`UNVERIFIED` or `not in rates file` must be confirmed with the NBR before you "
        "rely on it."
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
            detail=f"{figure.display} | status={figure.status} | key={figure.rates_key} | "
            f"source={figure.source} | as_of={figure.as_of}")

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
        "rates": {
            "path": str(position.rates_path) if position.rates_path else None,
            "file": position.rates_path.name if position.rates_path else None,
            "assessment_year": position.rates_assessment_year,
            "provenance": position.rates_provenance,
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
                "rates_key": f.rates_key,
                "value": f.raw_value if not isinstance(f.raw_value, float) else str(f.raw_value),
                "display": f.display,
                "verified": f.verified,
                "status": f.status,
                "source": f.source,
                "as_of": f.as_of,
                "note": f.note,
                "problem": f.problem,
            }
            for f in position.references
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
  hardcoded here. Missing figures are reported as missing; figures that are not
  verified = true are reported as UNVERIFIED. --strict makes either fatal.

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
