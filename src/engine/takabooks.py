"""TakaBooks shared library — বাংলাদেশ / Bangladesh bookkeeping & taxation engine.

This module is the single shared foundation every other TakaBooks engine script
imports (``init_books.py``, ``post.py``, ``report.py``, ``vat.py``, ``tax.py``,
``validate.py``).  It owns:

* :class:`Money`          — integer paisa arithmetic, never ``float``.
* :func:`format_bdt`      — লাখ/কোটি (lakh/crore) grouping ``12,34,567.89`` (default)
                            and international grouping ``1,234,567.89``.
* :class:`Account` / :class:`ChartOfAccounts` — ``accounts.toml`` loader + validation.
* :class:`TaxTag`         — the ``tax_tag`` grammar from spec §4.3.
* :class:`Posting` / :class:`Entry` / :class:`Ledger` — journal CSV IO and the
                            double-entry invariant (debits == credits, in paisa).
* :class:`Config`         — ``books/config.toml`` loader.
* :class:`RatesTable`     — structural reader for ``rates-AY<year>.toml``.
* A :class:`TakaBooksError` hierarchy with stable process exit codes.

Hard rules encoded here (see the design spec, sections 4.1–4.4):

1. Standard library only.  Floor is Python 3.11 (``tomllib``).
2. Money is ``int`` paisa internally.  Text is parsed with :class:`decimal.Decimal`.
   ``float`` is rejected loudly wherever money is involved.
3. Rounding is ``ROUND_HALF_UP``, applied once, at the final step.
4. **No tax rate, threshold, deadline or statute number is defined in this file.**
   Rates live in ``src/data/rates-AY*.toml`` and are read through
   :class:`RatesTable`, which surfaces ``verified = false`` to the caller.

TakaBooks — maintained by Moshiur Rahman (@bemoshiur) · TICON SYSTEM LTD
https://ticonsys.com · https://github.com/bemoshiur/TakaBooks · MIT licensed.
"""

from __future__ import annotations

import sys

# --------------------------------------------------------------------------------------
# Python version guard.  This must run before `tomllib` is imported, otherwise a user on
# Python 3.10 gets an opaque ImportError instead of a friendly sentence.
# --------------------------------------------------------------------------------------

MIN_PYTHON: tuple[int, int] = (3, 11)

_VERSION_MESSAGE = (
    "TakaBooks needs Python {needed} or newer (tomllib lives in the standard library "
    "from 3.11).  You are running Python {found} from {executable}.\n"
    "Install a newer Python from https://www.python.org/downloads/ and re-run with, "
    "for example, `python3.11 -m ...`."
)


def python_version_message(
    min_version: tuple[int, int] = MIN_PYTHON,
    found: tuple[int, ...] | None = None,
) -> str:
    """Return the friendly 'your Python is too old' sentence."""
    found = tuple(sys.version_info[:3]) if found is None else tuple(found)
    return _VERSION_MESSAGE.format(
        needed=".".join(str(part) for part in min_version),
        found=".".join(str(part) for part in found),
        executable=sys.executable or "python",
    )


if sys.version_info < MIN_PYTHON:  # pragma: no cover - cannot run on a new interpreter
    sys.stderr.write(python_version_message() + "\n")
    raise SystemExit(2)

import argparse  # noqa: E402
import contextlib  # noqa: E402
import csv  # noqa: E402
import dataclasses  # noqa: E402
import datetime  # noqa: E402
import decimal  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import tomllib  # noqa: E402
from collections.abc import Iterable, Iterator, Mapping, Sequence  # noqa: E402
from dataclasses import dataclass, field  # noqa: E402
from decimal import Decimal  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402

__all__ = [
    # metadata
    "__version__",
    "PROJECT_NAME",
    "PROJECT_URL",
    "MAINTAINER",
    "COMPANY",
    "COMPANY_URL",
    "ATTRIBUTION",
    "DISCLAIMER_EN",
    "DISCLAIMER_BN",
    "TERMS",
    "term",
    # version guard
    "MIN_PYTHON",
    "python_version_message",
    "require_python",
    "check_python_or_exit",
    # exceptions
    "TakaBooksError",
    "PythonVersionError",
    "ConfigError",
    "MoneyError",
    "AccountError",
    "DuplicateAccountError",
    "UnknownAccountError",
    "JournalError",
    "TaxTagError",
    "DuplicateEntryError",
    "BalanceError",
    "LedgerError",
    "RatesError",
    "ValidationError",
    # money
    "PAISA_PER_TAKA",
    "CURRENCY_CODE",
    "CURRENCY_SYMBOL",
    "ROUND_HALF_UP",
    "Money",
    "money_sum",
    "parse_bdt",
    # formatting
    "GROUPING_BD",
    "GROUPING_INTL",
    "BANGLA_DIGITS",
    "format_bdt",
    "format_bdt_international",
    "to_bangla_digits",
    "to_latin_digits",
    "markdown_table",
    # accounts
    "ACCOUNT_TYPES",
    "NORMAL_BALANCE",
    "BALANCE_SHEET_TYPES",
    "INCOME_STATEMENT_TYPES",
    "AccountBlock",
    "ACCOUNT_BLOCKS",
    "block_for_code",
    "Account",
    "ChartOfAccounts",
    "ROLE_VAT_INPUT",
    "ROLE_VAT_OUTPUT",
    "ROLE_TDS_RECEIVABLE",
    "ROLE_TDS_PAYABLE",
    "ROLE_VDS_PAYABLE",
    "ROLE_ADVANCE_INCOME_TAX",
    "ROLE_PROVIDENT_FUND_PAYABLE",
    "ROLE_GRATUITY_PROVISION",
    "ROLE_WPPF_PAYABLE",
    "ROLE_SUPPLEMENTARY_DUTY_PAYABLE",
    "REQUIRED_ROLES",
    # tax tags
    "TAG_NONE",
    "TAG_VAT_OUT",
    "TAG_VAT_IN",
    "TAG_TDS",
    "TAG_VDS",
    "TAX_TAG_KINDS",
    "TAX_TAG_GRAMMAR",
    "TaxTag",
    # journal
    "JOURNAL_COLUMNS",
    "JOURNAL_HEADER",
    "JOURNAL_FILENAME_RE",
    "Posting",
    "Entry",
    "group_postings",
    "parse_date",
    "parse_amount_field",
    "format_amount_for_csv",
    "read_journal_csv",
    "read_journal_dir",
    "write_journal_csv",
    "append_journal_csv",
    "journal_files",
    # ledger
    "AccountTotal",
    "Ledger",
    # config / paths
    "DEFAULT_BOOKS_DIR",
    "CONFIG_FILENAME",
    "ACCOUNTS_FILENAME",
    "JOURNAL_DIRNAME",
    "config_path",
    "accounts_path",
    "journal_dir",
    "journal_path_for",
    "Config",
    "load_toml",
    # rates
    "Rate",
    "RatesTable",
    # cli helpers
    "common_parser",
    "cli_guard",
    "to_jsonable",
    "json_dumps",
    "ensure_dir",
    "write_text_atomic",
]

# --------------------------------------------------------------------------------------
# Project metadata and attribution (spec §9)
# --------------------------------------------------------------------------------------

__version__ = "1.1.1"

PROJECT_NAME = "TakaBooks"
PROJECT_URL = "https://github.com/bemoshiur/TakaBooks"
MAINTAINER = "Moshiur Rahman (@bemoshiur)"
COMPANY = "TICON SYSTEM LTD"
COMPANY_URL = "https://ticonsys.com"
ATTRIBUTION = f"{PROJECT_NAME} — {MAINTAINER} · {COMPANY} ({COMPANY_URL})"

DISCLAIMER_EN = (
    "This output is generated by TakaBooks and is not professional advice. "
    "Verify every figure with a licensed Income Tax Practitioner (ITP) or Chartered "
    "Accountant, and against the National Board of Revenue (NBR), before you file."
)
DISCLAIMER_BN = (
    "এই ফলাফল TakaBooks দ্বারা তৈরি; এটি পেশাদার পরামর্শ নয়। দাখিলের আগে অনুগ্রহ করে "
    "লাইসেন্সপ্রাপ্ত আয়কর আইনজীবী (ITP) বা চার্টার্ড অ্যাকাউন্ট্যান্টের মাধ্যমে এবং জাতীয় "
    "রাজস্ব বোর্ড (NBR)-এর সঙ্গে প্রতিটি সংখ্যা যাচাই করে নিন।"
)

#: Statutory / accounting terms as (Bangla, English) pairs — content rule §6.4.
TERMS: dict[str, tuple[str, str]] = {
    "vat": ("মূসক", "VAT"),
    "tds": ("উৎসে কর কর্তন", "TDS"),
    "vds": ("উৎসে মূসক কর্তন", "VDS"),
    "income_tax": ("আয়কর", "income tax"),
    "ledger": ("খতিয়ান", "ledger"),
    "journal": ("জাবেদা", "journal"),
    "trial_balance": ("রেওয়ামিল", "trial balance"),
    "balance_sheet": ("স্থিতিপত্র", "balance sheet"),
    "profit_and_loss": ("লাভ-ক্ষতি হিসাব", "profit and loss"),
    "chart_of_accounts": ("হিসাব তালিকা", "chart of accounts"),
    "debit": ("ডেবিট", "debit"),
    "credit": ("ক্রেডিট", "credit"),
    "asset": ("সম্পদ", "asset"),
    "liability": ("দায়", "liability"),
    "equity": ("মূলধন", "equity"),
    "income": ("আয়", "income"),
    "expense": ("ব্যয়", "expense"),
    "assessment_year": ("করবর্ষ", "assessment year"),
    "taxpayer": ("করদাতা", "taxpayer"),
}


def term(key: str, *, order: str = "bn-en", sep: str = " / ") -> str:
    """Return a Bangla / English statutory term pair, e.g. ``"মূসক / VAT"``.

    ``order`` is ``"bn-en"`` (default) or ``"en-bn"``.  Unknown keys raise
    :class:`KeyError` — this is a programming error, not user input.
    """
    bn, en = TERMS[key]
    if order == "en-bn":
        return f"{en}{sep}{bn}"
    if order != "bn-en":
        raise ValueError(f"order must be 'bn-en' or 'en-bn', got {order!r}")
    return f"{bn}{sep}{en}"


# --------------------------------------------------------------------------------------
# Exceptions — every one carries a process exit code so CLIs can fail loudly (spec §2).
# --------------------------------------------------------------------------------------


class TakaBooksError(Exception):
    """Base class for every TakaBooks failure.  ``exit_code`` is 1."""

    exit_code = 1

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message if not self.hint else f"{self.message}\n  hint: {self.hint}"


class PythonVersionError(TakaBooksError):
    """The running interpreter is older than :data:`MIN_PYTHON`."""

    exit_code = 2


class ConfigError(TakaBooksError):
    """``books/config.toml`` is missing, unreadable or malformed."""

    exit_code = 2


class MoneyError(TakaBooksError):
    """An amount could not be parsed, or a ``float`` was offered where money was due."""

    exit_code = 9


class AccountError(TakaBooksError):
    """The chart of accounts is invalid."""

    exit_code = 3


class DuplicateAccountError(AccountError):
    """Two accounts share a code."""

    exit_code = 3


class UnknownAccountError(AccountError):
    """A posting references an account code that is not in ``accounts.toml``."""

    exit_code = 3

    def __init__(self, message: str, *, code: str = "", hint: str | None = None) -> None:
        super().__init__(message, hint=hint)
        self.code = code


class JournalError(TakaBooksError):
    """A journal CSV row or file is malformed."""

    exit_code = 4


class TaxTagError(JournalError):
    """A ``tax_tag`` value does not match the grammar in spec §4.3."""

    exit_code = 6


class DuplicateEntryError(JournalError):
    """An ``entry_id`` was reused where it must be unique."""

    exit_code = 4

    def __init__(self, message: str, *, entry_id: str = "", hint: str | None = None) -> None:
        super().__init__(message, hint=hint)
        self.entry_id = entry_id


class BalanceError(JournalError):
    """Debits do not equal credits.  Never silently corrected (spec §2)."""

    exit_code = 5

    def __init__(
        self,
        message: str,
        *,
        entry_id: str = "",
        difference: "Money | None" = None,
        total_debit: "Money | None" = None,
        total_credit: "Money | None" = None,
        entry_ids: Sequence[str] = (),
        hint: str | None = None,
    ) -> None:
        super().__init__(message, hint=hint)
        self.entry_id = entry_id
        self.difference = difference
        self.total_debit = total_debit
        self.total_credit = total_credit
        self.entry_ids = tuple(entry_ids) or ((entry_id,) if entry_id else ())


class LedgerError(TakaBooksError):
    """The books directory is missing or structurally wrong."""

    exit_code = 4


class RatesError(TakaBooksError):
    """A rates TOML file is missing, malformed, or lacks a requested key."""

    exit_code = 8


class ValidationError(TakaBooksError):
    """A whole-ledger integrity check failed (used by ``validate.py``)."""

    exit_code = 7

    def __init__(self, message: str, *, problems: Sequence[str] = (), hint: str | None = None) -> None:
        super().__init__(message, hint=hint)
        self.problems = tuple(problems)


def require_python(min_version: tuple[int, int] = MIN_PYTHON) -> None:
    """Raise :class:`PythonVersionError` if the interpreter is too old."""
    if tuple(sys.version_info[:2]) < tuple(min_version[:2]):
        raise PythonVersionError(python_version_message(min_version))


def check_python_or_exit(min_version: tuple[int, int] = MIN_PYTHON) -> None:
    """Print the friendly message and ``SystemExit(2)`` if the interpreter is too old."""
    try:
        require_python(min_version)
    except PythonVersionError as exc:  # pragma: no cover - see module-level guard
        sys.stderr.write(str(exc) + "\n")
        raise SystemExit(PythonVersionError.exit_code) from exc


# --------------------------------------------------------------------------------------
# Money — integer paisa (spec §4.2)
# --------------------------------------------------------------------------------------

PAISA_PER_TAKA = 100
CURRENCY_CODE = "BDT"
CURRENCY_SYMBOL = "৳"  # U+09F3 BENGALI RUPEE SIGN
ROUND_HALF_UP = decimal.ROUND_HALF_UP

#: Working precision for intermediate Decimal work.  Wide enough that no realistic
#: ledger loses a digit before the single final ROUND_HALF_UP.
_CALC_PRECISION = 60

BANGLA_DIGITS = "০১২৩৪৫৬৭৮৯"
_TO_BANGLA = str.maketrans("0123456789", BANGLA_DIGITS)
_TO_LATIN = str.maketrans(BANGLA_DIGITS, "0123456789")

_DECIMAL_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
_CURRENCY_NOISE_RE = re.compile(r"(?i)(?:BDT|TAKA|TK\.?|৳)")


def to_bangla_digits(text: str) -> str:
    """Convert Latin digits in ``text`` to Bangla digits (০-৯)."""
    return text.translate(_TO_BANGLA)


def to_latin_digits(text: str) -> str:
    """Convert Bangla digits (০-৯) in ``text`` to Latin digits."""
    return text.translate(_TO_LATIN)


def _reject_float(value: Any, *, what: str) -> None:
    if isinstance(value, float):
        raise MoneyError(
            f"{what} was given as a float ({value!r}). Money must never touch float — "
            "binary floating point cannot represent 0.10 exactly.",
            hint="Pass a str like '1234.56', a decimal.Decimal, or an int number of taka.",
        )


def _clean_amount_text(text: str, *, what: str) -> str:
    """Strip currency noise, grouping commas and Bangla digits from an amount string."""
    raw = text
    cleaned = to_latin_digits(text).strip()
    cleaned = cleaned.replace("\u00a0", "").replace("\u202f", "").replace("\u2009", "")
    cleaned = _CURRENCY_NOISE_RE.sub("", cleaned)
    cleaned = cleaned.replace(",", "").replace("_", "")
    cleaned = "".join(cleaned.split())
    negative = False
    if cleaned.startswith("(") and cleaned.endswith(")"):
        negative = True
        cleaned = cleaned[1:-1].strip()
    if not cleaned:
        raise MoneyError(f"{what} is empty (got {raw!r}); expected a BDT amount such as '1234.56'.")
    if not _DECIMAL_RE.match(cleaned):
        raise MoneyError(
            f"{what} {raw!r} is not a valid BDT amount.",
            hint="Use plain decimal digits, e.g. 1234.56, -1234.56, 12,34,567.89 or (500.00).",
        )
    if negative:
        cleaned = cleaned.lstrip("+")
        cleaned = cleaned[1:] if cleaned.startswith("-") else "-" + cleaned
    return cleaned


def _to_decimal(value: "Decimal | int | str", *, what: str = "amount") -> Decimal:
    """Coerce to :class:`Decimal`.  ``float`` is rejected."""
    _reject_float(value, what=what)
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):  # bool is an int subclass; almost certainly a bug
        raise MoneyError(f"{what} was given as a bool ({value!r}).")
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str):
        cleaned = _clean_amount_text(value, what=what)
        try:
            return Decimal(cleaned)
        except decimal.InvalidOperation as exc:  # pragma: no cover - regex guards this
            raise MoneyError(f"{what} {value!r} is not a valid BDT amount.") from exc
    raise MoneyError(f"{what} must be Money, Decimal, int or str; got {type(value).__name__}.")


def _decimal_to_paisa(value: Decimal, *, exact: bool, what: str) -> int:
    with decimal.localcontext() as ctx:
        ctx.prec = _CALC_PRECISION
        scaled = value * PAISA_PER_TAKA
        integral = scaled.to_integral_value(rounding=ROUND_HALF_UP)
    if exact and scaled != integral:
        raise MoneyError(
            f"{what} {value} has sub-paisa precision and would be rounded.",
            hint="Pass exact=False to round ROUND_HALF_UP, or supply at most 2 decimal places.",
        )
    return int(integral)


@dataclass(frozen=True, order=True)
class Money:
    """An exact BDT amount held as ``int`` paisa.  1 BDT = 100 paisa.

    Construct with :meth:`from_str`, :meth:`from_decimal`, :meth:`from_taka` or
    :meth:`from_paisa`.  ``Money(123456)`` also works and means *paisa*.
    Arithmetic that could silently lose precision is refused; rounding happens
    once, explicitly, via :meth:`mul_rate`, :meth:`percent`, :meth:`divide`,
    :meth:`allocate` or :meth:`split`.
    """

    paisa: int

    def __post_init__(self) -> None:
        _reject_float(self.paisa, what="Money.paisa")
        if isinstance(self.paisa, bool) or not isinstance(self.paisa, int):
            raise MoneyError(
                f"Money.paisa must be an int number of paisa; got {type(self.paisa).__name__}.",
                hint="Use Money.from_str('12.34') or Money.from_taka(12) for taka amounts.",
            )

    # -- constructors ------------------------------------------------------------------

    @classmethod
    def zero(cls) -> "Money":
        """৳0.00."""
        return cls(0)

    @classmethod
    def from_paisa(cls, paisa: int) -> "Money":
        """Build from an integer number of paisa."""
        return cls(paisa)

    @classmethod
    def from_decimal(cls, value: Decimal, *, exact: bool = False, what: str = "amount") -> "Money":
        """Build from a :class:`Decimal` number of **taka**."""
        dec = _to_decimal(value, what=what)
        return cls(_decimal_to_paisa(dec, exact=exact, what=what))

    @classmethod
    def from_str(cls, text: str, *, exact: bool = False, what: str = "amount") -> "Money":
        """Parse a human BDT string: ``'1234.56'``, ``'12,34,567.89'``, ``'৳ 1,000'``,
        ``'(500.00)'`` (negative), Bangla digits ``'১২৩৪.৫৬'``.

        Values finer than one paisa are rounded ``ROUND_HALF_UP`` unless
        ``exact=True``, which raises :class:`MoneyError` instead.
        """
        if not isinstance(text, str):
            raise MoneyError(f"{what} must be a str; got {type(text).__name__}.")
        dec = _to_decimal(text, what=what)
        return cls(_decimal_to_paisa(dec, exact=exact, what=what))

    @classmethod
    def from_taka(
        cls, value: "Decimal | int | str", *, exact: bool = False, what: str = "amount"
    ) -> "Money":
        """Build from a taka amount given as :class:`Decimal`, ``int`` or ``str``."""
        dec = _to_decimal(value, what=what)
        return cls(_decimal_to_paisa(dec, exact=exact, what=what))

    @classmethod
    def sum(cls, amounts: Iterable["Money"]) -> "Money":
        """Exact sum of an iterable of :class:`Money`."""
        total = 0
        for amount in amounts:
            if not isinstance(amount, Money):
                raise MoneyError(f"Money.sum expects Money values; got {type(amount).__name__}.")
            total += amount.paisa
        return cls(total)

    # -- conversion --------------------------------------------------------------------

    def to_decimal(self) -> Decimal:
        """Exact taka value as a 2-place :class:`Decimal`."""
        return (Decimal(self.paisa) / PAISA_PER_TAKA).quantize(Decimal("0.01"))

    @property
    def taka(self) -> Decimal:
        """Alias of :meth:`to_decimal`."""
        return self.to_decimal()

    @property
    def bdt(self) -> str:
        """User-facing Bangladeshi-grouped string with the ৳ symbol."""
        return format_bdt(self, symbol=True)

    def format(self, **kwargs: Any) -> str:
        """Shorthand for :func:`format_bdt` (``money.format(symbol=True)``)."""
        return format_bdt(self, **kwargs)

    # -- predicates --------------------------------------------------------------------

    def is_zero(self) -> bool:
        return self.paisa == 0

    def is_positive(self) -> bool:
        return self.paisa > 0

    def is_negative(self) -> bool:
        return self.paisa < 0

    def __bool__(self) -> bool:
        return self.paisa != 0

    # -- arithmetic --------------------------------------------------------------------

    def __add__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.paisa + other.paisa)

    def __sub__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.paisa - other.paisa)

    def __neg__(self) -> "Money":
        return Money(-self.paisa)

    def __pos__(self) -> "Money":
        return self

    def __abs__(self) -> "Money":
        return Money(abs(self.paisa))

    def __mul__(self, factor: int) -> "Money":
        """Exact multiplication by a whole number.  Rates must use :meth:`mul_rate`."""
        if isinstance(factor, bool) or not isinstance(factor, int):
            raise MoneyError(
                f"Money * x is only defined for whole numbers; got "
                f"{type(factor).__name__} {factor!r}.",
                hint="For a rate or fraction use money.mul_rate(Decimal('0.15')) or "
                "money.percent(Decimal('15')), which rounds ROUND_HALF_UP exactly once. "
                "Money never multiplies by a float.",
            )
        return Money(self.paisa * factor)

    __rmul__ = __mul__

    def mul_rate(
        self,
        rate: "Decimal | int | str",
        *,
        rounding: str = ROUND_HALF_UP,
    ) -> "Money":
        """Multiply by a **fraction** (``Decimal('0.15')`` for 15%), rounding once."""
        factor = _to_decimal(rate, what="rate")
        with decimal.localcontext() as ctx:
            ctx.prec = _CALC_PRECISION
            product = Decimal(self.paisa) * factor
            return Money(int(product.to_integral_value(rounding=rounding)))

    def percent(
        self,
        pct: "Decimal | int | str",
        *,
        rounding: str = ROUND_HALF_UP,
    ) -> "Money":
        """Multiply by a **percentage** (``15`` for 15%), rounding once."""
        value = _to_decimal(pct, what="percentage")
        with decimal.localcontext() as ctx:
            ctx.prec = _CALC_PRECISION
            product = Decimal(self.paisa) * value / Decimal(100)
            return Money(int(product.to_integral_value(rounding=rounding)))

    def divide(self, divisor: "Decimal | int | str", *, rounding: str = ROUND_HALF_UP) -> "Money":
        """Divide, rounding once.  Use :meth:`split` when the total must be preserved."""
        value = _to_decimal(divisor, what="divisor")
        if value == 0:
            raise MoneyError("Cannot divide money by zero.")
        with decimal.localcontext() as ctx:
            ctx.prec = _CALC_PRECISION
            quotient = Decimal(self.paisa) / value
            return Money(int(quotient.to_integral_value(rounding=rounding)))

    def ratio_to(self, other: "Money") -> Decimal:
        """Exact ratio of two amounts as a :class:`Decimal` (no rounding to paisa)."""
        if not isinstance(other, Money):
            raise MoneyError("ratio_to expects Money.")
        if other.paisa == 0:
            raise MoneyError("Cannot take a ratio to ৳0.00.")
        with decimal.localcontext() as ctx:
            ctx.prec = _CALC_PRECISION
            return Decimal(self.paisa) / Decimal(other.paisa)

    def allocate(self, weights: Sequence[int]) -> list["Money"]:
        """Split by integer weights so the parts sum **exactly** back to this amount.

        Largest-remainder distribution; ties go to the earlier weight.
        """
        if not weights:
            raise MoneyError("allocate() needs at least one weight.")
        for weight in weights:
            _reject_float(weight, what="allocation weight")
            if isinstance(weight, bool) or not isinstance(weight, int) or weight < 0:
                raise MoneyError(f"Allocation weights must be non-negative ints; got {weight!r}.")
        total_weight = sum(weights)
        if total_weight == 0:
            raise MoneyError("Allocation weights sum to zero; cannot allocate.")
        sign = -1 if self.paisa < 0 else 1
        magnitude = abs(self.paisa)
        shares: list[int] = []
        remainders: list[tuple[int, int]] = []
        for index, weight in enumerate(weights):
            quotient, remainder = divmod(magnitude * weight, total_weight)
            shares.append(quotient)
            remainders.append((remainder, -index))
        leftover = magnitude - sum(shares)
        for _, negative_index in sorted(remainders, reverse=True)[:leftover]:
            shares[-negative_index] += 1
        return [Money(sign * share) for share in shares]

    def split(self, parts: int) -> list["Money"]:
        """Split into ``parts`` near-equal amounts that sum exactly back."""
        if isinstance(parts, bool) or not isinstance(parts, int) or parts < 1:
            raise MoneyError(f"split() needs a positive whole number of parts; got {parts!r}.")
        return self.allocate([1] * parts)

    # -- text --------------------------------------------------------------------------

    def __str__(self) -> str:
        """Plain, ungrouped decimal taka — safe to write into a CSV cell."""
        return format_amount_for_csv(self)

    def __repr__(self) -> str:
        return f"Money(paisa={self.paisa})"


def money_sum(amounts: Iterable[Money]) -> Money:
    """Module-level alias of :meth:`Money.sum`."""
    return Money.sum(amounts)


def parse_bdt(text: str, *, exact: bool = False) -> Money:
    """Module-level alias of :meth:`Money.from_str`."""
    return Money.from_str(text, exact=exact)


# --------------------------------------------------------------------------------------
# Bangladeshi (lakh / crore) and international number formatting (spec §4.2)
# --------------------------------------------------------------------------------------

GROUPING_BD = "bd"
GROUPING_INTL = "international"

_GROUPING_ALIASES = {
    "bd": GROUPING_BD,
    "bn": GROUPING_BD,
    "bangladeshi": GROUPING_BD,
    "bangladesh": GROUPING_BD,
    "lakh": GROUPING_BD,
    "indian": GROUPING_BD,
    "international": GROUPING_INTL,
    "intl": GROUPING_INTL,
    "western": GROUPING_INTL,
    "us": GROUPING_INTL,
}


def _group_international(digits: str) -> str:
    parts: list[str] = []
    while len(digits) > 3:
        parts.insert(0, digits[-3:])
        digits = digits[:-3]
    parts.insert(0, digits)
    return ",".join(parts)


def _group_bd(digits: str) -> str:
    """Lakh/crore grouping: last three digits, then pairs — ``12,34,567``."""
    if len(digits) <= 3:
        return digits
    head, tail = digits[:-3], digits[-3:]
    parts: list[str] = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    parts.append(tail)
    return ",".join(parts)


def format_bdt(
    value: "Money | Decimal | int | str",
    *,
    grouping: str = GROUPING_BD,
    symbol: bool = False,
    symbol_sep: str = "",
    decimals: int = 2,
    bangla_digits: bool = False,
    parens_negative: bool = False,
) -> str:
    """Format a BDT amount.

    Default grouping is **Bangladeshi lakh/crore** — ``12,34,567.89`` — because that
    is what a Bangladeshi user reads.  Pass ``grouping="international"`` for
    ``1,234,567.89``.

    ``value`` may be :class:`Money`, or a taka amount as :class:`Decimal`/``int``/``str``.
    ``float`` is always refused.

    Examples::

        format_bdt(Money.from_str("1234567.89"))                  -> '12,34,567.89'
        format_bdt(Money.from_str("1234567.89"), grouping="intl") -> '1,234,567.89'
        format_bdt(Money.from_str("100000"))                      -> '1,00,000.00'
        format_bdt(Money.from_str("-500"), symbol=True)           -> '-৳500.00'
        format_bdt(Money.zero(), symbol=True)                     -> '৳0.00'
    """
    key = _GROUPING_ALIASES.get(str(grouping).strip().lower())
    if key is None:
        raise ValueError(
            f"grouping must be {GROUPING_BD!r} or {GROUPING_INTL!r}; got {grouping!r}."
        )
    if isinstance(decimals, bool) or not isinstance(decimals, int) or decimals < 0 or decimals > 9:
        raise ValueError(f"decimals must be a whole number between 0 and 9; got {decimals!r}.")

    amount = value if isinstance(value, Money) else Money.from_taka(value)
    quantum = Decimal(1).scaleb(-decimals)
    taka = amount.to_decimal().quantize(quantum, rounding=ROUND_HALF_UP)

    negative = taka < 0
    digits_text = format(abs(taka), "f")
    if "." in digits_text:
        int_part, frac_part = digits_text.split(".", 1)
    else:
        int_part, frac_part = digits_text, ""
    if decimals and len(frac_part) < decimals:
        frac_part = frac_part.ljust(decimals, "0")
    frac_part = frac_part[:decimals]

    grouped = _group_bd(int_part) if key == GROUPING_BD else _group_international(int_part)
    body = f"{grouped}.{frac_part}" if decimals else grouped

    # Never print "-0.00": once quantised to zero it is zero.
    if negative and set(body) <= set("0,."):
        negative = False

    if symbol:
        body = f"{CURRENCY_SYMBOL}{symbol_sep}{body}"
    if negative:
        body = f"({body})" if parens_negative else f"-{body}"
    if bangla_digits:
        body = to_bangla_digits(body)
    return body


def format_bdt_international(value: "Money | Decimal | int | str", **kwargs: Any) -> str:
    """:func:`format_bdt` with international grouping (``1,234,567.89``)."""
    kwargs["grouping"] = GROUPING_INTL
    return format_bdt(value, **kwargs)


def format_amount_for_csv(amount: Money) -> str:
    """Plain ungrouped 2-decimal taka for a journal CSV cell: ``'1234.56'``."""
    if not isinstance(amount, Money):
        raise MoneyError(f"format_amount_for_csv expects Money; got {type(amount).__name__}.")
    return format(amount.to_decimal(), "f")


def markdown_table(
    headers: Sequence[str],
    rows: Iterable[Sequence[Any]],
    *,
    aligns: Sequence[str] | None = None,
) -> str:
    """Render a GitHub-flavoured Markdown table.  ``aligns`` items are 'l', 'c' or 'r'."""
    header_cells = [str(cell) for cell in headers]
    width = len(header_cells)
    if aligns is None:
        aligns = ["l"] * width
    if len(aligns) != width:
        raise ValueError("aligns must have one entry per column.")
    rule = []
    for align in aligns:
        rule.append({"l": ":---", "c": ":---:", "r": "---:"}.get(align, ":---"))

    def escape(cell: Any) -> str:
        return str(cell).replace("|", "\\|").replace("\n", " ")

    lines = ["| " + " | ".join(escape(c) for c in header_cells) + " |",
             "| " + " | ".join(rule) + " |"]
    for row in rows:
        cells = [escape(cell) for cell in row]
        if len(cells) < width:
            cells += [""] * (width - len(cells))
        lines.append("| " + " | ".join(cells[:width]) + " |")
    return "\n".join(lines)


# --------------------------------------------------------------------------------------
# Chart of accounts (spec §4.4)
# --------------------------------------------------------------------------------------

ACCOUNT_TYPES: tuple[str, ...] = ("asset", "liability", "equity", "income", "expense")

#: The only normal balance each account type may carry.
NORMAL_BALANCE: dict[str, str] = {
    "asset": "debit",
    "expense": "debit",
    "liability": "credit",
    "equity": "credit",
    "income": "credit",
}

BALANCE_SHEET_TYPES: tuple[str, ...] = ("asset", "liability", "equity")
INCOME_STATEMENT_TYPES: tuple[str, ...] = ("income", "expense")


@dataclass(frozen=True)
class AccountBlock:
    """One leading-digit block of the chart of accounts."""

    digit: str
    label_en: str
    label_bn: str
    types: tuple[str, ...]

    @property
    def label(self) -> str:
        return f"{self.label_bn} / {self.label_en}"


#: Code blocks from spec §4.4.  ``types`` lists the account types allowed in the block;
#: 9xxx (tax accounts) can legitimately be assets or liabilities.
ACCOUNT_BLOCKS: dict[str, AccountBlock] = {
    "1": AccountBlock("1", "Assets", "সম্পদ", ("asset",)),
    "2": AccountBlock("2", "Liabilities", "দায়", ("liability",)),
    "3": AccountBlock("3", "Equity", "মূলধন", ("equity",)),
    "4": AccountBlock("4", "Income", "আয়", ("income",)),
    "5": AccountBlock("5", "Cost of Goods Sold", "বিক্রিত পণ্যের ব্যয়", ("expense",)),
    "6": AccountBlock("6", "Operating Expenses", "পরিচালন ব্যয়", ("expense",)),
    "7": AccountBlock("7", "Other Income", "অন্যান্য আয়", ("income",)),
    "8": AccountBlock("8", "Other Expenses", "অন্যান্য ব্যয়", ("expense",)),
    "9": AccountBlock("9", "Tax Accounts", "কর হিসাব", ("asset", "liability", "expense")),
}

# Optional `role` keys.  Names are normative (spec §4.4), codes are the book's own.
ROLE_VAT_INPUT = "vat_input"
ROLE_VAT_OUTPUT = "vat_output"
ROLE_TDS_RECEIVABLE = "tds_receivable"
ROLE_TDS_PAYABLE = "tds_payable"
ROLE_VDS_PAYABLE = "vds_payable"
ROLE_ADVANCE_INCOME_TAX = "advance_income_tax"
ROLE_PROVIDENT_FUND_PAYABLE = "provident_fund_payable"
ROLE_GRATUITY_PROVISION = "gratuity_provision"
ROLE_WPPF_PAYABLE = "wppf_payable"
ROLE_SUPPLEMENTARY_DUTY_PAYABLE = "supplementary_duty_payable"

#: Bangladesh-specific accounts that a complete chart must provide (spec §4.4).
REQUIRED_ROLES: tuple[str, ...] = (
    ROLE_VAT_INPUT,
    ROLE_VAT_OUTPUT,
    ROLE_TDS_RECEIVABLE,
    ROLE_TDS_PAYABLE,
    ROLE_VDS_PAYABLE,
    ROLE_ADVANCE_INCOME_TAX,
    ROLE_PROVIDENT_FUND_PAYABLE,
    ROLE_GRATUITY_PROVISION,
    ROLE_WPPF_PAYABLE,
    ROLE_SUPPLEMENTARY_DUTY_PAYABLE,
)

_ACCOUNT_CODE_RE = re.compile(r"^[0-9]{4}(?:[.-][0-9A-Za-z]{1,6})?$")


def block_for_code(code: str) -> AccountBlock | None:
    """Return the :class:`AccountBlock` a code belongs to, or ``None``."""
    code = str(code).strip()
    return ACCOUNT_BLOCKS.get(code[:1]) if code else None


@dataclass(frozen=True)
class Account:
    """One line of ``accounts.toml``."""

    code: str
    name: str
    type: str
    normal: str
    name_bn: str = ""
    description: str = ""
    role: str = ""
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        code = str(self.code).strip()
        if not code:
            raise AccountError("Account code is required and may not be blank.")
        if not self.name or not str(self.name).strip():
            raise AccountError(f"Account {code} has no name.")
        acct_type = str(self.type).strip().lower()
        if acct_type not in ACCOUNT_TYPES:
            raise AccountError(
                f"Account {code} ({self.name}) has type {self.type!r}; "
                f"must be one of {', '.join(ACCOUNT_TYPES)}.",
            )
        normal = str(self.normal).strip().lower()
        if normal not in ("debit", "credit"):
            raise AccountError(
                f"Account {code} ({self.name}) has normal={self.normal!r}; "
                "must be 'debit' or 'credit'."
            )
        expected = NORMAL_BALANCE[acct_type]
        if normal != expected:
            raise AccountError(
                f"Account {code} ({self.name}) is type {acct_type!r} so its normal balance "
                f"must be {expected!r}, not {normal!r}.",
                hint="assets/expenses are debit-normal; liabilities/equity/income are credit-normal.",
            )
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "name", str(self.name).strip())
        object.__setattr__(self, "type", acct_type)
        object.__setattr__(self, "normal", normal)
        object.__setattr__(self, "name_bn", str(self.name_bn or "").strip())
        object.__setattr__(self, "description", str(self.description or "").strip())
        object.__setattr__(self, "role", str(self.role or "").strip().lower())
        object.__setattr__(self, "tags", tuple(str(tag).strip() for tag in (self.tags or ())))

    # -- derived -----------------------------------------------------------------------

    @property
    def is_debit_normal(self) -> bool:
        return self.normal == "debit"

    @property
    def is_credit_normal(self) -> bool:
        return self.normal == "credit"

    @property
    def block(self) -> AccountBlock | None:
        return block_for_code(self.code)

    @property
    def is_balance_sheet(self) -> bool:
        return self.type in BALANCE_SHEET_TYPES

    @property
    def is_income_statement(self) -> bool:
        return self.type in INCOME_STATEMENT_TYPES

    @property
    def label(self) -> str:
        """``'1100 Cash in Hand (হাতে নগদ)'`` — Bangla shown when available."""
        if self.name_bn:
            return f"{self.code} {self.name} ({self.name_bn})"
        return f"{self.code} {self.name}"

    def code_block_is_conventional(self) -> bool:
        """True when the leading digit matches the account type (spec §4.4 blocks)."""
        block = self.block
        if block is None:
            return False
        return self.type in block.types

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any], *, where: str = "accounts.toml") -> "Account":
        """Build from a parsed ``[[account]]`` table."""
        if not isinstance(data, Mapping):
            raise AccountError(f"{where}: each [[account]] must be a table, got {type(data).__name__}.")
        unknown = set(data) - {
            "code", "name", "name_bn", "type", "normal", "description", "role", "tags",
        }
        if unknown:
            raise AccountError(
                f"{where}: account {data.get('code', '?')} has unknown key(s): "
                f"{', '.join(sorted(unknown))}.",
                hint="Allowed keys: code, name, name_bn, type, normal, description, role, tags.",
            )
        missing = [key for key in ("code", "name", "type", "normal") if key not in data]
        if missing:
            raise AccountError(
                f"{where}: account {data.get('code', data.get('name', '?'))} is missing "
                f"required key(s): {', '.join(missing)}."
            )
        tags = data.get("tags", ())
        if isinstance(tags, str):
            tags = (tags,)
        return cls(
            code=str(data["code"]),
            name=str(data["name"]),
            type=str(data["type"]),
            normal=str(data["normal"]),
            name_bn=str(data.get("name_bn", "")),
            description=str(data.get("description", "")),
            role=str(data.get("role", "")),
            tags=tuple(str(tag) for tag in tags),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "name_bn": self.name_bn,
            "type": self.type,
            "normal": self.normal,
            "description": self.description,
            "role": self.role,
            "tags": list(self.tags),
        }


class ChartOfAccounts:
    """The validated chart of accounts (হিসাব তালিকা)."""

    def __init__(
        self,
        accounts: Iterable[Account],
        *,
        source_path: "Path | str | None" = None,
    ) -> None:
        self.source_path: Path | None = Path(source_path) if source_path else None
        self._accounts: dict[str, Account] = {}
        where = str(self.source_path) if self.source_path else "chart of accounts"
        for account in accounts:
            if not isinstance(account, Account):
                raise AccountError(f"{where}: expected Account, got {type(account).__name__}.")
            if account.code in self._accounts:
                first = self._accounts[account.code]
                raise DuplicateAccountError(
                    f"{where}: account code {account.code} is used twice "
                    f"({first.name!r} and {account.name!r}). Codes must be unique.",
                )
            self._accounts[account.code] = account

    # -- loaders -----------------------------------------------------------------------

    @classmethod
    def from_mapping(
        cls,
        data: Mapping[str, Any],
        *,
        source_path: "Path | str | None" = None,
    ) -> "ChartOfAccounts":
        where = str(source_path) if source_path else "accounts.toml"
        raw = data.get("account")
        if raw is None:
            raise AccountError(
                f"{where}: no [[account]] tables found.",
                hint='Each account looks like:\n[[account]]\ncode = "1100"\nname = "Cash in Hand"\n'
                'name_bn = "হাতে নগদ"\ntype = "asset"\nnormal = "debit"',
            )
        if isinstance(raw, Mapping):
            raw = [raw]
        if not isinstance(raw, list):
            raise AccountError(f"{where}: 'account' must be an array of tables ([[account]]).")
        return cls(
            (Account.from_mapping(item, where=where) for item in raw),
            source_path=source_path,
        )

    @classmethod
    def from_toml_bytes(
        cls, data: bytes, *, source_path: "Path | str | None" = None
    ) -> "ChartOfAccounts":
        where = str(source_path) if source_path else "accounts.toml"
        try:
            parsed = tomllib.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
            raise AccountError(f"{where}: could not parse TOML — {exc}") from exc
        return cls.from_mapping(parsed, source_path=source_path)

    @classmethod
    def from_toml_path(cls, path: "Path | str") -> "ChartOfAccounts":
        """Read and validate ``accounts.toml``."""
        path = Path(path)
        if not path.is_file():
            raise AccountError(
                f"Chart of accounts not found: {path}",
                hint="Run init_books.py to scaffold a books/ directory, or pass --books.",
            )
        return cls.from_toml_bytes(path.read_bytes(), source_path=path)

    # -- container protocol ------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._accounts)

    def __iter__(self) -> Iterator[Account]:
        return iter(self._accounts.values())

    def __contains__(self, code: object) -> bool:
        return str(code) in self._accounts

    def __getitem__(self, code: str) -> Account:
        return self.get(code)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"ChartOfAccounts({len(self)} accounts, source={self.source_path})"

    # -- lookups -----------------------------------------------------------------------

    def get(self, code: str, *, where: str = "") -> Account:
        """Return the account, or raise :class:`UnknownAccountError`."""
        key = str(code).strip()
        try:
            return self._accounts[key]
        except KeyError:
            prefix = f"{where}: " if where else ""
            close = [c for c in self._accounts if c.startswith(key[:2])][:5]
            hint = (
                f"Similar codes in this chart: {', '.join(close)}"
                if close
                else "Add it to accounts.toml, or fix the journal row."
            )
            raise UnknownAccountError(
                f"{prefix}unknown account code {key!r}. "
                f"It is not in {self.source_path or 'accounts.toml'}.",
                code=key,
                hint=hint,
            ) from None

    def has(self, code: str) -> bool:
        return str(code).strip() in self._accounts

    def codes(self) -> list[str]:
        return list(self._accounts)

    def accounts(self) -> list[Account]:
        return list(self._accounts.values())

    def by_type(self, account_type: str) -> list[Account]:
        wanted = str(account_type).strip().lower()
        if wanted not in ACCOUNT_TYPES:
            raise AccountError(f"Unknown account type {account_type!r}.")
        return [a for a in self._accounts.values() if a.type == wanted]

    def by_block(self, digit: str) -> list[Account]:
        digit = str(digit)[:1]
        return [a for a in self._accounts.values() if a.code.startswith(digit)]

    def by_tag(self, tag: str) -> list[Account]:
        return [a for a in self._accounts.values() if tag in a.tags]

    def by_role(self, role: str) -> list[Account]:
        wanted = str(role).strip().lower()
        return [a for a in self._accounts.values() if a.role == wanted]

    def account_for_role(self, role: str) -> Account:
        """Return the single account carrying ``role``; raise if absent or ambiguous."""
        matches = self.by_role(role)
        if not matches:
            raise UnknownAccountError(
                f"No account in {self.source_path or 'accounts.toml'} declares role = {role!r}.",
                code="",
                hint=f'Add role = "{role}" to the appropriate [[account]] table.',
            )
        if len(matches) > 1:
            raise AccountError(
                f"role = {role!r} is claimed by more than one account: "
                f"{', '.join(a.code for a in matches)}. It must be unique.",
            )
        return matches[0]

    def missing_roles(self, roles: Sequence[str] = REQUIRED_ROLES) -> list[str]:
        """Roles from ``roles`` that no account declares."""
        present = {a.role for a in self._accounts.values() if a.role}
        return [role for role in roles if role not in present]

    def require(self, codes: Iterable[str], *, where: str = "") -> None:
        """Raise :class:`UnknownAccountError` if any code is absent."""
        missing = sorted({str(c).strip() for c in codes} - set(self._accounts))
        if missing:
            prefix = f"{where}: " if where else ""
            raise UnknownAccountError(
                f"{prefix}unknown account code(s): {', '.join(missing)}.",
                code=missing[0],
                hint=f"Known codes: {', '.join(sorted(self._accounts)[:12])}…",
            )

    # -- soft checks -------------------------------------------------------------------

    def code_format_warnings(self) -> list[str]:
        """Codes that do not look like ``NNNN`` (advisory, not fatal)."""
        return [
            f"account code {a.code!r} ({a.name}) is not a 4-digit code such as '1100'"
            for a in self._accounts.values()
            if not _ACCOUNT_CODE_RE.match(a.code)
        ]

    def block_warnings(self) -> list[str]:
        """Accounts whose leading digit disagrees with their type (advisory)."""
        warnings: list[str] = []
        for account in self._accounts.values():
            block = account.block
            if block is None:
                warnings.append(
                    f"account {account.code} ({account.name}) is outside the 1xxx–9xxx blocks"
                )
            elif account.type not in block.types:
                warnings.append(
                    f"account {account.code} ({account.name}) is type {account.type!r} but "
                    f"the {block.digit}xxx block is {block.label_en} "
                    f"({'/'.join(block.types)})"
                )
        return warnings


# --------------------------------------------------------------------------------------
# tax_tag grammar (spec §4.3)
# --------------------------------------------------------------------------------------

TAG_NONE = "NONE"
TAG_VAT_OUT = "VAT_OUT"
TAG_VAT_IN = "VAT_IN"
TAG_TDS = "TDS"
TAG_VDS = "VDS"

TAX_TAG_KINDS: tuple[str, ...] = (TAG_NONE, TAG_VAT_OUT, TAG_VAT_IN, TAG_TDS, TAG_VDS)

TAX_TAG_GRAMMAR = (
    "tax_tag grammar: "
    "VAT:OUT:<rate> (output VAT / প্রদেয় মূসক) · "
    "VAT:IN:<rate> (rebateable input VAT / রেয়াতযোগ্য উপকরণ মূসক) · "
    "TDS:<section>:<rate> (উৎসে কর কর্তন) · "
    "VDS:<rate> (উৎসে মূসক কর্তন) · "
    "NONE (not tax-relevant). <rate> is a percentage such as 15, 7.5 or 0."
)

_TAG_RATE_RE = re.compile(r"^(\d{1,3}(?:\.\d{1,4})?)\s*%?$")
_TAG_SECTION_RE = re.compile(r"^[0-9]{1,4}[A-Za-z]{0,4}(?:\([0-9A-Za-z]{1,4}\))?$")
_TAG_EMPTY = {"", "-", "--", "n/a", "na"}


def _format_rate(rate: Decimal) -> str:
    normalised = rate.normalize()
    if normalised == normalised.to_integral_value():
        normalised = normalised.quantize(Decimal(1))
    return format(normalised, "f")


@dataclass(frozen=True)
class TaxTag:
    """A parsed ``tax_tag`` cell.

    ``rate`` is a **percentage** as a :class:`Decimal` (15 means 15%), not a fraction.
    ``section`` is only set for TDS.  ``raw`` keeps the original cell text.
    """

    kind: str = TAG_NONE
    rate: Decimal | None = None
    section: str | None = None
    raw: str = TAG_NONE

    def __post_init__(self) -> None:
        if self.kind not in TAX_TAG_KINDS:
            raise TaxTagError(f"Unknown tax tag kind {self.kind!r}; expected one of {TAX_TAG_KINDS}.")

    # -- construction ------------------------------------------------------------------

    @classmethod
    def none(cls) -> "TaxTag":
        return cls(kind=TAG_NONE, rate=None, section=None, raw=TAG_NONE)

    @classmethod
    def parse(cls, text: str, *, allow_empty: bool = True, where: str = "") -> "TaxTag":
        """Parse a ``tax_tag`` cell.  Malformed tags raise :class:`TaxTagError`.

        An empty cell means ``NONE`` unless ``allow_empty=False``.
        """
        prefix = f"{where}: " if where else ""
        if text is None:
            text = ""
        if not isinstance(text, str):
            raise TaxTagError(f"{prefix}tax_tag must be text; got {type(text).__name__}.")
        raw = text.strip()
        if raw.lower() in _TAG_EMPTY:
            if not allow_empty and raw == "":
                raise TaxTagError(
                    f"{prefix}tax_tag is empty. Write NONE when a line is not tax-relevant.",
                    hint=TAX_TAG_GRAMMAR,
                )
            return cls(kind=TAG_NONE, rate=None, section=None, raw=raw or TAG_NONE)

        parts = [part.strip() for part in raw.split(":")]
        head = parts[0].upper()

        def bad(reason: str) -> TaxTagError:
            return TaxTagError(f"{prefix}malformed tax_tag {raw!r}: {reason}", hint=TAX_TAG_GRAMMAR)

        if head == TAG_NONE:
            if len(parts) != 1:
                raise bad("NONE takes no rate or section.")
            return cls(kind=TAG_NONE, rate=None, section=None, raw=raw)

        if head == "VAT":
            if len(parts) != 3:
                raise bad("expected VAT:OUT:<rate> or VAT:IN:<rate>.")
            direction = parts[1].upper()
            if direction not in ("OUT", "IN"):
                raise bad(f"VAT direction must be OUT or IN, got {parts[1]!r}.")
            rate = cls._parse_rate(parts[2], raw, prefix)
            return cls(
                kind=TAG_VAT_OUT if direction == "OUT" else TAG_VAT_IN,
                rate=rate,
                section=None,
                raw=raw,
            )

        if head == "TDS":
            if len(parts) != 3:
                raise bad("expected TDS:<section>:<rate>, e.g. TDS:52:5.")
            section = parts[1].strip()
            if not section:
                raise bad("the section is empty; TDS:<section>:<rate> needs a section.")
            if not _TAG_SECTION_RE.match(section):
                raise bad(
                    f"section {section!r} is not a statute section reference "
                    "(digits, optional letters, optional bracketed sub-clause)."
                )
            rate = cls._parse_rate(parts[2], raw, prefix)
            return cls(kind=TAG_TDS, rate=rate, section=section.upper(), raw=raw)

        if head == "VDS":
            if len(parts) != 2:
                raise bad("expected VDS:<rate>, e.g. VDS:15.")
            rate = cls._parse_rate(parts[1], raw, prefix)
            return cls(kind=TAG_VDS, rate=rate, section=None, raw=raw)

        raise bad(f"unknown tag type {parts[0]!r}.")

    @staticmethod
    def _parse_rate(text: str, raw: str, prefix: str) -> Decimal:
        match = _TAG_RATE_RE.match(text.strip())
        if not match:
            raise TaxTagError(
                f"{prefix}malformed tax_tag {raw!r}: rate {text!r} is not a percentage "
                "such as 15, 7.5 or 0.",
                hint=TAX_TAG_GRAMMAR,
            )
        rate = Decimal(match.group(1))
        if rate > 100:
            raise TaxTagError(
                f"{prefix}malformed tax_tag {raw!r}: rate {text!r} is above 100%. "
                "Rates are percentages, not fractions.",
                hint=TAX_TAG_GRAMMAR,
            )
        return rate

    # -- predicates --------------------------------------------------------------------

    @property
    def is_none(self) -> bool:
        return self.kind == TAG_NONE

    @property
    def is_vat(self) -> bool:
        return self.kind in (TAG_VAT_OUT, TAG_VAT_IN)

    @property
    def is_vat_output(self) -> bool:
        return self.kind == TAG_VAT_OUT

    @property
    def is_vat_input(self) -> bool:
        return self.kind == TAG_VAT_IN

    @property
    def is_tds(self) -> bool:
        return self.kind == TAG_TDS

    @property
    def is_vds(self) -> bool:
        return self.kind == TAG_VDS

    @property
    def rate_fraction(self) -> Decimal:
        """The rate as a fraction (15% -> ``Decimal('0.15')``); 0 for ``NONE``."""
        if self.rate is None:
            return Decimal(0)
        with decimal.localcontext() as ctx:
            ctx.prec = _CALC_PRECISION
            return self.rate / Decimal(100)

    def apply(self, base: Money, *, rounding: str = ROUND_HALF_UP) -> Money:
        """Tax on ``base`` at this tag's rate, rounded once.  ``NONE`` gives ৳0.00."""
        if not isinstance(base, Money):
            raise MoneyError(f"TaxTag.apply expects Money; got {type(base).__name__}.")
        if self.rate is None:
            return Money.zero()
        return base.percent(self.rate, rounding=rounding)

    def __str__(self) -> str:
        """Canonical form: ``VAT:OUT:15``, ``VAT:IN:7.5``, ``TDS:52:5``, ``VDS:15``, ``NONE``."""
        if self.kind == TAG_NONE:
            return TAG_NONE
        rate_text = _format_rate(self.rate if self.rate is not None else Decimal(0))
        if self.kind == TAG_VAT_OUT:
            return f"VAT:OUT:{rate_text}"
        if self.kind == TAG_VAT_IN:
            return f"VAT:IN:{rate_text}"
        if self.kind == TAG_TDS:
            return f"TDS:{self.section}:{rate_text}"
        return f"VDS:{rate_text}"

    def describe(self) -> str:
        """Human sentence with Bangla / English term pair."""
        if self.kind == TAG_NONE:
            return "not tax-relevant"
        rate_text = _format_rate(self.rate if self.rate is not None else Decimal(0)) + "%"
        if self.kind == TAG_VAT_OUT:
            return f"output {term('vat')} at {rate_text}"
        if self.kind == TAG_VAT_IN:
            return f"rebateable input {term('vat')} at {rate_text}"
        if self.kind == TAG_TDS:
            return f"{term('tds')} under section {self.section} at {rate_text}"
        return f"{term('vds')} at {rate_text}"


# --------------------------------------------------------------------------------------
# Books directory layout
# --------------------------------------------------------------------------------------

DEFAULT_BOOKS_DIR = "books"
CONFIG_FILENAME = "config.toml"
ACCOUNTS_FILENAME = "accounts.toml"
JOURNAL_DIRNAME = "journal"


def config_path(books_dir: "Path | str" = DEFAULT_BOOKS_DIR) -> Path:
    return Path(books_dir) / CONFIG_FILENAME


def accounts_path(books_dir: "Path | str" = DEFAULT_BOOKS_DIR) -> Path:
    return Path(books_dir) / ACCOUNTS_FILENAME


def journal_dir(
    books_dir: "Path | str" = DEFAULT_BOOKS_DIR, journal_dirname: str = JOURNAL_DIRNAME
) -> Path:
    return Path(books_dir) / journal_dirname


def journal_path_for(
    books_dir: "Path | str",
    when: "datetime.date | str",
    journal_dirname: str = JOURNAL_DIRNAME,
) -> Path:
    """``books/journal/YYYY-MM.csv`` for a date or an ISO date string."""
    if isinstance(when, str):
        when = parse_date(when)
    return journal_dir(books_dir, journal_dirname) / f"{when.year:04d}-{when.month:02d}.csv"


# --------------------------------------------------------------------------------------
# Journal CSV (spec §4.3)
# --------------------------------------------------------------------------------------

JOURNAL_COLUMNS: tuple[str, ...] = (
    "date",
    "entry_id",
    "description",
    "account",
    "debit",
    "credit",
    "party",
    "doc_ref",
    "tax_tag",
    "memo",
)
JOURNAL_HEADER = ",".join(JOURNAL_COLUMNS)

#: ``books/journal/YYYY-MM.csv``
JOURNAL_FILENAME_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])\.csv$")

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

#: The first six columns are mandatory in a data row; the rest may be omitted.
_MIN_ROW_FIELDS = 6


def parse_date(text: str, *, where: str = "", field_name: str = "date") -> datetime.date:
    """Parse a strict ISO ``YYYY-MM-DD`` date.  Anything else raises :class:`JournalError`."""
    prefix = f"{where}: " if where else ""
    if isinstance(text, datetime.datetime):
        return text.date()
    if isinstance(text, datetime.date):
        return text
    value = str(text or "").strip()
    if not _ISO_DATE_RE.match(value):
        raise JournalError(
            f"{prefix}{field_name} {text!r} is not an ISO date.",
            hint="Dates must be written YYYY-MM-DD, e.g. 2026-07-15.",
        )
    try:
        return datetime.date.fromisoformat(value)
    except ValueError as exc:
        raise JournalError(f"{prefix}{field_name} {text!r} is not a real calendar date ({exc}).") from None


def parse_amount_field(text: str, *, field_name: str, where: str = "") -> Money:
    """Parse a debit/credit CSV cell.  Blank means ৳0.00."""
    prefix = f"{where}: " if where else ""
    value = "" if text is None else str(text).strip()
    if value == "" or value == "-":
        return Money.zero()
    try:
        return Money.from_str(value, what=field_name)
    except MoneyError as exc:
        raise JournalError(f"{prefix}{exc.message}", hint=exc.hint) from None


@dataclass(frozen=True)
class Posting:
    """One journal line — one row of ``books/journal/YYYY-MM.csv``."""

    date: datetime.date
    entry_id: str
    description: str
    account: str
    debit: Money
    credit: Money
    party: str = ""
    doc_ref: str = ""
    tax_tag: TaxTag = field(default_factory=TaxTag.none)
    memo: str = ""
    source_file: str = field(default="", compare=False)
    source_line: int = field(default=0, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.date, datetime.date) or isinstance(self.date, datetime.datetime):
            object.__setattr__(self, "date", parse_date(self.date, where=self.location))
        entry_id = str(self.entry_id or "").strip()
        if not entry_id:
            raise JournalError(
                f"{self.location or 'journal row'}: entry_id is required — it is what groups "
                "lines into one balanced entry."
            )
        object.__setattr__(self, "entry_id", entry_id)
        object.__setattr__(self, "description", str(self.description or "").strip())
        account = str(self.account or "").strip()
        if not account:
            raise JournalError(f"{self.location or 'journal row'}: account code is required.")
        object.__setattr__(self, "account", account)
        for name in ("debit", "credit"):
            value = getattr(self, name)
            if not isinstance(value, Money):
                raise JournalError(
                    f"{self.location or 'journal row'}: {name} must be Money; "
                    f"got {type(value).__name__}."
                )
            if value.is_negative():
                raise JournalError(
                    f"{self.location or 'journal row'} (entry {entry_id}): {name} is negative "
                    f"({format_bdt(value, symbol=True)}). Reverse the sides instead of using a "
                    "negative amount."
                )
        if self.debit.is_zero() and self.credit.is_zero():
            raise JournalError(
                f"{self.location or 'journal row'} (entry {entry_id}, account {account}): both "
                "debit and credit are zero. Exactly one of the two must be non-zero."
            )
        if not self.debit.is_zero() and not self.credit.is_zero():
            raise JournalError(
                f"{self.location or 'journal row'} (entry {entry_id}, account {account}): debit "
                f"({format_bdt(self.debit, symbol=True)}) and credit "
                f"({format_bdt(self.credit, symbol=True)}) are both non-zero. Split it into two rows."
            )
        if isinstance(self.tax_tag, str):
            object.__setattr__(self, "tax_tag", TaxTag.parse(self.tax_tag, where=self.location))
        if not isinstance(self.tax_tag, TaxTag):
            raise TaxTagError(
                f"{self.location or 'journal row'}: tax_tag must be a TaxTag or a string; "
                f"got {type(self.tax_tag).__name__}."
            )
        object.__setattr__(self, "party", str(self.party or "").strip())
        object.__setattr__(self, "doc_ref", str(self.doc_ref or "").strip())
        object.__setattr__(self, "memo", str(self.memo or ""))

    # -- derived -----------------------------------------------------------------------

    @property
    def location(self) -> str:
        """``'books/journal/2026-07.csv line 4'`` when known, else ``''``."""
        if self.source_file and self.source_line:
            return f"{self.source_file} line {self.source_line}"
        return self.source_file or ""

    @property
    def is_debit(self) -> bool:
        return not self.debit.is_zero()

    @property
    def is_credit(self) -> bool:
        return not self.credit.is_zero()

    @property
    def amount(self) -> Money:
        """The non-zero side, always positive."""
        return self.debit if self.is_debit else self.credit

    @property
    def signed_amount(self) -> Money:
        """Debit-positive signed amount (debit − credit)."""
        return self.debit - self.credit

    @property
    def month(self) -> str:
        """``'2026-07'`` — the journal file this posting belongs in."""
        return f"{self.date.year:04d}-{self.date.month:02d}"

    # -- CSV ---------------------------------------------------------------------------

    @classmethod
    def from_row(
        cls,
        row: "Mapping[str, Any] | Sequence[Any]",
        *,
        source_file: str = "",
        source_line: int = 0,
    ) -> "Posting":
        """Build from a CSV row (a mapping keyed by :data:`JOURNAL_COLUMNS`, or a sequence)."""
        where = f"{source_file} line {source_line}" if source_file and source_line else ""
        if isinstance(row, Mapping):
            values = {key: row.get(key, "") for key in JOURNAL_COLUMNS}
        else:
            cells = list(row)
            if len(cells) < _MIN_ROW_FIELDS:
                raise JournalError(
                    f"{where or 'journal row'}: found {len(cells)} field(s), need at least "
                    f"{_MIN_ROW_FIELDS} ({', '.join(JOURNAL_COLUMNS[:_MIN_ROW_FIELDS])}).",
                    hint=f"Header must be: {JOURNAL_HEADER}",
                )
            if len(cells) > len(JOURNAL_COLUMNS):
                # `memo` is last precisely so unquoted commas in it are survivable.
                cells = cells[: len(JOURNAL_COLUMNS) - 1] + [",".join(
                    str(c) for c in cells[len(JOURNAL_COLUMNS) - 1:]
                )]
            cells += [""] * (len(JOURNAL_COLUMNS) - len(cells))
            values = dict(zip(JOURNAL_COLUMNS, cells))

        return cls(
            date=parse_date(values["date"], where=where),
            entry_id=str(values["entry_id"] or "").strip(),
            description=str(values["description"] or ""),
            account=str(values["account"] or "").strip(),
            debit=parse_amount_field(values["debit"], field_name="debit", where=where),
            credit=parse_amount_field(values["credit"], field_name="credit", where=where),
            party=str(values["party"] or ""),
            doc_ref=str(values["doc_ref"] or ""),
            tax_tag=TaxTag.parse(str(values["tax_tag"] or ""), where=where),
            memo=str(values["memo"] or ""),
            source_file=source_file,
            source_line=source_line,
        )

    def to_row(self) -> dict[str, str]:
        """Row as a mapping keyed by :data:`JOURNAL_COLUMNS`."""
        return {
            "date": self.date.isoformat(),
            "entry_id": self.entry_id,
            "description": self.description,
            "account": self.account,
            "debit": format_amount_for_csv(self.debit),
            "credit": format_amount_for_csv(self.credit),
            "party": self.party,
            "doc_ref": self.doc_ref,
            "tax_tag": str(self.tax_tag),
            "memo": self.memo,
        }

    def to_cells(self) -> list[str]:
        """Row as a list in :data:`JOURNAL_COLUMNS` order."""
        row = self.to_row()
        return [row[column] for column in JOURNAL_COLUMNS]


@dataclass(frozen=True)
class Entry:
    """All postings sharing one ``entry_id``.  Must balance (spec §4.3)."""

    entry_id: str
    postings: tuple[Posting, ...]

    def __post_init__(self) -> None:
        postings = tuple(self.postings)
        if not postings:
            raise JournalError(f"Entry {self.entry_id!r} has no postings.")
        wrong = [p for p in postings if p.entry_id != self.entry_id]
        if wrong:
            raise JournalError(
                f"Entry {self.entry_id!r} was given postings belonging to "
                f"{wrong[0].entry_id!r}."
            )
        object.__setattr__(self, "postings", postings)

    @classmethod
    def from_postings(cls, postings: Iterable[Posting]) -> "Entry":
        items = tuple(postings)
        if not items:
            raise JournalError("Cannot build an Entry from zero postings.")
        return cls(entry_id=items[0].entry_id, postings=items)

    # -- derived -----------------------------------------------------------------------

    @property
    def date(self) -> datetime.date:
        return self.postings[0].date

    @property
    def dates(self) -> tuple[datetime.date, ...]:
        return tuple(sorted({p.date for p in self.postings}))

    @property
    def description(self) -> str:
        for posting in self.postings:
            if posting.description:
                return posting.description
        return ""

    @property
    def total_debit(self) -> Money:
        return Money.sum(p.debit for p in self.postings)

    @property
    def total_credit(self) -> Money:
        return Money.sum(p.credit for p in self.postings)

    @property
    def difference(self) -> Money:
        """Debits − credits.  ৳0.00 when balanced."""
        return self.total_debit - self.total_credit

    @property
    def is_balanced(self) -> bool:
        return self.difference.is_zero()

    @property
    def accounts(self) -> tuple[str, ...]:
        seen: list[str] = []
        for posting in self.postings:
            if posting.account not in seen:
                seen.append(posting.account)
        return tuple(seen)

    @property
    def tax_tags(self) -> tuple[TaxTag, ...]:
        return tuple(p.tax_tag for p in self.postings)

    @property
    def source_files(self) -> tuple[str, ...]:
        return tuple(sorted({p.source_file for p in self.postings if p.source_file}))

    @property
    def source_lines(self) -> tuple[int, ...]:
        return tuple(sorted(p.source_line for p in self.postings if p.source_line))

    @property
    def location(self) -> str:
        files = self.source_files
        lines = self.source_lines
        if not files:
            return ""
        where = ", ".join(files)
        if lines:
            span = f"line {lines[0]}" if len(lines) == 1 else f"lines {lines[0]}–{lines[-1]}"
            return f"{where} {span}"
        return where

    def balance_message(self) -> str:
        """The human sentence used by :meth:`require_balanced`."""
        difference = self.difference
        side = "debit" if difference.is_positive() else "credit"
        where = f" — {self.location}" if self.location else ""
        return (
            f"Entry {self.entry_id!r} dated {self.date.isoformat()} does not balance: "
            f"debits {format_bdt(self.total_debit, symbol=True)} vs credits "
            f"{format_bdt(self.total_credit, symbol=True)}; "
            f"{format_bdt(abs(difference), symbol=True)} too much {side}{where}"
        )

    def require_balanced(self) -> None:
        """Raise :class:`BalanceError` unless debits == credits, in paisa."""
        if self.is_balanced:
            return
        raise BalanceError(
            self.balance_message(),
            entry_id=self.entry_id,
            difference=self.difference,
            total_debit=self.total_debit,
            total_credit=self.total_credit,
            entry_ids=(self.entry_id,),
            hint="Every entry must have equal debits and credits. TakaBooks never adjusts "
            "your numbers for you.",
        )


def group_postings(postings: Iterable[Posting]) -> list[Entry]:
    """Group postings into :class:`Entry` objects, ordered by date then first appearance."""
    order: list[str] = []
    buckets: dict[str, list[Posting]] = {}
    for posting in postings:
        if posting.entry_id not in buckets:
            buckets[posting.entry_id] = []
            order.append(posting.entry_id)
        buckets[posting.entry_id].append(posting)
    position = {entry_id: index for index, entry_id in enumerate(order)}
    entries = [Entry(entry_id=eid, postings=tuple(buckets[eid])) for eid in order]
    return sorted(entries, key=lambda entry: (entry.date, position[entry.entry_id]))


# --------------------------------------------------------------------------------------
# Journal file IO
# --------------------------------------------------------------------------------------


def _normalise_header(cells: Sequence[str]) -> list[str]:
    normalised = []
    for index, cell in enumerate(cells):
        text = str(cell)
        if index == 0:
            text = text.lstrip("\ufeff")
        normalised.append(text.strip().lower())
    while normalised and normalised[-1] == "":
        normalised.pop()
    return normalised


def read_journal_csv(
    path: "Path | str",
    *,
    chart: "ChartOfAccounts | None" = None,
    relative_to: "Path | str | None" = None,
) -> list[Posting]:
    """Read one ``books/journal/YYYY-MM.csv`` into :class:`Posting` objects.

    Blank lines and ``#`` comment lines are skipped.  If ``chart`` is given, every
    account code is checked and an unknown code is a hard error (spec §4.3).
    """
    path = Path(path)
    if not path.is_file():
        raise JournalError(f"Journal file not found: {path}")
    label = _display_path(path, relative_to)
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise JournalError(
            f"{label}: file is not UTF-8 ({exc}). Save it as UTF-8 (CSV UTF-8 in Excel)."
        ) from None

    reader = csv.reader(io.StringIO(text, newline=""))
    postings: list[Posting] = []
    header_seen = False
    for cells in reader:
        line_no = reader.line_num
        if not cells or all(str(cell).strip() == "" for cell in cells):
            continue
        if str(cells[0]).lstrip("\ufeff").lstrip().startswith("#"):
            continue
        if not header_seen:
            header = _normalise_header(cells)
            if header != list(JOURNAL_COLUMNS):
                raise JournalError(
                    f"{label} line {line_no}: unexpected header {','.join(header)}",
                    hint=f"The header must be exactly: {JOURNAL_HEADER}",
                )
            header_seen = True
            continue
        posting = Posting.from_row(cells, source_file=label, source_line=line_no)
        if chart is not None:
            chart.get(posting.account, where=f"{label} line {line_no} (entry {posting.entry_id})")
        postings.append(posting)

    if not header_seen:
        raise JournalError(
            f"{label}: no header row found.",
            hint=f"The first non-blank line must be: {JOURNAL_HEADER}",
        )
    return postings


def journal_files(
    books_dir: "Path | str" = DEFAULT_BOOKS_DIR,
    *,
    strict: bool = False,
    journal_dirname: str = JOURNAL_DIRNAME,
) -> list[Path]:
    """Sorted ``*.csv`` files in ``<books>/journal/``.

    With ``strict=True`` a filename that is not ``YYYY-MM.csv`` raises :class:`JournalError`.
    """
    directory = journal_dir(books_dir, journal_dirname)
    if not directory.is_dir():
        raise LedgerError(
            f"Journal directory not found: {directory}",
            hint="Run init_books.py to scaffold books/, or pass --books <dir>.",
        )
    files = sorted(p for p in directory.glob("*.csv") if p.is_file())
    if strict:
        bad = [p.name for p in files if not JOURNAL_FILENAME_RE.match(p.name)]
        if bad:
            raise JournalError(
                f"{directory}: journal file name(s) {', '.join(bad)} are not YYYY-MM.csv.",
                hint="One file per month, e.g. 2026-07.csv.",
            )
    return files


def read_journal_dir(
    books_dir: "Path | str" = DEFAULT_BOOKS_DIR,
    *,
    chart: "ChartOfAccounts | None" = None,
    strict_filenames: bool = False,
    journal_dirname: str = JOURNAL_DIRNAME,
) -> list[Posting]:
    """Read every journal file under ``<books>/journal/``."""
    root = Path(books_dir)
    postings: list[Posting] = []
    for path in journal_files(root, strict=strict_filenames, journal_dirname=journal_dirname):
        postings.extend(read_journal_csv(path, chart=chart, relative_to=root.parent))
    return postings


def write_journal_csv(
    path: "Path | str",
    postings: Iterable[Posting],
    *,
    header: bool = True,
) -> Path:
    """Write postings to a journal CSV, replacing the file.  Returns the path."""
    path = Path(path)
    handle = io.StringIO(newline="")
    writer = csv.writer(handle, lineterminator="\n")
    if header:
        writer.writerow(JOURNAL_COLUMNS)
    writer.writerows(posting.to_cells() for posting in postings)
    write_text_atomic(path, handle.getvalue())
    return path


def append_journal_csv(path: "Path | str", postings: Iterable[Posting]) -> Path:
    """Append postings, creating the file with a header when it does not exist yet."""
    path = Path(path)
    items = list(postings)
    if not items:
        return path
    needs_header = not path.exists() or path.stat().st_size == 0
    existing = "" if needs_header else path.read_text(encoding="utf-8-sig")
    if existing and not existing.endswith("\n"):
        existing += "\n"
    handle = io.StringIO(newline="")
    writer = csv.writer(handle, lineterminator="\n")
    if needs_header:
        writer.writerow(JOURNAL_COLUMNS)
    writer.writerows(posting.to_cells() for posting in items)
    write_text_atomic(path, existing + handle.getvalue())
    return path


def _display_path(path: Path, relative_to: "Path | str | None") -> str:
    if relative_to is None:
        return str(path)
    try:
        return str(path.resolve().relative_to(Path(relative_to).resolve()))
    except (ValueError, OSError):
        return str(path)


# --------------------------------------------------------------------------------------
# Books layout, config
# --------------------------------------------------------------------------------------

def load_toml(path: "Path | str", *, error: type[TakaBooksError] = ConfigError) -> dict[str, Any]:
    """Read a TOML file into a dict, raising ``error`` with a readable message."""
    path = Path(path)
    if not path.is_file():
        raise error(f"TOML file not found: {path}")
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise error(f"{path}: could not parse TOML — {exc}") from None
    except OSError as exc:
        raise error(f"{path}: could not be read — {exc}") from None


_MONTH_DAY_RE = re.compile(r"^(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")


@dataclass(frozen=True)
class Config:
    """``books/config.toml``.

    Nothing statutory is defaulted here: ``fiscal_year_start`` and ``assessment_year``
    come from the file or stay ``None``, because TakaBooks never invents a
    Bangladeshi tax fact (spec §6.2).
    """

    business_name: str = ""
    business_name_bn: str = ""
    business_type: str = ""
    bin: str = ""
    tin: str = ""
    address: str = ""
    currency: str = CURRENCY_CODE
    fiscal_year_start: str | None = None
    assessment_year: str | None = None
    rates_file: str | None = None
    accounts_file: str = ACCOUNTS_FILENAME
    journal_dirname: str = JOURNAL_DIRNAME
    language: str = "en"
    grouping: str = GROUPING_BD
    digits: str = "latin"
    source_path: Path | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)

    # -- loaders -----------------------------------------------------------------------

    @classmethod
    def from_mapping(
        cls, data: Mapping[str, Any], *, source_path: "Path | str | None" = None
    ) -> "Config":
        where = str(source_path) if source_path else CONFIG_FILENAME
        if not isinstance(data, Mapping):
            raise ConfigError(f"{where}: top level must be a TOML table.")
        business = data.get("business", {}) or {}
        books = data.get("books", {}) or {}
        locale = data.get("locale", {}) or {}
        for name, table in (("business", business), ("books", books), ("locale", locale)):
            if not isinstance(table, Mapping):
                raise ConfigError(f"{where}: [{name}] must be a table.")

        fiscal = books.get("fiscal_year_start")
        fiscal = str(fiscal).strip() if fiscal not in (None, "") else None
        if fiscal is not None and not _MONTH_DAY_RE.match(fiscal):
            raise ConfigError(
                f"{where}: books.fiscal_year_start = {fiscal!r} must be written MM-DD "
                "(the day your income year opens).",
                hint="TakaBooks does not assume a fiscal year for you — set it explicitly.",
            )

        grouping_raw = str(locale.get("grouping", GROUPING_BD)).strip().lower()
        grouping = _GROUPING_ALIASES.get(grouping_raw)
        if grouping is None:
            raise ConfigError(
                f"{where}: locale.grouping = {locale.get('grouping')!r} must be "
                f"{GROUPING_BD!r} or {GROUPING_INTL!r}."
            )
        digits = str(locale.get("digits", "latin")).strip().lower()
        if digits not in ("latin", "bangla"):
            raise ConfigError(f"{where}: locale.digits must be 'latin' or 'bangla'.")
        language = str(locale.get("language", "en")).strip().lower()
        if language not in ("en", "bn", "bn-en"):
            raise ConfigError(f"{where}: locale.language must be 'en', 'bn' or 'bn-en'.")

        currency = str(books.get("currency", CURRENCY_CODE)).strip().upper() or CURRENCY_CODE
        if currency != CURRENCY_CODE:
            raise ConfigError(
                f"{where}: books.currency = {currency!r}; TakaBooks keeps books in "
                f"{CURRENCY_CODE} only."
            )

        assessment_year = books.get("assessment_year")
        assessment_year = str(assessment_year).strip() if assessment_year not in (None, "") else None
        rates_file = books.get("rates_file")
        rates_file = str(rates_file).strip() if rates_file not in (None, "") else None

        return cls(
            business_name=str(business.get("name", "")).strip(),
            business_name_bn=str(business.get("name_bn", "")).strip(),
            business_type=str(business.get("type", "")).strip(),
            bin=str(business.get("bin", "")).strip(),
            tin=str(business.get("tin", "")).strip(),
            address=str(business.get("address", "")).strip(),
            currency=currency,
            fiscal_year_start=fiscal,
            assessment_year=assessment_year,
            rates_file=rates_file,
            accounts_file=str(books.get("accounts_file", ACCOUNTS_FILENAME)).strip()
            or ACCOUNTS_FILENAME,
            journal_dirname=str(books.get("journal_dir", JOURNAL_DIRNAME)).strip()
            or JOURNAL_DIRNAME,
            language=language,
            grouping=grouping,
            digits=digits,
            source_path=Path(source_path) if source_path else None,
            raw=dict(data),
        )

    @classmethod
    def from_toml_path(cls, path: "Path | str") -> "Config":
        path = Path(path)
        if not path.is_file():
            raise ConfigError(
                f"Config not found: {path}",
                hint="Run init_books.py to scaffold a books/ directory, or pass --books <dir>.",
            )
        return cls.from_mapping(load_toml(path), source_path=path)

    @classmethod
    def load(cls, books_dir: "Path | str" = DEFAULT_BOOKS_DIR) -> "Config":
        """Load ``<books>/config.toml``."""
        return cls.from_toml_path(config_path(books_dir))

    # -- access ------------------------------------------------------------------------

    def get(self, dotted_key: str, default: Any = None) -> Any:
        """Read any raw value, e.g. ``config.get('business.name')``."""
        node: Any = self.raw
        for part in str(dotted_key).split("."):
            if not isinstance(node, Mapping) or part not in node:
                return default
            node = node[part]
        return node

    def require_fiscal_year_start(self) -> str:
        """Return ``MM-DD`` or raise — TakaBooks never guesses your income year."""
        if not self.fiscal_year_start:
            raise ConfigError(
                f"{self.source_path or CONFIG_FILENAME}: books.fiscal_year_start is not set.",
                hint='Add it under [books], e.g. fiscal_year_start = "07-01". TakaBooks will '
                "not assume a fiscal year on your behalf.",
            )
        return self.fiscal_year_start

    def require_assessment_year(self) -> str:
        """Return the assessment year (করবর্ষ) or raise."""
        if not self.assessment_year:
            raise ConfigError(
                f"{self.source_path or CONFIG_FILENAME}: books.assessment_year is not set.",
                hint='Add it under [books], e.g. assessment_year = "2026-27". Every tax output '
                "must state the assessment year it used.",
            )
        return self.assessment_year

    @property
    def display_name(self) -> str:
        if self.business_name and self.business_name_bn:
            return f"{self.business_name} ({self.business_name_bn})"
        return self.business_name or self.business_name_bn or "(unnamed business)"

    def format_money(self, amount: Money, **kwargs: Any) -> str:
        """Format using the book's locale preferences."""
        kwargs.setdefault("grouping", self.grouping)
        kwargs.setdefault("bangla_digits", self.digits == "bangla")
        return format_bdt(amount, **kwargs)


# --------------------------------------------------------------------------------------
# Ledger
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class AccountTotal:
    """Debit / credit totals for one account."""

    code: str
    debit: Money
    credit: Money
    account: Account | None = None

    @property
    def net(self) -> Money:
        """Debit-positive net (debits − credits)."""
        return self.debit - self.credit

    @property
    def natural(self) -> Money:
        """Net expressed positively in the account's normal direction."""
        if self.account is not None and self.account.is_credit_normal:
            return self.credit - self.debit
        return self.net

    @property
    def name(self) -> str:
        return self.account.name if self.account else ""

    @property
    def type(self) -> str:
        return self.account.type if self.account else ""


class Ledger:
    """A loaded set of books (খতিয়ান): config + chart + every posting."""

    def __init__(
        self,
        postings: Iterable[Posting],
        *,
        chart: "ChartOfAccounts | None" = None,
        config: "Config | None" = None,
        books_dir: "Path | str | None" = None,
    ) -> None:
        self.postings: tuple[Posting, ...] = tuple(postings)
        self.chart = chart
        self.config = config
        self.books_dir: Path | None = Path(books_dir) if books_dir else None
        self.entries: tuple[Entry, ...] = tuple(group_postings(self.postings))
        self._by_id: dict[str, Entry] = {entry.entry_id: entry for entry in self.entries}

    # -- loading -----------------------------------------------------------------------

    @classmethod
    def load(
        cls,
        books_dir: "Path | str" = DEFAULT_BOOKS_DIR,
        *,
        require_balanced: bool = True,
        strict_accounts: bool = True,
        strict_filenames: bool = False,
        config: "Config | None" = None,
        chart: "ChartOfAccounts | None" = None,
    ) -> "Ledger":
        """Load ``config.toml``, ``accounts.toml`` and every ``journal/*.csv``.

        ``require_balanced`` defaults to **True**: reporting scripts must never
        compute from broken books.  ``validate.py`` passes ``False`` so it can
        collect and report every problem at once.
        """
        root = Path(books_dir)
        if not root.is_dir():
            raise LedgerError(
                f"Books directory not found: {root}",
                hint="Run init_books.py to create it, or pass --books <dir>.",
            )
        config = config if config is not None else Config.load(root)
        if chart is None:
            chart = ChartOfAccounts.from_toml_path(root / config.accounts_file)
        postings = read_journal_dir(
            root,
            chart=chart if strict_accounts else None,
            strict_filenames=strict_filenames,
            journal_dirname=config.journal_dirname,
        )
        ledger = cls(postings, chart=chart, config=config, books_dir=root)
        if require_balanced:
            ledger.require_balanced()
        return ledger

    # -- container -----------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.postings)

    def __iter__(self) -> Iterator[Posting]:
        return iter(self.postings)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"Ledger({len(self.postings)} postings, {len(self.entries)} entries, "
            f"books={self.books_dir})"
        )

    @property
    def is_empty(self) -> bool:
        return not self.postings

    def entry_ids(self) -> list[str]:
        return [entry.entry_id for entry in self.entries]

    def entry(self, entry_id: str) -> Entry:
        try:
            return self._by_id[str(entry_id)]
        except KeyError:
            raise LedgerError(f"No entry with entry_id {entry_id!r} in these books.") from None

    def has_entry(self, entry_id: str) -> bool:
        return str(entry_id) in self._by_id

    # -- balance enforcement (spec §2) ---------------------------------------------------

    def imbalances(self) -> list[tuple[str, Money]]:
        """``[(entry_id, debits − credits), …]`` for every entry that does not balance."""
        return [(e.entry_id, e.difference) for e in self.entries if not e.is_balanced]

    def unbalanced_entries(self) -> list[Entry]:
        return [entry for entry in self.entries if not entry.is_balanced]

    def require_balanced(self, *, max_reported: int = 10) -> None:
        """Raise :class:`BalanceError` naming every offending entry and its imbalance."""
        broken = self.unbalanced_entries()
        if not broken:
            return
        lines = [entry.balance_message() for entry in broken[:max_reported]]
        if len(broken) > max_reported:
            lines.append(f"…and {len(broken) - max_reported} more unbalanced entries.")
        head = (
            "The books do not balance — 1 entry is out"
            if len(broken) == 1
            else f"The books do not balance — {len(broken)} entries are out"
        )
        first = broken[0]
        raise BalanceError(
            head + ":\n  - " + "\n  - ".join(lines),
            entry_id=first.entry_id,
            difference=first.difference,
            total_debit=first.total_debit,
            total_credit=first.total_credit,
            entry_ids=[entry.entry_id for entry in broken],
            hint="Fix the journal rows. TakaBooks refuses to guess the missing side.",
        )

    def total_debits(self) -> Money:
        return Money.sum(p.debit for p in self.postings)

    def total_credits(self) -> Money:
        return Money.sum(p.credit for p in self.postings)

    def is_balanced(self) -> bool:
        return not self.unbalanced_entries()

    # -- integrity helpers for validate.py ----------------------------------------------

    def unknown_accounts(self) -> list[Posting]:
        """Postings whose account code is absent from the chart."""
        if self.chart is None:
            return []
        return [p for p in self.postings if not self.chart.has(p.account)]

    def entry_id_conflicts(self) -> list[str]:
        """Entry ids reused across files or across dates — usually a copy/paste slip."""
        problems: list[str] = []
        for entry in self.entries:
            if len(entry.dates) > 1:
                dates = ", ".join(d.isoformat() for d in entry.dates)
                problems.append(
                    f"entry_id {entry.entry_id!r} appears on more than one date ({dates})"
                )
            if len(entry.source_files) > 1:
                files = ", ".join(entry.source_files)
                problems.append(
                    f"entry_id {entry.entry_id!r} is split across files ({files})"
                )
        return problems

    def out_of_order_dates(self) -> list[str]:
        """Postings whose date runs backwards within one journal file."""
        problems: list[str] = []
        per_file: dict[str, Posting] = {}
        for posting in self.postings:
            previous = per_file.get(posting.source_file)
            if previous is not None and posting.date < previous.date:
                problems.append(
                    f"{posting.location}: date {posting.date.isoformat()} is earlier than "
                    f"{previous.date.isoformat()} on the line above"
                )
            per_file[posting.source_file] = posting
        return problems

    def misfiled_postings(self) -> list[str]:
        """Postings sitting in a journal file for a different month."""
        problems: list[str] = []
        for posting in self.postings:
            name = Path(posting.source_file).name if posting.source_file else ""
            match = JOURNAL_FILENAME_RE.match(name)
            if match and f"{match.group(1)}-{match.group(2)}" != posting.month:
                problems.append(
                    f"{posting.location}: dated {posting.date.isoformat()} but filed in {name}"
                )
        return problems

    # -- selection -----------------------------------------------------------------------

    def filter(
        self,
        *,
        since: "datetime.date | str | None" = None,
        until: "datetime.date | str | None" = None,
        accounts: Iterable[str] | None = None,
        account_types: Iterable[str] | None = None,
        tax_kinds: Iterable[str] | None = None,
        entry_ids: Iterable[str] | None = None,
        parties: Iterable[str] | None = None,
    ) -> "Ledger":
        """Return a new :class:`Ledger` holding the matching postings.

        Dates are inclusive on both ends.  ``account_types`` needs a chart.
        """
        since_date = parse_date(since) if isinstance(since, str) else since
        until_date = parse_date(until) if isinstance(until, str) else until
        account_set = {str(a).strip() for a in accounts} if accounts is not None else None
        type_set = {str(t).strip().lower() for t in account_types} if account_types is not None else None
        kind_set = {str(k).strip().upper() for k in tax_kinds} if tax_kinds is not None else None
        id_set = {str(i).strip() for i in entry_ids} if entry_ids is not None else None
        party_set = {str(p).strip() for p in parties} if parties is not None else None

        def keep(posting: Posting) -> bool:
            if since_date is not None and posting.date < since_date:
                return False
            if until_date is not None and posting.date > until_date:
                return False
            if account_set is not None and posting.account not in account_set:
                return False
            if id_set is not None and posting.entry_id not in id_set:
                return False
            if party_set is not None and posting.party not in party_set:
                return False
            if kind_set is not None and posting.tax_tag.kind not in kind_set:
                return False
            if type_set is not None:
                if self.chart is None:
                    raise LedgerError("filter(account_types=…) needs a chart of accounts.")
                if self.chart.get(posting.account).type not in type_set:
                    return False
            return True

        return Ledger(
            (p for p in self.postings if keep(p)),
            chart=self.chart,
            config=self.config,
            books_dir=self.books_dir,
        )

    def period(
        self, start: "datetime.date | str", end: "datetime.date | str"
    ) -> "Ledger":
        """Inclusive date window — shorthand for ``filter(since=…, until=…)``."""
        return self.filter(since=start, until=end)

    def by_account(self, code: str) -> list[Posting]:
        key = str(code).strip()
        return [p for p in self.postings if p.account == key]

    def tax_postings(self, kind: str) -> list[Posting]:
        """Postings whose tax tag is of ``kind`` (:data:`TAG_VAT_OUT` etc.)."""
        wanted = str(kind).strip().upper()
        if wanted not in TAX_TAG_KINDS:
            raise TaxTagError(f"Unknown tax tag kind {kind!r}; expected one of {TAX_TAG_KINDS}.")
        return [p for p in self.postings if p.tax_tag.kind == wanted]

    def date_range(self) -> tuple[datetime.date | None, datetime.date | None]:
        if not self.postings:
            return (None, None)
        dates = [p.date for p in self.postings]
        return (min(dates), max(dates))

    # -- aggregation ---------------------------------------------------------------------

    def account_totals(self, *, include_unused: bool = False) -> dict[str, AccountTotal]:
        """Debit/credit totals per account code, in chart order where a chart is loaded."""
        debits: dict[str, int] = {}
        credits: dict[str, int] = {}
        seen: list[str] = []
        for posting in self.postings:
            if posting.account not in debits:
                debits[posting.account] = 0
                credits[posting.account] = 0
                seen.append(posting.account)
            debits[posting.account] += posting.debit.paisa
            credits[posting.account] += posting.credit.paisa

        if self.chart is not None:
            ordered = [code for code in self.chart.codes() if code in debits or include_unused]
            ordered += [code for code in seen if code not in self.chart]
        else:
            ordered = seen

        totals: dict[str, AccountTotal] = {}
        for code in ordered:
            account = self.chart.get(code) if (self.chart is not None and self.chart.has(code)) else None
            totals[code] = AccountTotal(
                code=code,
                debit=Money(debits.get(code, 0)),
                credit=Money(credits.get(code, 0)),
                account=account,
            )
        return totals

    def balance(self, code: str) -> Money:
        """Debit-positive net balance of one account."""
        key = str(code).strip()
        return Money.sum(p.signed_amount for p in self.postings if p.account == key)

    def natural_balance(self, code: str) -> Money:
        """Balance expressed positively in the account's normal direction."""
        net = self.balance(code)
        if self.chart is not None and self.chart.has(code) and self.chart.get(code).is_credit_normal:
            return -net
        return net

    def type_total(self, account_type: str) -> Money:
        """Natural-direction total for every account of one type (needs a chart)."""
        if self.chart is None:
            raise LedgerError("type_total() needs a chart of accounts.")
        wanted = str(account_type).strip().lower()
        if wanted not in ACCOUNT_TYPES:
            raise AccountError(f"Unknown account type {account_type!r}.")
        total = 0
        for entry in self.account_totals().values():
            if entry.account is not None and entry.account.type == wanted:
                total += entry.natural.paisa
        return Money(total)


# --------------------------------------------------------------------------------------
# Rates TOML (spec §4.5) — structural only.  This file defines no Bangladeshi tax number.
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Rate:
    """One value read from a rates TOML, with its provenance."""

    key: str
    value: Any
    source: str = ""
    verified: bool = False
    as_of: str = ""
    note: str = ""
    unit: str = ""

    @property
    def is_verified(self) -> bool:
        return bool(self.verified)

    def caveat(self) -> str:
        """The sentence a consumer must show when the figure is unverified (spec §6.2)."""
        if self.verified:
            return ""
        return (
            f"UNVERIFIED: {self.key} could not be confirmed against a primary NBR source. "
            "Confirm it with the National Board of Revenue before you rely on it."
        )

    def as_decimal(self) -> Decimal:
        return _to_decimal(self.value, what=f"rate {self.key}")

    def as_money(self) -> Money:
        return Money.from_taka(self.value, what=f"rate {self.key}")


_MISSING = object()
_RATES_FILENAME_RE = re.compile(r"(?i)rates-AY(\d{4}-\d{2,4})\.toml$")


class RatesTable:
    """Reader for ``src/data/rates-AY<year>.toml``.

    Deliberately shape-agnostic: a node may be a bare scalar, or a table carrying
    ``value`` plus ``source`` / ``verified`` / ``as_of`` / ``note`` / ``unit``.  A node
    with no explicit ``verified = true`` is treated as **unverified**, because absent
    beats wrong (spec §6.2).
    """

    def __init__(
        self,
        data: Mapping[str, Any],
        *,
        source_path: "Path | str | None" = None,
        assessment_year: str | None = None,
    ) -> None:
        if not isinstance(data, Mapping):
            raise RatesError("Rates data must be a TOML table.")
        self.raw: Mapping[str, Any] = data
        self.source_path: Path | None = Path(source_path) if source_path else None
        year = assessment_year
        if year is None:
            meta = data.get("meta") if isinstance(data.get("meta"), Mapping) else {}
            year = meta.get("assessment_year") if isinstance(meta, Mapping) else None
        if year is None:
            year = data.get("assessment_year")
        if year is None and self.source_path is not None:
            match = _RATES_FILENAME_RE.search(self.source_path.name)
            if match:
                year = match.group(1)
        self.assessment_year: str | None = str(year).strip() if year not in (None, "") else None

    @classmethod
    def from_toml_path(cls, path: "Path | str") -> "RatesTable":
        path = Path(path)
        if not path.is_file():
            raise RatesError(
                f"Rates file not found: {path}",
                hint="Point --rates at a rates-AY<year>.toml, or set books.rates_file in config.toml.",
            )
        return cls(load_toml(path, error=RatesError), source_path=path)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"RatesTable(AY={self.assessment_year}, source={self.source_path})"

    # -- access --------------------------------------------------------------------------

    def _node(self, dotted_key: str) -> Any:
        node: Any = self.raw
        for part in str(dotted_key).split("."):
            if not isinstance(node, Mapping) or part not in node:
                return _MISSING
            node = node[part]
        return node

    def has(self, dotted_key: str) -> bool:
        return self._node(dotted_key) is not _MISSING

    def get(self, dotted_key: str, default: Any = _MISSING) -> Any:
        """Raw value at ``dotted_key`` (unwrapping a ``{value = …}`` table)."""
        node = self._node(dotted_key)
        if node is _MISSING:
            if default is _MISSING:
                raise RatesError(
                    f"{self.source_path or 'rates file'}: no value for {dotted_key!r}.",
                    hint="TakaBooks will not substitute a guessed rate. Add the figure to the "
                    "rates TOML with its source URL, or tell the user it is unavailable.",
                )
            return default
        if isinstance(node, Mapping) and "value" in node:
            return node["value"]
        return node

    def rate(self, dotted_key: str) -> Rate:
        """Value plus provenance at ``dotted_key``."""
        node = self._node(dotted_key)
        if node is _MISSING:
            raise RatesError(
                f"{self.source_path or 'rates file'}: no value for {dotted_key!r}.",
                hint="Absent beats wrong — do not substitute a remembered figure.",
            )
        if isinstance(node, Mapping):
            if "value" not in node:
                raise RatesError(
                    f"{self.source_path or 'rates file'}: {dotted_key!r} is a table without a "
                    "'value' key; it is a section, not a rate."
                )
            return Rate(
                key=dotted_key,
                value=node["value"],
                source=str(node.get("source", "")),
                verified=bool(node.get("verified", False)),
                as_of=str(node.get("as_of", "")),
                note=str(node.get("note", "")),
                unit=str(node.get("unit", "")),
            )
        return Rate(key=dotted_key, value=node, source="", verified=False)

    def decimal(self, dotted_key: str) -> Decimal:
        return _to_decimal(self.get(dotted_key), what=f"rate {dotted_key}")

    def money(self, dotted_key: str) -> Money:
        return Money.from_taka(self.get(dotted_key), what=f"rate {dotted_key}")

    def section(self, dotted_key: str) -> Mapping[str, Any]:
        node = self._node(dotted_key)
        if node is _MISSING or not isinstance(node, Mapping):
            raise RatesError(f"{self.source_path or 'rates file'}: {dotted_key!r} is not a section.")
        return node

    def unverified_keys(self) -> list[str]:
        """Dotted keys of every declared rate node (a table with ``value``) that is not
        marked ``verified = true``.  Bare scalars elsewhere in the file are metadata,
        not rates, so they are not audited here — but :meth:`rate` still reports a bare
        scalar as unverified, because absent beats wrong."""
        found: list[str] = []

        def walk(node: Any, prefix: str) -> None:
            if isinstance(node, Mapping):
                if "value" in node:
                    if not bool(node.get("verified", False)):
                        found.append(prefix)
                    return
                for key, child in node.items():
                    walk(child, f"{prefix}.{key}" if prefix else str(key))
            elif isinstance(node, list):
                for index, child in enumerate(node):
                    walk(child, f"{prefix}[{index}]")

        walk(self.raw, "")
        return sorted(found)

    def provenance(self) -> str:
        """The line every consumer must print (spec §4.5)."""
        name = self.source_path.name if self.source_path else "rates file"
        year = self.assessment_year or "unknown assessment year"
        return f"Rates source: {name} — {term('assessment_year')} {year}"

    def caveats(self) -> list[str]:
        """One warning line per unverified figure, for the consumer to surface."""
        return [
            f"UNVERIFIED: {key} in {self.source_path.name if self.source_path else 'rates file'} "
            "is not confirmed against a primary NBR source — verify before filing."
            for key in self.unverified_keys()
        ]


# --------------------------------------------------------------------------------------
# CLI helpers (spec §4.6: every script has --help, --books, --json, non-zero on failure)
# --------------------------------------------------------------------------------------


def common_parser(
    prog: str,
    description: str,
    *,
    books: bool = True,
    json_flag: bool = True,
    epilog: str | None = None,
) -> argparse.ArgumentParser:
    """An :class:`argparse.ArgumentParser` with the flags every TakaBooks script shares."""
    parser = argparse.ArgumentParser(
        prog=prog,
        description=description,
        epilog=epilog if epilog is not None else ATTRIBUTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    if books:
        parser.add_argument(
            "--books",
            default=DEFAULT_BOOKS_DIR,
            metavar="DIR",
            help=f"books directory (default: ./{DEFAULT_BOOKS_DIR})",
        )
    if json_flag:
        parser.add_argument(
            "--json",
            action="store_true",
            help="emit machine-readable JSON on stdout instead of text",
        )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{PROJECT_NAME} {__version__}",
    )
    return parser


@contextlib.contextmanager
def cli_guard(*, json_output: bool = False, stream: Any = None) -> Iterator[None]:
    """Turn a :class:`TakaBooksError` into a clean message and a non-zero exit.

    Usage::

        with cli_guard(json_output=args.json):
            main(args)
    """
    err = stream if stream is not None else sys.stderr
    try:
        yield
    except TakaBooksError as exc:
        if json_output:
            payload = {
                "ok": False,
                "error": type(exc).__name__,
                "message": exc.message,
                "hint": exc.hint,
                "exit_code": exc.exit_code,
            }
            err.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        else:
            err.write(f"error: {exc}\n")
        raise SystemExit(exc.exit_code) from exc
    except KeyboardInterrupt:  # pragma: no cover - interactive only
        err.write("\ninterrupted\n")
        raise SystemExit(130) from None


def to_jsonable(value: Any, *, money: str = "decimal") -> Any:
    """Recursively convert Money/Decimal/date/dataclass values for :func:`json.dumps`.

    ``money`` is ``"decimal"`` (``"1234.56"``), ``"paisa"`` (``123456``) or ``"object"``
    (``{"paisa": …, "bdt": "…", "formatted": "…"}``).
    """
    if isinstance(value, Money):
        if money == "paisa":
            return value.paisa
        if money == "object":
            return {
                "paisa": value.paisa,
                "bdt": format_amount_for_csv(value),
                "formatted": format_bdt(value, symbol=True),
            }
        if money != "decimal":
            raise ValueError("money must be 'decimal', 'paisa' or 'object'.")
        return format_amount_for_csv(value)
    if isinstance(value, TaxTag):
        return str(value)
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            f.name: to_jsonable(getattr(value, f.name), money=money)
            for f in dataclasses.fields(value)
        }
    if isinstance(value, Mapping):
        return {str(k): to_jsonable(v, money=money) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [to_jsonable(item, money=money) for item in value]
    return value


def json_dumps(value: Any, *, money: str = "decimal", indent: int = 2) -> str:
    """``json.dumps`` with TakaBooks types handled and Bangla text left readable."""
    return json.dumps(to_jsonable(value, money=money), ensure_ascii=False, indent=indent)


def ensure_dir(path: "Path | str") -> Path:
    """Create a directory (and parents) if needed; return it."""
    directory = Path(path)
    if str(directory) in ("", "."):
        return Path(".")
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise LedgerError(f"Could not create directory {directory}: {exc}") from None
    return directory


def write_text_atomic(path: "Path | str", text: str, *, encoding: str = "utf-8") -> Path:
    """Write ``text`` via a temporary file and :func:`os.replace`, so a crash cannot
    leave a half-written ledger behind."""
    path = Path(path)
    ensure_dir(path.parent)
    temp = path.with_name(path.name + ".takabooks-tmp")
    try:
        with temp.open("w", encoding=encoding, newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    except OSError as exc:
        with contextlib.suppress(OSError):
            temp.unlink()
        raise LedgerError(f"Could not write {path}: {exc}") from None
    return path


if __name__ == "__main__":  # pragma: no cover - convenience only
    print(f"{PROJECT_NAME} shared library {__version__}")
    print(ATTRIBUTION)
    print(f"Python {'.'.join(str(p) for p in sys.version_info[:3])} (minimum "
          f"{'.'.join(str(p) for p in MIN_PYTHON)})")
    print(TAX_TAG_GRAMMAR)
