"""Tests for ``src/engine/post.py`` and ``src/engine/init_books.py``.

Run with::

    python3 -m unittest discover tests

Spec §7 asks for the double-entry invariant to be proved at the gate: an unbalanced
entry, an unknown account, a malformed date and a bad ``tax_tag`` must each fail
loudly, name themselves and leave the journal untouched.  Beyond that this file
checks that generated entry ids are deterministic, that ``--dry-run`` previews the
exact bytes a real run writes, that rows written by ``post.py`` are rows the rest
of the engine (``Ledger.load``) accepts, and that ``init_books.py`` scaffolds books
without inventing a statutory value.

TakaBooks — Moshiur Rahman (@bemoshiur) · Ticon Sys — https://ticonsys.com
"""

from __future__ import annotations

import contextlib
import datetime
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = REPO_ROOT / "src" / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import takabooks as tb  # noqa: E402
import init_books  # noqa: E402
import post  # noqa: E402

M = tb.Money
POST_SCRIPT = ENGINE_DIR / "post.py"
INIT_SCRIPT = ENGINE_DIR / "init_books.py"


# ======================================================================================
# Helpers
# ======================================================================================


def scaffold(books: Path, *extra: str) -> None:
    """Create a books/ directory with init_books, silencing its output."""
    argv = [
        "--books", str(books), "--name", "Test Co", "--name-bn", "টেস্ট কোং",
        "--fiscal-year-start", "07-01", "--assessment-year", "2026-27", *extra,
    ]
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        code = init_books.main(argv)
    assert code == 0, "scaffold failed"


ACCOUNTS_TEMPLATE = REPO_ROOT / "src" / "templates" / "accounts.toml"


def shipped_chart() -> tb.ChartOfAccounts:
    """The chart ``init_books.py`` actually installs — ``src/templates/accounts.toml``.

    ``init_books`` reaches for its built-in chart only when that template is missing
    (proved by ``test_templates.test_init_books_uses_this_template_not_its_fallback``),
    so books scaffolded in these tests carry the shipped codes.  Per spec §4.4 the
    9xxx block holds the tax accounts: মূসক / VAT output payable is **9200**, VAT
    input / rebateable is 9100 and উৎসে কর কর্তন / TDS payable is 9320.
    """
    return tb.ChartOfAccounts.from_toml_path(ACCOUNTS_TEMPLATE)


def fallback_chart() -> tb.ChartOfAccounts:
    """The emergency chart carried inside ``init_books.py`` (numbered differently)."""
    return tb.ChartOfAccounts.from_toml_bytes(
        init_books.FALLBACK_ACCOUNTS_TOML.encode("utf-8"), source_path="accounts.toml"
    )


def L(account: str, debit=None, credit=None, **kwargs) -> post.LineSpec:
    return post.LineSpec(account=account, debit=debit, credit=credit, **kwargs)


def E(*lines: post.LineSpec, date: str = "2026-07-15", **kwargs) -> post.EntrySpec:
    kwargs.setdefault("description", "Test entry")
    return post.EntrySpec(date=date, lines=tuple(lines), **kwargs)


def sale() -> post.EntrySpec:
    """A three-line VAT sale that balances: Dr 1200 11,500 / Cr 4100 10,000 / Cr 9200 1,500."""
    return E(
        L("1200", debit="11500.00"),
        L("4100", credit="10000.00"),
        L("9200", credit="1500.00", tax_tag="VAT:OUT:15"),
        description="Sale to Rahim Traders",
        party="Rahim Traders",
        doc_ref="INV-0012",
    )


def run_cli(*args: str, stdin_text: str | None = None, script: Path = POST_SCRIPT):
    """Run a script as a real subprocess, exactly as a user or an LLM would."""
    return subprocess.run(
        [sys.executable, str(script), *args],
        input=stdin_text,
        stdin=None if stdin_text is not None else subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(REPO_ROOT),
    )


class BooksCase(unittest.TestCase):
    """A fresh scaffolded books/ directory per test."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.books = self.root / "books"
        scaffold(self.books)
        self.journal = self.books / "journal"


# ======================================================================================
# parse_amount
# ======================================================================================


class TestParseAmount(unittest.TestCase):
    def test_plain_and_grouped_strings(self):
        self.assertEqual(post.parse_amount("1000"), M(100000))
        self.assertEqual(post.parse_amount("1,00,000.00"), M(10000000))
        self.assertEqual(post.parse_amount("1,234,567.89"), M(123456789))
        self.assertEqual(post.parse_amount("৳ 1,234.56"), M(123456))
        self.assertEqual(post.parse_amount("১২৩৪.৫৬"), M(123456))

    def test_blank_means_zero(self):
        for value in (None, "", "   ", "-"):
            self.assertEqual(post.parse_amount(value), M.zero())

    def test_int_and_decimal(self):
        self.assertEqual(post.parse_amount(5), M(500))
        self.assertEqual(post.parse_amount(Decimal("12.34")), M(1234))

    def test_money_passes_through(self):
        self.assertEqual(post.parse_amount(M(7)), M(7))

    def test_float_is_refused(self):
        with self.assertRaises(tb.JournalError) as ctx:
            post.parse_amount(1000.5, where="line 1")
        self.assertIn("float", ctx.exception.message)
        self.assertTrue(ctx.exception.message.startswith("line 1: "))

    def test_bool_is_refused(self):
        with self.assertRaises(tb.JournalError):
            post.parse_amount(True)

    def test_sub_paisa_is_refused_not_rounded(self):
        with self.assertRaises(tb.JournalError) as ctx:
            post.parse_amount("1.005", what="debit")
        self.assertIn("1.005", ctx.exception.message)
        with self.assertRaises(tb.JournalError):
            post.parse_amount(Decimal("1.005"))

    def test_garbage_is_refused_with_location(self):
        with self.assertRaises(tb.JournalError) as ctx:
            post.parse_amount("abc", what="credit", where="--credit #2")
        self.assertTrue(ctx.exception.message.startswith("--credit #2: "))
        self.assertIn("abc", ctx.exception.message)

    def test_negative_parses_here_and_is_refused_later(self):
        self.assertEqual(post.parse_amount("(500)"), M(-50000))


# ======================================================================================
# parse_line_arg
# ======================================================================================


class TestParseLineArg(unittest.TestCase):
    def test_debit_line(self):
        line = post.parse_line_arg("1100=1000.00", post.SIDE_DEBIT)
        self.assertEqual(line.account, "1100")
        self.assertEqual(line.debit, "1000.00")
        self.assertIsNone(line.credit)
        self.assertEqual(line.tax_tag, tb.TAG_NONE)

    def test_credit_line_with_tag(self):
        line = post.parse_line_arg("9200=1500:VAT:OUT:15", post.SIDE_CREDIT)
        self.assertIsNone(line.debit)
        self.assertEqual(line.credit, "1500")
        self.assertEqual(line.tax_tag, "VAT:OUT:15")

    def test_whitespace_and_grouping_survive(self):
        line = post.parse_line_arg("  1100 = 1,00,000.00 ", post.SIDE_DEBIT)
        self.assertEqual(line.account, "1100")
        self.assertEqual(line.debit, "1,00,000.00")

    def test_missing_equals(self):
        with self.assertRaises(tb.JournalError) as ctx:
            post.parse_line_arg("1100 1000", post.SIDE_DEBIT)
        self.assertIn("ACCOUNT=AMOUNT", ctx.exception.message)

    def test_blank_account_or_amount(self):
        with self.assertRaises(tb.JournalError):
            post.parse_line_arg("=100", post.SIDE_DEBIT)
        with self.assertRaises(tb.JournalError):
            post.parse_line_arg("1100=", post.SIDE_DEBIT)

    def test_origin_label_in_message(self):
        with self.assertRaises(tb.JournalError) as ctx:
            post.parse_line_arg("nope", post.SIDE_CREDIT, origin="--credit #3")
        self.assertTrue(ctx.exception.message.startswith("--credit #3: "))

    def test_bad_side_is_a_programming_error(self):
        with self.assertRaises(ValueError):
            post.parse_line_arg("1100=1", "sideways")


# ======================================================================================
# parse_json_entry
# ======================================================================================


class TestParseJsonEntry(unittest.TestCase):
    DOC = {
        "date": "2026-07-15",
        "entry_id": "MANUAL-1",
        "description": "Purchase",
        "party": "Karim Supplies",
        "doc_ref": "BILL-7",
        "memo": "paid by bKash, ref 123",
        "lines": [
            {"account": "5100", "debit": "8000"},
            {"account": "9100", "debit": "1200", "tax_tag": "VAT:IN:15", "memo": "input VAT"},
            {"account": "2100", "credit": 9200},
        ],
    }

    def test_full_document_from_text(self):
        spec = post.parse_json_entry(json.dumps(self.DOC), where="stdin")
        self.assertEqual(spec.date, "2026-07-15")
        self.assertEqual(spec.entry_id, "MANUAL-1")
        self.assertEqual(spec.party, "Karim Supplies")
        self.assertEqual(spec.memo, "paid by bKash, ref 123")
        self.assertEqual(len(spec.lines), 3)
        self.assertEqual(spec.lines[0].origin, "stdin lines[0]")
        self.assertEqual(spec.lines[1].tax_tag, "VAT:IN:15")
        self.assertEqual(spec.lines[1].memo, "input VAT")
        self.assertIsNone(spec.lines[0].memo)  # inherits the entry memo later
        self.assertEqual(spec.lines[2].credit, 9200)
        self.assertEqual(spec.source, "stdin")

    def test_mapping_and_bytes_inputs(self):
        self.assertEqual(post.parse_json_entry(self.DOC).date, "2026-07-15")
        self.assertEqual(post.parse_json_entry(json.dumps(self.DOC).encode("utf-8")).date, "2026-07-15")

    def test_aliases(self):
        doc = {"date": "2026-07-15", "id": "X1", "narration": "n",
               "postings": [{"code": "1100", "debit": "1", "tag": "NONE"}]}
        spec = post.parse_json_entry(doc)
        self.assertEqual(spec.entry_id, "X1")
        self.assertEqual(spec.description, "n")
        self.assertEqual(spec.lines[0].account, "1100")
        self.assertEqual(spec.lines[0].tax_tag, "NONE")

    def test_bare_list_is_lines_only(self):
        spec = post.parse_json_entry([{"account": "1100", "debit": "1"}])
        self.assertEqual(spec.date, "")
        self.assertEqual(len(spec.lines), 1)

    def test_floats_become_decimal_never_float(self):
        spec = post.parse_json_entry('{"date": "2026-07-15", "lines": [{"account": "1100", "debit": 1500.5}]}')
        self.assertIsInstance(spec.lines[0].debit, Decimal)
        self.assertEqual(spec.lines[0].debit, Decimal("1500.5"))

    def test_unknown_keys_are_rejected(self):
        with self.assertRaises(tb.JournalError) as ctx:
            post.parse_json_entry({"date": "2026-07-15", "narrations": "x", "lines": []})
        self.assertIn("narrations", ctx.exception.message)
        with self.assertRaises(tb.JournalError) as ctx:
            post.parse_json_entry({"date": "2026-07-15", "lines": [{"account": "1", "amount": "5"}]})
        self.assertIn("amount", ctx.exception.message)
        self.assertIn("lines[0]", ctx.exception.message)

    def test_malformed_documents(self):
        with self.assertRaises(tb.JournalError) as ctx:
            post.parse_json_entry("not json", where="stdin")
        self.assertIn("not valid JSON", ctx.exception.message)
        with self.assertRaises(tb.JournalError) as ctx:
            post.parse_json_entry("   ", where="stdin")
        self.assertIn("empty", ctx.exception.message)
        with self.assertRaises(tb.JournalError):
            post.parse_json_entry('"just a string"')
        with self.assertRaises(tb.JournalError) as ctx:
            post.parse_json_entry({"date": "2026-07-15"})
        self.assertIn('"lines" is missing', ctx.exception.message)
        with self.assertRaises(tb.JournalError):
            post.parse_json_entry({"date": "2026-07-15", "lines": "1100=1"})
        with self.assertRaises(tb.JournalError):
            post.parse_json_entry({"date": "2026-07-15", "lines": ["1100=1"]})

    def test_single_posting_shape_gets_a_pointer(self):
        with self.assertRaises(tb.JournalError) as ctx:
            post.parse_json_entry({"date": "2026-07-15", "account": "1100", "debit": "5"})
        self.assertIn('"lines"', ctx.exception.message)

    def test_structured_text_fields_are_rejected(self):
        with self.assertRaises(tb.JournalError):
            post.parse_json_entry({"date": ["2026-07-15"], "lines": []})
        with self.assertRaises(tb.JournalError):
            post.parse_json_entry({"date": "2026-07-15", "lines": [{"account": {"code": 1}}]})


# ======================================================================================
# generate_entry_id — deterministic, no clock, no randomness
# ======================================================================================


class TestGenerateEntryId(unittest.TestCase):
    JULY = datetime.date(2026, 7, 15)

    def test_first_of_month(self):
        self.assertEqual(post.generate_entry_id(self.JULY, []), "JE-2026-07-0001")

    def test_next_after_highest(self):
        ids = ["JE-2026-07-0007", "JE-2026-07-0002", "JE-2026-08-0040", "MANUAL-9"]
        self.assertEqual(post.generate_entry_id(self.JULY, ids), "JE-2026-07-0008")
        self.assertEqual(post.generate_entry_id(datetime.date(2026, 8, 1), ids), "JE-2026-08-0041")
        self.assertEqual(post.generate_entry_id(datetime.date(2026, 9, 1), ids), "JE-2026-09-0001")

    def test_ignores_lookalikes(self):
        ids = ["JE-2026-07-0009x", "JE-2026-07-", "JE-2026-07-abc", "je-2026-07-0050"]
        self.assertEqual(post.generate_entry_id(self.JULY, ids), "JE-2026-07-0001")

    def test_deterministic_regardless_of_order(self):
        a = post.generate_entry_id(self.JULY, ["JE-2026-07-0003", "JE-2026-07-0001"])
        b = post.generate_entry_id(self.JULY, ["JE-2026-07-0001", "JE-2026-07-0003"])
        self.assertEqual(a, b)
        self.assertEqual(a, post.generate_entry_id("2026-07-31", {"JE-2026-07-0003"}))

    def test_sequence_grows_past_four_digits(self):
        self.assertEqual(post.generate_entry_id(self.JULY, ["JE-2026-07-9999"]), "JE-2026-07-10000")

    def test_never_collides(self):
        ids: set[str] = set()
        for _ in range(25):
            new = post.generate_entry_id(self.JULY, ids)
            self.assertNotIn(new, ids)
            ids.add(new)
        self.assertEqual(len(ids), 25)


# ======================================================================================
# build_entry — every refusal named, nothing silently fixed
# ======================================================================================


class TestBuildEntry(unittest.TestCase):
    def setUp(self) -> None:
        self.chart = shipped_chart()

    def build(self, spec, **kwargs):
        kwargs.setdefault("chart", self.chart)
        return post.build_entry(spec, **kwargs)

    def test_balanced_entry_with_generated_id(self):
        built = self.build(sale())
        entry = built.entry
        self.assertTrue(built.generated_id)
        self.assertEqual(entry.entry_id, "JE-2026-07-0001")
        self.assertTrue(entry.is_balanced)
        self.assertEqual(entry.total_debit, M(1150000))
        self.assertEqual([p.account for p in entry.postings], ["1200", "4100", "9200"])
        self.assertEqual(entry.postings[2].tax_tag, tb.TaxTag.parse("VAT:OUT:15"))
        self.assertEqual(entry.postings[0].party, "Rahim Traders")
        self.assertEqual(built.warnings, ())

    def test_debits_are_written_before_credits(self):
        spec = E(L("4100", credit="10"), L("1100", debit="4"), L("1110", debit="6"))
        entry = self.build(spec).entry
        self.assertEqual([p.account for p in entry.postings], ["1100", "1110", "4100"])

    def test_line_level_fields_override_entry_level(self):
        spec = E(
            L("1100", debit="10", memo="cash side", party="Walk-in"),
            L("4100", credit="10", description="own words"),
            description="Cash sale", party="Nobody", doc_ref="R-1", memo="entry memo",
        )
        entry = self.build(spec).entry
        self.assertEqual(entry.postings[0].memo, "cash side")
        self.assertEqual(entry.postings[0].party, "Walk-in")
        self.assertEqual(entry.postings[0].description, "Cash sale")
        self.assertEqual(entry.postings[1].description, "own words")
        self.assertEqual(entry.postings[1].memo, "entry memo")
        self.assertEqual(entry.postings[1].doc_ref, "R-1")

    def test_explicit_id_is_kept(self):
        built = self.build(E(L("1100", debit="1"), L("4100", credit="1"), entry_id=" V-77 "))
        self.assertFalse(built.generated_id)
        self.assertEqual(built.entry.entry_id, "V-77")

    def test_unbalanced_is_a_balance_error_naming_both_sides(self):
        with self.assertRaises(tb.BalanceError) as ctx:
            self.build(E(L("1100", debit="100"), L("4100", credit="90")))
        exc = ctx.exception
        self.assertEqual(exc.exit_code, 5)
        self.assertEqual(exc.difference, M(1000))
        self.assertEqual(exc.total_debit, M(10000))
        self.assertEqual(exc.total_credit, M(9000))
        self.assertIn("does not balance", exc.message)
        self.assertIn("৳100.00", exc.message)
        self.assertIn("৳90.00", exc.message)

    def test_single_line_can_never_balance(self):
        with self.assertRaises(tb.BalanceError):
            self.build(E(L("1100", debit="100")))

    def test_unknown_account(self):
        with self.assertRaises(tb.UnknownAccountError) as ctx:
            self.build(E(L("1201", debit="1"), L("4100", credit="1")))
        self.assertEqual(ctx.exception.exit_code, 3)
        self.assertEqual(ctx.exception.code, "1201")
        self.assertIn("1201", ctx.exception.message)
        self.assertIn("Did you mean", ctx.exception.hint)
        self.assertIn("1200", ctx.exception.hint)

    def test_without_a_chart_accounts_are_not_checked(self):
        entry = post.build_entry(E(L("9999", debit="1"), L("4100", credit="1"))).entry
        self.assertEqual(entry.postings[0].account, "9999")

    def test_bad_and_missing_date(self):
        with self.assertRaises(tb.JournalError) as ctx:
            self.build(E(L("1100", debit="1"), L("4100", credit="1"), date="15-07-2026"))
        self.assertEqual(ctx.exception.exit_code, 4)
        self.assertIn("15-07-2026", ctx.exception.message)
        with self.assertRaises(tb.JournalError) as ctx:
            self.build(E(L("1100", debit="1"), L("4100", credit="1"), date="2026-02-30"))
        self.assertIn("2026-02-30", ctx.exception.message)
        with self.assertRaises(tb.JournalError) as ctx:
            self.build(E(L("1100", debit="1"), L("4100", credit="1"), date=""))
        self.assertIn("date is required", ctx.exception.message)

    def test_bad_tax_tag(self):
        with self.assertRaises(tb.TaxTagError) as ctx:
            self.build(E(L("1100", debit="1"), L("4100", credit="1", tax_tag="VAT:15")))
        self.assertEqual(ctx.exception.exit_code, 6)
        self.assertEqual(ctx.exception.hint, tb.TAX_TAG_GRAMMAR)
        self.assertIn("VAT:15", ctx.exception.message)

    def test_zero_both_sides_and_negative(self):
        with self.assertRaises(tb.JournalError) as ctx:
            self.build(E(L("1100", debit="0"), L("4100", credit="1")))
        self.assertIn("zero", ctx.exception.message)
        with self.assertRaises(tb.JournalError) as ctx:
            self.build(E(L("1100", debit="1", credit="1"), L("4100", credit="1")))
        self.assertIn("both set", ctx.exception.message)
        with self.assertRaises(tb.JournalError) as ctx:
            self.build(E(L("1100", debit="(1)"), L("4100", credit="1")))
        self.assertIn("negative", ctx.exception.message)

    def test_blank_account_and_no_lines(self):
        with self.assertRaises(tb.JournalError) as ctx:
            self.build(E(L("  ", debit="1"), L("4100", credit="1")))
        self.assertIn("blank", ctx.exception.message)
        with self.assertRaises(tb.JournalError) as ctx:
            self.build(E())
        self.assertIn("no posting lines", ctx.exception.message)

    def test_many_problems_are_reported_together(self):
        spec = E(L("9999", debit="100.005"), L("4100", credit="abc", tax_tag="TDS:5"), date="2026-13-45")
        with self.assertRaises(tb.ValidationError) as ctx:
            self.build(spec)
        exc = ctx.exception
        self.assertEqual(exc.exit_code, 7)
        self.assertEqual(len(exc.problems), 5)
        joined = "\n".join(exc.problems)
        for needle in ("2026-13-45", "100.005", "9999", "abc", "TDS:5"):
            self.assertIn(needle, joined)
        self.assertIn("5 problems", exc.message)

    def test_duplicate_id(self):
        spec = E(L("1100", debit="1"), L("4100", credit="1"), entry_id="JE-2026-07-0001")
        with self.assertRaises(tb.DuplicateEntryError) as ctx:
            self.build(spec, existing={"JE-2026-07-0001"})
        self.assertEqual(ctx.exception.entry_id, "JE-2026-07-0001")
        self.assertEqual(ctx.exception.exit_code, 4)
        previous = self.build(E(L("1100", debit="1"), L("4100", credit="1"), entry_id="JE-2026-07-0001")).entry
        with self.assertRaises(tb.DuplicateEntryError) as ctx:
            self.build(spec, existing={"JE-2026-07-0001": previous})
        self.assertIn("dated 2026-07-15", ctx.exception.message)

    def test_generated_id_skips_existing(self):
        built = self.build(E(L("1100", debit="1"), L("4100", credit="1")),
                           existing=["JE-2026-07-0001", "JE-2026-07-0002"])
        self.assertEqual(built.entry.entry_id, "JE-2026-07-0003")

    def test_multiline_entry_id_rejected(self):
        with self.assertRaises(tb.JournalError):
            self.build(E(L("1100", debit="1"), L("4100", credit="1"), entry_id="a\nb"))

    def test_inactive_account_is_refused(self):
        chart = tb.ChartOfAccounts([
            tb.Account(code="1100", name="Cash", type="asset", normal="debit"),
            tb.Account(code="1900", name="Old Petty Cash", type="asset", normal="debit", tags=("closed",)),
            tb.Account(code="4100", name="Sales", type="income", normal="credit"),
        ])
        with self.assertRaises(tb.AccountError) as ctx:
            self.build(E(L("1900", debit="1"), L("4100", credit="1")), chart=chart)
        self.assertEqual(ctx.exception.exit_code, 3)
        self.assertIn("closed", ctx.exception.message)

    def test_tag_on_the_wrong_control_account(self):
        with self.assertRaises(tb.TaxTagError) as ctx:
            self.build(E(L("1100", debit="1"), L("9320", credit="1", tax_tag="VAT:OUT:15")))
        self.assertIn("different tax", ctx.exception.message)
        self.assertIn("tds_payable", ctx.exception.message)

    def test_tag_on_the_right_control_account_is_fine(self):
        built = self.build(E(L("1100", debit="1"), L("9200", credit="1", tax_tag="VAT:OUT:15"), doc_ref="M-1"))
        self.assertEqual(built.warnings, ())
        built = self.build(E(L("6610", debit="100"), L("9320", credit="5", tax_tag="TDS:52AA:5"),
                             L("1150", credit="95"), doc_ref="B-2"))
        self.assertEqual(built.warnings, ())

    def test_warnings_do_not_block(self):
        built = self.build(E(L("1100", debit="115"), L("4100", credit="115", tax_tag="VAT:OUT:15"),
                             description=""))
        text = "\n".join(built.warnings)
        self.assertIn("no description", text)
        self.assertIn("no doc_ref", text)
        self.assertIn("tax-tag orphan", text)
        self.assertIn("9200", text)


# ======================================================================================
# the built-in fallback chart inside init_books.py
# ======================================================================================


class TestFallbackChart(unittest.TestCase):
    """The emergency chart is numbered differently from the shipped template, so it gets
    its own proof: it must parse, and it must still carry every role the engine looks up
    (spec §4.4 — codes are indicative, names and roles are normative)."""

    def setUp(self) -> None:
        self.chart = fallback_chart()

    def test_it_parses_and_is_not_empty(self):
        self.assertGreater(len(self.chart), 0)

    def test_every_mandated_role_is_present(self):
        self.assertEqual(self.chart.missing_roles(), [])
        for role in tb.REQUIRED_ROLES:
            self.assertTrue(self.chart.account_for_role(role).code)

    def test_a_vat_sale_builds_against_it_whatever_its_codes_are(self):
        vat_out = self.chart.account_for_role(tb.ROLE_VAT_OUTPUT).code
        built = post.build_entry(
            E(L("1100", debit="115"), L("4100", credit="100"),
              L(vat_out, credit="15", tax_tag="VAT:OUT:15"), doc_ref="M-1"),
            chart=self.chart,
        )
        self.assertTrue(built.entry.is_balanced)
        self.assertEqual(built.warnings, ())


# ======================================================================================
# post_entry — the filesystem contract
# ======================================================================================


class TestPostEntry(BooksCase):
    def test_first_post_creates_file_with_header(self):
        result = post.post_entry(self.books, sale())
        path = self.journal / "2026-07.csv"
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith(tb.JOURNAL_HEADER + "\n"))
        self.assertEqual(text, result["csv"])
        self.assertTrue(result["created_file"])
        self.assertEqual(result["entry_id"], "JE-2026-07-0001")
        self.assertTrue(result["entry_id_generated"])
        self.assertEqual(result["lines"], 3)
        self.assertEqual(result["total_debit"], M(1150000))
        self.assertEqual(result["tax_tags"], ["VAT:OUT:15"])
        self.assertEqual(result["rows"][2]["tax_tag"], "VAT:OUT:15")
        self.assertEqual(result["rows"][0]["debit"], "11500.00")
        self.assertEqual(result["rows"][0]["credit"], "0.00")
        self.assertEqual(result["postings"][0]["account_name"], "Accounts Receivable — Trade")
        self.assertEqual(result["postings"][0]["amount_formatted"], "৳11,500.00")
        self.assertEqual(result["warnings"], [])
        self.assertIn("Ticon Sys", result["attribution"])

    def test_second_post_appends_without_a_second_header(self):
        post.post_entry(self.books, sale())
        result = post.post_entry(self.books, E(L("6200", debit="20,000"), L("1110", credit="20000"),
                                               description="Office rent", date="2026-07-16"))
        self.assertFalse(result["created_file"])
        self.assertEqual(result["entry_id"], "JE-2026-07-0002")
        lines = (self.journal / "2026-07.csv").read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines.count(tb.JOURNAL_HEADER), 1)
        self.assertEqual(len(lines), 6)
        self.assertEqual(lines[-1], "2026-07-16,JE-2026-07-0002,Office rent,1110,0.00,20000.00,,,NONE,")

    def test_files_are_chosen_by_entry_date(self):
        post.post_entry(self.books, sale())
        result = post.post_entry(self.books, E(L("1100", debit="1"), L("4100", credit="1"), date="2026-08-03"))
        self.assertEqual(Path(result["file"]).name, "2026-08.csv")
        self.assertEqual(result["month"], "2026-08")
        self.assertEqual(result["entry_id"], "JE-2026-08-0001")
        self.assertTrue((self.journal / "2026-08.csv").is_file())

    def test_dry_run_writes_nothing_and_previews_the_exact_bytes(self):
        preview = post.post_entry(self.books, sale(), dry_run=True)
        self.assertTrue(preview["dry_run"])
        self.assertFalse((self.journal / "2026-07.csv").exists())
        self.assertEqual(sorted(self.journal.iterdir()), [])
        real = post.post_entry(self.books, sale())
        self.assertEqual(preview["csv"], real["csv"])
        self.assertEqual(preview["entry_id"], real["entry_id"])
        self.assertEqual((self.journal / "2026-07.csv").read_text(encoding="utf-8"), preview["csv"])

    def test_refusals_leave_the_journal_untouched(self):
        post.post_entry(self.books, sale())
        path = self.journal / "2026-07.csv"
        before = path.read_bytes()
        bad = [
            E(L("1100", debit="100"), L("4100", credit="90")),
            E(L("9999", debit="1"), L("4100", credit="1")),
            E(L("1100", debit="1"), L("4100", credit="1"), date="2026-7-1"),
            E(L("1100", debit="1"), L("4100", credit="1", tax_tag="VDS")),
            E(L("1100", debit="1"), L("4100", credit="1"), entry_id="JE-2026-07-0001"),
        ]
        expected = (tb.BalanceError, tb.UnknownAccountError, tb.JournalError, tb.TaxTagError, tb.DuplicateEntryError)
        for spec, exc_type in zip(bad, expected):
            with self.assertRaises(exc_type):
                post.post_entry(self.books, spec)
            self.assertEqual(path.read_bytes(), before)
        self.assertEqual(sorted(p.name for p in self.journal.iterdir()), ["2026-07.csv"])

    def test_ids_are_deterministic_across_identical_books(self):
        other = self.root / "books2"
        scaffold(other)
        a = [post.post_entry(self.books, sale())["entry_id"] for _ in range(3)]
        b = [post.post_entry(other, sale())["entry_id"] for _ in range(3)]
        self.assertEqual(a, b)
        self.assertEqual(a, ["JE-2026-07-0001", "JE-2026-07-0002", "JE-2026-07-0003"])

    def test_ledger_accepts_what_post_wrote(self):
        post.post_entry(self.books, sale())
        post.post_entry(self.books, E(L("5100", debit="8000"), L("9100", debit="1200", tax_tag="VAT:IN:15"),
                                      L("2100", credit="9200"), description="Purchase", doc_ref="BILL-7",
                                      date="2026-08-01", memo="paid later, by cheque"))
        ledger = tb.Ledger.load(self.books)  # require_balanced=True by default
        self.assertTrue(ledger.is_balanced())
        self.assertEqual(ledger.entry_ids(), ["JE-2026-07-0001", "JE-2026-08-0001"])
        self.assertEqual(ledger.entry("JE-2026-08-0001").postings[2].memo, "paid later, by cheque")
        self.assertEqual(ledger.entry_id_conflicts(), [])
        self.assertEqual(ledger.misfiled_postings(), [])
        self.assertEqual(ledger.out_of_order_dates(), [])
        self.assertEqual(ledger.balance("9100"), M(120000))

    def test_missing_journal_dir_is_created(self):
        os.rmdir(self.journal)
        result = post.post_entry(self.books, sale())
        self.assertTrue(self.journal.is_dir())
        self.assertTrue(any("does not exist yet" in w for w in result["warnings"]))

    def test_pre_existing_imbalance_warns_but_new_entry_is_recorded(self):
        (self.journal / "2026-06.csv").write_text(
            tb.JOURNAL_HEADER + "\n2026-06-30,OLD-1,broken,1100,5.00,0.00,,,NONE,\n", encoding="utf-8"
        )
        result = post.post_entry(self.books, sale())
        self.assertTrue(any("unbalanced" in w and "OLD-1" in w for w in result["warnings"]))
        self.assertTrue((self.journal / "2026-07.csv").is_file())

    def test_back_dated_entry_warns(self):
        post.post_entry(self.books, E(L("1100", debit="1"), L("4100", credit="1"), date="2026-07-20"))
        result = post.post_entry(self.books, E(L("1100", debit="1"), L("4100", credit="1"), date="2026-07-10"))
        self.assertTrue(any("out of order" in w for w in result["warnings"]))

    def test_unreadable_existing_journal_blocks_the_write(self):
        (self.journal / "2026-05.csv").write_text("foo,bar\n1,2\n", encoding="utf-8")
        with self.assertRaises(tb.JournalError):
            post.post_entry(self.books, sale())
        self.assertFalse((self.journal / "2026-07.csv").exists())

    def test_duplicate_id_across_months(self):
        post.post_entry(self.books, E(L("1100", debit="1"), L("4100", credit="1"), entry_id="V-1"))
        with self.assertRaises(tb.DuplicateEntryError):
            post.post_entry(self.books, E(L("1100", debit="1"), L("4100", credit="1"), entry_id="V-1", date="2026-08-01"))
        self.assertFalse((self.journal / "2026-08.csv").exists())

    def test_memo_commas_and_bangla_survive_the_round_trip(self):
        memo = 'bKash, ref 123, "urgent"'
        post.post_entry(self.books, E(L("1100", debit="১,০০,০০০"), L("3100", credit="100000"),
                                      description="মালিকের মূলধন / owner capital", memo=memo))
        entry = tb.Ledger.load(self.books).entry("JE-2026-07-0001")
        self.assertEqual(entry.postings[0].memo, memo)
        self.assertEqual(entry.postings[0].debit, M(10000000))
        self.assertEqual(entry.description, "মালিকের মূলধন / owner capital")

    def test_config_journal_dir_and_locale_are_honoured(self):
        config = self.books / "config.toml"
        text = config.read_text(encoding="utf-8")
        text = text.replace('journal_dir = "journal"', 'journal_dir = "entries"')
        text = text.replace('grouping = "bd"', 'grouping = "international"')
        config.write_text(text, encoding="utf-8")
        os.rename(self.journal, self.books / "entries")
        result = post.post_entry(self.books, E(L("1100", debit="1234567.89"), L("3100", credit="1234567.89")))
        self.assertEqual(Path(result["file"]).parent.name, "entries")
        self.assertTrue((self.books / "entries" / "2026-07.csv").is_file())
        self.assertEqual(result["postings"][0]["amount_formatted"], "৳1,234,567.89")
        self.assertEqual(result["rows"][0]["debit"], "1234567.89")  # CSV never carries grouping

    def test_missing_books_is_a_config_error(self):
        with self.assertRaises(tb.ConfigError):
            post.post_entry(self.root / "nowhere", sale())


# ======================================================================================
# Argument merging and rendering
# ======================================================================================


class TestEntrySpecFromArgs(unittest.TestCase):
    def parse(self, *argv: str):
        return post.build_parser().parse_args(list(argv))

    def test_cli_lines_keep_command_line_order(self):
        args = self.parse("--date", "2026-07-15", "--credit", "4100=10", "--debit", "1100=10")
        spec = post.entry_spec_from_args(args, stdin=io.StringIO(""))
        self.assertEqual([l.account for l in spec.lines], ["4100", "1100"])
        self.assertEqual(spec.lines[0].origin, "--credit #1")
        self.assertEqual(spec.lines[1].origin, "--debit #2")
        self.assertEqual(spec.source, "command line")

    def test_json_plus_cli_merge_with_cli_overrides(self):
        doc = json.dumps({"date": "2026-07-15", "description": "from json", "lines": [{"account": "1100", "debit": "10"}]})
        args = self.parse("--stdin", "--date", "2026-07-20", "--credit", "4100=10")
        spec = post.entry_spec_from_args(args, stdin=io.StringIO(doc))
        self.assertEqual(spec.date, "2026-07-20")
        self.assertEqual(spec.description, "from json")
        self.assertEqual([l.account for l in spec.lines], ["1100", "4100"])
        self.assertEqual(spec.source, "stdin + command line")

    def test_json_flag_reads_a_pipe_only_when_no_lines_given(self):
        doc = json.dumps({"date": "2026-07-15", "lines": [{"account": "1100", "debit": "1"}]})
        args = self.parse("--json")
        spec = post.entry_spec_from_args(args, stdin=io.StringIO(doc))
        self.assertEqual(spec.source, "stdin")
        args = self.parse("--json", "--debit", "1100=1", "--date", "2026-07-15")
        spec = post.entry_spec_from_args(args, stdin=io.StringIO(doc))
        self.assertEqual(spec.source, "command line")
        self.assertEqual(len(spec.lines), 1)

    def test_input_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "entry.json"
            path.write_text(json.dumps({"date": "2026-07-15", "lines": []}), encoding="utf-8")
            spec = post.entry_spec_from_args(self.parse("--input", str(path)))
            self.assertEqual(spec.source, str(path))
            with self.assertRaises(tb.JournalError):
                post.entry_spec_from_args(self.parse("--input", str(Path(tmp) / "missing.json")))

    def test_nothing_given(self):
        with self.assertRaises(tb.JournalError) as ctx:
            post.entry_spec_from_args(self.parse("--date", "2026-07-15"), stdin=io.StringIO(""))
        self.assertIn("No entry given", ctx.exception.message)


class TestRendering(BooksCase):
    def test_render_csv_matches_library_writer(self):
        entry = post.build_entry(sale(), chart=shipped_chart()).entry
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.csv"
            tb.append_journal_csv(path, entry.postings)
            self.assertEqual(path.read_text(encoding="utf-8"), post.render_csv(entry.postings, header=True))
            tb.append_journal_csv(path, entry.postings)
            self.assertTrue(path.read_text(encoding="utf-8").endswith(post.render_csv(entry.postings, header=False)))

    def test_text_rendering(self):
        result = post.post_entry(self.books, sale(), dry_run=True)
        text = post.render_text(result)
        self.assertIn("dry run", text)
        self.assertIn("nothing was written", text)
        self.assertIn("JE-2026-07-0001", text)
        self.assertIn("Dr  1200 Accounts Receivable — Trade (প্রাপ্য হিসাব — বাণিজ্যিক (দেনাদার))", text)
        self.assertIn("Cr  9200 VAT Output Payable", text)
        self.assertIn("VAT:OUT:15 — output মূসক / VAT at 15%", text)
        self.assertIn("debits ৳11,500.00 = credits ৳11,500.00 — balanced", text)
        self.assertIn("would append to", text)
        self.assertIn("2026-07-15,JE-2026-07-0001,Sale to Rahim Traders,1200,11500.00,0.00,Rahim Traders,INV-0012,NONE,", text)
        real = post.render_text(post.post_entry(self.books, sale()))
        self.assertTrue(real.startswith("posted JE-2026-07-0001"))
        self.assertNotIn("would append", real)

    def test_json_rendering_is_plain_json(self):
        result = post.post_entry(self.books, sale())
        data = json.loads(tb.json_dumps(result))
        self.assertTrue(data["ok"])
        self.assertEqual(data["date"], "2026-07-15")
        self.assertEqual(data["total_debit"], "11500.00")
        self.assertEqual(data["postings"][2]["tax_tag"], "VAT:OUT:15")


# ======================================================================================
# The real command line
# ======================================================================================


class TestPostCli(BooksCase):
    def test_help_and_version(self):
        proc = run_cli("--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ACCOUNT=AMOUNT[:TAX_TAG]", proc.stdout)
        self.assertIn("--books", proc.stdout)
        self.assertIn("--json", proc.stdout)
        self.assertIn("exit codes", proc.stdout)
        self.assertIn("Ticon Sys", proc.stdout)
        proc = run_cli("--version")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("TakaBooks", proc.stdout)

    def test_successful_post_text(self):
        proc = run_cli("--books", str(self.books), "--date", "2026-07-15", "--description", "Cash sale",
                       "--doc-ref", "M-1", "--debit", "1100=11500", "--credit", "4100=10000",
                       "--credit", "9200=1500:VAT:OUT:15")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("posted JE-2026-07-0001", proc.stdout)
        self.assertEqual(proc.stderr, "")
        self.assertTrue((self.journal / "2026-07.csv").is_file())

    def test_successful_post_json(self):
        proc = run_cli("--books", str(self.books), "--json", "--date", "2026-07-15", "--description", "x",
                       "--debit", "1100=5", "--credit", "4100=5")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["entry_id"], "JE-2026-07-0001")
        self.assertEqual(data["rows"][0]["debit"], "5.00")

    def test_unbalanced_exits_5_and_writes_nothing(self):
        proc = run_cli("--books", str(self.books), "--date", "2026-07-15", "--description", "x",
                       "--debit", "1100=100", "--credit", "4100=90")
        self.assertEqual(proc.returncode, 5)
        self.assertIn("does not balance", proc.stderr)
        self.assertIn("৳100.00", proc.stderr)
        self.assertEqual(proc.stdout, "")
        self.assertFalse((self.journal / "2026-07.csv").exists())

    def test_unbalanced_json_error_goes_to_stderr(self):
        proc = run_cli("--books", str(self.books), "--json", "--date", "2026-07-15", "--description", "x",
                       "--debit", "1100=100", "--credit", "4100=90")
        self.assertEqual(proc.returncode, 5)
        self.assertEqual(proc.stdout, "")
        data = json.loads(proc.stderr)
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"], "BalanceError")
        self.assertEqual(data["exit_code"], 5)

    def test_exit_codes_per_refusal(self):
        cases = [
            (3, ["--date", "2026-07-15", "--debit", "1201=1", "--credit", "4100=1"]),
            (6, ["--date", "2026-07-15", "--debit", "1100=1", "--credit", "4100=1:VAT:15"]),
            (4, ["--date", "15/07/2026", "--debit", "1100=1", "--credit", "4100=1"]),
            (4, ["--date", "2026-07-15"]),
            (7, ["--date", "2026-13-01", "--debit", "9999=1", "--credit", "4100=1"]),
        ]
        for code, argv in cases:
            proc = run_cli("--books", str(self.books), "--description", "x", *argv)
            self.assertEqual(proc.returncode, code, f"{argv}: {proc.stderr}")
            self.assertTrue(proc.stderr.startswith("error: "), proc.stderr)
        self.assertEqual(sorted(self.journal.iterdir()), [])
        proc = run_cli("--books", str(self.root / "nowhere"), "--date", "2026-07-15",
                       "--debit", "1100=1", "--credit", "4100=1")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("init_books.py", proc.stderr)

    def test_json_entry_via_stdin_flag(self):
        doc = json.dumps({"date": "2026-08-01", "description": "Purchase", "doc_ref": "B-1",
                          "lines": [{"account": "5100", "debit": "8000"},
                                    {"account": "9100", "debit": "1200", "tax_tag": "VAT:IN:15"},
                                    {"account": "2100", "credit": 9200}]})
        proc = run_cli("--books", str(self.books), "--stdin", stdin_text=doc)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("posted JE-2026-08-0001", proc.stdout)
        self.assertIn("VAT:IN:15", (self.journal / "2026-08.csv").read_text(encoding="utf-8"))

    def test_json_flag_reads_piped_stdin(self):
        doc = json.dumps({"date": "2026-08-02", "description": "Bank charge",
                          "lines": [{"account": "6700", "debit": 150}, {"account": "1150", "credit": 150}]})
        proc = run_cli("--books", str(self.books), "--json", stdin_text=doc)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["entry_id"], "JE-2026-08-0001")

    def test_json_flag_with_empty_stdin_and_no_lines_does_not_hang(self):
        proc = run_cli("--books", str(self.books), "--json")  # stdin is DEVNULL
        self.assertEqual(proc.returncode, 4)
        self.assertIn("empty input", json.loads(proc.stderr)["message"])

    def test_input_file_and_dash(self):
        doc = json.dumps({"date": "2026-08-03", "description": "f",
                          "lines": [{"account": "1100", "debit": "1"}, {"account": "4100", "credit": "1"}]})
        path = self.root / "entry.json"
        path.write_text(doc, encoding="utf-8")
        proc = run_cli("--books", str(self.books), "--input", str(path))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        proc = run_cli("--books", str(self.books), "--input", "-", stdin_text=doc)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("JE-2026-08-0002", proc.stdout)

    def test_dry_run_from_cli(self):
        proc = run_cli("--books", str(self.books), "--dry-run", "--date", "2026-09-01", "--description", "x",
                       "--debit", "1100=1", "--credit", "4100=1")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("nothing was written", proc.stdout)
        self.assertIn("2026-09-01,JE-2026-09-0001,x,1100,1.00,0.00,,,NONE,", proc.stdout)
        self.assertFalse((self.journal / "2026-09.csv").exists())

    def test_warnings_go_to_stderr_and_do_not_fail(self):
        proc = run_cli("--books", str(self.books), "--date", "2026-07-15", "--debit", "1100=115",
                       "--credit", "4100=115:VAT:OUT:15")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("warning:", proc.stderr)
        self.assertIn("tax-tag orphan", proc.stderr)


# ======================================================================================
# init_books.py
# ======================================================================================


class TestInitBooks(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.books = self.root / "books"

    def run_main(self, *argv: str):
        out, err = io.StringIO(), io.StringIO()
        code = None
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = init_books.main(list(argv))
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue()

    def test_scaffold_layout(self):
        code, out, err = self.run_main("--books", str(self.books), "--name", "Ticon Sys",
                                       "--fiscal-year-start", "07-01", "--assessment-year", "2026-27",
                                       "--vat-registered", "yes", "--city-tier", "dhaka-chattogram-city")
        self.assertEqual(code, 0, err)
        for name in ("config.toml", "accounts.toml", "journal", "reports"):
            self.assertTrue((self.books / name).exists(), name)
        self.assertEqual(sorted((self.books / "journal").iterdir()), [])
        config = tb.Config.load(self.books)
        self.assertEqual(config.business_name, "Ticon Sys")
        self.assertEqual(config.fiscal_year_start, "07-01")
        self.assertEqual(config.assessment_year, "2026-27")
        self.assertEqual(config.get("compliance.vat_registered"), "yes")
        self.assertEqual(config.get("compliance.city_tier"), "dhaka-chattogram-city")
        chart = tb.ChartOfAccounts.from_toml_path(self.books / "accounts.toml")
        self.assertEqual(chart.missing_roles(), [])
        self.assertEqual(chart.code_format_warnings(), [])
        self.assertEqual(chart.block_warnings(), [])
        self.assertIn("books ready", out)
        self.assertIn("Ticon Sys", out)

    def test_statutory_values_are_never_defaulted(self):
        code, out, _ = self.run_main("--books", str(self.books), "--name", "X")
        self.assertEqual(code, 0)
        config = tb.Config.load(self.books)
        self.assertIsNone(config.fiscal_year_start)
        self.assertIsNone(config.assessment_year)
        text = (self.books / "config.toml").read_text(encoding="utf-8")
        self.assertIn('# fiscal_year_start = "MM-DD"', text)
        self.assertIn('# assessment_year = "YYYY-YY"', text)
        self.assertIn("fiscal_year_start", out)  # next-steps nag
        with self.assertRaises(tb.ConfigError):
            config.require_assessment_year()

    def test_no_rate_or_threshold_in_the_scaffold(self):
        """The scaffold writes labels only: every TOML value is text, never a number."""
        self.run_main("--books", str(self.books))
        import tomllib

        def walk(node, where: str) -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    walk(value, f"{where}.{key}")
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    walk(value, f"{where}[{index}]")
            else:
                self.assertIsInstance(node, str, f"{where} = {node!r} is a figure, not a label")

        for name in ("config.toml", "accounts.toml"):
            text = (self.books / name).read_text(encoding="utf-8")
            walk(tomllib.loads(text), name)
            body = "\n".join(
                line.split("#", 1)[0] for line in text.splitlines() if not line.lstrip().startswith("#")
            ).lower()
            for word in ("rate =", "threshold", "slab", "%", "deadline"):
                self.assertNotIn(word, body, f"{name} carries {word!r} outside a comment")

    def test_refuses_to_overwrite_without_force(self):
        self.run_main("--books", str(self.books), "--name", "First")
        before = (self.books / "config.toml").read_bytes()
        code, out, err = self.run_main("--books", str(self.books), "--name", "Second")
        self.assertEqual(code, 2)
        self.assertIn("refusing", err)
        self.assertIn("--force", err)
        self.assertEqual((self.books / "config.toml").read_bytes(), before)

    def test_force_rewrites_config_but_never_journals(self):
        self.run_main("--books", str(self.books), "--name", "First", "--start-month", "2026-07")
        journal = self.books / "journal" / "2026-07.csv"
        journal.write_text(tb.JOURNAL_HEADER + "\n2026-07-01,X,keep me,1100,1.00,0.00,,,NONE,\n", encoding="utf-8")
        code, out, _ = self.run_main("--books", str(self.books), "--name", "Second", "--force", "--start-month", "2026-07")
        self.assertEqual(code, 0)
        self.assertEqual(tb.Config.load(self.books).business_name, "Second")
        self.assertIn("keep me", journal.read_text(encoding="utf-8"))
        self.assertIn("overwritten", out)

    def test_dry_run_writes_nothing(self):
        code, out, _ = self.run_main("--books", str(self.books), "--dry-run", "--name", "Ghost")
        self.assertEqual(code, 0)
        self.assertFalse(self.books.exists())
        self.assertIn("dry run", out)
        code, out, _ = self.run_main("--books", str(self.books), "--dry-run", "--json")
        data = json.loads(out)
        self.assertTrue(data["dry_run"])
        self.assertIn("config_preview", data)
        self.assertFalse(self.books.exists())

    def test_bad_inputs_exit_2(self):
        for argv in (["--fiscal-year-start", "13-01"], ["--assessment-year", "26"], ["--start-month", "2026-7"]):
            code, _, err = self.run_main("--books", str(self.books), *argv)
            self.assertEqual(code, 2, argv)
            self.assertIn("error:", err)
        self.assertFalse(self.books.exists())
        code, _, err = self.run_main("--books", str(self.books), "--templates", str(self.root / "missing"))
        self.assertEqual(code, 2)

    def test_start_month_seeds_an_exact_header(self):
        self.run_main("--books", str(self.books), "--start-month", "2026-07")
        seed = self.books / "journal" / "2026-07.csv"
        self.assertEqual(seed.read_text(encoding="utf-8"), tb.JOURNAL_HEADER + "\n")
        self.assertEqual(tb.read_journal_csv(seed), [])

    def test_json_output(self):
        code, out, _ = self.run_main("--books", str(self.books), "--json", "--name", "J",
                                     "--assessment-year", "2026-27", "--rates-file", "rates-AY2026-27.toml")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertTrue(data["ok"])
        self.assertEqual(data["accounts"], len(shipped_chart()))
        self.assertEqual(data["missing_roles"], [])
        self.assertEqual(sorted(data["roles_present"]), sorted(tb.REQUIRED_ROLES))
        self.assertEqual(data["warnings"], [])
        self.assertIn("Ticon Sys", data["attribution"])

    def test_rates_file_year_mismatch_warns(self):
        code, _, err = self.run_main("--books", str(self.books), "--assessment-year", "2026-27",
                                     "--rates-file", "rates-AY2025-26.toml")
        self.assertEqual(code, 0)
        self.assertIn("warning:", err)
        self.assertIn("2026-27", err)

    def test_templates_are_used_but_statutory_values_are_not_copied(self):
        templates = self.root / "templates"
        templates.mkdir()
        (templates / "config.toml").write_text(
            '[business]\nname = "Demo"\n[books]\ncurrency = "BDT"\nfiscal_year_start = "07-01"\n'
            '[locale]\nlanguage = "bn-en"\ngrouping = "bd"\ndigits = "latin"\n', encoding="utf-8")
        (templates / "accounts.toml").write_text(
            '[[account]]\ncode = "1100"\nname = "Cash"\ntype = "asset"\nnormal = "debit"\n'
            '[[account]]\ncode = "4100"\nname = "Sales"\ntype = "income"\nnormal = "credit"\n', encoding="utf-8")
        (templates / "journal-header.csv").write_text(tb.JOURNAL_HEADER + "\n", encoding="utf-8")
        code, out, err = self.run_main("--books", str(self.books), "--templates", str(templates),
                                       "--start-month", "2026-07")
        self.assertEqual(code, 0, err)
        config = tb.Config.load(self.books)
        self.assertEqual(config.business_name, "")            # demo identity never inherited
        self.assertIsNone(config.fiscal_year_start)           # statutory value never copied
        self.assertEqual(config.language, "bn-en")            # non-statutory default inherited
        self.assertIn("does not copy statutory values", err)
        self.assertIn("missing spec §4.4 role", err)          # the tiny template chart lacks roles
        self.assertEqual(len(tb.ChartOfAccounts.from_toml_path(self.books / "accounts.toml")), 2)

    def test_template_header_mismatch_is_fatal(self):
        templates = self.root / "templates"
        templates.mkdir()
        (templates / "journal-header.csv").write_text("date,entry_id,memo\n", encoding="utf-8")
        code, _, err = self.run_main("--books", str(self.books), "--templates", str(templates),
                                     "--start-month", "2026-07")
        self.assertEqual(code, 4)
        self.assertIn("header", err)
        self.assertFalse(self.books.exists())

    def test_interactive_with_no_input_uses_defaults(self):
        with mock.patch("builtins.input", side_effect=EOFError):
            code, out, _ = self.run_main("--books", str(self.books), "--interactive")
        self.assertEqual(code, 0)
        config = tb.Config.load(self.books)
        self.assertEqual(config.business_name, "")
        self.assertEqual(config.get("compliance.vat_registered"), "unknown")
        self.assertEqual(config.get("compliance.city_tier"), "unspecified")

    def test_interactive_answers_are_used(self):
        answers = iter(["Prompted Co", "", "company", "", "", "", "07-01", "2026-27", "", "yes", "other-city"])
        with mock.patch("builtins.input", side_effect=lambda *_: next(answers)):
            code, _, err = self.run_main("--books", str(self.books), "-i")
        self.assertEqual(code, 0, err)
        config = tb.Config.load(self.books)
        self.assertEqual(config.business_name, "Prompted Co")
        self.assertEqual(config.business_type, "company")
        self.assertEqual(config.fiscal_year_start, "07-01")
        self.assertEqual(config.get("compliance.vat_registered"), "yes")
        self.assertEqual(config.get("compliance.city_tier"), "other-city")

    def test_render_config_toml_round_trips(self):
        values = {
            "business_name": 'Quote "Co"', "business_name_bn": "কোং", "business_type": "company",
            "tin": "1234", "bin": "5678", "address": "Dhaka\nBangladesh", "currency": "BDT",
            "fiscal_year_start": "07-01", "assessment_year": "2026-27", "rates_file": "",
            "accounts_file": "accounts.toml", "journal_dirname": "journal", "language": "en",
            "grouping": "bd", "digits": "latin", "vat_registered": "no", "city_tier": "other-area",
        }
        text = init_books.render_config_toml(values)
        import tomllib
        config = tb.Config.from_mapping(tomllib.loads(text))
        self.assertEqual(config.business_name, 'Quote "Co"')
        self.assertEqual(config.address, "Dhaka\nBangladesh")
        self.assertEqual(config.assessment_year, "2026-27")
        self.assertIn(tb.ATTRIBUTION, text)

    def test_labels_are_bilingual(self):
        for key, (bn, en) in init_books.CITY_TIERS.items():
            self.assertTrue(bn and en, key)
        self.assertEqual(init_books.VAT_REGISTRATION_CHOICES, ("yes", "no", "unknown"))

    def test_cli_subprocess(self):
        proc = run_cli("--books", str(self.books), "--name", "Sub Co", "--json", script=INIT_SCRIPT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(json.loads(proc.stdout)["ok"])
        proc = run_cli("--books", str(self.books), script=INIT_SCRIPT)
        self.assertEqual(proc.returncode, 2)
        proc = run_cli("--help", script=INIT_SCRIPT)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("--force", proc.stdout)
        self.assertIn("--vat-registered", proc.stdout)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
