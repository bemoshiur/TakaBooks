"""Tests for the TakaBooks shared library (``src/engine/takabooks.py``).

Run with::

    python3 -m unittest discover tests

Emphasis, per spec §7: money arithmetic (int paisa, never float, ROUND_HALF_UP),
লাখ/কোটি lakh-crore formatting edge cases, the ``tax_tag`` grammar, and the
double-entry invariant — an unbalanced entry must fail loudly and name itself.

TakaBooks — Moshiur Rahman (@bemoshiur) · Ticon Sys — https://ticonsys.com
"""

from __future__ import annotations

import datetime
import io
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = REPO_ROOT / "src" / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import takabooks as tb  # noqa: E402

M = tb.Money


# ======================================================================================
# Python version guard
# ======================================================================================


class TestPythonGuard(unittest.TestCase):
    def test_floor_is_3_11(self):
        self.assertEqual(tb.MIN_PYTHON, (3, 11))

    def test_running_interpreter_passes(self):
        tb.require_python()  # must not raise on a supported interpreter

    def test_too_old_raises_with_friendly_message(self):
        with self.assertRaises(tb.PythonVersionError) as ctx:
            tb.require_python((99, 0))
        message = str(ctx.exception)
        self.assertIn("99.0", message)
        self.assertIn("tomllib", message)
        self.assertEqual(ctx.exception.exit_code, 2)

    def test_message_helper_mentions_download_page(self):
        self.assertIn("python.org", tb.python_version_message((3, 11), (3, 10, 0)))


# ======================================================================================
# Exception hierarchy
# ======================================================================================


class TestExceptions(unittest.TestCase):
    def test_everything_derives_from_the_base(self):
        for cls in (
            tb.ConfigError,
            tb.MoneyError,
            tb.AccountError,
            tb.DuplicateAccountError,
            tb.UnknownAccountError,
            tb.JournalError,
            tb.TaxTagError,
            tb.DuplicateEntryError,
            tb.BalanceError,
            tb.LedgerError,
            tb.RatesError,
            tb.ValidationError,
            tb.PythonVersionError,
        ):
            self.assertTrue(issubclass(cls, tb.TakaBooksError), cls)

    def test_exit_codes_are_non_zero(self):
        for cls in (
            tb.TakaBooksError,
            tb.ConfigError,
            tb.MoneyError,
            tb.AccountError,
            tb.JournalError,
            tb.TaxTagError,
            tb.BalanceError,
            tb.LedgerError,
            tb.RatesError,
            tb.ValidationError,
        ):
            self.assertGreater(cls.exit_code, 0, cls)

    def test_specialisations(self):
        self.assertTrue(issubclass(tb.TaxTagError, tb.JournalError))
        self.assertTrue(issubclass(tb.BalanceError, tb.JournalError))
        self.assertTrue(issubclass(tb.UnknownAccountError, tb.AccountError))

    def test_hint_is_shown(self):
        exc = tb.ConfigError("broken", hint="do this instead")
        self.assertIn("do this instead", str(exc))
        self.assertEqual(exc.message, "broken")


# ======================================================================================
# Money — construction and parsing
# ======================================================================================


class TestMoneyParsing(unittest.TestCase):
    def test_paisa_is_the_internal_unit(self):
        self.assertEqual(M.from_str("1.00").paisa, 100)
        self.assertEqual(M.from_str("1234.56").paisa, 123456)
        self.assertEqual(tb.PAISA_PER_TAKA, 100)

    def test_zero(self):
        self.assertEqual(M.zero().paisa, 0)
        self.assertTrue(M.zero().is_zero())
        self.assertFalse(M.zero())

    def test_from_paisa_and_from_taka(self):
        self.assertEqual(M.from_paisa(4200), M.from_str("42.00"))
        self.assertEqual(M.from_taka(42), M.from_str("42"))
        self.assertEqual(M.from_taka(Decimal("42.5")), M.from_str("42.50"))
        self.assertEqual(M.from_taka("42.50"), M.from_str("42.5"))

    def test_grouping_separators_are_accepted_both_ways(self):
        self.assertEqual(M.from_str("12,34,567.89"), M.from_str("1234567.89"))
        self.assertEqual(M.from_str("1,234,567.89"), M.from_str("1234567.89"))

    def test_currency_noise_is_stripped(self):
        for text in ("৳1234.56", "৳ 1,234.56", "BDT 1234.56", "Tk. 1234.56", "1234.56 taka"):
            self.assertEqual(M.from_str(text), M.from_str("1234.56"), text)

    def test_bangla_digits_parse(self):
        self.assertEqual(M.from_str("১২৩৪.৫৬"), M.from_str("1234.56"))
        self.assertEqual(M.from_str("১,০০,০০০.০০"), M.from_str("100000"))

    def test_parentheses_mean_negative(self):
        self.assertEqual(M.from_str("(500.00)"), M.from_str("-500.00"))
        self.assertEqual(M.from_str("(৳1,00,000)"), M.from_str("-100000"))

    def test_signs(self):
        self.assertEqual(M.from_str("+12.34").paisa, 1234)
        self.assertEqual(M.from_str("-12.34").paisa, -1234)

    def test_leading_and_trailing_dot_forms(self):
        self.assertEqual(M.from_str(".50").paisa, 50)
        self.assertEqual(M.from_str("50.").paisa, 5000)

    def test_blank_and_garbage_are_rejected(self):
        for text in ("", "   ", "abc", "1.2.3", "12-34", "১২ক", "--5"):
            with self.assertRaises(tb.MoneyError, msg=text):
                M.from_str(text)

    def test_error_message_names_the_value(self):
        with self.assertRaises(tb.MoneyError) as ctx:
            M.from_str("abc", what="debit")
        self.assertIn("debit", ctx.exception.message)
        self.assertIn("abc", ctx.exception.message)


class TestMoneyRejectsFloat(unittest.TestCase):
    """Rule: money never touches float (spec §4.2)."""

    def test_constructor_rejects_float(self):
        with self.assertRaises(tb.MoneyError):
            M(12.34)

    def test_from_taka_rejects_float(self):
        with self.assertRaises(tb.MoneyError):
            M.from_taka(12.34)

    def test_from_decimal_rejects_float(self):
        with self.assertRaises(tb.MoneyError):
            M.from_decimal(0.1)  # type: ignore[arg-type]

    def test_mul_rate_rejects_float(self):
        with self.assertRaises(tb.MoneyError):
            M.from_str("100").mul_rate(0.15)  # type: ignore[arg-type]

    def test_percent_rejects_float(self):
        with self.assertRaises(tb.MoneyError):
            M.from_str("100").percent(15.0)  # type: ignore[arg-type]

    def test_multiplication_by_float_is_refused_with_guidance(self):
        with self.assertRaises(tb.MoneyError) as ctx:
            M.from_str("100") * 0.15  # type: ignore[operator]
        self.assertIn("mul_rate", ctx.exception.hint or "")

    def test_bool_is_not_a_number_of_paisa(self):
        with self.assertRaises(tb.MoneyError):
            M(True)  # type: ignore[arg-type]

    def test_format_bdt_rejects_float(self):
        with self.assertRaises(tb.MoneyError):
            tb.format_bdt(1234.56)  # type: ignore[arg-type]

    def test_source_file_never_calls_float(self):
        """Tokenise the engine and prove no `float(...)` call exists in real code."""
        import tokenize

        calls = []
        with tokenize.open(ENGINE_DIR / "takabooks.py") as handle:
            previous = None
            for token in tokenize.generate_tokens(handle.readline):
                if (
                    previous is not None
                    and previous.type == tokenize.NAME
                    and previous.string == "float"
                    and token.type == tokenize.OP
                    and token.string == "("
                ):
                    calls.append(previous.start[0])
                if token.type not in (tokenize.NL, tokenize.NEWLINE, tokenize.COMMENT):
                    previous = token
        self.assertEqual(calls, [], "the engine must never call float()")

    def test_source_file_never_converts_money_through_float(self):
        source = (ENGINE_DIR / "takabooks.py").read_text(encoding="utf-8")
        self.assertNotIn("round(", source)
        self.assertNotIn("math.", source)


class TestMoneyRounding(unittest.TestCase):
    """ROUND_HALF_UP, applied once, at the final step (spec §4.2)."""

    def test_half_rounds_up_away_from_zero(self):
        self.assertEqual(M.from_str("0.005").paisa, 1)
        self.assertEqual(M.from_str("0.015").paisa, 2)
        self.assertEqual(M.from_str("-0.005").paisa, -1)

    def test_below_half_rounds_down(self):
        self.assertEqual(M.from_str("0.004").paisa, 0)
        self.assertEqual(M.from_str("-0.004").paisa, 0)

    def test_exact_mode_refuses_to_round(self):
        with self.assertRaises(tb.MoneyError) as ctx:
            M.from_str("0.005", exact=True)
        self.assertIn("sub-paisa", ctx.exception.message)
        self.assertEqual(M.from_str("0.05", exact=True).paisa, 5)

    def test_banker_rounding_is_not_used(self):
        # 2.5 paisa must become 3, not 2 (ROUND_HALF_EVEN would give 2).
        self.assertEqual(M.from_str("0.025").paisa, 3)

    def test_percent_rounds_once(self):
        # 15% of 1234.56 = 185.184 -> 185.18
        self.assertEqual(M.from_str("1234.56").percent(15), M.from_str("185.18"))
        # 15% of 1000.10 = 150.015 -> 150.02 (half up)
        self.assertEqual(M.from_str("1000.10").percent(15), M.from_str("150.02"))

    def test_mul_rate_matches_percent(self):
        base = M.from_str("98765.43")
        self.assertEqual(base.percent(Decimal("7.5")), base.mul_rate(Decimal("0.075")))


class TestMoneyArithmetic(unittest.TestCase):
    def test_add_and_subtract(self):
        self.assertEqual(M.from_str("10.50") + M.from_str("0.50"), M.from_str("11.00"))
        self.assertEqual(M.from_str("10.00") - M.from_str("12.50"), M.from_str("-2.50"))

    def test_no_precision_loss_over_many_additions(self):
        total = M.zero()
        for _ in range(1000):
            total = total + M.from_str("0.10")
        self.assertEqual(total, M.from_str("100.00"))
        self.assertEqual(total.paisa, 10000)

    def test_unary_operators(self):
        self.assertEqual(-M.from_str("5.00"), M.from_str("-5.00"))
        self.assertEqual(abs(M.from_str("-5.00")), M.from_str("5.00"))
        self.assertEqual(+M.from_str("5.00"), M.from_str("5.00"))

    def test_adding_a_non_money_is_refused(self):
        with self.assertRaises(TypeError):
            M.from_str("1.00") + 1  # type: ignore[operator]
        with self.assertRaises(TypeError):
            M.from_str("1.00") - Decimal("1")  # type: ignore[operator]

    def test_multiplication_by_whole_numbers(self):
        self.assertEqual(M.from_str("12.50") * 4, M.from_str("50.00"))
        self.assertEqual(3 * M.from_str("0.33"), M.from_str("0.99"))

    def test_divide(self):
        self.assertEqual(M.from_str("100.00").divide(3), M.from_str("33.33"))
        self.assertEqual(M.from_str("100.00").divide(8), M.from_str("12.50"))
        with self.assertRaises(tb.MoneyError):
            M.from_str("1.00").divide(0)

    def test_comparisons_and_sorting(self):
        self.assertTrue(M.from_str("1.00") < M.from_str("2.00"))
        self.assertTrue(M.from_str("-1.00") < M.zero())
        self.assertEqual(
            sorted([M.from_str("3"), M.from_str("1"), M.from_str("2")]),
            [M.from_str("1"), M.from_str("2"), M.from_str("3")],
        )

    def test_hashable_and_equal_by_value(self):
        self.assertEqual(len({M.from_str("1.00"), M.from_paisa(100)}), 1)

    def test_sum(self):
        self.assertEqual(
            M.sum([M.from_str("1.11"), M.from_str("2.22"), M.from_str("3.33")]),
            M.from_str("6.66"),
        )
        self.assertEqual(M.sum([]), M.zero())
        self.assertEqual(tb.money_sum([M.from_str("1.00")]), M.from_str("1.00"))
        with self.assertRaises(tb.MoneyError):
            M.sum([1, 2])  # type: ignore[list-item]

    def test_ratio_to(self):
        self.assertEqual(M.from_str("50").ratio_to(M.from_str("200")), Decimal("0.25"))
        with self.assertRaises(tb.MoneyError):
            M.from_str("1").ratio_to(M.zero())

    def test_to_decimal_is_exact_two_places(self):
        self.assertEqual(M.from_str("1234.5").to_decimal(), Decimal("1234.50"))
        self.assertEqual(M.from_paisa(1).taka, Decimal("0.01"))

    def test_str_is_csv_safe_and_repr_is_paisa(self):
        self.assertEqual(str(M.from_str("12,34,567.89")), "1234567.89")
        self.assertEqual(repr(M.from_paisa(5)), "Money(paisa=5)")


class TestMoneyAllocation(unittest.TestCase):
    def test_split_preserves_the_total(self):
        parts = M.from_str("100.00").split(3)
        self.assertEqual(M.sum(parts), M.from_str("100.00"))
        self.assertEqual([p.paisa for p in parts], [3334, 3333, 3333])

    def test_split_of_a_negative_amount(self):
        parts = M.from_str("-100.00").split(3)
        self.assertEqual(M.sum(parts), M.from_str("-100.00"))
        self.assertEqual([p.paisa for p in parts], [-3334, -3333, -3333])

    def test_allocate_by_weights(self):
        parts = M.from_str("100.00").allocate([1, 1, 2])
        self.assertEqual(M.sum(parts), M.from_str("100.00"))
        self.assertEqual([p.paisa for p in parts], [2500, 2500, 5000])

    def test_allocate_remainder_goes_to_earliest_weight(self):
        parts = M.from_str("0.10").allocate([1, 1, 1])
        self.assertEqual([p.paisa for p in parts], [4, 3, 3])

    def test_allocate_rejects_bad_weights(self):
        with self.assertRaises(tb.MoneyError):
            M.from_str("1").allocate([])
        with self.assertRaises(tb.MoneyError):
            M.from_str("1").allocate([0, 0])
        with self.assertRaises(tb.MoneyError):
            M.from_str("1").allocate([-1, 2])
        with self.assertRaises(tb.MoneyError):
            M.from_str("1").allocate([1.5])  # type: ignore[list-item]

    def test_split_needs_a_positive_count(self):
        with self.assertRaises(tb.MoneyError):
            M.from_str("1").split(0)


# ======================================================================================
# Bangladeshi lakh/crore formatting — the bug farm
# ======================================================================================


class TestFormatBDT(unittest.TestCase):
    def fmt(self, text, **kwargs):
        return tb.format_bdt(M.from_str(text), **kwargs)

    def test_default_is_bangladeshi_grouping(self):
        self.assertEqual(self.fmt("1234567.89"), "12,34,567.89")

    def test_zero(self):
        self.assertEqual(self.fmt("0"), "0.00")
        self.assertEqual(self.fmt("0", symbol=True), "৳0.00")

    def test_small_amounts_are_ungrouped(self):
        self.assertEqual(self.fmt("1"), "1.00")
        self.assertEqual(self.fmt("99.99"), "99.99")
        self.assertEqual(self.fmt("999.99"), "999.99")

    def test_thousand_boundary(self):
        self.assertEqual(self.fmt("999"), "999.00")
        self.assertEqual(self.fmt("1000"), "1,000.00")
        self.assertEqual(self.fmt("99999"), "99,999.00")

    def test_exactly_one_lakh(self):
        self.assertEqual(self.fmt("100000"), "1,00,000.00")
        self.assertEqual(self.fmt("99999.99"), "99,999.99")
        self.assertEqual(self.fmt("100000.01"), "1,00,000.01")

    def test_lakh_range(self):
        self.assertEqual(self.fmt("123456"), "1,23,456.00")
        self.assertEqual(self.fmt("999999"), "9,99,999.00")
        self.assertEqual(self.fmt("1000000"), "10,00,000.00")
        self.assertEqual(self.fmt("9999999"), "99,99,999.00")

    def test_crore_boundaries(self):
        self.assertEqual(self.fmt("10000000"), "1,00,00,000.00")
        self.assertEqual(self.fmt("12345678"), "1,23,45,678.00")
        self.assertEqual(self.fmt("100000000"), "10,00,00,000.00")
        self.assertEqual(self.fmt("1000000000"), "1,00,00,00,000.00")
        self.assertEqual(self.fmt("123456789012"), "1,23,45,67,89,012.00")

    def test_negatives(self):
        self.assertEqual(self.fmt("-1"), "-1.00")
        self.assertEqual(self.fmt("-100000"), "-1,00,000.00")
        self.assertEqual(self.fmt("-1234567.89"), "-12,34,567.89")
        self.assertEqual(self.fmt("-100000", symbol=True), "-৳1,00,000.00")

    def test_negative_zero_never_printed(self):
        self.assertEqual(tb.format_bdt(M.from_paisa(-40), decimals=0), "0")
        self.assertEqual(tb.format_bdt(M.from_paisa(0)), "0.00")
        self.assertEqual(tb.format_bdt(M.from_paisa(-0)), "0.00")

    def test_parentheses_for_negatives(self):
        self.assertEqual(self.fmt("-500", parens_negative=True), "(500.00)")
        self.assertEqual(
            self.fmt("-500", parens_negative=True, symbol=True), "(৳500.00)"
        )

    def test_international_grouping(self):
        self.assertEqual(self.fmt("1234567.89", grouping="international"), "1,234,567.89")
        self.assertEqual(self.fmt("100000", grouping="intl"), "100,000.00")
        self.assertEqual(self.fmt("10000000", grouping="intl"), "10,000,000.00")
        self.assertEqual(self.fmt("999", grouping="intl"), "999.00")
        self.assertEqual(
            tb.format_bdt_international(M.from_str("1234567.89")), "1,234,567.89"
        )

    def test_both_groupings_agree_below_one_thousand(self):
        for taka in ("0", "1", "99.99", "999.99"):
            self.assertEqual(self.fmt(taka), self.fmt(taka, grouping="intl"), taka)

    def test_symbol_placement_and_separator(self):
        self.assertEqual(self.fmt("1000", symbol=True), "৳1,000.00")
        self.assertEqual(self.fmt("1000", symbol=True, symbol_sep=" "), "৳ 1,000.00")
        self.assertEqual(tb.CURRENCY_SYMBOL, "৳")

    def test_decimal_places(self):
        self.assertEqual(self.fmt("1234567.89", decimals=0), "12,34,568")
        self.assertEqual(self.fmt("1234567.89", decimals=4), "12,34,567.8900")
        self.assertEqual(self.fmt("1234.50", decimals=1), "1,234.50"[:-1])

    def test_decimals_zero_rounds_half_up(self):
        self.assertEqual(self.fmt("0.5", decimals=0), "1")
        self.assertEqual(self.fmt("1.5", decimals=0), "2")
        self.assertEqual(self.fmt("-1.5", decimals=0), "-2")

    def test_bangla_digits_output(self):
        self.assertEqual(self.fmt("100000", bangla_digits=True), "১,০০,০০০.০০")
        self.assertEqual(
            self.fmt("100000", bangla_digits=True, symbol=True), "৳১,০০,০০০.০০"
        )

    def test_accepts_decimal_int_and_str_as_taka(self):
        self.assertEqual(tb.format_bdt(Decimal("100000")), "1,00,000.00")
        self.assertEqual(tb.format_bdt(100000), "1,00,000.00")
        self.assertEqual(tb.format_bdt("100000"), "1,00,000.00")

    def test_money_format_helper(self):
        self.assertEqual(M.from_str("100000").format(symbol=True), "৳1,00,000.00")
        self.assertEqual(M.from_str("100000").bdt, "৳1,00,000.00")

    def test_bad_grouping_or_decimals(self):
        with self.assertRaises(ValueError):
            tb.format_bdt(M.zero(), grouping="martian")
        with self.assertRaises(ValueError):
            tb.format_bdt(M.zero(), decimals=-1)

    def test_csv_amount_is_ungrouped(self):
        self.assertEqual(tb.format_amount_for_csv(M.from_str("12,34,567.89")), "1234567.89")
        self.assertEqual(tb.format_amount_for_csv(M.zero()), "0.00")
        self.assertEqual(tb.format_amount_for_csv(M.from_str("-5")), "-5.00")
        with self.assertRaises(tb.MoneyError):
            tb.format_amount_for_csv("5.00")  # type: ignore[arg-type]

    def test_digit_conversion_round_trip(self):
        self.assertEqual(tb.to_bangla_digits("12,34,567.89"), "১২,৩৪,৫৬৭.৮৯")
        self.assertEqual(tb.to_latin_digits("১২,৩৪,৫৬৭.৮৯"), "12,34,567.89")


# ======================================================================================
# Accounts
# ======================================================================================

ACCOUNTS_TOML = """
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
code = "2320"
name = "TDS Payable"
type = "liability"
normal = "credit"
role = "tds_payable"

[[account]]
code = "3100"
name = "Owner's Capital"
type = "equity"
normal = "credit"

[[account]]
code = "4100"
name = "Sales Revenue"
name_bn = "বিক্রয় আয়"
type = "income"
normal = "credit"

[[account]]
code = "6100"
name = "Office Rent"
type = "expense"
normal = "debit"
tags = ["opex"]
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
rates_file = "rates-AY2026-27.toml"

[locale]
language = "en"
grouping = "bd"
digits = "latin"
"""


class TestAccount(unittest.TestCase):
    def test_valid_account(self):
        account = tb.Account(
            code="1100", name="Cash in Hand", type="asset", normal="debit", name_bn="হাতে নগদ"
        )
        self.assertTrue(account.is_debit_normal)
        self.assertFalse(account.is_credit_normal)
        self.assertTrue(account.is_balance_sheet)
        self.assertFalse(account.is_income_statement)
        self.assertEqual(account.label, "1100 Cash in Hand (হাতে নগদ)")
        self.assertEqual(account.block.digit, "1")

    def test_type_must_be_known(self):
        with self.assertRaises(tb.AccountError) as ctx:
            tb.Account(code="1100", name="X", type="revenue", normal="credit")
        self.assertIn("asset", ctx.exception.message)

    def test_normal_must_be_debit_or_credit(self):
        with self.assertRaises(tb.AccountError):
            tb.Account(code="1100", name="X", type="asset", normal="dr")

    def test_normal_balance_must_match_type(self):
        with self.assertRaises(tb.AccountError) as ctx:
            tb.Account(code="1100", name="Cash", type="asset", normal="credit")
        self.assertIn("must be 'debit'", ctx.exception.message)
        with self.assertRaises(tb.AccountError):
            tb.Account(code="4100", name="Sales", type="income", normal="debit")
        with self.assertRaises(tb.AccountError):
            tb.Account(code="6100", name="Rent", type="expense", normal="credit")
        with self.assertRaises(tb.AccountError):
            tb.Account(code="2100", name="AP", type="liability", normal="debit")
        with self.assertRaises(tb.AccountError):
            tb.Account(code="3100", name="Capital", type="equity", normal="debit")

    def test_normal_balance_table_covers_every_type(self):
        self.assertEqual(set(tb.NORMAL_BALANCE), set(tb.ACCOUNT_TYPES))

    def test_blank_code_or_name(self):
        with self.assertRaises(tb.AccountError):
            tb.Account(code="  ", name="X", type="asset", normal="debit")
        with self.assertRaises(tb.AccountError):
            tb.Account(code="1100", name="   ", type="asset", normal="debit")

    def test_case_and_whitespace_are_normalised(self):
        account = tb.Account(code=" 1100 ", name=" Cash ", type="ASSET", normal="Debit")
        self.assertEqual(account.code, "1100")
        self.assertEqual(account.name, "Cash")
        self.assertEqual(account.type, "asset")
        self.assertEqual(account.normal, "debit")

    def test_from_mapping_requires_keys(self):
        with self.assertRaises(tb.AccountError) as ctx:
            tb.Account.from_mapping({"code": "1100", "name": "Cash"})
        self.assertIn("missing required key", ctx.exception.message)

    def test_from_mapping_rejects_unknown_keys(self):
        with self.assertRaises(tb.AccountError) as ctx:
            tb.Account.from_mapping(
                {"code": "1100", "name": "Cash", "type": "asset", "normal": "debit", "rate": 15}
            )
        self.assertIn("rate", ctx.exception.message)

    def test_block_conventions(self):
        self.assertTrue(
            tb.Account(code="5100", name="COGS", type="expense", normal="debit").code_block_is_conventional()
        )
        self.assertFalse(
            tb.Account(code="1100", name="Odd", type="income", normal="credit").code_block_is_conventional()
        )
        self.assertEqual(set(tb.ACCOUNT_BLOCKS), set("123456789"))
        self.assertIsNone(tb.block_for_code(""))


class TestChartOfAccounts(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        self.path = self.root / "accounts.toml"
        self.path.write_text(ACCOUNTS_TOML, encoding="utf-8")
        self.chart = tb.ChartOfAccounts.from_toml_path(self.path)

    def tearDown(self):
        self.dir.cleanup()

    def test_loads_every_account(self):
        self.assertEqual(len(self.chart), 10)
        self.assertIn("1100", self.chart)
        self.assertEqual(self.chart["1100"].name, "Cash in Hand")
        self.assertEqual(self.chart.get("1100").name_bn, "হাতে নগদ")

    def test_iteration_preserves_file_order(self):
        self.assertEqual(self.chart.codes()[:3], ["1100", "1200", "1310"])

    def test_unknown_code_is_a_hard_error(self):
        with self.assertRaises(tb.UnknownAccountError) as ctx:
            self.chart.get("9999")
        self.assertEqual(ctx.exception.code, "9999")
        self.assertIn("9999", ctx.exception.message)
        self.assertFalse(self.chart.has("9999"))

    def test_duplicate_codes_are_rejected(self):
        doubled = ACCOUNTS_TOML + """
[[account]]
code = "1100"
name = "Cash Again"
type = "asset"
normal = "debit"
"""
        path = self.root / "dupe.toml"
        path.write_text(doubled, encoding="utf-8")
        with self.assertRaises(tb.DuplicateAccountError) as ctx:
            tb.ChartOfAccounts.from_toml_path(path)
        self.assertIn("1100", ctx.exception.message)
        self.assertIn("twice", ctx.exception.message)

    def test_missing_file(self):
        with self.assertRaises(tb.AccountError):
            tb.ChartOfAccounts.from_toml_path(self.root / "nope.toml")

    def test_malformed_toml(self):
        path = self.root / "bad.toml"
        path.write_text("[[account]\ncode = ", encoding="utf-8")
        with self.assertRaises(tb.AccountError):
            tb.ChartOfAccounts.from_toml_path(path)

    def test_no_accounts_at_all(self):
        path = self.root / "empty.toml"
        path.write_text("# nothing here\n", encoding="utf-8")
        with self.assertRaises(tb.AccountError) as ctx:
            tb.ChartOfAccounts.from_toml_path(path)
        self.assertIn("[[account]]", ctx.exception.message)

    def test_by_type_and_block(self):
        self.assertEqual(len(self.chart.by_type("asset")), 4)
        self.assertEqual(len(self.chart.by_type("income")), 1)
        self.assertEqual([a.code for a in self.chart.by_block("2")], ["2100", "2310", "2320"])
        with self.assertRaises(tb.AccountError):
            self.chart.by_type("nonsense")

    def test_tags(self):
        self.assertEqual([a.code for a in self.chart.by_tag("opex")], ["6100"])

    def test_roles(self):
        self.assertEqual(self.chart.account_for_role(tb.ROLE_VAT_INPUT).code, "1310")
        self.assertEqual(self.chart.account_for_role(tb.ROLE_VAT_OUTPUT).code, "2310")
        with self.assertRaises(tb.UnknownAccountError):
            self.chart.account_for_role(tb.ROLE_WPPF_PAYABLE)
        missing = self.chart.missing_roles()
        self.assertIn(tb.ROLE_WPPF_PAYABLE, missing)
        self.assertNotIn(tb.ROLE_VAT_INPUT, missing)

    def test_required_roles_cover_the_bd_specific_accounts(self):
        self.assertEqual(len(tb.REQUIRED_ROLES), 10)
        for role in (
            tb.ROLE_VAT_INPUT,
            tb.ROLE_VAT_OUTPUT,
            tb.ROLE_TDS_RECEIVABLE,
            tb.ROLE_TDS_PAYABLE,
            tb.ROLE_VDS_PAYABLE,
            tb.ROLE_ADVANCE_INCOME_TAX,
            tb.ROLE_PROVIDENT_FUND_PAYABLE,
            tb.ROLE_GRATUITY_PROVISION,
            tb.ROLE_WPPF_PAYABLE,
            tb.ROLE_SUPPLEMENTARY_DUTY_PAYABLE,
        ):
            self.assertIn(role, tb.REQUIRED_ROLES)

    def test_duplicate_role_is_ambiguous(self):
        text = ACCOUNTS_TOML + """
[[account]]
code = "1311"
name = "VAT Input (second)"
type = "asset"
normal = "debit"
role = "vat_input"
"""
        path = self.root / "dupe-role.toml"
        path.write_text(text, encoding="utf-8")
        chart = tb.ChartOfAccounts.from_toml_path(path)
        with self.assertRaises(tb.AccountError):
            chart.account_for_role(tb.ROLE_VAT_INPUT)

    def test_require(self):
        self.chart.require(["1100", "4100"])
        with self.assertRaises(tb.UnknownAccountError) as ctx:
            self.chart.require(["1100", "8888"])
        self.assertIn("8888", ctx.exception.message)

    def test_soft_warnings(self):
        self.assertEqual(self.chart.block_warnings(), [])
        self.assertEqual(self.chart.code_format_warnings(), [])
        odd = tb.ChartOfAccounts(
            [tb.Account(code="1100", name="Odd Income", type="income", normal="credit")]
        )
        self.assertEqual(len(odd.block_warnings()), 1)


# ======================================================================================
# tax_tag grammar (spec §4.3)
# ======================================================================================


class TestTaxTag(unittest.TestCase):
    def test_none_forms(self):
        for text in ("NONE", "none", " None ", "", "   ", "-"):
            tag = tb.TaxTag.parse(text)
            self.assertTrue(tag.is_none, text)
            self.assertIsNone(tag.rate)
            self.assertEqual(str(tag), "NONE")

    def test_vat_output(self):
        tag = tb.TaxTag.parse("VAT:OUT:15")
        self.assertEqual(tag.kind, tb.TAG_VAT_OUT)
        self.assertTrue(tag.is_vat)
        self.assertTrue(tag.is_vat_output)
        self.assertFalse(tag.is_vat_input)
        self.assertEqual(tag.rate, Decimal("15"))
        self.assertEqual(tag.rate_fraction, Decimal("0.15"))
        self.assertEqual(str(tag), "VAT:OUT:15")

    def test_vat_input(self):
        tag = tb.TaxTag.parse("VAT:IN:7.5")
        self.assertEqual(tag.kind, tb.TAG_VAT_IN)
        self.assertTrue(tag.is_vat_input)
        self.assertEqual(str(tag), "VAT:IN:7.5")

    def test_tds_with_section(self):
        tag = tb.TaxTag.parse("TDS:52:5")
        self.assertEqual(tag.kind, tb.TAG_TDS)
        self.assertEqual(tag.section, "52")
        self.assertEqual(tag.rate, Decimal("5"))
        self.assertEqual(str(tag), "TDS:52:5")

    def test_tds_section_variants(self):
        for text, section in (
            ("TDS:52AA:10", "52AA"),
            ("TDS:53f:5", "53F"),
            ("TDS:52A(1):3", "52A(1)"),
            ("TDS:108:0", "108"),
        ):
            tag = tb.TaxTag.parse(text)
            self.assertEqual(tag.section, section, text)

    def test_vds(self):
        tag = tb.TaxTag.parse("VDS:15")
        self.assertEqual(tag.kind, tb.TAG_VDS)
        self.assertTrue(tag.is_vds)
        self.assertIsNone(tag.section)
        self.assertEqual(str(tag), "VDS:15")

    def test_case_insensitive(self):
        self.assertEqual(str(tb.TaxTag.parse("vat:out:15")), "VAT:OUT:15")
        self.assertEqual(str(tb.TaxTag.parse("tds:52:5")), "TDS:52:5")
        self.assertEqual(str(tb.TaxTag.parse("vds:15")), "VDS:15")

    def test_percent_sign_and_zero_rate_allowed(self):
        self.assertEqual(tb.TaxTag.parse("VAT:OUT:15%").rate, Decimal("15"))
        self.assertEqual(tb.TaxTag.parse("VAT:OUT:0").rate, Decimal("0"))
        self.assertEqual(str(tb.TaxTag.parse("VAT:OUT:0")), "VAT:OUT:0")

    def test_canonical_form_trims_trailing_zeros(self):
        self.assertEqual(str(tb.TaxTag.parse("VAT:OUT:15.00")), "VAT:OUT:15")
        self.assertEqual(str(tb.TaxTag.parse("VAT:OUT:7.50")), "VAT:OUT:7.5")

    def test_round_trip_through_canonical_form(self):
        for text in ("NONE", "VAT:OUT:15", "VAT:IN:7.5", "TDS:52:5", "VDS:15"):
            self.assertEqual(str(tb.TaxTag.parse(str(tb.TaxTag.parse(text)))), text)

    def test_malformed_tags_are_rejected_loudly(self):
        bad = [
            "VAT:15",
            "VAT:OUT",
            "VAT:OUT:15:extra",
            "VAT:SIDEWAYS:15",
            "VAT:OUT:abc",
            "VAT:OUT:101",
            "TDS:52",
            "TDS::5",
            "TDS:52:",
            "TDS:52:abc",
            "TDS:no-such-section:5",
            "VDS",
            "VDS:15:2",
            "VDS:abc",
            "NONE:15",
            "FOO:1",
            "::",
            "VAT",
        ]
        for text in bad:
            with self.assertRaises(tb.TaxTagError, msg=text):
                tb.TaxTag.parse(text)

    def test_error_message_carries_the_grammar(self):
        with self.assertRaises(tb.TaxTagError) as ctx:
            tb.TaxTag.parse("VAT:OUT")
        self.assertIn("VAT:OUT:<rate>", ctx.exception.hint or "")
        self.assertIn("TDS:<section>:<rate>", ctx.exception.hint or "")
        self.assertIn("VDS:<rate>", ctx.exception.hint or "")

    def test_error_message_names_the_location(self):
        with self.assertRaises(tb.TaxTagError) as ctx:
            tb.TaxTag.parse("nonsense", where="books/journal/2026-07.csv line 4")
        self.assertIn("2026-07.csv line 4", ctx.exception.message)

    def test_empty_can_be_forbidden(self):
        with self.assertRaises(tb.TaxTagError):
            tb.TaxTag.parse("", allow_empty=False)

    def test_rate_above_100_is_a_fraction_mistake(self):
        with self.assertRaises(tb.TaxTagError) as ctx:
            tb.TaxTag.parse("VDS:150")
        self.assertIn("percentages", ctx.exception.message)

    def test_apply_computes_tax_at_the_tagged_rate(self):
        tag = tb.TaxTag.parse("VAT:OUT:15")
        self.assertEqual(tag.apply(M.from_str("1000.00")), M.from_str("150.00"))
        self.assertEqual(tag.apply(M.from_str("1234.56")), M.from_str("185.18"))
        self.assertEqual(tb.TaxTag.none().apply(M.from_str("1000")), M.zero())
        with self.assertRaises(tb.MoneyError):
            tag.apply("1000")  # type: ignore[arg-type]

    def test_describe_uses_bangla_english_pairs(self):
        self.assertIn("মূসক", tb.TaxTag.parse("VAT:OUT:15").describe())
        self.assertIn("উৎসে কর কর্তন", tb.TaxTag.parse("TDS:52:5").describe())
        self.assertIn("উৎসে মূসক কর্তন", tb.TaxTag.parse("VDS:15").describe())
        self.assertEqual(tb.TaxTag.none().describe(), "not tax-relevant")

    def test_kind_whitelist(self):
        with self.assertRaises(tb.TaxTagError):
            tb.TaxTag(kind="VAT")
        self.assertEqual(len(tb.TAX_TAG_KINDS), 5)

    def test_defines_no_rate_of_its_own(self):
        """The library must not carry a Bangladeshi VAT/TDS rate anywhere."""
        source = (ENGINE_DIR / "takabooks.py").read_text(encoding="utf-8")
        self.assertNotIn("vat_rate =", source)
        self.assertNotIn("VAT_RATE", source)
        self.assertNotIn("TDS_RATE", source)


# ======================================================================================
# Postings and journal rows
# ======================================================================================


def posting(entry_id="E1", account="1100", debit="0", credit="0", date="2026-07-01", **kwargs):
    return tb.Posting(
        date=tb.parse_date(date),
        entry_id=entry_id,
        description=kwargs.pop("description", "test"),
        account=account,
        debit=M.from_str(debit),
        credit=M.from_str(credit),
        **kwargs,
    )


class TestParseDate(unittest.TestCase):
    def test_iso_dates(self):
        self.assertEqual(tb.parse_date("2026-07-15"), datetime.date(2026, 7, 15))

    def test_non_iso_forms_are_rejected(self):
        for text in ("20260715", "15-07-2026", "2026/07/15", "2026-7-5", "", "yesterday"):
            with self.assertRaises(tb.JournalError, msg=text):
                tb.parse_date(text)

    def test_impossible_dates_are_rejected(self):
        with self.assertRaises(tb.JournalError):
            tb.parse_date("2026-02-30")

    def test_date_objects_pass_through(self):
        day = datetime.date(2026, 7, 15)
        self.assertEqual(tb.parse_date(day), day)


class TestPosting(unittest.TestCase):
    def test_debit_row(self):
        p = posting(debit="100.00")
        self.assertTrue(p.is_debit)
        self.assertFalse(p.is_credit)
        self.assertEqual(p.amount, M.from_str("100.00"))
        self.assertEqual(p.signed_amount, M.from_str("100.00"))
        self.assertEqual(p.month, "2026-07")

    def test_credit_row(self):
        p = posting(credit="100.00")
        self.assertTrue(p.is_credit)
        self.assertEqual(p.signed_amount, M.from_str("-100.00"))

    def test_exactly_one_side_must_be_non_zero(self):
        with self.assertRaises(tb.JournalError) as ctx:
            posting(debit="0", credit="0")
        self.assertIn("Exactly one", ctx.exception.message)
        with self.assertRaises(tb.JournalError) as ctx:
            posting(debit="10", credit="10")
        self.assertIn("both non-zero", ctx.exception.message)

    def test_negative_amounts_are_refused(self):
        with self.assertRaises(tb.JournalError) as ctx:
            posting(debit="-10")
        self.assertIn("negative", ctx.exception.message)

    def test_entry_id_and_account_are_required(self):
        with self.assertRaises(tb.JournalError):
            posting(entry_id="  ", debit="10")
        with self.assertRaises(tb.JournalError):
            posting(account="", debit="10")

    def test_tax_tag_string_is_parsed(self):
        p = posting(debit="10", tax_tag="VAT:OUT:15")
        self.assertIsInstance(p.tax_tag, tb.TaxTag)
        self.assertTrue(p.tax_tag.is_vat_output)

    def test_default_tax_tag_is_none(self):
        self.assertTrue(posting(debit="10").tax_tag.is_none)

    def test_bad_tax_tag_fails(self):
        with self.assertRaises(tb.TaxTagError):
            posting(debit="10", tax_tag="VAT:OUT")

    def test_money_must_be_money(self):
        with self.assertRaises(tb.JournalError):
            tb.Posting(
                date=datetime.date(2026, 7, 1),
                entry_id="E1",
                description="",
                account="1100",
                debit="100.00",  # type: ignore[arg-type]
                credit=M.zero(),
            )

    def test_location_string(self):
        p = posting(debit="10", source_file="books/journal/2026-07.csv", source_line=4)
        self.assertEqual(p.location, "books/journal/2026-07.csv line 4")
        self.assertEqual(posting(debit="10").location, "")


class TestPostingRows(unittest.TestCase):
    def test_from_mapping(self):
        p = tb.Posting.from_row(
            {
                "date": "2026-07-01",
                "entry_id": "INV-001",
                "description": "Sale",
                "account": "1100",
                "debit": "1150.00",
                "credit": "",
                "party": "Rahim Traders",
                "doc_ref": "INV-001",
                "tax_tag": "NONE",
                "memo": "cash sale",
            }
        )
        self.assertEqual(p.entry_id, "INV-001")
        self.assertEqual(p.debit, M.from_str("1150.00"))
        self.assertEqual(p.credit, M.zero())
        self.assertEqual(p.party, "Rahim Traders")

    def test_from_sequence(self):
        cells = ["2026-07-01", "E1", "Sale", "4100", "", "1000.00", "", "", "VAT:OUT:15", "note"]
        p = tb.Posting.from_row(cells, source_file="j.csv", source_line=2)
        self.assertEqual(p.credit, M.from_str("1000.00"))
        self.assertEqual(str(p.tax_tag), "VAT:OUT:15")
        self.assertEqual(p.source_line, 2)

    def test_short_row_is_padded_when_only_optional_fields_missing(self):
        cells = ["2026-07-01", "E1", "Sale", "4100", "", "1000.00"]
        p = tb.Posting.from_row(cells)
        self.assertEqual(p.memo, "")
        self.assertTrue(p.tax_tag.is_none)

    def test_too_short_row_fails(self):
        with self.assertRaises(tb.JournalError) as ctx:
            tb.Posting.from_row(["2026-07-01", "E1", "Sale"])
        self.assertIn("at least", ctx.exception.message)

    def test_unquoted_commas_in_memo_survive(self):
        cells = [
            "2026-07-01", "E1", "Sale", "4100", "", "1000.00", "", "", "NONE",
            "part one", " part two", " part three",
        ]
        p = tb.Posting.from_row(cells)
        self.assertEqual(p.memo, "part one, part two, part three")

    def test_to_row_round_trip(self):
        original = posting(debit="1234.56", tax_tag="TDS:52:5", memo="a, b", party="X")
        rebuilt = tb.Posting.from_row(original.to_row())
        self.assertEqual(original, rebuilt)

    def test_to_row_writes_plain_decimals(self):
        row = posting(debit="1234567.89").to_row()
        self.assertEqual(row["debit"], "1234567.89")
        self.assertEqual(row["credit"], "0.00")
        self.assertEqual(row["tax_tag"], "NONE")
        self.assertEqual(list(row), list(tb.JOURNAL_COLUMNS))

    def test_blank_amount_means_zero(self):
        self.assertEqual(tb.parse_amount_field("", field_name="debit"), M.zero())
        self.assertEqual(tb.parse_amount_field("-", field_name="debit"), M.zero())
        self.assertEqual(tb.parse_amount_field(None, field_name="debit"), M.zero())

    def test_bad_amount_raises_journal_error_with_location(self):
        with self.assertRaises(tb.JournalError) as ctx:
            tb.parse_amount_field("abc", field_name="debit", where="j.csv line 3")
        self.assertIn("j.csv line 3", ctx.exception.message)
        self.assertIn("debit", ctx.exception.message)


# ======================================================================================
# Entries and the double-entry invariant
# ======================================================================================


class TestEntryBalance(unittest.TestCase):
    def test_balanced_entry(self):
        entry = tb.Entry.from_postings(
            [posting(debit="1000.00", account="1100"), posting(credit="1000.00", account="4100")]
        )
        self.assertTrue(entry.is_balanced)
        self.assertEqual(entry.difference, M.zero())
        self.assertEqual(entry.total_debit, M.from_str("1000.00"))
        self.assertEqual(entry.total_credit, M.from_str("1000.00"))
        entry.require_balanced()

    def test_balance_is_checked_in_paisa_not_taka(self):
        entry = tb.Entry.from_postings(
            [posting(debit="1000.00", account="1100"), posting(credit="999.99", account="4100")]
        )
        self.assertFalse(entry.is_balanced)
        self.assertEqual(entry.difference, M.from_paisa(1))

    def test_multi_line_entry(self):
        entry = tb.Entry.from_postings(
            [
                posting(debit="1150.00", account="1100"),
                posting(credit="1000.00", account="4100", tax_tag="NONE"),
                posting(credit="150.00", account="2310", tax_tag="VAT:OUT:15"),
            ]
        )
        self.assertTrue(entry.is_balanced)
        self.assertEqual(entry.accounts, ("1100", "4100", "2310"))
        self.assertEqual(len(entry.tax_tags), 3)

    def test_unbalanced_entry_raises_naming_id_and_amount(self):
        entry = tb.Entry.from_postings(
            [
                posting(entry_id="INV-042", debit="1000.00", account="1100"),
                posting(entry_id="INV-042", credit="900.00", account="4100"),
            ]
        )
        with self.assertRaises(tb.BalanceError) as ctx:
            entry.require_balanced()
        exc = ctx.exception
        self.assertEqual(exc.entry_id, "INV-042")
        self.assertEqual(exc.difference, M.from_str("100.00"))
        self.assertEqual(exc.total_debit, M.from_str("1000.00"))
        self.assertEqual(exc.total_credit, M.from_str("900.00"))
        self.assertIn("INV-042", exc.message)
        self.assertIn("৳100.00", exc.message)
        self.assertIn("1,000.00", exc.message)
        self.assertIn("too much debit", exc.message)
        self.assertEqual(exc.exit_code, 5)

    def test_too_much_credit_is_named_as_such(self):
        entry = tb.Entry.from_postings(
            [
                posting(entry_id="E9", debit="900.00", account="1100"),
                posting(entry_id="E9", credit="1000.00", account="4100"),
            ]
        )
        with self.assertRaises(tb.BalanceError) as ctx:
            entry.require_balanced()
        self.assertIn("too much credit", ctx.exception.message)

    def test_message_points_at_the_file(self):
        entry = tb.Entry.from_postings(
            [
                posting(
                    entry_id="E1", debit="10.00", source_file="books/journal/2026-07.csv",
                    source_line=3,
                ),
                posting(
                    entry_id="E1", credit="9.00", source_file="books/journal/2026-07.csv",
                    source_line=4, account="4100",
                ),
            ]
        )
        with self.assertRaises(tb.BalanceError) as ctx:
            entry.require_balanced()
        self.assertIn("books/journal/2026-07.csv lines 3–4", ctx.exception.message)

    def test_entry_rejects_mixed_ids(self):
        with self.assertRaises(tb.JournalError):
            tb.Entry(entry_id="A", postings=(posting(entry_id="B", debit="1"),))
        with self.assertRaises(tb.JournalError):
            tb.Entry.from_postings([])

    def test_grouping_orders_by_date_then_appearance(self):
        postings = [
            posting(entry_id="B", date="2026-07-05", debit="1"),
            posting(entry_id="A", date="2026-07-01", debit="1"),
            posting(entry_id="B", date="2026-07-05", credit="1", account="4100"),
        ]
        entries = tb.group_postings(postings)
        self.assertEqual([e.entry_id for e in entries], ["A", "B"])
        self.assertEqual(len(entries[1].postings), 2)


# ======================================================================================
# Journal CSV files
# ======================================================================================

GOOD_JOURNAL = """date,entry_id,description,account,debit,credit,party,doc_ref,tax_tag,memo
# a cash sale with 15% output VAT (মূসক)
2026-07-01,INV-001,Cash sale,1100,1150.00,0.00,Rahim Traders,INV-001,NONE,

2026-07-01,INV-001,Cash sale,4100,0.00,1000.00,Rahim Traders,INV-001,NONE,
2026-07-01,INV-001,Cash sale,2310,0.00,150.00,Rahim Traders,INV-001,VAT:OUT:15,output VAT
2026-07-15,RENT-07,Office rent,6100,20000.00,0.00,Landlord,RCP-7,NONE,July rent
2026-07-15,RENT-07,Office rent,1100,0.00,20000.00,Landlord,RCP-7,NONE,
"""


class TestJournalCSV(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        self.books = self.root / "books"
        (self.books / "journal").mkdir(parents=True)
        (self.books / "accounts.toml").write_text(ACCOUNTS_TOML, encoding="utf-8")
        (self.books / "config.toml").write_text(CONFIG_TOML, encoding="utf-8")
        self.journal = self.books / "journal" / "2026-07.csv"
        self.journal.write_text(GOOD_JOURNAL, encoding="utf-8")
        self.chart = tb.ChartOfAccounts.from_toml_path(self.books / "accounts.toml")

    def tearDown(self):
        self.dir.cleanup()

    def test_header_constant_matches_the_spec(self):
        self.assertEqual(
            tb.JOURNAL_HEADER,
            "date,entry_id,description,account,debit,credit,party,doc_ref,tax_tag,memo",
        )
        self.assertEqual(tb.JOURNAL_COLUMNS[-1], "memo")

    def test_reads_every_data_row(self):
        postings = tb.read_journal_csv(self.journal, chart=self.chart)
        self.assertEqual(len(postings), 5)
        self.assertEqual(postings[0].entry_id, "INV-001")
        self.assertEqual(postings[0].debit, M.from_str("1150.00"))
        self.assertTrue(postings[2].tax_tag.is_vat_output)

    def test_comments_and_blank_lines_are_skipped(self):
        postings = tb.read_journal_csv(self.journal)
        self.assertTrue(all(p.entry_id for p in postings))

    def test_line_numbers_are_recorded(self):
        postings = tb.read_journal_csv(self.journal)
        self.assertEqual(postings[0].source_line, 3)
        self.assertEqual(postings[1].source_line, 5)

    def test_unknown_account_is_a_hard_error(self):
        bad = GOOD_JOURNAL + "2026-07-20,X,Odd,9999,1.00,0.00,,,NONE,\n"
        path = self.books / "journal" / "2026-08.csv"
        path.write_text(bad, encoding="utf-8")
        with self.assertRaises(tb.UnknownAccountError) as ctx:
            tb.read_journal_csv(path, chart=self.chart)
        self.assertIn("9999", ctx.exception.message)

    def test_wrong_header_is_rejected(self):
        path = self.books / "journal" / "2026-09.csv"
        path.write_text("date,entry,account,debit,credit\n", encoding="utf-8")
        with self.assertRaises(tb.JournalError) as ctx:
            tb.read_journal_csv(path)
        self.assertIn(tb.JOURNAL_HEADER, ctx.exception.hint or "")

    def test_missing_header_is_rejected(self):
        path = self.books / "journal" / "2026-10.csv"
        path.write_text("# only a comment\n", encoding="utf-8")
        with self.assertRaises(tb.JournalError):
            tb.read_journal_csv(path)

    def test_bom_is_tolerated(self):
        path = self.books / "journal" / "2026-11.csv"
        path.write_text("﻿" + GOOD_JOURNAL, encoding="utf-8")
        self.assertEqual(len(tb.read_journal_csv(path)), 5)

    def test_missing_file(self):
        with self.assertRaises(tb.JournalError):
            tb.read_journal_csv(self.books / "journal" / "nope.csv")

    def test_quoted_commas_in_memo(self):
        path = self.books / "journal" / "2026-12.csv"
        path.write_text(
            tb.JOURNAL_HEADER
            + '\n2026-12-01,E1,Sale,1100,10.00,0.00,,,NONE,"one, two, three"\n',
            encoding="utf-8",
        )
        self.assertEqual(tb.read_journal_csv(path)[0].memo, "one, two, three")

    def test_write_then_read_round_trip(self):
        postings = tb.read_journal_csv(self.journal, chart=self.chart)
        out = self.root / "out" / "2026-07.csv"
        tb.write_journal_csv(out, postings)
        again = tb.read_journal_csv(out, chart=self.chart)
        self.assertEqual([p.to_row() for p in postings], [p.to_row() for p in again])
        self.assertTrue(out.read_text(encoding="utf-8").startswith(tb.JOURNAL_HEADER))

    def test_append_creates_header_then_appends(self):
        out = self.root / "append" / "2026-07.csv"
        first = posting(entry_id="A1", debit="10.00")
        second = posting(entry_id="A1", credit="10.00", account="4100")
        tb.append_journal_csv(out, [first])
        tb.append_journal_csv(out, [second])
        text = out.read_text(encoding="utf-8")
        self.assertEqual(text.count(tb.JOURNAL_HEADER), 1)
        self.assertEqual(len(tb.read_journal_csv(out)), 2)

    def test_append_nothing_is_a_no_op(self):
        out = self.root / "append2" / "x.csv"
        tb.append_journal_csv(out, [])
        self.assertFalse(out.exists())

    def test_journal_files_are_sorted(self):
        (self.books / "journal" / "2026-08.csv").write_text(tb.JOURNAL_HEADER + "\n", encoding="utf-8")
        names = [p.name for p in tb.journal_files(self.books)]
        self.assertEqual(names, ["2026-07.csv", "2026-08.csv"])

    def test_strict_filenames(self):
        (self.books / "journal" / "notes.csv").write_text(tb.JOURNAL_HEADER + "\n", encoding="utf-8")
        with self.assertRaises(tb.JournalError):
            tb.journal_files(self.books, strict=True)
        self.assertEqual(len(tb.journal_files(self.books)), 2)

    def test_missing_journal_dir(self):
        with self.assertRaises(tb.LedgerError):
            tb.journal_files(self.root / "nowhere")

    def test_journal_path_for(self):
        self.assertEqual(
            tb.journal_path_for("books", "2026-07-15"), Path("books/journal/2026-07.csv")
        )
        self.assertEqual(
            tb.journal_path_for("books", datetime.date(2026, 1, 5)),
            Path("books/journal/2026-01.csv"),
        )

    def test_layout_helpers(self):
        self.assertEqual(tb.config_path("books"), Path("books/config.toml"))
        self.assertEqual(tb.accounts_path("books"), Path("books/accounts.toml"))
        self.assertEqual(tb.journal_dir("books"), Path("books/journal"))


# ======================================================================================
# Ledger
# ======================================================================================


class TestLedger(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        self.books = self.root / "books"
        (self.books / "journal").mkdir(parents=True)
        (self.books / "accounts.toml").write_text(ACCOUNTS_TOML, encoding="utf-8")
        (self.books / "config.toml").write_text(CONFIG_TOML, encoding="utf-8")
        (self.books / "journal" / "2026-07.csv").write_text(GOOD_JOURNAL, encoding="utf-8")

    def tearDown(self):
        self.dir.cleanup()

    def write_journal(self, name, body):
        (self.books / "journal" / name).write_text(
            tb.JOURNAL_HEADER + "\n" + body, encoding="utf-8"
        )

    def test_load(self):
        ledger = tb.Ledger.load(self.books)
        self.assertEqual(len(ledger), 5)
        self.assertEqual(len(ledger.entries), 2)
        self.assertEqual(ledger.entry_ids(), ["INV-001", "RENT-07"])
        self.assertTrue(ledger.is_balanced())
        self.assertIsNotNone(ledger.chart)
        self.assertIsNotNone(ledger.config)

    def test_load_refuses_unbalanced_books_by_default(self):
        self.write_journal(
            "2026-08.csv",
            "2026-08-01,BAD-1,Broken,1100,500.00,0.00,,,NONE,\n"
            "2026-08-01,BAD-1,Broken,4100,0.00,400.00,,,NONE,\n",
        )
        with self.assertRaises(tb.BalanceError) as ctx:
            tb.Ledger.load(self.books)
        self.assertIn("BAD-1", ctx.exception.message)
        self.assertIn("৳100.00", ctx.exception.message)
        self.assertEqual(ctx.exception.entry_ids, ("BAD-1",))

    def test_validate_style_load_collects_instead_of_raising(self):
        self.write_journal(
            "2026-08.csv",
            "2026-08-01,BAD-1,Broken,1100,500.00,0.00,,,NONE,\n"
            "2026-08-01,BAD-1,Broken,4100,0.00,400.00,,,NONE,\n"
            "2026-08-02,BAD-2,Broken,1100,1.00,0.00,,,NONE,\n"
            "2026-08-02,BAD-2,Broken,4100,0.00,2.00,,,NONE,\n",
        )
        ledger = tb.Ledger.load(self.books, require_balanced=False)
        problems = ledger.imbalances()
        self.assertEqual([entry_id for entry_id, _ in problems], ["BAD-1", "BAD-2"])
        self.assertEqual(problems[0][1], M.from_str("100.00"))
        self.assertEqual(problems[1][1], M.from_str("-1.00"))
        with self.assertRaises(tb.BalanceError) as ctx:
            ledger.require_balanced()
        self.assertIn("2 entries are out", ctx.exception.message)
        self.assertIn("BAD-1", ctx.exception.message)
        self.assertIn("BAD-2", ctx.exception.message)

    def test_missing_books_dir(self):
        with self.assertRaises(tb.LedgerError):
            tb.Ledger.load(self.root / "nope")

    def test_missing_config(self):
        (self.books / "config.toml").unlink()
        with self.assertRaises(tb.ConfigError):
            tb.Ledger.load(self.books)

    def test_totals_and_balances(self):
        ledger = tb.Ledger.load(self.books)
        self.assertEqual(ledger.total_debits(), ledger.total_credits())
        self.assertEqual(ledger.total_debits(), M.from_str("21150.00"))
        # Cash: 1150 in, 20000 out
        self.assertEqual(ledger.balance("1100"), M.from_str("-18850.00"))
        self.assertEqual(ledger.natural_balance("1100"), M.from_str("-18850.00"))
        # Sales is credit-normal, so its natural balance is positive
        self.assertEqual(ledger.balance("4100"), M.from_str("-1000.00"))
        self.assertEqual(ledger.natural_balance("4100"), M.from_str("1000.00"))

    def test_account_totals(self):
        totals = tb.Ledger.load(self.books).account_totals()
        self.assertEqual(totals["1100"].debit, M.from_str("1150.00"))
        self.assertEqual(totals["1100"].credit, M.from_str("20000.00"))
        self.assertEqual(totals["1100"].net, M.from_str("-18850.00"))
        self.assertEqual(totals["2310"].natural, M.from_str("150.00"))
        self.assertEqual(totals["4100"].name, "Sales Revenue")
        self.assertEqual(totals["4100"].type, "income")
        self.assertNotIn("1200", totals)

    def test_account_totals_can_include_unused_accounts(self):
        totals = tb.Ledger.load(self.books).account_totals(include_unused=True)
        self.assertIn("1200", totals)
        self.assertEqual(totals["1200"].debit, M.zero())

    def test_trial_balance_ties_out(self):
        totals = tb.Ledger.load(self.books).account_totals()
        self.assertEqual(
            M.sum(t.debit for t in totals.values()),
            M.sum(t.credit for t in totals.values()),
        )

    def test_type_total(self):
        ledger = tb.Ledger.load(self.books)
        self.assertEqual(ledger.type_total("income"), M.from_str("1000.00"))
        self.assertEqual(ledger.type_total("expense"), M.from_str("20000.00"))
        self.assertEqual(ledger.type_total("liability"), M.from_str("150.00"))
        with self.assertRaises(tb.AccountError):
            ledger.type_total("nonsense")

    def test_filter_by_date(self):
        ledger = tb.Ledger.load(self.books)
        july_first = ledger.filter(since="2026-07-01", until="2026-07-01")
        self.assertEqual(len(july_first), 3)
        self.assertEqual(july_first.entry_ids(), ["INV-001"])
        self.assertEqual(len(ledger.period("2026-07-10", "2026-07-31")), 2)

    def test_filter_by_account_and_type_and_tag(self):
        ledger = tb.Ledger.load(self.books)
        self.assertEqual(len(ledger.filter(accounts=["1100"])), 2)
        self.assertEqual(len(ledger.filter(account_types=["income"])), 1)
        self.assertEqual(len(ledger.filter(tax_kinds=[tb.TAG_VAT_OUT])), 1)
        self.assertEqual(len(ledger.filter(entry_ids=["RENT-07"])), 2)
        self.assertEqual(len(ledger.filter(parties=["Landlord"])), 2)

    def test_filter_returns_a_usable_ledger(self):
        ledger = tb.Ledger.load(self.books).filter(entry_ids=["INV-001"])
        self.assertTrue(ledger.is_balanced())
        self.assertEqual(ledger.chart, ledger.chart)
        self.assertEqual(ledger.total_debits(), M.from_str("1150.00"))

    def test_tax_postings(self):
        ledger = tb.Ledger.load(self.books)
        self.assertEqual(len(ledger.tax_postings(tb.TAG_VAT_OUT)), 1)
        self.assertEqual(len(ledger.tax_postings(tb.TAG_VDS)), 0)
        with self.assertRaises(tb.TaxTagError):
            ledger.tax_postings("WHAT")

    def test_entry_lookup(self):
        ledger = tb.Ledger.load(self.books)
        self.assertEqual(len(ledger.entry("INV-001").postings), 3)
        self.assertTrue(ledger.has_entry("RENT-07"))
        with self.assertRaises(tb.LedgerError):
            ledger.entry("NOPE")

    def test_date_range(self):
        ledger = tb.Ledger.load(self.books)
        self.assertEqual(
            ledger.date_range(), (datetime.date(2026, 7, 1), datetime.date(2026, 7, 15))
        )
        self.assertEqual(tb.Ledger([]).date_range(), (None, None))
        self.assertTrue(tb.Ledger([]).is_empty)

    def test_integrity_helpers(self):
        self.write_journal(
            "2026-08.csv",
            "2026-08-05,DUP-1,First,1100,10.00,0.00,,,NONE,\n"
            "2026-08-05,DUP-1,First,4100,0.00,10.00,,,NONE,\n"
            "2026-08-01,LATE,Backwards,1100,5.00,0.00,,,NONE,\n"
            "2026-08-01,LATE,Backwards,4100,0.00,5.00,,,NONE,\n"
            "2026-09-01,MISFILED,Wrong month,1100,5.00,0.00,,,NONE,\n"
            "2026-09-01,MISFILED,Wrong month,4100,0.00,5.00,,,NONE,\n",
        )
        ledger = tb.Ledger.load(self.books, require_balanced=False)
        self.assertTrue(any("earlier than" in p for p in ledger.out_of_order_dates()))
        self.assertTrue(any("MISFILED" not in p and "2026-08.csv" in p
                            for p in ledger.misfiled_postings()))
        self.assertEqual(ledger.unknown_accounts(), [])

    def test_entry_id_conflicts_across_files_and_dates(self):
        self.write_journal(
            "2026-08.csv",
            "2026-08-01,INV-001,Reused id,1100,10.00,0.00,,,NONE,\n"
            "2026-08-01,INV-001,Reused id,4100,0.00,10.00,,,NONE,\n",
        )
        ledger = tb.Ledger.load(self.books, require_balanced=False)
        problems = " ".join(ledger.entry_id_conflicts())
        self.assertIn("INV-001", problems)
        self.assertIn("more than one date", problems)
        self.assertIn("split across files", problems)

    def test_unknown_accounts_when_not_strict(self):
        self.write_journal(
            "2026-08.csv",
            "2026-08-01,X,Odd,9999,10.00,0.00,,,NONE,\n"
            "2026-08-01,X,Odd,4100,0.00,10.00,,,NONE,\n",
        )
        ledger = tb.Ledger.load(self.books, strict_accounts=False, require_balanced=False)
        self.assertEqual([p.account for p in ledger.unknown_accounts()], ["9999"])

    def test_ledger_without_a_chart(self):
        ledger = tb.Ledger([posting(debit="10"), posting(credit="10", account="4100")])
        self.assertTrue(ledger.is_balanced())
        self.assertEqual(ledger.unknown_accounts(), [])
        with self.assertRaises(tb.LedgerError):
            ledger.type_total("asset")
        with self.assertRaises(tb.LedgerError):
            ledger.filter(account_types=["asset"])


# ======================================================================================
# Config
# ======================================================================================


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        self.books = self.root / "books"
        self.books.mkdir()
        self.path = self.books / "config.toml"
        self.path.write_text(CONFIG_TOML, encoding="utf-8")

    def tearDown(self):
        self.dir.cleanup()

    def test_load(self):
        config = tb.Config.load(self.books)
        self.assertEqual(config.business_name, "Ticon Sys Demo Traders")
        self.assertEqual(config.business_name_bn, "টিকন সিস ডেমো ট্রেডার্স")
        self.assertEqual(config.currency, "BDT")
        self.assertEqual(config.fiscal_year_start, "07-01")
        self.assertEqual(config.assessment_year, "2026-27")
        self.assertEqual(config.grouping, tb.GROUPING_BD)
        self.assertIn("টিকন", config.display_name)

    def test_missing_file(self):
        with self.assertRaises(tb.ConfigError) as ctx:
            tb.Config.load(self.root / "nowhere")
        self.assertIn("init_books", ctx.exception.hint or "")

    def test_malformed_toml(self):
        self.path.write_text("[business\n", encoding="utf-8")
        with self.assertRaises(tb.ConfigError):
            tb.Config.load(self.books)

    def test_dotted_get(self):
        config = tb.Config.load(self.books)
        self.assertEqual(config.get("business.tin"), "000000000000")
        self.assertIsNone(config.get("business.nothing"))
        self.assertEqual(config.get("a.b.c", "fallback"), "fallback")

    def test_no_statutory_defaults_are_invented(self):
        empty = tb.Config.from_mapping({})
        self.assertIsNone(empty.fiscal_year_start)
        self.assertIsNone(empty.assessment_year)
        with self.assertRaises(tb.ConfigError) as ctx:
            empty.require_fiscal_year_start()
        self.assertIn("not assume", ctx.exception.hint or "")
        with self.assertRaises(tb.ConfigError) as ctx:
            empty.require_assessment_year()
        self.assertIn("assessment year", ctx.exception.hint or "")

    def test_fiscal_year_format_is_checked(self):
        self.path.write_text('[books]\nfiscal_year_start = "July"\n', encoding="utf-8")
        with self.assertRaises(tb.ConfigError) as ctx:
            tb.Config.load(self.books)
        self.assertIn("MM-DD", ctx.exception.message)

    def test_currency_is_bdt_only(self):
        self.path.write_text('[books]\ncurrency = "USD"\n', encoding="utf-8")
        with self.assertRaises(tb.ConfigError):
            tb.Config.load(self.books)

    def test_locale_validation(self):
        self.path.write_text('[locale]\ngrouping = "martian"\n', encoding="utf-8")
        with self.assertRaises(tb.ConfigError):
            tb.Config.load(self.books)
        self.path.write_text('[locale]\ndigits = "roman"\n', encoding="utf-8")
        with self.assertRaises(tb.ConfigError):
            tb.Config.load(self.books)
        self.path.write_text('[locale]\nlanguage = "fr"\n', encoding="utf-8")
        with self.assertRaises(tb.ConfigError):
            tb.Config.load(self.books)

    def test_grouping_alias_is_normalised(self):
        self.path.write_text('[locale]\ngrouping = "intl"\n', encoding="utf-8")
        self.assertEqual(tb.Config.load(self.books).grouping, tb.GROUPING_INTL)

    def test_format_money_follows_locale(self):
        config = tb.Config.load(self.books)
        self.assertEqual(config.format_money(M.from_str("100000")), "1,00,000.00")
        self.path.write_text('[locale]\ngrouping = "intl"\ndigits = "bangla"\n', encoding="utf-8")
        config = tb.Config.load(self.books)
        self.assertEqual(config.format_money(M.from_str("100000")), "১০০,০০০.০০")

    def test_sections_must_be_tables(self):
        self.path.write_text('business = "Acme"\n', encoding="utf-8")
        with self.assertRaises(tb.ConfigError):
            tb.Config.load(self.books)


# ======================================================================================
# Rates TOML — structural only; this library defines no Bangladeshi tax figure
# ======================================================================================

RATES_TOML = """
[meta]
assessment_year = "2026-27"

[vat.standard]
value = 15
unit = "percent"
source = "https://example.invalid/placeholder"
verified = false
note = "PLACEHOLDER — not confirmed against a primary NBR source"

[vat.threshold]
value = 0
unit = "BDT"
verified = false

[placeholders]
bare_scalar = 42
"""


class TestRatesTable(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        self.path = self.root / "rates-AY2026-27.toml"
        self.path.write_text(RATES_TOML, encoding="utf-8")
        self.rates = tb.RatesTable.from_toml_path(self.path)

    def tearDown(self):
        self.dir.cleanup()

    def test_assessment_year_from_meta(self):
        self.assertEqual(self.rates.assessment_year, "2026-27")

    def test_assessment_year_falls_back_to_filename(self):
        path = self.root / "rates-AY2027-28.toml"
        path.write_text("[vat]\n", encoding="utf-8")
        self.assertEqual(tb.RatesTable.from_toml_path(path).assessment_year, "2027-28")

    def test_get_unwraps_value_tables(self):
        self.assertEqual(self.rates.get("vat.standard"), 15)
        self.assertEqual(self.rates.decimal("vat.standard"), Decimal("15"))
        self.assertTrue(self.rates.has("vat.standard"))

    def test_missing_key_refuses_to_guess(self):
        with self.assertRaises(tb.RatesError) as ctx:
            self.rates.get("income_tax.slabs")
        self.assertIn("will not substitute", ctx.exception.hint or "")
        self.assertEqual(self.rates.get("income_tax.slabs", None), None)

    def test_rate_carries_provenance(self):
        rate = self.rates.rate("vat.standard")
        self.assertEqual(rate.value, 15)
        self.assertFalse(rate.is_verified)
        self.assertIn("PLACEHOLDER", rate.note)
        self.assertIn("UNVERIFIED", rate.caveat())

    def test_bare_scalars_are_treated_as_unverified(self):
        rate = self.rates.rate("placeholders.bare_scalar")
        self.assertFalse(rate.is_verified)
        self.assertNotEqual(rate.caveat(), "")

    def test_verified_true_clears_the_caveat(self):
        path = self.root / "rates-AY2030-31.toml"
        path.write_text(
            '[x]\nvalue = 1\nverified = true\nsource = "https://nbr.gov.bd/"\n', encoding="utf-8"
        )
        rate = tb.RatesTable.from_toml_path(path).rate("x")
        self.assertTrue(rate.is_verified)
        self.assertEqual(rate.caveat(), "")

    def test_unverified_keys_and_caveats(self):
        # unverified_keys() audits declared rate nodes (tables carrying `value`).
        self.assertEqual(self.rates.unverified_keys(), ["vat.standard", "vat.threshold"])
        self.assertEqual(len(self.rates.caveats()), 2)
        self.assertTrue(all("UNVERIFIED" in line for line in self.rates.caveats()))

    def test_section_access(self):
        self.assertIn("standard", self.rates.section("vat"))
        with self.assertRaises(tb.RatesError):
            self.rates.section("vat.standard.value")

    def test_provenance_line_names_the_file_and_year(self):
        line = self.rates.provenance()
        self.assertIn("rates-AY2026-27.toml", line)
        self.assertIn("2026-27", line)
        self.assertIn("করবর্ষ", line)

    def test_money_helper(self):
        self.assertEqual(self.rates.money("vat.threshold"), M.zero())

    def test_missing_file(self):
        with self.assertRaises(tb.RatesError):
            tb.RatesTable.from_toml_path(self.root / "nope.toml")

    def test_section_without_value_is_not_a_rate(self):
        with self.assertRaises(tb.RatesError):
            self.rates.rate("vat")


# ======================================================================================
# CLI helpers and utilities
# ======================================================================================


class TestCliHelpers(unittest.TestCase):
    def test_common_parser_flags(self):
        parser = tb.common_parser("report.py", "Trial balance")
        args = parser.parse_args([])
        self.assertEqual(args.books, "books")
        self.assertFalse(args.json)
        args = parser.parse_args(["--books", "/tmp/b", "--json"])
        self.assertEqual(args.books, "/tmp/b")
        self.assertTrue(args.json)

    def test_common_parser_credits_ticon_sys(self):
        parser = tb.common_parser("report.py", "Trial balance")
        self.assertIn("ticonsys.com", parser.epilog or "")

    def test_cli_guard_exits_non_zero_with_a_message(self):
        stream = io.StringIO()
        with self.assertRaises(SystemExit) as ctx:
            with tb.cli_guard(stream=stream):
                raise tb.BalanceError("entry X is out by ৳1.00", entry_id="X")
        self.assertEqual(ctx.exception.code, tb.BalanceError.exit_code)
        self.assertIn("entry X is out", stream.getvalue())

    def test_cli_guard_json_mode(self):
        import json

        stream = io.StringIO()
        with self.assertRaises(SystemExit):
            with tb.cli_guard(json_output=True, stream=stream):
                raise tb.UnknownAccountError("no such account 9999", code="9999")
        payload = json.loads(stream.getvalue())
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"], "UnknownAccountError")
        self.assertEqual(payload["exit_code"], tb.UnknownAccountError.exit_code)

    def test_cli_guard_passes_success_through(self):
        with tb.cli_guard():
            pass

    def test_to_jsonable(self):
        payload = tb.to_jsonable(
            {
                "amount": M.from_str("1234.56"),
                "when": datetime.date(2026, 7, 1),
                "tag": tb.TaxTag.parse("VAT:OUT:15"),
                "rate": Decimal("15.0"),
                "rows": [M.zero()],
            }
        )
        self.assertEqual(payload["amount"], "1234.56")
        self.assertEqual(payload["when"], "2026-07-01")
        self.assertEqual(payload["tag"], "VAT:OUT:15")
        self.assertEqual(payload["rate"], "15.0")
        self.assertEqual(payload["rows"], ["0.00"])

    def test_to_jsonable_money_modes(self):
        self.assertEqual(tb.to_jsonable(M.from_str("1.00"), money="paisa"), 100)
        as_object = tb.to_jsonable(M.from_str("100000"), money="object")
        self.assertEqual(as_object["paisa"], 10000000)
        self.assertEqual(as_object["formatted"], "৳1,00,000.00")
        with self.assertRaises(ValueError):
            tb.to_jsonable(M.zero(), money="wrong")

    def test_json_dumps_keeps_bangla_readable(self):
        text = tb.json_dumps({"name": "হাতে নগদ", "amount": M.from_str("1.00")})
        self.assertIn("হাতে নগদ", text)
        self.assertIn('"1.00"', text)

    def test_to_jsonable_handles_dataclasses(self):
        payload = tb.to_jsonable(posting(debit="10.00"))
        self.assertEqual(payload["debit"], "10.00")
        self.assertEqual(payload["date"], "2026-07-01")

    def test_markdown_table(self):
        text = tb.markdown_table(
            ["Account", "Debit"], [["1100 Cash", "1,000.00"]], aligns=["l", "r"]
        )
        lines = text.splitlines()
        self.assertEqual(lines[0], "| Account | Debit |")
        self.assertEqual(lines[1], "| :--- | ---: |")
        self.assertEqual(lines[2], "| 1100 Cash | 1,000.00 |")

    def test_markdown_table_escapes_pipes_and_pads(self):
        text = tb.markdown_table(["A", "B"], [["x|y"], ["p", "q"]])
        self.assertIn("x\\|y", text)
        self.assertIn("| x\\|y |  |", text)
        with self.assertRaises(ValueError):
            tb.markdown_table(["A"], [], aligns=["l", "r"])

    def test_write_text_atomic_and_ensure_dir(self):
        with tempfile.TemporaryDirectory() as name:
            target = Path(name) / "nested" / "out.md"
            tb.write_text_atomic(target, "শিরোনাম\nbody\n")
            self.assertEqual(target.read_text(encoding="utf-8"), "শিরোনাম\nbody\n")
            self.assertEqual(list(target.parent.glob("*.takabooks-tmp")), [])
            self.assertTrue(tb.ensure_dir(Path(name) / "a" / "b").is_dir())

    def test_attribution_and_disclaimer(self):
        self.assertIn("Ticon Sys", tb.ATTRIBUTION)
        self.assertIn("ticonsys.com", tb.ATTRIBUTION)
        self.assertIn("bemoshiur", tb.PROJECT_URL)
        self.assertIn("ITP", tb.DISCLAIMER_EN)
        self.assertIn("NBR", tb.DISCLAIMER_EN)
        self.assertIn("আয়কর", tb.DISCLAIMER_BN)

    def test_term_pairs(self):
        self.assertEqual(tb.term("vat"), "মূসক / VAT")
        self.assertEqual(tb.term("vat", order="en-bn"), "VAT / মূসক")
        self.assertEqual(tb.term("tds"), "উৎসে কর কর্তন / TDS")
        self.assertEqual(tb.term("ledger"), "খতিয়ান / ledger")
        with self.assertRaises(KeyError):
            tb.term("no-such-term")
        with self.assertRaises(ValueError):
            tb.term("vat", order="sideways")

    def test_public_api_is_exported(self):
        for name in tb.__all__:
            self.assertTrue(hasattr(tb, name), f"__all__ names {name} but it is missing")


# ======================================================================================
# End-to-end: a small set of books behaves like real books
# ======================================================================================


class TestEndToEnd(unittest.TestCase):
    """A cash sale with output VAT, a rent payment, and a purchase with input VAT."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.books = Path(self.dir.name) / "books"
        (self.books / "journal").mkdir(parents=True)
        (self.books / "accounts.toml").write_text(ACCOUNTS_TOML, encoding="utf-8")
        (self.books / "config.toml").write_text(CONFIG_TOML, encoding="utf-8")

        rows = [
            # Sale of ৳1,00,000 plus 15% output VAT, on credit.
            posting(entry_id="INV-100", date="2026-07-02", account="1200", debit="115000.00",
                    description="Credit sale", party="Karim Ltd", doc_ref="INV-100"),
            posting(entry_id="INV-100", date="2026-07-02", account="4100", credit="100000.00",
                    description="Credit sale", party="Karim Ltd", doc_ref="INV-100"),
            posting(entry_id="INV-100", date="2026-07-02", account="2310", credit="15000.00",
                    description="Credit sale", party="Karim Ltd", doc_ref="INV-100",
                    tax_tag="VAT:OUT:15"),
            # Rent paid, with TDS withheld from the landlord.
            posting(entry_id="RENT-07", date="2026-07-05", account="6100", debit="20000.00",
                    description="Office rent", party="Landlord"),
            posting(entry_id="RENT-07", date="2026-07-05", account="2320", credit="1000.00",
                    description="Office rent", party="Landlord", tax_tag="TDS:53A:5"),
            posting(entry_id="RENT-07", date="2026-07-05", account="1100", credit="19000.00",
                    description="Office rent", party="Landlord"),
        ]
        tb.write_journal_csv(self.books / "journal" / "2026-07.csv", rows)

    def tearDown(self):
        self.dir.cleanup()

    def test_books_load_and_balance(self):
        ledger = tb.Ledger.load(self.books)
        self.assertEqual(len(ledger.entries), 2)
        self.assertTrue(ledger.is_balanced())
        self.assertEqual(ledger.total_debits(), M.from_str("135000.00"))

    def test_output_vat_matches_the_tagged_rate(self):
        ledger = tb.Ledger.load(self.books)
        vat_rows = ledger.tax_postings(tb.TAG_VAT_OUT)
        self.assertEqual(len(vat_rows), 1)
        row = vat_rows[0]
        net_sale = ledger.natural_balance("4100")
        self.assertEqual(row.tax_tag.apply(net_sale), row.credit)
        self.assertEqual(row.credit, M.from_str("15000.00"))

    def test_tds_row_carries_its_section(self):
        ledger = tb.Ledger.load(self.books)
        tds = ledger.tax_postings(tb.TAG_TDS)[0]
        self.assertEqual(tds.tax_tag.section, "53A")
        self.assertEqual(tds.tax_tag.rate, Decimal("5"))
        self.assertEqual(tds.tax_tag.apply(M.from_str("20000.00")), tds.credit)

    def test_reported_figures_use_lakh_crore_grouping(self):
        ledger = tb.Ledger.load(self.books)
        self.assertEqual(
            ledger.config.format_money(ledger.natural_balance("4100"), symbol=True),
            "৳1,00,000.00",
        )

    def test_a_broken_entry_stops_the_whole_load(self):
        with (self.books / "journal" / "2026-08.csv").open("w", encoding="utf-8") as handle:
            handle.write(tb.JOURNAL_HEADER + "\n")
            handle.write("2026-08-01,OOPS,Typo,1100,1000.00,0.00,,,NONE,\n")
            handle.write("2026-08-01,OOPS,Typo,4100,0.00,100.00,,,NONE,\n")
        with self.assertRaises(tb.BalanceError) as ctx:
            tb.Ledger.load(self.books)
        self.assertIn("OOPS", ctx.exception.message)
        self.assertIn("৳900.00", ctx.exception.message)
        self.assertGreater(ctx.exception.exit_code, 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main(verbosity=2)
