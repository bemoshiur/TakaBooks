"""Tests for ``src/engine/report.py`` — রেওয়ামিল / trial balance, লাভ-ক্ষতি হিসাব / profit
and loss, স্থিতিপত্র / balance sheet.

Run with::

    python3 -m unittest discover tests

The fixture is a small hand-built ledger (three journal months) and **every expected figure
below was worked out by hand** before the code was run — see :data:`HAND_CHECKED` for the
arithmetic.  The suite proves, per spec §7, that every report ties back to the journal,
that the Markdown and CSV renderings never disagree, and that books that do not reconcile
exit non-zero instead of printing.

TakaBooks — Moshiur Rahman (@bemoshiur) · Ticon Sys — https://ticonsys.com
"""

from __future__ import annotations

import contextlib
import csv
import dataclasses
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

import report  # noqa: E402
import takabooks as tb  # noqa: E402

M = tb.Money
bdt = tb.Money.from_str
D = datetime.date


# ======================================================================================
# Fixture books
# ======================================================================================

ACCOUNTS_TOML = """
[[account]]
code = "1100"
name = "Cash in Hand"
name_bn = "হাতে নগদ"
type = "asset"
normal = "debit"

[[account]]
code = "1110"
name = "Bank Current Account"
name_bn = "ব্যাংক চলতি হিসাব"
type = "asset"
normal = "debit"

[[account]]
code = "1200"
name = "Accounts Receivable"
name_bn = "প্রাপ্য হিসাব"
type = "asset"
normal = "debit"

[[account]]
code = "1310"
name = "VAT Input / Rebateable"
name_bn = "রেয়াতযোগ্য উপকরণ মূসক"
type = "asset"
normal = "debit"
role = "vat_input"

[[account]]
code = "1320"
name = "TDS Receivable"
type = "asset"
normal = "debit"
role = "tds_receivable"

[[account]]
code = "1500"
name = "Office Equipment"
type = "asset"
normal = "debit"

[[account]]
code = "2100"
name = "Accounts Payable"
name_bn = "প্রদেয় হিসাব"
type = "liability"
normal = "credit"

[[account]]
code = "2310"
name = "VAT Output Payable"
name_bn = "প্রদেয় মূসক"
type = "liability"
normal = "credit"
role = "vat_output"

[[account]]
code = "3100"
name = "Owner's Capital"
name_bn = "মালিকের মূলধন"
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
type = "income"
normal = "credit"

[[account]]
code = "5100"
name = "Cost of Goods Sold"
name_bn = "বিক্রিত পণ্যের ব্যয়"
type = "expense"
normal = "debit"

[[account]]
code = "6100"
name = "Office Rent"
name_bn = "অফিস ভাড়া"
type = "expense"
normal = "debit"

[[account]]
code = "6200"
name = "Salaries and Wages"
type = "expense"
normal = "debit"

[[account]]
code = "7100"
name = "Bank Interest Income"
type = "income"
normal = "credit"

[[account]]
code = "8100"
name = "Bank Charges"
type = "expense"
normal = "debit"

[[account]]
code = "9100"
name = "Income Tax Expense"
type = "expense"
normal = "debit"
"""

CONFIG_TOML = """
[business]
name = "Ticon Sys Demo Traders"
name_bn = "টিকন সিস ডেমো ট্রেডার্স"
tin = "000000000000"
bin = "000000000-0000"

[books]
currency = "BDT"
fiscal_year_start = "07-01"
assessment_year = "2026-27"

[locale]
language = "en"
grouping = "bd"
digits = "latin"
"""

# The tax_tag cells below are the journal's own inputs (report.py never reads them); the
# figures are illustrative bookkeeping amounts, not a statement of any Bangladeshi rate.
JOURNAL_2026_06 = """\
date,entry_id,description,account,debit,credit,party,doc_ref,tax_tag,memo
2026-06-01,OPEN-001,Owner capital introduced,1110,500000.00,0.00,Owner,,NONE,
2026-06-01,OPEN-001,Owner capital introduced,3100,0.00,500000.00,Owner,,NONE,
2026-06-15,JUN-SALE-001,Cash sale,1100,115000.00,0.00,Walk-in,CM-1,NONE,
2026-06-15,JUN-SALE-001,Cash sale,4100,0.00,100000.00,Walk-in,CM-1,NONE,
2026-06-15,JUN-SALE-001,Cash sale,2310,0.00,15000.00,Walk-in,CM-1,VAT:OUT:15,
2026-06-30,JUN-RENT-001,June office rent,6100,20000.00,0.00,Landlord,,NONE,
2026-06-30,JUN-RENT-001,June office rent,1110,0.00,20000.00,Landlord,,NONE,
"""

JOURNAL_2026_07 = """\
date,entry_id,description,account,debit,credit,party,doc_ref,tax_tag,memo
2026-07-05,INV-001,Credit sale,1200,230000.00,0.00,Rahim Traders,INV-001,NONE,
2026-07-05,INV-001,Credit sale,4100,0.00,200000.00,Rahim Traders,INV-001,NONE,
2026-07-05,INV-001,Credit sale,2310,0.00,30000.00,Rahim Traders,INV-001,VAT:OUT:15,
2026-07-08,PUR-001,Goods for resale,5100,80000.00,0.00,Karim Supplies,BILL-77,NONE,
2026-07-08,PUR-001,Goods for resale,1310,12000.00,0.00,Karim Supplies,BILL-77,VAT:IN:15,
2026-07-08,PUR-001,Goods for resale,2100,0.00,92000.00,Karim Supplies,BILL-77,NONE,
2026-07-20,REC-001,Receipt from Rahim Traders,1110,100000.00,0.00,Rahim Traders,INV-001,NONE,
2026-07-20,REC-001,Receipt from Rahim Traders,1200,0.00,100000.00,Rahim Traders,INV-001,NONE,
2026-07-25,SAL-001,July salaries,6200,60000.00,0.00,Staff,,NONE,
2026-07-25,SAL-001,July salaries,1110,0.00,60000.00,Staff,,NONE,
2026-07-31,RENT-002,July office rent,6100,20000.00,0.00,Landlord,,NONE,
2026-07-31,RENT-002,July office rent,1110,0.00,20000.00,Landlord,,NONE,
2026-07-31,INT-001,Bank interest,1110,1234.56,0.00,Bank,,NONE,
2026-07-31,INT-001,Bank interest,7100,0.00,1234.56,Bank,,NONE,
2026-07-31,CHG-001,Bank charges,8100,345.67,0.00,Bank,,NONE,memo with, a comma
2026-07-31,CHG-001,Bank charges,1110,0.00,345.67,Bank,,NONE,
"""

JOURNAL_2026_08 = """\
date,entry_id,description,account,debit,credit,party,doc_ref,tax_tag,memo
2026-08-10,SRV-001,Consulting fee received,1100,50000.00,0.00,Client A,,NONE,
2026-08-10,SRV-001,Consulting fee received,4200,0.00,50000.00,Client A,,NONE,
2026-08-12,EQP-001,Office equipment,1500,120000.00,0.00,Shop B,,NONE,
2026-08-12,EQP-001,Office equipment,1110,0.00,120000.00,Shop B,,NONE,
2026-08-31,TAX-001,Income tax paid,9100,10000.00,0.00,NBR,,NONE,
2026-08-31,TAX-001,Income tax paid,1110,0.00,10000.00,NBR,,NONE,
"""

#: Hand-checked figures.  Worked out from the three journals above by hand; the tests
#: assert the code reproduces them, never the other way round.
#:
#: Whole ledger, as at 2026-08-31
#:   gross debits = 500000 + 115000 + 20000 + 230000 + 92000 + 60000 + 20000 + 100000
#:                  + 1234.56 + 345.67 + 50000 + 120000 + 10000        = 13,18,580.23
#:   1110 Bank  = (500000 + 100000 + 1234.56) − (20000 + 60000 + 20000 + 345.67
#:                  + 120000 + 10000)                                   = 3,70,888.89
#:   assets     = 165000 + 370888.89 + 130000 + 12000 + 120000          = 7,97,888.89
#:   liabilities= 92000 + 45000                                          = 1,37,000.00
#:   income     = 300000 + 50000 + 1234.56                               = 3,51,234.56
#:   expenses   = 80000 + 40000 + 60000 + 345.67 + 10000                 = 1,90,345.67
#:   net profit = 351234.56 − 190345.67                                  = 1,60,888.89
#:   equity     = 500000 + 160888.89                                     = 6,60,888.89
#:   L + E      = 137000 + 660888.89                                     = 7,97,888.89  ✓
#: Month 2026-07 (as at 2026-07-31; opening = June result 100000 − 20000 = 80,000)
#:   net profit = 200000 − 80000 − (20000 + 60000) + 1234.56 − 345.67  = 40,888.89
#:   assets     = 115000 + 500888.89 + 130000 + 12000                    = 7,57,888.89
#:   equity     = 500000 + 80000 + 40888.89                              = 6,20,888.89
#:   gross debits (June + July)                                          = 11,38,580.23
#: FY2026-27 (2026-07-01 → 2027-06-30; as at = whole ledger)
#:   net profit = 250000 − 80000 − 80000 + 1234.56 − 10345.67           = 80,888.89
#:   80000 brought forward + 80888.89                                    = 1,60,888.89  ✓
#: June only (2026-06-01 → 2026-06-30)
#:   net profit = 100000 − 20000 = 80,000 ; assets = 115000 + 480000     = 5,95,000.00
#:   liabilities = 15,000 ; equity = 500000 + 0 + 80000                  = 5,80,000.00  ✓
HAND_CHECKED = {
    "whole": {
        "tb_total": "1318580.23",
        "balances": {
            "1100": "165000.00", "1110": "370888.89", "1200": "130000.00",
            "1310": "12000.00", "1500": "120000.00", "2100": "92000.00",
            "2310": "45000.00", "3100": "500000.00", "4100": "300000.00",
            "4200": "50000.00", "5100": "80000.00", "6100": "40000.00",
            "6200": "60000.00", "7100": "1234.56", "8100": "345.67", "9100": "10000.00",
        },
        "revenue": "350000.00", "cost_of_sales": "80000.00", "gross_profit": "270000.00",
        "operating_expenses": "100000.00", "operating_profit": "170000.00",
        "other_income": "1234.56", "other_expenses": "10345.67", "net_profit": "160888.89",
        "assets": "797888.89", "liabilities": "137000.00", "capital": "500000.00",
        "opening": "0.00", "total_equity": "660888.89",
        "postings": 29, "entries": 13,
    },
    "july": {
        "tb_total": "1138580.23",
        "bank": ("601234.56", "100345.67", "500888.89"),
        "revenue": "200000.00", "cost_of_sales": "80000.00", "gross_profit": "120000.00",
        "operating_expenses": "80000.00", "operating_profit": "40000.00",
        "other_income": "1234.56", "other_expenses": "345.67", "net_profit": "40888.89",
        "assets": "757888.89", "liabilities": "137000.00", "opening": "80000.00",
        "total_equity": "620888.89",
        "postings": 23, "entries": 10, "period_postings": 16, "period_entries": 7,
    },
    "fy": {
        "revenue": "250000.00", "gross_profit": "170000.00", "operating_profit": "90000.00",
        "other_expenses": "10345.67", "net_profit": "80888.89", "opening": "80000.00",
        "accumulated": "160888.89", "period_postings": 22, "period_entries": 10,
    },
    "june": {
        "tb_total": "635000.00", "net_profit": "80000.00", "assets": "595000.00",
        "liabilities": "15000.00", "total_equity": "580000.00", "opening": "0.00",
    },
}


def write_books(root: Path, *, config: str = CONFIG_TOML, journals: bool = True) -> Path:
    books = root / "books"
    (books / "journal").mkdir(parents=True)
    (books / "accounts.toml").write_text(ACCOUNTS_TOML, encoding="utf-8")
    (books / "config.toml").write_text(config, encoding="utf-8")
    if journals:
        (books / "journal" / "2026-06.csv").write_text(JOURNAL_2026_06, encoding="utf-8")
        (books / "journal" / "2026-07.csv").write_text(JOURNAL_2026_07, encoding="utf-8")
        (books / "journal" / "2026-08.csv").write_text(JOURNAL_2026_08, encoding="utf-8")
    return books


def markdown_tables(text: str) -> dict[str, list[list[str]]]:
    """``{heading: rows}`` for every ``## `` section, header and alignment rows dropped,
    bold markers stripped."""
    tables: dict[str, list[list[str]]] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:]
            tables[current] = []
        elif current is not None and line.startswith("|"):
            cells = [c.strip().strip("*").strip() for c in line.strip().strip("|").split("|")]
            tables[current].append(cells)
    return {heading: rows[2:] for heading, rows in tables.items()}


def table_for(tables: dict[str, list[list[str]]], word: str) -> list[list[str]]:
    for heading, rows in tables.items():
        if word in heading:
            return rows
    raise AssertionError(f"no ## heading containing {word!r} in {list(tables)}")


def ungroup(cell: str) -> str:
    return cell.replace(",", "").replace("৳", "")


class BooksTestCase(unittest.TestCase):
    """A temporary ``books/`` tree written from the fixture above."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        self.books = write_books(self.root)

    def tearDown(self):
        self.dir.cleanup()

    def load(self) -> tb.Ledger:
        return tb.Ledger.load(self.books)

    def statements(self, **kwargs) -> report.FinancialStatements:
        return report.build_statements(self.load(), **kwargs)

    def run_cli(self, *argv: str, expect: int = 0) -> tuple[str, str]:
        out, err = io.StringIO(), io.StringIO()
        code: int | None
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = report.main([*argv], out=out)
            except SystemExit as exc:
                code = exc.code
        self.assertEqual(code, expect, f"stdout:\n{out.getvalue()}\nstderr:\n{err.getvalue()}")
        return out.getvalue(), err.getvalue()


# ======================================================================================
# Period resolution
# ======================================================================================


class TestResolvePeriod(unittest.TestCase):
    def setUp(self):
        self.config = tb.Config.from_mapping(
            {"books": {"fiscal_year_start": "07-01"}}, source_path="config.toml"
        )

    def test_no_flags_means_the_whole_ledger(self):
        self.assertEqual(report.resolve_period(), (None, None, "the whole ledger"))

    def test_month(self):
        start, end, label = report.resolve_period(period="2026-07")
        self.assertEqual((start, end), (D(2026, 7, 1), D(2026, 7, 31)))
        self.assertIn("2026-07-01 → 2026-07-31", label)

    def test_month_ends_handle_february_and_december(self):
        self.assertEqual(report.resolve_period(period="2028-02")[1], D(2028, 2, 29))
        self.assertEqual(report.resolve_period(period="2026-02")[1], D(2026, 2, 28))
        self.assertEqual(report.resolve_period(period="2026-12")[1], D(2026, 12, 31))

    def test_fiscal_year_forms(self):
        for text in ("FY2026", "FY2026-27", "FY2026-2027", "fy 2026/27", "FY_2026", "2026-27"):
            with self.subTest(period=text):
                start, end, label = report.resolve_period(period=text, config=self.config)
                self.assertEqual((start, end), (D(2026, 7, 1), D(2027, 6, 30)))
                self.assertIn("FY2026-27", label)
                self.assertIn("07-01", label)

    def test_fiscal_year_reads_the_books_own_start(self):
        config = tb.Config.from_mapping({"books": {"fiscal_year_start": "01-01"}})
        start, end, _ = report.resolve_period(period="FY2026", config=config)
        self.assertEqual((start, end), (D(2026, 1, 1), D(2026, 12, 31)))

    def test_fiscal_year_needs_config_and_a_configured_start(self):
        with self.assertRaises(tb.ConfigError):
            report.resolve_period(period="FY2026-27", config=None)
        with self.assertRaises(tb.ConfigError) as ctx:
            report.resolve_period(period="FY2026-27", config=tb.Config.from_mapping({}))
        self.assertIn("fiscal_year_start", ctx.exception.message)

    def test_fiscal_year_suffix_must_be_the_next_year(self):
        for text in ("FY2026-28", "2026-13", "FY2026-2026"):
            with self.subTest(period=text):
                with self.assertRaises(tb.ValidationError) as ctx:
                    report.resolve_period(period=text, config=self.config)
                self.assertIn("2027", ctx.exception.message)
                self.assertEqual(ctx.exception.exit_code, 7)

    def test_unknown_period_fails_with_the_accepted_forms(self):
        with self.assertRaises(tb.ValidationError) as ctx:
            report.resolve_period(period="July 2026")
        self.assertIn("YYYY-MM", ctx.exception.hint)
        self.assertIn("FY", ctx.exception.hint)

    def test_period_cannot_be_combined_with_from_or_to(self):
        with self.assertRaises(tb.ValidationError):
            report.resolve_period(period="2026-07", date_from="2026-07-01")
        with self.assertRaises(tb.ValidationError):
            report.resolve_period(period="2026-07", date_to="2026-07-31")

    def test_from_and_to_are_iso_and_ordered(self):
        start, end, label = report.resolve_period(date_from="2026-07-01", date_to="2026-07-31")
        self.assertEqual((start, end), (D(2026, 7, 1), D(2026, 7, 31)))
        self.assertEqual(label, "2026-07-01 → 2026-07-31")
        with self.assertRaises(tb.ValidationError) as ctx:
            report.resolve_period(date_from="2026-08-01", date_to="2026-07-01")
        self.assertIn("after", ctx.exception.message)
        for bad in ("15-07-2026", "20260715", "2026-7-5"):
            with self.subTest(date=bad):
                with self.assertRaises(tb.ValidationError) as ctx:
                    report.resolve_period(date_from=bad)
                self.assertIn("--from", ctx.exception.message)
                self.assertEqual(ctx.exception.exit_code, 7)

    def test_open_ended_windows_and_date_objects(self):
        self.assertEqual(report.resolve_period(date_from="2026-08-01")[2], "from 2026-08-01")
        self.assertEqual(report.resolve_period(date_to="2026-07-31")[2], "up to 2026-07-31")
        start, end, _ = report.resolve_period(date_from=D(2026, 7, 1), date_to=D(2026, 7, 31))
        self.assertEqual((start, end), (D(2026, 7, 1), D(2026, 7, 31)))


# ======================================================================================
# The computation, against the hand-checked figures
# ======================================================================================


class TestWholeLedger(BooksTestCase):
    def setUp(self):
        super().setUp()
        self.fs = self.statements()
        self.expect = HAND_CHECKED["whole"]

    def test_trial_balance_debits_equal_credits_and_match_the_hand_total(self):
        trial = self.fs.trial_balance
        self.assertEqual(trial.total_debit, bdt(self.expect["tb_total"]))
        self.assertEqual(trial.total_credit, bdt(self.expect["tb_total"]))
        self.assertTrue(trial.is_balanced)
        self.assertEqual(trial.difference, M.zero())
        self.assertEqual(trial.as_at, D(2026, 8, 31))

    def test_trial_balance_lines_are_in_chart_order_with_natural_balances(self):
        lines = {line.code: line for line in self.fs.trial_balance.lines}
        self.assertEqual(list(lines), list(self.expect["balances"]))
        for code, amount in self.expect["balances"].items():
            with self.subTest(code=code):
                self.assertEqual(lines[code].amount, bdt(amount))
        bank = lines["1110"]
        self.assertEqual((bank.debit, bank.credit), (bdt("601234.56"), bdt("230345.67")))
        self.assertNotIn("1320", lines, "an account with no postings is not listed by default")

    def test_profit_and_loss_sections(self):
        pl = self.fs.profit_and_loss
        for key in (
            "revenue", "cost_of_sales", "gross_profit", "operating_expenses",
            "operating_profit", "other_income", "other_expenses", "net_profit",
        ):
            with self.subTest(key=key):
                self.assertEqual(getattr(pl, key), bdt(self.expect[key]))
        self.assertEqual(pl.total_income, bdt("351234.56"))
        self.assertEqual(pl.total_expenses, bdt("190345.67"))
        self.assertEqual([s.key for s in pl.sections], [s.key for s in report.PL_SECTIONS])
        self.assertEqual([l.code for l in pl.section("revenue").lines], ["4100", "4200"])
        self.assertEqual([l.code for l in pl.section("other_expenses").lines], ["8100", "9100"])
        self.assertEqual((pl.start, pl.end), (D(2026, 6, 1), D(2026, 8, 31)))

    def test_balance_sheet_assets_equal_liabilities_plus_equity(self):
        bs = self.fs.balance_sheet
        self.assertEqual(bs.total_assets, bdt(self.expect["assets"]))
        self.assertEqual(bs.total_liabilities, bdt(self.expect["liabilities"]))
        self.assertEqual(bs.equity.total, bdt(self.expect["capital"]))
        self.assertEqual(bs.opening_result, bdt(self.expect["opening"]))
        self.assertEqual(bs.total_equity, bdt(self.expect["total_equity"]))
        self.assertEqual(bs.total_liabilities_and_equity, bs.total_assets)
        self.assertTrue(bs.is_balanced)
        self.assertEqual(bs.difference, M.zero())
        self.assertEqual([l.code for l in bs.assets.lines], ["1100", "1110", "1200", "1310", "1500"])
        self.assertEqual([l.code for l in bs.liabilities.lines], ["2100", "2310"])
        self.assertEqual([l.code for l in bs.equity.lines], ["3100"])

    def test_net_profit_is_carried_into_the_balance_sheet_unchanged(self):
        self.assertEqual(self.fs.balance_sheet.period_result, self.fs.profit_and_loss.net_profit)
        self.assertEqual(
            self.fs.balance_sheet.total_equity,
            self.fs.balance_sheet.equity.total
            + self.fs.balance_sheet.opening_result
            + self.fs.profit_and_loss.net_profit,
        )

    def test_every_reconciliation_passed(self):
        self.assertEqual(len(self.fs.checks), 4)
        self.assertTrue(all(check.ok for check in self.fs.checks))
        names = {check.name for check in self.fs.checks}
        self.assertIn("trial_balance_debits_equal_credits", names)
        self.assertIn("balance_sheet_assets_equal_liabilities_plus_equity", names)

    def test_counts_and_dates(self):
        self.assertEqual(self.fs.posting_count, self.expect["postings"])
        self.assertEqual(self.fs.entry_count, self.expect["entries"])
        self.assertEqual(self.fs.period_posting_count, self.expect["postings"])
        self.assertEqual(self.fs.period_entry_count, self.expect["entries"])
        self.assertEqual((self.fs.covers_from, self.fs.as_at), (D(2026, 6, 1), D(2026, 8, 31)))
        self.assertEqual(self.fs.period_label, "the whole ledger")

    def test_include_unused_lists_zero_accounts_without_changing_totals(self):
        fs = self.statements(include_unused=True)
        codes = [line.code for line in fs.trial_balance.lines]
        self.assertIn("1320", codes)
        unused = next(line for line in fs.trial_balance.lines if line.code == "1320")
        self.assertEqual((unused.debit, unused.credit, unused.amount), (M.zero(),) * 3)
        self.assertEqual(fs.trial_balance.total_debit, self.fs.trial_balance.total_debit)
        self.assertEqual(fs.balance_sheet.total_assets, self.fs.balance_sheet.total_assets)


class TestPeriods(BooksTestCase):
    def test_month_period_pl_covers_july_and_statements_are_as_at_july_end(self):
        expect = HAND_CHECKED["july"]
        start, end, label = report.resolve_period(period="2026-07")
        fs = self.statements(period_start=start, period_end=end, period_label=label)
        pl, bs, trial = fs.profit_and_loss, fs.balance_sheet, fs.trial_balance

        self.assertEqual(trial.total_debit, bdt(expect["tb_total"]))
        self.assertEqual(trial.total_credit, bdt(expect["tb_total"]))
        bank = next(line for line in trial.lines if line.code == "1110")
        self.assertEqual((bank.debit, bank.credit, bank.amount), tuple(map(bdt, expect["bank"])))
        self.assertNotIn("1500", [l.code for l in trial.lines], "August equipment is after as-at")

        for key in (
            "revenue", "cost_of_sales", "gross_profit", "operating_expenses",
            "operating_profit", "other_income", "other_expenses", "net_profit",
        ):
            with self.subTest(key=key):
                self.assertEqual(getattr(pl, key), bdt(expect[key]))
        self.assertEqual([l.code for l in pl.section("revenue").lines], ["4100"])

        self.assertEqual(bs.total_assets, bdt(expect["assets"]))
        self.assertEqual(bs.total_liabilities, bdt(expect["liabilities"]))
        self.assertEqual(bs.opening_result, bdt(expect["opening"]))
        self.assertEqual(bs.period_result, pl.net_profit)
        self.assertEqual(bs.total_equity, bdt(expect["total_equity"]))
        self.assertTrue(bs.is_balanced)

        self.assertEqual((fs.posting_count, fs.entry_count), (expect["postings"], expect["entries"]))
        self.assertEqual(
            (fs.period_posting_count, fs.period_entry_count),
            (expect["period_postings"], expect["period_entries"]),
        )
        self.assertEqual((fs.covers_from, fs.as_at), (D(2026, 7, 1), D(2026, 7, 31)))

    def test_fiscal_year_period(self):
        expect = HAND_CHECKED["fy"]
        start, end, label = report.resolve_period(period="FY2026-27", config=tb.Config.load(self.books))
        fs = self.statements(period_start=start, period_end=end, period_label=label)
        pl, bs = fs.profit_and_loss, fs.balance_sheet
        for key in ("revenue", "gross_profit", "operating_profit", "other_expenses", "net_profit"):
            with self.subTest(key=key):
                self.assertEqual(getattr(pl, key), bdt(expect[key]))
        self.assertEqual(bs.opening_result, bdt(expect["opening"]))
        self.assertEqual(bs.accumulated_result, bdt(expect["accumulated"]))
        # as at 2027-06-30 every posting is in, so the position equals the whole ledger's
        whole = HAND_CHECKED["whole"]
        self.assertEqual(fs.trial_balance.total_debit, bdt(whole["tb_total"]))
        self.assertEqual(bs.total_assets, bdt(whole["assets"]))
        self.assertEqual(bs.total_equity, bdt(whole["total_equity"]))
        self.assertEqual(
            (fs.period_posting_count, fs.period_entry_count),
            (expect["period_postings"], expect["period_entries"]),
        )
        self.assertEqual(fs.as_at, D(2027, 6, 30))

    def test_from_to_window(self):
        expect = HAND_CHECKED["june"]
        fs = self.statements(period_start=D(2026, 6, 1), period_end=D(2026, 6, 30))
        self.assertEqual(fs.trial_balance.total_debit, bdt(expect["tb_total"]))
        self.assertEqual(fs.profit_and_loss.net_profit, bdt(expect["net_profit"]))
        self.assertEqual(fs.profit_and_loss.cost_of_sales, M.zero())
        self.assertTrue(fs.profit_and_loss.section("cost_of_sales").is_empty)
        bs = fs.balance_sheet
        self.assertEqual(bs.total_assets, bdt(expect["assets"]))
        self.assertEqual(bs.total_liabilities, bdt(expect["liabilities"]))
        self.assertEqual(bs.opening_result, bdt(expect["opening"]))
        self.assertEqual(bs.total_equity, bdt(expect["total_equity"]))
        self.assertTrue(bs.is_balanced)

    def test_from_only_runs_to_the_last_posting(self):
        fs = self.statements(period_start=D(2026, 8, 1))
        self.assertEqual((fs.covers_from, fs.as_at), (D(2026, 8, 1), D(2026, 8, 31)))
        self.assertEqual(fs.profit_and_loss.revenue, bdt("50000.00"))
        self.assertEqual(fs.profit_and_loss.other_expenses, bdt("10000.00"))
        self.assertEqual(fs.profit_and_loss.net_profit, bdt("40000.00"))
        self.assertEqual(fs.balance_sheet.opening_result, bdt("120888.89"))
        self.assertEqual(fs.balance_sheet.accumulated_result, bdt("160888.89"))
        self.assertEqual((fs.period_posting_count, fs.period_entry_count), (6, 3))

    def test_to_only_starts_at_the_first_posting(self):
        fs = self.statements(period_end=D(2026, 7, 31))
        self.assertEqual((fs.covers_from, fs.as_at), (D(2026, 6, 1), D(2026, 7, 31)))
        self.assertEqual(fs.balance_sheet.opening_result, M.zero())
        self.assertEqual(fs.profit_and_loss.net_profit, bdt("120888.89"))
        self.assertEqual(fs.trial_balance.total_debit, bdt(HAND_CHECKED["july"]["tb_total"]))

    def test_window_with_no_postings_gives_a_zero_pl_but_the_cumulative_position(self):
        fs = self.statements(period_start=D(2027, 1, 1), period_end=D(2027, 1, 31))
        self.assertEqual(fs.profit_and_loss.net_profit, M.zero())
        self.assertTrue(all(section.is_empty for section in fs.profit_and_loss.sections))
        self.assertEqual((fs.period_posting_count, fs.period_entry_count), (0, 0))
        self.assertEqual(fs.balance_sheet.opening_result, bdt("160888.89"))
        self.assertEqual(fs.balance_sheet.total_assets, bdt(HAND_CHECKED["whole"]["assets"]))
        self.assertTrue(fs.balance_sheet.is_balanced)
        text = report.render_markdown(fs)
        self.assertIn("No postings fall inside the reporting period", text)

    def test_empty_books_report_zero_everywhere(self):
        empty = write_books(self.root / "empty", journals=False)
        fs = report.build_statements(tb.Ledger.load(empty))
        self.assertEqual(fs.posting_count, 0)
        self.assertEqual(fs.trial_balance.lines, ())
        self.assertTrue(fs.trial_balance.is_balanced)
        self.assertTrue(fs.balance_sheet.is_balanced)
        self.assertIsNone(fs.as_at)
        self.assertEqual(fs.as_at_text, "the end of the books")
        self.assertEqual(
            report.report_filenames(fs),
            {
                "trial_balance": "trial-balance_all.csv",
                "profit_and_loss": "profit-and-loss_start_all.csv",
                "balance_sheet": "balance-sheet_all.csv",
            },
        )
        self.assertIn("The journal has no postings", report.render_markdown(fs))


# ======================================================================================
# Integrity — a report that does not reconcile is never printed
# ======================================================================================


class TestIntegrity(BooksTestCase):
    def setUp(self):
        super().setUp()
        self.chart = tb.ChartOfAccounts.from_toml_bytes(ACCOUNTS_TOML.encode("utf-8"))

    def posting(self, day, entry_id, account, debit="0", credit="0"):
        return tb.Posting(
            date=day, entry_id=entry_id, description=entry_id, account=account,
            debit=bdt(debit), credit=bdt(credit),
        )

    def test_unbalanced_books_never_reach_the_report(self):
        journal = self.books / "journal" / "2026-08.csv"
        with journal.open("a", encoding="utf-8") as handle:
            handle.write("2026-08-31,BAD-001,Half an entry,1100,10.00,0.00,,,NONE,\n")
        with self.assertRaises(tb.BalanceError) as ctx:
            report.build_statements(self.load())
        self.assertEqual(ctx.exception.exit_code, 5)
        self.assertIn("BAD-001", ctx.exception.message)
        _, err = self.run_cli("--books", str(self.books), "--no-csv", expect=5)
        self.assertIn("BAD-001", err)
        self.assertIn("error:", err)
        _, err = self.run_cli("--books", str(self.books), "--no-csv", "--json", expect=5)
        payload = json.loads(err)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["exit_code"], 5)

    def test_trial_balance_that_does_not_tie_raises_balance_error(self):
        ledger = tb.Ledger(
            [self.posting(D(2026, 7, 1), "LOP", "1100", debit="100.00")], chart=self.chart
        )
        with self.assertRaises(tb.BalanceError) as ctx:
            report.build_statements(ledger)
        exc = ctx.exception
        self.assertEqual(exc.exit_code, 5)
        self.assertIn("trial balance", exc.message)
        self.assertIn("রেওয়ামিল", exc.message)
        self.assertEqual(exc.difference, bdt("100.00"))
        self.assertEqual((exc.total_debit, exc.total_credit), (bdt("100.00"), M.zero()))

    def test_an_entry_straddling_the_period_end_is_reported_not_hidden(self):
        ledger = tb.Ledger(
            [
                self.posting(D(2026, 7, 31), "STRADDLE", "1100", debit="500.00"),
                self.posting(D(2026, 8, 1), "STRADDLE", "4100", credit="500.00"),
            ],
            chart=self.chart,
        )
        report.build_statements(ledger)  # the whole ledger is fine
        with self.assertRaises(tb.BalanceError) as ctx:
            report.build_statements(ledger, period_end=D(2026, 7, 31))
        self.assertIn("straddle", ctx.exception.message)
        self.assertIn("validate.py", ctx.exception.message)

    def test_off_chart_account_cannot_be_placed_on_a_statement(self):
        ledger = tb.Ledger(
            [
                self.posting(D(2026, 7, 1), "X", "1100", debit="1.00"),
                self.posting(D(2026, 7, 1), "X", "9999", credit="1.00"),
            ],
            chart=self.chart,
        )
        with self.assertRaises(tb.UnknownAccountError) as ctx:
            report.build_statements(ledger)
        self.assertEqual(ctx.exception.code, "9999")

    def test_a_chart_is_required(self):
        with self.assertRaises(tb.LedgerError):
            report.build_statements(tb.Ledger([]))

    def test_balance_sheet_check_fires_and_exits_7_when_tampered(self):
        ledger = self.load()
        fs = report.build_statements(ledger)
        inflated = dataclasses.replace(
            fs.balance_sheet,
            assets=dataclasses.replace(fs.balance_sheet.assets, total=fs.balance_sheet.total_assets + M(1)),
        )
        self.assertFalse(inflated.is_balanced)
        checks = report._reconcile(fs.trial_balance, fs.profit_and_loss, inflated, ledger, ledger)
        failed = [c for c in checks if not c.ok]
        self.assertEqual([c.name for c in failed], ["balance_sheet_assets_equal_liabilities_plus_equity"])
        self.assertIn("0.01", failed[0].detail)
        with self.assertRaises(tb.ValidationError) as ctx:
            report._raise_for(failed, fs.trial_balance, inflated, None, None)
        self.assertEqual(ctx.exception.exit_code, 7)
        self.assertIn("do not reconcile", ctx.exception.message)
        self.assertTrue(any("balance_sheet" in p for p in ctx.exception.problems))

    def test_unconventional_code_blocks_still_land_in_a_pl_section(self):
        self.assertEqual(report._pl_section_key("income", "X-INC"), "revenue")
        self.assertEqual(report._pl_section_key("expense", "E-MISC"), "operating_expenses")
        self.assertEqual(report._pl_section_key("income", "7100"), "other_income")
        self.assertEqual(report._pl_section_key("expense", "9100"), "other_expenses")
        chart = tb.ChartOfAccounts(
            [
                tb.Account(code="1100", name="Cash", type="asset", normal="debit"),
                tb.Account(code="X-INC", name="Odd income", type="income", normal="credit"),
                tb.Account(code="E-MISC", name="Odd expense", type="expense", normal="debit"),
            ]
        )
        ledger = tb.Ledger(
            [
                self.posting(D(2026, 7, 1), "A", "1100", debit="300.00"),
                self.posting(D(2026, 7, 1), "A", "X-INC", credit="300.00"),
                self.posting(D(2026, 7, 2), "B", "E-MISC", debit="120.00"),
                self.posting(D(2026, 7, 2), "B", "1100", credit="120.00"),
            ],
            chart=chart,
        )
        fs = report.build_statements(ledger)
        self.assertEqual(fs.profit_and_loss.revenue, bdt("300.00"))
        self.assertEqual(fs.profit_and_loss.operating_expenses, bdt("120.00"))
        self.assertEqual(fs.profit_and_loss.net_profit, bdt("180.00"))
        self.assertEqual(fs.balance_sheet.total_assets, bdt("180.00"))
        self.assertTrue(all(check.ok for check in fs.checks))

    def test_report_module_never_calls_float(self):
        source = (ENGINE_DIR / "report.py").read_text(encoding="utf-8")
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
        for index, token in enumerate(tokens):
            if token.type == tokenize.NAME and token.string == "float":
                following = tokens[index + 1]
                self.assertFalse(
                    following.type == tokenize.OP and following.string == "(",
                    f"float() call at line {token.start[0]}",
                )


# ======================================================================================
# Two renderings, one computation
# ======================================================================================


class TestRenderingsAgree(BooksTestCase):
    def setUp(self):
        super().setUp()
        self.fs = self.statements()
        self.markdown = report.render_markdown(self.fs)
        self.tables = markdown_tables(self.markdown)
        self.reports_dir = self.root / "out"
        self.files = report.write_csv_reports(self.fs, self.reports_dir)

    def csv_rows(self, path: Path) -> list[dict[str, str]]:
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_trial_balance_markdown_and_csv_match_row_for_row(self):
        md = table_for(self.tables, "Trial balance")
        rows = self.csv_rows(self.files[0])
        self.assertEqual(len(md), len(rows))
        self.assertEqual(len(rows), len(HAND_CHECKED["whole"]["balances"]) + 1)
        for md_row, csv_row in zip(md, rows):
            code, _label, _type, debit, credit, balance = md_row
            self.assertEqual(code, csv_row["code"])
            self.assertEqual(ungroup(debit), csv_row["debit"])
            self.assertEqual(ungroup(credit), csv_row["credit"])
            self.assertEqual(ungroup(balance), csv_row["balance"])
        self.assertEqual(rows[-1]["kind"], "total")
        self.assertEqual(rows[-1]["debit"], HAND_CHECKED["whole"]["tb_total"])
        self.assertEqual(rows[-1]["credit"], HAND_CHECKED["whole"]["tb_total"])

    def _amount_statement_agrees(self, heading_word: str, path: Path, expected_total: str):
        md = [row for row in table_for(self.tables, heading_word) if row[2]]  # skip headings
        rows = self.csv_rows(path)
        self.assertEqual(len(md), len(rows))
        for md_row, csv_row in zip(md, rows):
            code, _label, amount = md_row
            self.assertEqual(code, csv_row["code"])
            self.assertEqual(ungroup(amount), csv_row["amount"])
        self.assertEqual(rows[-1]["kind"], "total")
        self.assertEqual(rows[-1]["amount"], expected_total)
        self.assertNotIn("heading", {row["kind"] for row in rows})

    def test_profit_and_loss_markdown_and_csv_match_row_for_row(self):
        self._amount_statement_agrees(
            "Profit and loss", self.files[1], HAND_CHECKED["whole"]["net_profit"]
        )

    def test_balance_sheet_markdown_and_csv_match_row_for_row(self):
        self._amount_statement_agrees("Balance sheet", self.files[2], HAND_CHECKED["whole"]["assets"])

    def test_csv_amounts_are_plain_decimals_never_grouped(self):
        plain = re.compile(r"^-?\d+\.\d{2}$")
        for path in self.files:
            for row in self.csv_rows(path):
                for column in ("debit", "credit", "balance", "amount"):
                    value = row.get(column)
                    if value:
                        self.assertRegex(value, plain, f"{path.name}: {column}={value!r}")

    def test_markdown_uses_lakh_crore_grouping_and_proves_both_identities(self):
        self.assertIn("13,18,580.23", self.markdown)
        self.assertIn("7,97,888.89", self.markdown)
        self.assertIn("6,60,888.89", self.markdown)
        self.assertNotIn("1,318,580.23", self.markdown)
        self.assertIn("**Debits equal credits**", self.markdown)
        self.assertIn("রেওয়ামিল মিলেছে", self.markdown)
        self.assertIn("**Assets equal Liabilities plus Equity**", self.markdown)
        self.assertIn("৳7,97,888.89 = ৳1,37,000.00 + ৳6,60,888.89", self.markdown)
        self.assertIn("স্থিতিপত্র মিলেছে", self.markdown)
        self.assertIn("**Net profit carried to the balance sheet** — ৳1,60,888.89", self.markdown)
        self.assertEqual(self.markdown.count("- **PASS**"), 4)
        self.assertNotIn("FAIL", self.markdown)

    def test_markdown_states_the_business_the_assessment_year_and_the_terms(self):
        self.assertIn("Ticon Sys Demo Traders (টিকন সিস ডেমো ট্রেডার্স)", self.markdown)
        self.assertIn("করবর্ষ / assessment year: 2026-27", self.markdown)
        self.assertIn("## রেওয়ামিল / Trial balance — as at 2026-08-31", self.markdown)
        self.assertIn("## লাভ-ক্ষতি হিসাব / Profit and loss — 2026-06-01 → 2026-08-31", self.markdown)
        self.assertIn("## স্থিতিপত্র / Balance sheet — as at 2026-08-31", self.markdown)
        self.assertIn("Retained earnings brought forward (প্রারম্ভিক সংরক্ষিত মুনাফা)", self.markdown)

    def test_markdown_ends_with_the_disclaimer_and_attribution(self):
        tail = self.markdown.rstrip().splitlines()
        self.assertEqual(tail[-1], tb.ATTRIBUTION)
        self.assertEqual(tail[-3], tb.DISCLAIMER_EN)
        self.assertNotIn(tb.DISCLAIMER_BN, self.markdown)

    def test_bangla_locale_adds_the_bangla_disclaimer(self):
        books = write_books(self.root / "bn", config=CONFIG_TOML.replace('language = "en"', 'language = "bn-en"'))
        text = report.render_markdown(report.build_statements(tb.Ledger.load(books)))
        self.assertIn(tb.DISCLAIMER_EN, text)
        self.assertIn(tb.DISCLAIMER_BN, text)

    def test_single_statement_rendering(self):
        text = report.render_markdown(self.fs, statement="pl")
        self.assertIn("## লাভ-ক্ষতি হিসাব", text)
        self.assertNotIn("## রেওয়ামিল", text)
        self.assertNotIn("## স্থিতিপত্র", text)
        self.assertIn("Reconciliations performed", text)
        self.assertIn(tb.DISCLAIMER_EN, text)
        text = report.render_markdown(self.fs, statement="tb")
        self.assertIn("## রেওয়ামিল", text)
        self.assertNotIn("## স্থিতিপত্র", text)
        with self.assertRaises(tb.ValidationError):
            report.render_markdown(self.fs, statement="cashflow")

    def test_international_grouping_can_be_requested(self):
        text = report.render_markdown(self.fs, grouping=tb.GROUPING_INTL)
        self.assertIn("1,318,580.23", text)
        self.assertNotIn("13,18,580.23", text, "the reconciliation lines must follow the tables")
        self.assertIn("total debits ৳1,318,580.23 vs total credits ৳1,318,580.23", text)

    def test_rows_are_the_shared_spine(self):
        tb_rows = report.trial_balance_rows(self.fs.trial_balance)
        self.assertEqual(tb_rows[-1].kind, "total")
        self.assertEqual(tb_rows[-1].debit, self.fs.trial_balance.total_debit)
        pl_rows = report.profit_and_loss_rows(self.fs.profit_and_loss)
        self.assertEqual(pl_rows[-1].amount, self.fs.profit_and_loss.net_profit)
        bs_rows = report.balance_sheet_rows(self.fs.balance_sheet)
        profit_row = next(r for r in bs_rows if r.label_en.startswith("Profit for the period"))
        self.assertEqual(profit_row.amount, self.fs.profit_and_loss.net_profit)
        self.assertEqual(bs_rows[-1].amount, self.fs.balance_sheet.total_liabilities_and_equity)
        kinds = {row.kind for row in pl_rows + bs_rows}
        self.assertEqual(kinds, {"heading", "line", "subtotal", "total"})


# ======================================================================================
# CSV files, JSON, CLI
# ======================================================================================


class TestFilesAndCli(BooksTestCase):
    def test_csvs_land_in_books_reports_with_deterministic_names(self):
        out, _ = self.run_cli("--books", str(self.books))
        reports = self.books / "reports"
        names = sorted(p.name for p in reports.iterdir())
        self.assertEqual(
            names,
            [
                "balance-sheet_2026-08-31.csv",
                "profit-and-loss_2026-06-01_2026-08-31.csv",
                "trial-balance_2026-08-31.csv",
            ],
        )
        self.assertFalse(list(reports.glob("*.takabooks-tmp")))
        for name in names:
            self.assertIn(name, out)
        before = {p.name: p.read_bytes() for p in reports.iterdir()}
        self.run_cli("--books", str(self.books))
        after = {p.name: p.read_bytes() for p in reports.iterdir()}
        self.assertEqual(before, after, "re-running must rewrite byte-identical CSVs")
        text = (reports / "trial-balance_2026-08-31.csv").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("section,kind,code,account,account_bn,debit,credit,balance\n"))
        self.assertIn("\nasset,line,1100,Cash in Hand,হাতে নগদ,165000.00,0.00,165000.00\n", text)
        self.assertNotIn("\r", text)

    def test_period_flags_name_the_files_and_reports_dir_and_no_csv_are_honoured(self):
        custom = self.root / "elsewhere"
        self.run_cli("--books", str(self.books), "--period", "2026-07", "--reports-dir", str(custom))
        self.assertEqual(
            sorted(p.name for p in custom.iterdir()),
            [
                "balance-sheet_2026-07-31.csv",
                "profit-and-loss_2026-07-01_2026-07-31.csv",
                "trial-balance_2026-07-31.csv",
            ],
        )
        self.assertFalse((self.books / "reports").exists())
        self.run_cli("--books", str(self.books), "--no-csv")
        self.assertFalse((self.books / "reports").exists())

    def test_json_output(self):
        out, err = self.run_cli("--books", str(self.books), "--json", "--period", "2026-07")
        self.assertEqual(err, "")
        payload = json.loads(out)
        expect = HAND_CHECKED["july"]
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["assessment_year"], "2026-27")
        self.assertEqual(payload["period"]["start"], "2026-07-01")
        self.assertEqual(payload["period"]["as_at"], "2026-07-31")
        self.assertEqual(payload["period"]["period_postings"], expect["period_postings"])
        self.assertEqual(payload["trial_balance"]["total_debit"], expect["tb_total"])
        self.assertTrue(payload["trial_balance"]["balanced"])
        self.assertEqual(payload["profit_and_loss"]["net_profit"], expect["net_profit"])
        self.assertEqual(payload["balance_sheet"]["opening_result"], expect["opening"])
        self.assertEqual(payload["balance_sheet"]["period_result"], expect["net_profit"])
        self.assertEqual(payload["balance_sheet"]["total_equity"], expect["total_equity"])
        self.assertEqual(payload["balance_sheet"]["total_assets"], expect["assets"])
        self.assertTrue(payload["balance_sheet"]["balanced"])
        self.assertTrue(all(check["ok"] for check in payload["checks"]))
        tb_check = payload["checks"][0]
        self.assertEqual(tb_check["name"], "trial_balance_debits_equal_credits")
        self.assertEqual(tb_check["amounts"], [expect["tb_total"], expect["tb_total"], "0.00"])
        self.assertIn("৳11,38,580.23", tb_check["detail"])
        self.assertEqual(len(payload["files"]), 3)
        self.assertEqual(payload["disclaimer_en"], tb.DISCLAIMER_EN)
        self.assertEqual(payload["attribution"], tb.ATTRIBUTION)
        self.assertIn("হাতে নগদ", out, "Bangla must not be ASCII-escaped")
        bank = next(l for l in payload["trial_balance"]["lines"] if l["code"] == "1110")
        self.assertEqual(bank["balance"], expect["bank"][2])

    def test_json_and_markdown_and_csv_carry_the_same_numbers(self):
        out, _ = self.run_cli("--books", str(self.books), "--json")
        payload = json.loads(out)
        md, _ = self.run_cli("--books", str(self.books))
        rows = table_for(markdown_tables(md), "Balance sheet")
        total = next(r for r in rows if r[1].startswith("Total liabilities and equity"))
        self.assertEqual(ungroup(total[2]), payload["balance_sheet"]["total_liabilities_and_equity"])
        with (self.books / "reports" / "balance-sheet_2026-08-31.csv").open(encoding="utf-8", newline="") as h:
            last = list(csv.DictReader(h))[-1]
        self.assertEqual(last["amount"], payload["balance_sheet"]["total_liabilities_and_equity"])

    def test_help_and_version(self):
        out, _ = self.run_cli("--help", expect=0)
        for flag in ("--books", "--json", "--from", "--to", "--period", "--statement", "--no-csv"):
            self.assertIn(flag, out)
        self.assertIn("রেওয়ামিল", out)
        out, err = self.run_cli("--version", expect=0)
        self.assertIn(tb.__version__, out + err)

    def test_cli_errors_exit_non_zero_with_a_message(self):
        _, err = self.run_cli("--books", str(self.root / "nowhere"), expect=4)
        self.assertIn("error:", err)
        _, err = self.run_cli("--books", str(self.books), "--period", "2026-07", "--from", "2026-07-01", expect=7)
        self.assertIn("--period cannot be combined", err)
        _, err = self.run_cli("--books", str(self.books), "--from", "2026-08-01", "--to", "2026-07-01", expect=7)
        self.assertIn("after", err)
        _, err = self.run_cli("--books", str(self.books), "--period", "FY2026-28", expect=7)
        self.assertIn("2027", err)
        _, err = self.run_cli("--books", str(self.books), "--statement", "cashflow", expect=2)
        self.assertIn("invalid choice", err)
        self.assertFalse((self.books / "reports").exists(), "no CSV is written on failure")

    def test_cli_period_forms_and_statement_selection(self):
        out, _ = self.run_cli("--books", str(self.books), "--period", "2026-27", "--statement", "bs", "--no-csv")
        self.assertIn("FY2026-27 (fiscal year starting 07-01): 2026-07-01 → 2027-06-30", out)
        self.assertIn("## স্থিতিপত্র", out)
        self.assertNotIn("## রেওয়ামিল", out)
        self.assertIn("80,000.00", out)  # brought forward
        self.assertIn("80,888.89", out)  # profit for the period
        out, _ = self.run_cli("--books", str(self.books), "--from", "2026-06-01", "--to", "2026-06-30", "--statement", "tb", "--no-csv")
        self.assertIn("6,35,000.00", out)
        out, _ = self.run_cli("--books", str(self.books), "--grouping", "international", "--no-csv")
        self.assertIn("1,318,580.23", out)

    def test_build_parser_has_the_standard_flags(self):
        parser = report.build_parser()
        args = parser.parse_args([])
        self.assertEqual(args.books, "books")
        self.assertFalse(args.json)
        self.assertEqual(args.statement, "all")
        self.assertIsNone(args.period)
        self.assertIsNone(args.date_from)
        self.assertIsNone(args.date_to)


if __name__ == "__main__":
    unittest.main()
