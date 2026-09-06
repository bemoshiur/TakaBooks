"""Tests for the shipped templates (``src/templates/``) and the GitHub community files.

Run with::

    python3 -m unittest discover tests

What is proven here, per spec §4.3–§4.4 and §6:

* ``accounts.toml`` loads through the engine's own :class:`takabooks.ChartOfAccounts`,
  declares every one of the ten mandatory Bangladesh roles exactly once, keeps every code
  inside its block, and carries **no rate, threshold or money figure** in its prose.
* ``config.toml`` loads through :class:`takabooks.Config`, contains only placeholders, and
  never pre-fills a statutory value (``fiscal_year_start`` / ``assessment_year``) that
  ``init_books.py`` would refuse to copy anyway.
* ``journal-header.csv`` is byte-for-byte the schema header, because ``init_books.py``
  cross-checks it and refuses to scaffold otherwise.
* The worked examples in ``src/templates/README.md`` balance, post only to template
  accounts, use only placeholder rates/sections, and come back **clean** from
  ``validate.py`` — via the real scaffold produced by ``init_books.py``.
* The ``.github`` issue forms ask for what keeps the project current after each Finance
  Act: statute reference, primary source URL, assessment year, old and new value.

TakaBooks — Moshiur Rahman (@bemoshiur) · TICON SYSTEM LTD — https://ticonsys.com
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = REPO_ROOT / "src" / "engine"
TEMPLATES_DIR = REPO_ROOT / "src" / "templates"
GITHUB_DIR = REPO_ROOT / ".github"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

import init_books  # noqa: E402
import takabooks as tb  # noqa: E402
import validate as validate_mod  # noqa: E402

ACCOUNTS_TOML = TEMPLATES_DIR / "accounts.toml"
CONFIG_TOML = TEMPLATES_DIR / "config.toml"
JOURNAL_HEADER_CSV = TEMPLATES_DIR / "journal-header.csv"
TEMPLATES_README = TEMPLATES_DIR / "README.md"

# A percentage, a taka amount, or a statute section written into prose would be a tax
# figure nobody verified.  Account codes ("9100", "1200") are not matched: no % sign, no
# currency marker, no "section" word in front of them.
_PERCENT_RE = re.compile(r"\d+(?:\.\d+)?\s*%")
_MONEY_RE = re.compile(r"(?:৳|\bTk\.?|\bBDT|\bTaka)\s*\d", re.IGNORECASE)
_SECTION_RE = re.compile(r"\b(?:section|sec\.|s\.|ধারা)\s*\d", re.IGNORECASE)
_SRO_RE = re.compile(r"\bSRO\s*(?:No\.?\s*)?\d", re.IGNORECASE)

_YES_NO_UNKNOWN = ("yes", "no", "unknown")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _assert_no_tax_figures(test: unittest.TestCase, text: str, label: str) -> None:
    for name, pattern in (
        ("percentage", _PERCENT_RE),
        ("money amount", _MONEY_RE),
        ("statute section", _SECTION_RE),
        ("SRO number", _SRO_RE),
    ):
        match = pattern.search(text)
        test.assertIsNone(
            match,
            f"{label} contains a {name} ({match.group(0) if match else ''!r}); "
            "every figure belongs in rates-AY<year>.toml (spec §4.5).",
        )


def _fenced_csv_blocks(markdown: str) -> list[str]:
    """Every ```csv … ``` block in a Markdown file, as text."""
    return re.findall(r"```csv\n(.*?)```", markdown, flags=re.DOTALL)


def _example_csv() -> str:
    """The worked-examples block from src/templates/README.md (the one with rows)."""
    blocks = [b for b in _fenced_csv_blocks(_read(TEMPLATES_README)) if b.count("\n") > 1]
    if not blocks:
        raise AssertionError("README.md has no ```csv block with example rows")
    return blocks[0]


def _write_books(root: Path, *, journal_text: str | None = None) -> Path:
    """Materialise a books/ directory from the templates (fiscal year pinned for the test)."""
    root.mkdir(parents=True, exist_ok=True)
    shutil.copy(ACCOUNTS_TOML, root / "accounts.toml")
    config_text = _read(CONFIG_TOML)
    assert '# fiscal_year_start = "MM-DD"' in config_text
    # The template deliberately leaves the income year blank.  A period is needed for the
    # date-window check, so the TEST pins one; the shipped file does not.
    config_text = config_text.replace('# fiscal_year_start = "MM-DD"', 'fiscal_year_start = "07-01"')
    # Likewise the assessment year: validate.py rightly warns when it is blank, and the
    # template leaves it blank on purpose.  The label is a period, not a rate.
    assert '# assessment_year = "YYYY-YY"' in config_text
    config_text = config_text.replace('# assessment_year = "YYYY-YY"', 'assessment_year = "2026-27"')
    (root / "config.toml").write_text(config_text, encoding="utf-8")
    (root / "journal").mkdir(exist_ok=True)
    if journal_text is not None:
        (root / "journal" / "2026-07.csv").write_text(journal_text, encoding="utf-8")
    return root


# ======================================================================================
# accounts.toml
# ======================================================================================


class TestAccountsTemplate(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = _read(ACCOUNTS_TOML)
        cls.chart = tb.ChartOfAccounts.from_toml_path(ACCOUNTS_TOML)
        cls.raw = tomllib.loads(cls.text)

    def test_loads_through_the_engine_and_is_a_real_chart(self):
        self.assertGreaterEqual(len(self.chart), 100, "a starter chart, not a stub")
        self.assertEqual(len(self.raw["account"]), len(self.chart), "no duplicate codes")

    def test_every_account_has_bangla_name_and_a_description(self):
        for account in self.chart:
            with self.subTest(code=account.code):
                self.assertTrue(account.name_bn, f"{account.code} has no name_bn")
                self.assertTrue(account.description, f"{account.code} has no description")
                self.assertNotIn('"', account.description)
                # One plain sentence: an owner should not need to scroll.
                self.assertLess(len(account.description), 360, account.code)

    def test_only_allowed_keys_are_used(self):
        allowed = {"code", "name", "name_bn", "type", "normal", "description", "role", "tags"}
        for item in self.raw["account"]:
            self.assertLessEqual(set(item), allowed, item.get("code"))

    def test_all_ten_required_roles_present_exactly_once(self):
        self.assertEqual(self.chart.missing_roles(), [])
        for role in tb.REQUIRED_ROLES:
            with self.subTest(role=role):
                account = self.chart.account_for_role(role)  # raises if absent or ambiguous
                self.assertTrue(account.code.startswith("9"), f"{role} sits outside 9xxx")

    def test_required_role_names_are_the_spec_names(self):
        expected = {
            tb.ROLE_VAT_INPUT: ("VAT Input", "asset"),
            tb.ROLE_VAT_OUTPUT: ("VAT Output Payable", "liability"),
            tb.ROLE_TDS_RECEIVABLE: ("TDS Receivable", "asset"),
            tb.ROLE_TDS_PAYABLE: ("TDS Payable", "liability"),
            tb.ROLE_VDS_PAYABLE: ("VDS Payable", "liability"),
            tb.ROLE_ADVANCE_INCOME_TAX: ("Advance Income Tax", "asset"),
            tb.ROLE_PROVIDENT_FUND_PAYABLE: ("Provident Fund Payable", "liability"),
            tb.ROLE_GRATUITY_PROVISION: ("Gratuity Provision", "liability"),
            tb.ROLE_WPPF_PAYABLE: ("WPPF Payable", "liability"),
            tb.ROLE_SUPPLEMENTARY_DUTY_PAYABLE: ("Supplementary Duty Payable", "liability"),
        }
        self.assertEqual(set(expected), set(tb.REQUIRED_ROLES))
        for role, (name_fragment, acct_type) in expected.items():
            with self.subTest(role=role):
                account = self.chart.account_for_role(role)
                self.assertIn(name_fragment, account.name)
                self.assertEqual(account.type, acct_type)
                self.assertTrue(account.name_bn)

    def test_codes_are_four_digits_sorted_and_inside_their_blocks(self):
        self.assertEqual(self.chart.code_format_warnings(), [])
        self.assertEqual(self.chart.block_warnings(), [])
        codes = self.chart.codes()
        self.assertEqual(codes, sorted(codes), "keep the file in code order")
        for code in codes:
            self.assertRegex(code, r"^[1-9]\d{3}$")
            self.assertIsNotNone(tb.block_for_code(code))

    def test_every_block_is_populated(self):
        for digit in "123456789":
            with self.subTest(block=f"{digit}xxx"):
                self.assertTrue(self.chart.by_block(digit), f"block {digit}xxx is empty")

    def test_normal_balance_follows_type(self):
        for account in self.chart:
            self.assertEqual(account.normal, tb.NORMAL_BALANCE[account.type], account.code)

    def test_contra_accounts_are_tagged(self):
        contra = {a.code for a in self.chart if "contra" in a.tags}
        self.assertTrue({"1290", "1690", "1790", "3300", "4190", "5190"} <= contra, contra)
        for code in sorted(contra):
            with self.subTest(code=code):
                self.assertIn("balance", self.chart.get(code).description.lower())

    def test_no_account_is_shipped_inactive(self):
        for account in self.chart:
            for tag in account.tags:
                self.assertNotIn(tag.lower(), validate_mod.INACTIVE_TAGS, account.code)

    def test_money_control_and_suspense_tags(self):
        self.assertIn("cash", self.chart.get("1100").tags)
        self.assertIn("bank", self.chart.get("1150").tags)
        self.assertIn("mfs", self.chart.get("1160").tags)
        self.assertIn("control", self.chart.get("1200").tags)
        self.assertIn("control", self.chart.get("2100").tags)
        self.assertIn("suspense", self.chart.get("2900").tags)
        self.assertIn("owner", self.chart.get("3300").tags)

    def test_tally_era_aliases_map_to_one_account(self):
        self.assertEqual([a.code for a in self.chart.by_tag("sundry-debtors")], ["1200"])
        self.assertEqual([a.code for a in self.chart.by_tag("sundry-creditors")], ["2100"])
        duties = self.chart.by_tag("duties-and-taxes")
        self.assertTrue(duties)
        self.assertTrue(all(a.code.startswith("9") for a in duties))

    def test_validate_recognises_the_roleless_tax_controls(self):
        # 9120 (VDS deducted by customers) and 9325 (salary TDS) carry no `role` but must
        # still satisfy validate.py's "control account present" check for their tag kind.
        self.assertTrue(validate_mod._account_matches_kind(self.chart.get("9120"), tb.TAG_VDS))
        self.assertTrue(validate_mod._account_matches_kind(self.chart.get("9325"), tb.TAG_TDS))
        # Non-rebateable input VAT must NOT pass as the rebate control: a VAT:IN tag on it
        # would be claiming a rebate the law does not allow.
        self.assertFalse(validate_mod._account_matches_kind(self.chart.get("9105"), tb.TAG_VAT_IN))

    def test_vat_side_never_nets(self):
        vat_in = self.chart.account_for_role(tb.ROLE_VAT_INPUT)
        vat_out = self.chart.account_for_role(tb.ROLE_VAT_OUTPUT)
        self.assertNotEqual(vat_in.code, vat_out.code)
        self.assertEqual((vat_in.type, vat_out.type), ("asset", "liability"))

    def test_bangla_english_pairs_on_statutory_accounts(self):
        self.assertIn("মূসক", self.chart.get("9100").name_bn)
        self.assertIn("মূসক", self.chart.get("9200").name_bn)
        self.assertIn("উৎসে কর্তিত", self.chart.get("9320").name_bn)
        self.assertIn("সম্পূরক শুল্ক", self.chart.get("9210").name_bn)
        self.assertIn("ভবিষ্য তহবিল", self.chart.get("9400").name_bn)

    def test_no_tax_figure_anywhere_in_the_file(self):
        _assert_no_tax_figures(self, self.text, "accounts.toml")

    def test_attribution_present(self):
        self.assertIn("TICON SYSTEM LTD", self.text)
        self.assertIn("ticonsys.com", self.text)

    def test_init_books_uses_this_template_not_its_fallback(self):
        text, source = init_books._accounts_text(TEMPLATES_DIR)
        self.assertEqual(source, str(ACCOUNTS_TOML))
        self.assertEqual(text, self.text)


# ======================================================================================
# config.toml
# ======================================================================================


class TestConfigTemplate(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = _read(CONFIG_TOML)
        cls.config = tb.Config.from_toml_path(CONFIG_TOML)
        cls.raw = tomllib.loads(cls.text)

    def test_loads_through_the_engine(self):
        cfg = self.config
        self.assertEqual(cfg.currency, tb.CURRENCY_CODE)
        self.assertEqual(cfg.business_name, "Example Traders")
        self.assertTrue(cfg.business_name_bn)
        self.assertEqual(cfg.business_type, "proprietorship")
        self.assertEqual(cfg.language, "en")
        self.assertEqual(cfg.grouping, tb.GROUPING_BD)
        self.assertEqual(cfg.digits, "latin")
        self.assertEqual(cfg.accounts_file, tb.ACCOUNTS_FILENAME)
        self.assertEqual(cfg.journal_dirname, tb.JOURNAL_DIRNAME)

    def test_statutory_fields_are_left_for_the_user(self):
        # Spec §6.2: TakaBooks never guesses an income year or assessment year.
        self.assertIsNone(self.config.fiscal_year_start)
        self.assertIsNone(self.config.assessment_year)
        self.assertIsNone(self.config.rates_file)
        with self.assertRaises(tb.ConfigError):
            self.config.require_fiscal_year_start()
        with self.assertRaises(tb.ConfigError):
            self.config.require_assessment_year()
        # …but the placeholders are visible so the user knows where they go.
        self.assertIn('# fiscal_year_start = "MM-DD"', self.text)
        self.assertIn('# fiscal_year_end = "MM-DD"', self.text)
        self.assertIn('# assessment_year = "YYYY-YY"', self.text)
        self.assertIn("# rates_file =", self.text)

    def test_identifiers_are_blank_placeholders(self):
        self.assertEqual(self.config.tin, "")
        self.assertEqual(self.config.bin, "")
        self.assertEqual(self.raw["business"].get("trade_licence"), "")
        self.assertEqual(self.raw["business"].get("registration_no"), "")
        self.assertNotRegex(self.config.business_name, r"\d")

    def test_compliance_values_are_valid_choices(self):
        cfg = self.config
        self.assertIn(cfg.get("compliance.vat_registered"), init_books.VAT_REGISTRATION_CHOICES)
        self.assertIn(cfg.get("compliance.city_tier"), init_books.CITY_TIERS)
        self.assertIn(cfg.get("compliance.turnover_tax_enlisted"), _YES_NO_UNKNOWN)
        self.assertIn(cfg.get("compliance.withholding_entity"), _YES_NO_UNKNOWN)
        self.assertIn(cfg.get("compliance.accounting_basis"), ("accrual", "cash"))
        # Honest defaults: nothing is asserted about a business we know nothing about.
        self.assertEqual(cfg.get("compliance.vat_registered"), "unknown")
        self.assertEqual(cfg.get("compliance.city_tier"), "unspecified")

    def test_init_books_inherits_only_non_statutory_defaults_and_warns_about_nothing(self):
        warnings: list[str] = []
        defaults = init_books._template_defaults(TEMPLATES_DIR, warnings)
        self.assertEqual(warnings, [], "the template must not carry a statutory value")
        self.assertEqual(defaults["source"], str(CONFIG_TOML))
        self.assertEqual(defaults["currency"], tb.CURRENCY_CODE)
        self.assertEqual(defaults["rates_file"], "")
        self.assertEqual(defaults["grouping"], tb.GROUPING_BD)
        self.assertEqual(defaults["language"], "en")
        self.assertEqual(defaults["digits"], "latin")

    def test_every_key_is_explained_by_a_comment(self):
        """A non-accountant fills this in: each key has a comment immediately above it."""
        lines = self.text.split("\n")
        for index, line in enumerate(lines):
            if not re.match(r"^\s*#?\s*[a-z_]+\s*=", line):
                continue
            key = line.strip().lstrip("#").strip().split("=")[0].strip()
            # Walk upwards through the paragraph this key belongs to.
            cursor = index - 1
            commented = False
            while cursor >= 0 and lines[cursor].strip() and not lines[cursor].startswith("["):
                if lines[cursor].lstrip().startswith("#") and "=" not in lines[cursor].split("#", 1)[1][:1]:
                    commented = True
                cursor -= 1
            self.assertTrue(commented, f"config.toml key {key!r} (line {index + 1}) has no explanatory comment")

    def test_no_tax_figure_anywhere_in_the_file(self):
        _assert_no_tax_figures(self, self.text, "config.toml")

    def test_currency_is_bdt_only(self):
        self.assertEqual(self.raw["books"]["currency"], "BDT")


# ======================================================================================
# journal-header.csv
# ======================================================================================


class TestJournalHeaderTemplate(unittest.TestCase):
    def test_is_exactly_the_schema_header(self):
        data = JOURNAL_HEADER_CSV.read_bytes()
        self.assertFalse(data.startswith(b"\xef\xbb\xbf"), "no BOM")
        self.assertTrue(data.endswith(b"\n"), "ends with a newline")
        text = data.decode("utf-8")
        self.assertEqual(text.strip(), tb.JOURNAL_HEADER)
        self.assertEqual(text.count("\n"), 1, "the header row and nothing else")
        self.assertEqual(text.strip().split(","), list(tb.JOURNAL_COLUMNS))

    def test_init_books_accepts_it(self):
        # init_books.py raises JournalError on any deviation from the schema.
        self.assertEqual(init_books._journal_header_text(TEMPLATES_DIR), tb.JOURNAL_HEADER + "\n")

    def test_memo_is_last_so_commas_survive(self):
        self.assertEqual(tb.JOURNAL_COLUMNS[-1], "memo")


# ======================================================================================
# README.md worked examples
# ======================================================================================


class TestReadmeWorkedExamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.readme = _read(TEMPLATES_README)
        cls.csv_text = _example_csv()
        cls.tmp = Path(tempfile.mkdtemp(prefix="takabooks-templates-"))
        cls.books = _write_books(cls.tmp / "books", journal_text=cls.csv_text)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_header_row_in_readme_is_the_schema(self):
        first_line = self.csv_text.split("\n", 1)[0]
        self.assertEqual(first_line, tb.JOURNAL_HEADER)
        header_only = [b for b in _fenced_csv_blocks(self.readme) if b.count("\n") == 1]
        self.assertTrue(header_only, "README shows the bare header too")
        self.assertEqual(header_only[0].strip(), tb.JOURNAL_HEADER)

    def test_examples_load_balanced_through_the_engine(self):
        ledger = tb.Ledger.load(self.books)  # require_balanced=True: raises if any entry is off
        self.assertTrue(ledger.is_balanced())
        self.assertEqual(ledger.entry_ids(), ["EX-0001", "EX-0002", "EX-0003"])
        self.assertEqual(len(ledger), 9)
        self.assertEqual(ledger.unknown_accounts(), [])

    def test_examples_cover_sale_purchase_and_tds_payment(self):
        ledger = tb.Ledger.load(self.books)
        kinds = {eid: {t.kind for t in ledger.entry(eid).tax_tags} for eid in ledger.entry_ids()}
        self.assertEqual(kinds["EX-0001"], {tb.TAG_NONE, tb.TAG_VAT_OUT})
        self.assertEqual(kinds["EX-0002"], {tb.TAG_NONE, tb.TAG_VAT_IN})
        self.assertEqual(kinds["EX-0003"], {tb.TAG_NONE, tb.TAG_TDS})
        # Cash sale hits cash; purchase hits payable; rent goes out through the bank.
        self.assertIn("1100", {p.account for p in ledger.entry("EX-0001").postings})
        self.assertIn("2100", {p.account for p in ledger.entry("EX-0002").postings})
        self.assertIn("1150", {p.account for p in ledger.entry("EX-0003").postings})

    def test_tax_lines_equal_value_times_placeholder_rate(self):
        ledger = tb.Ledger.load(self.books)
        checks = {
            "EX-0001": ("4100", "9200", tb.TAG_VAT_OUT),
            "EX-0002": ("5100", "9100", tb.TAG_VAT_IN),
            "EX-0003": ("6200", "9320", tb.TAG_TDS),
        }
        for entry_id, (value_code, tax_code, kind) in checks.items():
            with self.subTest(entry=entry_id):
                entry = ledger.entry(entry_id)
                value = [p for p in entry.postings if p.account == value_code]
                tax = [p for p in entry.postings if p.account == tax_code]
                self.assertEqual(len(value), 1)
                self.assertEqual(len(tax), 1)
                self.assertEqual(value[0].tax_tag.kind, kind)
                self.assertEqual(tax[0].tax_tag.kind, kind)
                self.assertEqual(value[0].tax_tag.rate, tax[0].tax_tag.rate)
                value_amount = value[0].debit if value[0].debit else value[0].credit
                tax_amount = tax[0].debit if tax[0].debit else tax[0].credit
                self.assertEqual(tax_amount, value_amount.percent(value[0].tax_tag.rate))

    def test_examples_are_loudly_fake(self):
        ledger = tb.Ledger.load(self.books)
        for posting in ledger:
            with self.subTest(line=posting.source_line):
                self.assertTrue(posting.entry_id.startswith("EX-"))
                self.assertTrue(posting.description.startswith("EXAMPLE"))
                self.assertTrue(posting.memo.startswith("EXAMPLE ONLY"))
                self.assertTrue(posting.doc_ref, "doc_ref is never blank, even in an example")
                self.assertIn(posting.party, ("Walk-in customer", "Example Supplier Ltd", "Example Landlord"))
                if posting.tax_tag.kind == tb.TAG_TDS:
                    self.assertEqual(posting.tax_tag.section, "0XX", "placeholder section, not a statute")
                if posting.tax_tag.rate is not None:
                    self.assertIn(posting.tax_tag.rate, (Decimal(10), Decimal(5)))

    def test_examples_come_back_clean_from_validate(self):
        report = validate_mod.validate_books(self.books)
        self.assertTrue(
            report.is_clean,
            "validate.py findings:\n" + "\n".join(f.to_dict().get("message", str(f)) for f in report.findings)
            + "\nnotes:\n" + "\n".join(report.notes),
        )
        self.assertEqual(report.entries, 3)
        self.assertEqual(report.exit_code(), 0)

    def test_readme_explains_why_the_csv_holds_only_the_header(self):
        self.assertIn("cross-checks this file", self.readme)
        self.assertIn("placeholder", self.readme.lower())
        self.assertIn("rates-AY<year>.toml", self.readme)
        self.assertIn("TICON SYSTEM LTD", self.readme)


# ======================================================================================
# init_books.py end-to-end with the shipped templates
# ======================================================================================


class TestInitBooksScaffoldsFromTemplates(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = Path(tempfile.mkdtemp(prefix="takabooks-scaffold-"))
        cls.books = cls.tmp / "books"
        cls.result = subprocess.run(
            [
                sys.executable,
                str(ENGINE_DIR / "init_books.py"),
                "--books", str(cls.books),
                "--templates", str(TEMPLATES_DIR),
                "--name", "Test Traders",
                "--name-bn", "টেস্ট ট্রেডার্স",
                "--fiscal-year-start", "07-01",
                "--assessment-year", "2026-27",
                "--start-month", "2026-07",
                "--json",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_scaffold_succeeds(self):
        self.assertEqual(self.result.returncode, 0, self.result.stdout + self.result.stderr)
        payload = json.loads(self.result.stdout)
        self.assertEqual(payload["templates_dir"], str(TEMPLATES_DIR))
        self.assertTrue((self.books / "config.toml").is_file())
        self.assertTrue((self.books / "accounts.toml").is_file())
        journal = self.books / "journal" / "2026-07.csv"
        self.assertTrue(journal.is_file())
        self.assertEqual(_read(journal), tb.JOURNAL_HEADER + "\n")

    def test_scaffolded_chart_is_the_template_chart(self):
        scaffolded = tb.ChartOfAccounts.from_toml_path(self.books / "accounts.toml")
        template = tb.ChartOfAccounts.from_toml_path(ACCOUNTS_TOML)
        self.assertEqual(scaffolded.codes(), template.codes())
        self.assertEqual(scaffolded.missing_roles(), [])

    def test_scaffolded_books_validate_clean_with_the_examples(self):
        self.assertEqual(self.result.returncode, 0, self.result.stderr)
        (self.books / "journal" / "2026-07.csv").write_text(_example_csv(), encoding="utf-8")
        report = validate_mod.validate_books(self.books)
        self.assertTrue(
            report.is_clean,
            "validate.py findings:\n" + "\n".join(str(f.to_dict()) for f in report.findings),
        )
        ledger = tb.Ledger.load(self.books)
        self.assertEqual(len(ledger.entry_ids()), 3)


# ======================================================================================
# .github community files
# ======================================================================================


_ISSUE_FORMS = ("bug_report.yml", "feature_request.yml", "tax-rule-update.yml")
_FORM_TYPES = {"markdown", "input", "textarea", "dropdown", "checkboxes"}


class TestGithubCommunityFiles(unittest.TestCase):
    def _form(self, name: str) -> str:
        return _read(GITHUB_DIR / "ISSUE_TEMPLATE" / name)

    def test_issue_forms_have_the_form_schema_shape(self):
        for name in _ISSUE_FORMS:
            with self.subTest(form=name):
                text = self._form(name)
                self.assertNotIn("\t", text, "YAML must not use tabs")
                self.assertRegex(text, r"(?m)^name: ")
                self.assertRegex(text, r"(?m)^description: ")
                self.assertRegex(text, r"(?m)^body:$")
                types = re.findall(r"(?m)^\s+- type: (\S+)", text)
                self.assertTrue(types)
                self.assertLessEqual(set(types), _FORM_TYPES)
                ids = re.findall(r"(?m)^\s+id: (\S+)", text)
                self.assertEqual(len(ids), len(set(ids)), f"duplicate ids in {name}")
                for field_id in ids:
                    self.assertRegex(field_id, r"^[A-Za-z0-9_-]+$")
                # Every form insists on fake data only.
                self.assertIn("TIN", text)
                self.assertIn("TICON SYSTEM LTD", text)

    def test_tax_rule_update_asks_for_what_keeps_the_project_current(self):
        text = self._form("tax-rule-update.yml")
        ids = set(re.findall(r"(?m)^\s+id: (\S+)", text))
        for required in ("assessment_year", "statute", "source_url", "as_of", "old_value", "new_value", "confidence"):
            self.assertIn(required, ids)
        # Those five are mandatory fields, not optional ones.
        for field_id in ("assessment_year", "statute", "source_url", "as_of", "old_value", "new_value"):
            block = text.split(f"id: {field_id}", 1)[1].split("- type:", 1)[0]
            self.assertIn("required: true", block, f"{field_id} must be required")
        self.assertIn("verified", text)
        self.assertIn("nbr.gov.bd", text)
        self.assertIn("rates-AY", text)
        self.assertIn("করবর্ষ", text)

    def test_bug_report_redirects_tax_figures_to_the_update_form(self):
        text = self._form("bug_report.yml")
        self.assertIn("Tax rule update", text)
        self.assertIn("python3 --version", text)

    def test_issue_template_config_disables_blank_issues(self):
        text = _read(GITHUB_DIR / "ISSUE_TEMPLATE" / "config.yml")
        self.assertIn("blank_issues_enabled: false", text)
        self.assertIn("contact_links:", text)
        self.assertIn("https://github.com/bemoshiur/TakaBooks/discussions", text)
        self.assertIn("https://ticonsys.com", text)
        self.assertNotIn("\t", text)

    def test_pull_request_template_carries_the_hard_rules(self):
        text = _read(GITHUB_DIR / "PULL_REQUEST_TEMPLATE.md")
        for needle in (
            "python3 -m unittest discover tests",
            "python3 build/build.py --check",
            "Standard library only",
            "paisa",
            "rates-AY<year>.toml",
            "verified = true",
            "TICON SYSTEM LTD",
            "মূসক",
        ):
            self.assertIn(needle, text)

    def test_funding_is_minimal_and_points_at_the_maintainer(self):
        text = _read(GITHUB_DIR / "FUNDING.yml")
        self.assertIn("github: [bemoshiur]", text)
        self.assertNotIn("\t", text)

    def test_dependabot_covers_actions_and_npm_but_never_pip(self):
        text = _read(GITHUB_DIR / "dependabot.yml")
        self.assertIn("version: 2", text)
        self.assertIn('package-ecosystem: "github-actions"', text)
        self.assertIn('package-ecosystem: "npm"', text)
        self.assertNotIn('package-ecosystem: "pip"', text)
        self.assertNotIn("\t", text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
