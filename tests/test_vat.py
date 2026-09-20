"""Tests for ``src/engine/vat.py`` — the মূসক / VAT position (spec §4.6, §7).

Run with::

    python3 -m unittest discover tests

What is covered, per spec §7 "VAT: output/input/net position, VDS":

* output VAT, rebateable input VAT, net payable / carry-forward, VDS withheld — golden
  arithmetic on int paisa with ROUND_HALF_UP, checked by hand;
* per-entry reconciliation of posted VAT against taxable value × the tag's own rate;
* control-account opening / tagged / other / closing across periods;
* every statutory figure read from the rates TOML: missing required keys exit non-zero,
  ``verified = false`` and ``placeholder = true`` are surfaced on every output format,
  the assessment-year file used is printed;
* Markdown, CSV and ``--json`` renderings from one computation, ending with the
  disclaimer;
* the CLI: ``--help``, ``--books``, ``--json``, non-zero exit on every integrity failure.

**Every rate in these fixtures is synthetic** (10%, 2.5%, 7.5%, made-up thresholds and
prose deadlines).  They exist to exercise arithmetic and plumbing and assert nothing
about Bangladeshi law — the rates file the tests write is labelled FIXTURE throughout.

TakaBooks — Moshiur Rahman (@bemoshiur) · TICON SYSTEM LTD — https://ticonsys.com
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
import tokenize
import unittest
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = REPO_ROOT / "src" / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import rates as rt  # noqa: E402
import takabooks as tb  # noqa: E402
import tax  # noqa: E402  (posture symmetry is asserted against the other engine)
import vat  # noqa: E402

M = tb.Money
D = Decimal


# ======================================================================================
# Fixtures — synthetic books and a synthetic rates file
# ======================================================================================

ACCOUNTS_TOML = """\
[[account]]
code = "1100"
name = "Cash in Hand"
name_bn = "হাতে নগদ"
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
name = "VAT Input Rebateable"
name_bn = "রেয়াতযোগ্য উপকরণ মূসক"
type = "asset"
normal = "debit"
role = "vat_input"

[[account]]
code = "2100"
name = "Accounts Payable"
name_bn = "প্রদেয় হিসাব"
type = "liability"
normal = "credit"

[[account]]
code = "2310"
name = "VAT Output Payable"
name_bn = "প্রদেয় উৎপাদ মূসক"
type = "liability"
normal = "credit"
role = "vat_output"

[[account]]
code = "2320"
name = "TDS Payable"
name_bn = "প্রদেয় উৎসে কর"
type = "liability"
normal = "credit"
role = "tds_payable"

[[account]]
code = "2330"
name = "VDS Payable"
name_bn = "প্রদেয় উৎসে কর্তিত মূসক"
type = "liability"
normal = "credit"
role = "vds_payable"

[[account]]
code = "4100"
name = "Sales"
name_bn = "বিক্রয়"
type = "income"
normal = "credit"

[[account]]
code = "5100"
name = "Purchases"
name_bn = "ক্রয়"
type = "expense"
normal = "debit"

[[account]]
code = "6200"
name = "Consultancy Expense"
name_bn = "পরামর্শ ব্যয়"
type = "expense"
normal = "debit"
"""

#: The same chart with no VAT roles declared at all.
ACCOUNTS_TOML_NO_ROLES = ACCOUNTS_TOML.replace('role = "vat_input"\n', "").replace(
    'role = "vat_output"\n', ""
).replace('role = "vds_payable"\n', "")


def config_toml(*, language: str = "bn-en", assessment_year: str | None = "2026-27",
                rates_file: str | None = None) -> str:
    books = ['currency = "BDT"', 'fiscal_year_start = "07-01"']
    if assessment_year:
        books.append(f'assessment_year = "{assessment_year}"')
    if rates_file:
        books.append(f'rates_file = "{rates_file}"')
    return (
        "[business]\n"
        'name = "Fixture Traders"\n'
        'name_bn = "ফিক্সচার ট্রেডার্স"\n'
        'type = "proprietorship"\n'
        'bin = "000000000-0000"\n'
        'tin = "000000000000"\n'
        "\n[books]\n" + "\n".join(books) + "\n"
        "\n[locale]\n"
        f'language = "{language}"\n'
        'grouping = "bd"\n'
        'digits = "latin"\n'
    )


HEADER = tb.JOURNAL_HEADER

# A 10% sale: value line 4100, tax line 2310 (role vat_output).
SALE = [
    "2026-07-05,S-001,Sale to Karim,1200,11000.00,,Karim,INV-1,NONE,",
    "2026-07-05,S-001,Sale to Karim,4100,,10000.00,Karim,INV-1,VAT:OUT:10,",
    "2026-07-05,S-001,Sale to Karim,2310,,1000.00,Karim,INV-1,VAT:OUT:10,",
]
# A 10% purchase: value line 5100, tax line 1310 (role vat_input).
PURCHASE = [
    "2026-07-10,P-001,Purchase from Alam,5100,4000.00,,Alam,BILL-7,VAT:IN:10,",
    "2026-07-10,P-001,Purchase from Alam,1310,400.00,,Alam,BILL-7,VAT:IN:10,",
    "2026-07-10,P-001,Purchase from Alam,2100,,4400.00,Alam,BILL-7,NONE,",
]
# A service bill with 10% VDS withheld: value line 6200, tax line 2330 (role vds_payable).
VDS = [
    "2026-07-20,C-001,Consultancy from Sultana,6200,20000.00,,Sultana,BILL-9,VDS:10,",
    "2026-07-20,C-001,Consultancy from Sultana,2330,,2000.00,Sultana,BILL-9,VDS:10,",
    "2026-07-20,C-001,Consultancy from Sultana,2100,,18000.00,Sultana,BILL-9,NONE,",
]


def rates_toml(
    *,
    verified: bool = True,
    placeholder: bool = False,
    placeholder_keys: tuple[str, ...] = (),
    unverified_keys: tuple[str, ...] = (),
    file_placeholder: bool = False,
    assessment_year: str | None = "2026-27",
    standard: str = '"10"',
    omit: tuple[str, ...] = (),
    extra: str = "",
) -> str:
    """A rates file whose every figure is a labelled FIXTURE, never a real BD figure.

    ``placeholder_keys`` / ``unverified_keys`` mark *individual* nodes, which is how the
    MIXED case is built: a file where some figures have landed and some have not.
    """

    def node(key: str, value: str, unit: str, label_en: str, label_bn: str) -> str:
        if key in omit:
            return ""
        is_verified = verified and key not in unverified_keys and key not in placeholder_keys
        flags = f"verified = {'true' if is_verified else 'false'}\n"
        if placeholder or key in placeholder_keys:
            flags += "placeholder = true\n"
        return (
            f"[{key}]\n"
            f'label_en = "{label_en} (FIXTURE)"\n'
            f'label_bn = "{label_bn}"\n'
            f"value = {value}\n"
            f'unit = "{unit}"\n'
            'source = "https://example.invalid/fixture"\n'
            'as_of = "2026-09-01"\n'
            f"{flags}\n"
        )

    meta = "[meta]\n"
    if assessment_year:
        meta += f'assessment_year = "{assessment_year}"\n'
    if file_placeholder:
        meta += 'status = "placeholder"\nplaceholder = true\n'
    meta += 'note = "FIXTURE — every value below is synthetic test data"\n\n'

    return (
        meta
        + node("vat.rates.standard", standard, "percent", "Standard rate", "প্রমিত হার")
        + node("vat.rates.zero_rated", "0", "percent", "Zero-rated", "শূন্যহার")
        + node("vat.rates.reduced.fixture_supply", '"2.5"', "percent", "Reduced rate", "হ্রাসকৃত হার")
        + node("vat.thresholds.registration", "1234567", "BDT", "Registration threshold", "নিবন্ধন সীমা")
        + node(
            "vat.thresholds.turnover_tax_enlistment",
            '"765432.50"',
            "BDT",
            "Turnover enlistment threshold",
            "তালিকাভুক্তি সীমা",
        )
        + node("vat.turnover_tax.rate", '"1.5"', "percent", "Turnover tax rate", "টার্নওভার হার")
        + node("vds.services.fixture_service", '"7.5"', "percent", "Fixture service", "ফিক্সচার সেবা")
        + node(
            "deadlines.vat_return_monthly",
            '"FIXTURE: the Nth day of the following month"',
            "date",
            "Monthly return deadline",
            "দাখিলের সময়সীমা",
        )
        + node(
            "deadlines.vat_return_quarterly",
            '"FIXTURE: within N days of the end of every three tax periods"',
            "date",
            "Quarterly return deadline",
            "ত্রৈমাসিক দাখিলের সময়সীমা",
        )
        + node(
            "deadlines.vat_legacy_settlement_s137a",
            '"FIXTURE: legacy settlement window closes on a fixture date"',
            "date",
            "Legacy VAT settlement window",
            "পুরনো মূসক দাবি নিষ্পত্তির সুযোগ",
        )
        + node(
            "vds.deposit.deadline",
            '"FIXTURE: within N days of deduction"',
            "date",
            "VDS deposit deadline",
            "জমার সময়সীমা",
        )
        + extra
    )


RETURN_FORM_EXTRA = """
[vat.return_form]
note = "FIXTURE form map"

[[vat.return_form.line]]
line = "F-1"
figure = "output.tax"
label_en = "Fixture output line"
label_bn = "ফিক্সচার উৎপাদ"

[[vat.return_form.line]]
line = "F-2"
figure = "no.such.figure"
label_en = "Fixture broken line"
"""


class VatFixture(unittest.TestCase):
    """Base class: a temp directory with books/ and a rates file."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.books = self.root / "books"
        self.rates_path = self.root / "rates-AY2026-27.toml"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # -- builders ----------------------------------------------------------------------

    def write_books(
        self,
        journals: dict[str, list[str]] | None = None,
        *,
        accounts: str = ACCOUNTS_TOML,
        config: str | None = None,
    ) -> Path:
        (self.books / "journal").mkdir(parents=True, exist_ok=True)
        (self.books / "config.toml").write_text(config or config_toml(), encoding="utf-8")
        (self.books / "accounts.toml").write_text(accounts, encoding="utf-8")
        for month, rows in (journals or {"2026-07": SALE + PURCHASE + VDS}).items():
            (self.books / "journal" / f"{month}.csv").write_text(
                HEADER + "\n" + "\n".join(rows) + "\n", encoding="utf-8"
            )
        return self.books

    def write_rates(self, text: str | None = None, *, name: str | None = None) -> Path:
        path = self.root / name if name else self.rates_path
        path.write_text(text if text is not None else rates_toml(), encoding="utf-8")
        return path

    def position(
        self,
        *,
        journals: dict[str, list[str]] | None = None,
        rates: str | None = None,
        period: str | None = "2026-07",
        accounts: str = ACCOUNTS_TOML,
        config: str | None = None,
        allow_placeholders: bool = False,
    ) -> vat.VatPosition:
        books = self.write_books(journals, accounts=accounts, config=config)
        rates_path = self.write_rates(rates)
        ledger = tb.Ledger.load(books)
        # Deliberately still a takabooks.RatesTable: compute_vat_position must keep
        # accepting the parser object and adapt it onto the one reader itself.
        table = tb.RatesTable.from_toml_path(rates_path)
        since, until, label = vat.resolve_period(period=period)
        return vat.compute_vat_position(
            ledger,
            rates=table,
            since=since,
            until=until,
            period_label=label,
            allow_placeholders=allow_placeholders,
        )

    def cli(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = vat.main(list(argv))
            except SystemExit as exc:  # argparse / cli_guard
                code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
        return code, out.getvalue(), err.getvalue()


# ======================================================================================
# Module surface
# ======================================================================================


class TestModuleSurface(unittest.TestCase):
    def test_every_exported_name_exists(self):
        for name in vat.__all__:
            self.assertTrue(hasattr(vat, name), name)

    def test_no_float_call_anywhere_in_vat_py(self):
        """Money is int paisa; the module must never construct a float (spec §4.2)."""
        source = (ENGINE_DIR / "vat.py").read_text(encoding="utf-8")
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
        for index, token in enumerate(tokens[:-1]):
            if token.type == tokenize.NAME and token.string == "float":
                following = tokens[index + 1]
                self.assertFalse(
                    following.type == tokenize.OP and following.string == "(",
                    f"float() call at line {token.start[0]}",
                )

    def test_no_bangladeshi_rate_is_hardcoded(self):
        """The only percentages in the module are in docstrings; none drives arithmetic.

        Guard: no ``Decimal("15")`` / ``percent(15)`` style literal reaches the code path.
        """
        source = (ENGINE_DIR / "vat.py").read_text(encoding="utf-8")
        for needle in ('Decimal("15")', "percent(15)", 'Decimal("7.5")', 'Decimal("5")'):
            self.assertNotIn(needle, source)

    def test_rate_text_trims_zeros(self):
        self.assertEqual(vat.rate_text(D("15.00")), "15")
        self.assertEqual(vat.rate_text(D("7.50")), "7.5")
        self.assertEqual(vat.rate_text(D("0")), "0")
        self.assertEqual(vat.rate_text(D("0.0")), "0")

    def test_reference_specs_read_canonical_keys(self):
        keys = {spec.rates_key for spec in vat.REFERENCE_SPECS}
        self.assertIn("vat.rates.standard", keys)
        self.assertIn("deadlines.vat_return_quarterly", keys)
        self.assertIn("deadlines.vat_return_monthly", keys)
        self.assertIn("deadlines.vat_legacy_settlement_s137a", keys)
        self.assertIn("vds.deposit.deadline", keys)
        self.assertIn("vat.thresholds.turnover_tax_enlistment", keys)
        required = {s.rates_key for s in vat.REFERENCE_SPECS if s.required == vat.REQUIRED_ALWAYS}
        self.assertEqual(required, {"vat.rates.standard", "deadlines.vat_return_quarterly"})

    def test_shipped_rates_file_keys_are_the_ones_vat_reads(self):
        """The real ``src/data/rates-AY2026-27.toml`` must carry every key vat.py reads,
        so a placeholder file never looks like a missing one."""
        shipped = REPO_ROOT / "src" / "data" / "rates-AY2026-27.toml"
        if not shipped.is_file():  # pragma: no cover - data file owned elsewhere
            self.skipTest("shipped rates file not present")
        table = tb.RatesTable.from_toml_path(shipped)
        for spec in vat.REFERENCE_SPECS:
            self.assertTrue(table.has(spec.rates_key), spec.rates_key)


# ======================================================================================
# Period resolution
# ======================================================================================


class TestResolvePeriod(unittest.TestCase):
    def test_month_expands_to_inclusive_window(self):
        start, end, label = vat.resolve_period(period="2026-07")
        self.assertEqual((start, end), (datetime.date(2026, 7, 1), datetime.date(2026, 7, 31)))
        self.assertEqual(label, "2026-07")

    def test_february_leap_year(self):
        _, end, _ = vat.resolve_period(period="2028-02")
        self.assertEqual(end, datetime.date(2028, 2, 29))

    def test_bad_month_is_config_error(self):
        with self.assertRaises(tb.ConfigError):
            vat.resolve_period(period="2026-13")
        with self.assertRaises(tb.ConfigError):
            vat.resolve_period(period="July 2026")

    def test_period_cannot_combine_with_range(self):
        with self.assertRaises(tb.ConfigError):
            vat.resolve_period(period="2026-07", since="2026-07-01")

    def test_range_and_open_ends(self):
        start, end, label = vat.resolve_period(since="2026-07-01", until="2026-09-30")
        self.assertEqual(start, datetime.date(2026, 7, 1))
        self.assertEqual(end, datetime.date(2026, 9, 30))
        self.assertIn("2026-07-01", label)
        self.assertEqual(vat.resolve_period(), (None, None, "every posting in the books"))
        self.assertEqual(vat.resolve_period(since="2026-07-01")[2], "from 2026-07-01")

    def test_reversed_range_rejected(self):
        with self.assertRaises(tb.ConfigError):
            vat.resolve_period(since="2026-09-01", until="2026-07-01")

    def test_non_iso_dates_rejected(self):
        with self.assertRaises(tb.JournalError):
            vat.resolve_period(since="01-07-2026")


# ======================================================================================
# Finding and loading the rates file
# ======================================================================================


class TestRatesResolution(VatFixture):
    def test_explicit_path_wins(self):
        path = self.write_rates()
        self.assertEqual(vat.resolve_rates_path(explicit=path), path)

    def test_config_rates_file_relative_to_books(self):
        self.write_books(config=config_toml(rates_file="my-rates.toml"))
        target = self.books / "my-rates.toml"
        target.write_text(rates_toml(), encoding="utf-8")
        config = tb.Config.load(self.books)
        found = vat.resolve_rates_path(config=config, books_dir=self.books, data_dir=self.root / "nowhere")
        self.assertEqual(found, target)

    def test_config_rates_file_missing_is_rates_error(self):
        self.write_books(config=config_toml(rates_file="ghost.toml"))
        config = tb.Config.load(self.books)
        with self.assertRaises(tb.RatesError) as ctx:
            vat.resolve_rates_path(config=config, books_dir=self.books, data_dir=self.root)
        self.assertIn("ghost.toml", str(ctx.exception))
        self.assertEqual(ctx.exception.exit_code, 8)

    def test_assessment_year_file_in_data_dir(self):
        self.write_books()
        path = self.write_rates()
        config = tb.Config.load(self.books)
        self.assertEqual(vat.resolve_rates_path(config=config, data_dir=self.root), path)

    def test_single_file_used_when_year_unknown(self):
        self.write_books(config=config_toml(assessment_year=None))
        path = self.write_rates(name="rates-AY2030-31.toml")
        config = tb.Config.load(self.books)
        self.assertEqual(vat.resolve_rates_path(config=config, data_dir=self.root), path)

    def test_several_files_without_a_year_refuses_to_choose(self):
        self.write_books(config=config_toml(assessment_year=None))
        self.write_rates(name="rates-AY2030-31.toml")
        self.write_rates(name="rates-AY2031-32.toml")
        config = tb.Config.load(self.books)
        with self.assertRaises(tb.RatesError):
            vat.resolve_rates_path(config=config, data_dir=self.root)

    def test_no_file_at_all_is_rates_error(self):
        with self.assertRaises(tb.RatesError) as ctx:
            vat.resolve_rates_path(data_dir=self.root / "empty")
        self.assertIn("No rates file", str(ctx.exception))

    def test_assessment_year_mismatch_is_fatal_unless_allowed(self):
        self.write_books()
        path = self.write_rates(rates_toml(assessment_year="2031-32"), name="rates-AY2031-32.toml")
        config = tb.Config.load(self.books)
        with self.assertRaises(tb.RatesError) as ctx:
            vat.load_rates(explicit=path, config=config)
        self.assertIn("2031-32", str(ctx.exception))
        rates, warnings = vat.load_rates(explicit=path, config=config, allow_ay_mismatch=True)
        self.assertEqual(rates.assessment_year, "2031-32")
        self.assertTrue(any("MISMATCH" in w for w in warnings))

    def test_file_without_assessment_year_warns(self):
        self.write_books()
        path = self.write_rates(rates_toml(assessment_year=None), name="rates.toml")
        config = tb.Config.load(self.books)
        _, warnings = vat.load_rates(explicit=path, config=config)
        self.assertTrue(any("NO ASSESSMENT YEAR" in w for w in warnings))


# ======================================================================================
# Reference figures and declared rates read from the rates file
# ======================================================================================


class TestReferenceFigures(VatFixture):
    def table(self, text: str | None = None) -> tb.RatesTable:
        return tb.RatesTable.from_toml_path(self.write_rates(text))

    def test_verified_file_reads_cleanly(self):
        figures, warnings = vat.reference_figures(self.table(), vds_present=True)
        self.assertEqual(warnings, [])
        by_key = {f.key: f for f in figures}
        self.assertEqual(by_key["standard_rate"].display, "10%")
        self.assertEqual(by_key["registration_threshold"].money, M.from_str("1234567"))
        self.assertEqual(by_key["turnover_tax_enlistment_threshold"].money, M.from_str("765432.50"))
        self.assertTrue(all(f.status == "verified" for f in figures), [f.status for f in figures])
        self.assertTrue(all(f.usable for f in figures))

    def test_missing_required_key_is_rates_error_naming_the_key(self):
        table = self.table(rates_toml(omit=("vat.rates.standard",)))
        with self.assertRaises(tb.RatesError) as ctx:
            vat.reference_figures(table)
        message = str(ctx.exception)
        self.assertIn("vat.rates.standard", message)
        self.assertIn("rates-AY2026-27.toml", message)
        self.assertEqual(ctx.exception.exit_code, 8)

    def test_every_missing_required_key_is_listed_at_once(self):
        table = self.table(rates_toml(omit=("vat.rates.standard", "deadlines.vat_return_quarterly")))
        with self.assertRaises(tb.RatesError) as ctx:
            vat.reference_figures(table)
        self.assertIn("vat.rates.standard", str(ctx.exception))
        self.assertIn("deadlines.vat_return_quarterly", str(ctx.exception))
        self.assertIn("2 figures", str(ctx.exception))

    def test_vds_deadline_required_only_with_vds_postings(self):
        table = self.table(rates_toml(omit=("vds.deposit.deadline",)))
        figures, warnings = vat.reference_figures(table, vds_present=False)
        self.assertFalse({f.key: f for f in figures}["vds_deposit_deadline"].available)
        self.assertTrue(any("NOT IN RATES FILE" in w and "vds.deposit.deadline" in w for w in warnings))
        with self.assertRaises(tb.RatesError):
            vat.reference_figures(table, vds_present=True)

    def test_missing_optional_key_is_a_visible_warning(self):
        table = self.table(rates_toml(omit=("vat.turnover_tax.rate",)))
        figures, warnings = vat.reference_figures(table)
        figure = {f.key: f for f in figures}["turnover_tax_rate"]
        self.assertEqual(figure.status, "not in rates file")
        self.assertTrue(any("vat.turnover_tax.rate" in w for w in warnings))

    def test_unverified_figure_is_flagged(self):
        figures, warnings = vat.reference_figures(self.table(rates_toml(verified=False)))
        self.assertTrue(all(f.status == "UNVERIFIED" for f in figures))
        self.assertTrue(all(f.usable for f in figures))  # unverified is still comparable
        self.assertEqual(len([w for w in warnings if w.startswith("UNVERIFIED")]), len(figures))
        self.assertTrue(all("NBR" in w for w in warnings))

    def test_required_placeholder_is_refused_like_a_missing_key(self):
        """An unlanded required figure is an absent one wearing a label (exit 8)."""
        table = self.table(rates_toml(verified=False, placeholder=True))
        with self.assertRaises(tb.RatesError) as ctx:
            vat.reference_figures(table)
        self.assertEqual(ctx.exception.exit_code, 8)
        self.assertIn("vat.rates.standard", str(ctx.exception))
        self.assertIn("deadlines.vat_return_quarterly", str(ctx.exception))
        self.assertIn("still a placeholder", str(ctx.exception))
        self.assertIn("--allow-placeholder-rates", ctx.exception.hint)

    def test_placeholder_figure_is_flagged_and_unusable(self):
        figures, warnings = vat.reference_figures(
            self.table(rates_toml(verified=False, placeholder=True)),
            allow_placeholders=True,
        )
        self.assertTrue(all(f.status == "PLACEHOLDER" for f in figures))
        self.assertTrue(all(f.grade == vat.GRADE_PLACEHOLDER for f in figures))
        self.assertFalse(any(f.usable for f in figures))
        self.assertTrue(all(w.startswith("PLACEHOLDER") for w in warnings), warnings)

    def test_optional_placeholder_withholds_its_value_but_does_not_refuse(self):
        """The MIXED case: required figures landed, one optional still a placeholder."""
        text = rates_toml(placeholder_keys=("vat.thresholds.registration",))
        figures, warnings = vat.reference_figures(self.table(text))
        by_key = {f.key: f for f in figures}
        held = by_key["registration_threshold"]
        self.assertTrue(held.placeholder)
        self.assertTrue(held.withheld)
        self.assertIsNone(held.raw_value)          # the unlanded number never surfaces
        self.assertIsNone(held.money)
        self.assertNotIn("1234567", held.display)
        self.assertEqual(held.status, "PLACEHOLDER")
        self.assertEqual(held.grade, vat.GRADE_PLACEHOLDER)
        self.assertFalse(held.usable)
        # Everything else in the same file is untouched and still fully usable.
        self.assertEqual(by_key["standard_rate"].display, "10%")
        self.assertTrue(by_key["standard_rate"].usable)
        self.assertEqual(by_key["standard_rate"].grade, vat.GRADE_FINAL)
        self.assertTrue(any("vat.thresholds.registration" in w for w in warnings))
        self.assertTrue(any("withheld" in w for w in warnings))

        # With the opt-in, the same node's value is shown — and still marked PLACEHOLDER.
        figures, _ = vat.reference_figures(self.table(text), allow_placeholders=True)
        shown = {f.key: f for f in figures}["registration_threshold"]
        self.assertFalse(shown.withheld)
        self.assertEqual(shown.money, M.from_str("1234567"))
        self.assertEqual(shown.status, "PLACEHOLDER")

    def test_toml_float_is_refused_not_used(self):
        figures, warnings = vat.reference_figures(self.table(rates_toml(standard="7.5")))
        figure = {f.key: f for f in figures}["standard_rate"]
        self.assertTrue(figure.problem)
        self.assertFalse(figure.usable)
        self.assertTrue(any("UNUSABLE RATE" in w and "float" in w for w in warnings))

    def test_percentage_over_100_is_a_fraction_mixup(self):
        figures, warnings = vat.reference_figures(self.table(rates_toml(standard='"150"')))
        figure = {f.key: f for f in figures}["standard_rate"]
        self.assertFalse(figure.usable)
        self.assertTrue(any("UNUSABLE RATE" in w for w in warnings))

    def test_blank_text_value_is_flagged_unless_placeholder(self):
        blank = rates_toml().replace(
            'value = "FIXTURE: within N days of the end of every three tax periods"',
            'value = ""',
        )
        figures, warnings = vat.reference_figures(self.table(blank))
        figure = {f.key: f for f in figures}["return_deadline"]
        self.assertEqual(figure.problem, "blank")
        self.assertTrue(any(w.startswith("BLANK") for w in warnings))

    def test_section_without_value_is_unreadable(self):
        broken = rates_toml(omit=("vat.turnover_tax.rate",)) + "[vat.turnover_tax.rate]\nnote = 'no value'\n"
        figures, warnings = vat.reference_figures(self.table(broken))
        figure = {f.key: f for f in figures}["turnover_tax_rate"]
        self.assertTrue(figure.problem)
        self.assertTrue(any(w.startswith("UNREADABLE") for w in warnings))


class TestDeclaredRates(VatFixture):
    def table(self, text: str | None = None) -> tb.RatesTable:
        return tb.RatesTable.from_toml_path(self.write_rates(text))

    def test_collects_every_declared_rate_with_scope(self):
        declared, warnings = vat.declared_rates(self.table())
        self.assertEqual(warnings, [])
        got = {(d.scope, d.rates_key): d.rate for d in declared}
        self.assertEqual(got[("vat", "vat.rates.standard")], D("10"))
        self.assertEqual(got[("vat", "vat.rates.zero_rated")], D("0"))
        self.assertEqual(got[("vat", "vat.rates.reduced.fixture_supply")], D("2.5"))
        self.assertEqual(got[("vds", "vds.services.fixture_service")], D("7.5"))
        self.assertTrue(all(d.usable for d in declared))

    def test_placeholders_are_unusable_and_only_new_keys_warn(self):
        declared, warnings = vat.declared_rates(
            self.table(rates_toml(verified=False, placeholder=True)),
            allow_placeholders=True,
        )
        self.assertFalse(any(d.usable for d in declared))
        keys_warned = {w.split(":")[1].split("(")[0].strip() for w in warnings}
        # standard / zero_rated are reported by reference_figures, not again here
        self.assertNotIn("vat.rates.standard", keys_warned)
        self.assertIn("vat.rates.reduced.fixture_supply", keys_warned)
        self.assertIn("vds.services.fixture_service", keys_warned)

    def test_placeholder_rate_is_withheld_by_default_and_never_matches_a_tag(self):
        """A rate nobody landed cannot silently bless a rate written in the journal."""
        text = rates_toml(placeholder_keys=("vat.rates.reduced.fixture_supply",))
        declared, warnings = vat.declared_rates(self.table(text))
        held = {d.rates_key: d for d in declared}["vat.rates.reduced.fixture_supply"]
        self.assertTrue(held.placeholder)
        self.assertTrue(held.withheld)
        self.assertIsNone(held.rate)               # 2.5% never surfaces
        self.assertEqual(held.rate_text, "—")
        self.assertFalse(held.usable)
        self.assertEqual(held.grade, vat.GRADE_PLACEHOLDER)
        self.assertTrue(any("withheld" in w for w in warnings))
        # The landed rates in the same file are unaffected.
        self.assertEqual(
            {d.rates_key for d in declared if d.usable},
            {"vat.rates.standard", "vat.rates.zero_rated", "vds.services.fixture_service"},
        )
        declared, _ = vat.declared_rates(self.table(text), allow_placeholders=True)
        shown = {d.rates_key: d for d in declared}["vat.rates.reduced.fixture_supply"]
        self.assertEqual(shown.rate, D("2.5"))
        self.assertFalse(shown.usable)             # opting in never makes it filing-ready

    def test_missing_sections_are_simply_absent(self):
        text = rates_toml(omit=("vat.rates.reduced.fixture_supply", "vds.services.fixture_service"))
        declared, _ = vat.declared_rates(self.table(text))
        self.assertEqual({d.rates_key for d in declared}, {"vat.rates.standard", "vat.rates.zero_rated"})

    def test_file_level_placeholder_detection(self):
        self.assertFalse(vat.rates_file_is_placeholder(self.table()))
        self.assertTrue(vat.rates_file_is_placeholder(self.table(rates_toml(file_placeholder=True))))
        status_only = tb.RatesTable({"meta": {"status": "placeholder"}})
        self.assertTrue(vat.rates_file_is_placeholder(status_only))
        self.assertFalse(vat.rates_file_is_placeholder(tb.RatesTable({})))


# ======================================================================================
# The computation — golden arithmetic
# ======================================================================================


class TestVatPosition(VatFixture):
    def test_golden_output_input_net_and_vds(self):
        """10,000 @ 10% out; 4,000 @ 10% in; 20,000 @ 10% VDS — all hand-checked."""
        position = self.position()
        self.assertEqual(position.output_taxable_value, M.from_str("10000"))
        self.assertEqual(position.output_tax, M.from_str("1000"))
        self.assertEqual(position.input_taxable_value, M.from_str("4000"))
        self.assertEqual(position.input_tax, M.from_str("400"))
        self.assertEqual(position.net, M.from_str("600"))
        self.assertEqual(position.net_payable, M.from_str("600"))
        self.assertEqual(position.carry_forward, M.zero())
        self.assertEqual(position.vds_supply_value, M.from_str("20000"))
        self.assertEqual(position.vds_withheld, M.from_str("2000"))
        # VDS is never netted against the VAT payable.
        self.assertEqual(position.net, position.output_tax - position.input_tax)

    def test_verified_and_reconciled_is_not_provisional(self):
        position = self.position()
        self.assertEqual(position.warnings, ())
        self.assertEqual(position.issues, ())
        self.assertFalse(position.provisional)
        self.assertEqual(position.filing_status, vat.STATUS_RECONCILED)
        self.assertEqual(position.assessment_year, "2026-27")
        self.assertIn("rates-AY2026-27.toml", position.rates_provenance)

    def test_excess_input_is_carried_forward_not_negative_payable(self):
        big_purchase = [
            "2026-07-12,P-002,Stock purchase,5100,50000.00,,Alam,BILL-8,VAT:IN:10,",
            "2026-07-12,P-002,Stock purchase,1310,5000.00,,Alam,BILL-8,VAT:IN:10,",
            "2026-07-12,P-002,Stock purchase,2100,,55000.00,Alam,BILL-8,NONE,",
        ]
        position = self.position(journals={"2026-07": SALE + big_purchase})
        self.assertEqual(position.output_tax, M.from_str("1000"))
        self.assertEqual(position.input_tax, M.from_str("5000"))
        self.assertEqual(position.net, M.from_str("-4000"))
        self.assertEqual(position.net_payable, M.zero())
        self.assertEqual(position.carry_forward, M.from_str("4000"))
        figures = position.figure_map()
        self.assertEqual(figures["net.carry_forward"].amount, M.from_str("4000"))
        self.assertEqual(figures["net.payable"].amount, M.zero())

    def test_return_figures_are_in_filing_order_with_bilingual_labels(self):
        keys = [f.key for f in self.position().return_figures()]
        self.assertEqual(
            keys,
            [
                "output.taxable_value",
                "output.tax",
                "input.taxable_value",
                "input.tax",
                "net.output_less_input",
                "net.payable",
                "net.carry_forward",
                "vds.supply_value",
                "vds.withheld",
            ],
        )
        for figure in self.position().return_figures():
            self.assertTrue(figure.label_bn and figure.label_en, figure.key)

    def test_buckets_split_by_rate_and_sum_to_totals(self):
        reduced_sale = [
            "2026-07-06,S-002,Reduced-rate sale,1200,1025.00,,Karim,INV-2,NONE,",
            "2026-07-06,S-002,Reduced-rate sale,4100,,1000.00,Karim,INV-2,VAT:OUT:2.5,",
            "2026-07-06,S-002,Reduced-rate sale,2310,,25.00,Karim,INV-2,VAT:OUT:2.5,",
        ]
        position = self.position(journals={"2026-07": SALE + reduced_sale})
        buckets = position.buckets[tb.TAG_VAT_OUT]
        self.assertEqual([b.rate for b in buckets], [D("2.5"), D("10")])
        self.assertEqual([b.tag_text for b in buckets], ["VAT:OUT:2.5", "VAT:OUT:10"])
        self.assertEqual(buckets[0].vat_amount, M.from_str("25"))
        self.assertEqual(position.output_tax, M.from_str("1025"))
        self.assertEqual(position.output_taxable_value, M.from_str("11000"))
        self.assertEqual(position.warnings, ())  # 2.5% is a declared fixture rate

    def test_derived_tax_when_no_control_line_uses_round_half_up(self):
        """1.25 @ 10% = 0.125 -> 0.13 (ROUND_HALF_UP; bankers would give 0.12)."""
        untagged_control = [
            "2026-07-07,S-003,Tiny sale,1200,1.38,,Cash,INV-3,NONE,",
            "2026-07-07,S-003,Tiny sale,4100,,1.25,Cash,INV-3,VAT:OUT:10,",
            "2026-07-07,S-003,Tiny sale,2310,,0.13,Cash,INV-3,NONE,",
        ]
        position = self.position(journals={"2026-07": untagged_control})
        bucket = position.buckets[tb.TAG_VAT_OUT][0]
        self.assertEqual(bucket.tax_source, "derived")
        self.assertEqual(bucket.posted_tax, M.zero())
        self.assertEqual(bucket.expected_tax, M(13))
        self.assertEqual(bucket.vat_amount, M(13))
        self.assertEqual(position.output_tax, M(13))
        self.assertTrue(any(n.startswith("DERIVED") for n in position.notes))
        # The control account moved without a tag: reported, never silently absorbed.
        self.assertTrue(any(n.startswith("CONTROL MOVEMENT") for n in position.notes))
        self.assertEqual(position.issues, ())

    def test_reconciliation_issue_when_posted_vat_differs_from_value_times_rate(self):
        wrong = [
            "2026-07-08,S-004,Mis-posted sale,1200,9900.00,,Karim,INV-4,NONE,",
            "2026-07-08,S-004,Mis-posted sale,4100,,9000.00,Karim,INV-4,VAT:OUT:10,",
            "2026-07-08,S-004,Mis-posted sale,2310,,900.00,Karim,INV-4,VAT:OUT:10,",
            "2026-07-09,S-005,Wrong VAT,1200,11100.00,,Karim,INV-5,NONE,",
            "2026-07-09,S-005,Wrong VAT,4100,,10000.00,Karim,INV-5,VAT:OUT:10,",
            "2026-07-09,S-005,Wrong VAT,2310,,1100.00,Karim,INV-5,VAT:OUT:10,",
        ]
        position = self.position(journals={"2026-07": wrong})
        self.assertEqual(len(position.issues), 1)
        issue = position.issues[0]
        self.assertEqual(issue.entry_id, "S-005")
        self.assertEqual(issue.expected_tax, M.from_str("1000"))
        self.assertEqual(issue.posted_tax, M.from_str("1100"))
        self.assertEqual(issue.difference, M.from_str("100"))
        self.assertIn("2026-07.csv", issue.location)
        self.assertIn("S-005", issue.message())
        self.assertTrue(any(w.startswith("RECONCILIATION") for w in position.warnings))
        self.assertTrue(position.provisional)
        # Posted VAT is what the return reports; the variance is shown, not hidden.
        self.assertEqual(position.output_tax, M.from_str("2000"))
        self.assertEqual(position.buckets[tb.TAG_VAT_OUT][0].variance, M.from_str("100"))

    def test_period_filter_and_control_account_roll_forward(self):
        payment = [
            "2026-08-15,PAY-1,VAT deposited to treasury,2310,1000.00,,NBR,CHALLAN-1,NONE,",
            "2026-08-15,PAY-1,VAT deposited to treasury,1100,,1000.00,NBR,CHALLAN-1,NONE,",
        ]
        august_sale = [r.replace("2026-07-05", "2026-08-20").replace("S-001", "S-010") for r in SALE]
        journals = {"2026-07": SALE + PURCHASE + VDS, "2026-08": payment + august_sale}

        july = self.position(journals=journals, period="2026-07")
        self.assertEqual(july.posting_count, 9)
        self.assertEqual(july.output_tax, M.from_str("1000"))
        out_control = next(c for c in july.controls if c.role == tb.ROLE_VAT_OUTPUT)
        self.assertEqual((out_control.opening, out_control.closing), (M.zero(), M.from_str("1000")))

        books = self.books
        ledger = tb.Ledger.load(books)
        rates = tb.RatesTable.from_toml_path(self.rates_path)
        since, until, label = vat.resolve_period(period="2026-08")
        august = vat.compute_vat_position(ledger, rates=rates, since=since, until=until, period_label=label)
        self.assertEqual(august.posting_count, 5)
        self.assertEqual(august.output_tax, M.from_str("1000"))
        self.assertEqual(august.input_tax, M.zero())
        control = next(c for c in august.controls if c.role == tb.ROLE_VAT_OUTPUT)
        self.assertEqual(control.opening, M.from_str("1000"))
        self.assertEqual(control.tagged, M.from_str("1000"))
        self.assertEqual(control.untagged, M.from_str("-1000"))
        self.assertEqual(control.closing, M.from_str("1000"))
        self.assertTrue(any("CONTROL MOVEMENT" in n and "2310" in n for n in august.notes))
        self.assertFalse(august.provisional)

    def test_whole_books_when_no_period(self):
        journals = {"2026-07": SALE, "2026-08": [r.replace("2026-07", "2026-08").replace("S-001", "S-9") for r in SALE]}
        position = self.position(journals=journals, period=None)
        self.assertEqual(position.output_tax, M.from_str("2000"))
        self.assertEqual(position.period_label, "every posting in the books")

    def test_missing_control_role_is_an_account_error_only_when_tagged(self):
        with self.assertRaises(tb.AccountError) as ctx:
            self.position(accounts=ACCOUNTS_TOML_NO_ROLES)
        self.assertIn("vat_output", str(ctx.exception))
        # No VAT tags at all: no role needed, no control accounts, nil figures.
        plain = [
            "2026-07-01,X-1,Owner cash,1100,500.00,,,,NONE,",
            "2026-07-01,X-1,Owner cash,2100,,500.00,,,NONE,",
        ]
        position = self.position(journals={"2026-07": plain}, accounts=ACCOUNTS_TOML_NO_ROLES)
        self.assertEqual(position.controls, ())
        self.assertEqual(position.output_tax, M.zero())
        self.assertTrue(any(n.startswith("NO VAT POSTINGS") for n in position.notes))

    def test_tds_postings_are_out_of_scope_but_counted(self):
        tds = [
            "2026-07-25,T-1,Rent with TDS,6200,10000.00,,Landlord,RENT-7,NONE,",
            "2026-07-25,T-1,Rent with TDS,2320,,500.00,Landlord,RENT-7,TDS:53A:5,",
            "2026-07-25,T-1,Rent with TDS,1100,,9500.00,Landlord,RENT-7,NONE,",
        ]
        position = self.position(journals={"2026-07": SALE + tds})
        self.assertEqual(position.tds_posting_count, 1)
        self.assertTrue(any(n.startswith("OUT OF SCOPE") for n in position.notes))
        self.assertEqual(position.output_tax, M.from_str("1000"))

    def test_tagged_rate_not_declared_in_rates_file_is_flagged(self):
        odd = [
            "2026-07-05,S-001,Sale at an undeclared rate,1200,10400.00,,Karim,INV-1,NONE,",
            "2026-07-05,S-001,Sale at an undeclared rate,4100,,10000.00,Karim,INV-1,VAT:OUT:4,",
            "2026-07-05,S-001,Sale at an undeclared rate,2310,,400.00,Karim,INV-1,VAT:OUT:4,",
        ]
        position = self.position(journals={"2026-07": odd})
        self.assertEqual(position.output_tax, M.from_str("400"))
        flagged = [w for w in position.warnings if w.startswith("RATE NOT DECLARED")]
        self.assertEqual(len(flagged), 1)
        self.assertIn("4%", flagged[0])
        self.assertIn("10%", flagged[0])
        self.assertTrue(position.provisional)

    def test_vds_rate_checked_against_vds_services_and_vat_rates(self):
        vds_75 = [
            "2026-07-21,C-2,Service,6200,1000.00,,S,B-1,VDS:7.5,",
            "2026-07-21,C-2,Service,2330,,75.00,S,B-1,VDS:7.5,",
            "2026-07-21,C-2,Service,2100,,925.00,S,B-1,NONE,",
        ]
        position = self.position(journals={"2026-07": vds_75 + VDS})
        self.assertEqual(position.warnings, ())
        self.assertEqual(position.vds_withheld, M.from_str("2075"))

    def test_placeholder_rates_file_is_refused_until_opted_in(self):
        """Same refusal, same exit code and same remedy as tax.py on the same file."""
        text = rates_toml(verified=False, placeholder=True, file_placeholder=True)
        with self.assertRaises(tb.RatesError) as ctx:
            self.position(rates=text)
        self.assertEqual(ctx.exception.exit_code, 8)
        self.assertIn("awaiting verified data", str(ctx.exception))
        self.assertIn("--allow-placeholder-rates", ctx.exception.hint)

    def test_placeholder_rates_file_stamps_output_placeholder_and_skips_rate_check(self):
        position = self.position(
            rates=rates_toml(verified=False, placeholder=True, file_placeholder=True),
            allow_placeholders=True,
        )
        self.assertTrue(position.rates_file_placeholder)
        self.assertTrue(position.provisional)
        self.assertTrue(position.placeholder_data_used)
        self.assertEqual(position.data_grade, vat.GRADE_PLACEHOLDER)
        self.assertEqual(position.filing_status, vat.STATUS_PLACEHOLDER)
        self.assertIn("NOT FOR FILING", vat.STATUS_PLACEHOLDER)
        self.assertTrue(position.warnings[0].startswith("PLACEHOLDER RATES FILE"))
        self.assertTrue(any(w.startswith("RATE CHECK SKIPPED") for w in position.warnings))
        self.assertFalse(any(w.startswith("RATE NOT DECLARED") for w in position.warnings))
        # The arithmetic itself is untouched by the state of the rates file.
        self.assertEqual(position.net, M.from_str("600"))
        self.assertEqual(position.rates_caveats, position.warnings)

    def test_mixed_file_computes_from_landed_nodes_and_withholds_the_rest(self):
        """Per figure, not per file: one unlanded optional node does not stop the return."""
        position = self.position(
            rates=rates_toml(
                placeholder_keys=("vat.rates.reduced.fixture_supply",),
                unverified_keys=("vat.turnover_tax.rate",),
            )
        )
        # The return figures are journal arithmetic and are exactly as before.
        self.assertEqual(position.net, M.from_str("600"))
        self.assertEqual(position.output_tax, M.from_str("1000"))
        # An unlanded node that was withheld never touched the answer, so the answer is
        # PROVISIONAL (something is unconfirmed), not PLACEHOLDER (something is invented).
        self.assertFalse(position.placeholder_data_used)
        self.assertEqual(position.data_grade, vat.GRADE_UNVERIFIED)
        self.assertEqual(position.filing_status, vat.STATUS_PROVISIONAL)
        self.assertEqual(
            position.placeholder_figures_withheld, ("vat.rates.reduced.fixture_supply",)
        )
        self.assertEqual(position.placeholder_figures_used, ())
        self.assertTrue(
            any(w.startswith("UNVERIFIED") and "vat.turnover_tax.rate" in w
                for w in position.warnings)
        )
        # 10% is still declared and landed, so the journal's own rate still checks out.
        self.assertFalse(any(w.startswith("RATE NOT DECLARED") for w in position.warnings))
        self.assertFalse(any(w.startswith("RATE CHECK SKIPPED") for w in position.warnings))

    def test_unverified_rates_file_is_provisional_but_still_checks_rates(self):
        position = self.position(rates=rates_toml(verified=False))
        self.assertTrue(position.provisional)
        self.assertTrue(any(w.startswith("UNVERIFIED") and "vat.rates.standard" in w for w in position.warnings))
        self.assertFalse(any(w.startswith("RATE CHECK SKIPPED") for w in position.warnings))

    def test_return_form_map_from_rates_file(self):
        position = self.position(rates=rates_toml(extra=RETURN_FORM_EXTRA))
        self.assertEqual(len(position.return_form), 2)
        first, second = position.return_form
        self.assertEqual((first.line, first.figure_key, first.amount), ("F-1", "output.tax", M.from_str("1000")))
        self.assertIsNone(second.amount)
        self.assertIn("no.such.figure", second.problem)
        self.assertFalse(any(n.startswith("FORM MAP") for n in position.notes))

    def test_no_form_map_is_said_out_loud(self):
        position = self.position()
        self.assertEqual(position.return_form, ())
        self.assertTrue(any(n.startswith("FORM MAP") for n in position.notes))

    def test_missing_assessment_year_in_config_is_config_error(self):
        with self.assertRaises(tb.ConfigError):
            self.position(config=config_toml(assessment_year=None))

    def test_extra_warnings_flow_through(self):
        books = self.write_books()
        rates = tb.RatesTable.from_toml_path(self.write_rates())
        position = vat.compute_vat_position(
            tb.Ledger.load(books), rates=rates, extra_warnings=["MISMATCH: fixture"]
        )
        self.assertIn("MISMATCH: fixture", position.warnings)
        self.assertTrue(position.provisional)


# ======================================================================================
# Rendering — Markdown, CSV, JSON from one computation
# ======================================================================================


class TestRendering(VatFixture):
    def test_markdown_states_year_provenance_and_ends_with_disclaimer(self):
        text = vat.render_markdown(self.position())
        self.assertIn("করবর্ষ / assessment year:** 2026-27", text)
        self.assertIn("Rates source: rates-AY2026-27.toml", text)
        self.assertIn("মূসক / VAT", text)
        self.assertIn("উৎসে মূসক কর্তন", text)
        self.assertIn("৳1,000.00", text)
        self.assertIn("৳20,000.00", text)
        self.assertIn(tb.DISCLAIMER_EN, text)
        self.assertIn(tb.DISCLAIMER_BN, text)  # bn-en locale
        tail = text.rstrip().splitlines()[-4:]
        self.assertTrue(any(tb.DISCLAIMER_BN in line for line in tail))
        self.assertTrue(text.rstrip().endswith(f"_{tb.ATTRIBUTION}_"))
        self.assertIn("TICON SYSTEM LTD", text)
        self.assertNotIn("PROVISIONAL", text.split("## 1.")[0])

    def test_markdown_english_locale_has_only_english_disclaimer(self):
        text = vat.render_markdown(self.position(config=config_toml(language="en")))
        self.assertIn(tb.DISCLAIMER_EN, text)
        self.assertNotIn(tb.DISCLAIMER_BN, text)

    def test_markdown_uses_lakh_crore_grouping(self):
        lakh_sale = [
            "2026-07-05,S-L,Big sale,1200,1100000.00,,Karim,INV-L,NONE,",
            "2026-07-05,S-L,Big sale,4100,,1000000.00,Karim,INV-L,VAT:OUT:10,",
            "2026-07-05,S-L,Big sale,2310,,100000.00,Karim,INV-L,VAT:OUT:10,",
        ]
        position = self.position(journals={"2026-07": lakh_sale})
        text = vat.render_markdown(position)
        self.assertIn("৳10,00,000.00", text)
        self.assertIn("৳1,00,000.00", text)
        csv_text = vat.render_csv(position)
        self.assertIn(",1000000.00,", csv_text)
        self.assertIn(",100000.00,", csv_text)

    def test_markdown_shows_unverified_and_placeholder_visibly(self):
        text = vat.render_markdown(self.position(rates=rates_toml(verified=False)))
        self.assertIn("UNVERIFIED", text)
        self.assertIn("PROVISIONAL / অস্থায়ী", text)
        self.assertIn("NOT FOR FILING", text)
        self.assertNotIn("PLACEHOLDER DATA", text)
        text = vat.render_markdown(self.position(
            rates=rates_toml(verified=False, placeholder=True, file_placeholder=True),
            allow_placeholders=True,
        ))
        self.assertIn("PLACEHOLDER", text)
        self.assertIn("PLACEHOLDER DATA / অস্থায়ী উপাত্ত — NOT FOR FILING", text)
        self.assertIn("placeholder schema", text)
        self.assertIn(vat.STATUS_PLACEHOLDER, text)

    def test_markdown_names_a_withheld_placeholder_without_printing_its_value(self):
        position = self.position(
            rates=rates_toml(placeholder_keys=("vat.rates.reduced.fixture_supply",))
        )
        text = vat.render_markdown(position)
        self.assertIn("PROVISIONAL / অস্থায়ী — NOT FOR FILING", text)
        self.assertIn("vat.rates.reduced.fixture_supply", text)
        self.assertIn("PLACEHOLDER", text)          # the node's own status column
        self.assertNotIn("2.5%", text)              # but never its unlanded percentage

    def test_markdown_lists_declared_rates_and_reconciliation(self):
        text = vat.render_markdown(self.position())
        self.assertIn("Rates declared in the rates file", text)
        self.assertIn("`vat.rates.reduced.fixture_supply`", text)
        self.assertIn("Every tagged entry ties", text)

    def test_csv_is_long_format_ungrouped_and_carries_disclaimer(self):
        text = vat.render_csv(self.position())
        lines = text.splitlines()
        self.assertEqual(lines[0], ",".join(vat.CSV_COLUMNS))
        rows = [line.split(",") for line in lines[1:]]
        figure_rows = {r[1]: r for r in rows if r[0] == "figure"}
        self.assertEqual(figure_rows["output.tax"][5], "1000.00")
        self.assertEqual(figure_rows["net.payable"][5], "600.00")
        self.assertEqual(figure_rows["vds.withheld"][5], "2000.00")
        amount_cells = [r[5] for r in rows if len(r) > 5]
        self.assertFalse(any("৳" in cell or "," in cell for cell in amount_cells))
        self.assertIn("meta,rates_provenance,,,,,Rates source: rates-AY2026-27.toml", text)
        self.assertIn("meta,assessment_year,করবর্ষ,assessment year,,,2026-27", text)
        self.assertIn("meta,filing_status", text)
        self.assertIn("declared_rate,vat.rates.standard", text)
        self.assertIn(tb.DISCLAIMER_EN, text)
        self.assertTrue(lines[-1].startswith("disclaimer,"))

    def test_csv_flags_unverified(self):
        text = vat.render_csv(self.position(rates=rates_toml(verified=False)))
        self.assertIn("status=UNVERIFIED", text)
        self.assertIn("warning,1,,,,,UNVERIFIED", text)
        self.assertIn("meta,provisional,,,,,true", text)

    def test_json_payload_is_explicit_and_parses(self):
        position = self.position()
        data = json.loads(vat.render_json(position))
        self.assertTrue(data["ok"])
        self.assertEqual(data["tool"], "vat.py")
        self.assertEqual(data["assessment_year"], "2026-27")
        self.assertEqual(data["rates"]["file"], "rates-AY2026-27.toml")
        self.assertIn("Rates source", data["rates"]["provenance"])
        self.assertEqual(data["net"], {"output_less_input": "600.00", "payable": "600.00", "carry_forward": "0.00"})
        self.assertEqual(data["output"]["tax"], "1000.00")
        self.assertEqual(data["vds"]["withheld"], "2000.00")
        self.assertEqual(data["output"]["by_rate"][0]["rate_percent"], "10")
        self.assertEqual(data["filing_status"], vat.STATUS_RECONCILED)
        self.assertFalse(data["provisional"])
        self.assertEqual(data["warnings"], [])
        self.assertEqual(data["disclaimer_en"], tb.DISCLAIMER_EN)
        self.assertEqual(data["disclaimer_bn"], tb.DISCLAIMER_BN)
        self.assertEqual({d["rates_key"] for d in data["declared_rates"]} >= {"vat.rates.standard"}, True)
        figures = {f["key"]: f["amount"] for f in data["figures"]}
        self.assertEqual(figures["input.tax"], "400.00")
        self.assertEqual(data["attribution"], tb.ATTRIBUTION)

    def test_json_flags_unverified_and_placeholder(self):
        data = json.loads(vat.render_json(self.position(rates=rates_toml(verified=False))))
        self.assertTrue(data["provisional"])
        self.assertEqual(data["data_grade"], vat.GRADE_UNVERIFIED)
        self.assertFalse(data["placeholder_data_used"])
        self.assertTrue(all(f["status"] == "UNVERIFIED" for f in data["reference_figures"]))
        self.assertTrue(any(w.startswith("UNVERIFIED") for w in data["warnings"]))
        data = json.loads(vat.render_json(self.position(
            rates=rates_toml(verified=False, placeholder=True, file_placeholder=True),
            allow_placeholders=True,
        )))
        self.assertTrue(data["rates"]["file_placeholder"])
        self.assertTrue(data["rates"]["allow_placeholder_rates"])
        self.assertTrue(data["placeholder_data_used"])
        self.assertEqual(data["data_grade"], vat.GRADE_PLACEHOLDER)
        self.assertEqual(data["filing_status"], vat.STATUS_PLACEHOLDER)
        self.assertTrue(all(f["status"] == "PLACEHOLDER" for f in data["reference_figures"]))
        self.assertGreater(data["rates"]["unverified_keys_in_file"], 0)
        self.assertGreater(data["rates"]["placeholder_keys_in_file"], 0)

    def test_json_separates_withheld_placeholders_from_used_ones(self):
        data = json.loads(vat.render_json(self.position(
            rates=rates_toml(placeholder_keys=("vat.rates.reduced.fixture_supply",))
        )))
        rates_block = data["rates"]
        self.assertEqual(
            rates_block["placeholder_figures_withheld"],
            ["vat.rates.reduced.fixture_supply"],
        )
        self.assertEqual(rates_block["placeholder_figures_used"], [])
        self.assertFalse(data["placeholder_data_used"])
        self.assertEqual(data["data_grade"], vat.GRADE_UNVERIFIED)
        held = {d["rates_key"]: d for d in data["declared_rates"]}[
            "vat.rates.reduced.fixture_supply"
        ]
        self.assertTrue(held["withheld"])
        self.assertIsNone(held["rate_percent"])
        self.assertEqual(held["grade"], vat.GRADE_PLACEHOLDER)


# ======================================================================================
# CLI
# ======================================================================================


class TestCli(VatFixture):
    def test_help_lists_standard_flags(self):
        code, out, _ = self.cli("--help")
        self.assertEqual(code, 0)
        for flag in ("--books", "--json", "--period", "--rates", "--strict", "--format",
                     "--allow-placeholder-rates"):
            self.assertIn(flag, out)
        self.assertIn("vat.rates.standard", out)
        self.assertIn("TICON SYSTEM LTD", out)

    def test_markdown_by_default(self):
        books = self.write_books()
        rates = self.write_rates()
        code, out, err = self.cli("--books", str(books), "--rates", str(rates), "--period", "2026-07")
        self.assertEqual(code, 0, err)
        self.assertTrue(out.startswith("# মূসক / VAT position"))
        self.assertIn("Rates source: rates-AY2026-27.toml", out)
        self.assertIn(tb.DISCLAIMER_EN, out)

    def test_json_flag(self):
        books = self.write_books()
        rates = self.write_rates()
        code, out, err = self.cli("--books", str(books), "--rates", str(rates), "--json")
        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(data["net"]["payable"], "600.00")

    def test_format_csv_and_out_files(self):
        books = self.write_books()
        rates = self.write_rates()
        target = self.root / "vat.md"
        csv_target = self.root / "vat.csv"
        code, out, err = self.cli(
            "--books", str(books), "--rates", str(rates), "--period", "2026-07",
            "--out", str(target), "--csv-out", str(csv_target),
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "")
        self.assertIn("# মূসক / VAT position", target.read_text(encoding="utf-8"))
        self.assertTrue(csv_target.read_text(encoding="utf-8").startswith("section,key,"))
        code, out, _ = self.cli("--books", str(books), "--rates", str(rates), "--format", "csv")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("section,key,"))

    def test_json_conflicts_with_other_format(self):
        code, _, err = self.cli("--json", "--format", "csv")
        self.assertEqual(code, 2)
        self.assertIn("--json", err)

    def test_unbalanced_books_exit_5(self):
        broken = SALE[:2]  # tax line missing: 11,000 debit vs 10,000 credit
        books = self.write_books({"2026-07": broken})
        rates = self.write_rates()
        code, out, err = self.cli("--books", str(books), "--rates", str(rates))
        self.assertEqual(code, 5)
        self.assertEqual(out, "")
        self.assertIn("S-001", err)
        self.assertIn("do not balance", err)

    def test_unknown_account_exit_3(self):
        bad = SALE + [
            "2026-07-30,Z-1,Typo account,9999,1.00,,,,NONE,",
            "2026-07-30,Z-1,Typo account,1100,,1.00,,,NONE,",
        ]
        books = self.write_books({"2026-07": bad})
        rates = self.write_rates()
        code, _, err = self.cli("--books", str(books), "--rates", str(rates))
        self.assertEqual(code, 3)
        self.assertIn("9999", err)

    def test_missing_required_rate_exits_8_and_names_the_key(self):
        books = self.write_books()
        rates = self.write_rates(rates_toml(omit=("vat.rates.standard",)))
        code, out, err = self.cli("--books", str(books), "--rates", str(rates))
        self.assertEqual(code, 8)
        self.assertEqual(out, "")
        self.assertIn("vat.rates.standard", err)
        self.assertIn("will not assume", err)
        code, _, err = self.cli("--books", str(books), "--rates", str(rates), "--json")
        self.assertEqual(code, 8)
        payload = json.loads(err)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["exit_code"], 8)
        self.assertIn("vat.rates.standard", payload["message"])

    def test_missing_rates_file_exits_8(self):
        books = self.write_books()
        code, _, err = self.cli("--books", str(books), "--rates", str(self.root / "nope.toml"))
        self.assertEqual(code, 8)
        self.assertIn("nope.toml", err)

    def test_missing_books_dir_exits_non_zero(self):
        code, _, err = self.cli("--books", str(self.root / "ghost"))
        self.assertNotEqual(code, 0)
        self.assertIn("ghost", err)

    def test_bad_period_exits_2(self):
        books = self.write_books()
        rates = self.write_rates()
        code, _, err = self.cli("--books", str(books), "--rates", str(rates), "--period", "2026-7")
        self.assertEqual(code, 2)
        self.assertIn("YYYY-MM", err)

    def test_unverified_output_still_prints_but_carries_warning(self):
        books = self.write_books()
        rates = self.write_rates(rates_toml(verified=False))
        code, out, _ = self.cli("--books", str(books), "--rates", str(rates))
        self.assertEqual(code, 0)
        self.assertIn("UNVERIFIED", out)
        self.assertIn("PROVISIONAL", out)

    def test_strict_fails_on_unverified_and_passes_when_clean(self):
        books = self.write_books()
        unverified = self.write_rates(rates_toml(verified=False), name="rates-unverified.toml")
        code, out, err = self.cli("--books", str(books), "--rates", str(unverified), "--strict", "--allow-ay-mismatch")
        self.assertEqual(code, 7)
        self.assertIn("UNVERIFIED", err)
        self.assertIn("not ready to file", err)
        verified = self.write_rates()
        code, out, err = self.cli("--books", str(books), "--rates", str(verified), "--strict")
        self.assertEqual(code, 0, err)
        self.assertIn(vat.STATUS_RECONCILED, out)

    def test_strict_fails_on_reconciliation_difference(self):
        wrong = [
            "2026-07-09,S-005,Wrong VAT,1200,11100.00,,Karim,INV-5,NONE,",
            "2026-07-09,S-005,Wrong VAT,4100,,10000.00,Karim,INV-5,VAT:OUT:10,",
            "2026-07-09,S-005,Wrong VAT,2310,,1100.00,Karim,INV-5,VAT:OUT:10,",
        ]
        books = self.write_books({"2026-07": wrong})
        rates = self.write_rates()
        code, _, err = self.cli("--books", str(books), "--rates", str(rates), "--strict")
        self.assertEqual(code, 7)
        self.assertIn("S-005", err)

    def test_assessment_year_mismatch_exits_8(self):
        books = self.write_books()
        rates = self.write_rates(rates_toml(assessment_year="2031-32"), name="rates-AY2031-32.toml")
        code, _, err = self.cli("--books", str(books), "--rates", str(rates))
        self.assertEqual(code, 8)
        self.assertIn("2031-32", err)

    def test_all_caveats_lists_the_whole_file(self):
        books = self.write_books()
        rates = self.write_rates(rates_toml(verified=False))
        _, out_default, _ = self.cli("--books", str(books), "--rates", str(rates), "--json")
        _, out_all, _ = self.cli("--books", str(books), "--rates", str(rates), "--json", "--all-caveats")
        self.assertGreater(len(json.loads(out_all)["warnings"]), len(json.loads(out_default)["warnings"]))

    def test_rates_file_found_through_config(self):
        books = self.write_books(config=config_toml(rates_file="fixture-rates.toml"))
        (books / "fixture-rates.toml").write_text(rates_toml(), encoding="utf-8")
        code, out, err = self.cli("--books", str(books), "--json")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["rates"]["file"], "fixture-rates.toml")

    def test_placeholder_file_exits_8_then_computes_under_the_opt_in(self):
        books = self.write_books()
        rates = self.write_rates(
            rates_toml(verified=False, placeholder=True, file_placeholder=True)
        )
        code, out, err = self.cli("--books", str(books), "--rates", str(rates))
        self.assertEqual(code, 8)
        self.assertEqual(out, "")
        self.assertIn("--allow-placeholder-rates", err)

        code, out, err = self.cli("--books", str(books), "--rates", str(rates),
                                  "--allow-placeholder-rates")
        self.assertEqual(code, 0, err)
        self.assertIn(vat.STATUS_PLACEHOLDER, out)
        self.assertIn("PLACEHOLDER DATA", out)
        self.assertIn(tb.DISCLAIMER_EN, out)

        # --strict must still refuse it: opting in never makes a figure fileable.
        code, _, err = self.cli("--books", str(books), "--rates", str(rates),
                                "--allow-placeholder-rates", "--strict")
        self.assertEqual(code, 7)
        self.assertIn("not ready to file", err)

    def test_required_placeholder_key_exits_8_and_names_it(self):
        books = self.write_books()
        rates = self.write_rates(rates_toml(placeholder_keys=("vat.rates.standard",)))
        code, out, err = self.cli("--books", str(books), "--rates", str(rates))
        self.assertEqual(code, 8)
        self.assertEqual(out, "")
        self.assertIn("vat.rates.standard", err)
        self.assertIn("still a placeholder", err)

    def test_optional_placeholder_key_runs_and_marks_json(self):
        books = self.write_books()
        rates = self.write_rates(
            rates_toml(placeholder_keys=("vat.thresholds.registration",))
        )
        code, out, err = self.cli("--books", str(books), "--rates", str(rates), "--json")
        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(data["net"]["payable"], "600.00")
        self.assertEqual(
            data["rates"]["placeholder_figures_withheld"], ["vat.thresholds.registration"]
        )
        self.assertNotIn("1234567", out)


# ======================================================================================
# Posture symmetry — tax.py and vat.py must answer "has this landed?" the same way
# ======================================================================================


class TestEnginePostureSymmetry(unittest.TestCase):
    """The two engines share a vocabulary and a gate.  Lock them together.

    The adversarial review found an ASYMMETRIC REFUSAL: with a placeholder rates file
    ``tax.py`` exited 8 while ``vat.py`` computed and exited 0 — two engines, two opposite
    default postures towards unlanded data.  These tests are what stops that recurring.
    """

    def test_both_modules_share_the_same_words(self):
        for name in ("ALLOW_PLACEHOLDERS_FLAG", "GRADE_FINAL", "GRADE_UNVERIFIED",
                     "GRADE_PLACEHOLDER", "STATUS_PLACEHOLDER", "STATUS_PROVISIONAL",
                     "PLACEHOLDER_STATUS_TEXT"):
            with self.subTest(constant=name):
                self.assertEqual(getattr(tax, name), getattr(vat, name), name)
        self.assertIn("NOT FOR FILING", vat.STATUS_PLACEHOLDER)
        self.assertIn("not for filing", vat.STATUS_PROVISIONAL)

    def test_both_read_the_rates_file_through_the_same_reader(self):
        """One reader, one implementation of "has this figure landed?"."""
        self.assertIs(vat.rt, tax.rt)
        self.assertIs(vat.as_rate_set(tb.RatesTable({})).__class__, rt.RateSet)
        source = (ENGINE_DIR / "vat.py").read_text(encoding="utf-8")
        # vat.py must not grow a second placeholder rule of its own.
        self.assertNotIn('get("placeholder")', source)
        self.assertNotIn('["placeholder"]', source)

    def test_file_level_gate_agrees_across_every_meta_shape(self):
        shapes = {
            "empty": {},
            "no meta key": {"meta": {}},
            "flag true": {"meta": {"placeholder": True}},
            "flag false": {"meta": {"placeholder": False}},
            "status only": {"meta": {"status": "placeholder"}},
            "status landed": {"meta": {"status": "landed"}},
            "status landed, flag true": {"meta": {"status": "landed", "placeholder": True}},
            "both": {"meta": {"status": "placeholder", "placeholder": True}},
            "status mixed case": {"meta": {"status": "  PlaceHolder "}},
        }
        for label, raw in shapes.items():
            with self.subTest(shape=label):
                table = tb.RatesTable(raw)
                from_vat = vat.rates_file_is_placeholder(table)
                from_tax = tax.rates_file_is_placeholder(
                    rt.RateSet(table, allow_placeholders=True)
                )
                self.assertEqual(from_vat, from_tax, label)

    def test_refusal_and_opt_in_agree_across_every_meta_shape(self):
        """Whatever the file says, both engines refuse or allow it identically."""
        for raw, expect_refusal in (
            ({"meta": {}}, False),
            ({"meta": {"placeholder": True}}, True),
            ({"meta": {"status": "placeholder"}}, True),
            ({"meta": {"status": "landed", "placeholder": False}}, False),
        ):
            for allow in (False, True):
                with self.subTest(meta=raw["meta"], allow=allow):
                    table = tb.RatesTable(raw)
                    should_raise = expect_refusal and not allow

                    # Same signature, same call, two engines — the point of the test.
                    def call_vat():
                        vat.require_landed_rates(table, allow_placeholders=allow)

                    def call_tax():
                        tax.require_landed_rates(
                            rt.RateSet(table), allow_placeholders=allow
                        )

                    def call_vat_via_posture():
                        vat.require_landed_rates(
                            rt.RateSet(table, allow_placeholders=allow)
                        )

                    def call_tax_via_posture():
                        tax.require_landed_rates(
                            rt.RateSet(table, allow_placeholders=allow)
                        )

                    calls = (
                        ("vat", call_vat),
                        ("tax", call_tax),
                        ("vat via RateSet posture", call_vat_via_posture),
                        ("tax via RateSet posture", call_tax_via_posture),
                    )
                    for name, call in calls:
                        if should_raise:
                            with self.assertRaises(tb.RatesError, msg=name) as ctx:
                                call()
                            self.assertEqual(ctx.exception.exit_code, 8, name)
                            self.assertIn(
                                vat.ALLOW_PLACEHOLDERS_FLAG, ctx.exception.hint, name
                            )
                        else:
                            call()  # must not raise

    def test_both_clis_offer_the_same_two_flags(self):
        vat_flags = {
            option
            for action in vat.build_parser()._actions
            for option in action.option_strings
        }
        tax_flags = {
            option
            for action in tax.build_parser()._actions
            for option in action.option_strings
        }
        for flag in ("--allow-placeholder-rates", "--strict", "--json", "--rates"):
            with self.subTest(flag=flag):
                self.assertIn(flag, vat_flags)
                self.assertIn(flag, tax_flags)

    def test_the_same_placeholder_file_is_refused_by_both_command_lines(self):
        """The end-to-end symmetry: one file, two tools, one exit code."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        books = root / "books"
        (books / "journal").mkdir(parents=True)
        (books / "config.toml").write_text(config_toml(), encoding="utf-8")
        (books / "accounts.toml").write_text(ACCOUNTS_TOML, encoding="utf-8")
        (books / "journal" / "2026-07.csv").write_text(
            HEADER + "\n" + "\n".join(SALE) + "\n", encoding="utf-8"
        )
        rates_path = root / "rates-AY2026-27.toml"
        rates_path.write_text(
            rates_toml(verified=False, placeholder=True, file_placeholder=True)
            + PLACEHOLDER_INCOME_TAX_EXTRA,
            encoding="utf-8",
        )

        def run(script: str, *args: str) -> subprocess.CompletedProcess:
            env = dict(os.environ, PYTHONIOENCODING="utf-8")
            return subprocess.run(
                [sys.executable, str(ENGINE_DIR / script), *args],
                capture_output=True, text=True, encoding="utf-8", env=env,
            )

        vat_args = ("--books", str(books), "--rates", str(rates_path))
        tax_args = ("--books", str(books), "--rates", str(rates_path), "--income", "500000")

        refused = (run("vat.py", *vat_args), run("tax.py", *tax_args))
        for result in refused:
            self.assertEqual(result.returncode, 8, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertIn("--allow-placeholder-rates", result.stderr)

        allowed = (
            run("vat.py", *vat_args, "--allow-placeholder-rates"),
            run("tax.py", *tax_args, "--allow-placeholder-rates"),
        )
        for result in allowed:
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(vat.STATUS_PLACEHOLDER, result.stdout)
            self.assertIn("NOT FOR FILING", result.stdout)

        strict = (
            run("vat.py", *vat_args, "--allow-placeholder-rates", "--strict"),
            run("tax.py", *tax_args, "--allow-placeholder-rates", "--strict"),
        )
        for result in strict:
            self.assertEqual(result.returncode, 7, result.stderr)
            self.assertIn("not ready to file", result.stderr)


#: The income-tax half of a rates file, so one fixture can drive both engines.  Every
#: figure is a placeholder, which is the whole point: neither tool may compute from it.
PLACEHOLDER_INCOME_TAX_EXTRA = """
[income_tax.individual]
default_category = "general"
default_location = "metro"

[income_tax.individual.thresholds.general]
label_en = "General taxpayer (FIXTURE)"
label_bn = "সাধারণ করদাতা"
value = 100000
unit = "BDT"
source = "https://example.invalid/fixture"
verified = false
placeholder = true

[[income_tax.individual.slabs]]
order = 1
label_en = "Tax-free threshold (FIXTURE)"
width_source = "category_threshold"
  [income_tax.individual.slabs.rate]
  value = 0
  unit = "percent"
  source = "https://example.invalid/fixture"
  verified = false
  placeholder = true

[[income_tax.individual.slabs]]
order = 2
label_en = "Balance of income (FIXTURE)"
  [income_tax.individual.slabs.rate]
  value = 10
  unit = "percent"
  source = "https://example.invalid/fixture"
  verified = false
  placeholder = true

[income_tax.individual.rebate]
formula = "min_of_three_caps"
  [income_tax.individual.rebate.rate]
  value = 10
  unit = "percent"
  source = "https://example.invalid/fixture"
  verified = false
  placeholder = true
  [income_tax.individual.rebate.income_cap_percent]
  value = 25
  unit = "percent"
  source = "https://example.invalid/fixture"
  verified = false
  placeholder = true
  [income_tax.individual.rebate.absolute_cap]
  value = 500000
  unit = "BDT"
  source = "https://example.invalid/fixture"
  verified = false
  placeholder = true

[income_tax.individual.minimum_tax.applies_when]
value = "always"
unit = "policy"
allowed = ["always", "taxable_income_above_threshold", "never"]
source = "https://example.invalid/fixture"
verified = false
placeholder = true

[income_tax.individual.minimum_tax.by_location.metro]
label_en = "Metropolitan (FIXTURE)"
value = 4000
unit = "BDT"
source = "https://example.invalid/fixture"
verified = false
placeholder = true

[income_tax.individual.surcharge]
  [income_tax.individual.surcharge.base]
  value = "tax_after_rebate"
  unit = "policy"
  allowed = ["tax_after_rebate", "tax_after_minimum"]
  source = "https://example.invalid/fixture"
  verified = false
  placeholder = true

[[income_tax.individual.surcharge.bands]]
order = 1
label_en = "No surcharge (FIXTURE)"
  [income_tax.individual.surcharge.bands.rate]
  value = 0
  unit = "percent"
  source = "https://example.invalid/fixture"
  verified = false
  placeholder = true
"""


class DeadlinesSurfacedTests(VatFixture):
    """Which filing deadline vat.py puts in front of the return preparer.

    Two defects are pinned here.

    **The quarterly return.**  From 1 July 2026 the মূসক return is QUARTERLY —
    VAT Act s.64(1), within 15 days of the end of every three tax periods.  Monthly
    filing survives only as a voluntary election under s.64(2).  vat.py used to read
    ``deadlines.vat_return_monthly`` and nothing else, so a registered person filing
    the default return was told they had a full month when the statute gives 15 days.
    The monthly node's own text already said "Monthly filing is NO LONGER THE DEFAULT".

    **The s.137A legacy-settlement window.**  New VAT Act s.137A (১৩৭ক) opens an
    interest-waiver scheme for legacy demands for six months from 1 July 2026, closing
    31 December 2026.  It lived only as prose in ``compliance-calendar.md`` and inside
    another node's ``note``, so no engine could surface it and ``rates.py --all`` never
    listed it — in the very quarter the calendar calls "the last quarter to use it".
    """

    def test_quarterly_deadline_is_the_required_return_deadline(self):
        keys = {spec.rates_key for spec in vat.REFERENCE_SPECS}
        self.assertIn("deadlines.vat_return_quarterly", keys)
        required = {s.rates_key for s in vat.REFERENCE_SPECS if s.required == vat.REQUIRED_ALWAYS}
        self.assertIn(
            "deadlines.vat_return_quarterly",
            required,
            "the statutory default return deadline must be a required figure",
        )

    def test_monthly_deadline_is_retained_but_only_as_an_election(self):
        """The monthly node is still read — it is a real s.64(2) election — but it is
        no longer what a preparer is shown as *the* deadline."""
        by_key = {s.rates_key: s for s in vat.REFERENCE_SPECS}
        self.assertIn("deadlines.vat_return_monthly", by_key)
        self.assertEqual(by_key["deadlines.vat_return_monthly"].required, vat.OPTIONAL)

    def test_legacy_settlement_window_is_a_reference_figure(self):
        by_key = {s.rates_key: s for s in vat.REFERENCE_SPECS}
        self.assertIn("deadlines.vat_legacy_settlement_s137a", by_key)
        spec = by_key["deadlines.vat_legacy_settlement_s137a"]
        self.assertEqual(spec.required, vat.OPTIONAL, "a closed window must not break a run")
        self.assertEqual(spec.kind, "text")

    def test_both_deadlines_reach_the_rendered_report(self):
        position = self.position()
        figures = {f.key: f for f in position.references}
        self.assertIn("return_deadline", figures)
        self.assertIn("legacy_settlement_window", figures)
        text = vat.render_markdown(position)
        self.assertIn("ত্রৈমাসিক", text)
        self.assertIn("পুরনো মূসক দাবি নিষ্পত্তির সুযোগ", text)

    def test_the_shipped_rates_file_carries_the_s137a_node(self):
        """Not a fixture assertion — the real AY 2026-27 file must carry the window,
        so `rates.py --key deadlines.vat_legacy_settlement_s137a` can print it."""
        real = REPO_ROOT / "src" / "data" / "rates-AY2026-27.toml"
        table = tb.RatesTable.from_toml_path(real)
        entry = table.raw["deadlines"]["vat_legacy_settlement_s137a"]
        self.assertIn("31 December 2026", entry["value"])
        self.assertIs(entry["verified"], False, "the close rests on secondary reporting")
        self.assertIn("137A", entry["note"])

    def test_s137a_window_is_not_confused_with_tds_section_137A(self):
        """ITA 2023 s.137A (club membership withholding) and VAT Act s.137A (the legacy
        settlement window) share a number and are unrelated.  Each must say so, so that
        grepping 137A cannot make either look like coverage of the other."""
        real = REPO_ROOT / "src" / "data" / "rates-AY2026-27.toml"
        raw = tb.RatesTable.from_toml_path(real).raw
        vat_note = raw["deadlines"]["vat_legacy_settlement_s137a"]["note"]
        tds_note = raw["tds"]["sections"]["137A"]["note"]
        self.assertIn("VAT Act", vat_note)
        self.assertIn("not", vat_note.lower())
        self.assertIn("VAT Act", tds_note)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
