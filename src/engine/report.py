#!/usr/bin/env python3
"""TakaBooks ``report.py`` — আর্থিক বিবরণী / financial statements from the journal.

Three statements, **one computation, two renderings**:

* রেওয়ামিল / trial balance — proves ``debits == credits`` and says so in words.
* লাভ-ক্ষতি হিসাব / profit and loss — for the reporting period.
* স্থিতিপত্র / balance sheet — proves ``Assets == Liabilities + Equity``.

Every figure printed as Markdown and every figure written to CSV comes from the same
``StatementRow`` list, so the two renderings *cannot* disagree: the Markdown renderer adds
heading rows and bold, and nothing else.

Period semantics (stated on every report so nobody has to guess):

* ``--from`` / ``--to`` (or ``--period``) define the **reporting period**.
* The **profit and loss account covers that period**.
* The **trial balance and balance sheet are stated “as at” the period end**, cumulative
  from the start of the books — that is what an “as at” statement means.
* The equity section therefore carries the accumulated result in two lines:
  retained earnings brought forward (everything before ``--from``) **plus the profit for
  the period, which is literally the P&L bottom line object**.  Together they reconcile
  the balance sheet exactly.

Integrity, per spec §2 — a report that does not reconcile is never printed:

* trial balance out of balance          -> :class:`takabooks.BalanceError`  (exit 5)
* Assets != Liabilities + Equity        -> :class:`takabooks.ValidationError` (exit 7)
* a P&L section partition that loses an account, or an accumulated result that does not
  match the ledger, fails the same way.

This module defines **no Bangladeshi tax rate, threshold, deadline or statute number**.
It only adds up what the journal already says.

TakaBooks — Moshiur Rahman (@bemoshiur) · TICON SYSTEM LTD — https://ticonsys.com
"""

from __future__ import annotations

import csv
import datetime
import io
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

ENGINE_DIR = Path(__file__).resolve().parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import takabooks as tb  # noqa: E402

__all__ = [
    "REPORTS_DIRNAME",
    "PL_SECTIONS",
    "SectionSpec",
    "ReportLine",
    "Section",
    "StatementRow",
    "Check",
    "TrialBalance",
    "ProfitAndLoss",
    "BalanceSheet",
    "FinancialStatements",
    "resolve_period",
    "build_statements",
    "trial_balance_rows",
    "profit_and_loss_rows",
    "balance_sheet_rows",
    "render_markdown",
    "build_payload",
    "write_csv_reports",
    "report_filenames",
    "build_parser",
    "run",
    "main",
]

#: Reports are written into ``<books>/reports/`` unless ``--reports-dir`` says otherwise.
REPORTS_DIRNAME = "reports"

#: Row kinds.  Only ``heading`` rows are Markdown-only; every number-bearing row goes to
#: both renderings, which is what makes them impossible to disagree.
KIND_HEADING = "heading"
KIND_LINE = "line"
KIND_SUBTOTAL = "subtotal"
KIND_TOTAL = "total"


# ======================================================================================
# Statement shapes
# ======================================================================================


@dataclass(frozen=True)
class SectionSpec:
    """How one profit-and-loss section is recognised in the chart of accounts."""

    key: str
    label_en: str
    label_bn: str
    account_type: str
    blocks: tuple[str, ...]

    @property
    def label(self) -> str:
        return f"{self.label_bn} / {self.label_en}"


#: Profit and loss sections, keyed off the account *type* first and the spec §4.4 code
#: block second.  An income/expense account whose code does not follow the conventional
#: block wording still lands in a section (see :func:`_pl_section_key`), so no account can
#: silently fall out of the statement.
PL_SECTIONS: tuple[SectionSpec, ...] = (
    SectionSpec("revenue", "Revenue", "আয়", "income", ("4",)),
    SectionSpec("cost_of_sales", "Cost of Goods Sold", "বিক্রিত পণ্যের ব্যয়", "expense", ("5",)),
    SectionSpec("operating_expenses", "Operating Expenses", "পরিচালন ব্যয়", "expense", ("6",)),
    SectionSpec("other_income", "Other Income", "অন্যান্য আয়", "income", ("7",)),
    SectionSpec("other_expenses", "Other Expenses", "অন্যান্য ব্যয়", "expense", ("8", "9")),
)

_PL_SECTION_BY_KEY: dict[str, SectionSpec] = {spec.key: spec for spec in PL_SECTIONS}

#: Balance sheet sections, in presentation order.
BS_SECTIONS: tuple[tuple[str, str, str], ...] = (
    ("asset", "Assets", "সম্পদ"),
    ("liability", "Liabilities", "দায়"),
    ("equity", "Equity", "মূলধন"),
)


@dataclass(frozen=True)
class ReportLine:
    """One account on one statement."""

    code: str
    name: str
    name_bn: str
    account_type: str
    debit: tb.Money
    credit: tb.Money
    amount: tb.Money  # natural direction: positive in the account's normal balance

    @property
    def label(self) -> str:
        return f"{self.name} ({self.name_bn})" if self.name_bn else self.name


@dataclass(frozen=True)
class Section:
    """A named group of :class:`ReportLine` plus its total."""

    key: str
    label_en: str
    label_bn: str
    lines: tuple[ReportLine, ...]
    total: tb.Money

    @property
    def label(self) -> str:
        return f"{self.label_bn} / {self.label_en}"

    @property
    def is_empty(self) -> bool:
        return not self.lines


@dataclass(frozen=True)
class StatementRow:
    """One printable row.  Markdown and CSV both render exactly these."""

    section: str
    kind: str
    code: str
    label_en: str
    label_bn: str
    amount: tb.Money | None = None
    debit: tb.Money | None = None
    credit: tb.Money | None = None

    @property
    def label(self) -> str:
        if self.label_bn and self.label_en:
            return f"{self.label_en} ({self.label_bn})"
        return self.label_en or self.label_bn


@dataclass(frozen=True)
class Check:
    """A reconciliation that had to hold before anything was printed.

    The amounts are kept as :class:`takabooks.Money` and formatted only when rendered, so
    the reconciliation lines follow the same digit grouping as the tables they sit under.
    """

    name: str
    ok: bool
    template: str  # str.format template; {0}, {1}, … are the amounts below
    amounts: tuple[tb.Money, ...] = ()

    def describe(self, fmt: Callable[[tb.Money], str] | None = None) -> str:
        formatter = fmt or (lambda amount: tb.format_bdt(amount, symbol=True))
        return self.template.format(*(formatter(amount) for amount in self.amounts))

    @property
    def detail(self) -> str:
        """The sentence with default (লাখ/কোটি) grouping — used in errors and JSON."""
        return self.describe()


@dataclass(frozen=True)
class TrialBalance:
    """রেওয়ামিল / trial balance, stated as at :attr:`as_at`."""

    as_at: datetime.date | None
    lines: tuple[ReportLine, ...]
    total_debit: tb.Money
    total_credit: tb.Money

    @property
    def difference(self) -> tb.Money:
        return self.total_debit - self.total_credit

    @property
    def is_balanced(self) -> bool:
        return self.difference.is_zero()


@dataclass(frozen=True)
class ProfitAndLoss:
    """লাভ-ক্ষতি হিসাব / profit and loss for the reporting period."""

    start: datetime.date | None
    end: datetime.date | None
    sections: tuple[Section, ...]

    def section(self, key: str) -> Section:
        for candidate in self.sections:
            if candidate.key == key:
                return candidate
        raise KeyError(key)

    @property
    def revenue(self) -> tb.Money:
        return self.section("revenue").total

    @property
    def cost_of_sales(self) -> tb.Money:
        return self.section("cost_of_sales").total

    @property
    def gross_profit(self) -> tb.Money:
        return self.revenue - self.cost_of_sales

    @property
    def operating_expenses(self) -> tb.Money:
        return self.section("operating_expenses").total

    @property
    def operating_profit(self) -> tb.Money:
        return self.gross_profit - self.operating_expenses

    @property
    def other_income(self) -> tb.Money:
        return self.section("other_income").total

    @property
    def other_expenses(self) -> tb.Money:
        return self.section("other_expenses").total

    @property
    def net_profit(self) -> tb.Money:
        return self.operating_profit + self.other_income - self.other_expenses

    @property
    def total_income(self) -> tb.Money:
        return self.revenue + self.other_income

    @property
    def total_expenses(self) -> tb.Money:
        return self.cost_of_sales + self.operating_expenses + self.other_expenses


@dataclass(frozen=True)
class BalanceSheet:
    """স্থিতিপত্র / balance sheet, stated as at :attr:`as_at`."""

    as_at: datetime.date | None
    assets: Section
    liabilities: Section
    equity: Section
    opening_result: tb.Money  # accumulated profit earned before the period started
    period_result: tb.Money  # the P&L bottom line for the period, carried in unchanged

    @property
    def accumulated_result(self) -> tb.Money:
        return self.opening_result + self.period_result

    @property
    def total_assets(self) -> tb.Money:
        return self.assets.total

    @property
    def total_liabilities(self) -> tb.Money:
        return self.liabilities.total

    @property
    def total_equity(self) -> tb.Money:
        """Capital accounts plus the accumulated result (books are not closed for us)."""
        return self.equity.total + self.accumulated_result

    @property
    def total_liabilities_and_equity(self) -> tb.Money:
        return self.total_liabilities + self.total_equity

    @property
    def difference(self) -> tb.Money:
        return self.total_assets - self.total_liabilities_and_equity

    @property
    def is_balanced(self) -> bool:
        return self.difference.is_zero()


@dataclass(frozen=True)
class FinancialStatements:
    """Everything one run computed — the single source both renderings read."""

    config: tb.Config | None
    books_dir: Path | None
    period_start: datetime.date | None
    period_end: datetime.date | None
    covers_from: datetime.date | None
    as_at: datetime.date | None
    period_label: str
    trial_balance: TrialBalance
    profit_and_loss: ProfitAndLoss
    balance_sheet: BalanceSheet
    checks: tuple[Check, ...]
    posting_count: int  # postings up to as_at — what the trial balance is built from
    entry_count: int
    period_posting_count: int = 0  # postings inside the reporting period — the P&L's input
    period_entry_count: int = 0

    @property
    def period_text(self) -> str:
        start = self.covers_from.isoformat() if self.covers_from else "the start of the books"
        end = self.as_at.isoformat() if self.as_at else "the end of the books"
        return f"{start} → {end}"

    @property
    def as_at_text(self) -> str:
        return self.as_at.isoformat() if self.as_at else "the end of the books"


# ======================================================================================
# Period resolution — --period YYYY-MM (month) or FY<year> (fiscal year from config)
# ======================================================================================

_MONTH_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
#: ``FY2026``, ``FY2026-27``, ``FY 2026/2027`` — or the bare income-year form ``2026-27``.
#: Without the ``FY`` prefix the second half is mandatory; months (``2026-07``) are matched
#: by :data:`_MONTH_RE` first, so a month can never be read as a fiscal year.
_FY_RE = re.compile(
    r"^(?:FY[ _-]?(\d{4})(?:[-/](\d{2}|\d{4}))?|(\d{4})[-/](\d{2}|\d{4}))$", re.IGNORECASE
)

_PERIOD_FORMS = (
    "a month as YYYY-MM (e.g. 2026-07), or "
    "a fiscal year as FY<year>, FY<year>-<next> or <year>-<next> (e.g. FY2026-27 or "
    "2026-27), which reads books.fiscal_year_start from config.toml"
)


def _month_end(year: int, month: int) -> datetime.date:
    """Last calendar day of a month, computed without any third-party date library."""
    if month == 12:
        return datetime.date(year, 12, 31)
    return datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)


def _parse_cli_date(text: str, *, flag: str) -> datetime.date:
    try:
        return tb.parse_date(text, where=flag, field_name="date")
    except tb.JournalError as exc:
        raise tb.ValidationError(
            f"{flag} {text!r} is not an ISO date.",
            problems=(f"{flag}={text!r}",),
            hint="Write dates as YYYY-MM-DD, e.g. --from 2026-07-01.",
        ) from None


def _fiscal_year_window(
    start_year: int, config: tb.Config | None
) -> tuple[datetime.date, datetime.date, str]:
    """Fiscal year beginning in ``start_year``, using ``books.fiscal_year_start``.

    TakaBooks never assumes a Bangladeshi income year: the month-day comes from the book's
    own ``config.toml`` and :meth:`Config.require_fiscal_year_start` raises if it is absent.
    """
    if config is None:
        raise tb.ConfigError(
            "A fiscal-year period needs books/config.toml (books.fiscal_year_start).",
            hint="Pass --books <dir>, or use --from/--to instead.",
        )
    month_day = config.require_fiscal_year_start()
    month, day = (int(part) for part in month_day.split("-", 1))
    try:
        start = datetime.date(start_year, month, day)
        next_start = datetime.date(start_year + 1, month, day)
    except ValueError as exc:
        raise tb.ConfigError(
            f"books.fiscal_year_start = {month_day!r} does not exist in every year ({exc}).",
            hint="Use a month-day that exists in all years, e.g. 07-01.",
        ) from None
    end = next_start - datetime.timedelta(days=1)
    label = (
        f"FY{start_year}-{(start_year + 1) % 100:02d} "
        f"(fiscal year starting {month_day}): {start.isoformat()} → {end.isoformat()}"
    )
    return start, end, label


def resolve_period(
    *,
    period: str | None = None,
    date_from: str | datetime.date | None = None,
    date_to: str | datetime.date | None = None,
    config: tb.Config | None = None,
) -> tuple[datetime.date | None, datetime.date | None, str]:
    """Turn CLI period flags into ``(start, end, label)``.  Both bounds are inclusive."""
    if period and (date_from or date_to):
        raise tb.ValidationError(
            "--period cannot be combined with --from/--to.",
            problems=("--period", "--from/--to"),
            hint="Pick one: --period 2026-07, or --from 2026-07-01 --to 2026-07-31.",
        )

    if period:
        text = str(period).strip()
        month = _MONTH_RE.match(text)
        if month:
            year, mon = int(month.group(1)), int(month.group(2))
            start = datetime.date(year, mon, 1)
            end = _month_end(year, mon)
            label = f"{text} (month): {start.isoformat()} → {end.isoformat()}"
            return start, end, label

        fiscal = _FY_RE.match(text)
        if fiscal:
            prefixed = fiscal.group(1) is not None
            start_year = int(fiscal.group(1) if prefixed else fiscal.group(3))
            suffix = fiscal.group(2) if prefixed else fiscal.group(4)
            if suffix is not None:
                expected = start_year + 1
                given = int(suffix)
                matches = given == expected if len(suffix) == 4 else given == expected % 100
                if not matches:
                    raise tb.ValidationError(
                        f"--period {text!r}: a fiscal year starting in {start_year} ends in "
                        f"{expected}, so the second half must be "
                        f"{expected} or {expected % 100:02d}.",
                        problems=(f"--period={text!r}",),
                        hint=f"Write it as FY{start_year}-{expected % 100:02d}.",
                    )
            return _fiscal_year_window(start_year, config)

        raise tb.ValidationError(
            f"--period {text!r} is not a period TakaBooks understands.",
            problems=(f"--period={text!r}",),
            hint=f"Use {_PERIOD_FORMS}.",
        )

    start = (
        _parse_cli_date(date_from, flag="--from")
        if isinstance(date_from, str)
        else date_from
    )
    end = _parse_cli_date(date_to, flag="--to") if isinstance(date_to, str) else date_to
    if start is not None and end is not None and start > end:
        raise tb.ValidationError(
            f"--from {start.isoformat()} is after --to {end.isoformat()}.",
            problems=(f"--from={start.isoformat()}", f"--to={end.isoformat()}"),
            hint="The period runs --from (earliest) to --to (latest), both inclusive.",
        )
    if start is None and end is None:
        label = "the whole ledger"
    elif start is None:
        label = f"up to {end.isoformat()}"
    elif end is None:
        label = f"from {start.isoformat()}"
    else:
        label = f"{start.isoformat()} → {end.isoformat()}"
    return start, end, label


# ======================================================================================
# The one computation
# ======================================================================================


def _line_from_total(total: tb.AccountTotal) -> ReportLine:
    account = total.account
    if account is None:
        raise tb.UnknownAccountError(
            f"Account {total.code!r} is used in the journal but is not in the chart of "
            "accounts, so it cannot be placed on a statement.",
            code=total.code,
            hint="Add it to accounts.toml, or fix the journal row.",
        )
    return ReportLine(
        code=total.code,
        name=account.name,
        name_bn=account.name_bn,
        account_type=account.type,
        debit=total.debit,
        credit=total.credit,
        amount=total.natural,
    )


def _pl_section_key(account_type: str, code: str) -> str:
    """Which P&L section an income/expense account belongs to.

    Falls back to revenue / operating expenses for an unconventional code block, so the
    partition is total: no income or expense account can escape the statement.
    """
    block = code[:1] if code else ""
    for spec in PL_SECTIONS:
        if account_type == spec.account_type and block in spec.blocks:
            return spec.key
    return "revenue" if account_type == "income" else "operating_expenses"


def _section(key: str, label_en: str, label_bn: str, lines: Iterable[ReportLine]) -> Section:
    items = tuple(lines)
    return Section(
        key=key,
        label_en=label_en,
        label_bn=label_bn,
        lines=items,
        total=tb.Money.sum(line.amount for line in items),
    )


def _result_of(ledger: tb.Ledger) -> tb.Money:
    """Income less expenses for a ledger slice (natural direction)."""
    return ledger.type_total("income") - ledger.type_total("expense")


def build_statements(
    ledger: tb.Ledger,
    *,
    period_start: datetime.date | None = None,
    period_end: datetime.date | None = None,
    period_label: str = "",
    include_unused: bool = False,
) -> FinancialStatements:
    """Compute all three statements once, reconcile them, and refuse to return if they
    do not tie."""
    if ledger.chart is None:
        raise tb.LedgerError(
            "report.py needs a chart of accounts to classify assets, liabilities, equity, "
            "income and expenses.",
            hint="Load the books with Ledger.load(<books dir>).",
        )

    as_at_ledger = ledger.filter(until=period_end) if period_end is not None else ledger
    period_ledger = (
        as_at_ledger.filter(since=period_start) if period_start is not None else as_at_ledger
    )
    if period_start is not None:
        opening_ledger = ledger.filter(until=period_start - datetime.timedelta(days=1))
    else:
        opening_ledger = tb.Ledger((), chart=ledger.chart, config=ledger.config)

    first_posting, last_posting = ledger.date_range()
    covers_from = period_start if period_start is not None else first_posting
    as_at = period_end if period_end is not None else last_posting

    # -- রেওয়ামিল / trial balance, as at the period end ---------------------------------
    tb_totals = as_at_ledger.account_totals(include_unused=include_unused)
    tb_lines = tuple(_line_from_total(total) for total in tb_totals.values())
    trial = TrialBalance(
        as_at=as_at,
        lines=tb_lines,
        total_debit=tb.Money.sum(line.debit for line in tb_lines),
        total_credit=tb.Money.sum(line.credit for line in tb_lines),
    )

    # -- লাভ-ক্ষতি হিসাব / profit and loss, for the period -------------------------------
    pl_totals = period_ledger.account_totals(include_unused=include_unused)
    buckets: dict[str, list[ReportLine]] = {spec.key: [] for spec in PL_SECTIONS}
    for total in pl_totals.values():
        line = _line_from_total(total)
        if line.account_type not in tb.INCOME_STATEMENT_TYPES:
            continue
        buckets[_pl_section_key(line.account_type, line.code)].append(line)
    profit_and_loss = ProfitAndLoss(
        start=covers_from,
        end=as_at,
        sections=tuple(
            _section(spec.key, spec.label_en, spec.label_bn, buckets[spec.key])
            for spec in PL_SECTIONS
        ),
    )

    # -- স্থিতিপত্র / balance sheet, as at the period end --------------------------------
    bs_buckets: dict[str, list[ReportLine]] = {key: [] for key, _, _ in BS_SECTIONS}
    for line in tb_lines:
        if line.account_type in bs_buckets:
            bs_buckets[line.account_type].append(line)
    sections = {
        key: _section(key, label_en, label_bn, bs_buckets[key])
        for key, label_en, label_bn in BS_SECTIONS
    }
    balance_sheet = BalanceSheet(
        as_at=as_at,
        assets=sections["asset"],
        liabilities=sections["liability"],
        equity=sections["equity"],
        opening_result=_result_of(opening_ledger),
        period_result=profit_and_loss.net_profit,
    )

    checks = _reconcile(trial, profit_and_loss, balance_sheet, as_at_ledger, period_ledger)
    failures = [check for check in checks if not check.ok]
    if failures:
        _raise_for(failures, trial, balance_sheet, period_start, period_end)

    return FinancialStatements(
        config=ledger.config,
        books_dir=ledger.books_dir,
        period_start=period_start,
        period_end=period_end,
        covers_from=covers_from,
        as_at=as_at,
        period_label=period_label or "the whole ledger",
        trial_balance=trial,
        profit_and_loss=profit_and_loss,
        balance_sheet=balance_sheet,
        checks=checks,
        posting_count=len(as_at_ledger),
        entry_count=len(as_at_ledger.entries),
        period_posting_count=len(period_ledger),
        period_entry_count=len(period_ledger.entries),
    )


def _reconcile(
    trial: TrialBalance,
    profit_and_loss: ProfitAndLoss,
    balance_sheet: BalanceSheet,
    as_at_ledger: tb.Ledger,
    period_ledger: tb.Ledger,
) -> tuple[Check, ...]:
    """Every reconciliation that must hold before a figure is allowed out of this module."""
    ledger_result = _result_of(as_at_ledger)
    period_result = _result_of(period_ledger)

    checks = [
        Check(
            name="trial_balance_debits_equal_credits",
            ok=trial.is_balanced,
            template="total debits {0} vs total credits {1} — difference {2}",
            amounts=(trial.total_debit, trial.total_credit, trial.difference),
        ),
        Check(
            name="balance_sheet_assets_equal_liabilities_plus_equity",
            ok=balance_sheet.is_balanced,
            template="assets {0} vs liabilities {1} + equity {2} — difference {3}",
            amounts=(
                balance_sheet.total_assets,
                balance_sheet.total_liabilities,
                balance_sheet.total_equity,
                balance_sheet.difference,
            ),
        ),
        Check(
            name="profit_and_loss_sections_cover_every_income_and_expense_account",
            ok=profit_and_loss.net_profit == period_result,
            template=(
                "net profit from the sections {0} vs income less expenses straight from "
                "the ledger {1}"
            ),
            amounts=(profit_and_loss.net_profit, period_result),
        ),
        Check(
            name="accumulated_result_ties_to_the_ledger",
            ok=balance_sheet.accumulated_result == ledger_result,
            template=(
                "brought forward {0} + period {1} = {2} vs cumulative income less "
                "expenses {3}"
            ),
            amounts=(
                balance_sheet.opening_result,
                balance_sheet.period_result,
                balance_sheet.accumulated_result,
                ledger_result,
            ),
        ),
    ]
    return tuple(checks)


def _raise_for(
    failures: Sequence[Check],
    trial: TrialBalance,
    balance_sheet: BalanceSheet,
    period_start: datetime.date | None,
    period_end: datetime.date | None,
) -> None:
    """Turn a failed reconciliation into the loudest sensible TakaBooks error."""
    names = [check.name for check in failures]
    details = tuple(f"{check.name}: {check.detail}" for check in failures)

    if "trial_balance_debits_equal_credits" in names:
        window = ""
        if period_start is not None or period_end is not None:
            window = (
                " The reporting window may have cut a journal entry in half: an entry_id "
                "whose rows carry different dates can straddle the period boundary. Run "
                "validate.py to find entry_ids that span dates."
            )
        raise tb.BalanceError(
            "রেওয়ামিল / trial balance does not balance: debits "
            f"{tb.format_bdt(trial.total_debit, symbol=True)} vs credits "
            f"{tb.format_bdt(trial.total_credit, symbol=True)} (difference "
            f"{tb.format_bdt(trial.difference, symbol=True)})." + window,
            difference=trial.difference,
            total_debit=trial.total_debit,
            total_credit=trial.total_credit,
            hint="No statement is printed from books that do not tie back to the journal.",
        )

    raise tb.ValidationError(
        "The statements do not reconcile, so nothing was printed: "
        + "; ".join(check.detail for check in failures)
        + ".",
        problems=details,
        hint="Run validate.py on the books; report.py refuses to print a report that does "
        "not tie back to the journal.",
    )


# ======================================================================================
# Rows — the shared spine of both renderings
# ======================================================================================


def trial_balance_rows(trial: TrialBalance) -> list[StatementRow]:
    rows: list[StatementRow] = []
    for line in trial.lines:
        rows.append(
            StatementRow(
                section=line.account_type,
                kind=KIND_LINE,
                code=line.code,
                label_en=line.name,
                label_bn=line.name_bn,
                amount=line.amount,
                debit=line.debit,
                credit=line.credit,
            )
        )
    rows.append(
        StatementRow(
            section="total",
            kind=KIND_TOTAL,
            code="",
            label_en="Total",
            label_bn="সর্বমোট",
            amount=None,
            debit=trial.total_debit,
            credit=trial.total_credit,
        )
    )
    return rows


def _line_rows(section: Section) -> list[StatementRow]:
    return [
        StatementRow(
            section=section.key,
            kind=KIND_LINE,
            code=line.code,
            label_en=line.name,
            label_bn=line.name_bn,
            amount=line.amount,
            debit=line.debit,
            credit=line.credit,
        )
        for line in section.lines
    ]


def _subtotal(section_key: str, label_en: str, label_bn: str, amount: tb.Money) -> StatementRow:
    return StatementRow(
        section=section_key,
        kind=KIND_SUBTOTAL,
        code="",
        label_en=label_en,
        label_bn=label_bn,
        amount=amount,
    )


def _heading(section: Section) -> StatementRow:
    return StatementRow(
        section=section.key,
        kind=KIND_HEADING,
        code="",
        label_en=section.label_en,
        label_bn=section.label_bn,
    )


def profit_and_loss_rows(profit_and_loss: ProfitAndLoss) -> list[StatementRow]:
    """Line, subtotal and total rows for the P&L, in presentation order."""
    rows: list[StatementRow] = []

    def emit(key: str) -> None:
        section = profit_and_loss.section(key)
        if section.is_empty:
            return
        rows.append(_heading(section))
        rows.extend(_line_rows(section))
        rows.append(
            _subtotal(
                section.key,
                f"Total {section.label_en.lower()}",
                f"মোট {section.label_bn}",
                section.total,
            )
        )

    emit("revenue")
    emit("cost_of_sales")
    rows.append(
        _subtotal("gross_profit", "Gross profit", "মোট মুনাফা", profit_and_loss.gross_profit)
    )
    emit("operating_expenses")
    rows.append(
        _subtotal(
            "operating_profit", "Operating profit", "পরিচালন মুনাফা", profit_and_loss.operating_profit
        )
    )
    emit("other_income")
    emit("other_expenses")
    rows.append(
        StatementRow(
            section="net_profit",
            kind=KIND_TOTAL,
            code="",
            label_en="Net profit for the period",
            label_bn="সময়কালের নিট মুনাফা",
            amount=profit_and_loss.net_profit,
        )
    )
    return rows


def balance_sheet_rows(balance_sheet: BalanceSheet) -> list[StatementRow]:
    """Line, subtotal and total rows for the balance sheet, in presentation order."""
    rows: list[StatementRow] = []

    rows.append(_heading(balance_sheet.assets))
    rows.extend(_line_rows(balance_sheet.assets))
    rows.append(
        _subtotal("total_assets", "Total assets", "মোট সম্পদ", balance_sheet.total_assets)
    )

    rows.append(_heading(balance_sheet.liabilities))
    rows.extend(_line_rows(balance_sheet.liabilities))
    rows.append(
        _subtotal(
            "total_liabilities", "Total liabilities", "মোট দায়", balance_sheet.total_liabilities
        )
    )

    rows.append(_heading(balance_sheet.equity))
    rows.extend(_line_rows(balance_sheet.equity))
    rows.append(
        StatementRow(
            section="equity",
            kind=KIND_LINE,
            code="",
            label_en="Retained earnings brought forward",
            label_bn="প্রারম্ভিক সংরক্ষিত মুনাফা",
            amount=balance_sheet.opening_result,
        )
    )
    rows.append(
        StatementRow(
            section="equity",
            kind=KIND_LINE,
            code="",
            label_en="Profit for the period (from the profit and loss account)",
            label_bn="সময়কালের মুনাফা",
            amount=balance_sheet.period_result,
        )
    )
    rows.append(
        _subtotal("total_equity", "Total equity", "মোট মূলধন", balance_sheet.total_equity)
    )
    rows.append(
        StatementRow(
            section="total",
            kind=KIND_TOTAL,
            code="",
            label_en="Total liabilities and equity",
            label_bn="মোট দায় ও মূলধন",
            amount=balance_sheet.total_liabilities_and_equity,
        )
    )
    return rows


# ======================================================================================
# Markdown rendering
# ======================================================================================


def _make_formatter(
    config: tb.Config | None, grouping: str | None = None
) -> Callable[..., str]:
    def fmt(amount: tb.Money, *, symbol: bool = False) -> str:
        kwargs: dict[str, Any] = {"symbol": symbol}
        if grouping:
            kwargs["grouping"] = grouping
        if config is not None:
            return config.format_money(amount, **kwargs)
        return tb.format_bdt(amount, **kwargs)

    return fmt


def _term_heading(key: str) -> str:
    """``"রেওয়ামিল / Trial balance"`` — the library's term pair, English capitalised."""
    bn, en = tb.TERMS[key]
    return f"{bn} / {en[:1].upper()}{en[1:]}"


def _bold(text: str) -> str:
    return f"**{text}**" if text else ""


def _md_cell(fmt: Callable[..., str], amount: tb.Money | None, *, strong: bool) -> str:
    if amount is None:
        return ""
    text = fmt(amount)
    return _bold(text) if strong else text


def _row_label(row: StatementRow) -> str:
    if row.kind == KIND_HEADING:
        return _bold(f"{row.label_bn} / {row.label_en}" if row.label_bn else row.label_en)
    label = f"{row.label_en} ({row.label_bn})" if row.label_bn else row.label_en
    return _bold(label) if row.kind in (KIND_SUBTOTAL, KIND_TOTAL) else label


def _render_trial_balance(
    trial: TrialBalance, fmt: Callable[..., str], as_at_text: str
) -> list[str]:
    strong = {KIND_SUBTOTAL, KIND_TOTAL}
    rows = []
    for row in trial_balance_rows(trial):
        emphasise = row.kind in strong
        rows.append(
            [
                row.code,
                _row_label(row),
                row.section if row.kind == KIND_LINE else "",
                _md_cell(fmt, row.debit, strong=emphasise),
                _md_cell(fmt, row.credit, strong=emphasise),
                _md_cell(fmt, row.amount, strong=emphasise),
            ]
        )
    out = [
        f"## {_term_heading('trial_balance')} — as at {as_at_text}",
        "",
        tb.markdown_table(
            ["Code", "Account", "Type", "Debit (৳)", "Credit (৳)", "Balance (৳)"],
            rows,
            aligns=["l", "l", "l", "r", "r", "r"],
        ),
        "",
        "Balance is stated positively in each account's normal direction — "
        f"{tb.term('debit')} for assets and expenses, {tb.term('credit')} for liabilities, "
        "equity and income.",
        "",
        "**Debits equal credits** — "
        f"{fmt(trial.total_debit, symbol=True)} debit against "
        f"{fmt(trial.total_credit, symbol=True)} credit, difference "
        f"{fmt(trial.difference, symbol=True)}. রেওয়ামিল মিলেছে / the trial balance ties.",
    ]
    return out


def _render_amount_statement(
    heading: str, rows: Sequence[StatementRow], fmt: Callable[..., str]
) -> list[str]:
    table_rows = []
    for row in rows:
        emphasise = row.kind in (KIND_SUBTOTAL, KIND_TOTAL)
        table_rows.append(
            [row.code, _row_label(row), _md_cell(fmt, row.amount, strong=emphasise)]
        )
    return [
        heading,
        "",
        tb.markdown_table(
            ["Code", "Item", "Amount (৳)"], table_rows, aligns=["l", "l", "r"]
        ),
    ]


def render_markdown(
    statements: FinancialStatements,
    *,
    files: Sequence[Path] = (),
    statement: str = "all",
    grouping: str | None = None,
) -> str:
    """Render the statements for reading in chat.  Every number here is also in the CSVs."""
    config = statements.config
    fmt = _make_formatter(config, grouping)
    wanted = _normalise_statement(statement)

    lines: list[str] = [f"# {tb.PROJECT_NAME} — আর্থিক বিবরণী / Financial statements", ""]

    if config is not None:
        lines.append(f"**{config.display_name}**")
        identifiers = []
        if config.bin:
            identifiers.append(f"BIN {config.bin}")
        if config.tin:
            identifiers.append(f"TIN {config.tin}")
        if identifiers:
            lines.append(" · ".join(identifiers))
        if config.assessment_year:
            lines.append(f"{tb.term('assessment_year')}: {config.assessment_year}")
    if statements.books_dir is not None:
        lines.append(f"Books: `{statements.books_dir}`")
    lines.append(f"Period requested: {statements.period_label}")
    lines.append(
        f"{statements.posting_count} postings in {statements.entry_count} "
        f"{tb.term('journal')} entries up to {statements.as_at_text}; "
        f"{statements.period_posting_count} postings in {statements.period_entry_count} "
        "entries fall inside the period."
    )
    if statements.posting_count == 0:
        lines.append("")
        lines.append(
            "> **The journal has no postings up to this date.** Every figure below is zero; "
            "nothing has been earned, spent, owned or owed yet."
        )
    elif statements.period_posting_count == 0:
        lines.append("")
        lines.append(
            "> **No postings fall inside the reporting period.** The "
            f"{tb.term('profit_and_loss')} account below is therefore zero; the "
            f"{tb.term('trial_balance')} and {tb.term('balance_sheet')} still carry the "
            "cumulative position."
        )
    lines.append("")
    lines.append(
        f"> The {tb.term('profit_and_loss')} account covers **{statements.period_text}**. "
        f"The {tb.term('trial_balance')} and the {tb.term('balance_sheet')} are stated "
        f"**as at {statements.as_at_text}**, cumulative from the start of the books."
    )
    lines.append("")

    if "trial-balance" in wanted:
        lines.extend(_render_trial_balance(statements.trial_balance, fmt, statements.as_at_text))
        lines.append("")

    if "profit-and-loss" in wanted:
        lines.extend(
            _render_amount_statement(
                f"## {_term_heading('profit_and_loss')} — {statements.period_text}",
                profit_and_loss_rows(statements.profit_and_loss),
                fmt,
            )
        )
        lines.append("")
        lines.append(
            "**Net profit carried to the balance sheet** — "
            f"{fmt(statements.profit_and_loss.net_profit, symbol=True)} appears unchanged as "
            f"\u201cProfit for the period\u201d in the {tb.term('equity')} section of the "
            f"{tb.term('balance_sheet')}."
        )
        lines.append("")

    if "balance-sheet" in wanted:
        balance_sheet = statements.balance_sheet
        lines.extend(
            _render_amount_statement(
                f"## {_term_heading('balance_sheet')} — as at {statements.as_at_text}",
                balance_sheet_rows(balance_sheet),
                fmt,
            )
        )
        lines.append("")
        lines.append(
            "**Assets equal Liabilities plus Equity** — "
            f"{fmt(balance_sheet.total_assets, symbol=True)} = "
            f"{fmt(balance_sheet.total_liabilities, symbol=True)} + "
            f"{fmt(balance_sheet.total_equity, symbol=True)}, difference "
            f"{fmt(balance_sheet.difference, symbol=True)}. স্থিতিপত্র মিলেছে / "
            "the balance sheet ties."
        )
        lines.append("")

    lines.append("### Reconciliations performed")
    lines.append("")
    for check in statements.checks:
        mark = "PASS" if check.ok else "FAIL"
        detail = check.describe(lambda amount: fmt(amount, symbol=True))
        lines.append(f"- **{mark}** `{check.name}` — {detail}")
    lines.append("")

    if files:
        lines.append("### CSV written")
        lines.append("")
        for path in files:
            lines.append(f"- `{path}`")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(tb.DISCLAIMER_EN)
    if config is not None and config.language in ("bn", "bn-en"):
        lines.append("")
        lines.append(tb.DISCLAIMER_BN)
    lines.append("")
    lines.append(tb.ATTRIBUTION)
    return "\n".join(lines)


def _normalise_statement(statement: str) -> tuple[str, ...]:
    key = str(statement or "all").strip().lower()
    aliases = {
        "tb": "trial-balance",
        "trial": "trial-balance",
        "trial-balance": "trial-balance",
        "pl": "profit-and-loss",
        "p&l": "profit-and-loss",
        "profit-and-loss": "profit-and-loss",
        "bs": "balance-sheet",
        "balance-sheet": "balance-sheet",
    }
    if key in ("all", ""):
        return ("trial-balance", "profit-and-loss", "balance-sheet")
    if key in aliases:
        return (aliases[key],)
    raise tb.ValidationError(
        f"--statement {statement!r} is not one I know.",
        problems=(f"--statement={statement!r}",),
        hint="Use all, trial-balance (tb), profit-and-loss (pl) or balance-sheet (bs).",
    )


# ======================================================================================
# CSV rendering — same rows, machine-readable amounts
# ======================================================================================

_TRIAL_BALANCE_CSV_HEADERS = (
    "section",
    "kind",
    "code",
    "account",
    "account_bn",
    "debit",
    "credit",
    "balance",
)
_AMOUNT_CSV_HEADERS = ("section", "kind", "code", "item", "item_bn", "amount")


def _csv_text(headers: Sequence[str], rows: Iterable[Sequence[str]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(list(headers))
    for row in rows:
        writer.writerow(["" if cell is None else str(cell) for cell in row])
    return buffer.getvalue()


def _csv_amount(amount: tb.Money | None) -> str:
    return "" if amount is None else tb.format_amount_for_csv(amount)


def trial_balance_csv(trial: TrialBalance) -> str:
    rows = [
        (
            row.section,
            row.kind,
            row.code,
            row.label_en,
            row.label_bn,
            _csv_amount(row.debit),
            _csv_amount(row.credit),
            _csv_amount(row.amount),
        )
        for row in trial_balance_rows(trial)
        if row.kind != KIND_HEADING
    ]
    return _csv_text(_TRIAL_BALANCE_CSV_HEADERS, rows)


def _amount_csv(rows: Sequence[StatementRow]) -> str:
    return _csv_text(
        _AMOUNT_CSV_HEADERS,
        [
            (row.section, row.kind, row.code, row.label_en, row.label_bn, _csv_amount(row.amount))
            for row in rows
            if row.kind != KIND_HEADING
        ],
    )


def report_filenames(statements: FinancialStatements) -> dict[str, str]:
    """Deterministic, re-runnable CSV names that state the period they cover."""
    as_at = statements.as_at.isoformat() if statements.as_at else "all"
    covers_from = statements.covers_from.isoformat() if statements.covers_from else "start"
    return {
        "trial_balance": f"trial-balance_{as_at}.csv",
        "profit_and_loss": f"profit-and-loss_{covers_from}_{as_at}.csv",
        "balance_sheet": f"balance-sheet_{as_at}.csv",
    }


def write_csv_reports(
    statements: FinancialStatements, reports_dir: "Path | str"
) -> list[Path]:
    """Write all three CSVs atomically.  Returns the paths in statement order."""
    directory = tb.ensure_dir(reports_dir)
    names = report_filenames(statements)
    written = [
        tb.write_text_atomic(
            directory / names["trial_balance"], trial_balance_csv(statements.trial_balance)
        ),
        tb.write_text_atomic(
            directory / names["profit_and_loss"],
            _amount_csv(profit_and_loss_rows(statements.profit_and_loss)),
        ),
        tb.write_text_atomic(
            directory / names["balance_sheet"],
            _amount_csv(balance_sheet_rows(statements.balance_sheet)),
        ),
    ]
    return written


# ======================================================================================
# JSON payload
# ======================================================================================


def _line_payload(line: ReportLine) -> dict[str, Any]:
    return {
        "code": line.code,
        "name": line.name,
        "name_bn": line.name_bn,
        "type": line.account_type,
        "debit": line.debit,
        "credit": line.credit,
        "balance": line.amount,
    }


def _section_payload(section: Section) -> dict[str, Any]:
    return {
        "key": section.key,
        "label_en": section.label_en,
        "label_bn": section.label_bn,
        "total": section.total,
        "lines": [_line_payload(line) for line in section.lines],
    }


def build_payload(
    statements: FinancialStatements, *, files: Sequence[Path] = ()
) -> dict[str, Any]:
    """The ``--json`` document.  Same numbers as the Markdown and the CSVs."""
    config = statements.config
    trial = statements.trial_balance
    profit_and_loss = statements.profit_and_loss
    balance_sheet = statements.balance_sheet
    return {
        "ok": True,
        "project": tb.PROJECT_NAME,
        "version": tb.__version__,
        "books": statements.books_dir,
        "business": {
            "name": config.business_name if config else "",
            "name_bn": config.business_name_bn if config else "",
            "bin": config.bin if config else "",
            "tin": config.tin if config else "",
        },
        "assessment_year": config.assessment_year if config else None,
        "period": {
            "requested": statements.period_label,
            "start": statements.period_start,
            "end": statements.period_end,
            "covers_from": statements.covers_from,
            "as_at": statements.as_at,
            "postings": statements.posting_count,
            "entries": statements.entry_count,
            "period_postings": statements.period_posting_count,
            "period_entries": statements.period_entry_count,
        },
        "trial_balance": {
            "as_at": trial.as_at,
            "lines": [_line_payload(line) for line in trial.lines],
            "total_debit": trial.total_debit,
            "total_credit": trial.total_credit,
            "difference": trial.difference,
            "balanced": trial.is_balanced,
        },
        "profit_and_loss": {
            "start": profit_and_loss.start,
            "end": profit_and_loss.end,
            "sections": [_section_payload(section) for section in profit_and_loss.sections],
            "revenue": profit_and_loss.revenue,
            "cost_of_sales": profit_and_loss.cost_of_sales,
            "gross_profit": profit_and_loss.gross_profit,
            "operating_expenses": profit_and_loss.operating_expenses,
            "operating_profit": profit_and_loss.operating_profit,
            "other_income": profit_and_loss.other_income,
            "other_expenses": profit_and_loss.other_expenses,
            "net_profit": profit_and_loss.net_profit,
        },
        "balance_sheet": {
            "as_at": balance_sheet.as_at,
            "assets": _section_payload(balance_sheet.assets),
            "liabilities": _section_payload(balance_sheet.liabilities),
            "equity": _section_payload(balance_sheet.equity),
            "opening_result": balance_sheet.opening_result,
            "period_result": balance_sheet.period_result,
            "accumulated_result": balance_sheet.accumulated_result,
            "total_assets": balance_sheet.total_assets,
            "total_liabilities": balance_sheet.total_liabilities,
            "total_equity": balance_sheet.total_equity,
            "total_liabilities_and_equity": balance_sheet.total_liabilities_and_equity,
            "difference": balance_sheet.difference,
            "balanced": balance_sheet.is_balanced,
        },
        "checks": [
            {
                "name": check.name,
                "ok": check.ok,
                "detail": check.detail,
                "amounts": list(check.amounts),
            }
            for check in statements.checks
        ],
        "files": [str(path) for path in files],
        "attribution": tb.ATTRIBUTION,
        "disclaimer_en": tb.DISCLAIMER_EN,
        "disclaimer_bn": tb.DISCLAIMER_BN,
    }


# ======================================================================================
# CLI
# ======================================================================================


def build_parser() -> Any:
    parser = tb.common_parser(
        "report.py",
        "Financial statements from the journal: রেওয়ামিল / trial balance, "
        "লাভ-ক্ষতি হিসাব / profit and loss, স্থিতিপত্র / balance sheet. "
        "Markdown on stdout, CSV in <books>/reports/, both from one computation.",
    )
    parser.add_argument(
        "--from",
        dest="date_from",
        metavar="YYYY-MM-DD",
        help="first date of the reporting period (inclusive)",
    )
    parser.add_argument(
        "--to",
        dest="date_to",
        metavar="YYYY-MM-DD",
        help="last date of the reporting period (inclusive); the trial balance and "
        "balance sheet are stated as at this date",
    )
    parser.add_argument(
        "--period",
        metavar="PERIOD",
        help="a month as YYYY-MM (e.g. 2026-07) or a fiscal year as FY2026-27 / 2026-27 "
        "(reads books.fiscal_year_start from config.toml); not combinable with --from/--to",
    )
    parser.add_argument(
        "--statement",
        default="all",
        choices=(
            "all",
            "trial-balance",
            "tb",
            "profit-and-loss",
            "pl",
            "balance-sheet",
            "bs",
        ),
        help="which statement to print (Markdown only; --json always emits all three)",
    )
    parser.add_argument(
        "--reports-dir",
        metavar="DIR",
        help=f"where the CSVs go (default: <books>/{REPORTS_DIRNAME})",
    )
    parser.add_argument(
        "--no-csv", action="store_true", help="print only; do not write any CSV file"
    )
    parser.add_argument(
        "--include-unused",
        action="store_true",
        help="also list chart accounts that have no postings in the period",
    )
    parser.add_argument(
        "--grouping",
        choices=(tb.GROUPING_BD, tb.GROUPING_INTL),
        help="digit grouping for the Markdown output "
        f"(default: locale.grouping from config.toml, normally {tb.GROUPING_BD} — "
        "লাখ/কোটি 12,34,567.89)",
    )
    return parser


def run(args: Any, *, out: Any = None) -> dict[str, Any]:
    """Load, compute, reconcile, write and print.  Raises :class:`tb.TakaBooksError`."""
    stream = out if out is not None else sys.stdout

    # Ledger.load defaults to require_balanced=True: a report is never computed from
    # books that do not tie back to the journal (spec §2).
    ledger = tb.Ledger.load(args.books)
    statement = getattr(args, "statement", "all")
    _normalise_statement(statement)  # fail on a bad --statement before doing any work

    start, end, label = resolve_period(
        period=getattr(args, "period", None),
        date_from=getattr(args, "date_from", None),
        date_to=getattr(args, "date_to", None),
        config=ledger.config,
    )
    statements = build_statements(
        ledger,
        period_start=start,
        period_end=end,
        period_label=label,
        include_unused=bool(getattr(args, "include_unused", False)),
    )

    files: list[Path] = []
    if not getattr(args, "no_csv", False):
        reports_dir = (
            Path(args.reports_dir)
            if getattr(args, "reports_dir", None)
            else Path(args.books) / REPORTS_DIRNAME
        )
        files = write_csv_reports(statements, reports_dir)

    payload = build_payload(statements, files=files)
    if getattr(args, "json", False):
        stream.write(tb.json_dumps(payload) + "\n")
    else:
        stream.write(
            render_markdown(
                statements,
                files=files,
                statement=statement,
                grouping=getattr(args, "grouping", None),
            )
            + "\n"
        )
    return payload


def main(argv: Sequence[str] | None = None, *, out: Any = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    with tb.cli_guard(json_output=bool(getattr(args, "json", False))):
        run(args, out=out)
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised by the CLI, not the tests
    tb.check_python_or_exit()
    raise SystemExit(main())
