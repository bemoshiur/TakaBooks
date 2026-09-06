"""Tests for the TakaBooks build (``build/build.py``).

Run with::

    python3 -m unittest discover tests

What is covered, per spec §5 and §7:

* every target emits the files the spec, the CI workflow and the npm installer expect;
* the ChatGPT 8,000-character cap and the knowledge-file caps are *actually enforced* —
  an over-cap build exits non-zero and writes nothing;
* the Claude Skill frontmatter satisfies the strictest published limit of every surface,
  and the zip has the skill folder at its root;
* the build is deterministic (two builds, two directories, identical bytes — zip included)
  and idempotent (a rebuild replaces stale output);
* ``--check`` writes nothing, ``--clean`` wipes, ``--all`` builds everything, ``--strict``
  turns a missing source into a failure.

Two source trees are exercised.  A synthetic fixture (no real tax figure anywhere in it)
drives the cap and behaviour tests, so they stay green no matter what ``src/`` says today.
A copy of the real ``src/`` drives the "does the repository actually build" tests, which
is the release gate the spec asks for.

TakaBooks — Moshiur Rahman (@bemoshiur) · TICON SYSTEM LTD — https://ticonsys.com
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import re
import shutil
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_PY = REPO_ROOT / "build" / "build.py"
SRC_DIR = REPO_ROOT / "src"


def _load_build_module():
    """Import ``build/build.py`` under a private name.

    ``build/`` is not a package and "build" is also the name of a PyPI project, so a plain
    ``import build`` could pick up the wrong thing on a developer machine.  The module is
    registered in ``sys.modules`` before execution because ``@dataclass`` resolves
    ``from __future__ import annotations`` strings through ``sys.modules[__module__]``.
    """
    spec = importlib.util.spec_from_file_location("takabooks_build", BUILD_PY)
    module = importlib.util.module_from_spec(spec)
    sys.modules["takabooks_build"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


build = _load_build_module()

SKILL = build.SKILL_NAME  # "bd-bookkeeping-tax"


# ======================================================================================
# Synthetic source tree — contains NO real Bangladeshi tax figure, by construction
# ======================================================================================

FIXTURE_AY = "2099-00"

FIXTURE_RATES_TOML = f"""# synthetic fixture — every value is an obvious placeholder
[meta]
assessment_year = "{FIXTURE_AY}"
status = "placeholder"
placeholder = true
verified = false

[income_tax.fixture_node]
value = "PLACEHOLDER"
verified = false
placeholder = true
source = "https://example.invalid/not-a-real-source"
as_of = "2099-01-01"
note = "Fixture only. Contains ``backticks`` on purpose."
"""

DEFAULT_CORE = {
    "00-identity.md": (
        "# Fixture identity\n\nWho this is. মূসক / VAT and উৎসে কর কর্তন / TDS.\n\n"
        "## Disclaimer\n\n> Not professional advice.\n"
    ),
    "10-workflow.md": (
        "# Fixture workflow\n\n## Run the tools\n\n```\n"
        "python3 post.py --books ./books --json\n# a comment that is not a heading\n```\n"
    ),
    "20-bookkeeping.md": "# Fixture bookkeeping\n\nDebit / ডেবিট and credit / ক্রেডিট.\n",
    "30-tax-overview.md": (
        "# Fixture routing\n\n| Question | Load |\n|---|---|\n| VAT | `vat-mushak.md` |\n"
    ),
}


def default_references() -> dict[str, str]:
    refs: dict[str, str] = {}
    for stem in build.REFERENCE_ORDER:
        refs[f"{stem}.md"] = (
            f"# {stem} fixture\n\n"
            "See [VAT](vat-mushak.md) and [NBR](https://nbr.gov.bd) and "
            "[glossary](../references/glossary-bn-en.md#term).\n\n"
            "## Detail\n\nFixture text only.\n"
        )
    return refs


DEFAULT_ENGINE = {
    "takabooks.py": '"""Shared library fixture."""\n\nMIN_PYTHON = (3, 11)\n',
    "init_books.py": '"""Scaffold fixture."""\n',
    "post.py": '"""Post fixture."""\n',
    "report.py": '"""Report fixture."""\n',
    "vat.py": '"""VAT fixture."""\n',
    "tax.py": '"""Tax fixture."""\n',
    "validate.py": '"""Validate fixture."""\n',
    "rates.py": '"""TakaBooks — versioned rates loader fixture.\n\nSecond paragraph.\n"""\n',
}

DEFAULT_TEMPLATES = {
    "accounts.toml": (
        '[[account]]\ncode = "1100"\nname = "Cash in Hand"\nname_bn = "হাতে নগদ"\n'
        'type = "asset"\nnormal = "debit"\n'
    ),
    "config.toml": 'business_name = "Fixture Traders"\n',
    "journal-header.csv": (
        "date,entry_id,description,account,debit,credit,party,doc_ref,tax_tag,memo\n"
    ),
}


def make_repo(
    root: Path,
    *,
    core: dict[str, str] | None = None,
    references: dict[str, str] | None = None,
    engine: dict[str, str] | None = None,
    templates: dict[str, str] | None = None,
    rates: str | None = FIXTURE_RATES_TOML,
) -> Path:
    """Write a synthetic ``src/`` under ``root`` and return ``root``."""
    layout = {
        "core": DEFAULT_CORE if core is None else core,
        "references": default_references() if references is None else references,
        "engine": DEFAULT_ENGINE if engine is None else engine,
        "templates": DEFAULT_TEMPLATES if templates is None else templates,
    }
    for directory, files in layout.items():
        (root / "src" / directory).mkdir(parents=True, exist_ok=True)
        for name, text in files.items():
            (root / "src" / directory / name).write_text(text, encoding="utf-8")
    (root / "src" / "data").mkdir(parents=True, exist_ok=True)
    if rates is not None:
        (root / "src" / "data" / f"rates-AY{FIXTURE_AY}.toml").write_text(
            rates, encoding="utf-8"
        )
    return root


def read_outputs(root: Path) -> dict[str, bytes]:
    """Every build output under ``root`` as ``{relative path: bytes}``."""
    outputs: dict[str, bytes] = {}
    dist = root / "dist"
    if dist.is_dir():
        for path in sorted(dist.rglob("*")):
            if path.is_file():
                outputs[path.relative_to(root).as_posix()] = path.read_bytes()
    agents = root / "AGENTS.md"
    if agents.is_file():
        outputs["AGENTS.md"] = agents.read_bytes()
    return outputs


def run_main(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = build.main(argv)
    return code, out.getvalue(), err.getvalue()


def parse_frontmatter(text: str) -> dict[str, object]:
    """Parse the tiny YAML subset the build emits: quoted scalars and one nested map."""
    lines = text.split("\n")
    assert lines[0] == "---", "frontmatter must open on the very first line"
    close = lines.index("---", 1)
    data: dict[str, object] = {}
    current_map: dict[str, str] | None = None
    for line in lines[1:close]:
        if line.startswith("  "):
            assert current_map is not None, line
            key, _, value = line.strip().partition(": ")
            current_map[key] = json.loads(value)
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if value == "":
            current_map = {}
            data[key] = current_map
        else:
            current_map = None
            data[key] = json.loads(value)
    return data


class FixtureCase(unittest.TestCase):
    """A fresh temporary directory per test, cleaned up afterwards."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def repo(self, name: str = "repo", **overrides) -> Path:
        return make_repo(self.tmp / name, **overrides)


# ======================================================================================
# Constants and helpers
# ======================================================================================


class TestConstants(unittest.TestCase):
    def test_python_floor_is_3_11(self):
        self.assertEqual(build.MIN_PYTHON, (3, 11))

    def test_targets_match_the_spec(self):
        self.assertEqual(
            build.TARGETS, ("claude-skill", "chatgpt", "gemini", "universal", "agents-md")
        )

    def test_hard_caps_are_the_researched_numbers(self):
        self.assertEqual(build.CHATGPT_INSTRUCTIONS_MAX_CHARS, 8000)
        self.assertEqual(build.CHATGPT_KNOWLEDGE_MAX_FILES, 20)
        self.assertEqual(build.GEMINI_KNOWLEDGE_MAX_FILES, 10)
        self.assertEqual(build.SKILL_DESCRIPTION_MAX_CHARS, 200)
        self.assertEqual(build.SKILL_NAME_MAX_CHARS, 64)
        self.assertEqual(build.AGENTS_MD_MAX_BYTES, 32 * 1024)

    def test_skill_name_is_valid_everywhere(self):
        self.assertEqual(SKILL, "bd-bookkeeping-tax")
        self.assertRegex(SKILL, build.SKILL_NAME_RE)
        self.assertLessEqual(len(SKILL), 64)
        for word in ("claude", "anthropic"):
            self.assertNotIn(word, SKILL)

    def test_skill_description_fits_and_carries_trigger_terms(self):
        description = build.SKILL_DESCRIPTION
        self.assertLessEqual(len(description), 200, "claude.ai upload UI cap")
        self.assertNotRegex(description, r"<[^>]+>", "no XML tags allowed")
        lowered = description.lower()
        for term in (
            "bangladesh", "bdt", "taka", "vat", "মূসক", "mushak", "tds", "nbr",
            "tin", "bin", "income tax", "bookkeeping",
        ):
            self.assertIn(term, lowered, f"trigger term {term!r} missing")

    def test_compatibility_fits(self):
        self.assertLessEqual(len(build.SKILL_COMPATIBILITY), 500)
        self.assertIn("3.11", build.SKILL_COMPATIBILITY)

    def test_attribution_credits_ticon_sys(self):
        self.assertIn("TICON SYSTEM LTD", build.ATTRIBUTION)
        self.assertIn("https://ticonsys.com", build.ATTRIBUTION)
        self.assertIn("@bemoshiur", build.ATTRIBUTION)
        self.assertIn("MIT", build.ATTRIBUTION)


class TestTextHelpers(unittest.TestCase):
    def test_normalise_strips_bom_and_crlf(self):
        self.assertEqual(build.normalise("﻿a\r\nb\r\n\r\n"), "a\nb\n")
        self.assertEqual(build.normalise("x"), "x\n")

    def test_slugify_keeps_bangla_vowel_signs(self):
        slug = build.slugify("6. VAT / মূসক and the Mushak forms")
        self.assertEqual(slug, "6-vat--মূসক-and-the-mushak-forms")
        self.assertIn("মূসক", slug, "combining marks must survive or the anchor dangles")

    def test_slugify_drops_punctuation_like_github(self):
        self.assertEqual(build.slugify("12. Rates — assessment year 2026-27"),
                         "12-rates--assessment-year-2026-27")
        self.assertEqual(build.slugify("**Bold** (x) [y]: z"), "bold-x-y-z")

    def test_shift_headings_leaves_fenced_code_alone(self):
        text = "# Title\n\n```bash\n# not a heading\n```\n\n## Sub\n"
        shifted = build.shift_headings(text, 3)
        self.assertIn("### Title", shifted)
        self.assertIn("#### Sub", shifted)
        self.assertIn("\n# not a heading\n", shifted)

    def test_shift_headings_clamps_to_six(self):
        self.assertIn("###### Deep", build.shift_headings("##### Deep\n", 6))

    def test_fenced_outgrows_inner_backticks(self):
        block = build.fenced("a ```` b", "toml")
        self.assertTrue(block.startswith("`````toml\n"))
        self.assertTrue(block.endswith("\n`````"))

    def test_rewrite_links_to_anchors(self):
        anchors = {"vat-mushak.md": "6-vat"}
        text = (
            "[VAT](references/vat-mushak.md) [same](vat-mushak.md#x) "
            "[NBR](https://nbr.gov.bd) [local](#here) [other](payroll.md)\n"
            "```\n[VAT](vat-mushak.md)\n```\n"
        )
        out = build.rewrite_links_to_anchors(text, anchors)
        self.assertEqual(out.count("(#6-vat)"), 2)
        self.assertIn("(https://nbr.gov.bd)", out)
        self.assertIn("(#here)", out)
        self.assertIn("(payroll.md)", out, "unknown targets are left alone")
        self.assertIn("```\n[VAT](vat-mushak.md)\n```", out, "fenced code is untouched")

    def test_knowledge_only_helpers(self):
        text = "keep\n<!-- knowledge-only -->\nsecret\n<!-- /knowledge-only -->\nend\n"
        self.assertEqual(build.strip_knowledge_only(text), "keep\nend\n")
        self.assertEqual(build.drop_knowledge_only_markers(text), "keep\nsecret\nend\n")

    def test_yaml_double_quote(self):
        self.assertEqual(build.yaml_double_quote('a "b" \\ c\nd'), '"a \\"b\\" \\\\ c\\nd"')
        self.assertEqual(json.loads(build.yaml_double_quote("মূসক: VAT")), "মূসক: VAT")

    def test_estimate_tokens_is_bytes_over_four_rounded_up(self):
        self.assertEqual(build.estimate_tokens("abcd"), 1)
        self.assertEqual(build.estimate_tokens("abcde"), 2)
        self.assertEqual(build.estimate_tokens("মূ"), 2)  # 6 bytes

    def test_module_purpose(self):
        self.assertEqual(build.module_purpose("tax.py", "whatever"), build.ENGINE_PURPOSE["tax.py"])
        self.assertEqual(
            build.module_purpose("rates.py", DEFAULT_ENGINE["rates.py"]),
            "Versioned rates loader fixture",
        )
        self.assertEqual(
            build.module_purpose("broken.py", "def ("),
            "Supporting module for the engine scripts.",
        )

    def test_resolve_targets(self):
        self.assertEqual(build.resolve_targets(None), list(build.TARGETS))
        self.assertEqual(build.resolve_targets(["all", "chatgpt"]), list(build.TARGETS))
        self.assertEqual(build.resolve_targets(["none"]), [])
        self.assertEqual(
            build.resolve_targets(["gemini", "chatgpt", "gemini"]), ["chatgpt", "gemini"]
        )
        with self.assertRaises(build.BuildError):
            build.resolve_targets(["none", "chatgpt"])


# ======================================================================================
# Source discovery
# ======================================================================================


class TestSourceTree(FixtureCase):
    def test_loads_every_directory_in_declared_order(self):
        tree = build.SourceTree.load(self.repo())
        self.assertEqual(list(tree.core), list(DEFAULT_CORE))
        self.assertEqual(
            list(tree.references), [f"{stem}.md" for stem in build.REFERENCE_ORDER]
        )
        self.assertEqual(list(tree.engine)[:7], [f"{s}.py" for s in build.ENGINE_ORDER])
        self.assertEqual(list(tree.engine)[7:], ["rates.py"], "extras follow, alphabetical")
        self.assertEqual(sorted(tree.templates), sorted(DEFAULT_TEMPLATES))
        self.assertEqual(tree.rates_filename, f"rates-AY{FIXTURE_AY}.toml")
        self.assertEqual(tree.missing, [])

    def test_assessment_year_comes_from_the_rates_file_not_a_guess(self):
        tree = build.SourceTree.load(self.repo())
        self.assertEqual(tree.assessment_year, FIXTURE_AY)
        root = self.repo("nometa", rates='[x]\nvalue = "PLACEHOLDER"\n')
        self.assertEqual(build.SourceTree.load(root).assessment_year, FIXTURE_AY,
                         "falls back to the year in the file name")
        self.assertEqual(build.SourceTree.load(self.repo("norates", rates=None)).assessment_year,
                         "unknown")

    def test_missing_files_are_reported(self):
        engine = {k: v for k, v in DEFAULT_ENGINE.items() if k != "post.py"}
        tree = build.SourceTree.load(self.repo(engine=engine, templates={}, rates=None))
        self.assertIn("src/engine/post.py", tree.missing)
        self.assertIn("src/templates/", tree.missing)
        self.assertIn("src/data/rates-AY<year>.toml", tree.missing)

    def test_no_src_is_a_build_error(self):
        with self.assertRaises(build.BuildError):
            build.SourceTree.load(self.tmp / "empty")

    def test_non_utf8_source_is_a_build_error(self):
        root = self.repo()
        (root / "src" / "references" / "payroll.md").write_bytes(b"# \xff\xfe bad\n")
        with self.assertRaises(build.BuildError):
            build.SourceTree.load(root)

    def test_build_id_depends_on_content_only(self):
        a = build.SourceTree.load(self.repo("a")).build_id()
        b = build.SourceTree.load(self.repo("b")).build_id()
        self.assertEqual(a, b, "same bytes, different directories, same id")
        root = self.repo("c")
        (root / "src" / "core" / "00-identity.md").write_text("# changed\n", encoding="utf-8")
        self.assertNotEqual(a, build.SourceTree.load(root).build_id())


# ======================================================================================
# Every target emits — on the synthetic tree
# ======================================================================================


class TestAllTargetsEmit(FixtureCase):
    def setUp(self) -> None:
        super().setUp()
        self.root = self.repo()
        self.report = build.run_build(self.root, list(build.TARGETS))
        self.assertEqual(self.report.failures, [], [c.render() for c in self.report.failures])
        self.assertTrue(self.report.wrote_anything)

    def path(self, rel: str) -> Path:
        return self.root / rel

    def text(self, rel: str) -> str:
        return self.path(rel).read_text(encoding="utf-8")

    # --- claude-skill -------------------------------------------------------------------

    def test_skill_folder_layout(self):
        base = f"dist/claude-skill/{SKILL}"
        self.assertTrue(self.path(f"{base}/SKILL.md").is_file())
        for name in build.REFERENCE_ORDER:
            self.assertTrue(self.path(f"{base}/references/{name}.md").is_file(), name)
        for name in DEFAULT_ENGINE:
            self.assertTrue(self.path(f"{base}/scripts/{name}").is_file(), name)
        self.assertTrue(self.path(f"{base}/scripts/USAGE.md").is_file())
        for name in DEFAULT_TEMPLATES:
            self.assertTrue(self.path(f"{base}/templates/{name}").is_file(), name)
        self.assertTrue(self.path("dist/claude-skill/README-install.md").is_file())

    def test_skill_ships_rates_under_data_where_rates_py_looks(self):
        # rates.py resolves `<script dir>/../data/`; the core says `data/rates-AY<year>.toml`.
        rates = self.path(f"dist/claude-skill/{SKILL}/data/rates-AY{FIXTURE_AY}.toml")
        self.assertTrue(rates.is_file())
        self.assertEqual(rates.read_text(encoding="utf-8"), FIXTURE_RATES_TOML)
        self.assertFalse(self.path(f"dist/claude-skill/{SKILL}/assets").exists())

    def test_skill_scripts_are_verbatim_and_executable(self):
        for name, source in DEFAULT_ENGINE.items():
            path = self.path(f"dist/claude-skill/{SKILL}/scripts/{name}")
            self.assertEqual(path.read_text(encoding="utf-8"), source)
            self.assertTrue(path.stat().st_mode & stat.S_IXUSR, f"{name} not executable")

    def test_skill_frontmatter(self):
        text = self.text(f"dist/claude-skill/{SKILL}/SKILL.md")
        self.assertTrue(text.startswith("---\n"), "no BOM, no blank line before ---")
        data = parse_frontmatter(text)
        self.assertEqual(data["name"], SKILL)
        self.assertEqual(data["description"], build.SKILL_DESCRIPTION)
        self.assertLessEqual(len(data["description"]), 200)
        self.assertEqual(data["license"], "MIT")
        self.assertLessEqual(len(data["compatibility"]), 500)
        metadata = data["metadata"]
        self.assertEqual(metadata["author"], "TICON SYSTEM LTD")
        self.assertEqual(metadata["homepage"], "https://ticonsys.com")
        self.assertEqual(metadata["assessment_year"], FIXTURE_AY)
        self.assertEqual(set(data), {"name", "description", "license", "compatibility", "metadata"})

    def test_skill_body_is_core_plus_navigation(self):
        text = self.text(f"dist/claude-skill/{SKILL}/SKILL.md")
        body = text.split("\n---\n", 1)[1]  # everything after the frontmatter closes
        self.assertTrue(body.lstrip().startswith("# TakaBooks — Bangladeshi bookkeeping"))
        self.assertIn("## Fixture identity", body, "core H1s become H2 under the title")
        self.assertIn("Debit / ডেবিট", body)
        self.assertIn("(references/vat-mushak.md)", body)
        self.assertIn(f"(data/rates-AY{FIXTURE_AY}.toml)", body)
        self.assertIn("`scripts/validate.py`", body)
        self.assertIn("(templates/accounts.toml)", body)
        self.assertIn("(scripts/USAGE.md)", body)
        self.assertIn("TICON SYSTEM LTD", body)
        self.assertNotIn("Non-negotiable rules", body, "the build does not restate the core")
        self.assertNotIn("<!-- knowledge-only -->", body)
        self.assertIn(f"assessment year {FIXTURE_AY}", body)

    def test_skill_zip_has_folder_at_root(self):
        zip_path = self.path(f"dist/claude-skill/{SKILL}.zip")
        self.assertTrue(zip_path.is_file())
        with zipfile.ZipFile(zip_path) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            self.assertIn(f"{SKILL}/SKILL.md", names)
            self.assertIn(f"{SKILL}/references/vat-mushak.md", names)
            self.assertIn(f"{SKILL}/scripts/tax.py", names)
            self.assertIn(f"{SKILL}/data/rates-AY{FIXTURE_AY}.toml", names)
            for info in infos:
                self.assertTrue(info.filename.startswith(f"{SKILL}/"), info.filename)
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0), "fixed stamp")
            self.assertEqual(names, sorted(names), "entries in a fixed order")
            script = archive.getinfo(f"{SKILL}/scripts/validate.py")
            self.assertEqual((script.external_attr >> 16) & 0o777, 0o755)
            doc = archive.getinfo(f"{SKILL}/SKILL.md")
            self.assertEqual((doc.external_attr >> 16) & 0o777, 0o644)
            skill_text = archive.read(f"{SKILL}/SKILL.md").decode("utf-8")
            self.assertEqual(skill_text, self.text(f"dist/claude-skill/{SKILL}/SKILL.md"))
            self.assertIsNone(archive.testzip())

    # --- chatgpt ------------------------------------------------------------------------

    def test_chatgpt_layout_and_knowledge_names(self):
        self.assertTrue(self.path("dist/chatgpt/instructions.md").is_file())
        self.assertTrue(self.path("dist/chatgpt/README-install.md").is_file())
        knowledge = sorted(p.name for p in self.path("dist/chatgpt/knowledge").iterdir())
        expected = sorted(
            list(DEFAULT_CORE)
            + [f"{stem}.md" for stem in build.REFERENCE_ORDER]
            + [f"rates-AY{FIXTURE_AY}.md", "engine-usage.md"]
        )
        self.assertEqual(knowledge, expected)
        self.assertLessEqual(len(knowledge), build.CHATGPT_KNOWLEDGE_MAX_FILES)

    def test_chatgpt_instructions_are_core_plus_navigation_footer(self):
        instructions = self.text("dist/chatgpt/instructions.md")
        self.assertLessEqual(len(instructions), build.CHATGPT_INSTRUCTIONS_MAX_CHARS)
        self.assertTrue(instructions.startswith("# Fixture identity\n"))
        for text in DEFAULT_CORE.values():
            self.assertIn(text.strip(), instructions)
        self.assertIn("## Knowledge files", instructions)
        self.assertIn(f"`rates-AY{FIXTURE_AY}.md`", instructions)
        self.assertIn("`engine-usage.md`", instructions)
        self.assertNotIn("Non-negotiable rules", instructions)

    def test_chatgpt_rates_knowledge_carries_toml_verbatim(self):
        text = self.text(f"dist/chatgpt/knowledge/rates-AY{FIXTURE_AY}.md")
        self.assertIn("```toml\n" + FIXTURE_RATES_TOML.rstrip("\n") + "\n```", text)
        self.assertIn(FIXTURE_AY, text)
        self.assertIn("verified = false", text)

    def test_chatgpt_reference_knowledge_is_verbatim(self):
        for name, source in default_references().items():
            self.assertEqual(self.text(f"dist/chatgpt/knowledge/{name}"), source)

    def test_chatgpt_engine_usage_points_at_a_clone(self):
        text = self.text("dist/chatgpt/knowledge/engine-usage.md")
        self.assertIn("src/engine/tax.py", text)
        self.assertIn(build.REPO_URL, text)
        self.assertIn("Versioned rates loader fixture", text, "docstring-derived purpose")
        self.assertIn("### `accounts.toml`", text, "templates are inlined")
        self.assertIn("date,entry_id,description,account,debit,credit", text)

    # --- gemini -------------------------------------------------------------------------

    def test_gemini_layout(self):
        self.assertTrue(self.path("dist/gemini/gem-instructions.md").is_file())
        self.assertTrue(self.path("dist/gemini/README-install.md").is_file())
        knowledge = sorted(p.name for p in self.path("dist/gemini/knowledge").iterdir())
        self.assertLessEqual(len(knowledge), build.GEMINI_KNOWLEDGE_MAX_FILES)
        self.assertEqual(len(knowledge), 10, "all ten groups populated on a full tree")
        self.assertIn("8-glossary-bn-en.md", knowledge)
        self.assertIn("7-rates.md", knowledge)

    def test_gemini_instructions_follow_googles_four_blocks(self):
        text = self.text("dist/gemini/gem-instructions.md")
        for block in ("**Persona.**", "**Task.**", "**Context.**", "**Format.**"):
            self.assertIn(block, text)
        self.assertIn(FIXTURE_AY, text)
        self.assertIn("verified = false", text)
        self.assertIn("ITP", text)
        self.assertIn("`7-rates.md`", text)

    def test_gemini_merge_keeps_every_source_whole(self):
        merged = self.text("dist/gemini/knowledge/1-core-bookkeeping.md")
        self.assertIn("Debit / ডেবিট", merged)
        self.assertIn("python3 post.py --books ./books --json", merged)
        rates = self.text("dist/gemini/knowledge/7-rates.md")
        self.assertIn(FIXTURE_RATES_TOML.rstrip("\n"), rates)

    # --- universal ----------------------------------------------------------------------

    def test_universal_single_file(self):
        text = self.text("dist/universal/takabooks-complete.md")
        self.assertTrue(text.startswith("# TakaBooks"), "no frontmatter — an H1 first")
        self.assertIn("STOP — READ THIS FIRST", text)
        self.assertIn("## Contents", text)
        self.assertIn(FIXTURE_RATES_TOML.rstrip("\n"), text, "rates verbatim")
        self.assertIn("Debit / ডেবিট", text)
        self.assertIn(FIXTURE_AY, text)
        self.assertTrue(text.rstrip().endswith(f"Build id: `{self.report.build_id}`"))
        self.assertIn(build.ATTRIBUTION, text)
        self.assertNotIn("<!-- knowledge-only -->", text)

    def test_universal_toc_anchors_resolve(self):
        text = self.text("dist/universal/takabooks-complete.md")
        toc = re.findall(r"^- \[(.+?)\]\(#(.+?)\)$", text, flags=re.MULTILINE)
        self.assertGreaterEqual(len(toc), 4 + len(build.REFERENCE_ORDER) + 3)
        headings = {build.slugify(h) for h in re.findall(r"^## (.+)$", text, flags=re.MULTILINE)}
        for title, anchor in toc:
            self.assertIn(anchor, headings, f"TOC entry {title!r} points at nothing")
            self.assertEqual(build.slugify(title), anchor)

    def test_universal_rewrites_cross_file_links(self):
        text = self.text("dist/universal/takabooks-complete.md")
        self.assertNotIn("](vat-mushak.md)", text)
        self.assertNotIn("](../references/glossary-bn-en.md#term)", text)
        self.assertIn("[NBR](https://nbr.gov.bd)", text, "external links untouched")
        vat_anchor = build.slugify(f"6. {build.REFERENCE_TITLES['vat-mushak']}")
        self.assertIn(f"[VAT](#{vat_anchor})", text)

    # --- agents-md ----------------------------------------------------------------------

    def test_agents_md_at_root_and_in_dist(self):
        root_copy = self.text("AGENTS.md")
        dist_copy = self.text("dist/agents-md/AGENTS.md")
        self.assertEqual(root_copy, dist_copy)
        self.assertTrue(root_copy.startswith("# TakaBooks"), "plain Markdown, no frontmatter")
        self.assertLessEqual(len(root_copy.encode("utf-8")), build.AGENTS_MD_MAX_BYTES)
        for needle in (
            "python3 -m unittest discover tests",
            "python3 build/build.py",
            "TICON SYSTEM LTD",
            "https://ticonsys.com",
            "paisa",
            "মূসক / VAT",
            "8,000",
            "CLAUDE.md",
            f"rates-AY{FIXTURE_AY}.toml",
        ):
            self.assertIn(needle, root_copy, needle)

    # --- cross-cutting ------------------------------------------------------------------

    def test_every_bundle_credits_ticon_sys(self):
        for rel in (
            f"dist/claude-skill/{SKILL}/SKILL.md",
            "dist/claude-skill/README-install.md",
            "dist/chatgpt/README-install.md",
            "dist/gemini/README-install.md",
            "dist/universal/takabooks-complete.md",
            "AGENTS.md",
        ):
            self.assertIn("TICON SYSTEM LTD", self.text(rel), rel)

    def test_no_absolute_path_leaks_into_output(self):
        needle = str(self.root)
        for rel, data in read_outputs(self.root).items():
            if rel.endswith(".zip"):
                continue
            self.assertNotIn(needle, data.decode("utf-8"), rel)

    def test_report_lists_every_written_file(self):
        written = set(self.report.written)
        self.assertIn(f"dist/claude-skill/{SKILL}.zip", written)
        self.assertIn("dist/chatgpt/instructions.md", written)
        self.assertIn("dist/gemini/gem-instructions.md", written)
        self.assertIn("dist/universal/takabooks-complete.md", written)
        self.assertIn("AGENTS.md", written)
        self.assertIn("dist/agents-md/AGENTS.md", written)
        on_disk = set(read_outputs(self.root))
        self.assertEqual(on_disk, written)


# ======================================================================================
# Caps are enforced — an over-cap build fails loudly and writes nothing
# ======================================================================================


class TestCapsEnforced(FixtureCase):
    def assert_nothing_written(self, root: Path) -> None:
        self.assertFalse((root / "dist").exists(), "dist/ must not be created")
        self.assertFalse((root / "AGENTS.md").exists(), "AGENTS.md must not be written")

    def test_chatgpt_cap_fails_the_build_and_writes_nothing(self):
        core = dict(DEFAULT_CORE)
        core["10-workflow.md"] = "# Big\n\n" + ("x" * 8001) + "\n"
        root = self.repo(core=core)
        report = build.run_build(root, list(build.TARGETS))
        names = [(c.target, c.name) for c in report.failures]
        self.assertIn(("chatgpt", "instructions.md"), names)
        self.assertFalse(report.wrote_anything)
        self.assert_nothing_written(root)
        failure = next(c for c in report.failures if c.name == "instructions.md")
        self.assertIn("OVER BY", failure.detail)
        self.assertIn("knowledge-only", failure.detail)

    def test_chatgpt_cap_via_cli_exits_one_with_a_clear_message(self):
        core = dict(DEFAULT_CORE)
        core["20-bookkeeping.md"] = "# Big\n\n" + ("y" * 9000) + "\n"
        root = self.repo(core=core)
        code, out, err = run_main(["--repo-root", str(root)])
        self.assertEqual(code, 1)
        self.assertIn("BUILD FAILED", err)
        self.assertIn("8,000", err)
        self.assertIn("Nothing was written", err)
        self.assert_nothing_written(root)

    def test_chatgpt_cap_counts_codepoints_not_bytes(self):
        # 7,000 Bangla characters are 21,000 UTF-8 bytes: must PASS, the cap is characters.
        core = dict(DEFAULT_CORE)
        core["20-bookkeeping.md"] = "# বাংলা\n\n" + ("ক" * 7000) + "\n"
        report = build.run_build(self.repo("bn", core=core), list(build.TARGETS))
        self.assertEqual(report.failures, [], [c.render() for c in report.failures])
        # 7,999 ASCII characters plus the other core files and the footer: must FAIL.
        core["20-bookkeeping.md"] = "# ascii\n\n" + ("z" * 7999) + "\n"
        report = build.run_build(self.repo("ascii", core=core), list(build.TARGETS))
        self.assertTrue(any(c.name == "instructions.md" for c in report.failures))

    def test_chatgpt_cap_boundary_is_exact(self):
        # Fill a single core file so the rendered instruction lands on exactly 8,000.
        root = self.repo()
        tree = build.SourceTree.load(root)
        footer = build.chatgpt_footer(tree)
        others = "\n\n".join(
            text.strip() for name, text in DEFAULT_CORE.items() if name != "20-bookkeeping.md"
        )
        # instruction = core_joined + "\n\n" + footer + "\n"; core_joined joins 4 files.
        fixed = len(others) + len("\n\n") + len("\n\n") + len(footer) + len("\n")
        header = "# pad\n\n"
        pad = build.CHATGPT_INSTRUCTIONS_MAX_CHARS - fixed - len(header)
        core = dict(DEFAULT_CORE)
        core["20-bookkeeping.md"] = header + ("p" * pad) + "\n"
        report = build.run_build(self.repo("exact", core=core), list(build.TARGETS))
        check = next(c for c in report.checks if c.name == "instructions.md")
        self.assertEqual(check.value, 8000)
        self.assertTrue(check.ok)
        core["20-bookkeeping.md"] = header + ("p" * (pad + 1)) + "\n"
        report = build.run_build(self.repo("over", core=core), list(build.TARGETS))
        check = next(c for c in report.checks if c.name == "instructions.md")
        self.assertEqual(check.value, 8001)
        self.assertFalse(check.ok)
        self.assertIn(check, report.failures)

    def test_chatgpt_knowledge_file_cap(self):
        references = default_references()
        for index in range(15):
            references[f"extra-{index:02d}.md"] = f"# extra {index}\n\ntext\n"
        root = self.repo(references=references)
        report = build.run_build(root, list(build.TARGETS))
        names = [(c.target, c.name) for c in report.failures]
        self.assertIn(("chatgpt", "knowledge.files"), names)
        self.assertNotIn(("gemini", "knowledge.files"), names, "Gemini merges instead")
        self.assert_nothing_written(root)

    def test_gemini_merges_extras_and_never_drops_a_source(self):
        references = default_references()
        for index in range(5):
            references[f"extra-{index:02d}.md"] = f"# extra {index}\n\nEXTRA-{index}-TEXT\n"
        root = self.repo(references=references)
        report = build.run_build(root, ["gemini"])
        self.assertEqual(report.failures, [])
        files = sorted(p.name for p in (root / "dist/gemini/knowledge").iterdir())
        self.assertLessEqual(len(files), 10)
        overflow = (root / "dist/gemini/knowledge" / build.GEMINI_OVERFLOW_GROUP).read_text(
            encoding="utf-8"
        )
        for index in range(5):
            self.assertIn(f"EXTRA-{index}-TEXT", overflow)
        coverage = next(c for c in report.checks if c.name == "knowledge.coverage")
        self.assertTrue(coverage.ok)

    def test_skill_description_cap_is_enforced(self):
        root = self.repo()
        with mock.patch.object(build, "SKILL_DESCRIPTION", "d" * 201):
            report = build.run_build(root, ["claude-skill"])
        self.assertIn(("claude-skill", "frontmatter.description"),
                      [(c.target, c.name) for c in report.failures])
        self.assertFalse((root / "dist").exists())
        with mock.patch.object(build, "SKILL_DESCRIPTION", "   "):
            report = build.run_build(root, ["claude-skill"])
        self.assertIn("frontmatter.description.nonempty", [c.name for c in report.failures])

    def test_skill_name_rules_are_enforced(self):
        root = self.repo()
        for bad in ("claude-books", "bd--tax", "-lead", "Upper-Case", "x" * 65):
            with mock.patch.object(build, "SKILL_NAME", bad):
                report = build.run_build(root, ["claude-skill"])
            self.assertTrue(report.failures, bad)
            self.assertFalse((root / "dist").exists(), bad)

    def test_agents_md_cap_is_enforced(self):
        root = self.repo()
        with mock.patch.object(build, "AGENTS_MD_MAX_BYTES", 512):
            report = build.run_build(root, ["agents-md"])
        self.assertIn(("agents-md", "AGENTS.md.bytes"),
                      [(c.target, c.name) for c in report.failures])
        self.assertFalse((root / "AGENTS.md").exists())

    def test_gemini_instruction_limit_is_soft_and_configurable(self):
        root = self.repo()
        report = build.run_build(root, ["gemini"], gemini_soft_limit=10)
        self.assertEqual(report.failures, [], "an undocumented limit never fails the build")
        self.assertIn("gem-instructions.md", [c.name for c in report.warnings])
        self.assertTrue((root / "dist/gemini/gem-instructions.md").is_file())

    def test_soft_limits_never_fail(self):
        for check in build.run_build(self.repo(), list(build.TARGETS)).checks:
            if not check.hard:
                self.assertNotEqual(check.status, "FAIL")

    def test_missing_sources_warn_by_default_and_fail_with_strict(self):
        engine = {k: v for k, v in DEFAULT_ENGINE.items() if k != "post.py"}
        root = self.repo(engine=engine)
        report = build.run_build(root, list(build.TARGETS))
        self.assertEqual(report.failures, [])
        self.assertIn("expected.files", [c.name for c in report.warnings])
        self.assertTrue(report.wrote_anything)
        strict_root = self.repo("strict", engine=engine)
        report = build.run_build(strict_root, list(build.TARGETS), strict=True)
        self.assertIn("expected.files", [c.name for c in report.failures])
        self.assert_nothing_written(strict_root)

    def test_knowledge_only_blocks_leave_the_instruction_but_stay_everywhere_else(self):
        core = dict(DEFAULT_CORE)
        core["00-identity.md"] = (
            "# Identity\n\nAlways here.\n\n<!-- knowledge-only -->\n"
            "DETAIL-ONLY-IN-KNOWLEDGE\n<!-- /knowledge-only -->\n"
        )
        root = self.repo(core=core)
        build.run_build(root, list(build.TARGETS))
        instructions = (root / "dist/chatgpt/instructions.md").read_text(encoding="utf-8")
        self.assertNotIn("DETAIL-ONLY-IN-KNOWLEDGE", instructions)
        for rel in (
            "dist/chatgpt/knowledge/00-identity.md",
            "dist/gemini/knowledge/1-core-bookkeeping.md",
            "dist/universal/takabooks-complete.md",
            f"dist/claude-skill/{SKILL}/SKILL.md",
        ):
            text = (root / rel).read_text(encoding="utf-8")
            self.assertIn("DETAIL-ONLY-IN-KNOWLEDGE", text, rel)
            self.assertNotIn("knowledge-only -->", text, f"markers stripped from {rel}")


# ======================================================================================
# Determinism, idempotency and the CLI
# ======================================================================================


class TestDeterminismAndCli(FixtureCase):
    def test_two_directories_produce_identical_bytes_including_the_zip(self):
        a, b = self.repo("a"), self.repo("b")
        build.run_build(a, list(build.TARGETS))
        build.run_build(b, list(build.TARGETS))
        outputs_a, outputs_b = read_outputs(a), read_outputs(b)
        self.assertEqual(sorted(outputs_a), sorted(outputs_b))
        for rel in outputs_a:
            self.assertEqual(outputs_a[rel], outputs_b[rel], f"{rel} differs between builds")

    def test_rebuild_is_idempotent_and_replaces_stale_output(self):
        root = self.repo()
        build.run_build(root, list(build.TARGETS))
        first = read_outputs(root)
        stale = root / "dist/chatgpt/knowledge/stale.md"
        stale.write_text("left over\n", encoding="utf-8")
        junk = root / "dist/junk.txt"
        junk.write_text("not ours\n", encoding="utf-8")
        build.run_build(root, list(build.TARGETS))
        self.assertFalse(stale.exists(), "a target directory is replaced wholesale")
        self.assertTrue(junk.exists(), "without --clean, unrelated files survive")
        second = read_outputs(root)
        del second["dist/junk.txt"]
        self.assertEqual(first, second)
        build.run_build(root, list(build.TARGETS), clean=True)
        self.assertFalse(junk.exists(), "--clean wipes dist/ first")
        self.assertEqual(first, read_outputs(root))

    def test_check_writes_nothing(self):
        root = self.repo()
        code, out, err = run_main(["--check", "--repo-root", str(root)])
        self.assertEqual(code, 0, err)
        self.assertFalse((root / "dist").exists())
        self.assertFalse((root / "AGENTS.md").exists())
        self.assertIn("checked 5 target(s)", out)
        self.assertIn("chatgpt/instructions.md", out)

    def test_check_reports_the_instruction_budget_every_time(self):
        code, out, _ = run_main(["--check", "--repo-root", str(self.repo())])
        self.assertEqual(code, 0)
        self.assertRegex(out, r"src/core/ [\d,]+ \+ navigation footer [\d,]+ = [\d,]+ of 8,000")
        self.assertIn("headroom", out)
        self.assertIn("UTF-8 bytes", out)

    def test_check_exits_nonzero_over_cap_without_writing(self):
        core = dict(DEFAULT_CORE)
        core["10-workflow.md"] = "# Big\n\n" + ("x" * 8001) + "\n"
        root = self.repo(core=core)
        code, _, err = run_main(["--check", "--repo-root", str(root)])
        self.assertEqual(code, 1)
        self.assertIn("BUILD FAILED", err)
        self.assertFalse((root / "dist").exists())

    def test_all_flag_builds_every_target(self):
        root = self.repo()
        code, out, err = run_main(["--all", "--repo-root", str(root)])
        self.assertEqual(code, 0, err)
        self.assertIn("built 5 target(s)", out)
        for rel in (
            f"dist/claude-skill/{SKILL}/SKILL.md",
            f"dist/claude-skill/{SKILL}.zip",
            "dist/chatgpt/instructions.md",
            "dist/gemini/gem-instructions.md",
            "dist/universal/takabooks-complete.md",
            "dist/agents-md/AGENTS.md",
            "AGENTS.md",
        ):
            self.assertTrue((root / rel).is_file(), rel)

    def test_single_target_builds_only_that_target(self):
        root = self.repo()
        code, _, err = run_main(["--target", "gemini", "--repo-root", str(root)])
        self.assertEqual(code, 0, err)
        self.assertTrue((root / "dist/gemini/gem-instructions.md").is_file())
        self.assertFalse((root / "dist/chatgpt").exists())
        self.assertFalse((root / "AGENTS.md").exists())

    def test_clean_with_target_none_only_removes_dist(self):
        root = self.repo()
        run_main(["--repo-root", str(root)])
        self.assertTrue((root / "dist").is_dir())
        code, out, _ = run_main(["--clean", "--target", "none", "--repo-root", str(root)])
        self.assertEqual(code, 0)
        self.assertIn("removed dist/", out)
        self.assertFalse((root / "dist").exists())
        self.assertTrue((root / "src").is_dir())

    def test_check_and_clean_together_is_an_error(self):
        code, _, err = run_main(["--check", "--clean", "--repo-root", str(self.repo())])
        self.assertEqual(code, 1)
        self.assertIn("build error", err)

    def test_json_report(self):
        root = self.repo()
        code, out, _ = run_main(["--check", "--json", "--repo-root", str(root)])
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertTrue(report["ok"])
        self.assertFalse(report["wrote_anything"])
        self.assertEqual(report["assessment_year"], FIXTURE_AY)
        self.assertEqual(report["targets"], list(build.TARGETS))
        names = {(c["target"], c["name"]) for c in report["checks"]}
        self.assertIn(("chatgpt", "instructions.md"), names)
        self.assertIn(("claude-skill", "frontmatter.description"), names)
        self.assertIn(("gemini", "knowledge.files"), names)
        self.assertIn(("agents-md", "AGENTS.md.bytes"), names)

    def test_json_report_exit_code_on_failure(self):
        core = dict(DEFAULT_CORE)
        core["10-workflow.md"] = "# Big\n\n" + ("x" * 8001) + "\n"
        code, out, _ = run_main(["--check", "--json", "--repo-root", str(self.repo(core=core))])
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(out)["ok"])

    def test_quiet_prints_nothing_on_success(self):
        code, out, err = run_main(["--quiet", "--check", "--repo-root", str(self.repo())])
        self.assertEqual(code, 0)
        self.assertEqual(out, "")
        self.assertEqual(err, "")

    def test_missing_src_is_reported_not_raised(self):
        code, _, err = run_main(["--repo-root", str(self.tmp / "nowhere")])
        self.assertEqual(code, 1)
        self.assertIn("No src/ directory", err)

    def test_help_mentions_every_target_and_ticon_sys(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as ctx:
            build.main(["--help"])
        self.assertEqual(ctx.exception.code, 0)
        text = out.getvalue()
        for flag in ("--target", "--all", "--clean", "--check", "--strict", "--json",
                     "--gemini-soft-limit", "--repo-root"):
            self.assertIn(flag, text, flag)
        for target in build.TARGETS:
            self.assertIn(target, text, target)
        self.assertIn("TICON SYSTEM LTD", text)

    def test_write_refuses_to_leave_the_repo(self):
        root = self.repo()
        with self.assertRaises(build.BuildError):
            build._assert_inside(root.resolve(), Path("../escape.md"))
        bundle = build.Bundle(target="x", clean_dir="src")
        with self.assertRaises(build.BuildError):
            build.write_bundle(bundle, root.resolve())
        bundle = build.Bundle(target="x", clean_dir="dist")
        with self.assertRaises(build.BuildError):
            build.write_bundle(bundle, root.resolve())

    def test_bundle_refuses_duplicate_paths(self):
        bundle = build.Bundle(target="x")
        bundle.add("a.md", "one")
        with self.assertRaises(build.BuildError):
            bundle.add("a.md", "two")


# ======================================================================================
# The real repository builds — the release gate (spec §7: "every target emits; 8k cap")
# ======================================================================================


@unittest.skipUnless(SRC_DIR.is_dir(), "no src/ in this checkout")
class TestRealSources(unittest.TestCase):
    """Build from a copy of the real ``src/`` so the test never touches the repo's dist/."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls._tmp.name) / "repo"
        shutil.copytree(
            SRC_DIR, cls.root / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
        )
        cls.report = build.run_build(cls.root, list(build.TARGETS))

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def require_clean_build(self) -> None:
        """Every other test here needs the outputs; if the gate failed, say so once."""
        if self.report.failures:
            self.skipTest(
                "the real src/ breaks a hard platform cap, so nothing was built — "
                "see test_no_hard_limit_is_exceeded for the numbers"
            )

    def test_no_hard_limit_is_exceeded(self):
        """THE release gate.  When this fails, fix src/ (not the build): the message
        says which cap, by how much, and which source file carries the weight."""
        rendered = "\n".join(c.render() for c in self.report.failures)
        self.assertEqual(
            self.report.failures,
            [],
            "\nThe real src/ exceeds a hard platform cap; the build refuses to write and so "
            "must this test. Trim the file named below or wrap reference material in "
            f"{build.KNOWLEDGE_ONLY_OPEN} ... {build.KNOWLEDGE_ONLY_CLOSE}.\n" + rendered,
        )
        self.assertTrue(self.report.wrote_anything)

    def test_chatgpt_instruction_fits_8000_characters(self):
        self.require_clean_build()
        instructions = (self.root / "dist/chatgpt/instructions.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(instructions), 8000)
        knowledge = list((self.root / "dist/chatgpt/knowledge").iterdir())
        self.assertLessEqual(len(knowledge), 20)

    def test_every_target_is_present(self):
        self.require_clean_build()
        for rel in (
            f"dist/claude-skill/{SKILL}/SKILL.md",
            f"dist/claude-skill/{SKILL}.zip",
            "dist/claude-skill/README-install.md",
            "dist/chatgpt/instructions.md",
            "dist/chatgpt/README-install.md",
            "dist/gemini/gem-instructions.md",
            "dist/gemini/README-install.md",
            "dist/universal/takabooks-complete.md",
            "dist/agents-md/AGENTS.md",
            "AGENTS.md",
        ):
            self.assertTrue((self.root / rel).is_file(), rel)
        self.assertLessEqual(len(list((self.root / "dist/gemini/knowledge").iterdir())), 10)

    def test_assessment_year_is_read_from_the_rates_file(self):
        self.require_clean_build()
        self.assertNotEqual(self.report.assessment_year, "unknown")
        self.assertRegex(self.report.assessment_year, r"^\d{4}-\d{2}$")
        skill = (self.root / f"dist/claude-skill/{SKILL}/SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(parse_frontmatter(skill)["metadata"]["assessment_year"],
                         self.report.assessment_year)

    def test_skill_ships_the_real_engine_and_rates(self):
        self.require_clean_build()
        base = self.root / f"dist/claude-skill/{SKILL}"
        for name in (self.root / "src/engine").glob("*.py"):
            shipped = base / "scripts" / name.name
            self.assertTrue(shipped.is_file(), name.name)
            self.assertEqual(
                shipped.read_text(encoding="utf-8"),
                build.normalise(name.read_text(encoding="utf-8")),
            )
        for name in (self.root / "src/data").glob("rates-AY*.toml"):
            self.assertTrue((base / "data" / name.name).is_file(), name.name)

    def test_rates_toml_travels_verbatim_into_every_bundle(self):
        self.require_clean_build()
        tree = build.SourceTree.load(self.root)
        if not tree.rates:
            self.skipTest("no rates file in src/data/ yet")
        toml_text = tree.rates_text.rstrip("\n")
        for rel in (
            f"dist/chatgpt/knowledge/{build.chatgpt_rates_knowledge_name(tree)}",
            "dist/gemini/knowledge/7-rates.md",
            "dist/universal/takabooks-complete.md",
        ):
            self.assertIn(toml_text, (self.root / rel).read_text(encoding="utf-8"), rel)

    def test_real_build_is_deterministic(self):
        self.require_clean_build()
        other = Path(self._tmp.name) / "again"
        shutil.copytree(self.root / "src", other / "src")
        build.run_build(other, list(build.TARGETS))
        self.assertEqual(read_outputs(self.root), read_outputs(other))

    def test_universal_toc_resolves_on_real_content(self):
        self.require_clean_build()
        text = (self.root / "dist/universal/takabooks-complete.md").read_text(encoding="utf-8")
        headings = {build.slugify(h) for h in re.findall(r"^## (.+)$", text, flags=re.MULTILINE)}
        toc = re.findall(r"^- \[(.+?)\]\(#(.+?)\)$", text, flags=re.MULTILINE)
        self.assertTrue(toc)
        for title, anchor in toc:
            self.assertIn(anchor, headings, title)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
