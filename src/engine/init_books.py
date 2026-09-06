#!/usr/bin/env python3
"""Scaffold a TakaBooks ``books/`` directory (spec §4.6).

Creates::

    books/
    ├── config.toml      business identity + locale + book settings
    ├── accounts.toml    হিসাব তালিকা / chart of accounts
    ├── journal/         জাবেদা / journal — one YYYY-MM.csv per month
    └── reports/         generated trial balance, P&L, balance sheet

Source of the two TOML files is ``src/templates/`` when it exists; otherwise a
complete built-in Bangladesh chart is used so the tool always works standalone.

**Nothing statutory is invented here.**  ``fiscal_year_start`` and
``assessment_year`` (করবর্ষ) are written only when you supply them; otherwise
they are left as commented-out lines with a note, because TakaBooks refuses to
guess a Bangladeshi tax fact on your behalf (spec §6.2).  No rate, threshold or
deadline appears in this file — those live in ``src/data/rates-AY*.toml``.

Examples::

    python3 src/engine/init_books.py --books books --name "Ticon Sys" \
        --fiscal-year-start 07-01 --assessment-year 2026-27 --vat-registered yes
    python3 src/engine/init_books.py --interactive
    python3 src/engine/init_books.py --dry-run --json

TakaBooks — Moshiur Rahman (@bemoshiur) · Ticon Sys — https://ticonsys.com
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

_ENGINE_DIR = Path(__file__).resolve().parent
if str(_ENGINE_DIR) not in sys.path:  # pragma: no cover - import plumbing
    sys.path.insert(0, str(_ENGINE_DIR))

import takabooks as tb  # noqa: E402

# ``takabooks`` performs the Python 3.11 floor check at import time, before it
# imports tomllib, so importing tomllib after it is safe on every interpreter
# that got this far.
import tomllib  # noqa: E402

__all__ = [
    "CITY_TIERS",
    "VAT_REGISTRATION_CHOICES",
    "REPORTS_DIRNAME",
    "TEMPLATES_DIRNAME",
    "FALLBACK_ACCOUNTS_TOML",
    "default_templates_dir",
    "render_config_toml",
    "build_parser",
    "run",
    "main",
]

REPORTS_DIRNAME = "reports"
TEMPLATES_DIRNAME = "templates"
TEMPLATE_CONFIG = "config.toml"
TEMPLATE_ACCOUNTS = "accounts.toml"
TEMPLATE_JOURNAL_HEADER = "journal-header.csv"

#: Where the business is located.  This is a *label only*: TakaBooks attaches no
#: amount to it.  Anything that depends on location comes from the assessment
#: year rates file, never from this script (spec §4.5, §6.2).
CITY_TIERS: dict[str, tuple[str, str]] = {
    "unspecified": ("অনির্দিষ্ট", "not stated"),
    "dhaka-chattogram-city": (
        "ঢাকা বা চট্টগ্রাম সিটি কর্পোরেশন এলাকা",
        "Dhaka or Chattogram city corporation area",
    ),
    "other-city": ("অন্যান্য সিটি কর্পোরেশন এলাকা", "other city corporation area"),
    "other-area": ("অন্যান্য এলাকা", "any other area"),
}

#: মূসক নিবন্ধন / VAT registration.  Tri-state on purpose — "unknown" is an
#: honest answer and beats a fabricated "no".
VAT_REGISTRATION_CHOICES: tuple[str, ...] = ("yes", "no", "unknown")

_MONTH_DAY_RE = re.compile(r"^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$")
_ASSESSMENT_YEAR_RE = re.compile(r"^\d{4}-(\d{2}|\d{4})$")
_MONTH_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
_TOML_ESCAPES = {"\\": "\\\\", '"': '\\"', "\b": "\\b", "\f": "\\f",
                 "\n": "\\n", "\r": "\\r", "\t": "\\t"}


# --------------------------------------------------------------------------------------
# Built-in fallback chart of accounts
#
# Used only when src/templates/accounts.toml is absent.  Codes follow the spec §4.4
# blocks (1 assets · 2 liabilities · 3 equity · 4 income · 5 COGS · 6 operating
# expenses · 7 other income · 8 other expenses · 9 tax accounts) and every one of the
# ten Bangladesh-specific accounts the spec mandates carries its `role` key, so the
# VAT/TDS engines can find it whatever code you renumber it to.
# --------------------------------------------------------------------------------------

FALLBACK_ACCOUNTS_TOML = '''# TakaBooks — হিসাব তালিকা / chart of accounts
#
# Codes are yours to renumber; `role` is what the engine looks up, so keep the
# role keys on whichever accounts play those parts.
#   1xxx সম্পদ / assets          2xxx দায় / liabilities      3xxx মূলধন / equity
#   4xxx আয় / income            5xxx বিক্রিত পণ্যের ব্যয় / COGS
#   6xxx পরিচালন ব্যয় / operating expenses                   7xxx অন্যান্য আয় / other income
#   8xxx অন্যান্য ব্যয় / other expenses                        9xxx কর হিসাব / tax accounts
#
# type: asset|liability|equity|income|expense
# normal: debit for asset/expense, credit for liability/equity/income
#
# TakaBooks — Moshiur Rahman (@bemoshiur) · Ticon Sys — https://ticonsys.com

[[account]]
code = "1100"
name = "Cash in Hand"
name_bn = "হাতে নগদ"
type = "asset"
normal = "debit"

[[account]]
code = "1110"
name = "Bank Account"
name_bn = "ব্যাংক হিসাব"
type = "asset"
normal = "debit"

[[account]]
code = "1200"
name = "Accounts Receivable"
name_bn = "প্রাপ্য হিসাব"
type = "asset"
normal = "debit"

[[account]]
code = "1250"
name = "Inventory"
name_bn = "মজুদ পণ্য"
type = "asset"
normal = "debit"

[[account]]
code = "1310"
name = "VAT Input / Rebateable"
name_bn = "রেয়াতযোগ্য উপকরণ মূসক"
type = "asset"
normal = "debit"
role = "vat_input"
description = "Input মূসক / VAT paid to suppliers and claimable as rebate."

[[account]]
code = "1320"
name = "TDS Receivable"
name_bn = "প্রাপ্য উৎসে কর্তিত কর"
type = "asset"
normal = "debit"
role = "tds_receivable"
description = "উৎসে কর কর্তন / TDS your customers deducted from your bills."

[[account]]
code = "1330"
name = "Advance Income Tax"
name_bn = "অগ্রিম আয়কর"
type = "asset"
normal = "debit"
role = "advance_income_tax"

[[account]]
code = "1400"
name = "Prepaid Expenses"
name_bn = "অগ্রিম প্রদত্ত খরচ"
type = "asset"
normal = "debit"

[[account]]
code = "1500"
name = "Furniture and Fixtures"
name_bn = "আসবাবপত্র"
type = "asset"
normal = "debit"

[[account]]
code = "1510"
name = "Office Equipment"
name_bn = "অফিস সরঞ্জাম"
type = "asset"
normal = "debit"

[[account]]
code = "2100"
name = "Accounts Payable"
name_bn = "প্রদেয় হিসাব"
type = "liability"
normal = "credit"

[[account]]
code = "2200"
name = "Salaries Payable"
name_bn = "প্রদেয় বেতন"
type = "liability"
normal = "credit"

[[account]]
code = "2310"
name = "VAT Output Payable"
name_bn = "প্রদেয় মূসক"
type = "liability"
normal = "credit"
role = "vat_output"
description = "Output মূসক / VAT charged on your sales and payable to NBR."

[[account]]
code = "2320"
name = "TDS Payable"
name_bn = "প্রদেয় উৎসে কর্তিত কর"
type = "liability"
normal = "credit"
role = "tds_payable"
description = "উৎসে কর কর্তন / TDS you deducted from vendors, awaiting deposit."

[[account]]
code = "2330"
name = "VDS Payable"
name_bn = "প্রদেয় উৎসে কর্তিত মূসক"
type = "liability"
normal = "credit"
role = "vds_payable"
description = "উৎসে মূসক কর্তন / VDS withheld from suppliers, awaiting deposit."

[[account]]
code = "2340"
name = "Supplementary Duty Payable"
name_bn = "প্রদেয় সম্পূরক শুল্ক"
type = "liability"
normal = "credit"
role = "supplementary_duty_payable"

[[account]]
code = "2410"
name = "Provident Fund Payable"
name_bn = "প্রদেয় ভবিষ্য তহবিল"
type = "liability"
normal = "credit"
role = "provident_fund_payable"

[[account]]
code = "2420"
name = "Gratuity Provision"
name_bn = "গ্র্যাচুইটি সঞ্চিতি"
type = "liability"
normal = "credit"
role = "gratuity_provision"

[[account]]
code = "2430"
name = "WPPF Payable"
name_bn = "প্রদেয় শ্রমিক অংশগ্রহণ তহবিল"
type = "liability"
normal = "credit"
role = "wppf_payable"
description = "Workers' Profit Participation Fund."

[[account]]
code = "2500"
name = "Loans Payable"
name_bn = "প্রদেয় ঋণ"
type = "liability"
normal = "credit"

[[account]]
code = "3100"
name = "Owner's Capital"
name_bn = "মালিকের মূলধন"
type = "equity"
normal = "credit"

[[account]]
code = "3200"
name = "Retained Earnings"
name_bn = "সংরক্ষিত মুনাফা"
type = "equity"
normal = "credit"

[[account]]
code = "4100"
name = "Sales Revenue"
name_bn = "বিক্রয় আয়"
type = "income"
normal = "credit"

[[account]]
code = "4200"
name = "Service Revenue"
name_bn = "সেবা আয়"
type = "income"
normal = "credit"

[[account]]
code = "5100"
name = "Purchases"
name_bn = "ক্রয়"
type = "expense"
normal = "debit"

[[account]]
code = "5200"
name = "Cost of Goods Sold"
name_bn = "বিক্রিত পণ্যের ব্যয়"
type = "expense"
normal = "debit"

[[account]]
code = "5300"
name = "Direct Wages"
name_bn = "প্রত্যক্ষ মজুরি"
type = "expense"
normal = "debit"

[[account]]
code = "6100"
name = "Salaries and Wages"
name_bn = "বেতন ও মজুরি"
type = "expense"
normal = "debit"

[[account]]
code = "6200"
name = "Office Rent"
name_bn = "অফিস ভাড়া"
type = "expense"
normal = "debit"

[[account]]
code = "6300"
name = "Utilities"
name_bn = "ইউটিলিটি বিল"
type = "expense"
normal = "debit"

[[account]]
code = "6400"
name = "Telephone and Internet"
name_bn = "টেলিফোন ও ইন্টারনেট"
type = "expense"
normal = "debit"

[[account]]
code = "6500"
name = "Repairs and Maintenance"
name_bn = "মেরামত ও রক্ষণাবেক্ষণ"
type = "expense"
normal = "debit"

[[account]]
code = "6600"
name = "Depreciation Expense"
name_bn = "অবচয় ব্যয়"
type = "expense"
normal = "debit"

[[account]]
code = "6700"
name = "Professional Fees"
name_bn = "পেশাদার ফি"
type = "expense"
normal = "debit"

[[account]]
code = "6800"
name = "Bank Charges"
name_bn = "ব্যাংক চার্জ"
type = "expense"
normal = "debit"

[[account]]
code = "6900"
name = "Trade Licence and Government Fees"
name_bn = "ট্রেড লাইসেন্স ও সরকারি ফি"
type = "expense"
normal = "debit"

[[account]]
code = "7100"
name = "Interest Income"
name_bn = "সুদ আয়"
type = "income"
normal = "credit"

[[account]]
code = "7200"
name = "Other Income"
name_bn = "অন্যান্য আয়"
type = "income"
normal = "credit"

[[account]]
code = "8100"
name = "Interest Expense"
name_bn = "সুদ ব্যয়"
type = "expense"
normal = "debit"

[[account]]
code = "8200"
name = "Penalties and Fines"
name_bn = "জরিমানা ও দণ্ড"
type = "expense"
normal = "debit"

[[account]]
code = "9100"
name = "Income Tax Expense"
name_bn = "আয়কর ব্যয়"
type = "expense"
normal = "debit"

[[account]]
code = "9200"
name = "Provision for Income Tax"
name_bn = "আয়কর সঞ্চিতি"
type = "liability"
normal = "credit"
'''


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------


def default_templates_dir() -> Path:
    """``src/templates`` — the directory this script scaffolds from."""
    return _ENGINE_DIR.parent / TEMPLATES_DIRNAME


def _toml_string(value: Any) -> str:
    """Render a TOML basic string.  Everything we write is a string."""
    text = "" if value is None else str(value)
    return '"' + "".join(_TOML_ESCAPES.get(ch, ch) for ch in text) + '"'


def _check_month_day(value: str) -> str:
    value = value.strip()
    if not _MONTH_DAY_RE.match(value):
        raise tb.ConfigError(
            f"--fiscal-year-start {value!r} must be written MM-DD, e.g. 07-01.",
            hint="TakaBooks does not assume an income year for you; state the day it opens.",
        )
    return value


def _check_assessment_year(value: str) -> str:
    value = value.strip()
    if not _ASSESSMENT_YEAR_RE.match(value):
        raise tb.ConfigError(
            f"--assessment-year {value!r} should look like 2026-27 "
            f"({tb.term('assessment_year')}).",
            hint="Use the assessment year printed on your NBR return, not a calendar year.",
        )
    return value


def _check_month(value: str) -> str:
    value = value.strip()
    if not _MONTH_RE.match(value):
        raise tb.ConfigError(
            f"--start-month {value!r} must be written YYYY-MM, e.g. 2026-07.",
            hint="One journal file per month: books/journal/YYYY-MM.csv.",
        )
    return value


def _ask(question: str, default: str = "") -> str:
    """Prompt once.  End-of-input keeps the default, so piping never hangs."""
    suffix = f" [{default}]" if default else ""
    try:
        answer = input(f"{question}{suffix}: ")
    except EOFError:
        return default
    answer = answer.strip()
    return answer or default


def _ask_choice(question: str, choices: tuple[str, ...], default: str) -> str:
    answer = _ask(f"{question} ({'/'.join(choices)})", default)
    while answer not in choices:
        retry = _ask(f"  choose one of {', '.join(choices)}", default)
        if retry == answer:
            return default
        answer = retry
    return answer


# --------------------------------------------------------------------------------------
# config.toml rendering
# --------------------------------------------------------------------------------------


def render_config_toml(values: dict[str, Any]) -> str:
    """Render ``books/config.toml`` from resolved answers.

    Statutory keys (``fiscal_year_start``, ``assessment_year``) are emitted as
    commented placeholders when the user did not supply them — never guessed.
    """
    out: list[str] = []
    add = out.append

    add("# books/config.toml — TakaBooks")
    add(f"# {tb.ATTRIBUTION}")
    add("#")
    add("# Edit this by hand whenever you like; TakaBooks only ever reads it.")
    add("# Verify TIN/BIN against your NBR documents before filing anything.")
    add("")
    add("[business]")
    add(f"name = {_toml_string(values['business_name'])}")
    add(f"name_bn = {_toml_string(values['business_name_bn'])}          # নাম / name in Bangla")
    add(f"type = {_toml_string(values['business_type'])}"
        "          # proprietorship | partnership | company | ngo | other")
    add(f"tin = {_toml_string(values['tin'])}"
        "           # করদাতা সনাক্তকরণ নম্বর / Taxpayer's Identification Number")
    add(f"bin = {_toml_string(values['bin'])}"
        "           # ব্যবসা সনাক্তকরণ নম্বর / Business Identification Number (মূসক / VAT)")
    add(f"address = {_toml_string(values['address'])}")
    add("")
    add("[books]")
    add(f"currency = {_toml_string(values['currency'])}      # TakaBooks keeps books in BDT only")
    add("")
    add("# The day your income year opens, written MM-DD.  TakaBooks will NOT guess it:")
    add("# every report that needs a period refuses to run until this is set.")
    if values.get("fiscal_year_start"):
        add(f"fiscal_year_start = {_toml_string(values['fiscal_year_start'])}")
    else:
        add('# fiscal_year_start = "MM-DD"')
    add("")
    add(f"# {tb.term('assessment_year')} — as printed on your NBR return, e.g. \"2026-27\".")
    add("# Every tax output must state it, so tax scripts refuse to run without it.")
    if values.get("assessment_year"):
        add(f"assessment_year = {_toml_string(values['assessment_year'])}")
    else:
        add('# assessment_year = "YYYY-YY"')
    add("")
    add("# Machine-readable rates for that assessment year.  No rate is ever written")
    add("# into config.toml, prose or code — it all lives in this one file.")
    if values.get("rates_file"):
        add(f"rates_file = {_toml_string(values['rates_file'])}")
    else:
        add('# rates_file = "rates-AY<year>.toml"')
    add("")
    add(f"accounts_file = {_toml_string(values['accounts_file'])}")
    add(f"journal_dir = {_toml_string(values['journal_dirname'])}")
    add("")
    add("[locale]")
    add(f"language = {_toml_string(values['language'])}          # en | bn | bn-en")
    add(f"grouping = {_toml_string(values['grouping'])}"
        "          # bd = 12,34,567.89 (লাখ/কোটি) · international = 1,234,567.89")
    add(f"digits = {_toml_string(values['digits'])}         # latin | bangla")
    add("")
    add("[compliance]")
    add("# Recorded for your own reference and for the assistant's questions.")
    add("# TakaBooks attaches NO rate, threshold or deadline to these labels — every")
    add("# such figure comes from the assessment-year rates file, with its source URL.")
    add(f"vat_registered = {_toml_string(values['vat_registered'])}"
        "   # yes | no | unknown — মূসক নিবন্ধন / VAT registration")
    tier_bn, tier_en = CITY_TIERS[values["city_tier"]]
    add(f"city_tier = {_toml_string(values['city_tier'])}"
        f"   # {tier_bn} / {tier_en}")
    add("")
    return "\n".join(out)


def _template_defaults(templates_dir: Path | None, warnings: list[str]) -> dict[str, Any]:
    """Non-statutory defaults inherited from ``src/templates/config.toml``.

    Business identity is never inherited (it would be demo data) and neither are
    ``fiscal_year_start`` / ``assessment_year`` — copying a statutory value out of
    a template is exactly the kind of guess this project forbids.
    """
    defaults: dict[str, Any] = {
        "currency": tb.CURRENCY_CODE,
        "accounts_file": tb.ACCOUNTS_FILENAME,
        "journal_dirname": tb.JOURNAL_DIRNAME,
        "rates_file": "",
        "language": "en",
        "grouping": tb.GROUPING_BD,
        "digits": "latin",
        "source": "built-in defaults",
    }
    if templates_dir is None:
        return defaults
    path = templates_dir / TEMPLATE_CONFIG
    if not path.is_file():
        return defaults
    data = tb.load_toml(path)
    books = data.get("books", {}) or {}
    locale = data.get("locale", {}) or {}
    if not isinstance(books, dict) or not isinstance(locale, dict):
        raise tb.ConfigError(f"{path}: [books] and [locale] must be tables.")
    for key in ("fiscal_year_start", "assessment_year"):
        if books.get(key):
            warnings.append(
                f"{path} sets books.{key} = {books[key]!r}; init_books does not copy "
                f"statutory values into your books. Pass --{key.replace('_', '-')} to set it."
            )
    defaults["currency"] = str(books.get("currency", defaults["currency"]) or defaults["currency"])
    defaults["accounts_file"] = str(
        books.get("accounts_file", defaults["accounts_file"]) or defaults["accounts_file"]
    )
    defaults["journal_dirname"] = str(
        books.get("journal_dir", defaults["journal_dirname"]) or defaults["journal_dirname"]
    )
    defaults["rates_file"] = str(books.get("rates_file", "") or "")
    defaults["language"] = str(locale.get("language", defaults["language"]) or defaults["language"])
    defaults["grouping"] = str(locale.get("grouping", defaults["grouping"]) or defaults["grouping"])
    defaults["digits"] = str(locale.get("digits", defaults["digits"]) or defaults["digits"])
    defaults["source"] = str(path)
    return defaults


def _accounts_text(templates_dir: Path | None) -> tuple[str, str]:
    """``(toml_text, source_label)`` for the chart of accounts."""
    if templates_dir is not None:
        path = templates_dir / TEMPLATE_ACCOUNTS
        if path.is_file():
            try:
                return path.read_text(encoding="utf-8"), str(path)
            except (OSError, UnicodeDecodeError) as exc:
                raise tb.AccountError(f"Could not read {path}: {exc}") from None
    return FALLBACK_ACCOUNTS_TOML, "built-in Bangladesh chart of accounts"


def _journal_header_text(templates_dir: Path | None) -> str:
    """The journal header row, cross-checked against the schema in the library."""
    header = tb.JOURNAL_HEADER
    if templates_dir is not None:
        path = templates_dir / TEMPLATE_JOURNAL_HEADER
        if path.is_file():
            template_header = path.read_text(encoding="utf-8").strip().lstrip("\ufeff")
            if template_header != header:
                raise tb.JournalError(
                    f"{path}: journal header does not match the schema.",
                    hint=f"It must be exactly: {header}",
                )
    return header + "\n"


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = tb.common_parser(
        "init_books.py",
        "Scaffold a TakaBooks books/ directory — config.toml, "
        f"{tb.term('chart_of_accounts')}, journal/ and reports/.",
        epilog=(
            "Statutory values are never invented: fiscal_year_start and assessment_year\n"
            "(করবর্ষ) are written only when you pass them.\n\n"
            "exit codes: 0 ok · 1 general · 2 config/usage · 3 account · 4 journal\n\n"
            f"{tb.ATTRIBUTION}"
        ),
    )
    parser.add_argument("--name", default=None, metavar="TEXT", help="business name")
    parser.add_argument("--name-bn", default=None, metavar="TEXT",
                        help="business name in Bangla (নাম)")
    parser.add_argument("--business-type", default=None, metavar="TEXT",
                        help="proprietorship | partnership | company | ngo | other")
    parser.add_argument("--tin", default=None, metavar="TIN",
                        help="করদাতা সনাক্তকরণ নম্বর / Taxpayer's Identification Number")
    parser.add_argument("--bin", default=None, metavar="BIN",
                        help="ব্যবসা সনাক্তকরণ নম্বর / Business Identification Number (মূসক / VAT)")
    parser.add_argument("--address", default=None, metavar="TEXT", help="business address")
    parser.add_argument("--fiscal-year-start", default=None, metavar="MM-DD",
                        help="day the income year opens, e.g. 07-01 (never guessed)")
    parser.add_argument("--assessment-year", default=None, metavar="YYYY-YY",
                        help="করবর্ষ / assessment year, e.g. 2026-27 (never guessed)")
    parser.add_argument("--rates-file", default=None, metavar="FILE",
                        help="rates TOML for that assessment year, e.g. rates-AY2026-27.toml")
    parser.add_argument("--vat-registered", default=None, choices=VAT_REGISTRATION_CHOICES,
                        help="মূসক নিবন্ধন / VAT registration status (default: unknown)")
    parser.add_argument("--city-tier", default=None, choices=tuple(CITY_TIERS),
                        help="where the business is located (a label only; carries no figure)")
    parser.add_argument("--language", default=None, choices=("en", "bn", "bn-en"),
                        help="reply language recorded in [locale]")
    parser.add_argument("--grouping", default=None, choices=(tb.GROUPING_BD, tb.GROUPING_INTL),
                        help="digit grouping: bd = 12,34,567.89 (default)")
    parser.add_argument("--digits", default=None, choices=("latin", "bangla"),
                        help="numerals used in reports")
    parser.add_argument("--start-month", default=None, metavar="YYYY-MM",
                        help="also create an empty journal file for this month")
    parser.add_argument("--templates", default=None, metavar="DIR",
                        help="template directory (default: src/templates)")
    parser.add_argument("-i", "--interactive", action="store_true",
                        help="ask for anything not given on the command line")
    parser.add_argument("--force", action="store_true",
                        help="rewrite config.toml and accounts.toml "
                             "(existing journal CSVs are never touched)")
    parser.add_argument("--dry-run", action="store_true",
                        help="show what would be created and write nothing")
    return parser


def _resolve_values(args: argparse.Namespace, defaults: dict[str, Any]) -> dict[str, Any]:
    interactive = bool(args.interactive)

    def pick(value: Any, question: str, fallback: str = "") -> str:
        if value is not None:
            return str(value).strip()
        if interactive:
            return _ask(question, fallback).strip()
        return fallback

    values: dict[str, Any] = {
        "business_name": pick(args.name, "Business name"),
        "business_name_bn": pick(args.name_bn, "Business name in Bangla (নাম)"),
        "business_type": pick(
            args.business_type,
            "Business type (proprietorship/partnership/company/ngo/other)",
        ),
        "tin": pick(args.tin, "TIN / করদাতা সনাক্তকরণ নম্বর"),
        "bin": pick(args.bin, "BIN / ব্যবসা সনাক্তকরণ নম্বর"),
        "address": pick(args.address, "Address"),
        "currency": defaults["currency"],
        "accounts_file": defaults["accounts_file"],
        "journal_dirname": defaults["journal_dirname"],
    }

    fiscal = args.fiscal_year_start
    if fiscal is None and interactive:
        fiscal = _ask("Income year opens on (MM-DD, blank to fill in later)") or None
    values["fiscal_year_start"] = _check_month_day(fiscal) if fiscal else ""

    assessment = args.assessment_year
    if assessment is None and interactive:
        assessment = _ask(
            f"{tb.term('assessment_year')} (YYYY-YY, blank to fill in later)"
        ) or None
    values["assessment_year"] = _check_assessment_year(assessment) if assessment else ""

    rates_file = args.rates_file
    if rates_file is None and interactive:
        rates_file = _ask("Rates file", defaults["rates_file"]) or None
    values["rates_file"] = str(rates_file).strip() if rates_file else defaults["rates_file"]

    if args.vat_registered is not None:
        values["vat_registered"] = args.vat_registered
    elif interactive:
        values["vat_registered"] = _ask_choice(
            "মূসক / VAT registered", VAT_REGISTRATION_CHOICES, "unknown"
        )
    else:
        values["vat_registered"] = "unknown"

    if args.city_tier is not None:
        values["city_tier"] = args.city_tier
    elif interactive:
        values["city_tier"] = _ask_choice("Location", tuple(CITY_TIERS), "unspecified")
    else:
        values["city_tier"] = "unspecified"

    values["language"] = args.language or defaults["language"]
    values["grouping"] = args.grouping or defaults["grouping"]
    values["digits"] = args.digits or defaults["digits"]
    return values


def run(args: argparse.Namespace) -> dict[str, Any]:
    """Do the work.  Raises :class:`tb.TakaBooksError` on any refusal."""
    warnings: list[str] = []
    books_dir = Path(args.books)

    templates_dir: Path | None
    if args.templates is not None:
        templates_dir = Path(args.templates)
        if not templates_dir.is_dir():
            raise tb.ConfigError(f"Template directory not found: {templates_dir}")
    else:
        candidate = default_templates_dir()
        templates_dir = candidate if candidate.is_dir() else None

    defaults = _template_defaults(templates_dir, warnings)
    values = _resolve_values(args, defaults)

    # ---- render and validate BEFORE anything is written ------------------------------
    config_text = render_config_toml(values)
    try:
        parsed = tomllib.loads(config_text)
    except tomllib.TOMLDecodeError as exc:  # pragma: no cover - our own renderer
        raise tb.ConfigError(f"Generated config.toml is not valid TOML: {exc}") from None
    config = tb.Config.from_mapping(parsed, source_path=tb.config_path(books_dir))

    accounts_text, accounts_source = _accounts_text(templates_dir)
    chart = tb.ChartOfAccounts.from_toml_bytes(
        accounts_text.encode("utf-8"), source_path=accounts_source
    )
    missing_roles = chart.missing_roles()
    if missing_roles:
        warnings.append(
            "chart of accounts is missing spec §4.4 role(s): "
            + ", ".join(missing_roles)
            + " — VAT/TDS reporting cannot find those accounts until you add "
              'a role = "..." key to them.'
        )
    warnings.extend(chart.code_format_warnings())
    warnings.extend(chart.block_warnings())

    if values["assessment_year"] and values["rates_file"]:
        year = values["assessment_year"]
        if year not in values["rates_file"] and year.replace("-", "") not in values["rates_file"]:
            warnings.append(
                f"books.rates_file = {values['rates_file']!r} does not name assessment year "
                f"{year!r}; check you are pointing at the right rates file."
            )

    # ---- overwrite policy ------------------------------------------------------------
    config_file = tb.config_path(books_dir)
    accounts_file = books_dir / values["accounts_file"]
    journal_directory = tb.journal_dir(books_dir, values["journal_dirname"])
    reports_directory = books_dir / REPORTS_DIRNAME

    occupied = [p for p in (config_file, accounts_file) if p.exists()]
    existing_journals = (
        sorted(p.name for p in journal_directory.glob("*.csv"))
        if journal_directory.is_dir()
        else []
    )
    if (occupied or existing_journals) and not args.force:
        found = ", ".join([p.name for p in occupied] + [f"journal/{n}" for n in existing_journals])
        raise tb.ConfigError(
            f"{books_dir} already holds books ({found}); refusing to overwrite them.",
            hint="Pass --force to rewrite config.toml and accounts.toml (journal CSV files "
            "are never touched), or scaffold somewhere else with --books DIR.",
        )

    start_month = _check_month(args.start_month) if args.start_month else ""
    seed_journal = journal_directory / f"{start_month}.csv" if start_month else None
    header_text = _journal_header_text(templates_dir) if start_month else ""
    if seed_journal is not None and seed_journal.exists():
        warnings.append(f"{seed_journal} already exists; leaving it exactly as it is.")
        seed_journal = None

    created: list[str] = []
    overwritten: list[str] = []
    for directory in (books_dir, journal_directory, reports_directory):
        if not directory.exists():
            created.append(str(directory) + "/")
    for target in (config_file, accounts_file):
        (overwritten if target.exists() else created).append(str(target))
    if seed_journal is not None:
        created.append(str(seed_journal))

    result: dict[str, Any] = {
        "ok": True,
        "dry_run": bool(args.dry_run),
        "books_dir": str(books_dir),
        "created": created,
        "overwritten": overwritten,
        "config_file": str(config_file),
        "accounts_file": str(accounts_file),
        "journal_dir": str(journal_directory),
        "reports_dir": str(reports_directory),
        "templates_dir": str(templates_dir) if templates_dir else "",
        "config_defaults_from": defaults["source"],
        "accounts_from": accounts_source,
        "accounts": len(chart),
        "roles_present": sorted(a.role for a in chart if a.role),
        "missing_roles": missing_roles,
        "fiscal_year_start": values["fiscal_year_start"],
        "assessment_year": values["assessment_year"],
        "vat_registered": values["vat_registered"],
        "city_tier": values["city_tier"],
        "business_name": config.display_name,
        "warnings": warnings,
        "attribution": tb.ATTRIBUTION,
    }

    if args.dry_run:
        result["config_preview"] = config_text
        result["accounts_preview_lines"] = len(accounts_text.splitlines())
        return result

    # ---- write -----------------------------------------------------------------------
    tb.ensure_dir(books_dir)
    tb.write_text_atomic(config_file, config_text)
    tb.write_text_atomic(accounts_file, accounts_text)
    tb.ensure_dir(journal_directory)
    tb.ensure_dir(reports_directory)
    if seed_journal is not None:
        tb.write_text_atomic(seed_journal, header_text)

    # ---- read back, so we never claim success on something unreadable ----------------
    written_config = tb.Config.load(books_dir)
    written_chart = tb.ChartOfAccounts.from_toml_path(accounts_file)
    result["accounts"] = len(written_chart)
    result["business_name"] = written_config.display_name
    return result


def _render_text(result: dict[str, Any]) -> str:
    lines: list[str] = []
    verb = "would create" if result["dry_run"] else "created"
    head = "dry run — nothing was written" if result["dry_run"] else "books ready"
    lines.append(f"TakaBooks — {head}: {result['books_dir']}")
    lines.append(f"  business        {result['business_name']}")
    lines.append(
        f"  {tb.term('chart_of_accounts')}  {result['accounts']} accounts "
        f"from {result['accounts_from']}"
    )
    fiscal = result["fiscal_year_start"] or "(not set — fill it in before any report)"
    year = result["assessment_year"] or "(not set — fill it in before any tax output)"
    lines.append(f"  income year opens  {fiscal}")
    lines.append(f"  {tb.term('assessment_year')}  {year}")
    lines.append(f"  মূসক / VAT registered  {result['vat_registered']}")
    tier_bn, tier_en = CITY_TIERS[result["city_tier"]]
    lines.append(f"  location        {tier_bn} / {tier_en}")
    lines.append("")
    if result["created"]:
        lines.append(f"{verb}:")
        lines.extend(f"  {path}" for path in result["created"])
    if result["overwritten"]:
        lines.append("would overwrite:" if result["dry_run"] else "overwritten:")
        lines.extend(f"  {path}" for path in result["overwritten"])
        lines.append("  (journal CSV files were left untouched)")
    lines.append("")
    lines.append("next steps:")
    step = 1
    if not result["fiscal_year_start"]:
        lines.append(
            f"  {step}. Set books.fiscal_year_start (MM-DD) in "
            f"{result['config_file']} — TakaBooks will not guess your income year."
        )
        step += 1
    if not result["assessment_year"]:
        lines.append(
            f"  {step}. Set books.assessment_year ({tb.term('assessment_year')}) — "
            "every tax output must state it."
        )
        step += 1
    lines.append(f"  {step}. Check TIN/BIN and the chart of accounts against your own records.")
    step += 1
    lines.append(
        f"  {step}. Record your first entry:  python3 src/engine/post.py "
        f"--books {result['books_dir']} --date YYYY-MM-DD --description '...' "
        "--debit 1100=1000.00 --credit 4100=1000.00"
    )
    lines.append("")
    lines.append(result["attribution"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    with tb.cli_guard(json_output=args.json):
        result = run(args)
        for warning in result["warnings"]:
            sys.stderr.write(f"warning: {warning}\n")
        if args.json:
            sys.stdout.write(tb.json_dumps(result) + "\n")
        else:
            sys.stdout.write(_render_text(result) + "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
