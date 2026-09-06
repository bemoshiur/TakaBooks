"""Tests for ``src/engine/tax.py`` and ``src/engine/rates.py``.

Run with::

    python3 -m unittest discover tests

Every computation test runs against a SYNTHETIC rates fixture (``FIXTURE`` below) whose
figures are round numbers chosen so the expected values can be checked by hand.  They are
**not** Bangladeshi tax figures, and the tests do not depend on the real
``src/data/rates-AY2026-27.toml`` carrying any particular value — that file is only tested
for its *shape* and for being correctly refused while it is a placeholder.

Golden case (fixture AY 2031-32, category ``general``, threshold ৳1,00,000):

    income ৳10,00,000 · investment ৳3,00,000 · net wealth ৳6,00,00,000 · tax paid ৳20,000

    slab 1   1,00,000 @  0%  =       0
    slab 2     50,000 @  5%  =   2,500
    slab 3   1,00,000 @ 10%  =  10,000
    slab 4   2,00,000 @ 15%  =  30,000
    slab 5   5,50,000 @ 20%  = 1,10,000      gross tax 1,52,500
    rebate: eligible = min(3,00,000, 25% × 10,00,000 = 2,50,000, 5,00,000) = 2,50,000
            10% × 2,50,000 = 25,000         tax after rebate 1,27,500
    minimum tax: metro floor 4,000 < 1,27,500  → unchanged
    surcharge: wealth 6,00,00,000 > 5,00,00,000 → band 3 @ 20% × 1,27,500 = 25,500
    total 1,53,000 · less paid 20,000 → net payable 1,33,000

TakaBooks — Moshiur Rahman (@bemoshiur) · Ticon Sys — https://ticonsys.com
"""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import tempfile
import tokenize
import unittest
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = REPO_ROOT / "src" / "engine"
DATA_DIR = REPO_ROOT / "src" / "data"
REAL_RATES = DATA_DIR / "rates-AY2026-27.toml"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import rates as rt  # noqa: E402
import takabooks as tb  # noqa: E402
import tax  # noqa: E402
import vat  # noqa: E402  (posture symmetry is asserted against the other engine)

M = tb.Money


def T(value) -> tb.Money:
    """Taka -> Money."""
    return M.from_taka(value)


FIXTURE_AY = "2031-32"
FIXTURE_NAME = f"rates-AY{FIXTURE_AY}.toml"
SRC = 'source = "https://example.invalid/fixture"'

# ``# MARK:`` comments let tests derive variants by editing one line (or one 5-line block)
# without a TOML writer, which the stdlib does not have.
FIXTURE = f"""\
# SYNTHETIC TEST FIXTURE — these are NOT Bangladeshi tax figures.
[meta]
assessment_year = "{FIXTURE_AY}"
placeholder = false  # MARK:file_placeholder
note = "Synthetic fixture with round numbers so tests can be hand-checked."

[income_tax.individual]
default_category = "general"  # MARK:default_category
default_location = "metro"

[income_tax.individual.thresholds.general]
label_en = "General taxpayer"
label_bn = "সাধারণ করদাতা"
value = 100000
unit = "BDT"
{SRC}
as_of = "2031-01-01"
verified = true  # MARK:general_verified

[income_tax.individual.thresholds.female]
label_en = "Female taxpayer"
label_bn = "নারী করদাতা"
value = 150000
unit = "BDT"
{SRC}
verified = true

[[income_tax.individual.slabs]]
order = 1
label_en = "Tax-free threshold"
label_bn = "করমুক্ত আয়সীমা"
width_source = "category_threshold"  # MARK:slab1_width_source
  [income_tax.individual.slabs.rate]  # MARK:slab1_rate
  value = 0
  unit = "percent"
  {SRC}
  verified = true

[[income_tax.individual.slabs]]
order = 2
label_en = "Second slab"
label_bn = "দ্বিতীয় ধাপ"
  [income_tax.individual.slabs.width]
  value = 50000
  unit = "BDT"
  {SRC}
  verified = true
  [income_tax.individual.slabs.rate]  # MARK:slab2_rate
  value = 5  # MARK:slab2_rate_value
  unit = "percent"
  {SRC}
  verified = true

[[income_tax.individual.slabs]]
order = 3
label_en = "Third slab"
label_bn = "তৃতীয় ধাপ"
  [income_tax.individual.slabs.width]  # MARK:slab3_width
  value = 100000
  unit = "BDT"
  {SRC}
  verified = true
  [income_tax.individual.slabs.rate]
  value = 10
  unit = "percent"
  {SRC}
  verified = true

[[income_tax.individual.slabs]]
order = 4
label_en = "Fourth slab"
label_bn = "চতুর্থ ধাপ"
  [income_tax.individual.slabs.width]
  value = 200000
  unit = "BDT"
  {SRC}
  verified = true
  [income_tax.individual.slabs.rate]
  value = 15
  unit = "percent"
  {SRC}
  verified = true

[[income_tax.individual.slabs]]
order = 5
label_en = "Top slab"
label_bn = "সর্বোচ্চ ধাপ"
  [income_tax.individual.slabs.rate]  # MARK:slab5_rate
  value = 20
  unit = "percent"
  {SRC}
  verified = true

[income_tax.individual.rebate]
formula = "min_of_three_caps"  # MARK:formula
  [income_tax.individual.rebate.rate]
  value = 10
  unit = "percent"
  {SRC}
  verified = true  # MARK:rebate_rate_verified
  [income_tax.individual.rebate.income_cap_percent]
  value = 25
  unit = "percent"
  {SRC}
  verified = true
  [income_tax.individual.rebate.absolute_cap]
  value = 500000
  unit = "BDT"
  {SRC}
  verified = true

[income_tax.individual.minimum_tax.applies_when]
value = "taxable_income_above_threshold"  # MARK:applies_when
unit = "policy"
allowed = ["always", "taxable_income_above_threshold", "never"]  # MARK:applies_when_allowed
{SRC}
verified = true

[income_tax.individual.minimum_tax.by_location.metro]
label_en = "Metro"
label_bn = "মহানগর"
value = 4000
unit = "BDT"
{SRC}
verified = true

[income_tax.individual.minimum_tax.by_location.rural]
label_en = "Rural"
label_bn = "গ্রামীণ"
value = 2000
unit = "BDT"
{SRC}
verified = true

[income_tax.individual.minimum_tax.on_gross_receipts.rate]
value = "0.5"  # MARK:receipts_rate
unit = "percent"
{SRC}
verified = true

[income_tax.individual.minimum_tax.on_gross_receipts.applies_above]
value = 2000000
unit = "BDT"
{SRC}
verified = true

[income_tax.individual.surcharge.base]
value = "tax_after_minimum"  # MARK:surcharge_base
unit = "policy"
allowed = ["tax_after_rebate", "tax_after_minimum"]
{SRC}
verified = true

[income_tax.individual.surcharge.minimum]
value = 0  # MARK:surcharge_minimum
unit = "BDT"
{SRC}
verified = true

[[income_tax.individual.surcharge.bands]]
order = 1
label_en = "No surcharge"
label_bn = "সারচার্জ নেই"
  [income_tax.individual.surcharge.bands.rate]  # MARK:band1_rate
  value = 0
  unit = "percent"
  {SRC}
  verified = true

[[income_tax.individual.surcharge.bands]]
order = 2
label_en = "Band two"
label_bn = "দ্বিতীয় ধাপ"
  [income_tax.individual.surcharge.bands.wealth_above]  # MARK:band2_wealth_above
  value = 10000000
  unit = "BDT"
  {SRC}
  verified = true
  [income_tax.individual.surcharge.bands.rate]
  value = 10
  unit = "percent"
  {SRC}
  verified = true

[[income_tax.individual.surcharge.bands]]
order = 3
label_en = "Band three"
label_bn = "তৃতীয় ধাপ"
  [income_tax.individual.surcharge.bands.wealth_above]
  value = 50000000  # MARK:band3_wealth_above_value
  unit = "BDT"
  {SRC}
  verified = true
  [income_tax.individual.surcharge.bands.rate]
  value = 20
  unit = "percent"
  {SRC}
  verified = true
"""

WIDTH_BLOCK = f"""\
  [income_tax.individual.slabs.width]
  value = 12345
  unit = "BDT"
  {SRC}
  verified = true
"""

BAND_WEALTH_BLOCK = f"""\
  [income_tax.individual.surcharge.bands.wealth_above]
  value = 1
  unit = "BDT"
  {SRC}
  verified = true
"""


def _marked_line(text: str, marker: str) -> str:
    for line in text.splitlines():
        if line.rstrip().endswith(f"# MARK:{marker}"):
            return line
    raise AssertionError(f"fixture has no line marked {marker}")


def replace_marked(text: str, marker: str, new_line: str) -> str:
    """Swap the single line carrying ``# MARK:<marker>`` for ``new_line``."""
    line = _marked_line(text, marker)
    indent = line[: len(line) - len(line.lstrip())]
    return text.replace(line + "\n", indent + new_line + "\n", 1)


def drop_block(text: str, marker: str, lines: int = 5) -> str:
    """Delete the marked line and the ``lines - 1`` lines after it (a whole rate node)."""
    all_lines = text.splitlines(keepends=True)
    for index, line in enumerate(all_lines):
        if line.rstrip().endswith(f"# MARK:{marker}"):
            del all_lines[index : index + lines]
            return "".join(all_lines)
    raise AssertionError(f"fixture has no line marked {marker}")


def insert_before(text: str, marker: str, block: str) -> str:
    line = _marked_line(text, marker)
    return text.replace(line + "\n", block + line + "\n", 1)


def run_cli(script: str, *args: str, cwd: "Path | str | None" = None) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(
        [sys.executable, str(ENGINE_DIR / script), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(cwd) if cwd else None,
        env=env,
    )


class FixtureCase(unittest.TestCase):
    """A temp data dir holding the synthetic fixture."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data_dir = self.root / "data"
        self.data_dir.mkdir()
        self.path = self.write_fixture()

    def write_fixture(self, text: str = FIXTURE, name: str = FIXTURE_NAME, directory: "Path | None" = None) -> Path:
        path = (directory or self.data_dir) / name
        path.write_text(text, encoding="utf-8")
        return path

    def rates(self, text: str | None = None, *, allow_placeholders: bool = False) -> rt.RateSet:
        path = self.path if text is None else self.write_fixture(text, name="variant.toml")
        return rt.RateSet.from_path(path, allow_placeholders=allow_placeholders)

    def compute(
        self,
        income,
        *,
        category: str = "general",
        location: str = "metro",
        investment=0,
        net_wealth=None,
        gross_receipts=None,
        tax_paid=0,
        text: str | None = None,
        rates: rt.RateSet | None = None,
        allow_placeholders: bool = False,
    ) -> tax.TaxComputation:
        rates = rates or self.rates(text, allow_placeholders=allow_placeholders)
        inputs = tax.TaxInputs(
            income=T(income),
            category=category,
            location=location,
            investment=T(investment),
            net_wealth=None if net_wealth is None else T(net_wealth),
            gross_receipts=None if gross_receipts is None else T(gross_receipts),
            tax_paid=T(tax_paid),
        )
        return tax.compute_income_tax(rates, inputs)


# ======================================================================================
# rates.py — assessment-year naming and file selection
# ======================================================================================


class TestAssessmentYearNaming(unittest.TestCase):
    def test_canonical_forms(self):
        for text in ("2026-27", "2026-2027", "AY2026-27", "ay 2026/27", "AY 2026–27", "2026_27", "২০২৬-২৭"):
            with self.subTest(text=text):
                self.assertEqual(rt.normalise_assessment_year(text), "2026-27")

    def test_century_rollover(self):
        self.assertEqual(rt.normalise_assessment_year("2099-00"), "2099-00")
        self.assertEqual(rt.normalise_assessment_year("2099-2100"), "2099-00")

    def test_rejects_non_consecutive_or_malformed(self):
        for text in ("2026", "2026-29", "2026-2028", "26-27", "", None, "next year"):
            with self.subTest(text=text):
                with self.assertRaises(tb.RatesError):
                    rt.normalise_assessment_year(text)

    def test_filename_round_trip(self):
        self.assertEqual(rt.rates_filename("2026-27"), "rates-AY2026-27.toml")
        self.assertEqual(rt.assessment_year_from_filename("rates-AY2026-27.toml"), "2026-27")
        self.assertEqual(rt.assessment_year_from_filename(Path("/x/rates-AY2026-2027.toml")), "2026-27")
        self.assertIsNone(rt.assessment_year_from_filename("rates.toml"))
        self.assertIsNone(rt.assessment_year_from_filename("rates-AY2026-29.toml"))


class TestFindRatesFile(FixtureCase):
    def test_single_file_needs_no_year(self):
        self.assertEqual(rt.find_rates_file(data_dir=self.data_dir), self.path)
        self.assertEqual(rt.available_assessment_years(self.data_dir), [FIXTURE_AY])

    def test_named_year_selects_file(self):
        other = self.write_fixture(FIXTURE.replace(FIXTURE_AY, "2032-33"), name="rates-AY2032-33.toml")
        self.assertEqual(rt.find_rates_file("2032-33", data_dir=self.data_dir), other)
        self.assertEqual(rt.find_rates_file("AY 2031/32", data_dir=self.data_dir), self.path)
        self.assertEqual(rt.available_assessment_years(self.data_dir), [FIXTURE_AY, "2032-33"])

    def test_several_files_without_a_year_is_refused(self):
        self.write_fixture(FIXTURE, name="rates-AY2032-33.toml")
        with self.assertRaises(tb.RatesError) as ctx:
            rt.find_rates_file(data_dir=self.data_dir)
        self.assertIn("name the assessment year", str(ctx.exception))
        self.assertIn("2031-32", ctx.exception.hint)
        self.assertIn("2032-33", ctx.exception.hint)

    def test_missing_year_lists_available(self):
        with self.assertRaises(tb.RatesError) as ctx:
            rt.find_rates_file("2040-41", data_dir=self.data_dir)
        self.assertIn("2040-41", str(ctx.exception))
        self.assertIn(FIXTURE_AY, ctx.exception.hint)

    def test_empty_or_missing_directory(self):
        empty = self.root / "empty"
        empty.mkdir()
        with self.assertRaises(tb.RatesError):
            rt.find_rates_file(data_dir=empty)
        with self.assertRaises(tb.RatesError):
            rt.find_rates_file(data_dir=self.root / "nope")

    def test_non_rates_files_are_ignored(self):
        (self.data_dir / "notes.toml").write_text("x = 1\n", encoding="utf-8")
        self.assertEqual([p.name for p in rt.available_rate_files(self.data_dir)], [FIXTURE_NAME])

    def test_default_data_dir_is_src_data(self):
        self.assertEqual(rt.default_data_dir(), DATA_DIR)


# ======================================================================================
# rates.py — RateSet: provenance, gating, coercion
# ======================================================================================


class TestRateSet(FixtureCase):
    def test_identity_and_provenance(self):
        rates = self.rates()
        self.assertEqual(rates.assessment_year, FIXTURE_AY)
        self.assertEqual(rates.require_assessment_year(), FIXTURE_AY)
        self.assertEqual(rates.filename, FIXTURE_NAME)
        self.assertIn(FIXTURE_NAME, rates.provenance())
        self.assertIn(FIXTURE_AY, rates.provenance())
        self.assertIn("করবর্ষ", rates.provenance())
        self.assertFalse(rates.file_is_placeholder)
        rates.require_usable()  # must not raise

    def test_entry_carries_provenance(self):
        entry = self.rates().rate("income_tax.individual.thresholds.general")
        self.assertTrue(entry.is_verified)
        self.assertFalse(entry.is_placeholder)
        self.assertFalse(entry.is_provisional)
        self.assertEqual(entry.caveat(), "")
        self.assertEqual(entry.as_money(), T(100000))
        self.assertEqual(entry.label, "সাধারণ করদাতা / General taxpayer")
        self.assertEqual(entry.as_of, "2031-01-01")
        self.assertIn("example.invalid", entry.provenance())
        self.assertIn("verified", entry.provenance())

    def test_missing_key_is_an_error_not_a_default(self):
        rates = self.rates()
        with self.assertRaises(tb.RatesError) as ctx:
            rates.rate("income_tax.individual.thresholds.martian")
        self.assertEqual(ctx.exception.exit_code, 8)
        self.assertIn("never substitutes", ctx.exception.hint)
        self.assertIsNone(rates.optional_rate("income_tax.individual.thresholds.martian"))
        self.assertIsNotNone(rates.optional_rate("income_tax.individual.thresholds.general"))
        self.assertFalse(rates.has("income_tax.nothing"))

    def test_section_without_value_is_not_a_rate(self):
        with self.assertRaises(tb.RatesError):
            self.rates().rate("income_tax.individual.thresholds")
        with self.assertRaises(tb.RatesError):
            self.rates().section("income_tax.individual.thresholds.general.value")

    def test_placeholder_node_refused_by_default(self):
        text = FIXTURE.replace("verified = true  # MARK:general_verified", "verified = false\nplaceholder = true")
        with self.assertRaises(tb.RatesError) as ctx:
            self.rates(text).rate("income_tax.individual.thresholds.general")
        self.assertIn("placeholder", str(ctx.exception))
        entry = self.rates(text, allow_placeholders=True).rate("income_tax.individual.thresholds.general")
        self.assertTrue(entry.is_placeholder)
        self.assertTrue(entry.is_provisional)
        self.assertTrue(entry.caveat().startswith("PLACEHOLDER"))

    def test_placeholder_file_refused_until_opted_in(self):
        text = replace_marked(FIXTURE, "file_placeholder", "placeholder = true")
        with self.assertRaises(tb.RatesError) as ctx:
            self.rates(text).require_usable()
        self.assertIn("--allow-placeholder-rates", ctx.exception.hint)
        rates = self.rates(text, allow_placeholders=True)
        rates.require_usable()
        self.assertTrue(rates.file_is_placeholder)
        self.assertTrue(rates.is_provisional)
        self.assertTrue(rates.caveats()[0].startswith("PLACEHOLDER FILE"))

    def test_unverified_node_is_allowed_but_provisional(self):
        text = replace_marked(FIXTURE, "general_verified", "verified = false")
        rates = self.rates(text)
        self.assertFalse(rates.is_provisional)
        entry = rates.rate("income_tax.individual.thresholds.general")
        self.assertFalse(entry.is_verified)
        self.assertFalse(entry.is_placeholder)
        self.assertTrue(entry.caveat().startswith("UNVERIFIED"))
        self.assertIn("income_tax.individual.thresholds.general", entry.caveat())
        self.assertTrue(rates.is_provisional)
        self.assertEqual(len(rates.caveats()), 1)
        self.assertEqual(rates.unverified_used(), (entry,))

    def test_bare_scalar_is_never_verified(self):
        entry = self.rates().rate("income_tax.individual.default_category")
        self.assertEqual(entry.value, "general")
        self.assertFalse(entry.is_verified)
        self.assertEqual(entry.as_text(), "general")

    def test_float_value_is_refused(self):
        text = replace_marked(FIXTURE, "receipts_rate", "value = 0.5")
        with self.assertRaises(tb.RatesError) as ctx:
            self.rates(text).rate("income_tax.individual.minimum_tax.on_gross_receipts.rate")
        self.assertIn("float", str(ctx.exception))
        self.assertIn('"7.5"', ctx.exception.hint)

    def test_percent_coercion(self):
        rates = self.rates()
        self.assertEqual(rates.percent("income_tax.individual.minimum_tax.on_gross_receipts.rate"), Decimal("0.5"))
        self.assertEqual(rates.fraction("income_tax.individual.rebate.rate"), Decimal("0.1"))
        self.assertEqual(rates.decimal("income_tax.individual.rebate.absolute_cap"), Decimal(500000))
        text = replace_marked(FIXTURE, "receipts_rate", 'value = "150"')
        with self.assertRaises(tb.RatesError) as ctx:
            self.rates(text).percent("income_tax.individual.minimum_tax.on_gross_receipts.rate")
        self.assertIn("not a percentage", str(ctx.exception))
        text = replace_marked(FIXTURE, "receipts_rate", 'value = "-1"')
        with self.assertRaises(tb.RatesError):
            self.rates(text).percent("income_tax.individual.minimum_tax.on_gross_receipts.rate")
        text = replace_marked(FIXTURE, "receipts_rate", 'value = "half"')
        with self.assertRaises(tb.RatesError):
            self.rates(text).percent("income_tax.individual.minimum_tax.on_gross_receipts.rate")
        text = replace_marked(FIXTURE, "receipts_rate", 'value = ""')
        with self.assertRaises(tb.RatesError) as ctx:
            self.rates(text).percent("income_tax.individual.minimum_tax.on_gross_receipts.rate")
        self.assertIn("blank", str(ctx.exception))

    def test_money_coercion(self):
        rates = self.rates()
        self.assertEqual(rates.money("income_tax.individual.surcharge.minimum"), M.zero())
        self.assertEqual(rates.money("income_tax.individual.minimum_tax.by_location.metro"), T(4000))
        text = replace_marked(FIXTURE, "surcharge_minimum", 'value = "-5"')
        with self.assertRaises(tb.RatesError):
            self.rates(text).money("income_tax.individual.surcharge.minimum")
        self.assertEqual(
            self.rates(text).money("income_tax.individual.surcharge.minimum", allow_negative=True), T(-5)
        )
        text = replace_marked(FIXTURE, "surcharge_minimum", 'value = "1,00,000.50"')
        self.assertEqual(self.rates(text).money("income_tax.individual.surcharge.minimum"), M(10000050))

    def test_policy_choice(self):
        rates = self.rates()
        self.assertEqual(rates.choice(tax.KEY_MINIMUM_TAX_APPLIES_WHEN, tax.MINIMUM_TAX_POLICIES),
                         "taxable_income_above_threshold")
        text = replace_marked(FIXTURE, "applies_when", 'value = "sometimes"')
        with self.assertRaises(tb.RatesError) as ctx:
            self.rates(text).choice(tax.KEY_MINIMUM_TAX_APPLIES_WHEN, tax.MINIMUM_TAX_POLICIES)
        self.assertIn("sometimes", str(ctx.exception))
        # A file that *offers* an option the engine cannot implement fails at read time.
        text = replace_marked(FIXTURE, "applies_when_allowed", 'allowed = ["always", "on_tuesdays"]')
        with self.assertRaises(tb.RatesError) as ctx:
            self.rates(text).choice(tax.KEY_MINIMUM_TAX_APPLIES_WHEN, tax.MINIMUM_TAX_POLICIES)
        self.assertIn("on_tuesdays", str(ctx.exception))

    def test_items_and_option_keys(self):
        rates = self.rates()
        self.assertEqual(len(rates.items(tax.KEY_SLABS)), 5)
        self.assertEqual(len(rates.items(tax.KEY_SURCHARGE_BANDS)), 3)
        self.assertEqual(rates.option_keys(tax.KEY_THRESHOLDS), ["general", "female"])
        self.assertEqual(rates.option_keys(tax.KEY_MINIMUM_TAX_BY_LOCATION), ["metro", "rural"])
        with self.assertRaises(tb.RatesError):
            rates.items("income_tax.individual.nothing")
        with self.assertRaises(tb.RatesError):
            rates.items("income_tax.individual.thresholds")  # a table, not a list
        empty = self.rates("[meta]\nassessment_year = '2031-32'\n[income_tax.individual]\nslabs = []\n")
        with self.assertRaises(tb.RatesError) as ctx:
            empty.items(tax.KEY_SLABS)
        self.assertIn("empty", str(ctx.exception))

    def test_used_tracks_first_use_order(self):
        rates = self.rates()
        rates.money("income_tax.individual.minimum_tax.by_location.metro")
        rates.percent("income_tax.individual.rebate.rate")
        rates.money("income_tax.individual.minimum_tax.by_location.metro")  # again: no duplicate
        self.assertEqual(
            [e.key for e in rates.used()],
            ["income_tax.individual.minimum_tax.by_location.metro", "income_tax.individual.rebate.rate"],
        )
        self.assertEqual(rates.unverified_used(), ())
        self.assertEqual(rates.placeholders_used(), ())

    def test_audit_census(self):
        audit = self.rates().audit()
        self.assertTrue(audit["usable"])
        self.assertEqual(audit["placeholder_count"], 0)
        self.assertEqual(audit["unverified_count"], 0)
        self.assertEqual(audit["verified_count"], audit["total_rate_nodes"])
        self.assertIn("income_tax.individual.slabs[1].width", audit["verified"])
        text = replace_marked(FIXTURE, "general_verified", "verified = false")
        audit = self.rates(text).audit()
        self.assertFalse(audit["usable"])
        self.assertEqual(audit["unverified"], ["income_tax.individual.thresholds.general"])

    def test_bad_file_is_a_rates_error(self):
        bad = self.write_fixture("this is = not [toml", name="rates-AY2031-32.toml", directory=self.root)
        with self.assertRaises(tb.RatesError):
            rt.RateSet.from_path(bad)
        with self.assertRaises(tb.RatesError):
            rt.RateSet.from_path(self.root / "absent.toml")
        with self.assertRaises(tb.RatesError):
            rt.RateSet("not a table")  # type: ignore[arg-type]

    def test_file_without_assessment_year(self):
        path = self.write_fixture("[meta]\nx = 1\n", name="rates.toml")
        with self.assertRaises(tb.RatesError) as ctx:
            rt.RateSet.from_path(path).require_assessment_year()
        self.assertIn("assessment year", str(ctx.exception))


class TestResolveRates(FixtureCase):
    def _config(self, body: str, directory: "Path | None" = None) -> tb.Config:
        books = directory or (self.root / "books")
        books.mkdir(exist_ok=True)
        (books / "config.toml").write_text(body, encoding="utf-8")
        return tb.Config.load(books)

    def test_explicit_path_wins(self):
        config = self._config('[books]\nassessment_year = "2040-41"\n')
        rates = rt.resolve_rates(path=self.path, config=config, data_dir=self.root / "nope")
        self.assertEqual(rates.assessment_year, FIXTURE_AY)

    def test_explicit_year_beats_config(self):
        config = self._config('[books]\nassessment_year = "2040-41"\n')
        rates = rt.resolve_rates(assessment_year="2031-32", config=config, data_dir=self.data_dir)
        self.assertEqual(rates.assessment_year, FIXTURE_AY)

    def test_config_rates_file_relative_to_config(self):
        books = self.root / "books"
        books.mkdir()
        self.write_fixture(FIXTURE, name="my-rates.toml", directory=books)
        config = self._config('[books]\nrates_file = "my-rates.toml"\n', directory=books)
        rates = rt.resolve_rates(config=config, data_dir=self.root / "nope")
        self.assertEqual(rates.filename, "my-rates.toml")
        self.assertEqual(rates.assessment_year, FIXTURE_AY)  # from [meta]

    def test_config_rates_file_missing_is_an_error(self):
        config = self._config('[books]\nrates_file = "ghost.toml"\n')
        with self.assertRaises(tb.RatesError) as ctx:
            rt.resolve_rates(config=config, data_dir=self.data_dir)
        self.assertIn("ghost.toml", str(ctx.exception))

    def test_config_assessment_year_picks_file(self):
        config = self._config(f'[books]\nassessment_year = "{FIXTURE_AY}"\n')
        self.write_fixture(FIXTURE, name="rates-AY2032-33.toml")  # a second file: year must decide
        rates = rt.resolve_rates(config=config, data_dir=self.data_dir)
        self.assertEqual(rates.path, self.path)

    def test_no_hints_at_all_uses_the_only_file(self):
        rates = rt.resolve_rates(data_dir=self.data_dir)
        self.assertEqual(rates.path, self.path)

    def test_config_helper_skips_missing_but_not_broken(self):
        self.assertIsNone(rt._load_config_if_present(self.root / "nobooks"))
        self.assertIsNone(tax.load_config_if_present(self.root / "nobooks"))
        books = self.root / "books"
        books.mkdir()
        (books / "config.toml").write_text('[books]\ncurrency = "USD"\n', encoding="utf-8")
        with self.assertRaises(tb.ConfigError):
            rt._load_config_if_present(books)
        with self.assertRaises(tb.ConfigError):
            tax.load_config_if_present(books)


class TestRatesCli(FixtureCase):
    def test_list(self):
        result = run_cli("rates.py", "--list", "--data-dir", str(self.data_dir), cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(FIXTURE_AY, result.stdout)
        result = run_cli("rates.py", "--list", "--json", "--data-dir", str(self.data_dir), cwd=self.root)
        self.assertEqual(json.loads(result.stdout)["assessment_years"], [FIXTURE_AY])

    def test_audit_of_verified_fixture(self):
        result = run_cli("rates.py", "--rates", str(self.path), cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Every rate node in this file is marked verified", result.stdout)
        self.assertIn(tb.ATTRIBUTION, result.stdout)
        result = run_cli("rates.py", "--rates", str(self.path), "--json", cwd=self.root)
        audit = json.loads(result.stdout)
        self.assertTrue(audit["ok"])
        self.assertTrue(audit["usable"])
        self.assertIn("Rates source:", audit["rates_source"])

    def test_key_lookup(self):
        result = run_cli("rates.py", "--rates", str(self.path), "--key",
                         "income_tax.individual.thresholds.general", cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("100000", result.stdout)
        self.assertIn("General taxpayer", result.stdout)
        result = run_cli("rates.py", "--rates", str(self.path), "--key", "no.such.key", cwd=self.root)
        self.assertEqual(result.returncode, 8)
        self.assertIn("no value", result.stderr)

    def test_real_file_audit_counts_each_verification_state(self):
        """The shipped file is MIXED — landed, unlanded and unverified nodes together."""
        result = run_cli("rates.py", "--rates", str(REAL_RATES), "--json", cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        audit = json.loads(result.stdout)
        self.assertGreater(audit["verified_count"], 0)
        self.assertGreater(audit["placeholder_count"], 0)   # still figures to land
        self.assertEqual(
            audit["verified_count"] + audit["unverified_count"] + audit["placeholder_count"],
            audit["total_rate_nodes"],
        )
        # A mixed file is not "usable" as a whole: it still has unlanded nodes in it.
        self.assertFalse(audit["usable"])
        result = run_cli("rates.py", "--rates", str(REAL_RATES), cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("NOT ready", result.stdout)

    def test_real_file_placeholder_node_is_still_refused_one_by_one(self):
        """Per figure, not per file: a landed file may still hold unlanded nodes."""
        audit = json.loads(
            run_cli("rates.py", "--rates", str(REAL_RATES), "--json", "--all",
                    cwd=self.root).stdout
        )
        self.assertTrue(audit["placeholder"], "shipped file has no placeholder node left")
        key = audit["placeholder"][0]
        result = run_cli("rates.py", "--rates", str(REAL_RATES), "--key", key, cwd=self.root)
        self.assertEqual(result.returncode, 8, result.stdout)
        self.assertIn("placeholder", result.stderr)
        result = run_cli("rates.py", "--rates", str(REAL_RATES), "--key", key,
                         "--allow-placeholder-rates", cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PLACEHOLDER", result.stdout)
        # …while a node that HAS landed reads cleanly with no opt-in at all.
        self.assertTrue(audit["verified"])
        result = run_cli("rates.py", "--rates", str(REAL_RATES), "--key",
                         audit["verified"][0], cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)


# ======================================================================================
# The shipped rates-AY2026-27.toml — a MIXED file: some figures landed, some not
# ======================================================================================


class TestShippedRatesFile(unittest.TestCase):
    def setUp(self):
        self.assertTrue(REAL_RATES.is_file(), REAL_RATES)
        self.rates = rt.RateSet.from_path(REAL_RATES, allow_placeholders=True)
        self.text = REAL_RATES.read_text(encoding="utf-8")

    def test_header_states_how_far_the_file_is_verified(self):
        self.assertIn("ticonsys.com", self.text)
        # The file must document its own verification vocabulary for whoever edits it.
        for phrase in ("verified = true", "verified = false", "placeholder = true"):
            self.assertIn(phrase, self.text, phrase)
        self.assertIn("Absent beats wrong", self.text)

    def test_states_its_assessment_year_and_its_own_landed_state(self):
        self.assertEqual(self.rates.assessment_year, "2026-27")
        # [meta] placeholder is the contract flag both engines gate on. Whatever it says,
        # tax.py and vat.py must agree about it.
        self.assertEqual(
            tax.rates_file_is_placeholder(self.rates),
            vat.rates_file_is_placeholder(self.rates),
        )

    def test_every_rate_node_carries_its_provenance_keys(self):
        audit = self.rates.audit()
        self.assertGreater(audit["total_rate_nodes"], 0)
        self.assertEqual(
            audit["verified_count"] + audit["unverified_count"] + audit["placeholder_count"],
            audit["total_rate_nodes"],
        )

        problems: list[str] = []

        def walk(node, prefix):
            if isinstance(node, dict):
                if "value" in node:
                    for key in ("source", "verified", "note", "placeholder"):
                        if key not in node:
                            problems.append(f"{prefix} lacks {key}")
                    if not isinstance(node.get("verified"), bool):
                        problems.append(f"{prefix} verified is not a boolean")
                    if node.get("verified") is True and node.get("placeholder") is True:
                        problems.append(f"{prefix} is both verified and a placeholder")
                    if not str(node.get("source", "")).startswith("http"):
                        problems.append(f"{prefix} source is not a URL")
                    return
                for key, child in node.items():
                    walk(child, f"{prefix}.{key}" if prefix else key)
            elif isinstance(node, list):
                for index, child in enumerate(node):
                    walk(child, f"{prefix}[{index}]")

        walk(self.rates.table.raw, "")
        self.assertEqual(problems, [])

    def test_no_float_anywhere_in_the_file(self):
        floats: list[str] = []

        def walk(node, prefix):
            if isinstance(node, float):
                floats.append(prefix)
            elif isinstance(node, dict):
                for key, child in node.items():
                    walk(child, f"{prefix}.{key}" if prefix else key)
            elif isinstance(node, list):
                for index, child in enumerate(node):
                    walk(child, f"{prefix}[{index}]")

        walk(self.rates.table.raw, "")
        self.assertEqual(floats, [])

    def test_unlanded_nodes_are_refused_one_by_one_without_the_opt_in(self):
        """Per figure, not per file: this is the MIXED case the engines must handle."""
        audit = self.rates.audit()
        gated = rt.RateSet.from_path(REAL_RATES)
        self.assertTrue(audit["placeholder"], "no placeholder node left to test against")
        for key in audit["placeholder"][:5]:
            with self.subTest(key=key):
                with self.assertRaises(tb.RatesError) as ctx:
                    gated.rate(key)
                self.assertIn("placeholder", str(ctx.exception))
                self.assertIn("--allow-placeholder-rates", ctx.exception.hint)
        # A landed node on the same file reads with no opt-in and is not provisional.
        for key in audit["verified"][:5]:
            with self.subTest(key=key):
                entry = rt.RateSet.from_path(REAL_RATES).rate(key)
                self.assertTrue(entry.is_verified)
                self.assertEqual(entry.caveat(), "")
        # A landed-but-unverified node reads too, and says so out loud.
        for key in audit["unverified"][:5]:
            with self.subTest(key=key):
                entry = rt.RateSet.from_path(REAL_RATES).rate(key)
                self.assertFalse(entry.is_verified)
                self.assertTrue(entry.caveat().startswith("UNVERIFIED"))

    def test_carries_every_key_tax_py_reads(self):
        for key in (
            tax.KEY_INDIVIDUAL, tax.KEY_THRESHOLDS, tax.KEY_SLABS, tax.KEY_REBATE,
            tax.KEY_REBATE_RATE, tax.KEY_REBATE_INCOME_CAP_PERCENT, tax.KEY_REBATE_ABSOLUTE_CAP,
            tax.KEY_MINIMUM_TAX_APPLIES_WHEN, tax.KEY_MINIMUM_TAX_BY_LOCATION,
            tax.KEY_MINIMUM_TAX_RECEIPTS_RATE, tax.KEY_MINIMUM_TAX_RECEIPTS_ABOVE,
            tax.KEY_SURCHARGE, tax.KEY_SURCHARGE_BASE, tax.KEY_SURCHARGE_MINIMUM,
            tax.KEY_SURCHARGE_BANDS,
        ):
            with self.subTest(key=key):
                self.assertTrue(self.rates.has(key), key)
        for section in ("vat.rates.standard", "vat.thresholds.registration", "tds.sections",
                        "vds.services", "deadlines", "income_tax.corporate.rates"):
            with self.subTest(section=section):
                self.assertTrue(self.rates.has(section), section)

    def test_shape_satisfies_the_structural_checks(self):
        """The schema must satisfy tax.py's structural checks (slab/band ordering etc.)."""
        individual = self.rates.section(tax.KEY_INDIVIDUAL)
        category = individual["default_category"]
        location = individual["default_location"]
        self.assertIn(category, tax.available_categories(self.rates))
        self.assertIn(location, tax.available_locations(self.rates))
        threshold, entry = tax.category_threshold(self.rates, category)
        slabs = tax.build_slabs(self.rates, threshold, threshold_key=entry.key)
        self.assertGreaterEqual(len(slabs), 2)
        self.assertTrue(slabs[-1].is_open_ended)
        self.assertTrue(all(not s.is_open_ended for s in slabs[:-1]))
        self.assertEqual(slabs[0].width_key, entry.key)

    def test_a_working_that_needs_an_unlanded_figure_is_refused_and_names_it(self):
        """The MIXED case end to end: the same file computes, then refuses at the node.

        ``income_tax.individual.minimum_tax.on_gross_receipts.applies_above`` had not
        landed when this was written.  If it later does, this test finds another unlanded
        input rather than asserting a Bangladeshi figure of its own — and skips loudly if
        the whole file has landed, which is the day this refusal stops being reachable.
        """
        individual = self.rates.section(tax.KEY_INDIVIDUAL)
        category, location = individual["default_category"], individual["default_location"]
        gated = rt.RateSet.from_path(REAL_RATES)

        def inputs(**over):
            base = dict(income=T(800000), category=category, location=location,
                        investment=T(0), net_wealth=None, gross_receipts=None,
                        tax_paid=T(0))
            base.update(over)
            return tax.TaxInputs(**base)

        placeholders = set(self.rates.audit()["placeholder"])
        if not any(key.startswith("income_tax.individual.") for key in placeholders):
            self.skipTest("every individual income-tax figure has landed")

        with self.assertRaises(tb.RatesError) as ctx:
            tax.compute_income_tax(gated, inputs(gross_receipts=T(5000000)))
        self.assertIn("placeholder", str(ctx.exception))
        self.assertIn("--allow-placeholder-rates", ctx.exception.hint)

        # The very same file, opted into, computes and stamps the result unmistakably.
        allowed = rt.RateSet.from_path(REAL_RATES, allow_placeholders=True)
        result = tax.compute_income_tax(allowed, inputs(gross_receipts=T(5000000)))
        self.assertTrue(result.placeholder_data_used)
        self.assertEqual(result.data_grade, tax.GRADE_PLACEHOLDER)
        self.assertEqual(result.filing_status, tax.STATUS_PLACEHOLDER)
        self.assertTrue(result.placeholder_figures)
        self.assertTrue(any(c.startswith("PLACEHOLDER") for c in result.caveats))

    def test_landed_nodes_compute_without_any_opt_in(self):
        """A mixed file must still work for a working that touches only landed figures."""
        individual = self.rates.section(tax.KEY_INDIVIDUAL)
        result = tax.compute_income_tax(
            rt.RateSet.from_path(REAL_RATES),
            tax.TaxInputs(
                income=T(800000),
                category=individual["default_category"],
                location=individual["default_location"],
            ),
        )
        self.assertFalse(result.placeholder_data_used)
        self.assertNotEqual(result.data_grade, tax.GRADE_PLACEHOLDER)
        self.assertTrue(result.rates_used)
        self.assertFalse(any(e.is_placeholder for e in result.rates_used))


# ======================================================================================
# tax.py — slabs
# ======================================================================================


class TestSlabs(FixtureCase):
    def test_build_slabs_shape(self):
        rates = self.rates()
        threshold, entry = tax.category_threshold(rates, "general")
        slabs = tax.build_slabs(rates, threshold, threshold_key=entry.key)
        self.assertEqual([s.order for s in slabs], [1, 2, 3, 4, 5])
        self.assertEqual([s.lower for s in slabs], [T(0), T(100000), T(150000), T(250000), T(450000)])
        self.assertEqual([s.upper for s in slabs], [T(100000), T(150000), T(250000), T(450000), None])
        self.assertEqual(slabs[0].width, T(100000))
        self.assertEqual(slabs[0].width_key, "income_tax.individual.thresholds.general")
        self.assertEqual(slabs[1].width_key, "income_tax.individual.slabs[1].width")
        self.assertEqual(slabs[4].rate_key, "income_tax.individual.slabs[4].rate")
        self.assertTrue(slabs[-1].is_open_ended)
        self.assertEqual(slabs[1].label, "দ্বিতীয় ধাপ / Second slab")
        self.assertEqual([s.rate for s in slabs], [Decimal(0), Decimal(5), Decimal(10), Decimal(15), Decimal(20)])

    def test_female_threshold_widens_first_slab(self):
        rates = self.rates()
        threshold, entry = tax.category_threshold(rates, "female")
        slabs = tax.build_slabs(rates, threshold, threshold_key=entry.key)
        self.assertEqual(slabs[0].width, T(150000))
        self.assertEqual(slabs[1].lower, T(150000))
        self.assertEqual(slabs[4].lower, T(500000))

    def test_golden_slab_working(self):
        result = self.compute(1000000)
        taxable = [s.taxable for s in result.slabs]
        taxes = [s.tax for s in result.slabs]
        self.assertEqual(taxable, [T(100000), T(50000), T(100000), T(200000), T(550000)])
        self.assertEqual(taxes, [T(0), T(2500), T(10000), T(30000), T(110000)])
        self.assertEqual(M.sum(taxable), T(1000000))
        self.assertEqual(result.gross_tax, T(152500))

    def test_zero_and_below_threshold(self):
        self.assertEqual(self.compute(0).gross_tax, M.zero())
        result = self.compute(90000)
        self.assertEqual([s.taxable for s in result.slabs], [T(90000), T(0), T(0), T(0), T(0)])
        self.assertEqual(result.gross_tax, M.zero())
        self.assertFalse(result.is_above_threshold)

    def test_exact_boundaries(self):
        self.assertEqual(self.compute(100000).gross_tax, M.zero())
        self.assertFalse(self.compute(100000).is_above_threshold)
        result = self.compute(150000)
        self.assertEqual([s.taxable for s in result.slabs], [T(100000), T(50000), T(0), T(0), T(0)])
        self.assertEqual(result.gross_tax, T(2500))
        self.assertEqual(self.compute(100001).gross_tax, M(5))  # 5% of ৳1 = 5 paisa

    def test_round_half_up_once_per_slab(self):
        text = replace_marked(FIXTURE, "slab2_rate_value", 'value = "7.5"')
        result = self.compute(133333, text=text)
        # 7.5% of ৳33,333 = ৳2,499.975 -> ৳2,499.98 (half up), never a float
        self.assertEqual(result.slabs[1].taxable, T(33333))
        self.assertEqual(result.slabs[1].tax, M(249998))
        self.assertEqual(result.gross_tax, M(249998))
        self.assertEqual(result.slabs[1].rate, Decimal("7.5"))

    def test_rows_add_up_to_total_for_awkward_income(self):
        result = self.compute("1234567.89")
        self.assertEqual(M.sum(s.taxable for s in result.slabs), M(123456789))
        self.assertEqual(M.sum(s.tax for s in result.slabs), result.gross_tax)

    def test_open_ended_slab_must_be_last(self):
        text = drop_block(FIXTURE, "slab3_width")
        with self.assertRaises(tb.RatesError) as ctx:
            self.compute(1, text=text)
        self.assertIn("open-ended", str(ctx.exception))
        self.assertIn("slabs[2]", str(ctx.exception))

    def test_last_slab_must_be_open_ended(self):
        text = insert_before(FIXTURE, "slab5_rate", WIDTH_BLOCK)
        with self.assertRaises(tb.RatesError) as ctx:
            self.compute(1, text=text)
        self.assertIn("open-ended", str(ctx.exception))

    def test_unknown_width_source(self):
        text = replace_marked(FIXTURE, "slab1_width_source", 'width_source = "moon_phase"')
        with self.assertRaises(tb.RatesError) as ctx:
            self.compute(1, text=text)
        self.assertIn("moon_phase", str(ctx.exception))

    def test_width_and_width_source_together(self):
        text = insert_before(FIXTURE, "slab1_rate", WIDTH_BLOCK)
        with self.assertRaises(tb.RatesError) as ctx:
            self.compute(1, text=text)
        self.assertIn("both", str(ctx.exception))

    def test_slab_without_rate(self):
        text = drop_block(FIXTURE, "slab2_rate")
        with self.assertRaises(tb.RatesError) as ctx:
            self.compute(1, text=text)
        self.assertIn("'rate'", str(ctx.exception))

    def test_unknown_category(self):
        with self.assertRaises(tb.RatesError) as ctx:
            self.compute(1, category="martian")
        self.assertIn("martian", str(ctx.exception))
        self.assertIn("general, female", ctx.exception.hint)

    def test_apply_slabs_refuses_negative(self):
        slabs = tax.build_slabs(self.rates(), T(100000))
        with self.assertRaises(tb.ValidationError):
            tax.apply_slabs(slabs, T(-1))


# ======================================================================================
# tax.py — rebate
# ======================================================================================


class TestRebate(FixtureCase):
    def test_golden_income_cap_binds(self):
        reb = self.compute(1000000, investment=300000).rebate
        self.assertTrue(reb.claimed)
        self.assertEqual(reb.formula, "min_of_three_caps")
        self.assertEqual(reb.income_cap_percent, Decimal(25))
        self.assertEqual(reb.income_cap_amount, T(250000))
        self.assertEqual(reb.absolute_cap, T(500000))
        self.assertEqual(reb.eligible, T(250000))
        self.assertEqual(reb.rate, Decimal(10))
        self.assertEqual(reb.rebate_computed, T(25000))
        self.assertEqual(reb.rebate, T(25000))
        self.assertFalse(reb.capped_by_gross_tax)
        self.assertEqual(reb.tax_after_rebate, T(127500))

    def test_investment_binds(self):
        reb = self.compute(1000000, investment=100000).rebate
        self.assertEqual(reb.eligible, T(100000))
        self.assertEqual(reb.rebate, T(10000))

    def test_absolute_cap_binds(self):
        # 25% of 40,00,000 = 10,00,000 > absolute cap 5,00,000 < investment 8,00,000
        reb = self.compute(4000000, investment=800000).rebate
        self.assertEqual(reb.income_cap_amount, T(1000000))
        self.assertEqual(reb.eligible, T(500000))
        self.assertEqual(reb.rebate, T(50000))

    def test_rebate_never_exceeds_gross_tax(self):
        # income 1,50,000 -> gross 2,500; eligible = 25% × 1,50,000 = 37,500 -> 3,750 > 2,500
        reb = self.compute(150000, investment=500000).rebate
        self.assertEqual(reb.gross_tax, T(2500))
        self.assertEqual(reb.rebate_computed, T(3750))
        self.assertEqual(reb.rebate, T(2500))
        self.assertTrue(reb.capped_by_gross_tax)
        self.assertEqual(reb.tax_after_rebate, M.zero())

    def test_no_investment_reads_no_rebate_node(self):
        rates = self.rates()
        result = self.compute(1000000, rates=rates)
        self.assertFalse(result.rebate.claimed)
        self.assertEqual(result.rebate.rebate, M.zero())
        self.assertEqual(result.tax_after_rebate, T(152500))
        self.assertFalse(any(e.key.startswith(tax.KEY_REBATE) for e in rates.used()))

    def test_missing_formula_is_refused(self):
        text = replace_marked(FIXTURE, "formula", "formula_note = 'gone'")
        with self.assertRaises(tb.RatesError) as ctx:
            self.compute(1000000, investment=1, text=text)
        self.assertIn("formula", str(ctx.exception))
        self.assertIn("min_of_three_caps", ctx.exception.hint)

    def test_unknown_formula_is_refused(self):
        text = replace_marked(FIXTURE, "formula", 'formula = "flat_percent"')
        with self.assertRaises(tb.RatesError) as ctx:
            self.compute(1000000, investment=1, text=text)
        self.assertIn("flat_percent", str(ctx.exception))
        # ...but only when a rebate is actually claimed
        self.compute(1000000, text=text)


# ======================================================================================
# tax.py — minimum tax
# ======================================================================================


class TestMinimumTax(FixtureCase):
    def test_floor_does_not_bite_when_income_below_threshold(self):
        mt = self.compute(90000).minimum_tax
        self.assertEqual(mt.policy, "taxable_income_above_threshold")
        self.assertEqual(mt.location_floor, T(4000))
        self.assertFalse(mt.location_floor_applies)
        self.assertEqual(mt.floor, M.zero())
        self.assertEqual(mt.tax_after, M.zero())
        self.assertFalse(mt.floor_bites)

    def test_floor_bites_just_above_threshold(self):
        result = self.compute(100001)
        mt = result.minimum_tax
        self.assertTrue(mt.location_floor_applies)
        self.assertEqual(mt.tax_before, M(5))
        self.assertEqual(mt.floor, T(4000))
        self.assertEqual(mt.tax_after, T(4000))
        self.assertEqual(mt.adjustment, M(399995))
        self.assertTrue(mt.floor_bites)
        self.assertEqual(result.total_tax, T(4000))

    def test_location_tier_changes_floor(self):
        mt = self.compute(100001, location="rural").minimum_tax
        self.assertEqual(mt.location_floor, T(2000))
        self.assertEqual(mt.location_label, "গ্রামীণ / Rural")
        self.assertEqual(mt.tax_after, T(2000))

    def test_policy_always(self):
        text = replace_marked(FIXTURE, "applies_when", 'value = "always"')
        mt = self.compute(90000, text=text).minimum_tax
        self.assertEqual(mt.policy, "always")
        self.assertTrue(mt.location_floor_applies)
        self.assertEqual(mt.tax_after, T(4000))

    def test_policy_never(self):
        text = replace_marked(FIXTURE, "applies_when", 'value = "never"')
        rates = self.rates(text)
        mt = self.compute(100001, rates=rates).minimum_tax
        self.assertEqual(mt.policy, "never")
        self.assertIsNone(mt.location_floor)
        self.assertEqual(mt.floor, M.zero())
        self.assertEqual(mt.tax_after, M(5))
        self.assertFalse(any(e.key.startswith(tax.KEY_MINIMUM_TAX_BY_LOCATION) for e in rates.used()))
        with self.assertRaises(tb.RatesError):  # a typo'd tier is still refused
            self.compute(1, location="lunar", text=text)

    def test_invalid_policy_is_refused(self):
        text = replace_marked(FIXTURE, "applies_when", 'value = "sometimes"')
        with self.assertRaises(tb.RatesError):
            self.compute(1, text=text)

    def test_unknown_location(self):
        with self.assertRaises(tb.RatesError) as ctx:
            self.compute(1, location="lunar")
        self.assertIn("lunar", str(ctx.exception))
        self.assertIn("metro, rural", ctx.exception.hint)

    def test_gross_receipts_floor(self):
        # 0.5% of 30,00,000 = 15,000 > metro 4,000 > tax 2,500
        mt = self.compute(150000, gross_receipts=3000000).minimum_tax
        self.assertEqual(mt.receipts_applies_above, T(2000000))
        self.assertEqual(mt.receipts_rate, Decimal("0.5"))
        self.assertEqual(mt.receipts_floor, T(15000))
        self.assertTrue(mt.receipts_floor_applies)
        self.assertEqual(mt.floor, T(15000))
        self.assertEqual(mt.tax_after, T(15000))
        self.assertEqual(mt.adjustment, T(12500))

    def test_gross_receipts_at_or_below_trigger(self):
        mt = self.compute(150000, gross_receipts=2000000).minimum_tax
        self.assertFalse(mt.receipts_floor_applies)
        self.assertIsNone(mt.receipts_floor)
        self.assertIsNone(mt.receipts_rate)
        self.assertEqual(mt.floor, T(4000))
        mt = self.compute(150000, gross_receipts=2000000).minimum_tax
        self.assertEqual(mt.gross_receipts, T(2000000))

    def test_no_receipts_means_not_assessed(self):
        rates = self.rates()
        mt = self.compute(150000, rates=rates).minimum_tax
        self.assertIsNone(mt.gross_receipts)
        self.assertIsNone(mt.receipts_floor)
        self.assertFalse(any("on_gross_receipts" in e.key for e in rates.used()))

    def test_greater_floor_wins(self):
        # rural 2,000 vs receipts 0.5% × 21,00,000 = 10,500
        mt = self.compute(150000, location="rural", gross_receipts=2100000).minimum_tax
        self.assertEqual(mt.floor, T(10500))
        # rural 2,000 vs receipts floor absent (receipts not above trigger)
        mt = self.compute(150000, location="rural", gross_receipts=1).minimum_tax
        self.assertEqual(mt.floor, T(2000))


# ======================================================================================
# tax.py — surcharge
# ======================================================================================


class TestSurcharge(FixtureCase):
    def test_not_assessed_without_net_wealth(self):
        rates = self.rates()
        sc = self.compute(1000000, rates=rates).surcharge
        self.assertFalse(sc.assessed)
        self.assertEqual(sc.surcharge, M.zero())
        self.assertFalse(any(e.key.startswith(tax.KEY_SURCHARGE) for e in rates.used()))

    def test_golden_band_three(self):
        sc = self.compute(1000000, investment=300000, net_wealth=60000000).surcharge
        self.assertTrue(sc.assessed)
        self.assertEqual(sc.band_order, 3)
        self.assertEqual(sc.band_label, "তৃতীয় ধাপ / Band three")
        self.assertEqual(sc.wealth_above, T(50000000))
        self.assertEqual(sc.rate, Decimal(20))
        self.assertEqual(sc.base, "tax_after_minimum")
        self.assertEqual(sc.base_amount, T(127500))
        self.assertEqual(sc.computed, T(25500))
        self.assertEqual(sc.minimum, M.zero())
        self.assertEqual(sc.surcharge, T(25500))
        self.assertFalse(sc.lifted_to_minimum)

    def test_band_boundaries_are_exclusive(self):
        self.assertEqual(self.compute(1000000, net_wealth=10000000).surcharge.band_order, 1)
        self.assertEqual(self.compute(1000000, net_wealth=10000000).surcharge.surcharge, M.zero())
        sc = self.compute(1000000, net_wealth="10000000.01").surcharge
        self.assertEqual(sc.band_order, 2)
        self.assertEqual(sc.surcharge, T(15250))  # 10% of 1,52,500
        self.assertEqual(self.compute(1000000, net_wealth=50000000).surcharge.band_order, 2)
        self.assertEqual(self.compute(1000000, net_wealth=50000001).surcharge.band_order, 3)
        self.assertEqual(self.compute(1000000, net_wealth=0).surcharge.band_order, 1)

    def test_first_band_reads_no_minimum(self):
        sc = self.compute(1000000, net_wealth=1).surcharge
        self.assertTrue(sc.assessed)
        self.assertEqual(sc.computed, M.zero())
        self.assertIsNone(sc.minimum)

    def test_base_switch(self):
        # income 1,00,001: tax after rebate ৳0.05, after minimum ৳4,000; band 2 at 10%
        sc = self.compute(100001, net_wealth=20000000).surcharge
        self.assertEqual(sc.base_amount, T(4000))
        self.assertEqual(sc.surcharge, T(400))
        text = replace_marked(FIXTURE, "surcharge_base", 'value = "tax_after_rebate"')
        sc = self.compute(100001, net_wealth=20000000, text=text).surcharge
        self.assertEqual(sc.base, "tax_after_rebate")
        self.assertEqual(sc.base_amount, M(5))
        self.assertEqual(sc.surcharge, M(1))  # 10% of 5 paisa = 0.5 paisa -> 1 paisa, half up

    def test_minimum_surcharge_lifts_a_small_surcharge(self):
        text = replace_marked(FIXTURE, "surcharge_minimum", "value = 5000")
        sc = self.compute(100001, net_wealth=20000000, text=text).surcharge
        self.assertEqual(sc.computed, T(400))
        self.assertEqual(sc.minimum, T(5000))
        self.assertEqual(sc.surcharge, T(5000))
        self.assertTrue(sc.lifted_to_minimum)
        # a zero surcharge (first band) is not lifted
        sc = self.compute(100001, net_wealth=1, text=text).surcharge
        self.assertEqual(sc.surcharge, M.zero())
        self.assertIsNone(sc.minimum)

    def test_invalid_base_is_refused(self):
        text = replace_marked(FIXTURE, "surcharge_base", 'value = "gross_tax"')
        with self.assertRaises(tb.RatesError):
            self.compute(1, net_wealth=1, text=text)

    def test_first_band_must_start_at_zero(self):
        text = insert_before(FIXTURE, "band1_rate", BAND_WEALTH_BLOCK)
        with self.assertRaises(tb.RatesError) as ctx:
            self.compute(1, net_wealth=1, text=text)
        self.assertIn("start at zero", str(ctx.exception))

    def test_later_band_needs_wealth_above(self):
        text = drop_block(FIXTURE, "band2_wealth_above")
        with self.assertRaises(tb.RatesError) as ctx:
            self.compute(1, net_wealth=1, text=text)
        self.assertIn("wealth_above", str(ctx.exception))

    def test_bands_must_ascend(self):
        text = replace_marked(FIXTURE, "band3_wealth_above_value", "value = 5000000")
        with self.assertRaises(tb.RatesError) as ctx:
            self.compute(1, net_wealth=1, text=text)
        self.assertIn("ascending", str(ctx.exception))

    def test_band_without_rate(self):
        text = drop_block(FIXTURE, "band1_rate")
        with self.assertRaises(tb.RatesError):
            self.compute(1, net_wealth=1, text=text)


# ======================================================================================
# tax.py — the whole computation
# ======================================================================================


class TestComputeIncomeTax(FixtureCase):
    def test_golden_case(self):
        result = self.compute(1000000, investment=300000, net_wealth=60000000, tax_paid=20000)
        self.assertEqual(result.assessment_year, FIXTURE_AY)
        self.assertIn(FIXTURE_NAME, result.rates_source)
        self.assertEqual(result.rates_path, self.path)
        self.assertEqual(result.category_label, "সাধারণ করদাতা / General taxpayer")
        self.assertEqual(result.threshold, T(100000))
        self.assertEqual(result.gross_tax, T(152500))
        self.assertEqual(result.rebate.rebate, T(25000))
        self.assertEqual(result.tax_after_rebate, T(127500))
        self.assertEqual(result.tax_after_minimum, T(127500))
        self.assertEqual(result.surcharge.surcharge, T(25500))
        self.assertEqual(result.total_tax, T(153000))
        self.assertEqual(result.net_payable, T(133000))
        self.assertFalse(result.provisional)
        self.assertEqual(result.caveats, ())
        self.assertEqual(result.warnings, ())
        used = [e.key for e in result.rates_used]
        self.assertEqual(used[0], "income_tax.individual.thresholds.general")
        self.assertIn("income_tax.individual.slabs[4].rate", used)
        self.assertIn("income_tax.individual.surcharge.bands[2].wealth_above", used)
        self.assertTrue(all(e.is_verified for e in result.rates_used))

    def test_refund_position(self):
        result = self.compute(150000, tax_paid=10000)
        self.assertEqual(result.total_tax, T(4000))
        self.assertEqual(result.net_payable, T(-6000))
        self.assertTrue(result.net_payable.is_negative())

    def test_female_category(self):
        result = self.compute(1000000, category="female")
        self.assertEqual(result.threshold, T(150000))
        self.assertEqual(result.gross_tax, T(142500))
        self.assertEqual(result.category_label, "নারী করদাতা / Female taxpayer")

    def test_unverified_rate_makes_result_provisional(self):
        text = replace_marked(FIXTURE, "general_verified", "verified = false")
        result = self.compute(1000000, text=text)
        self.assertTrue(result.provisional)
        self.assertEqual(len(result.caveats), 1)
        self.assertTrue(result.caveats[0].startswith("UNVERIFIED"))
        self.assertIn("income_tax.individual.thresholds.general", result.caveats[0])
        self.assertIn("NBR", result.caveats[0])
        self.assertEqual(result.gross_tax, T(152500))  # the arithmetic is unchanged

    def test_unverified_rate_that_was_not_used_does_not_taint(self):
        text = replace_marked(FIXTURE, "rebate_rate_verified", "verified = false")
        self.assertFalse(self.compute(1000000, text=text).provisional)
        result = self.compute(1000000, investment=1000, text=text)
        self.assertTrue(result.provisional)
        self.assertIn("income_tax.individual.rebate.rate", result.caveats[0])

    def test_placeholder_file_refused_then_provisional_when_allowed(self):
        text = replace_marked(FIXTURE, "file_placeholder", "placeholder = true")
        with self.assertRaises(tb.RatesError) as ctx:
            self.compute(1000000, text=text)
        self.assertEqual(ctx.exception.exit_code, 8)
        result = self.compute(1000000, text=text, allow_placeholders=True)
        self.assertTrue(result.provisional)
        self.assertTrue(result.caveats[0].startswith("PLACEHOLDER FILE"))

    def test_shipped_placeholder_file_refused(self):
        rates = rt.RateSet.from_path(REAL_RATES)
        with self.assertRaises(tb.RatesError):
            tax.compute_income_tax(rates, tax.TaxInputs(income=T(1), category="general", location="other_area"))

    def test_inputs_validation(self):
        with self.assertRaises(tb.ValidationError) as ctx:
            tax.TaxInputs(income=T(-1), category="general", location="metro")
        self.assertEqual(ctx.exception.exit_code, 7)
        self.assertIn("income", ctx.exception.problems[0])
        with self.assertRaises(tb.ValidationError):
            tax.TaxInputs(income=T(1), category="general", location="metro", net_wealth=T(-1))
        with self.assertRaises(tb.ValidationError):
            tax.TaxInputs(income=1000, category="general", location="metro")  # type: ignore[arg-type]
        with self.assertRaises(tb.ValidationError):
            tax.TaxInputs(income=T(1), category="", location="metro")
        inputs = tax.TaxInputs(income=T(1), category="general", location="metro")
        self.assertEqual(inputs.investment, M.zero())
        self.assertIsNone(inputs.net_wealth)

    def test_warnings_and_config_are_carried(self):
        config = tb.Config.from_mapping(
            {"business": {"name": "Test Shop", "name_bn": "টেস্ট শপ", "tin": "123"}}
        )
        result = tax.compute_income_tax(
            self.rates(),
            tax.TaxInputs(income=T(1), category="general", location="metro"),
            config=config,
            warnings=["be careful"],
        )
        self.assertEqual(result.warnings, ("be careful",))
        self.assertEqual(result.business_name, "Test Shop (টেস্ট শপ)")
        self.assertEqual(result.tin, "123")

    def test_available_options(self):
        rates = self.rates()
        self.assertEqual(tax.available_categories(rates), ["general", "female"])
        self.assertEqual(tax.available_locations(rates), ["metro", "rural"])


# ======================================================================================
# tax.py — rendering
# ======================================================================================


_TABLE_ROW = re.compile(r"^\|\s*(\d+)\s*\|")


def _slab_taxes_from_markdown(text: str) -> list[tb.Money]:
    """Read the Tax column of the slab table back out of the rendered Markdown."""
    taxes = []
    for line in text.splitlines():
        if _TABLE_ROW.match(line):
            cells = [c.strip().strip("*") for c in line.strip().strip("|").split("|")]
            if len(cells) == 8:
                taxes.append(M.from_str(cells[7]))
    return taxes


class TestRendering(FixtureCase):
    def test_markdown_has_every_required_element(self):
        result = self.compute(1000000, investment=300000, net_wealth=60000000, tax_paid=20000)
        text = tax.render_markdown(result)
        for needle in (
            f"**{tb.term('assessment_year')}:** {FIXTURE_AY}",
            result.rates_source,
            "Step 1", "Step 2", "Step 3", "Step 4", "Step 5",
            "করমুক্ত আয়সীমা / Tax-free threshold",
            "সর্বোচ্চ ধাপ / Top slab",
            "৳1,52,500.00",   # gross tax, lakh grouping
            "৳25,000.00",     # rebate
            "৳25,500.00",     # surcharge
            "৳1,53,000.00",   # total
            "৳1,33,000.00",   # net payable
            "Net tax payable / নিট প্রদেয় কর",
            "## Rates used / ব্যবহৃত হার",
            "`income_tax.individual.thresholds.general`",
            "## Caveats / সতর্কতা",
            "Every rate used in this computation is marked verified",
            tb.DISCLAIMER_EN,
            tb.ATTRIBUTION,
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)
        self.assertNotIn("PROVISIONAL", text)
        self.assertNotIn(tb.DISCLAIMER_BN, text)
        self.assertTrue(text.rstrip().endswith(tb.ATTRIBUTION))
        # The disclaimer is the last thing before the attribution.
        self.assertGreater(text.index(tb.DISCLAIMER_EN), text.index("## Caveats"))

    def test_slab_rows_in_markdown_sum_to_gross_tax(self):
        result = self.compute("1234567.89", investment=1)
        taxes = _slab_taxes_from_markdown(tax.render_markdown(result))
        self.assertEqual(len(taxes), len(result.slabs))
        self.assertEqual(M.sum(taxes), result.gross_tax)

    def test_bangla_disclaimer_when_asked(self):
        result = self.compute(1)
        self.assertIn(tb.DISCLAIMER_BN, tax.render_markdown(result, language="bn"))
        self.assertIn(tb.DISCLAIMER_BN, tax.render_markdown(result, language="bn-en"))
        with self.assertRaises(ValueError):
            tax.render_markdown(result, language="fr")

    def test_provisional_banner(self):
        text = replace_marked(FIXTURE, "general_verified", "verified = false")
        rendered = tax.render_markdown(self.compute(1000000, text=text))
        self.assertIn("PROVISIONAL / অস্থায়ী", rendered)
        self.assertIn("NOT FOR FILING", rendered)
        self.assertIn("- UNVERIFIED: income_tax.individual.thresholds.general", rendered)
        self.assertIn("| UNVERIFIED |", rendered)

    def test_unassessed_sections_say_so(self):
        rendered = tax.render_markdown(self.compute(150000, tax_paid=10000))
        self.assertIn("No investment was claimed", rendered)
        self.assertIn("Not assessed: no net wealth", rendered)
        self.assertIn("not assessed — no gross receipts", rendered)
        self.assertIn("refundable", rendered)
        self.assertIn("৳6,000.00", rendered)
        self.assertIn("lifted by ৳1,500.00", rendered)

    def test_config_locale_formatting(self):
        config = tb.Config.from_mapping({"locale": {"digits": "bangla"}, "business": {"name": "Shop"}})
        result = tax.compute_income_tax(
            self.rates(), tax.TaxInputs(income=T(1000000), category="general", location="metro"), config=config
        )
        rendered = tax.render_markdown(result, config=config)
        self.assertIn("৳১,৫২,৫০০.০০", rendered)
        self.assertIn("Taxpayer: Shop", rendered)
        intl = tb.Config.from_mapping({"locale": {"grouping": "international"}})
        rendered = tax.render_markdown(result, config=intl)
        self.assertIn("৳152,500.00", rendered)

    def test_json_shape(self):
        result = self.compute(1000000, investment=300000, net_wealth=60000000, tax_paid=20000)
        data = json.loads(tb.json_dumps(tax.to_json_dict(result)))
        self.assertTrue(data["ok"])
        self.assertEqual(data["assessment_year"], FIXTURE_AY)
        self.assertFalse(data["provisional"])
        self.assertEqual(data["currency"], "BDT")
        self.assertEqual(data["rates_file"], str(self.path))
        self.assertEqual(data["gross_tax"], "152500.00")
        self.assertEqual(data["rebate"]["rebate"], "25000.00")
        self.assertEqual(data["minimum_tax"]["floor"], "4000.00")
        self.assertEqual(data["surcharge"]["surcharge"], "25500.00")
        self.assertEqual(data["summary"]["total_tax"], "153000.00")
        self.assertEqual(data["summary"]["net_payable"], "133000.00")
        self.assertEqual(data["summary"]["refundable"], "0.00")
        self.assertEqual(len(data["slabs"]), 5)
        self.assertEqual(data["slabs"][4]["to"], None)
        self.assertTrue(data["slabs"][4]["open_ended"])
        self.assertEqual(data["slabs"][1]["rate_percent"], "5")
        self.assertEqual(data["threshold"]["amount"], "100000.00")
        self.assertEqual(data["inputs"]["category_label"], "সাধারণ করদাতা / General taxpayer")
        self.assertEqual(data["disclaimer"]["en"], tb.DISCLAIMER_EN)
        self.assertEqual(data["disclaimer"]["bn"], tb.DISCLAIMER_BN)
        self.assertEqual(data["attribution"], tb.ATTRIBUTION)
        self.assertEqual(data["caveats"], [])
        self.assertEqual(len(data["rates_used"]), len(result.rates_used))
        self.assertTrue(all(e["verified"] for e in data["rates_used"]))

    def test_json_refund_and_unassessed(self):
        data = json.loads(tb.json_dumps(tax.to_json_dict(self.compute(150000, tax_paid=10000))))
        self.assertEqual(data["summary"]["net_payable"], "-6000.00")
        self.assertEqual(data["summary"]["refundable"], "6000.00")
        self.assertFalse(data["surcharge"]["assessed"])
        self.assertIsNone(data["inputs"]["net_wealth"])
        self.assertFalse(data["rebate"]["claimed"])


# ======================================================================================
# tax.py — command line
# ======================================================================================


class TestTaxCli(FixtureCase):
    def cli(self, *args: str) -> subprocess.CompletedProcess:
        return run_cli("tax.py", "--books", str(self.root / "nobooks"), *args, cwd=self.root)

    def test_help_and_version(self):
        result = self.cli("--help")
        self.assertEqual(result.returncode, 0)
        for flag in ("--income", "--investment", "--net-wealth", "--gross-receipts", "--tax-paid",
                     "--category", "--location", "--assessment-year", "--rates", "--json",
                     "--allow-placeholder-rates", "--strict", "--list-options", "--books"):
            self.assertIn(flag, result.stdout)
        self.assertIn(tb.ATTRIBUTION, result.stdout)
        result = self.cli("--version")
        self.assertEqual(result.returncode, 0)
        self.assertIn(tb.__version__, result.stdout)

    def test_golden_markdown(self):
        result = self.cli("--rates", str(self.path), "--income", "10,00,000", "--investment", "300000",
                          "--net-wealth", "6,00,00,000", "--tax-paid", "20000")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("৳1,33,000.00", result.stdout)
        self.assertIn(FIXTURE_AY, result.stdout)
        self.assertIn(tb.DISCLAIMER_EN, result.stdout)
        self.assertNotIn("PROVISIONAL", result.stdout)

    def test_golden_json(self):
        result = self.cli("--rates", str(self.path), "--income", "1000000", "--investment", "300000",
                          "--net-wealth", "60000000", "--tax-paid", "20000", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["summary"]["net_payable"], "133000.00")
        self.assertEqual(data["assessment_year"], FIXTURE_AY)

    def test_year_selects_file_from_data_dir(self):
        self.write_fixture(FIXTURE.replace(FIXTURE_AY, "2032-33"), name="rates-AY2032-33.toml")
        result = self.cli("--data-dir", str(self.data_dir), "--assessment-year", "2032-33",
                          "--income", "1000000", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["assessment_year"], "2032-33")
        result = self.cli("--data-dir", str(self.data_dir), "--income", "1000000")
        self.assertEqual(result.returncode, 8)
        self.assertIn("name the assessment year", result.stderr)

    def test_missing_income(self):
        result = self.cli("--rates", str(self.path))
        self.assertEqual(result.returncode, 2)
        self.assertIn("--income is required", result.stderr)

    def test_bad_amounts_exit_non_zero(self):
        result = self.cli("--rates", str(self.path), "--income", "-5")
        self.assertEqual(result.returncode, 7)
        self.assertIn("cannot be negative", result.stderr)
        result = self.cli("--rates", str(self.path), "--income", "abc")
        self.assertEqual(result.returncode, 7)
        self.assertIn("--income", result.stderr)
        self.assertNotIn("--income: --income", result.stderr)
        result = self.cli("--rates", str(self.path), "--income", "1", "--net-wealth", "1.5.2")
        self.assertEqual(result.returncode, 7)

    def test_unknown_category_exit_code(self):
        result = self.cli("--rates", str(self.path), "--income", "1", "--category", "martian", "--json")
        self.assertEqual(result.returncode, 8)
        payload = json.loads(result.stderr)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"], "RatesError")
        self.assertIn("general, female", payload["hint"])

    def test_shipped_mixed_file_computes_from_landed_nodes(self):
        """The shipped file is mixed, so a plain slab computation must succeed."""
        result = self.cli("--rates", str(REAL_RATES), "--income", "500000", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["assessment_year"], "2026-27")
        self.assertFalse(data["placeholder_data_used"])
        self.assertEqual(data["placeholder_figures_used"], [])
        self.assertNotEqual(data["data_grade"], tax.GRADE_PLACEHOLDER)
        self.assertFalse(any(e["placeholder"] for e in data["rates_used"]))

    def test_shipped_file_refuses_a_working_that_needs_an_unlanded_figure(self):
        placeholders = [
            key
            for key in rt.RateSet.from_path(REAL_RATES, allow_placeholders=True)
            .audit()["placeholder"]
            if key.startswith("income_tax.individual.")
        ]
        if not placeholders:
            self.skipTest("every individual income-tax figure has landed")
        args = ("--rates", str(REAL_RATES), "--income", "500000",
                "--gross-receipts", "5000000")
        result = self.cli(*args)
        self.assertEqual(result.returncode, 8, result.stdout)
        self.assertEqual(result.stdout, "")
        self.assertIn("placeholder", result.stderr)
        self.assertIn("--allow-placeholder-rates", result.stderr)

        result = self.cli(*args, "--allow-placeholder-rates")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(tax.STATUS_PLACEHOLDER, result.stdout)
        self.assertIn("PLACEHOLDER DATA", result.stdout)
        self.assertIn("NOT FOR FILING", result.stdout)
        self.assertIn("2026-27", result.stdout)
        self.assertIn(tb.DISCLAIMER_EN, result.stdout)

        result = self.cli(*args, "--allow-placeholder-rates", "--json")
        data = json.loads(result.stdout)
        self.assertTrue(data["provisional"])
        self.assertTrue(data["placeholder_data_used"])
        self.assertEqual(data["data_grade"], tax.GRADE_PLACEHOLDER)
        self.assertEqual(data["filing_status"], tax.STATUS_PLACEHOLDER)
        self.assertTrue(data["placeholder_figures_used"])
        self.assertTrue(any(c.startswith("PLACEHOLDER") for c in data["caveats"]))

        # Opting in never makes the answer fileable: --strict still refuses it.
        result = self.cli(*args, "--allow-placeholder-rates", "--strict")
        self.assertEqual(result.returncode, 7)
        self.assertIn("not ready to file", result.stderr)

    def test_strict_refuses_an_unverified_figure_and_passes_on_a_verified_one(self):
        result = self.cli("--rates", str(self.path), "--income", "1000000",
                          "--investment", "300000", "--strict")
        self.assertEqual(result.returncode, 0, result.stderr)   # fixture is all verified
        text = replace_marked(FIXTURE, "general_verified", "verified = false")
        variant = self.write_fixture(text, name="unverified.toml")
        result = self.cli("--rates", str(variant), "--income", "1000000", "--strict")
        self.assertEqual(result.returncode, 7)
        self.assertIn("not ready to file", result.stderr)
        self.assertIn("UNVERIFIED", result.stderr)
        self.assertIn("income_tax.individual.thresholds.general", result.stderr)
        # Without --strict the same run still produces the working, marked PROVISIONAL.
        result = self.cli("--rates", str(variant), "--income", "1000000")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PROVISIONAL", result.stdout)
        self.assertNotIn("PLACEHOLDER DATA", result.stdout)

    def test_list_options(self):
        result = self.cli("--rates", str(self.path), "--list-options")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("general", result.stdout)
        self.assertIn("নারী করদাতা / Female taxpayer", result.stdout)
        self.assertIn("rural", result.stdout)
        self.assertIn("--category general --location metro", result.stdout)
        result = self.cli("--rates", str(self.path), "--list-options", "--json")
        data = json.loads(result.stdout)
        self.assertEqual([c["id"] for c in data["categories"]], ["general", "female"])
        self.assertEqual([c["id"] for c in data["locations"]], ["metro", "rural"])
        self.assertEqual(data["default_category"], "general")
        # Listing must work on the placeholder file too, without the opt-in flag.
        result = self.cli("--rates", str(REAL_RATES), "--list-options")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("general", result.stdout)

    def test_default_category_missing_is_refused(self):
        text = replace_marked(FIXTURE, "default_category", "")
        path = self.write_fixture(text, name="variant.toml")
        result = self.cli("--rates", str(path), "--income", "1")
        self.assertEqual(result.returncode, 8)
        self.assertIn("--category", result.stderr)
        result = self.cli("--rates", str(path), "--income", "1", "--category", "female", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_language_flag(self):
        result = self.cli("--rates", str(self.path), "--income", "1", "--language", "bn")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(tb.DISCLAIMER_BN, result.stdout)
        result = self.cli("--rates", str(self.path), "--income", "1")
        self.assertNotIn(tb.DISCLAIMER_BN, result.stdout)


class TestTaxCliWithBooks(FixtureCase):
    """config.toml supplies the assessment year, rates file, locale and taxpayer name."""

    def setUp(self):
        super().setUp()
        self.books = self.root / "books"
        self.books.mkdir()
        self.write_fixture(FIXTURE, directory=self.books)

    def write_config(self, body: str) -> None:
        (self.books / "config.toml").write_text(body, encoding="utf-8")

    def cli(self, *args: str) -> subprocess.CompletedProcess:
        return run_cli("tax.py", "--books", str(self.books), *args, cwd=self.root)

    def test_config_drives_everything(self):
        self.write_config(
            '[business]\nname = "Test Shop"\ntin = "123456789012"\n'
            f'[books]\nassessment_year = "{FIXTURE_AY}"\nrates_file = "{FIXTURE_NAME}"\n'
            '[locale]\nlanguage = "bn-en"\n'
        )
        result = self.cli("--income", "1000000")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Taxpayer: Test Shop · TIN 123456789012", result.stdout)
        self.assertIn(tb.DISCLAIMER_BN, result.stdout)
        self.assertIn("৳1,52,500.00", result.stdout)
        self.assertNotIn("WARNING", result.stdout)

    def test_config_year_finds_file_in_data_dir(self):
        self.write_config(f'[books]\nassessment_year = "{FIXTURE_AY}"\n')
        result = self.cli("--data-dir", str(self.data_dir), "--income", "1000000", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["rates_file"], str(self.path))

    def test_year_mismatch_is_an_error_unless_explicit(self):
        self.write_config(f'[books]\nassessment_year = "2030-31"\nrates_file = "{FIXTURE_NAME}"\n')
        result = self.cli("--income", "1000000")
        self.assertEqual(result.returncode, 8)
        self.assertIn("2030-31", result.stderr)
        self.assertIn(FIXTURE_AY, result.stderr)
        result = self.cli("--income", "1000000", "--rates", str(self.path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("WARNING", result.stdout)
        self.assertIn("2030-31", result.stdout)
        result = self.cli("--income", "1000000", "--rates", str(self.path), "--json")
        self.assertEqual(len(json.loads(result.stdout)["warnings"]), 1)

    def test_broken_config_is_not_ignored(self):
        self.write_config('[books]\ncurrency = "USD"\n')
        result = self.cli("--rates", str(self.path), "--income", "1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("BDT", result.stderr)

    def test_no_config_is_fine(self):
        (self.books / "config.toml").unlink(missing_ok=True)
        result = self.cli("--rates", str(self.path), "--income", "1", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)


# ======================================================================================
# Module hygiene
# ======================================================================================


class TestModuleHygiene(unittest.TestCase):
    def test_public_names_exist(self):
        for module in (tax, rt):
            for name in module.__all__:
                with self.subTest(module=module.__name__, name=name):
                    self.assertTrue(hasattr(module, name), name)

    def _tokens(self, path: Path):
        source = path.read_text(encoding="utf-8")
        return list(tokenize.generate_tokens(io.StringIO(source).readline))

    def test_no_float_call_or_literal_in_tax_or_rates(self):
        for name in ("tax.py", "rates.py"):
            tokens = self._tokens(ENGINE_DIR / name)
            for index, token in enumerate(tokens):
                if token.type == tokenize.NAME and token.string == "float":
                    following = tokens[index + 1].string if index + 1 < len(tokens) else ""
                    self.assertNotEqual(following, "(", f"{name} line {token.start[0]} calls float()")
                if token.type == tokenize.NUMBER:
                    self.assertNotIn(".", token.string, f"{name} line {token.start[0]} has a float literal")

    def test_tax_py_hardcodes_no_figure(self):
        """No integer literal above 100 exists in tax.py — every threshold, slab and band
        must come from the rates file."""
        for token in self._tokens(ENGINE_DIR / "tax.py"):
            if token.type == tokenize.NUMBER:
                self.assertLessEqual(int(token.string), 100, f"tax.py line {token.start[0]}: {token.string}")

    def test_engine_uses_the_shared_library_disclaimer(self):
        source = (ENGINE_DIR / "tax.py").read_text(encoding="utf-8")
        self.assertIn("DISCLAIMER_EN", source)
        self.assertIn("DISCLAIMER_BN", source)
        self.assertIn("ATTRIBUTION", source)


# ======================================================================================
# Posture symmetry — the tax.py half
#
# tests/test_vat.py::TestEnginePostureSymmetry holds the cross-engine matrix; these are
# the per-figure assertions that belong with tax.py's own fixture.
# ======================================================================================


class TestEnginePostureSymmetry(FixtureCase):
    """A tool must not compute a Bangladeshi figure from unlanded data unasked."""

    def test_shares_the_verification_vocabulary_with_vat(self):
        for name in ("ALLOW_PLACEHOLDERS_FLAG", "GRADE_FINAL", "GRADE_UNVERIFIED",
                     "GRADE_PLACEHOLDER", "STATUS_PLACEHOLDER", "STATUS_PROVISIONAL",
                     "PLACEHOLDER_STATUS_TEXT"):
            with self.subTest(constant=name):
                self.assertEqual(getattr(tax, name), getattr(vat, name), name)

    def test_placeholder_node_refused_the_moment_the_working_needs_it(self):
        """Per figure, not per file: the file opens, the working stops at the node."""
        text = FIXTURE.replace(
            "verified = true  # MARK:general_verified",
            "verified = false\nplaceholder = true",
        )
        rates = self.rates(text)                      # [meta] placeholder is still false
        tax.require_landed_rates(rates)               # so the FILE is perfectly readable
        self.assertFalse(tax.rates_file_is_placeholder(rates))
        with self.assertRaises(tb.RatesError) as ctx:
            self.compute(1000000, rates=rates)
        self.assertIn("income_tax.individual.thresholds.general", str(ctx.exception))
        self.assertIn("--allow-placeholder-rates", ctx.exception.hint)

    def test_opting_in_computes_but_stamps_the_answer_placeholder(self):
        text = FIXTURE.replace(
            "verified = true  # MARK:general_verified",
            "verified = false\nplaceholder = true",
        )
        result = self.compute(1000000, text=text, allow_placeholders=True)
        self.assertTrue(result.placeholder_data_used)
        self.assertEqual(result.data_grade, tax.GRADE_PLACEHOLDER)
        self.assertEqual(result.filing_status, tax.STATUS_PLACEHOLDER)
        self.assertEqual(
            result.placeholder_figures, ("income_tax.individual.thresholds.general",)
        )
        markdown = tax.render_markdown(result)
        self.assertIn("PLACEHOLDER DATA / অস্থায়ী উপাত্ত — NOT FOR FILING", markdown)
        self.assertIn("income_tax.individual.thresholds.general", markdown)
        self.assertIn(tax.STATUS_PLACEHOLDER, markdown)
        self.assertTrue(result.blocking_problems())

    def test_unverified_computes_and_is_only_provisional(self):
        """Unverified is a caveat, not a refusal — a landed figure is still a figure."""
        text = replace_marked(FIXTURE, "general_verified", "verified = false")
        result = self.compute(1000000, text=text)
        self.assertTrue(result.provisional)
        self.assertFalse(result.placeholder_data_used)
        self.assertEqual(result.data_grade, tax.GRADE_UNVERIFIED)
        self.assertEqual(result.filing_status, tax.STATUS_PROVISIONAL)
        markdown = tax.render_markdown(result)
        self.assertIn("PROVISIONAL / অস্থায়ী — NOT FOR FILING", markdown)
        self.assertNotIn("PLACEHOLDER DATA", markdown)

    def test_a_fully_verified_file_is_graded_final(self):
        result = self.compute(1000000)
        self.assertFalse(result.provisional)
        self.assertFalse(result.placeholder_data_used)
        self.assertEqual(result.data_grade, tax.GRADE_FINAL)
        self.assertEqual(result.filing_status, tax.STATUS_VERIFIED)
        self.assertEqual(result.blocking_problems(), ())
        self.assertNotIn("PROVISIONAL", tax.render_markdown(result))

    def test_file_level_gate_matches_vat_on_the_fixture_variants(self):
        for label, text in (
            ("landed", FIXTURE),
            ("flagged", replace_marked(FIXTURE, "file_placeholder", "placeholder = true")),
            ("status only", replace_marked(
                FIXTURE, "file_placeholder", 'status = "placeholder"')),
        ):
            with self.subTest(shape=label):
                path = self.write_fixture(text, name=f"{label.replace(' ', '-')}.toml")
                rate_set = rt.RateSet.from_path(path, allow_placeholders=True)
                self.assertEqual(
                    tax.rates_file_is_placeholder(rate_set),
                    vat.rates_file_is_placeholder(rate_set),
                    label,
                )


if __name__ == "__main__":
    unittest.main()
