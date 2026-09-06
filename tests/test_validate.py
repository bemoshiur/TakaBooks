"""Tests for ``src/engine/validate.py`` — the whole-ledger integrity checker.

Run with::

    python3 -m unittest discover tests

Spec §7: unknown account, duplicate entry_id, malformed date and bad tax_tag must all
fail loudly.  Every finding here is checked for the file, line and entry_id it names,
and the exit code is asserted to be 0 only when the ledger is fully clean.

The rates and section numbers written into fixture ``tax_tag`` cells (``VAT:OUT:10``,
``TDS:52:3`` …) are arbitrary test values, not statutory Bangladeshi figures: the
validator only checks that a tag parses and sits on a sensible account.  Likewise the
``fiscal_year_start = "07-01"`` in the fixture config is a value *read from* the
config, never a default the code assumes.

TakaBooks — Moshiur Rahman (@bemoshiur) · Ticon Sys — https://ticonsys.com
"""

from __future__ import annotations

import contextlib
import datetime
import io
import json
import re
import sys
import tempfile
import tokenize
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = REPO_ROOT / "src" / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import takabooks as tb  # noqa: E402
import validate  # noqa: E402

M = tb.Money
HEADER = tb.JOURNAL_HEADER

#: Every check slug some test observed in a report — the coverage invariant at the end.
SEEN_CHECKS: set[str] = set()

# --------------------------------------------------------------------------------------
# Fixture material
# --------------------------------------------------------------------------------------

ROLES = {
    "1310": tb.ROLE_VAT_INPUT,
    "1320": tb.ROLE_TDS_RECEIVABLE,
    "1330": tb.ROLE_ADVANCE_INCOME_TAX,
    "2210": tb.ROLE_VAT_OUTPUT,
    "2220": tb.ROLE_TDS_PAYABLE,
    "2230": tb.ROLE_VDS_PAYABLE,
    "2240": tb.ROLE_SUPPLEMENTARY_DUTY_PAYABLE,
    "2310": tb.ROLE_PROVIDENT_FUND_PAYABLE,
    "2320": tb.ROLE_GRATUITY_PROVISION,
    "2330": tb.ROLE_WPPF_PAYABLE,
}

ACCOUNTS = [
    ("1100", "Cash in Hand", "asset", "debit"),
    ("1200", "Accounts Receivable", "asset", "debit"),
    ("1310", "VAT Input Rebateable", "asset", "debit"),
    ("1320", "TDS Receivable", "asset", "debit"),
    ("1330", "Advance Income Tax", "asset", "debit"),
    ("2100", "Accounts Payable", "liability", "credit"),
    ("2210", "VAT Output Payable", "liability", "credit"),
    ("2220", "TDS Payable", "liability", "credit"),
    ("2230", "VDS Payable", "liability", "credit"),
    ("2240", "Supplementary Duty Payable", "liability", "credit"),
    ("2310", "Provident Fund Payable", "liability", "credit"),
    ("2320", "Gratuity Provision", "liability", "credit"),
    ("2330", "WPPF Payable", "liability", "credit"),
    ("3100", "Owner Capital", "equity", "credit"),
    ("4100", "Sales", "income", "credit"),
    ("6100", "Office Rent", "expense", "debit"),
    ("6900", "Old Sundry Expense", "expense", "debit"),
]

DEFAULT_TAGS = {"6900": ["inactive"]}


def accounts_toml(*, accounts=ACCOUNTS, roles=ROLES, tags=DEFAULT_TAGS, extra: str = "") -> str:
    out: list[str] = []
    for code, name, kind, normal in accounts:
        out.append(f'[[account]]\ncode = "{code}"\nname = "{name}"\ntype = "{kind}"\nnormal = "{normal}"')
        if code == "1100":
            out.append('name_bn = "হাতে নগদ"')
        if code in roles:
            out.append(f'role = "{roles[code]}"')
        if code in tags:
            out.append("tags = [" + ", ".join(f'"{t}"' for t in tags[code]) + "]")
        out.append("")
    return "\n".join(out) + extra


def config_toml(
    *,
    fiscal_year_start: str | None = "07-01",
    assessment_year: str | None = "2026-27",
    language: str = "en",
    journal_dir: str | None = None,
    extra: str = "",
) -> str:
    lines = [
        "[business]",
        'name = "Demo Traders"',
        'name_bn = "ডেমো ট্রেডার্স"',
        'tin = "000000000000"',
        "",
        "[books]",
        'currency = "BDT"',
    ]
    if fiscal_year_start:
        lines.append(f'fiscal_year_start = "{fiscal_year_start}"')
    if assessment_year:
        lines.append(f'assessment_year = "{assessment_year}"')
    if journal_dir:
        lines.append(f'journal_dir = "{journal_dir}"')
    lines += ["", "[locale]", f'language = "{language}"', ""]
    return "\n".join(lines) + extra


def row(
    date: str,
    entry_id: str,
    account: str,
    debit: str = "",
    credit: str = "",
    tag: str = "NONE",
    *,
    desc: str = "test",
    party: str = "",
    ref: str = "",
    memo: str = "",
) -> str:
    return ",".join([date, entry_id, desc, account, debit, credit, party, ref, tag, memo])


def entry(date: str, entry_id: str, dr: str, cr: str, amount: str, *, dr_tag="NONE", cr_tag="NONE") -> list[str]:
    """A balanced two-line entry."""
    return [row(date, entry_id, dr, amount, "", dr_tag), row(date, entry_id, cr, "", amount, cr_tag)]


CLEAN_ROWS = [
    row("2026-07-01", "OPEN-001", "1100", "100000.00", "0.00", desc="Opening capital"),
    row("2026-07-01", "OPEN-001", "3100", "0.00", "100000.00", desc="Opening capital"),
    row("2026-07-05", "SALE-001", "1100", "11000.00", "", desc="Cash sale", party="Walk-in", ref="INV-1"),
    row("2026-07-05", "SALE-001", "4100", "", "10000.00", "VAT:OUT:10", desc="Cash sale"),
    row("2026-07-05", "SALE-001", "2210", "", "1000.00", "VAT:OUT:10", desc="Cash sale"),
    row("2026-07-10", "RENT-001", "6100", "20000.00", "", "TDS:52:3", desc="July rent", memo="memo with, a comma"),
    row("2026-07-10", "RENT-001", "2220", "", "600.00", "TDS:52:3", desc="July rent"),
    row("2026-07-10", "RENT-001", "1100", "", "19400.00", desc="July rent"),
]
CLEAN_TOTAL = M(13100000)  # ৳1,31,000.00 of debits (and of credits)


class BooksCase(unittest.TestCase):
    """A temporary ``books/`` directory with a valid config and chart, ready to dirty."""

    def setUp(self) -> None:
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        self.books = self.root / "books"
        self.journal = self.books / "journal"
        self.journal.mkdir(parents=True)
        self.write_config()
        self.write_accounts()

    def tearDown(self) -> None:
        self.dir.cleanup()

    # -- writers -----------------------------------------------------------------------

    def write_config(self, text: str | None = None, **kwargs) -> None:
        (self.books / "config.toml").write_text(text if text is not None else config_toml(**kwargs), encoding="utf-8")

    def write_accounts(self, text: str | None = None, **kwargs) -> None:
        (self.books / "accounts.toml").write_text(text if text is not None else accounts_toml(**kwargs), encoding="utf-8")

    def write_journal(self, name: str, rows, *, header: str | None = HEADER, newline: str = "\n", bom: bool = False) -> Path:
        lines = ([header] if header is not None else []) + list(rows)
        text = newline.join(lines) + newline
        path = self.journal / name
        path.write_bytes((("\ufeff" if bom else "") + text).encode("utf-8"))
        return path

    # -- running -----------------------------------------------------------------------

    def run_validate(self, **kwargs) -> validate.ValidationReport:
        report = validate.validate_books(self.books, **kwargs)
        SEEN_CHECKS.update(f.check for f in report.findings)
        return report

    def run_main(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        try:
            code = validate.main(list(argv), stdout=out, stderr=err)
        except SystemExit as exc:
            code = exc.code
        return code, out.getvalue(), err.getvalue()

    # -- assertions --------------------------------------------------------------------

    @staticmethod
    def slugs(report: validate.ValidationReport) -> list[str]:
        return sorted({f.check for f in report.findings})

    @staticmethod
    def find(report: validate.ValidationReport, slug: str) -> list[validate.Finding]:
        return [f for f in report.findings if f.check == slug]

    def assertOnly(self, report: validate.ValidationReport, *slugs: str) -> None:
        self.assertEqual(self.slugs(report), sorted(set(slugs)), [f.render() for f in report.findings])

    def assertHas(self, report: validate.ValidationReport, slug: str, count: int | None = None) -> list[validate.Finding]:
        found = self.find(report, slug)
        self.assertTrue(found, f"expected {slug!r}; got {self.slugs(report)}")
        if count is not None:
            self.assertEqual(len(found), count, [f.render() for f in found])
        return found

    def assertLacks(self, report: validate.ValidationReport, slug: str) -> None:
        self.assertFalse(self.find(report, slug), [f.render() for f in self.find(report, slug)])


# ======================================================================================
# The catalogue of checks
# ======================================================================================


class TestCatalogue(unittest.TestCase):
    def test_slugs_are_unique_and_kebab_case(self):
        slugs = [c.slug for c in validate.CHECKS]
        self.assertEqual(len(slugs), len(set(slugs)))
        for slug in slugs:
            self.assertRegex(slug, r"^[a-z][a-z0-9-]+$")

    def test_every_check_has_a_valid_severity_and_summary(self):
        for check in validate.CHECKS:
            self.assertIn(check.severity, validate.SEVERITIES)
            self.assertTrue(check.summary.strip())

    def test_lookup_table_matches_the_tuple(self):
        self.assertEqual(set(validate.CHECKS_BY_SLUG), {c.slug for c in validate.CHECKS})
        for check in validate.CHECKS:
            self.assertIs(validate.CHECKS_BY_SLUG[check.slug], check)

    def test_bad_severity_is_refused(self):
        with self.assertRaises(ValueError):
            validate.Check("x", "fatal", "nope")

    def test_every_finding_built_in_source_uses_a_declared_slug(self):
        source = (ENGINE_DIR / "validate.py").read_text(encoding="utf-8")
        used = set(re.findall(r'_finding\(\s*"([a-z0-9-]+)"', source))
        self.assertTrue(used)
        self.assertEqual(used - set(validate.CHECKS_BY_SLUG), set())

    def test_render_checks_lists_every_slug_grouped_by_severity(self):
        text = validate.render_checks()
        for check in validate.CHECKS:
            self.assertIn(check.slug, text)
        self.assertLess(text.index("ERRORS"), text.index("WARNINGS"))
        self.assertIn(tb.ATTRIBUTION, text)

    def test_exit_code_for_findings_is_the_validation_error_code(self):
        self.assertEqual(validate.FINDINGS_EXIT_CODE, tb.ValidationError.exit_code)
        self.assertNotEqual(validate.FINDINGS_EXIT_CODE, 0)

    def test_no_float_anywhere_in_the_validator(self):
        with tokenize.open(ENGINE_DIR / "validate.py") as handle:
            names = [t.string for t in tokenize.generate_tokens(handle.readline) if t.type == tokenize.NAME]
        self.assertNotIn("float", names)

    def test_public_api_names_exist(self):
        for name in validate.__all__:
            self.assertTrue(hasattr(validate, name), name)


# ======================================================================================
# Financial-year arithmetic (pure calendar, no statutory assumption)
# ======================================================================================


class TestFiscalYear(unittest.TestCase):
    D = datetime.date

    def test_window_for_a_july_year(self):
        self.assertEqual(validate.fiscal_year_window(self.D(2026, 7, 1), 7, 1), (self.D(2026, 7, 1), self.D(2027, 6, 30)))
        self.assertEqual(validate.fiscal_year_window(self.D(2027, 6, 30), 7, 1), (self.D(2026, 7, 1), self.D(2027, 6, 30)))
        self.assertEqual(validate.fiscal_year_window(self.D(2026, 6, 30), 7, 1), (self.D(2025, 7, 1), self.D(2026, 6, 30)))

    def test_window_for_a_calendar_year(self):
        self.assertEqual(validate.fiscal_year_window(self.D(2026, 3, 15), 1, 1), (self.D(2026, 1, 1), self.D(2026, 12, 31)))

    def test_start_for_boundary_days(self):
        self.assertEqual(validate.fiscal_year_start_for(self.D(2026, 7, 1), 7, 1), self.D(2026, 7, 1))
        self.assertEqual(validate.fiscal_year_start_for(self.D(2026, 6, 30), 7, 1), self.D(2025, 7, 1))

    def test_leap_day_start_survives_a_common_year(self):
        start, end = validate.fiscal_year_window(self.D(2025, 3, 1), 2, 29)
        self.assertEqual(start, self.D(2025, 2, 28))
        self.assertEqual(end, self.D(2026, 2, 27))

    def test_majority_ignores_a_stray_backdated_row(self):
        dates = [self.D(2026, 7, d) for d in range(1, 10)] + [self.D(2025, 6, 30)]
        window, inside, total = validate.majority_fiscal_year(dates, 7, 1)
        self.assertEqual(window, (self.D(2026, 7, 1), self.D(2027, 6, 30)))
        self.assertEqual((inside, total), (9, 10))

    def test_majority_tie_goes_to_the_later_year(self):
        dates = [self.D(2025, 8, 1), self.D(2026, 8, 1)]
        window, inside, total = validate.majority_fiscal_year(dates, 7, 1)
        self.assertEqual(window[0], self.D(2026, 7, 1))
        self.assertEqual((inside, total), (1, 2))

    def test_majority_needs_a_date(self):
        with self.assertRaises(ValueError):
            validate.majority_fiscal_year([], 7, 1)


# ======================================================================================
# Finding
# ======================================================================================


class TestFinding(unittest.TestCase):
    def make(self, **kw) -> validate.Finding:
        base = dict(severity="error", check="bad-date", message="msg")
        base.update(kw)
        return validate.Finding(**base)

    def test_location_variants(self):
        self.assertEqual(self.make().location, "")
        self.assertEqual(self.make(file="books/journal/2026-07.csv").location, "books/journal/2026-07.csv")
        self.assertEqual(self.make(file="j.csv", line=4).location, "j.csv line 4")
        self.assertEqual(self.make(file="j.csv", line=3, end_line=4).location, "j.csv lines 3–4")
        self.assertEqual(self.make(file="j.csv", line=3, end_line=3).location, "j.csv line 3")

    def test_where_adds_the_entry_id(self):
        self.assertEqual(self.make(file="j.csv", line=2, entry_id="X").where, "j.csv line 2 · entry X")
        self.assertEqual(self.make(entry_id="X").where, "entry X")

    def test_render_and_to_dict(self):
        f = self.make(file="j.csv", line=2, entry_id="X", hint="fix it", amount=M(150))
        text = f.render()
        self.assertTrue(text.startswith("[bad-date] j.csv line 2 · entry X"))
        self.assertIn("hint: fix it", text)
        d = f.to_dict()
        self.assertEqual(d["line"], 2)
        self.assertIsNone(d["end_line"])
        self.assertEqual(d["amount"], M(150))
        self.assertEqual(d["location"], "j.csv line 2")
        self.assertTrue(f.is_error)

    def test_sort_puts_errors_first_then_config_level_then_by_file_and_line(self):
        a = self.make(severity="warning", check="x", file="a.csv", line=1)
        b = self.make(severity="error", check="x", file="b.csv", line=9)
        c = self.make(severity="error", check="x")  # no file: config-level
        d = self.make(severity="error", check="x", file="b.csv", line=2)
        ordered = sorted([a, b, c, d], key=lambda f: f.sort_key())
        self.assertEqual(ordered, [c, d, b, a])


# ======================================================================================
# Clean books
# ======================================================================================


class TestCleanBooks(BooksCase):
    def setUp(self) -> None:
        super().setUp()
        self.write_journal("2026-07.csv", CLEAN_ROWS)

    def test_clean_books_have_no_findings_and_exit_zero(self):
        report = self.run_validate()
        self.assertOnly(report)
        self.assertTrue(report.is_clean)
        self.assertEqual(report.exit_code(), 0)
        self.assertEqual(report.counts()["errors"], 0)
        self.assertEqual(report.postings_checked, 8)
        self.assertEqual(report.rows_read, 8)
        self.assertEqual(report.entries, 3)
        self.assertEqual(report.total_debit, CLEAN_TOTAL)
        self.assertEqual(report.total_credit, CLEAN_TOTAL)
        self.assertEqual(report.difference, M.zero())
        self.assertEqual(report.first_date, datetime.date(2026, 7, 1))
        self.assertEqual(report.last_date, datetime.date(2026, 7, 10))

    def test_clean_books_also_load_strictly_through_the_library(self):
        ledger = tb.Ledger.load(self.books)  # require_balanced=True: must not raise
        self.assertEqual(len(ledger), 8)

    def test_financial_year_comes_from_config_and_says_so(self):
        report = self.run_validate()
        self.assertEqual(report.financial_year, (datetime.date(2026, 7, 1), datetime.date(2027, 6, 30)))
        self.assertIn("07-01", report.financial_year_source)
        self.assertIn("all 8", report.financial_year_source)

    def test_memo_commas_survive(self):
        report = self.run_validate()
        ledger = tb.Ledger.load(self.books)
        rent = [p for p in ledger.postings if p.entry_id == "RENT-001" and p.account == "6100"][0]
        self.assertEqual(rent.memo, "memo with, a comma")
        self.assertTrue(report.is_clean)

    def test_text_report_states_the_assessment_year_and_ends_with_the_disclaimer(self):
        text = validate.render_text(self.run_validate())
        self.assertIn("2026-27", text)
        self.assertIn(tb.term("assessment_year"), text)
        self.assertIn(tb.ATTRIBUTION, text)
        self.assertIn("RESULT: clean", text)
        self.assertIn("৳1,31,000.00", text)  # লাখ grouping, symbol on
        self.assertTrue(text.rstrip().endswith(tb.DISCLAIMER_EN))
        self.assertNotIn(tb.DISCLAIMER_BN, text)

    def test_bangla_locale_adds_the_bangla_disclaimer(self):
        self.write_config(language="bn")
        text = validate.render_text(self.run_validate())
        self.assertIn(tb.DISCLAIMER_EN, text)
        self.assertTrue(text.rstrip().endswith(tb.DISCLAIMER_BN))

    def test_quiet_is_one_line(self):
        text = validate.render_text(self.run_validate(), quiet=True)
        self.assertEqual(len(text.splitlines()), 1)
        self.assertTrue(text.startswith("RESULT: clean"))

    def test_json_is_machine_readable_and_never_uses_floats(self):
        payload = json.loads(validate.render_json(self.run_validate()))
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["exit_code"], 0)
        self.assertEqual(payload["findings"], [])
        self.assertEqual(payload["by_check"], {})
        self.assertEqual(payload["totals"], {"debit": "131000.00", "credit": "131000.00", "difference": "0.00"})
        self.assertEqual(payload["assessment_year"], "2026-27")
        self.assertEqual(payload["financial_year"]["start"], "2026-07-01")
        self.assertEqual(payload["date_range"], {"first": "2026-07-01", "last": "2026-07-10"})
        self.assertEqual(payload["business"]["name_bn"], "ডেমো ট্রেডার্স")
        self.assertEqual(payload["disclaimer"], {"en": tb.DISCLAIMER_EN, "bn": tb.DISCLAIMER_BN})
        self.assertEqual(payload["attribution"], tb.ATTRIBUTION)
        self.assertEqual(payload["counts"]["postings_checked"], 8)

    def test_bom_crlf_comments_and_blank_lines_are_tolerated(self):
        rows = ["# a comment line", ""] + CLEAN_ROWS[:2] + ["", "   ", "# another"] + CLEAN_ROWS[2:]
        self.write_journal("2026-07.csv", rows, newline="\r\n", bom=True)
        report = self.run_validate()
        self.assertOnly(report)
        self.assertEqual(report.postings_checked, 8)

    def test_header_case_and_trailing_empty_columns_are_tolerated(self):
        self.write_journal("2026-07.csv", CLEAN_ROWS, header=HEADER.upper() + ",,")
        self.assertOnly(self.run_validate())

    def test_multiple_files_in_order_are_clean(self):
        self.write_journal("2026-08.csv", entry("2026-08-03", "AUG-1", "6100", "1100", "500.00"))
        report = self.run_validate()
        self.assertOnly(report)
        self.assertEqual(len(report.journal_files), 2)
        self.assertEqual(report.entries, 4)
        self.assertEqual(report.notes, [])

    def test_month_gap_is_a_note_not_a_finding(self):
        self.write_journal("2026-10.csv", entry("2026-10-03", "OCT-1", "6100", "1100", "500.00"))
        report = self.run_validate()
        self.assertOnly(report)
        self.assertEqual(report.exit_code(), 0)
        self.assertEqual(len(report.notes), 1)
        self.assertIn("2026-08, 2026-09", report.notes[0])

    def test_ok_and_exit_code_with_allow_warnings(self):
        report = self.run_validate()
        self.assertTrue(report.ok())
        self.assertTrue(report.ok(allow_warnings=True))
        self.assertEqual(report.exit_code(allow_warnings=True), 0)


# ======================================================================================
# Row-level checks — each finding names file, line and entry_id
# ======================================================================================


class TestRowLevel(BooksCase):
    def one_bad_row(self, bad: str, *, slug: str, entry_id: str = "BAD-1") -> validate.Finding:
        """Write clean rows plus one broken row on line 10; return the finding for it."""
        self.write_journal("2026-07.csv", CLEAN_ROWS + [bad])
        report = self.run_validate()
        found = self.assertHas(report, slug, 1)[0]
        self.assertTrue(found.file.endswith("books/journal/2026-07.csv"), found.file)
        self.assertEqual(found.line, 10)
        self.assertEqual(found.entry_id, entry_id)
        self.assertTrue(found.is_error)
        self.assertEqual(report.exit_code(), validate.FINDINGS_EXIT_CODE)
        return found

    def test_bad_date_is_reported_not_raised(self):
        f = self.one_bad_row(row("2026-7-6", "BAD-1", "1100", "5.00"), slug="bad-date")
        self.assertIn("'2026-7-6'", f.message)
        self.assertIn("YYYY-MM-DD", f.hint)

    def test_impossible_calendar_date(self):
        f = self.one_bad_row(row("2026-02-30", "BAD-1", "1100", "5.00"), slug="bad-date")
        self.assertIn("2026-02-30", f.message)

    def test_non_iso_date_formats_are_rejected(self):
        for text in ("20260715", "15-07-2026", "15/07/2026"):
            with self.subTest(text=text):
                self.write_journal("2026-07.csv", [row(text, "BAD-1", "1100", "5.00"), row(text, "BAD-1", "4100", "", "5.00")])
                self.assertHas(self.run_validate(), "bad-date", 2)

    def test_blank_entry_id(self):
        self.write_journal("2026-07.csv", CLEAN_ROWS + [row("2026-07-11", "", "1100", "5.00")])
        report = self.run_validate()
        f = self.assertHas(report, "missing-entry-id", 1)[0]
        self.assertEqual((f.line, f.entry_id, f.account), (10, "", "1100"))
        self.assertLacks(report, "orphan-entry")  # it belongs to no entry, so no second finding

    def test_blank_account(self):
        f = self.one_bad_row(row("2026-07-11", "BAD-1", "", "5.00"), slug="missing-account")
        self.assertIn("blank", f.message)

    def test_unreadable_amount(self):
        f = self.one_bad_row(row("2026-07-11", "BAD-1", "1100", "abc"), slug="bad-amount")
        self.assertIn("'abc'", f.message)
        self.assertEqual(f.account, "1100")

    def test_negative_amount_states_the_amount(self):
        f = self.one_bad_row(row("2026-07-11", "BAD-1", "1100", "-50.00"), slug="negative-amount")
        self.assertIn("-৳50.00", f.message)
        self.assertEqual(f.amount, M(-5000))
        f = self.one_bad_row(row("2026-07-11", "BAD-1", "1100", "", "(25.00)"), slug="negative-amount")
        self.assertIn("credit", f.message)
        self.assertEqual(f.amount, M(-2500))

    def test_both_sides_set(self):
        f = self.one_bad_row(row("2026-07-11", "BAD-1", "1100", "10.00", "10.00"), slug="both-sides")
        self.assertIn("৳10.00", f.message)

    def test_neither_side_set(self):
        f = self.one_bad_row(row("2026-07-11", "BAD-1", "1100", "0.00", "0.00"), slug="no-amount")
        self.assertIn("৳0.00", f.message)
        self.one_bad_row(row("2026-07-11", "BAD-1", "1100", "", ""), slug="no-amount")

    def test_malformed_tax_tag_gets_the_grammar_as_hint(self):
        for tag in ("VAT:15", "VAT:OUT", "TDS:5", "VDS", "GST:15", "VAT:OUT:150"):
            with self.subTest(tag=tag):
                f = self.one_bad_row(row("2026-07-11", "BAD-1", "4100", "", "5.00", tag), slug="bad-tax-tag")
                self.assertEqual(f.hint, tb.TAX_TAG_GRAMMAR)
                self.assertIn("tax_tag", f.message)

    def test_short_row(self):
        f = self.one_bad_row("2026-07-11,BAD-1,too few", slug="row-fields")
        self.assertIn("3 field(s)", f.message)
        self.assertIn(HEADER, f.hint)

    def test_one_row_with_several_faults_reports_each(self):
        self.write_journal("2026-07.csv", CLEAN_ROWS + [row("bad", "BAD-1", "", "-1", "", "NOPE")])
        report = self.run_validate()
        self.assertEqual(
            {f.check for f in report.findings if f.line == 10},
            {"bad-date", "missing-account", "negative-amount", "bad-tax-tag"},
        )
        self.assertEqual(len([f for f in report.findings if f.line == 10]), 4)

    def test_a_damaged_entry_skips_the_balance_check_with_a_note(self):
        rows = CLEAN_ROWS + [row("2026-07-11", "DMG-1", "1100", "abc"), row("2026-07-11", "DMG-1", "4100", "", "5.00")]
        self.write_journal("2026-07.csv", rows)
        report = self.run_validate()
        self.assertOnly(report, "bad-amount")
        self.assertTrue(any("DMG-1" in n and "could not be read" in n for n in report.notes), report.notes)


# ======================================================================================
# Accounts and the chart
# ======================================================================================


class TestAccounts(BooksCase):
    def test_unknown_account_is_an_error_pinned_to_its_row(self):
        self.write_journal("2026-07.csv", CLEAN_ROWS + entry("2026-07-11", "UNK-1", "9999", "1100", "10.00"))
        report = self.run_validate()
        f = self.assertHas(report, "unknown-account", 1)[0]
        self.assertEqual((f.line, f.entry_id, f.account), (10, "UNK-1", "9999"))
        self.assertIn("'9999'", f.message)
        self.assertIn("accounts.toml", f.message)
        self.assertTrue(f.is_error)

    def test_inactive_account_is_a_warning(self):
        self.write_journal("2026-07.csv", CLEAN_ROWS + entry("2026-07-11", "OLD-1", "6900", "1100", "10.00"))
        report = self.run_validate()
        f = self.assertHas(report, "inactive-account", 1)[0]
        self.assertEqual(f.severity, validate.SEVERITY_WARNING)
        self.assertEqual((f.line, f.entry_id, f.account), (10, "OLD-1", "6900"))
        self.assertIn("'inactive'", f.message)
        self.assertEqual(report.exit_code(), validate.FINDINGS_EXIT_CODE)
        self.assertEqual(report.exit_code(allow_warnings=True), 0)

    def test_every_inactive_tag_spelling_counts(self):
        for tag in validate.INACTIVE_TAGS:
            with self.subTest(tag=tag):
                self.write_accounts(tags={"6900": [tag.upper()]})
                self.write_journal("2026-07.csv", entry("2026-07-11", "OLD-1", "6900", "1100", "10.00"))
                self.assertHas(self.run_validate(), "inactive-account", 1)

    def test_missing_required_role_is_a_warning_naming_the_role(self):
        roles = {code: role for code, role in ROLES.items() if role != tb.ROLE_WPPF_PAYABLE}
        self.write_accounts(roles=roles)
        self.write_journal("2026-07.csv", CLEAN_ROWS)
        report = self.run_validate()
        f = self.assertHas(report, "missing-required-role", 1)[0]
        self.assertIn(tb.ROLE_WPPF_PAYABLE, f.message)
        self.assertTrue(f.file.endswith("accounts.toml"))
        self.assertEqual(f.severity, validate.SEVERITY_WARNING)

    def test_chart_code_format_and_block_warnings_are_surfaced(self):
        extra = (
            '[[account]]\ncode = "A1"\nname = "Odd code"\ntype = "asset"\nnormal = "debit"\n\n'
            '[[account]]\ncode = "5100"\nname = "Misfiled income"\ntype = "income"\nnormal = "credit"\n'
        )
        self.write_accounts(extra=extra)
        self.write_journal("2026-07.csv", CLEAN_ROWS)
        report = self.run_validate()
        self.assertHas(report, "chart-code-format", 1)
        self.assertHas(report, "chart-block")
        self.assertIn("'A1'", self.find(report, "chart-code-format")[0].message)

    def test_unreadable_chart_is_an_error_but_balance_is_still_checked(self):
        (self.books / "accounts.toml").unlink()
        self.write_journal("2026-07.csv", CLEAN_ROWS + [row("2026-07-11", "ORPH", "1100", "5.00")])
        report = self.run_validate()
        self.assertOnly(report, "accounts-unreadable", "orphan-entry")
        self.assertIsNone(report.chart)
        self.assertTrue(any("chart of accounts could not be read" in n for n in report.notes))

    def test_duplicate_account_code_is_reported_as_unreadable_chart(self):
        self.write_accounts(extra='[[account]]\ncode = "1100"\nname = "Again"\ntype = "asset"\nnormal = "debit"\n')
        self.write_journal("2026-07.csv", CLEAN_ROWS)
        self.assertHas(self.run_validate(), "accounts-unreadable", 1)


# ======================================================================================
# Entry-level checks — the double-entry invariant
# ======================================================================================


class TestEntries(BooksCase):
    def test_unbalanced_entry_states_the_imbalance_in_taka(self):
        rows = [
            row("2026-07-01", "OPEN-001", "1100", "100000.00", desc="Opening"),
            row("2026-07-01", "OPEN-001", "3100", "", "90000.00", desc="Opening"),
        ]
        self.write_journal("2026-07.csv", rows)
        report = self.run_validate()
        f = self.assertHas(report, "unbalanced-entry", 1)[0]
        self.assertEqual((f.line, f.end_line, f.entry_id), (2, 3, "OPEN-001"))
        self.assertEqual(f.location, f"{f.file} lines 2–3")
        self.assertIn("৳1,00,000.00", f.message)
        self.assertIn("৳90,000.00", f.message)
        self.assertIn("৳10,000.00 too much debit", f.message)
        self.assertEqual(f.amount, M(1000000))
        self.assertTrue(f.is_error)
        self.assertEqual(report.exit_code(), validate.FINDINGS_EXIT_CODE)
        self.assertEqual(report.exit_code(allow_warnings=True), validate.FINDINGS_EXIT_CODE)
        with self.assertRaises(tb.BalanceError):  # and the strict loader agrees
            tb.Ledger.load(self.books)

    def test_too_much_credit_is_worded_that_way(self):
        self.write_journal("2026-07.csv", [row("2026-07-01", "E", "1100", "1.00"), row("2026-07-01", "E", "4100", "", "1.50")])
        f = self.assertHas(self.run_validate(), "unbalanced-entry", 1)[0]
        self.assertIn("৳0.50 too much credit", f.message)
        self.assertEqual(f.amount, M(-50))

    def test_orphan_single_line_entry(self):
        self.write_journal("2026-07.csv", CLEAN_ROWS + [row("2026-07-11", "ORPHAN-1", "1100", "7.00")])
        report = self.run_validate()
        f = self.assertHas(report, "orphan-entry", 1)[0]
        self.assertEqual((f.line, f.entry_id, f.account, f.amount), (10, "ORPHAN-1", "1100", M(700)))
        self.assertIn("single line", f.message)
        self.assertIn("৳7.00", f.message)
        self.assertLacks(report, "unbalanced-entry")

    def test_reused_entry_id_in_the_same_file(self):
        rows = entry("2026-07-01", "E-1", "1100", "3100", "10.00") + entry("2026-07-02", "E-2", "6100", "1100", "1.00") + entry("2026-07-03", "E-1", "6100", "1100", "2.00")
        self.write_journal("2026-07.csv", rows)
        report = self.run_validate()
        f = self.assertHas(report, "duplicate-entry-id", 1)[0]
        self.assertEqual((f.line, f.end_line, f.entry_id), (2, 3, "E-1"))
        self.assertIn("2 separate groups", f.message)
        self.assertIn("on 2026-07-01, 2026-07-03", f.message)
        self.assertIn("lines 2–3", f.message)
        self.assertIn("lines 6–7", f.message)
        self.assertTrue(f.is_error)
        # both transactions balance on their own: no phantom imbalance is invented
        self.assertLacks(report, "unbalanced-entry")
        self.assertLacks(report, "orphan-entry")

    def test_reused_entry_id_across_files(self):
        self.write_journal("2026-07.csv", entry("2026-07-01", "E-1", "1100", "3100", "10.00"))
        self.write_journal("2026-08.csv", entry("2026-08-01", "E-1", "6100", "1100", "2.00"))
        f = self.assertHas(self.run_validate(), "duplicate-entry-id", 1)[0]
        self.assertIn("across 2 files", f.message)
        self.assertIn("2026-07.csv", f.message)
        self.assertIn("2026-08.csv", f.message)

    def test_one_entry_over_two_dates_is_a_reused_id(self):
        rows = [row("2026-07-16", "SPLIT", "1100", "9.00"), row("2026-07-17", "SPLIT", "4100", "", "9.00")]
        self.write_journal("2026-07.csv", rows)
        report = self.run_validate()
        f = self.assertHas(report, "duplicate-entry-id", 1)[0]
        self.assertIn("on 2026-07-16, 2026-07-17", f.message)
        # the rows balance together, so only the root cause is reported and a note says why
        self.assertOnly(report, "duplicate-entry-id")
        self.assertTrue(any("SPLIT" in n and "balance when taken together" in n for n in report.notes), report.notes)

    def test_reuse_hidden_behind_a_broken_row_is_still_caught(self):
        rows = [
            row("2026-07-18", "GAP-A", "1100", "8.00"),
            row("2026-07-18", "GAP-B", "1100", "xx"),
            row("2026-07-18", "GAP-A", "4100", "", "8.00"),
        ]
        self.write_journal("2026-07.csv", rows)
        report = self.run_validate()
        self.assertOnly(report, "bad-amount", "duplicate-entry-id")
        self.assertEqual(self.find(report, "duplicate-entry-id")[0].entry_id, "GAP-A")

    def test_reused_id_where_one_transaction_is_unbalanced_reports_that_transaction_only(self):
        rows = [
            row("2026-07-01", "E", "1100", "100.00"),
            row("2026-07-01", "E", "3100", "", "90.00"),
            row("2026-07-02", "X", "6100", "1.00"),
            row("2026-07-02", "X", "1100", "", "1.00"),
            row("2026-07-03", "E", "6100", "2.00"),
            row("2026-07-03", "E", "1100", "", "2.00"),
        ]
        self.write_journal("2026-07.csv", rows)
        report = self.run_validate()
        self.assertOnly(report, "duplicate-entry-id", "unbalanced-entry")
        f = self.find(report, "unbalanced-entry")[0]
        self.assertEqual((f.line, f.end_line), (2, 3))
        self.assertIn("৳10.00 too much debit", f.message)

    def test_many_broken_entries_are_all_reported_at_once(self):
        rows = []
        for n in range(1, 6):
            rows += [row("2026-07-0%d" % n, f"E-{n}", "1100", "10.00"), row("2026-07-0%d" % n, f"E-{n}", "4100", "", "9.00")]
        self.write_journal("2026-07.csv", rows)
        report = self.run_validate()
        self.assertHas(report, "unbalanced-entry", 5)
        self.assertEqual([f.entry_id for f in report.sorted_findings()], [f"E-{n}" for n in range(1, 6)])


# ======================================================================================
# Tax tags on accounts
# ======================================================================================


class TestTaxTags(BooksCase):
    def test_vat_tag_on_the_tds_control_account_is_an_error(self):
        rows = [row("2026-07-10", "T-1", "2220", "", "100.00", "VAT:OUT:10"), row("2026-07-10", "T-1", "6100", "100.00")]
        self.write_journal("2026-07.csv", rows)
        report = self.run_validate()
        f = self.assertHas(report, "tax-tag-account-mismatch", 1)[0]
        self.assertEqual((f.line, f.entry_id, f.account), (2, "T-1", "2220"))
        self.assertIn(tb.term("vat"), f.message)
        self.assertIn("'tds_payable'", f.message)
        self.assertTrue(f.is_error)
        self.assertLacks(report, "tax-tag-orphan")  # the mismatch already says it all

    def test_tds_tag_on_the_vat_control_account_is_an_error(self):
        rows = [row("2026-07-10", "T-1", "2210", "", "100.00", "TDS:52:3"), row("2026-07-10", "T-1", "6100", "100.00")]
        self.write_journal("2026-07.csv", rows)
        f = self.assertHas(self.run_validate(), "tax-tag-account-mismatch", 1)[0]
        self.assertIn(tb.term("tds"), f.message)

    def test_tag_on_its_own_control_account_is_fine(self):
        self.write_journal("2026-07.csv", CLEAN_ROWS)
        self.assertOnly(self.run_validate())

    def test_vat_tag_without_a_control_line_is_a_warning(self):
        rows = [row("2026-07-10", "T-1", "4100", "", "100.00", "VAT:OUT:10"), row("2026-07-10", "T-1", "1100", "100.00")]
        self.write_journal("2026-07.csv", rows)
        report = self.run_validate()
        f = self.assertHas(report, "tax-tag-orphan", 1)[0]
        self.assertEqual((f.line, f.entry_id, f.account), (2, "T-1", "4100"))
        self.assertIn("2210 VAT Output Payable", f.message)
        self.assertEqual(f.severity, validate.SEVERITY_WARNING)

    def test_vds_and_vat_in_tags_expect_their_own_control_accounts(self):
        rows = [row("2026-07-10", "T-1", "6100", "100.00", "", "VDS:5"), row("2026-07-10", "T-1", "1100", "", "100.00")]
        self.write_journal("2026-07.csv", rows)
        self.assertIn("2230 VDS Payable", self.assertHas(self.run_validate(), "tax-tag-orphan", 1)[0].message)
        rows = [row("2026-07-10", "T-2", "6100", "100.00", "", "VAT:IN:10"), row("2026-07-10", "T-2", "1100", "", "100.00")]
        self.write_journal("2026-07.csv", rows)
        self.assertIn("1310 VAT Input Rebateable", self.assertHas(self.run_validate(), "tax-tag-orphan", 1)[0].message)

    def test_tag_only_on_the_control_line_is_a_warning(self):
        rows = [row("2026-07-15", "DEP-1", "2210", "1000.00", "", "VAT:OUT:10"), row("2026-07-15", "DEP-1", "1100", "", "1000.00")]
        self.write_journal("2026-07.csv", rows)
        report = self.run_validate()
        f = self.assertHas(report, "tax-tag-control-only", 1)[0]
        self.assertEqual((f.line, f.entry_id, f.account), (2, "DEP-1", "2210"))
        self.assertIn("৳0.00", f.message)
        self.assertIn("NONE", f.hint)
        self.assertEqual(f.severity, validate.SEVERITY_WARNING)

    def test_untagged_tax_deposit_is_clean(self):
        rows = [row("2026-07-15", "DEP-1", "2210", "1000.00"), row("2026-07-15", "DEP-1", "1100", "", "1000.00")]
        self.write_journal("2026-07.csv", rows)
        self.assertOnly(self.run_validate())

    def test_no_orphan_check_when_the_chart_declares_no_such_role(self):
        roles = {code: role for code, role in ROLES.items() if role != tb.ROLE_VAT_OUTPUT}
        self.write_accounts(roles=roles)
        rows = [row("2026-07-10", "T-1", "4100", "", "100.00", "VAT:OUT:10"), row("2026-07-10", "T-1", "1100", "100.00")]
        self.write_journal("2026-07.csv", rows)
        report = self.run_validate()
        self.assertOnly(report, "missing-required-role")

    def test_account_tags_can_mark_tax_relevance_without_a_role(self):
        accounts = ACCOUNTS + [("2290", "Output VAT (tagged)", "liability", "credit")]
        self.write_accounts(accounts=accounts, tags={**DEFAULT_TAGS, "2290": ["VAT"]})
        rows = [
            row("2026-07-10", "T-1", "4100", "", "100.00", "VAT:OUT:10"),
            row("2026-07-10", "T-1", "2290", "", "10.00", "VAT:OUT:10"),
            row("2026-07-10", "T-1", "1100", "110.00"),
        ]
        self.write_journal("2026-07.csv", rows)
        self.assertOnly(self.run_validate())  # 2290 counts as the control line via its tag
        (self.books / "accounts.toml").write_text(accounts_toml(accounts=accounts), encoding="utf-8")
        self.assertHas(self.run_validate(), "tax-tag-orphan", 1)  # and without the tag it does not

    def test_tag_checks_are_skipped_without_a_chart(self):
        (self.books / "accounts.toml").unlink()
        rows = [row("2026-07-10", "T-1", "2220", "", "100.00", "VAT:OUT:10"), row("2026-07-10", "T-1", "6100", "100.00")]
        self.write_journal("2026-07.csv", rows)
        self.assertOnly(self.run_validate(), "accounts-unreadable")


# ======================================================================================
# Dates, months and the financial year
# ======================================================================================


class TestDates(BooksCase):
    def test_dates_running_backwards_in_one_file(self):
        rows = CLEAN_ROWS + entry("2026-07-03", "BACK-1", "6100", "1100", "2.00")
        self.write_journal("2026-07.csv", rows)
        report = self.run_validate()
        f = self.assertHas(report, "date-out-of-order", 1)[0]
        self.assertEqual((f.line, f.entry_id), (10, "BACK-1"))
        self.assertIn("2026-07-03 is earlier than 2026-07-10 on line 9", f.message)
        self.assertEqual(f.severity, validate.SEVERITY_WARNING)

    def test_order_is_judged_per_file(self):
        self.write_journal("2026-08.csv", entry("2026-08-03", "AUG-1", "6100", "1100", "2.00"))
        self.write_journal("2026-07.csv", CLEAN_ROWS)
        self.assertOnly(self.run_validate())

    def test_row_in_the_wrong_month_file(self):
        rows = CLEAN_ROWS + entry("2026-08-02", "MISF-1", "6100", "1100", "3.00")
        self.write_journal("2026-07.csv", rows)
        report = self.run_validate()
        found = self.assertHas(report, "misfiled-posting", 2)
        self.assertEqual([f.line for f in found], [10, 11])
        self.assertIn("belongs in 2026-08.csv", found[0].message)

    def test_stray_backdated_row_is_the_odd_one_out_not_the_rest(self):
        rows = CLEAN_ROWS + [row("2025-06-30", "OLD-1", "1100", "4.00"), row("2025-06-30", "OLD-1", "4100", "", "4.00")]
        self.write_journal("2026-07.csv", rows)
        report = self.run_validate()
        found = self.assertHas(report, "date-outside-financial-year", 2)
        self.assertEqual({f.entry_id for f in found}, {"OLD-1"})
        self.assertIn("2026-07-01 → 2027-06-30", found[0].message)
        self.assertEqual(report.financial_year, (datetime.date(2026, 7, 1), datetime.date(2027, 6, 30)))
        self.assertIn("8 of 10", report.financial_year_source)
        self.assertEqual(found[0].severity, validate.SEVERITY_WARNING)

    def test_fy_start_argument_pins_the_window(self):
        self.write_journal("2026-07.csv", CLEAN_ROWS)
        report = self.run_validate(fy_start=datetime.date(2025, 7, 1))
        self.assertEqual(report.financial_year, (datetime.date(2025, 7, 1), datetime.date(2026, 6, 30)))
        self.assertEqual(report.financial_year_source, "from --fy-start")
        self.assertHas(report, "date-outside-financial-year", 8)
        report = self.run_validate(fy_start="2026-07-01")
        self.assertOnly(report)

    def test_fy_start_is_used_even_when_config_has_none(self):
        self.write_config(fiscal_year_start=None)
        self.write_journal("2026-07.csv", CLEAN_ROWS)
        report = self.run_validate(fy_start="2026-07-01")
        self.assertOnly(report)

    def test_missing_fiscal_year_start_skips_the_check_with_a_warning(self):
        self.write_config(fiscal_year_start=None)
        self.write_journal("2026-07.csv", CLEAN_ROWS + entry("2019-01-01", "ANCIENT", "6100", "1100", "1.00"))
        report = self.run_validate()
        self.assertOnly(report, "config-fiscal-year", "date-out-of-order", "misfiled-posting")
        self.assertIsNone(report.financial_year)
        self.assertTrue(any("skipped" in n for n in report.notes))
        self.assertTrue(self.find(report, "config-fiscal-year")[0].file.endswith("config.toml"))

    def test_outside_year_findings_are_capped_with_a_summary(self):
        rows = list(CLEAN_ROWS)
        for n in range(1, 8):
            rows += entry("2026-07-1%d" % n, f"IN-{n}", "6100", "1100", "1.00")  # 22 postings inside
        stray = []
        for n in range(1, 7):
            stray += entry("2025-06-0%d" % n, f"OUT-{n}", "6100", "1100", "1.00")  # 12 postings outside
        self.write_journal("2025-06.csv", stray)  # its own month file: no misfiling noise
        self.write_journal("2026-07.csv", rows)
        report = self.run_validate()
        found = self.assertHas(report, "date-outside-financial-year", validate._MAX_FY_FINDINGS + 1)
        self.assertTrue(found[-1].message.startswith("…and 2 more"))
        self.assertIn("22 of 34", report.financial_year_source)

    def test_no_readable_postings_skips_the_check_with_a_note(self):
        self.write_journal("2026-07.csv", [])
        report = self.run_validate()
        self.assertOnly(report)
        self.assertIsNone(report.financial_year)
        self.assertTrue(any("no postings were readable" in n for n in report.notes), report.notes)


# ======================================================================================
# Files, directories and config
# ======================================================================================


class TestFilesAndConfig(BooksCase):
    def test_missing_books_directory_raises_ledger_error(self):
        with self.assertRaises(tb.LedgerError) as ctx:
            validate.validate_books(self.root / "nowhere")
        self.assertEqual(ctx.exception.exit_code, 4)

    def test_missing_config_is_an_error_and_the_journal_is_still_read(self):
        (self.books / "config.toml").unlink()
        self.write_journal("2026-07.csv", CLEAN_ROWS + [row("2026-07-11", "ORPH", "1100", "1.00")])
        report = self.run_validate()
        self.assertOnly(report, "config-unreadable", "orphan-entry")
        self.assertIsNone(report.config)
        self.assertTrue(self.find(report, "config-unreadable")[0].file.endswith("config.toml"))
        text = validate.render_text(report)
        self.assertIn("not checked", text)  # financial year line

    def test_invalid_config_values_are_errors_not_tracebacks(self):
        self.write_config('[books]\ncurrency = "USD"\n')
        self.write_journal("2026-07.csv", CLEAN_ROWS)
        f = self.assertHas(self.run_validate(), "config-unreadable", 1)[0]
        self.assertIn("USD", f.message)

    def test_missing_assessment_year_is_a_warning(self):
        self.write_config(assessment_year=None)
        self.write_journal("2026-07.csv", CLEAN_ROWS)
        report = self.run_validate()
        f = self.assertHas(report, "config-assessment-year", 1)[0]
        self.assertIn(tb.term("assessment_year"), f.message)
        self.assertEqual(f.severity, validate.SEVERITY_WARNING)
        self.assertIn("(not set in config.toml)", validate.render_text(report))

    def test_custom_journal_directory_from_config(self):
        self.write_config(journal_dir="entries")
        (self.books / "entries").mkdir()
        (self.books / "entries" / "2026-07.csv").write_text(HEADER + "\n" + "\n".join(CLEAN_ROWS) + "\n", encoding="utf-8")
        report = self.run_validate()
        self.assertOnly(report)
        self.assertEqual(report.postings_checked, 8)
        self.assertTrue(report.journal_files[0].endswith("entries/2026-07.csv"))

    def test_missing_journal_directory(self):
        self.journal.rmdir()
        report = self.run_validate()
        self.assertOnly(report, "journal-missing")
        self.assertTrue(self.find(report, "journal-missing")[0].is_error)
        self.assertEqual(report.journal_files, [])

    def test_no_journal_files_is_a_warning(self):
        report = self.run_validate()
        self.assertOnly(report, "no-journal-files")
        self.assertEqual(report.exit_code(), validate.FINDINGS_EXIT_CODE)
        self.assertEqual(report.exit_code(allow_warnings=True), 0)

    def test_stray_and_misnamed_files(self):
        self.write_journal("2026-07.csv", CLEAN_ROWS)
        (self.journal / "notes.txt").write_text("hello", encoding="utf-8")
        (self.journal / "2026-07.csv.takabooks-tmp").write_text("", encoding="utf-8")
        (self.journal / ".DS_Store").write_bytes(b"\x00")
        (self.journal / "archive").mkdir()
        self.write_journal("scratch.csv", [])
        report = self.run_validate()
        self.assertOnly(report, "journal-stray-file", "journal-filename")
        strays = {Path(f.file).name for f in self.find(report, "journal-stray-file")}
        self.assertEqual(strays, {"notes.txt", "2026-07.csv.takabooks-tmp"})
        self.assertEqual(Path(self.find(report, "journal-filename")[0].file).name, "scratch.csv")

    def test_wrong_header_skips_the_file_with_an_error(self):
        self.write_journal("2026-07.csv", CLEAN_ROWS, header="date,id,desc,account,dr,cr")
        report = self.run_validate()
        self.assertOnly(report, "journal-header")
        f = self.find(report, "journal-header")[0]
        self.assertEqual(f.line, 1)
        self.assertIn("Unexpected header row", f.message)
        self.assertIn(HEADER, f.hint)
        self.assertEqual(report.postings_checked, 0)
        self.assertTrue(any("header row is wrong" in n for n in report.notes))

    def test_data_without_a_header_is_called_out(self):
        self.write_journal("2026-07.csv", CLEAN_ROWS, header=None)
        f = self.assertHas(self.run_validate(), "journal-header", 1)[0]
        self.assertIn("first row is data", f.message)

    def test_empty_file_has_no_header(self):
        (self.journal / "2026-07.csv").write_text("", encoding="utf-8")
        f = self.assertHas(self.run_validate(), "journal-header", 1)[0]
        self.assertIn("No header row", f.message)

    def test_header_only_file_is_clean(self):
        self.write_journal("2026-07.csv", [])
        report = self.run_validate()
        self.assertOnly(report)
        self.assertEqual(report.rows_read, 0)

    def test_non_utf8_file_is_reported_not_raised(self):
        (self.journal / "2026-07.csv").write_bytes(b"\xff\xfe\x00 not utf-8 \xc3\x28")
        report = self.run_validate()
        self.assertOnly(report, "journal-unreadable")
        f = self.find(report, "journal-unreadable")[0]
        self.assertIn("UTF-8", f.message)
        self.assertTrue(f.is_error)

    def test_labels_are_relative_to_the_books_parent(self):
        self.write_journal("2026-07.csv", CLEAN_ROWS + [row("2026-07-11", "ORPH", "1100", "1.00")])
        f = self.assertHas(self.run_validate(), "orphan-entry", 1)[0]
        self.assertEqual(f.file, "books/journal/2026-07.csv")
        self.assertEqual(f.location, "books/journal/2026-07.csv line 10")


# ======================================================================================
# Report rendering
# ======================================================================================


class TestRendering(BooksCase):
    def setUp(self) -> None:
        super().setUp()
        rows = CLEAN_ROWS + [
            row("2026-07-11", "ORPH", "1100", "1.00"),
            *entry("2026-07-12", "OLD-1", "6900", "1100", "10.00"),
        ]
        self.write_journal("2026-07.csv", rows)
        self.report = self.run_validate()

    def test_findings_are_grouped_by_severity_and_numbered(self):
        text = validate.render_text(self.report)
        self.assertIn("ERRORS", text)
        self.assertIn("WARNINGS", text)
        self.assertLess(text.index("ERRORS"), text.index("WARNINGS"))
        self.assertIn("  1. [orphan-entry] books/journal/2026-07.csv line 10 · entry ORPH", text)
        self.assertIn("  1. [inactive-account] books/journal/2026-07.csv line 11 · entry OLD-1", text)
        self.assertIn("RESULT: 1 error(s), 1 warning(s)", text)
        self.assertIn(f"(exit {validate.FINDINGS_EXIT_CODE})", text)
        self.assertTrue(text.rstrip().endswith(tb.DISCLAIMER_EN))

    def test_summary_line_variants(self):
        self.assertIn("do not file", self.report.summary_line())
        warnings_only = validate.ValidationReport(books_dir=self.books, findings=self.report.warnings)
        self.assertIn("not fully clean", warnings_only.summary_line())
        self.assertIn("--allow-warnings", warnings_only.summary_line())
        self.assertIn("warnings accepted", warnings_only.summary_line(allow_warnings=True))
        self.assertEqual(warnings_only.exit_code(allow_warnings=True), 0)
        self.assertEqual(warnings_only.exit_code(), validate.FINDINGS_EXIT_CODE)

    def test_by_check_follows_catalogue_order(self):
        self.assertEqual(list(self.report.by_check()), ["inactive-account", "orphan-entry"])
        self.assertEqual(self.report.by_check(), {"inactive-account": 1, "orphan-entry": 1})

    def test_json_findings_carry_location_fields(self):
        payload = json.loads(validate.render_json(self.report))
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["exit_code"], validate.FINDINGS_EXIT_CODE)
        self.assertEqual(payload["counts"]["errors"], 1)
        self.assertEqual(payload["counts"]["warnings"], 1)
        first = payload["findings"][0]
        self.assertEqual(first["check"], "orphan-entry")
        self.assertEqual(first["severity"], "error")
        self.assertEqual(first["file"], "books/journal/2026-07.csv")
        self.assertEqual(first["line"], 10)
        self.assertEqual(first["entry_id"], "ORPH")
        self.assertEqual(first["amount"], "1.00")
        self.assertEqual(first["location"], "books/journal/2026-07.csv line 10")
        self.assertEqual(payload["by_check"], {"inactive-account": 1, "orphan-entry": 1})

    def test_json_with_allow_warnings_only_flips_when_no_errors_remain(self):
        payload = json.loads(validate.render_json(self.report, allow_warnings=True))
        self.assertFalse(payload["ok"])
        warnings_only = validate.ValidationReport(books_dir=self.books, findings=self.report.warnings)
        self.assertTrue(json.loads(validate.render_json(warnings_only, allow_warnings=True))["ok"])


# ======================================================================================
# The command line
# ======================================================================================


class TestCLI(BooksCase):
    def test_help_lists_the_standard_flags(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), self.assertRaises(SystemExit) as ctx:
            validate.main(["--help"])
        self.assertEqual(ctx.exception.code, 0)
        text = buf.getvalue()
        for flag in ("--books", "--json", "--version", "--allow-warnings", "--quiet", "--fy-start", "--list-checks"):
            self.assertIn(flag, text)
        self.assertIn(tb.ATTRIBUTION, text)
        self.assertEqual(validate.build_parser().prog, "validate.py")

    def test_list_checks(self):
        code, out, err = self.run_main("--list-checks")
        self.assertEqual(code, 0)
        for check in validate.CHECKS:
            self.assertIn(check.slug, out)
        self.assertEqual(err, "")

    def test_clean_books_exit_zero(self):
        self.write_journal("2026-07.csv", CLEAN_ROWS)
        code, out, err = self.run_main("--books", str(self.books))
        self.assertEqual(code, 0)
        self.assertIn("RESULT: clean", out)
        self.assertIn(tb.DISCLAIMER_EN, out)
        self.assertEqual(err, "")

    def test_dirty_books_exit_non_zero_with_findings_on_stdout(self):
        self.write_journal("2026-07.csv", CLEAN_ROWS + [row("2026-07-11", "ORPH", "1100", "1.00")])
        code, out, err = self.run_main("--books", str(self.books))
        self.assertEqual(code, validate.FINDINGS_EXIT_CODE)
        self.assertIn("[orphan-entry]", out)

    def test_quiet_prints_one_line(self):
        self.write_journal("2026-07.csv", CLEAN_ROWS)
        code, out, _ = self.run_main("--books", str(self.books), "--quiet")
        self.assertEqual(code, 0)
        self.assertEqual(len(out.strip().splitlines()), 1)

    def test_json_flag(self):
        self.write_journal("2026-07.csv", CLEAN_ROWS + entry("2026-07-12", "OLD-1", "6900", "1100", "10.00"))
        code, out, err = self.run_main("--books", str(self.books), "--json")
        payload = json.loads(out)
        self.assertEqual(code, validate.FINDINGS_EXIT_CODE)
        self.assertFalse(payload["ok"])
        self.assertEqual([f["check"] for f in payload["findings"]], ["inactive-account"])
        self.assertEqual(err, "")

    def test_allow_warnings(self):
        self.write_journal("2026-07.csv", CLEAN_ROWS + entry("2026-07-12", "OLD-1", "6900", "1100", "10.00"))
        code, out, _ = self.run_main("--books", str(self.books), "--allow-warnings")
        self.assertEqual(code, 0)
        self.assertIn("warnings accepted", out)
        code, out, _ = self.run_main("--books", str(self.books), "--allow-warnings", "--json")
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)["ok"])
        # errors are never waved through
        self.write_journal("2026-07.csv", CLEAN_ROWS + [row("2026-07-11", "ORPH", "1100", "1.00")])
        code, _, _ = self.run_main("--books", str(self.books), "--allow-warnings")
        self.assertEqual(code, validate.FINDINGS_EXIT_CODE)

    def test_missing_books_directory_exits_with_the_ledger_error_code(self):
        code, out, err = self.run_main("--books", str(self.root / "nope"))
        self.assertEqual(code, 4)
        self.assertEqual(out, "")
        self.assertIn("error: Books directory not found", err)
        self.assertIn("hint:", err)

    def test_missing_books_directory_json_error(self):
        code, out, err = self.run_main("--books", str(self.root / "nope"), "--json")
        self.assertEqual(code, 4)
        payload = json.loads(err)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"], "LedgerError")
        self.assertEqual(payload["exit_code"], 4)

    def test_bad_fy_start_is_a_config_error(self):
        self.write_journal("2026-07.csv", CLEAN_ROWS)
        code, out, err = self.run_main("--books", str(self.books), "--fy-start", "2026-7-1")
        self.assertEqual(code, 2)
        self.assertIn("--fy-start", err)
        self.assertIn("YYYY-MM-DD", err)
        code, _, err = self.run_main("--books", str(self.books), "--fy-start", "junk", "--json")
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(err)["error"], "ConfigError")

    def test_good_fy_start_pins_the_window(self):
        self.write_journal("2026-07.csv", CLEAN_ROWS)
        code, out, _ = self.run_main("--books", str(self.books), "--fy-start", "2026-07-01")
        self.assertEqual(code, 0)
        self.assertIn("from --fy-start", out)
        code, out, _ = self.run_main("--books", str(self.books), "--fy-start", "2025-07-01", "--json")
        self.assertEqual(code, validate.FINDINGS_EXIT_CODE)
        self.assertEqual(json.loads(out)["by_check"], {"date-outside-financial-year": 8})

    def test_script_runs_as_a_subprocess(self):
        import subprocess

        self.write_journal("2026-07.csv", CLEAN_ROWS)
        script = ENGINE_DIR / "validate.py"
        done = subprocess.run([sys.executable, str(script), "--books", str(self.books), "--quiet"], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("RESULT: clean", done.stdout)
        done = subprocess.run([sys.executable, str(script), "--books", str(self.root / "nope")], capture_output=True, text=True)
        self.assertEqual(done.returncode, 4)
        self.assertIn("error:", done.stderr)


# ======================================================================================
# Coverage invariant: every declared check is exercised somewhere above
# ======================================================================================


class TestZZEveryCheckIsExercised(unittest.TestCase):
    #: Defensive slugs that cannot be reached with a well-formed library underneath.
    UNREACHABLE = {"row-invalid"}

    def test_every_check_slug_was_observed_by_some_test(self):
        if len(SEEN_CHECKS) < 5:
            self.skipTest("run the whole module for the coverage invariant")
        expected = {c.slug for c in validate.CHECKS} - self.UNREACHABLE
        self.assertEqual(expected - SEEN_CHECKS, set(), "checks no test exercised")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
