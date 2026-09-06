#!/usr/bin/env python3
"""TakaBooks — whole-ledger integrity checker (খতিয়ান যাচাই / ledger validation).

This is the tool a user runs *before* trusting anything else: before a trial balance,
before a মূসক / VAT return, before an আয়কর / income tax computation.  It reads every
file under ``books/`` and reports every problem it can find **at once**, each one
carrying the file, the line and the ``entry_id`` that caused it.

Unlike ``report.py`` / ``vat.py`` / ``tax.py`` — which load the ledger strictly and stop
at the first broken entry — this script is deliberately tolerant while reading: a row
that cannot be parsed becomes a *finding*, not a traceback, so one typo never hides the
nine problems behind it.

What it checks (see :data:`CHECKS`, or run ``--list-checks``):

* entries whose debits do not equal their credits, with the imbalance stated in ৳
* unknown account codes, and postings to accounts the chart marks inactive
* an ``entry_id`` reused by rows that are not part of the same entry
* malformed dates, dates outside the configured financial year, rows filed in the
  wrong month, dates running backwards, journal files not named ``YYYY-MM.csv``
* rows with both ``debit`` and ``credit`` set, or with neither
* negative amounts, blank ``entry_id``/``account``, short rows, wrong CSV header
* malformed ``tax_tag`` cells, and VAT/TDS/VDS tags sitting on accounts that are not
  relevant to that tax
* orphan postings — an ``entry_id`` with a single line, which can never balance

Findings are grouped by severity.  **The exit code is 0 only when nothing was found**
(pass ``--allow-warnings`` to accept a book that has warnings but no errors).

This script defines no Bangladeshi rate, threshold, deadline or statute number.  It
checks structure only; every figure it prints comes from the user's own journal.

TakaBooks — Moshiur Rahman (@bemoshiur) · TICON SYSTEM LTD — https://ticonsys.com
MIT licensed · https://github.com/bemoshiur/TakaBooks
"""

from __future__ import annotations

import argparse
import calendar
import csv
import datetime
import io
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

_ENGINE_DIR = str(Path(__file__).resolve().parent)
if _ENGINE_DIR not in sys.path:  # pragma: no cover - import plumbing
    sys.path.insert(0, _ENGINE_DIR)

import takabooks as tb  # noqa: E402  (must follow the sys.path bootstrap above)

__all__ = [
    "SEVERITY_ERROR",
    "SEVERITY_WARNING",
    "SEVERITIES",
    "FINDINGS_EXIT_CODE",
    "Check",
    "CHECKS",
    "CHECKS_BY_SLUG",
    "INACTIVE_TAGS",
    "Finding",
    "ValidationReport",
    "validate_books",
    "fiscal_year_window",
    "fiscal_year_start_for",
    "majority_fiscal_year",
    "render_text",
    "render_json",
    "render_checks",
    "build_parser",
    "main",
]

PROG = "validate.py"

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"
SEVERITIES: tuple[str, ...] = (SEVERITY_ERROR, SEVERITY_WARNING)

#: Account tags (in ``accounts.toml``) that retire an account from day-to-day posting.
INACTIVE_TAGS: tuple[str, ...] = ("inactive", "archived", "closed", "disabled", "retired")

#: Exit code used when the ledger is not clean — :class:`takabooks.ValidationError`.
FINDINGS_EXIT_CODE = tb.ValidationError.exit_code

#: At most this many individual "outside the financial year" findings are listed.
_MAX_FY_FINDINGS = 10

_ISO_DATEISH = re.compile(r"^\d{4}-\d{1,2}-\d{1,2}$")

#: Byte-order mark Excel likes to prepend to a UTF-8 CSV.
_BOM = "﻿"

# Which chart roles a tax_tag kind expects to see somewhere in its entry.
_KIND_ROLES: dict[str, tuple[str, ...]] = {
    tb.TAG_VAT_OUT: (tb.ROLE_VAT_OUTPUT,),
    tb.TAG_VAT_IN: (tb.ROLE_VAT_INPUT,),
    tb.TAG_TDS: (tb.ROLE_TDS_PAYABLE, tb.ROLE_TDS_RECEIVABLE),
    tb.TAG_VDS: (tb.ROLE_VDS_PAYABLE,),
}
# Every role that marks a tax control account; a tag on one of these must match.
_CONTROL_ROLES: frozenset[str] = frozenset(
    role for roles in _KIND_ROLES.values() for role in roles
)
# Loose account tags accepted as "this account is relevant to that tax".
_KIND_TAGS: dict[str, tuple[str, ...]] = {
    tb.TAG_VAT_OUT: ("vat", "vat_output", "output_vat"),
    tb.TAG_VAT_IN: ("vat", "vat_input", "input_vat"),
    tb.TAG_TDS: ("tds", "withholding"),
    tb.TAG_VDS: ("vds", "withholding"),
}
_KIND_TERM: dict[str, str] = {
    tb.TAG_VAT_OUT: tb.term("vat"),
    tb.TAG_VAT_IN: tb.term("vat"),
    tb.TAG_TDS: tb.term("tds"),
    tb.TAG_VDS: tb.term("vds"),
}


# ======================================================================================
# The catalogue of checks — `--list-checks` prints this, and every Finding must use one
# ======================================================================================


@dataclass(frozen=True)
class Check:
    """One named check: its stable slug, its severity and a one-line summary."""

    slug: str
    severity: str
    summary: str

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"check {self.slug!r} has severity {self.severity!r}")


CHECKS: tuple[Check, ...] = (
    # --- books / config / chart --------------------------------------------------------
    Check("config-unreadable", SEVERITY_ERROR, "books/config.toml is missing or invalid"),
    Check("accounts-unreadable", SEVERITY_ERROR, "accounts.toml is missing, invalid, or has duplicate codes"),
    Check("journal-missing", SEVERITY_ERROR, "the journal directory does not exist"),
    Check("journal-unreadable", SEVERITY_ERROR, "a journal file could not be read (encoding or permissions)"),
    Check("journal-header", SEVERITY_ERROR, "a journal file has a missing or wrong header row"),
    Check("no-journal-files", SEVERITY_WARNING, "no journal/*.csv files were found — nothing to validate"),
    Check("journal-filename", SEVERITY_WARNING, "a journal file is not named YYYY-MM.csv"),
    Check("journal-stray-file", SEVERITY_WARNING, "a non-CSV file is sitting in the journal directory"),
    Check("config-fiscal-year", SEVERITY_WARNING, "books.fiscal_year_start is not set, so date-range checks are skipped"),
    Check("config-assessment-year", SEVERITY_WARNING, "books.assessment_year (করবর্ষ) is not set; tax output must state it"),
    Check("missing-required-role", SEVERITY_WARNING, "a mandatory Bangladesh account role is not declared in accounts.toml"),
    Check("chart-code-format", SEVERITY_WARNING, "an account code is not a 4-digit code such as 1100"),
    Check("chart-block", SEVERITY_WARNING, "an account's leading digit disagrees with its type"),
    # --- row level ---------------------------------------------------------------------
    Check("row-fields", SEVERITY_ERROR, "a row has fewer columns than the journal schema needs"),
    Check("row-invalid", SEVERITY_ERROR, "a row was rejected by the journal schema"),
    Check("bad-date", SEVERITY_ERROR, "the date is not a strict ISO YYYY-MM-DD calendar date"),
    Check("missing-entry-id", SEVERITY_ERROR, "entry_id is blank, so the row belongs to no entry"),
    Check("missing-account", SEVERITY_ERROR, "the account code cell is blank"),
    Check("bad-amount", SEVERITY_ERROR, "a debit/credit cell is not a readable amount"),
    Check("negative-amount", SEVERITY_ERROR, "a debit or credit is negative; reverse the sides instead"),
    Check("both-sides", SEVERITY_ERROR, "debit and credit are both non-zero on one row"),
    Check("no-amount", SEVERITY_ERROR, "neither debit nor credit is set on the row"),
    Check("bad-tax-tag", SEVERITY_ERROR, "the tax_tag cell does not match the tax_tag grammar"),
    Check("unknown-account", SEVERITY_ERROR, "the account code is not in accounts.toml"),
    Check("inactive-account", SEVERITY_WARNING, "the account is tagged inactive in accounts.toml"),
    Check("tax-tag-account-mismatch", SEVERITY_ERROR, "a tax tag sits on the control account of a different tax"),
    Check("date-outside-financial-year", SEVERITY_WARNING, "the date falls outside the financial year being validated"),
    Check("date-out-of-order", SEVERITY_WARNING, "the date runs backwards inside one journal file"),
    Check("misfiled-posting", SEVERITY_WARNING, "the row sits in the journal file of a different month"),
    # --- entry level ---------------------------------------------------------------------
    Check("unbalanced-entry", SEVERITY_ERROR, "debits do not equal credits for one entry_id"),
    Check("orphan-entry", SEVERITY_ERROR, "an entry_id has a single line, so it can never balance"),
    Check("duplicate-entry-id", SEVERITY_ERROR, "one entry_id is used by rows that are not one entry"),
    Check("tax-tag-orphan", SEVERITY_WARNING, "an entry carries a tax tag but posts to no matching tax account"),
    Check("tax-tag-control-only", SEVERITY_WARNING, "a tax tag sits only on the tax control account, so its taxable value is ৳0.00"),
)

CHECKS_BY_SLUG: dict[str, Check] = {check.slug: check for check in CHECKS}


# ======================================================================================
# Findings
# ======================================================================================


@dataclass(frozen=True)
class Finding:
    """One problem, pinned to the file, line and entry that caused it."""

    severity: str
    check: str
    message: str
    file: str = ""
    line: int = 0
    end_line: int = 0
    entry_id: str = ""
    account: str = ""
    amount: "tb.Money | None" = None
    hint: str = ""

    @property
    def is_error(self) -> bool:
        return self.severity == SEVERITY_ERROR

    @property
    def location(self) -> str:
        """``'books/journal/2026-07.csv lines 3–4'`` — as precise as the finding allows."""
        if not self.file:
            return ""
        if self.line and self.end_line and self.end_line != self.line:
            return f"{self.file} lines {self.line}–{self.end_line}"
        if self.line:
            return f"{self.file} line {self.line}"
        return self.file

    @property
    def where(self) -> str:
        """Location plus ``· entry <id>`` when an entry_id is known."""
        parts = [part for part in (self.location, f"entry {self.entry_id}" if self.entry_id else "") if part]
        return " · ".join(parts)

    def sort_key(self) -> tuple[Any, ...]:
        rank = 0 if self.severity == SEVERITY_ERROR else 1
        return (rank, 0 if not self.file else 1, self.file, self.line, self.check, self.message)

    def render(self) -> str:
        """Multi-line text block for the human report."""
        head = f"[{self.check}]"
        where = self.where
        lines = [f"{head} {where}" if where else head, f"    {self.message}"]
        if self.hint:
            lines.append(f"    hint: {self.hint}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "check": self.check,
            "message": self.message,
            "file": self.file,
            "line": self.line or None,
            "end_line": self.end_line or None,
            "entry_id": self.entry_id,
            "account": self.account,
            "amount": self.amount,
            "hint": self.hint,
            "location": self.location,
        }


def _finding(slug: str, message: str, **kwargs: Any) -> Finding:
    """Build a :class:`Finding`, taking its severity from :data:`CHECKS`."""
    check = CHECKS_BY_SLUG[slug]  # KeyError here means an undeclared check slug.
    return Finding(severity=check.severity, check=slug, message=message, **kwargs)


# ======================================================================================
# Small helpers
# ======================================================================================


def _label(path: Path, relative_to: "Path | None") -> str:
    """Display a path relative to the books directory's parent, like the library does."""
    if relative_to is None:
        return str(path)
    try:
        return str(path.resolve().relative_to(Path(relative_to).resolve()))
    except (ValueError, OSError):
        return str(path)


def _money(amount: tb.Money, config: "tb.Config | None" = None) -> str:
    """Format money for humans: ৳ with লাখ/কোটি grouping, honouring the book's locale."""
    if config is not None:
        return config.format_money(amount, symbol=True)
    return tb.format_bdt(amount, symbol=True)


def _safe_date(year: int, month: int, day: int) -> datetime.date:
    """A date that never explodes on 29 February or a short month."""
    last = calendar.monthrange(year, month)[1]
    return datetime.date(year, month, min(day, last))


def fiscal_year_start_for(when: datetime.date, start_month: int, start_day: int) -> datetime.date:
    """The opening day of the financial year (starting MM-DD) that contains ``when``."""
    opens_this_year = _safe_date(when.year, start_month, start_day)
    if when >= opens_this_year:
        return opens_this_year
    return _safe_date(when.year - 1, start_month, start_day)


def fiscal_year_window(
    anchor: datetime.date, start_month: int, start_day: int
) -> tuple[datetime.date, datetime.date]:
    """The financial year (inclusive) that contains ``anchor`` and opens on MM-DD.

    This is pure calendar arithmetic: TakaBooks never assumes *which* month a
    Bangladeshi income year opens in — that comes from ``books.fiscal_year_start``.
    """
    start = fiscal_year_start_for(anchor, start_month, start_day)
    next_start = _safe_date(start.year + 1, start_month, start_day)
    return start, next_start - datetime.timedelta(days=1)


def majority_fiscal_year(
    dates: Iterable[datetime.date], start_month: int, start_day: int
) -> tuple[tuple[datetime.date, datetime.date], int, int]:
    """The financial year holding the most of ``dates`` → ``(window, inside, total)``.

    Anchoring on the *majority* rather than on the earliest row means one stray
    backdated posting is reported as the odd one out, instead of dragging the whole
    window back a year and flagging every correct row.  A tie goes to the later year.
    """
    counted = Counter(fiscal_year_start_for(d, start_month, start_day) for d in dates)
    if not counted:
        raise ValueError("majority_fiscal_year() needs at least one date.")
    best = max(counted, key=lambda start: (counted[start], start))
    return fiscal_year_window(best, start_month, start_day), counted[best], sum(counted.values())


def _account_matches_kind(account: tb.Account, kind: str) -> bool:
    """Is this account a control/relevant account for that tax tag kind?"""
    roles = _KIND_ROLES.get(kind, ())
    if account.role and account.role in roles:
        return True
    wanted = {tag.lower() for tag in _KIND_TAGS.get(kind, ())} | set(roles)
    return any(tag.strip().lower() in wanted for tag in account.tags)


# ======================================================================================
# The report
# ======================================================================================


@dataclass
class ValidationReport:
    """Everything ``validate.py`` learned about one ``books/`` directory."""

    books_dir: Path
    findings: list[Finding] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    config: "tb.Config | None" = None
    chart: "tb.ChartOfAccounts | None" = None
    journal_files: list[str] = field(default_factory=list)
    rows_read: int = 0
    postings_checked: int = 0
    entries: int = 0
    total_debit: tb.Money = field(default_factory=tb.Money.zero)
    total_credit: tb.Money = field(default_factory=tb.Money.zero)
    first_date: "datetime.date | None" = None
    last_date: "datetime.date | None" = None
    financial_year: "tuple[datetime.date, datetime.date] | None" = None
    financial_year_source: str = ""

    # -- derived --------------------------------------------------------------------

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == SEVERITY_ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == SEVERITY_WARNING]

    @property
    def difference(self) -> tb.Money:
        """Total debits − total credits across every posting that could be read."""
        return self.total_debit - self.total_credit

    @property
    def is_clean(self) -> bool:
        return not self.findings

    def ok(self, *, allow_warnings: bool = False) -> bool:
        return not self.errors if allow_warnings else self.is_clean

    def exit_code(self, *, allow_warnings: bool = False) -> int:
        return 0 if self.ok(allow_warnings=allow_warnings) else FINDINGS_EXIT_CODE

    def counts(self) -> dict[str, int]:
        return {
            "journal_files": len(self.journal_files),
            "rows_read": self.rows_read,
            "postings_checked": self.postings_checked,
            "entries": self.entries,
            "errors": len(self.errors),
            "warnings": len(self.warnings),
        }

    def by_check(self) -> dict[str, int]:
        """``{check slug: number of findings}`` in catalogue order — handy for summaries."""
        counted = Counter(finding.check for finding in self.findings)
        return {check.slug: counted[check.slug] for check in CHECKS if counted[check.slug]}

    def sorted_findings(self) -> list[Finding]:
        return sorted(self.findings, key=lambda f: f.sort_key())

    def summary_line(self, *, allow_warnings: bool = False) -> str:
        errors, warnings = len(self.errors), len(self.warnings)
        code = self.exit_code(allow_warnings=allow_warnings)
        if self.is_clean:
            tie = _money(self.total_debit, self.config)
            return (
                f"RESULT: clean — {self.postings_checked} posting(s) in {self.entries} "
                f"entry/entries, debits and credits agree at {tie}. (exit {code})"
            )
        counted = f"{errors} error(s), {warnings} warning(s)"
        if errors:
            return (
                f"RESULT: {counted} — do not file or report from these books until the "
                f"errors are fixed. (exit {code})"
            )
        if allow_warnings:
            return (
                f"RESULT: {counted} — no errors; warnings accepted because "
                f"--allow-warnings was given. (exit {code})"
            )
        return (
            f"RESULT: {counted} — no errors, but the ledger is not fully clean. "
            f"(exit {code}; pass --allow-warnings to accept warnings)"
        )

    def to_dict(self, *, allow_warnings: bool = False) -> dict[str, Any]:
        config = self.config
        fy = self.financial_year
        return {
            "ok": self.ok(allow_warnings=allow_warnings),
            "tool": PROG,
            "takabooks_version": tb.__version__,
            "books": str(self.books_dir),
            "business": {
                "name": config.business_name if config else "",
                "name_bn": config.business_name_bn if config else "",
                "bin": config.bin if config else "",
                "tin": config.tin if config else "",
            },
            "assessment_year": (config.assessment_year if config else None),
            "financial_year": (
                {
                    "start": fy[0],
                    "end": fy[1],
                    "source": self.financial_year_source,
                }
                if fy
                else None
            ),
            "journal_files": list(self.journal_files),
            "counts": self.counts(),
            "by_check": self.by_check(),
            "totals": {
                "debit": self.total_debit,
                "credit": self.total_credit,
                "difference": self.difference,
            },
            "date_range": {"first": self.first_date, "last": self.last_date},
            "findings": [finding.to_dict() for finding in self.sorted_findings()],
            "notes": list(self.notes),
            "summary": self.summary_line(allow_warnings=allow_warnings),
            "exit_code": self.exit_code(allow_warnings=allow_warnings),
            "attribution": tb.ATTRIBUTION,
            "disclaimer": {"en": tb.DISCLAIMER_EN, "bn": tb.DISCLAIMER_BN},
        }


# ======================================================================================
# Reading the journal tolerantly — a bad row is a finding, never a traceback
# ======================================================================================


@dataclass
class _Run:
    """One contiguous block of rows sharing an ``entry_id`` in one file on one date.

    A journal entry is one transaction on one date, written as adjacent rows.  Runs are
    built from *every* data row — parsed or not — so a broken row between two blocks
    of the same id cannot hide that the id was reused.
    """

    entry_id: str
    file: str
    first_line: int
    last_line: int
    date: "datetime.date | None"
    postings: list[tb.Posting] = field(default_factory=list)
    damaged: bool = False

    @property
    def location(self) -> str:
        if self.first_line == self.last_line:
            return f"{self.file} line {self.first_line}"
        return f"{self.file} lines {self.first_line}–{self.last_line}"


@dataclass(frozen=True)
class _RowResult:
    posting: "tb.Posting | None"
    entry_id: str
    date: "datetime.date | None"


def _normalise_header(cells: Sequence[str]) -> list[str]:
    normalised: list[str] = []
    for index, cell in enumerate(cells):
        text = str(cell)
        if index == 0:
            text = text.lstrip(_BOM)
        normalised.append(text.strip().lower())
    while normalised and normalised[-1] == "":
        normalised.pop()
    return normalised


def _check_row(
    cells: Sequence[str],
    *,
    label: str,
    line: int,
    findings: list[Finding],
) -> _RowResult:
    """Validate one CSV data row.

    Returns the :class:`tb.Posting` when the row is sound, otherwise ``None`` in its
    place — after recording one finding per problem, so a row with a bad date *and* a
    bad amount reports both.
    """
    values = list(cells)
    entry_id_guess = str(values[1]).strip() if len(values) > 1 else ""

    if len(values) < 6:
        findings.append(
            _finding(
                "row-fields",
                f"This row has {len(values)} field(s); a journal row needs at least 6 "
                f"({', '.join(tb.JOURNAL_COLUMNS[:6])}).",
                file=label,
                line=line,
                entry_id=entry_id_guess,
                hint=f"The header must be: {tb.JOURNAL_HEADER}",
            )
        )
        return _RowResult(None, entry_id_guess, None)

    # `memo` is last precisely so unquoted commas in it survive — mirror Posting.from_row.
    if len(values) > len(tb.JOURNAL_COLUMNS):
        keep = len(tb.JOURNAL_COLUMNS) - 1
        values = values[:keep] + [",".join(str(cell) for cell in values[keep:])]
    values += [""] * (len(tb.JOURNAL_COLUMNS) - len(values))
    row = dict(zip(tb.JOURNAL_COLUMNS, (str(cell) for cell in values)))

    entry_id = row["entry_id"].strip()
    account = row["account"].strip()
    broken = False

    date: datetime.date | None = None
    try:
        date = tb.parse_date(row["date"])
    except tb.JournalError as exc:
        broken = True
        findings.append(
            _finding(
                "bad-date",
                exc.message,
                file=label,
                line=line,
                entry_id=entry_id,
                account=account,
                hint=exc.hint or "",
            )
        )

    if not entry_id:
        broken = True
        findings.append(
            _finding(
                "missing-entry-id",
                "entry_id is blank — it is what groups rows into one balanced entry.",
                file=label,
                line=line,
                account=account,
                hint="Give every line of one transaction the same entry_id, e.g. SAL-2026-07-001.",
            )
        )
    if not account:
        broken = True
        findings.append(
            _finding(
                "missing-account",
                "The account code cell is blank; every posting needs a code from accounts.toml.",
                file=label,
                line=line,
                entry_id=entry_id,
            )
        )

    amounts: dict[str, tb.Money] = {}
    for side in ("debit", "credit"):
        try:
            amounts[side] = tb.parse_amount_field(row[side], field_name=side)
        except tb.JournalError as exc:
            broken = True
            findings.append(
                _finding(
                    "bad-amount",
                    exc.message,
                    file=label,
                    line=line,
                    entry_id=entry_id,
                    account=account,
                    hint=exc.hint or "Write plain decimal taka, e.g. 12500.00 (blank means ৳0.00).",
                )
            )

    if len(amounts) == 2:
        debit, credit = amounts["debit"], amounts["credit"]
        negative = False
        for side, amount in (("debit", debit), ("credit", credit)):
            if amount.is_negative():
                broken = True
                negative = True
                findings.append(
                    _finding(
                        "negative-amount",
                        f"The {side} is negative ({_money(amount)}). Amounts are always positive; "
                        "put the value on the other side instead of negating it.",
                        file=label,
                        line=line,
                        entry_id=entry_id,
                        account=account,
                        amount=amount,
                    )
                )
        if not negative and not debit.is_zero() and not credit.is_zero():
            broken = True
            findings.append(
                _finding(
                    "both-sides",
                    f"Debit ({_money(debit)}) and credit ({_money(credit)}) are both non-zero. "
                    "One row carries one side; split it into two rows.",
                    file=label,
                    line=line,
                    entry_id=entry_id,
                    account=account,
                )
            )
        elif not negative and debit.is_zero() and credit.is_zero():
            broken = True
            findings.append(
                _finding(
                    "no-amount",
                    "Both debit and credit are ৳0.00 — exactly one of the two must be non-zero.",
                    file=label,
                    line=line,
                    entry_id=entry_id,
                    account=account,
                )
            )

    tax_tag: tb.TaxTag | None = None
    try:
        tax_tag = tb.TaxTag.parse(row["tax_tag"])
    except tb.TaxTagError as exc:
        broken = True
        findings.append(
            _finding(
                "bad-tax-tag",
                exc.message,
                file=label,
                line=line,
                entry_id=entry_id,
                account=account,
                hint=exc.hint or tb.TAX_TAG_GRAMMAR,
            )
        )

    if broken or date is None or tax_tag is None or len(amounts) != 2:
        return _RowResult(None, entry_id, date)

    try:
        posting = tb.Posting(
            date=date,
            entry_id=entry_id,
            description=row["description"],
            account=account,
            debit=amounts["debit"],
            credit=amounts["credit"],
            party=row["party"],
            doc_ref=row["doc_ref"],
            tax_tag=tax_tag,
            memo=row["memo"],
            source_file=label,
            source_line=line,
        )
    except tb.TakaBooksError as exc:  # pragma: no cover - belt and braces
        findings.append(
            _finding(
                "row-invalid",
                exc.message,
                file=label,
                line=line,
                entry_id=entry_id,
                account=account,
                hint=exc.hint or "",
            )
        )
        return _RowResult(None, entry_id, date)
    return _RowResult(posting, entry_id, date)


def _extend_runs(runs: list[_Run], result: _RowResult, *, label: str, line: int) -> None:
    """Attach one data row to the current run, or open a new one."""
    if not result.entry_id:
        return  # already reported as missing-entry-id; it belongs to nothing
    current = runs[-1] if runs else None
    continues = (
        current is not None
        and current.file == label
        and current.entry_id == result.entry_id
        and (result.date is None or current.date is None or current.date == result.date)
    )
    if current is None or not continues:
        current = _Run(result.entry_id, label, line, line, result.date)
        runs.append(current)
    current.last_line = line
    if current.date is None and result.date is not None:
        current.date = result.date
    if result.posting is None:
        current.damaged = True
    else:
        current.postings.append(result.posting)


def _read_journal_file(
    path: Path,
    *,
    label: str,
    findings: list[Finding],
    notes: list[str],
    runs: list[_Run],
) -> tuple[list[tb.Posting], int]:
    """Read one journal CSV tolerantly.  Returns (postings, data rows seen)."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        findings.append(
            _finding(
                "journal-unreadable",
                f"This file is not UTF-8 ({exc}). Its rows were not checked.",
                file=label,
                hint="Save it as UTF-8 (choose 'CSV UTF-8' in Excel).",
            )
        )
        return [], 0
    except OSError as exc:
        findings.append(
            _finding(
                "journal-unreadable",
                f"This file could not be read ({exc}). Its rows were not checked.",
                file=label,
            )
        )
        return [], 0

    reader = csv.reader(io.StringIO(text, newline=""))
    postings: list[tb.Posting] = []
    rows = 0
    header_seen = False
    for cells in reader:
        line = reader.line_num
        if not cells or all(str(cell).strip() == "" for cell in cells):
            continue
        if str(cells[0]).lstrip(_BOM).lstrip().startswith("#"):
            continue
        if not header_seen:
            header = _normalise_header(cells)
            if header != list(tb.JOURNAL_COLUMNS):
                looks_like_data = bool(_ISO_DATEISH.match(header[0] if header else ""))
                message = (
                    "The first row is data, not a header row."
                    if looks_like_data
                    else f"Unexpected header row: {','.join(header)}"
                )
                findings.append(
                    _finding(
                        "journal-header",
                        f"{message} No row in this file was checked.",
                        file=label,
                        line=line,
                        hint=f"The first non-blank line must be exactly: {tb.JOURNAL_HEADER}",
                    )
                )
                notes.append(f"{label}: rows were not checked because its header row is wrong.")
                return [], 0
            header_seen = True
            continue
        rows += 1
        result = _check_row(cells, label=label, line=line, findings=findings)
        _extend_runs(runs, result, label=label, line=line)
        if result.posting is not None:
            postings.append(result.posting)

    if not header_seen:
        findings.append(
            _finding(
                "journal-header",
                "No header row was found in this file.",
                file=label,
                hint=f"The first non-blank line must be exactly: {tb.JOURNAL_HEADER}",
            )
        )
    return postings, rows


# ======================================================================================
# Structural checks over the postings that did parse
# ======================================================================================


def _check_accounts(
    postings: Sequence[tb.Posting], chart: "tb.ChartOfAccounts | None", findings: list[Finding]
) -> None:
    """Unknown codes (error) and postings to retired accounts (warning)."""
    if chart is None:
        return
    for posting in postings:
        if not chart.has(posting.account):
            findings.append(
                _finding(
                    "unknown-account",
                    f"Account code {posting.account!r} is not in "
                    f"{chart.source_path.name if chart.source_path else 'accounts.toml'}.",
                    file=posting.source_file,
                    line=posting.source_line,
                    entry_id=posting.entry_id,
                    account=posting.account,
                    hint="Add the account to accounts.toml, or correct the code on this row.",
                )
            )
            continue
        account = chart.get(posting.account)
        retired = [tag for tag in account.tags if tag.strip().lower() in INACTIVE_TAGS]
        if retired:
            findings.append(
                _finding(
                    "inactive-account",
                    f"Account {account.label} is tagged {retired[0]!r} in accounts.toml but is "
                    "still being posted to.",
                    file=posting.source_file,
                    line=posting.source_line,
                    entry_id=posting.entry_id,
                    account=posting.account,
                    hint="Post to the replacement account, or drop the inactive tag if the "
                    "account is in use again.",
                )
            )


def _runs_by_id(runs: Sequence[_Run]) -> dict[str, list[_Run]]:
    by_id: dict[str, list[_Run]] = {}
    for run in runs:
        by_id.setdefault(run.entry_id, []).append(run)
    return by_id


def _check_duplicate_entry_ids(runs: Sequence[_Run], findings: list[Finding]) -> set[str]:
    """One entry_id must cover exactly one contiguous group of rows, in one file, on one date.

    Returns the ids that were reported, so the entry checks can treat them specially.
    """
    duplicated: set[str] = set()
    for entry_id, groups in _runs_by_id(runs).items():
        if len(groups) < 2:
            continue
        duplicated.add(entry_id)
        reasons: list[str] = []
        files = sorted({run.file for run in groups if run.file})
        dates = sorted({run.date for run in groups if run.date is not None})
        if len(files) > 1:
            reasons.append(f"across {len(files)} files")
        if len(dates) > 1:
            reasons.append(
                "on " + ", ".join(d.isoformat() for d in dates[:4])
                + (" …" if len(dates) > 4 else "")
            )
        where = "; ".join(run.location for run in groups)
        detail = f" ({', '.join(reasons)})" if reasons else ""
        first = groups[0]
        findings.append(
            _finding(
                "duplicate-entry-id",
                f"entry_id {entry_id!r} is used by {len(groups)} separate groups of rows"
                f"{detail}: {where}. Rows sharing an entry_id must be one entry, written "
                "together on one date.",
                file=first.file,
                line=first.first_line,
                end_line=first.last_line,
                entry_id=entry_id,
                hint="Give each transaction its own entry_id; TakaBooks balances rows by "
                "entry_id, so a reused id silently merges two transactions.",
            )
        )
    return duplicated


def _check_entries(
    runs: Sequence[_Run],
    findings: list[Finding],
    notes: list[str],
    config: "tb.Config | None",
    *,
    duplicated: "set[str] | frozenset[str]" = frozenset(),
) -> None:
    """Orphan lines and the double-entry invariant (spec §2), one run at a time.

    Checking per contiguous run — not per merged entry_id — means a reused id is
    reported once as ``duplicate-entry-id`` while each transaction is still judged on
    its own rows, instead of the two being summed into one meaningless imbalance.
    When the rows of a reused id *do* balance taken together (one entry split by a
    date typo or an interleaved row), only the duplicate is reported: it is the root
    cause, and the per-run orphans it would produce are noise.
    """
    by_id = _runs_by_id(runs)
    settled: set[str] = set()
    for entry_id in sorted(duplicated):
        group = by_id.get(entry_id, [])
        if not group or any(run.damaged for run in group):
            continue
        together = [posting for run in group for posting in run.postings]
        if len(together) > 1 and tb.Entry.from_postings(together).is_balanced:
            settled.add(entry_id)
            notes.append(
                f"entry {entry_id!r}: its {len(together)} rows balance when taken together, "
                "so only the reused entry_id was reported — fix that first."
            )
    for run in runs:
        if run.entry_id in settled:
            continue
        if run.damaged:
            notes.append(
                f"Balance was not checked for entry {run.entry_id!r} ({run.location}) "
                "because at least one of its rows could not be read."
            )
            continue
        first = run.postings[0]
        if len(run.postings) == 1:
            findings.append(
                _finding(
                    "orphan-entry",
                    f"entry_id {run.entry_id!r} has a single line "
                    f"({first.account} {'debit' if first.is_debit else 'credit'} "
                    f"{_money(first.amount, config)}), so it can never balance. Every entry "
                    "needs at least one debit and one credit.",
                    file=run.file,
                    line=run.first_line,
                    entry_id=run.entry_id,
                    account=first.account,
                    amount=first.amount,
                    hint="Add the other side of the transaction, or fix the entry_id if this "
                    "row belongs to an entry above.",
                )
            )
            continue
        entry = tb.Entry.from_postings(run.postings)
        if not entry.is_balanced:
            difference = entry.difference
            side = "debit" if difference.is_positive() else "credit"
            findings.append(
                _finding(
                    "unbalanced-entry",
                    f"entry_id {run.entry_id!r} dated {entry.date.isoformat()} does not "
                    f"balance: debits {_money(entry.total_debit, config)} vs credits "
                    f"{_money(entry.total_credit, config)} — "
                    f"{_money(abs(difference), config)} too much {side}.",
                    file=run.file,
                    line=run.first_line,
                    end_line=run.last_line,
                    entry_id=run.entry_id,
                    amount=difference,
                    hint="Correct the rows. TakaBooks never adjusts your numbers for you.",
                )
            )


def _check_tax_tags(
    runs: Sequence[_Run], chart: "tb.ChartOfAccounts | None", findings: list[Finding]
) -> None:
    """VAT/TDS/VDS tags must sit on, and travel with, the right accounts.

    The convention shared with ``vat.py``: inside one entry, the line hitting the tax
    control account (chart role ``vat_output`` / ``vat_input`` / ``vds_payable`` /
    ``tds_*``) *is* the tax; every other line carrying the same tag is taxable value.
    """
    if chart is None:
        return

    # Row level: a tag sitting directly on the control account of a *different* tax.
    mismatched: set[tuple[str, str]] = set()
    for run in runs:
        for posting in run.postings:
            kind = posting.tax_tag.kind
            if kind == tb.TAG_NONE or not chart.has(posting.account):
                continue
            account = chart.get(posting.account)
            if account.role in _CONTROL_ROLES and account.role not in _KIND_ROLES.get(kind, ()):
                mismatched.add((run.entry_id, kind))
                findings.append(
                    _finding(
                        "tax-tag-account-mismatch",
                        f"tax_tag {str(posting.tax_tag)} ({_KIND_TERM.get(kind, kind)}) sits on "
                        f"{account.label}, which accounts.toml declares as role "
                        f"{account.role!r} — a different tax.",
                        file=posting.source_file,
                        line=posting.source_line,
                        entry_id=posting.entry_id,
                        account=posting.account,
                        hint=tb.TAX_TAG_GRAMMAR,
                    )
                )

    # Entry level: the tag should be accompanied by its control account somewhere, and
    # the control line must not be the *only* tagged line.
    declared = {
        kind: [role for role in roles if chart.by_role(role)]
        for kind, roles in _KIND_ROLES.items()
    }
    for run in runs:
        known = {p.account: chart.get(p.account) for p in run.postings if chart.has(p.account)}
        tagged_by_kind: dict[str, list[tb.Posting]] = {}
        for posting in run.postings:
            kind = posting.tax_tag.kind
            if kind != tb.TAG_NONE:
                tagged_by_kind.setdefault(kind, []).append(posting)
        for kind, tagged in tagged_by_kind.items():
            if not declared.get(kind) or (run.entry_id, kind) in mismatched:
                continue  # nothing to compare, or the row-level error already says it all
            first = tagged[0]
            control_present = any(_account_matches_kind(a, kind) for a in known.values())
            if not control_present:
                expected = ", ".join(
                    account.label for role in declared[kind] for account in chart.by_role(role)
                )
                findings.append(
                    _finding(
                        "tax-tag-orphan",
                        f"entry_id {run.entry_id!r} carries tax_tag {str(first.tax_tag)} "
                        f"({_KIND_TERM.get(kind, kind)}) but no line in it posts to the "
                        f"matching tax account ({expected}).",
                        file=first.source_file,
                        line=first.source_line,
                        entry_id=run.entry_id,
                        account=first.account,
                        hint="Either post the tax to its control account in the same entry, or "
                        "clear the tax_tag on this row if the line is not tax-relevant.",
                    )
                )
                continue
            value_lines = [
                p
                for p in tagged
                if not (p.account in known and _account_matches_kind(known[p.account], kind))
            ]
            if not value_lines:
                control = known[first.account]
                findings.append(
                    _finding(
                        "tax-tag-control-only",
                        f"entry_id {run.entry_id!r} carries tax_tag {str(first.tax_tag)} "
                        f"({_KIND_TERM.get(kind, kind)}) only on its tax control account "
                        f"({control.label}); no value line is tagged, so the taxable value "
                        "behind this tax would be read as ৳0.00.",
                        file=first.source_file,
                        line=first.source_line,
                        entry_id=run.entry_id,
                        account=first.account,
                        hint="Tag the sales/purchase line that the tax was charged on as well. "
                        "A pure tax deposit or adjustment should use NONE.",
                    )
                )


def _check_dates(
    postings: Sequence[tb.Posting],
    findings: list[Finding],
    window: "tuple[datetime.date, datetime.date] | None",
    window_source: str,
) -> None:
    """Backwards dates, rows in the wrong month file, dates outside the financial year."""
    previous: dict[str, tb.Posting] = {}
    for posting in postings:
        earlier = previous.get(posting.source_file)
        if earlier is not None and posting.date < earlier.date:
            findings.append(
                _finding(
                    "date-out-of-order",
                    f"Date {posting.date.isoformat()} is earlier than "
                    f"{earlier.date.isoformat()} on line {earlier.source_line} above it.",
                    file=posting.source_file,
                    line=posting.source_line,
                    entry_id=posting.entry_id,
                    account=posting.account,
                    hint="Keep each journal file in date order so the খতিয়ান / ledger reads "
                    "chronologically.",
                )
            )
        previous[posting.source_file] = posting

        name = Path(posting.source_file).name if posting.source_file else ""
        match = tb.JOURNAL_FILENAME_RE.match(name)
        if match and f"{match.group(1)}-{match.group(2)}" != posting.month:
            findings.append(
                _finding(
                    "misfiled-posting",
                    f"This row is dated {posting.date.isoformat()} but sits in {name}; it "
                    f"belongs in {posting.month}.csv.",
                    file=posting.source_file,
                    line=posting.source_line,
                    entry_id=posting.entry_id,
                    account=posting.account,
                )
            )

    if window is None:
        return
    start, end = window
    outside = [p for p in postings if not (start <= p.date <= end)]
    for posting in outside[:_MAX_FY_FINDINGS]:
        findings.append(
            _finding(
                "date-outside-financial-year",
                f"Date {posting.date.isoformat()} is outside the financial year being "
                f"validated ({start.isoformat()} → {end.isoformat()}; {window_source}).",
                file=posting.source_file,
                line=posting.source_line,
                entry_id=posting.entry_id,
                account=posting.account,
                hint="Keep one income year per books/ directory, or pass --fy-start to "
                "validate a different year.",
            )
        )
    if len(outside) > _MAX_FY_FINDINGS:
        extra = outside[_MAX_FY_FINDINGS:]
        findings.append(
            _finding(
                "date-outside-financial-year",
                f"…and {len(extra)} more row(s) dated outside {start.isoformat()} → "
                f"{end.isoformat()} ({extra[0].date.isoformat()} … "
                f"{extra[-1].date.isoformat()}).",
                file=extra[0].source_file,
                line=extra[0].source_line,
                entry_id=extra[0].entry_id,
            )
        )


def _note_month_gaps(journal_labels: Sequence[str], notes: list[str]) -> None:
    """A missing month between two journal files is worth a note — never a finding."""
    months: list[tuple[int, int, str]] = []
    for label in journal_labels:
        name = Path(label).name
        match = tb.JOURNAL_FILENAME_RE.match(name)
        if match:
            months.append((int(match.group(1)), int(match.group(2)), name))
    months.sort()
    for (y1, m1, n1), (y2, m2, n2) in zip(months, months[1:]):
        span = (y2 - y1) * 12 + (m2 - m1)
        if span > 1:
            missing = []
            y, m = y1, m1
            for _ in range(span - 1):
                m += 1
                if m > 12:
                    m, y = 1, y + 1
                missing.append(f"{y:04d}-{m:02d}")
            notes.append(
                f"No journal file for {', '.join(missing)} between {n1} and {n2} — fine if "
                "those months had no transactions, otherwise entries are missing."
            )


# ======================================================================================
# The pipeline
# ======================================================================================


def validate_books(
    books_dir: "Path | str" = tb.DEFAULT_BOOKS_DIR,
    *,
    fy_start: "datetime.date | str | None" = None,
) -> ValidationReport:
    """Validate a whole ``books/`` directory and return everything found.

    ``fy_start`` pins the financial year window explicitly (an ISO date, the day the
    year opens).  Without it the window comes from ``books.fiscal_year_start`` in
    ``config.toml``, anchored on the year that holds most postings; with neither, the
    date-range check is skipped and said so.  TakaBooks never guesses an income year.

    Raises :class:`takabooks.LedgerError` only when ``books_dir`` itself is not a
    directory; every other problem is returned as a finding.
    """
    root = Path(books_dir)
    if not root.is_dir():
        raise tb.LedgerError(
            f"Books directory not found: {root}",
            hint="Run init_books.py to create it, or pass --books <dir>.",
        )
    relative_to = root.parent
    report = ValidationReport(books_dir=root)
    findings, notes = report.findings, report.notes

    # -- config.toml -----------------------------------------------------------------
    config: tb.Config | None = None
    try:
        config = tb.Config.load(root)
    except tb.TakaBooksError as exc:
        findings.append(
            _finding(
                "config-unreadable",
                exc.message,
                file=_label(tb.config_path(root), relative_to),
                hint=exc.hint or "",
            )
        )
        notes.append(
            "Locale, financial year and business identity checks were skipped because "
            "config.toml could not be read."
        )
    report.config = config

    if config is not None and not config.assessment_year:
        findings.append(
            _finding(
                "config-assessment-year",
                f"books.assessment_year ({tb.term('assessment_year')}) is not set. Every tax "
                "output must state the year it was computed for.",
                file=_label(tb.config_path(root), relative_to),
                hint='Add assessment_year = "YYYY-YY" under [books]. TakaBooks will not '
                "assume one for you.",
            )
        )

    # -- accounts.toml ---------------------------------------------------------------
    accounts_file = config.accounts_file if config is not None else tb.ACCOUNTS_FILENAME
    chart: tb.ChartOfAccounts | None = None
    try:
        chart = tb.ChartOfAccounts.from_toml_path(root / accounts_file)
    except tb.TakaBooksError as exc:
        findings.append(
            _finding(
                "accounts-unreadable",
                exc.message,
                file=_label(root / accounts_file, relative_to),
                hint=exc.hint or "",
            )
        )
        notes.append(
            "Account-code, inactive-account and tax-account checks were skipped because "
            "the chart of accounts could not be read."
        )
    report.chart = chart

    if chart is not None:
        chart_label = _label(root / accounts_file, relative_to)
        missing = chart.missing_roles()
        if missing:
            findings.append(
                _finding(
                    "missing-required-role",
                    f"{len(missing)} mandatory Bangladesh account role(s) are not declared: "
                    f"{', '.join(missing)}.",
                    file=chart_label,
                    hint='Add role = "<role>" to the matching [[account]] table so VAT/TDS '
                    "tooling can find it (spec §4.4).",
                )
            )
        for warning in chart.code_format_warnings():
            findings.append(_finding("chart-code-format", warning + ".", file=chart_label))
        for warning in chart.block_warnings():
            findings.append(_finding("chart-block", warning + ".", file=chart_label))

    # -- journal files ---------------------------------------------------------------
    journal_dirname = config.journal_dirname if config is not None else tb.JOURNAL_DIRNAME
    jdir = tb.journal_dir(root, journal_dirname)
    postings: list[tb.Posting] = []
    runs: list[_Run] = []
    if not jdir.is_dir():
        findings.append(
            _finding(
                "journal-missing",
                f"Journal directory not found: {_label(jdir, relative_to)}",
                file=_label(jdir, relative_to),
                hint="Run init_books.py to scaffold books/, or check books.journal_dir in "
                "config.toml.",
            )
        )
    else:
        files = sorted(path for path in jdir.glob("*.csv") if path.is_file())
        report.journal_files = [_label(path, relative_to) for path in files]
        known = set(files)
        for stray in sorted(jdir.iterdir()):
            if stray.is_dir() or stray in known or stray.name.startswith("."):
                continue
            findings.append(
                _finding(
                    "journal-stray-file",
                    f"{stray.name} is in the journal directory but is not a *.csv journal "
                    "file, so nothing in it was validated.",
                    file=_label(stray, relative_to),
                    hint="Move it out of books/journal/ (a leftover .takabooks-tmp file "
                    "means an earlier write was interrupted).",
                )
            )
        if not files:
            findings.append(
                _finding(
                    "no-journal-files",
                    f"No journal files found in {_label(jdir, relative_to)} — there is "
                    "nothing to validate yet.",
                    file=_label(jdir, relative_to),
                    hint="Record entries with post.py; they land in "
                    "books/journal/YYYY-MM.csv.",
                )
            )
        for path in files:
            label = _label(path, relative_to)
            if not tb.JOURNAL_FILENAME_RE.match(path.name):
                findings.append(
                    _finding(
                        "journal-filename",
                        f"{path.name} is not named YYYY-MM.csv, so month-filing checks cannot "
                        "run on it.",
                        file=label,
                        hint="One journal file per month, e.g. 2026-07.csv.",
                    )
                )
            file_postings, rows = _read_journal_file(
                path, label=label, findings=findings, notes=notes, runs=runs
            )
            postings.extend(file_postings)
            report.rows_read += rows
        _note_month_gaps(report.journal_files, notes)

    # -- ledger-level checks ----------------------------------------------------------
    ledger = tb.Ledger(postings, chart=chart, config=config, books_dir=root)
    report.postings_checked = len(ledger.postings)
    report.entries = len(runs)
    report.total_debit = ledger.total_debits()
    report.total_credit = ledger.total_credits()
    report.first_date, report.last_date = ledger.date_range()

    window, window_source = _resolve_financial_year(
        report,
        config=config,
        fy_start=fy_start,
        dates=[p.date for p in ledger.postings],
        notes=notes,
        findings=findings,
        relative_to=relative_to,
    )
    report.financial_year = window
    report.financial_year_source = window_source

    _check_accounts(ledger.postings, chart, findings)
    duplicated = _check_duplicate_entry_ids(runs, findings)
    _check_entries(runs, findings, notes, config, duplicated=duplicated)
    _check_tax_tags(runs, chart, findings)
    _check_dates(ledger.postings, findings, window, window_source)
    return report


def _resolve_financial_year(
    report: ValidationReport,
    *,
    config: "tb.Config | None",
    fy_start: "datetime.date | str | None",
    dates: Sequence[datetime.date],
    notes: list[str],
    findings: list[Finding],
    relative_to: "Path | None",
) -> tuple["tuple[datetime.date, datetime.date] | None", str]:
    """Work out which financial year to check dates against — never by guessing."""
    if fy_start is not None:
        anchor = fy_start if isinstance(fy_start, datetime.date) else tb.parse_date(str(fy_start))
        end = _safe_date(anchor.year + 1, anchor.month, anchor.day) - datetime.timedelta(days=1)
        return (anchor, end), "from --fy-start"

    if config is None or not config.fiscal_year_start:
        if config is not None:
            findings.append(
                _finding(
                    "config-fiscal-year",
                    "books.fiscal_year_start is not set, so rows cannot be checked against a "
                    "financial year.",
                    file=_label(tb.config_path(report.books_dir), relative_to),
                    hint='Add fiscal_year_start = "MM-DD" under [books] (the day your income '
                    "year opens). TakaBooks does not assume one.",
                )
            )
        notes.append(
            "The financial-year date check was skipped: no books.fiscal_year_start and no "
            "--fy-start."
        )
        return None, ""

    if not dates:
        notes.append("The financial-year date check was skipped: no postings were readable.")
        return None, ""

    month_text, _, day_text = config.fiscal_year_start.partition("-")
    try:
        month, day = int(month_text), int(day_text)
        window, inside, total = majority_fiscal_year(dates, month, day)
    except ValueError:  # pragma: no cover - Config already validates the MM-DD shape
        notes.append(
            f"The financial-year date check was skipped: fiscal_year_start "
            f"{config.fiscal_year_start!r} could not be read as MM-DD."
        )
        return None, ""
    share = f"all {total}" if inside == total else f"{inside} of {total}"
    return window, (
        f"config fiscal_year_start = {config.fiscal_year_start}; the year holding "
        f"{share} posting(s)"
    )


# ======================================================================================
# Rendering
# ======================================================================================

_RULE = "=" * 78
_THIN = "-" * 78


def render_checks() -> str:
    """The catalogue printed by ``--list-checks``."""
    rows = [(check.slug, check.severity, check.summary) for check in CHECKS]
    width = max(len(slug) for slug, _, _ in rows)
    lines = [
        f"{tb.PROJECT_NAME} {PROG} — checks performed (খতিয়ান যাচাই / ledger validation)",
        _THIN,
    ]
    for severity in SEVERITIES:
        lines.append(f"{severity.upper()}S")
        for slug, sev, summary in rows:
            if sev == severity:
                lines.append(f"  {slug.ljust(width)}  {summary}")
        lines.append("")
    lines.append(
        "An account counts as inactive when accounts.toml tags it "
        + ", ".join(repr(tag) for tag in INACTIVE_TAGS)
        + "."
    )
    lines.append(tb.ATTRIBUTION)
    return "\n".join(lines)


def _meta_rows(report: ValidationReport) -> list[tuple[str, str]]:
    config = report.config
    rows: list[tuple[str, str]] = [("Books directory", str(report.books_dir))]
    if config is not None:
        rows.append(("Business", config.display_name))
        identity = " · ".join(
            part
            for part in (
                f"BIN {config.bin}" if config.bin else "",
                f"TIN {config.tin}" if config.tin else "",
            )
            if part
        )
        if identity:
            rows.append(("Identifiers", identity))
        rows.append(
            (
                tb.term("assessment_year").capitalize(),
                config.assessment_year or "(not set in config.toml)",
            )
        )
    if report.financial_year is not None:
        start, end = report.financial_year
        rows.append(
            (
                "Financial year",
                f"{start.isoformat()} → {end.isoformat()} ({report.financial_year_source})",
            )
        )
    else:
        rows.append(("Financial year", "not checked (no fiscal_year_start, no --fy-start)"))
    rows.append(
        (
            "Journal files",
            f"{len(report.journal_files)}"
            + (f" — {', '.join(Path(f).name for f in report.journal_files)}" if report.journal_files else ""),
        )
    )
    rows.append(
        (
            "Rows",
            f"{report.rows_read} data row(s) read · {report.postings_checked} posting(s) "
            f"checked · {report.entries} entry/entries",
        )
    )
    if report.first_date and report.last_date:
        rows.append(("Date range", f"{report.first_date.isoformat()} → {report.last_date.isoformat()}"))
    rows.append(("Total debits", _money(report.total_debit, report.config)))
    rows.append(("Total credits", _money(report.total_credit, report.config)))
    rows.append(("Difference", _money(report.difference, report.config)))
    return rows


def render_text(
    report: ValidationReport, *, quiet: bool = False, allow_warnings: bool = False
) -> str:
    """The human report: header, findings grouped by severity, notes, result, disclaimer."""
    if quiet:
        return report.summary_line(allow_warnings=allow_warnings)

    config = report.config
    lines: list[str] = [
        f"{tb.PROJECT_NAME} — খতিয়ান যাচাই / ledger validation",
        tb.ATTRIBUTION,
        _RULE,
    ]
    rows = _meta_rows(report)
    width = max(len(key) for key, _ in rows)
    lines.extend(f"{key.ljust(width)} : {value}" for key, value in rows)

    grouped: dict[str, list[Finding]] = {severity: [] for severity in SEVERITIES}
    for finding in report.sorted_findings():
        grouped[finding.severity].append(finding)

    headings = {
        SEVERITY_ERROR: "ERRORS — fix these; the books cannot be trusted until you do",
        SEVERITY_WARNING: "WARNINGS — review these; they are usually a typo or a missing declaration",
    }
    for severity in SEVERITIES:
        items = grouped[severity]
        if not items:
            continue
        lines.extend(["", _THIN, f"{headings[severity]} ({len(items)})", _THIN])
        for number, finding in enumerate(items, start=1):
            block = finding.render().splitlines()
            lines.append(f"{number:>3}. {block[0]}")
            lines.extend(f"     {line.strip()}" for line in block[1:])

    if report.notes:
        lines.extend(["", _THIN, "NOTES", _THIN])
        lines.extend(f"  - {note}" for note in report.notes)

    lines.extend(["", _RULE, report.summary_line(allow_warnings=allow_warnings), ""])
    lines.append(tb.DISCLAIMER_EN)
    if config is not None and config.language in ("bn", "bn-en"):
        lines.append(tb.DISCLAIMER_BN)
    return "\n".join(lines)


def render_json(report: ValidationReport, *, allow_warnings: bool = False) -> str:
    """The ``--json`` payload — the same findings, machine-readable."""
    return tb.json_dumps(report.to_dict(allow_warnings=allow_warnings))


# ======================================================================================
# CLI
# ======================================================================================

_EPILOG = f"""severity:
  error    the books cannot be trusted until this is fixed
  warning  almost always a typo or a missing declaration — review before you file

exit codes:
  0  clean (or only warnings remain and --allow-warnings was given)
  {FINDINGS_EXIT_CODE}  findings were reported
  {tb.ConfigError.exit_code}  a config problem (e.g. --fy-start is not an ISO date)
  {tb.LedgerError.exit_code}  the books directory could not be read

{tb.ATTRIBUTION}"""


def build_parser() -> argparse.ArgumentParser:
    """The ``validate.py`` argument parser (``--help`` / ``--books`` / ``--json`` + extras)."""
    parser = tb.common_parser(
        PROG,
        "Check a whole TakaBooks ledger (খতিয়ান) for integrity problems: balance, unknown "
        "accounts, duplicate entry ids, dates, tax tags. Reports every problem it can find "
        "at once and exits non-zero unless the books are clean.",
        epilog=_EPILOG,
    )
    parser.add_argument(
        "--allow-warnings",
        action="store_true",
        help="exit 0 when only warnings remain (errors still fail)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="print only the one-line result (text output only)",
    )
    parser.add_argument(
        "--fy-start",
        metavar="YYYY-MM-DD",
        default=None,
        help="pin the financial year to check dates against (default: from "
        "books.fiscal_year_start in config.toml)",
    )
    parser.add_argument(
        "--list-checks",
        action="store_true",
        help="list every check this script performs, then exit",
    )
    return parser


def main(argv: "Sequence[str] | None" = None, *, stdout: Any = None, stderr: Any = None) -> int:
    """Run the validator.  Returns the process exit code."""
    out = stdout if stdout is not None else sys.stdout
    args = build_parser().parse_args(argv)

    if args.list_checks:
        out.write(render_checks() + "\n")
        return 0

    with tb.cli_guard(json_output=args.json, stream=stderr):
        fy_start = None
        if args.fy_start:
            try:
                fy_start = tb.parse_date(args.fy_start, field_name="--fy-start")
            except tb.JournalError as exc:
                raise tb.ConfigError(exc.message, hint=exc.hint) from None
        report = validate_books(args.books, fy_start=fy_start)
        text = (
            render_json(report, allow_warnings=args.allow_warnings)
            if args.json
            else render_text(report, quiet=args.quiet, allow_warnings=args.allow_warnings)
        )
        out.write(text + "\n")
        return report.exit_code(allow_warnings=args.allow_warnings)
    return 1  # pragma: no cover - cli_guard either yields or raises SystemExit


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    tb.check_python_or_exit()
    raise SystemExit(main())
