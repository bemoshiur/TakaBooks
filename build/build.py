#!/usr/bin/env python3
"""TakaBooks build — one source of truth in ``src/``, many platform bundles in ``dist/``.

Usage::

    python3 build/build.py                      # build every target
    python3 build/build.py --all                # the same, spelled out (CI uses this)
    python3 build/build.py --target chatgpt     # build one target
    python3 build/build.py --clean              # wipe dist/ first, then build
    python3 build/build.py --check              # verify every limit, write nothing
    python3 build/build.py --json               # machine-readable report

Targets (design spec §5):

===============  ==============================================================
``claude-skill`` ``dist/claude-skill/bd-bookkeeping-tax/`` + a zip whose ROOT
                 entry is the skill folder, so the one artifact works for a
                 claude.ai upload and for ``~/.claude/skills/`` alike.
``chatgpt``      ``dist/chatgpt/instructions.md`` (HARD 8,000 characters) plus
                 ``knowledge/`` (HARD 20 files).
``gemini``       ``dist/gemini/gem-instructions.md`` plus ``knowledge/``
                 (HARD 10 files — the tightest packaging cap of any platform).
``universal``    ``dist/universal/takabooks-complete.md`` — one paste-anywhere
                 file with an anchor-linked table of contents.
``agents-md``    ``AGENTS.md`` at the repository root, plus a copy at
                 ``dist/agents-md/AGENTS.md`` for the npm installer.
===============  ==============================================================

One source of truth.  ``src/core/`` *is* the assistant instruction on every platform;
the build never restates its rules.  What the build adds is navigation only — where the
references, the rates file and the scripts live on that particular platform — so a rule
edited in ``src/core/`` reaches every bundle and no bundle can drift.

Design contracts this file honours:

* **Standard library only.**  Floor is Python 3.11 (``tomllib``).
* **Deterministic and idempotent.**  Same ``src/`` bytes in, byte-identical
  ``dist/`` bytes out.  No timestamps, no randomness, no dictionary-order
  dependence, and zip entries are written with a fixed 1980-01-01 stamp so
  CI can diff two builds.
* **Nothing is written until every hard limit has passed.**  The whole bundle
  is assembled in memory, checked, and only then flushed to disk.  A build
  that would exceed a platform cap fails loudly and writes nothing.
* **This file never states a tax rate, threshold, deadline or statute number.**
  Every figure lives in ``src/data/rates-AY*.toml`` and travels verbatim.

TakaBooks — maintained by Moshiur Rahman (@bemoshiur) · TICON SYSTEM LTD
https://ticonsys.com · https://github.com/bemoshiur/TakaBooks · MIT licensed.
"""

from __future__ import annotations

import sys

# --------------------------------------------------------------------------------------
# Python version guard — before `tomllib` is imported, so a 3.10 user gets a sentence
# rather than an opaque ImportError.
# --------------------------------------------------------------------------------------

MIN_PYTHON: tuple[int, int] = (3, 11)

if sys.version_info < MIN_PYTHON:  # pragma: no cover - cannot run on a new interpreter
    sys.stderr.write(
        "TakaBooks build needs Python 3.11 or newer (tomllib lives in the standard "
        "library from 3.11). You are running Python "
        f"{'.'.join(str(p) for p in sys.version_info[:3])}.\n"
    )
    raise SystemExit(2)

import argparse  # noqa: E402
import ast  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import tomllib  # noqa: E402
import zipfile  # noqa: E402
from dataclasses import dataclass, field  # noqa: E402
from pathlib import Path  # noqa: E402

__all__ = [
    "BuildError",
    "Bundle",
    "Check",
    "SourceTree",
    "TARGETS",
    "build_target",
    "main",
    "run_build",
]


# ======================================================================================
# Project constants
# ======================================================================================

PROJECT_NAME = "TakaBooks"
PROJECT_VERSION = "1.2.0"
REPO_URL = "https://github.com/bemoshiur/TakaBooks"
COMPANY = "TICON SYSTEM LTD"
COMPANY_URL = "https://ticonsys.com"
MAINTAINER = "Moshiur Rahman (@bemoshiur)"
LICENSE_NAME = "MIT"

ATTRIBUTION = (
    f"{PROJECT_NAME} — maintained by {MAINTAINER} · {COMPANY} — {COMPANY_URL} · "
    f"{LICENSE_NAME} licensed · {REPO_URL}"
)

DISCLAIMER = (
    "**Disclaimer / দাবিত্যাগ** — TakaBooks is not professional advice and is not an "
    "e-filing robot. It prepares figures; a human files them. Verify every figure with a "
    "licensed Income Tax Practitioner (ITP) or Chartered Accountant (CA) before "
    "submitting anything to the National Board of Revenue (NBR)."
)

# Where the engine scripts sit for a user who has no bundle with scripts in it (ChatGPT,
# Gemini, the single-file bundle): a clone of the repository.
CLONE_LOCATION = f"in a clone of {REPO_URL}"

# The behavioural rules — prime directive, never invent a figure, state the assessment
# year, the user's language, the disclaimer — live in ``src/core/`` and nowhere else.
# This file deliberately holds no copy of them.


# --------------------------------------------------------------------------------------
# Claude Skill frontmatter.  Every value below sits inside the STRICTEST published cap of
# every surface (claude.ai upload UI, platform.claude.com, the open Agent Skills spec).
# --------------------------------------------------------------------------------------

SKILL_NAME = "bd-bookkeeping-tax"

# The description is the ONLY thing an assistant sees before deciding to load the skill,
# so it says when to trigger and is dense with the terms a user actually types:
# Bangladesh, BDT, taka, VAT, মূসক, Mushak, TDS, উৎসে কর কর্তন, VDS, NBR, TIN, BIN,
# income tax, payroll, journals, trial balance, P&L.  It must stay within 200 characters
# (the claude.ai upload cap); the build measures it in Unicode codepoints.
SKILL_DESCRIPTION = (
    "Bangladesh bookkeeping and tax. Use when a user mentions Bangladesh, BDT/taka, "
    "VAT/মূসক, Mushak forms, TDS/উৎসে কর কর্তন, VDS, NBR, TIN/BIN, income tax, payroll, "
    "journals, trial balance or P&L."
)

SKILL_COMPATIBILITY = (
    "Requires Python 3.11 or newer, standard library only. No package installs and no "
    "network access are needed; the bundled scripts run fully offline."
)


# ======================================================================================
# Platform limits
#
# Each entry records the number AND whether it is hard (build fails) or soft (build warns).
# A hard gate on an undocumented number would be inventing a limit, so anything Google or
# OpenAI has not published is a soft warning.
# ======================================================================================

# --- Claude / Agent Skills -------------------------------------------------------------
SKILL_NAME_MAX_CHARS = 64  # hard  · agentskills.io spec + platform.claude.com
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")  # no leading/trailing/double '-'
SKILL_NAME_FORBIDDEN = ("claude", "anthropic")  # hard · platform.claude.com
SKILL_DESCRIPTION_MAX_CHARS = 200  # hard · claude.ai upload UI (stricter than the 1024
#                                    of platform.claude.com; 200 is the portable value)
SKILL_COMPATIBILITY_MAX_CHARS = 500  # hard · agentskills.io spec
SKILL_BODY_MAX_LINES = 500  # soft · "under 500 lines" recommendation
SKILL_BODY_MAX_TOKENS = 5000  # soft · "< 5,000 tokens" recommendation
SKILL_BUNDLE_MAX_BYTES = 30 * 1000 * 1000  # hard · Skills API "under 30 MB uncompressed"

# --- ChatGPT ---------------------------------------------------------------------------
CHATGPT_INSTRUCTIONS_MAX_CHARS = 8000  # hard · Custom GPT instructions field
CHATGPT_KNOWLEDGE_MAX_FILES = 20  # hard · knowledge files per Custom GPT

# --- Gemini ----------------------------------------------------------------------------
GEMINI_KNOWLEDGE_MAX_FILES = 10  # hard · "Gems supports up to 10 source documents"
GEMINI_INSTRUCTIONS_SOFT_CHARS = 2000  # soft · Google publishes NO limit; see --help

# --- Universal single-file bundle ------------------------------------------------------
UNIVERSAL_CORE_SOFT_TOKENS = 50_000  # soft · takabooks-core.md must fit a 128K context
UNIVERSAL_CORE_SOFT_BYTES = 200_000  # soft · same budget expressed in UTF-8 bytes
# takabooks-complete.md embeds every reference and the rates TOML verbatim, because
# summarising a rate table is how a wrong number reaches NBR.  It is therefore large by
# design and is the large-context / attach-as-a-file option, not the paste-anywhere one.
UNIVERSAL_COMPLETE_SOFT_TOKENS = 300_000  # soft · needs a 512K+ context model
UNIVERSAL_COMPLETE_SOFT_BYTES = 1_200_000  # soft · same ceiling in UTF-8 bytes

# --- AGENTS.md -------------------------------------------------------------------------
AGENTS_MD_MAX_BYTES = 32 * 1024  # hard · Codex `project_doc_max_bytes` default
AGENTS_MD_SOFT_BYTES = 8 * 1024  # soft · leave room for nested AGENTS.md files


# ======================================================================================
# Source layout (design spec §3)
# ======================================================================================

CORE_ORDER = ("00-identity", "10-workflow", "20-bookkeeping", "30-tax-overview")

CORE_TITLES = {
    "00-identity": "Identity and disclaimer",
    "10-workflow": "Workflow — how to behave",
    "20-bookkeeping": "Bookkeeping rules / হিসাব সংরক্ষণ",
    "30-tax-overview": "Which reference to read when",
}

REFERENCE_ORDER = (
    "income-tax",
    "vat-mushak",
    "withholding-tds-vds",
    "bookkeeping-standards",
    "payroll",
    "compliance-calendar",
    "penalties",
    "glossary-bn-en",
)

REFERENCE_TITLES = {
    "income-tax": "Income tax / আয়কর",
    "vat-mushak": "VAT / মূসক and the Mushak forms",
    "withholding-tds-vds": "Withholding — TDS / উৎসে কর কর্তন and VDS / উৎসে মূসক কর্তন",
    "bookkeeping-standards": "Bookkeeping standards / হিসাবরক্ষণ মান",
    "payroll": "Payroll / বেতন-ভাতা",
    "compliance-calendar": "Compliance calendar / সম্মতি পঞ্জিকা",
    "penalties": "Penalties and interest / জরিমানা ও সুদ",
    "glossary-bn-en": "Glossary বাংলা ↔ English",
}

ENGINE_ORDER = (
    "takabooks",
    "init_books",
    "post",
    "report",
    "vat",
    "tax",
    "validate",
)

# Verbatim from design spec §4.6 — module responsibilities, not tax content.
ENGINE_PURPOSE = {
    "takabooks.py": (
        "Shared library: Money, Account, Entry, Ledger, TOML/CSV IO, validation, "
        "Bangladeshi লাখ/কোটি formatting"
    ),
    "init_books.py": "Scaffold a `books/` directory from the templates",
    "post.py": "Validate and append a journal entry; refuse if it is unbalanced",
    "report.py": "Trial balance, P&L, balance sheet — Markdown + CSV from one computation",
    "vat.py": "VAT position, input/output reconciliation, Mushak 9.1 figures",
    "tax.py": "Income tax: slabs, rebate, minimum tax, surcharge — reads the rates TOML",
    "validate.py": (
        "Whole-ledger integrity: balance, unknown accounts, date order, duplicate ids"
    ),
}


def module_purpose(name: str, source: str) -> str:
    """One line on what an engine module is for.

    Spec §4.6 wording when the module is one the spec names; otherwise the first line of
    the module's own docstring (``rates.py`` and any helper added later), so a script is
    never listed as "see the module docstring" — that is exactly the file the assistant
    is told not to read.
    """
    purpose = ENGINE_PURPOSE.get(name)
    if purpose:
        return purpose
    try:
        docstring = ast.get_docstring(ast.parse(source)) or ""
    except (SyntaxError, ValueError):
        docstring = ""
    for line in docstring.split("\n"):
        line = line.strip()
        if not line:
            continue
        line = re.sub(rf"^{re.escape(PROJECT_NAME)}\s*[—–-]\s*", "", line).rstrip(".")
        return line[:1].upper() + line[1:]
    return "Supporting module for the engine scripts."


# Content between these markers is dropped from the two *compact instruction* targets
# (ChatGPT `instructions.md`, Gemini `gem-instructions.md`) and kept everywhere else.
# It is the documented escape valve when `src/core/` grows past the 8,000-character cap.
KNOWLEDGE_ONLY_OPEN = "<!-- knowledge-only -->"
KNOWLEDGE_ONLY_CLOSE = "<!-- /knowledge-only -->"

TARGETS = ("claude-skill", "chatgpt", "gemini", "universal", "agents-md")


class BuildError(Exception):
    """A build could not proceed.  Exit code 1."""

    exit_code = 1


# ======================================================================================
# Text utilities — all deterministic, all fence-aware
# ======================================================================================

_FENCE_RE = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")
_ATX_RE = re.compile(r"^( {0,3})(#{1,6})(\s.*|)$")


def normalise(text: str) -> str:
    """Strip a BOM, force LF line endings, guarantee exactly one trailing newline."""
    text = text.replace("﻿", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.rstrip("\n") + "\n"


def _fence_states(lines: list[str]):
    """Yield ``(line, inside_fence)`` for every line.  Fence delimiters count as inside."""
    open_fence: tuple[str, int] | None = None
    for line in lines:
        match = _FENCE_RE.match(line)
        if match is not None:
            delimiter = match.group(2)
            if open_fence is None:
                open_fence = (delimiter[0], len(delimiter))
                yield line, True
                continue
            char, length = open_fence
            closes = (
                delimiter[0] == char
                and len(delimiter) >= length
                and match.group(3).strip() == ""
            )
            if closes:
                open_fence = None
                yield line, True
                continue
        yield line, open_fence is not None


def heading_levels(text: str) -> list[int]:
    """ATX heading levels outside fenced code blocks, in document order."""
    levels: list[int] = []
    for line, in_fence in _fence_states(text.split("\n")):
        if in_fence:
            continue
        match = _ATX_RE.match(line)
        if match is not None:
            levels.append(len(match.group(2)))
    return levels


def shift_headings(text: str, target_min_level: int) -> str:
    """Re-level a document so its shallowest heading becomes ``target_min_level``.

    Headings inside fenced code blocks are left alone, so a ``# comment`` in a shell
    snippet survives untouched.  Levels are clamped to the 1..6 ATX range.
    """
    levels = heading_levels(text)
    if not levels:
        return text
    delta = target_min_level - min(levels)
    if delta == 0:
        return text
    out: list[str] = []
    for line, in_fence in _fence_states(text.split("\n")):
        if in_fence:
            out.append(line)
            continue
        match = _ATX_RE.match(line)
        if match is None:
            out.append(line)
            continue
        level = min(6, max(1, len(match.group(2)) + delta))
        out.append(f"{match.group(1)}{'#' * level}{match.group(3)}")
    return "\n".join(out)


# Punctuation GitHub's slugger drops: ASCII punctuation plus the general and supplemental
# punctuation blocks (em dash, ellipsis, ...).  Letters, digits and combining marks in every
# script survive, so a Bangla heading keeps its vowel signs.
_SLUG_DROP_RE = re.compile(
    "[\u2000-\u206f\u2e00-\u2e7f" + re.escape("\\'!\"#$%&()*+,./:;<=>?@[]^`{|}~") + "]"
)


def slugify(title: str) -> str:
    """GitHub-style anchor slug: lower-case, drop punctuation, spaces become hyphens.

    ``re``'s ``\\w`` does not match combining marks, so a ``[^\\w\\s-]`` strip would turn
    ``মূসক`` into ``মসক`` and every Bangla anchor would dangle.  This follows the algorithm
    GitHub, VS Code and most Markdown renderers use instead.
    """
    slug = title.strip().lower()
    slug = _SLUG_DROP_RE.sub("", slug)
    return slug.replace(" ", "-")


def fence_for(text: str, language: str = "") -> tuple[str, str]:
    """Return ``(open_fence, close_fence)`` long enough to wrap ``text`` safely."""
    longest = 0
    for run in re.findall(r"`+", text):
        longest = max(longest, len(run))
    ticks = "`" * max(3, longest + 1)
    return f"{ticks}{language}", ticks


def fenced(text: str, language: str = "") -> str:
    """Wrap ``text`` in a fenced code block that cannot be broken by its own backticks."""
    open_fence, close_fence = fence_for(text, language)
    return f"{open_fence}\n{text.rstrip(chr(10))}\n{close_fence}"


def language_for(suffix: str) -> str:
    return {
        ".toml": "toml",
        ".csv": "csv",
        ".py": "python",
        ".json": "json",
        ".md": "markdown",
        ".yaml": "yaml",
        ".yml": "yaml",
    }.get(suffix.lower(), "text")


def estimate_tokens(text: str) -> int:
    """A deterministic, documented token *estimate*: UTF-8 bytes / 4, rounded up.

    Bangla codepoints are three UTF-8 bytes each, so a bytes-based estimate is the
    conservative one for a bilingual bundle.  It is an estimate, never a measurement,
    and only ever drives soft warnings.
    """
    byte_length = len(text.encode("utf-8"))
    return -(-byte_length // 4)


def strip_knowledge_only(text: str) -> str:
    """Drop ``<!-- knowledge-only -->`` blocks — used by the compact instruction targets."""
    out: list[str] = []
    skipping = False
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped == KNOWLEDGE_ONLY_OPEN:
            skipping = True
            continue
        if stripped == KNOWLEDGE_ONLY_CLOSE:
            skipping = False
            continue
        if not skipping:
            out.append(line)
    return "\n".join(out)


def drop_knowledge_only_markers(text: str) -> str:
    """Keep the content, remove only the marker lines — used by full-content targets."""
    return "\n".join(
        line
        for line in text.split("\n")
        if line.strip() not in (KNOWLEDGE_ONLY_OPEN, KNOWLEDGE_ONLY_CLOSE)
    )


_LINK_RE = re.compile(r"\]\(\s*(?!https?:|mailto:|#)([^)\s]+?)(#[^)\s]*)?\s*\)")


def rewrite_links_to_anchors(text: str, anchors_by_basename: dict[str, str]) -> str:
    """Turn cross-file relative links into in-document anchors.

    The single-file bundle has no filesystem around it, so ``[VAT](references/vat.md)``
    must become ``[VAT](#6-vat--মূসক)`` or the model follows a link into nothing.
    Links whose target is not part of the bundle are left exactly as they are.
    """
    if not anchors_by_basename:
        return text

    def replace(match: re.Match[str]) -> str:
        target = match.group(1)
        basename = target.rsplit("/", 1)[-1]
        anchor = anchors_by_basename.get(basename)
        if anchor is None:
            return match.group(0)
        return f"](#{anchor})"

    out: list[str] = []
    for line, in_fence in _fence_states(text.split("\n")):
        out.append(line if in_fence else _LINK_RE.sub(replace, line))
    return "\n".join(out)


def yaml_double_quote(value: str) -> str:
    """Emit a YAML double-quoted scalar.  Safe for colons, dashes and Bangla alike."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    escaped = escaped.replace("\n", "\\n")
    return f'"{escaped}"'


# ======================================================================================
# Source discovery
# ======================================================================================


def order_key(stems: tuple[str, ...]):
    """Sort helper: declared stems first in declared order, then extras alphabetically."""
    index = {stem: position for position, stem in enumerate(stems)}

    def key(path: Path) -> tuple[int, int, str]:
        stem = path.stem
        if stem in index:
            return (0, index[stem], stem)
        return (1, 0, stem)

    return key


@dataclass
class SourceTree:
    """Everything ``build.py`` reads.  Discovery is by glob, so extra files are picked up."""

    repo_root: Path
    core: dict[str, str] = field(default_factory=dict)
    references: dict[str, str] = field(default_factory=dict)
    engine: dict[str, str] = field(default_factory=dict)
    templates: dict[str, str] = field(default_factory=dict)
    rates: dict[str, str] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    assessment_year: str = "unknown"

    @property
    def src_dir(self) -> Path:
        return self.repo_root / "src"

    @classmethod
    def load(cls, repo_root: Path) -> SourceTree:
        repo_root = repo_root.resolve()
        tree = cls(repo_root=repo_root)
        src = repo_root / "src"
        if not src.is_dir():
            raise BuildError(
                f"No src/ directory under {repo_root}. build.py emits dist/ from src/; "
                "point it at the repository root with --repo-root."
            )

        tree.core = _read_dir(src / "core", "*.md", order_key(CORE_ORDER))
        tree.references = _read_dir(src / "references", "*.md", order_key(REFERENCE_ORDER))
        tree.engine = _read_dir(src / "engine", "*.py", order_key(ENGINE_ORDER))
        tree.templates = _read_dir(src / "templates", "*", lambda path: (0, 0, path.name))
        tree.rates = _read_dir(src / "data", "rates-AY*.toml", lambda p: (0, 0, p.name))

        for stem in CORE_ORDER:
            if f"{stem}.md" not in tree.core:
                tree.missing.append(f"src/core/{stem}.md")
        for stem in REFERENCE_ORDER:
            if f"{stem}.md" not in tree.references:
                tree.missing.append(f"src/references/{stem}.md")
        for stem in ENGINE_ORDER:
            if f"{stem}.py" not in tree.engine:
                tree.missing.append(f"src/engine/{stem}.py")
        if not tree.rates:
            tree.missing.append("src/data/rates-AY<year>.toml")
        if not tree.templates:
            tree.missing.append("src/templates/")

        tree.assessment_year = tree._detect_assessment_year()
        return tree

    # -- helpers ------------------------------------------------------------------------

    def _detect_assessment_year(self) -> str:
        """Read the assessment year from the rates data — never from a hardcoded guess."""
        if not self.rates:
            return "unknown"
        name = self.rates_filename
        for key in ("assessment_year", "ay"):
            try:
                parsed = tomllib.loads(self.rates[name])
            except (tomllib.TOMLDecodeError, ValueError):
                break
            value = parsed.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
            meta = parsed.get("meta")
            if isinstance(meta, dict):
                value = meta.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        match = re.search(r"rates-AY([0-9]{4}(?:-[0-9]{2,4})?)\.toml$", name)
        return match.group(1) if match else "unknown"

    @property
    def rates_filename(self) -> str:
        """The newest rates file by name (``rates-AY2026-27.toml`` sorts after ...2025-26)."""
        return sorted(self.rates)[-1] if self.rates else ""

    @property
    def rates_text(self) -> str:
        return self.rates.get(self.rates_filename, "")

    def core_files(self) -> list[tuple[str, str]]:
        return list(self.core.items())

    def reference_files(self) -> list[tuple[str, str]]:
        return list(self.references.items())

    def build_id(self) -> str:
        """A deterministic content fingerprint of every input byte.  No clock involved."""
        digest = hashlib.sha256()
        parts: list[tuple[str, str]] = []
        for prefix, mapping in (
            ("core", self.core),
            ("references", self.references),
            ("engine", self.engine),
            ("templates", self.templates),
            ("data", self.rates),
        ):
            for name in sorted(mapping):
                parts.append((f"{prefix}/{name}", mapping[name]))
        digest.update(f"{PROJECT_NAME}\0{PROJECT_VERSION}\0".encode("utf-8"))
        for name, text in parts:
            digest.update(name.encode("utf-8"))
            digest.update(b"\0")
            digest.update(text.encode("utf-8"))
            digest.update(b"\0")
        return digest.hexdigest()[:12]


def _read_dir(directory: Path, pattern: str, key) -> dict[str, str]:
    """Read a directory into ``{filename: normalised text}``, deterministically ordered."""
    if not directory.is_dir():
        return {}
    paths = sorted((p for p in directory.glob(pattern) if p.is_file()), key=key)
    result: dict[str, str] = {}
    for path in paths:
        if path.name.startswith("."):
            continue
        try:
            result[path.name] = normalise(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError as exc:
            raise BuildError(
                f"{path} is not valid UTF-8 ({exc}). Every TakaBooks source file is UTF-8; "
                "Bangla text depends on it."
            ) from exc
    return result


# ======================================================================================
# Checks and bundles
# ======================================================================================


@dataclass
class Check:
    """One measured limit.  ``hard`` checks fail the build; soft ones only warn."""

    target: str
    name: str
    value: int
    limit: int | None
    unit: str
    hard: bool
    ok: bool
    detail: str = ""

    @property
    def status(self) -> str:
        if self.ok:
            return "ok"
        return "FAIL" if self.hard else "warn"

    def render(self) -> str:
        limit = "—" if self.limit is None else f"{self.limit:,}"
        head = f"  [{self.status:>4}] {self.target}/{self.name}: {self.value:,} {self.unit}"
        if self.limit is not None:
            head += f" (limit {limit})"
        if self.detail:
            head += f"\n         {self.detail}"
        return head

    def to_dict(self) -> dict[str, object]:
        return {
            "target": self.target,
            "name": self.name,
            "value": self.value,
            "limit": self.limit,
            "unit": self.unit,
            "hard": self.hard,
            "ok": self.ok,
            "status": self.status,
            "detail": self.detail,
        }


def limit_check(
    target: str,
    name: str,
    value: int,
    limit: int,
    unit: str,
    hard: bool,
    detail: str = "",
) -> Check:
    return Check(target, name, value, limit, unit, hard, value <= limit, detail)


@dataclass
class Bundle:
    """An in-memory build result.  Nothing reaches the disk until every hard check passes."""

    target: str
    files: dict[str, str] = field(default_factory=dict)
    executable: set[str] = field(default_factory=set)
    checks: list[Check] = field(default_factory=list)
    clean_dir: str | None = None
    zips: list[tuple[str, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def add(self, relpath: str, text: str, executable: bool = False) -> None:
        if relpath in self.files:
            raise BuildError(f"{self.target}: refusing to emit {relpath} twice.")
        self.files[relpath] = normalise(text)
        if executable:
            self.executable.add(relpath)

    def total_bytes(self) -> int:
        return sum(len(text.encode("utf-8")) for text in self.files.values())

    def failures(self) -> list[Check]:
        return [check for check in self.checks if check.hard and not check.ok]

    def warnings(self) -> list[Check]:
        return [check for check in self.checks if not check.hard and not check.ok]


# ======================================================================================
# Shared document fragments (build-owned prose — contains no tax figures)
# ======================================================================================


def engine_usage_markdown(
    tree: SourceTree,
    script_dir: str = "scripts",
    location: str = "inside this skill folder",
) -> str:
    """The 'how to run the engine' document, generated from the scripts that actually exist.

    ``script_dir`` and ``location`` say where the scripts are *for the reader of this
    particular bundle*: ``scripts/`` inside the skill folder, ``src/engine/`` in a clone
    for everyone else.
    """
    lines = [
        "# Running the TakaBooks engine",
        "",
        "The engine is the half of TakaBooks that is allowed to do arithmetic. It is pure "
        "Python 3.11+ standard library — no `pip install`, no network. The scripts live in "
        f"`{script_dir}/` {location}.",
        "",
        "## Scripts",
        "",
        "| Script | What it does |",
        "| --- | --- |",
    ]
    if tree.engine:
        for name, source in tree.engine.items():
            lines.append(f"| `{script_dir}/{name}` | {module_purpose(name, source)} |")
    else:
        lines.append("| _(no engine scripts were present at build time)_ | |")

    lines += [
        "",
        "## Common flags",
        "",
        "Every script accepts:",
        "",
        "- `--help` — what it does and how to call it.",
        "- `--books <dir>` — the books directory (default `./books`).",
        "- `--json` — machine-readable output, for you to parse.",
        "",
        "Every script exits **non-zero** on any integrity failure — an unbalanced entry, an "
        "unknown account code, a duplicate `entry_id`. A non-zero exit is a refusal, not a "
        "warning: report it to the user and stop. Silent correction is forbidden.",
        "",
        "## A typical session",
        "",
        fenced(
            "\n".join(
                [
                    "# 1. create a fresh set of books",
                    f"python3 {script_dir}/init_books.py --books ./books",
                    "",
                    "# 2. record a transaction (one journal entry, many posting lines)",
                    f"python3 {script_dir}/post.py --books ./books --help",
                    "",
                    "# 3. check the whole ledger before you trust any report",
                    f"python3 {script_dir}/validate.py --books ./books --json",
                    "",
                    "# 4. statements, VAT position, income tax",
                    f"python3 {script_dir}/report.py --books ./books --json",
                    f"python3 {script_dir}/vat.py --books ./books --json",
                    f"python3 {script_dir}/tax.py --books ./books --json",
                ]
            ),
            "bash",
        ),
        "",
        "## If you cannot execute Python",
        "",
        "Many chat surfaces cannot run a script. In that case **do not compute the answer "
        "yourself.** Instead give the user:",
        "",
        "1. the classification — which accounts the transaction debits and credits,",
        "2. the account codes from `accounts.toml`,",
        "3. the `tax_tag` for each line,",
        "4. the formula in words, and",
        "5. the exact command to run locally, asking them to paste the JSON back.",
        "",
        "## Journal CSV schema",
        "",
        "`books/journal/YYYY-MM.csv`, one row per posting line, amounts as human-readable "
        "BDT decimals (so the file opens correctly in Excel) and converted to integer paisa "
        "on read:",
        "",
        fenced(
            "date,entry_id,description,account,debit,credit,party,doc_ref,tax_tag,memo",
            "csv",
        ),
        "",
        "- `date` — ISO `YYYY-MM-DD`.",
        "- `entry_id` — groups rows into one journal entry; **all rows sharing an "
        "`entry_id` must balance**.",
        "- `account` — a code from `accounts.toml`; an unknown code is a hard error.",
        "- `debit` / `credit` — decimal BDT; exactly one of the two is non-zero per row.",
        "- `tax_tag` — `VAT:OUT:<rate>` output VAT · `VAT:IN:<rate>` rebateable input VAT · "
        "`TDS:<section>:<rate>` · `VDS:<rate>` · `NONE` when not tax-relevant.",
        "- `memo` — free text, always the last column so commas inside it survive.",
        "",
        "## Money",
        "",
        "1 BDT = 100 paisa. All internal arithmetic is `int` paisa — never `float`. Text "
        "amounts are parsed with `decimal.Decimal`, and rounding is `ROUND_HALF_UP` applied "
        "once, at the final step. Display in the Bangladeshi লাখ/কোটি grouping by default "
        "(`৳ 12,34,567.89`); the international grouping (`1,234,567.89`) is available when "
        "asked for. Always state the unit.",
    ]

    if tree.templates:
        lines += ["", "## Templates", ""]
        for name, text in tree.templates.items():
            suffix = Path(name).suffix
            lines += [
                f"### `{name}`",
                "",
                fenced(text, language_for(suffix)),
                "",
            ]

    return "\n".join(lines).rstrip() + "\n"


def rates_markdown(tree: SourceTree) -> str:
    """The rates TOML rendered as Markdown, because `.toml` is not an accepted upload type.

    The TOML travels verbatim inside a fenced block: lossless, exactly quotable, and it
    keeps every `source` URL and `verified` flag intact.  Nothing is summarised, because
    summarising a rate table is how a wrong number reaches NBR.
    """
    if not tree.rates:
        return (
            "# Rates — NOT AVAILABLE\n"
            "\n"
            "No `rates-AY<year>.toml` was present when this bundle was built. **Do not "
            "state any rate, threshold or deadline.** Tell the user the figure is "
            "unavailable in this bundle and that they must confirm it with the National "
            "Board of Revenue (NBR).\n"
        )
    lines = [
        f"# Rates and thresholds — assessment year {tree.assessment_year}",
        "",
        f"Source file: `src/data/{tree.rates_filename}` — reproduced below **verbatim**, "
        "with every `source` URL and every `verified` flag intact.",
        "",
        "How to use it:",
        "",
        "- Quote a figure only if you can point at the key it came from.",
        "- If the entry carries `verified = false`, say so in your answer and tell the user "
        "to confirm with NBR before filing.",
        f"- State the assessment year (**{tree.assessment_year}**) in every tax output.",
        "- Never interpolate, average or update a rate. A rate that is not in this file "
        "does not exist for you.",
        "",
        "## The data",
        "",
        fenced(tree.rates_text, "toml"),
    ]
    return "\n".join(lines).rstrip() + "\n"


def compact_core_text(tree: SourceTree) -> str:
    """`src/core/` concatenated for the two character-capped instruction targets."""
    chunks: list[str] = []
    for name, text in tree.core_files():
        body = strip_knowledge_only(text).strip()
        if body:
            chunks.append(body)
    return "\n\n".join(chunks)


def install_readme(target: str, tree: SourceTree, body: str) -> str:
    return (
        f"# Installing {PROJECT_NAME} — {target}\n"
        "\n"
        f"{body.rstrip()}\n"
        "\n"
        "---\n"
        "\n"
        f"{DISCLAIMER}\n"
        "\n"
        f"{ATTRIBUTION}  \n"
        f"Assessment year: {tree.assessment_year} · Build id: `{tree.build_id()}`\n"
    )


# ======================================================================================
# Target: claude-skill
# ======================================================================================


def skill_frontmatter(tree: SourceTree) -> str:
    fields = [
        ("name", SKILL_NAME),
        ("description", SKILL_DESCRIPTION),
        ("license", LICENSE_NAME),
        ("compatibility", SKILL_COMPATIBILITY),
    ]
    lines = ["---"]
    for key, value in fields:
        lines.append(f"{key}: {yaml_double_quote(value)}")
    lines.append("metadata:")
    for key, value in (
        ("author", COMPANY),
        ("homepage", COMPANY_URL),
        ("maintainer", MAINTAINER),
        ("version", PROJECT_VERSION),
        ("assessment_year", tree.assessment_year),
        ("repository", REPO_URL),
        ("build_id", tree.build_id()),
    ):
        lines.append(f"  {key}: {yaml_double_quote(value)}")
    lines.append("---")
    return "\n".join(lines)


def skill_markdown(tree: SourceTree) -> str:
    """`SKILL.md` — frontmatter, the core instruction verbatim, then where everything is.

    Level 2 of progressive disclosure: this whole file loads when the skill triggers, so
    the detail lives one relative link away in ``references/`` and the arithmetic lives
    one bash call away in ``scripts/``.  The rules come from ``src/core/`` and are not
    restated here; the sections after the core only say where things are in this folder.
    """
    parts = [skill_frontmatter(tree), ""]
    parts.append(
        f"# {PROJECT_NAME} — Bangladeshi bookkeeping & taxation "
        f"(assessment year {tree.assessment_year})"
    )
    parts.append("")

    if tree.core:
        for _name, text in tree.core_files():
            body = drop_knowledge_only_markers(text).strip()
            if body:
                parts.append(shift_headings(body, 2).strip())
                parts.append("")
    else:
        parts.append("_`src/core/` was empty when this bundle was built._")
        parts.append("")

    parts.append("## Where everything is in this skill folder")
    parts.append("")
    parts.append(
        "The instruction above names files by their bare names. In this folder they are:"
    )
    parts.append("")

    parts.append("### References — load one when the question needs it")
    parts.append("")
    if tree.references:
        for name in tree.references:
            stem = Path(name).stem
            title = REFERENCE_TITLES.get(stem, stem.replace("-", " "))
            parts.append(f"- [`references/{name}`](references/{name}) — {title}")
    else:
        parts.append("_No reference files were present at build time._")
    parts.append("")

    parts.append("### Rates data")
    parts.append("")
    if tree.rates:
        parts.append(
            f"[`data/{tree.rates_filename}`](data/{tree.rates_filename}) — assessment year "
            f"{tree.assessment_year}. The scripts read it from there; you quote it, never "
            "memory. Each entry carries a `source` URL and a `verified` flag."
        )
    else:
        parts.append(
            "_No rates file was present at build time. Do not state any rate, threshold or "
            "deadline; say the figure is unavailable and send the user to NBR._"
        )
    parts.append("")

    parts.append("### Scripts — the only thing allowed to do arithmetic")
    parts.append("")
    if tree.engine:
        parts.append("| Script | What it does |")
        parts.append("| --- | --- |")
        for name, source in tree.engine.items():
            parts.append(f"| `scripts/{name}` | {module_purpose(name, source)} |")
        parts.append("")
        parts.append(
            "Run them with bash from this folder. Their source never enters your context — "
            "only their stdout does, which is exactly the point. Every script takes "
            "`--help`, `--books <dir>` (default `./books`) and `--json`, and exits non-zero "
            "on any integrity failure. A non-zero exit is a refusal: report it and stop."
        )
        parts.append("")
        parts.append(fenced("python3 scripts/validate.py --books ./books --json", "bash"))
        parts.append("")
        parts.append("Full engine guide: [`scripts/USAGE.md`](scripts/USAGE.md).")
    else:
        parts.append("_No engine scripts were present at build time._")
    parts.append("")

    if tree.templates:
        parts.append("### Templates")
        parts.append("")
        parts.append(
            "Starting `accounts.toml`, `config.toml` and the journal header. "
            "`scripts/init_books.py` copies them into a new `books/` directory; scripts "
            "only ever *read* TOML — humans and you edit it."
        )
        parts.append("")
        for name in tree.templates:
            parts.append(f"- [`templates/{name}`](templates/{name})")
        parts.append("")

    parts.append("---")
    parts.append("")
    parts.append(ATTRIBUTION)
    return "\n".join(parts).rstrip() + "\n"


def build_claude_skill(tree: SourceTree) -> Bundle:
    bundle = Bundle(target="claude-skill", clean_dir="dist/claude-skill")
    root = f"dist/claude-skill/{SKILL_NAME}"

    skill_text = skill_markdown(tree)
    bundle.add(f"{root}/SKILL.md", skill_text)

    for name, text in tree.reference_files():
        bundle.add(f"{root}/references/{name}", drop_knowledge_only_markers(text))
    for name, text in tree.engine.items():
        bundle.add(f"{root}/scripts/{name}", text, executable=True)
    bundle.add(f"{root}/scripts/USAGE.md", engine_usage_markdown(tree, "scripts"))
    for name, text in tree.templates.items():
        bundle.add(f"{root}/templates/{name}", text)
    # `data/`, not `assets/`: rates.py resolves its data directory as
    # `<script dir>/../data/`, and the core instruction names `data/rates-AY<year>.toml`.
    # Either would break if the file sat anywhere else.
    for name, text in tree.rates.items():
        bundle.add(f"{root}/data/{name}", text)

    bundle.add(
        "dist/claude-skill/README-install.md",
        install_readme(
            "Claude (claude.ai, Claude Code, Claude API)",
            tree,
            "\n".join(
                [
                    "## claude.ai",
                    "",
                    "1. Settings → Features → Skills → upload "
                    f"`{SKILL_NAME}.zip`. Code execution must be enabled.",
                    f"2. The zip has the `{SKILL_NAME}/` folder at its root, which is the "
                    "layout claude.ai expects.",
                    "3. Skills uploaded on claude.ai are per-user. There is no org-wide "
                    "management, and they do **not** sync to the API or to Claude Code.",
                    "",
                    "## Claude Code",
                    "",
                    "Unzip the same artifact into either location:",
                    "",
                    fenced(
                        "\n".join(
                            [
                                "# personal — available in every project",
                                f"unzip {SKILL_NAME}.zip -d ~/.claude/skills/",
                                "",
                                "# project — checked in with the repository",
                                f"unzip {SKILL_NAME}.zip -d .claude/skills/",
                            ]
                        ),
                        "bash",
                    ),
                    "",
                    "A personal skill overrides a project skill of the same name; an "
                    "enterprise-managed one overrides both.",
                    "",
                    "## Claude API",
                    "",
                    f"Upload the same zip to `/v1/skills`. `{SKILL_NAME}/SKILL.md` sits at "
                    "the top of a single enclosing folder, which is what the endpoint "
                    "expects. Versions are complete snapshots, not deltas — re-upload the "
                    "whole file set every time. The API sandbox has no network access and "
                    "cannot install packages; TakaBooks needs neither.",
                    "",
                    "## Other Agent Skills hosts",
                    "",
                    "`SKILL.md` follows the open Agent Skills standard, so the same folder "
                    "also works with any tool that reads it — Codex CLI "
                    "(`~/.codex/skills/`), Gemini CLI, Cursor, VS Code and others.",
                ]
            ),
        ),
    )

    bundle.zips.append((f"dist/claude-skill/{SKILL_NAME}.zip", root))

    # --- checks -------------------------------------------------------------------------
    name_ok = bool(SKILL_NAME_RE.match(SKILL_NAME))
    bundle.checks.append(
        limit_check(
            "claude-skill",
            "frontmatter.name",
            len(SKILL_NAME),
            SKILL_NAME_MAX_CHARS,
            "chars",
            hard=True,
        )
    )
    bundle.checks.append(
        Check(
            "claude-skill",
            "frontmatter.name.format",
            len(SKILL_NAME),
            None,
            "chars",
            hard=True,
            ok=name_ok
            and not any(word in SKILL_NAME for word in SKILL_NAME_FORBIDDEN)
            and SKILL_NAME == Path(root).name,
            detail=(
                "must be lowercase a-z0-9 with single hyphens, must not contain "
                "'claude' or 'anthropic', and must equal the parent directory name"
            ),
        )
    )
    bundle.checks.append(
        limit_check(
            "claude-skill",
            "frontmatter.description",
            len(SKILL_DESCRIPTION),
            SKILL_DESCRIPTION_MAX_CHARS,
            "chars",
            hard=True,
            detail=(
                "the claude.ai upload UI caps this at 200 even though the open spec "
                "allows 1024; 200 is the portable value"
            ),
        )
    )
    bundle.checks.append(
        Check(
            "claude-skill",
            "frontmatter.description.nonempty",
            len(SKILL_DESCRIPTION),
            None,
            "chars",
            hard=True,
            ok=bool(SKILL_DESCRIPTION.strip()),
        )
    )
    bundle.checks.append(
        limit_check(
            "claude-skill",
            "frontmatter.compatibility",
            len(SKILL_COMPATIBILITY),
            SKILL_COMPATIBILITY_MAX_CHARS,
            "chars",
            hard=True,
        )
    )
    bundle.checks.append(
        limit_check(
            "claude-skill",
            "SKILL.md.lines",
            len(skill_text.rstrip("\n").split("\n")),
            SKILL_BODY_MAX_LINES,
            "lines",
            hard=False,
            detail="recommendation, not a hard cap — move detail into references/",
        )
    )
    bundle.checks.append(
        limit_check(
            "claude-skill",
            "SKILL.md.tokens",
            estimate_tokens(skill_text),
            SKILL_BODY_MAX_TOKENS,
            "est. tokens",
            hard=False,
            detail="estimate = UTF-8 bytes / 4; recommendation, not a hard cap",
        )
    )
    bundle.checks.append(
        limit_check(
            "claude-skill",
            "bundle.size",
            bundle.total_bytes(),
            SKILL_BUNDLE_MAX_BYTES,
            "bytes",
            hard=True,
            detail="Skills API refuses an upload of 30 MB or more (uncompressed)",
        )
    )
    return bundle


# ======================================================================================
# Target: chatgpt
# ======================================================================================


def chatgpt_rates_knowledge_name(tree: SourceTree) -> str:
    """``rates-AY2026-27.toml`` → ``rates-AY2026-27.md``: same stem, an accepted suffix."""
    return f"{Path(tree.rates_filename).stem}.md" if tree.rates else ""


def chatgpt_knowledge(tree: SourceTree) -> list[tuple[str, str]]:
    """Knowledge files, ≤ 20, each source document whole and under its own basename.

    The core's routing table says "load `vat-mushak.md`"; a knowledge file with exactly
    that name is what makes the instruction true inside a Custom GPT without spending
    instruction characters on a name map.  The core files ride along too — the copy in
    knowledge keeps any ``knowledge-only`` passages the instruction had to drop.
    """
    files: list[tuple[str, str]] = []
    for name, text in tree.core_files():
        files.append((name, drop_knowledge_only_markers(text)))
    for name, text in tree.reference_files():
        files.append((name, text))
    if tree.rates:
        files.append((chatgpt_rates_knowledge_name(tree), rates_markdown(tree)))
    files.append(
        ("engine-usage.md", engine_usage_markdown(tree, "src/engine", CLONE_LOCATION))
    )
    return files


def chatgpt_footer(tree: SourceTree) -> str:
    """The only text the build adds to the Custom GPT instruction: where the files are.

    Kept to a few lines on purpose — every character here is a character ``src/core/``
    cannot use.  The rules themselves are in the core; this just makes its file names
    resolve inside a GPT whose knowledge is a flat list of uploads.
    """
    if tree.rates:
        rates = (
            f"`data/{tree.rates_filename}` as `{chatgpt_rates_knowledge_name(tree)}` "
            "(TOML verbatim)"
        )
    else:
        rates = "no rates file — state no figure"
    return (
        "## Knowledge files\n"
        f"`references/*.md` are attached by name; {rates}; `engine-usage.md` shows how to "
        "run the scripts. Open a file before answering from it."
    )


def chatgpt_instructions(tree: SourceTree) -> str:
    """`src/core/` verbatim (minus ``knowledge-only`` passages) plus the navigation footer.

    Nothing else.  The 8,000-character field is the binding constraint of the whole
    project (spec §5), so the build spends none of it restating what the core says.
    """
    pieces = [piece for piece in (compact_core_text(tree), chatgpt_footer(tree)) if piece]
    return "\n\n".join(pieces).rstrip() + "\n"


def build_chatgpt(tree: SourceTree) -> Bundle:
    bundle = Bundle(target="chatgpt", clean_dir="dist/chatgpt")
    knowledge = chatgpt_knowledge(tree)
    for name, text in knowledge:
        bundle.add(f"dist/chatgpt/knowledge/{name}", text)

    instructions = chatgpt_instructions(tree)
    bundle.add("dist/chatgpt/instructions.md", instructions)

    rates_knowledge = chatgpt_rates_knowledge_name(tree) or "the rates file"
    bundle.add(
        "dist/chatgpt/README-install.md",
        install_readme(
            "ChatGPT",
            tree,
            "\n".join(
                [
                    "## Custom GPT (Free, Plus, Pro)",
                    "",
                    "1. ChatGPT → Explore GPTs → Create.",
                    "2. Configure → paste the whole of `instructions.md` into "
                    "**Instructions**. It is built to fit the 8,000-character field; the "
                    "build fails rather than emit an over-long file.",
                    "3. Knowledge → upload every file in `knowledge/`. A Custom GPT holds "
                    f"up to {CHATGPT_KNOWLEDGE_MAX_FILES} knowledge files; this bundle "
                    f"ships {len(knowledge)}. Keep the file names: the instruction refers "
                    "to them by name.",
                    "4. The engine scripts are not in the knowledge set — the GPT explains "
                    "and classifies; the numbers come from running the scripts locally, "
                    "as `engine-usage.md` describes.",
                    "",
                    f"The rates file is shipped as `{rates_knowledge}`: Markdown with the "
                    "TOML inside a fenced block, because `.toml` is not on any published "
                    "list of accepted upload types. The values are byte-identical to "
                    "`src/data/`.",
                    "",
                    "## Projects",
                    "",
                    "Paste `instructions.md` into the project instructions and add the "
                    "`knowledge/` files. A project holds fewer files than a Custom GPT "
                    "(5 on Free), so on a small plan add, in order: "
                    f"`{rates_knowledge}`, `30-tax-overview.md`, then the reference you "
                    "need for the task.",
                    "",
                    "## ChatGPT Skills and Codex CLI",
                    "",
                    "Both read the open Agent Skills format, so use the Claude Skill "
                    f"bundle instead: `dist/claude-skill/{SKILL_NAME}/`. Drop it in "
                    f"`~/.codex/skills/{SKILL_NAME}/` for Codex CLI, or upload the zip "
                    "under Skills in ChatGPT. Skills in ChatGPT are limited to Business, "
                    "Enterprise, Healthcare and Edu plans, and an admin may have to enable "
                    "them first.",
                ]
            ),
        ),
    )

    # The budget is printed on every build, not only on failure: the core's author needs
    # to know how much of the 8,000 the navigation footer takes and how much is left.
    used = len(instructions)
    core_chars = len(compact_core_text(tree))
    footer_chars = used - core_chars
    headroom = CHATGPT_INSTRUCTIONS_MAX_CHARS - used
    per_file = ", ".join(
        f"{name} {len(strip_knowledge_only(text).strip()):,}"
        for name, text in tree.core_files()
    )
    detail = (
        f"src/core/ {core_chars:,} + navigation footer {footer_chars:,} = {used:,} of "
        f"{CHATGPT_INSTRUCTIONS_MAX_CHARS:,} characters; headroom {headroom:,} "
        f"({per_file or 'no core files'})"
    )
    if headroom < 0:
        detail = (
            f"OVER BY {-headroom:,} characters. src/core/ contributes {core_chars:,} "
            f"({per_file or 'no core files'}); the navigation footer contributes "
            f"{footer_chars:,}. Cut src/core/, or wrap reference material in "
            f"{KNOWLEDGE_ONLY_OPEN} ... {KNOWLEDGE_ONLY_CLOSE} so it ships in knowledge/ "
            "instead of in the instruction."
        )
    bundle.checks.append(
        limit_check(
            "chatgpt",
            "instructions.md",
            len(instructions),
            CHATGPT_INSTRUCTIONS_MAX_CHARS,
            "chars",
            hard=True,
            detail=detail,
        )
    )
    bundle.checks.append(
        Check(
            "chatgpt",
            "instructions.md.bytes",
            len(instructions.encode("utf-8")),
            None,
            "UTF-8 bytes",
            hard=False,
            ok=True,
            detail="informational — Bangla codepoints are 3 bytes each; the cap counts "
            "characters, not bytes",
        )
    )
    bundle.checks.append(
        limit_check(
            "chatgpt",
            "knowledge.files",
            len(knowledge),
            CHATGPT_KNOWLEDGE_MAX_FILES,
            "files",
            hard=True,
            detail="a Custom GPT accepts at most 20 knowledge files",
        )
    )
    return bundle


# ======================================================================================
# Target: gemini
#
# Ten source documents is the tightest packaging cap of any platform researched, so the
# knowledge set is MERGED at file level.  Never truncated: truncation would drop a
# `source` URL or a `verified` flag, and a rate without its provenance is a wrong rate.
# ======================================================================================

GEMINI_GROUPS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "1-core-bookkeeping.md",
        "Identity, workflow and bookkeeping rules",
        ("core:00-identity", "core:10-workflow", "core:20-bookkeeping"),
    ),
    ("2-income-tax.md", REFERENCE_TITLES["income-tax"], ("ref:income-tax",)),
    ("3-vat-mushak.md", REFERENCE_TITLES["vat-mushak"], ("ref:vat-mushak",)),
    (
        "4-withholding-tds-vds.md",
        REFERENCE_TITLES["withholding-tds-vds"],
        ("ref:withholding-tds-vds",),
    ),
    (
        "5-payroll-standards-and-other.md",
        "Payroll, bookkeeping standards and any other reference",
        ("ref:payroll", "ref:bookkeeping-standards"),
    ),
    (
        "6-calendar-and-penalties.md",
        "Compliance calendar, penalties and interest",
        ("ref:compliance-calendar", "ref:penalties"),
    ),
    ("7-rates.md", "Rates and thresholds", ("generated:rates",)),
    ("8-glossary-bn-en.md", REFERENCE_TITLES["glossary-bn-en"], ("ref:glossary-bn-en",)),
    ("9-engine-usage.md", "Running the engine", ("generated:engine",)),
    ("10-tax-routing.md", CORE_TITLES["30-tax-overview"], ("core:30-tax-overview",)),
)

# Reference files that no group claims are appended here, so nothing is ever dropped.
GEMINI_OVERFLOW_GROUP = "5-payroll-standards-and-other.md"


def build_gemini_knowledge(tree: SourceTree) -> tuple[list[tuple[str, str]], list[str], list[str]]:
    """Return ``(files, notes, unplaced)``.

    ``unplaced`` must always be empty — it exists so the build can fail loudly rather
    than silently drop a source document into the 10-file cap.
    """
    claimed: set[str] = set()
    for _, _, keys in GEMINI_GROUPS:
        claimed.update(keys)

    overflow_keys: list[str] = []
    for name in tree.references:
        key = f"ref:{Path(name).stem}"
        if key not in claimed:
            overflow_keys.append(key)
    for name in tree.core:
        key = f"core:{Path(name).stem}"
        if key not in claimed:
            overflow_keys.append(key)

    def source_for(key: str) -> tuple[str, str] | None:
        kind, _, stem = key.partition(":")
        if kind == "core":
            text = tree.core.get(f"{stem}.md")
            if text is None:
                return None
            title = CORE_TITLES.get(stem, stem.replace("-", " "))
            return title, drop_knowledge_only_markers(text)
        if kind == "ref":
            text = tree.references.get(f"{stem}.md")
            if text is None:
                return None
            title = REFERENCE_TITLES.get(stem, stem.replace("-", " "))
            return title, text
        if kind == "generated" and stem == "rates":
            return None if not tree.rates else ("Rates", rates_markdown(tree))
        if kind == "generated" and stem == "engine":
            return "Engine", engine_usage_markdown(tree, "src/engine", CLONE_LOCATION)
        return None

    files: list[tuple[str, str]] = []
    notes: list[str] = []
    placed: set[str] = set()

    for filename, group_title, keys in GEMINI_GROUPS:
        keys = list(keys)
        if filename == GEMINI_OVERFLOW_GROUP:
            keys.extend(overflow_keys)
        chunks: list[str] = []
        merged: list[str] = []
        for key in keys:
            source = source_for(key)
            if source is None:
                continue
            title, text = source
            placed.add(key)
            merged.append(key)
            if key.startswith("generated:"):
                chunks.append(shift_headings(text.strip(), 2))
            else:
                chunks.append(f"## {title}\n\n{shift_headings(text.strip(), 3)}")
        if not chunks:
            continue
        body = "\n\n---\n\n".join(chunks)
        files.append((filename, f"# {group_title}\n\n{body}\n"))
        notes.append(f"{filename} ← {', '.join(merged)}")

    available = {f"core:{Path(n).stem}" for n in tree.core}
    available |= {f"ref:{Path(n).stem}" for n in tree.references}
    if tree.rates:
        available.add("generated:rates")
    available.add("generated:engine")
    unplaced = sorted(available - placed)
    return files, notes, unplaced


def gemini_instructions(tree: SourceTree, knowledge_names: list[str]) -> str:
    """Google's own four-block shape: Persona, Task, Context, Format.

    Gems drift away from their knowledge files under long instructions, so only the four
    rules that cannot be delegated live here: the assessment year, the `verified = false`
    caveat, the user's language, and the disclaimer.
    """
    listing = ", ".join(f"`{name}`" for name in knowledge_names) or "(none in this build)"
    lines = [
        f"**Persona.** You are {PROJECT_NAME}, a Bangladeshi bookkeeping and taxation "
        "assistant: double-entry books (খতিয়ান / ledger), VAT / মূসক, উৎসে কর কর্তন / TDS, "
        "VDS and income tax, all in BDT / টাকা (৳). You are not a licensed ITP or CA.",
        "",
        "**Task.** Classify transactions into accounts, choose the right Mushak form and "
        "TDS section, explain the rule, and prepare filing figures. You never do "
        "arithmetic: the TakaBooks Python engine computes every number. If you cannot run "
        "it, give the accounts, the `tax_tag` and the formula, and ask the user to run the "
        "script and paste the output back.",
        "",
        f"**Context.** Your knowledge files are {listing}. Every rate, threshold and "
        "deadline comes from the rates file and nowhere else — never from memory, never "
        "interpolated. If a figure is marked `verified = false`, say so and tell the user "
        "to confirm with the National Board of Revenue (NBR). If a figure is not in the "
        "file, say it is unavailable.",
        "",
        f"**Format.** State the assessment year ({tree.assessment_year}) in every tax "
        "computation. Give the Bangla statutory term beside the English one so the user "
        "can find the form on the NBR portal. Reply in the user's language — Bangla, "
        "Banglish or English — and reason in English. Show amounts in the লাখ/কোটি "
        "grouping (৳ 12,34,567.89). End every tax answer with: not professional advice; "
        "verify with a licensed ITP or CA before filing.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_gemini(tree: SourceTree, soft_limit: int = GEMINI_INSTRUCTIONS_SOFT_CHARS) -> Bundle:
    bundle = Bundle(target="gemini", clean_dir="dist/gemini")
    knowledge, notes, unplaced = build_gemini_knowledge(tree)
    bundle.notes.extend(notes)

    for name, text in knowledge:
        bundle.add(f"dist/gemini/knowledge/{name}", text)

    instructions = gemini_instructions(tree, [name for name, _ in knowledge])
    bundle.add("dist/gemini/gem-instructions.md", instructions)

    bundle.add(
        "dist/gemini/README-install.md",
        install_readme(
            "Gemini Gems",
            tree,
            "\n".join(
                [
                    "1. Gemini → Gems → New Gem.",
                    "2. Paste `gem-instructions.md` into **Instructions**.",
                    "3. Knowledge → add every file in `knowledge/`. A Gem supports up to "
                    f"{GEMINI_KNOWLEDGE_MAX_FILES} source documents, which is why these "
                    f"files are merged; this bundle ships {len(knowledge)}.",
                    "",
                    "## Why the files are merged",
                    "",
                    "Ten documents is the tightest packaging cap of any platform TakaBooks "
                    "targets. The merge is at whole-file level, never a truncation, so "
                    "every `source` URL and every `verified` flag survives intact.",
                    "",
                    "## Keeping rates current without re-uploading",
                    "",
                    "Gemini reads the latest version of a Google Doc or Sheet from Drive "
                    "automatically, but other file types must be re-uploaded by hand. If "
                    "you publish the rates file as a Google Doc and add it from Drive, a "
                    "Finance Act update reaches every Gem that uses it without any "
                    "re-upload.",
                    "",
                    "## A note on the instruction length",
                    "",
                    "Google publishes no character limit for Gem instructions. TakaBooks "
                    f"targets {soft_limit:,} characters because longer instructions are "
                    "widely reported to make a Gem start ignoring its own knowledge files. "
                    "It is a warning in the build, never a hard failure — gating on an "
                    "undocumented number would be inventing a limit.",
                ]
            ),
        ),
    )

    bundle.checks.append(
        limit_check(
            "gemini",
            "knowledge.files",
            len(knowledge),
            GEMINI_KNOWLEDGE_MAX_FILES,
            "files",
            hard=True,
            detail="a Gem supports at most 10 source documents — merge, never truncate",
        )
    )
    bundle.checks.append(
        Check(
            "gemini",
            "knowledge.coverage",
            len(unplaced),
            0,
            "unplaced sources",
            hard=True,
            ok=not unplaced,
            detail=(
                "every source document must land in exactly one knowledge file; unplaced: "
                + ", ".join(unplaced)
            )
            if unplaced
            else "every source document lands in exactly one knowledge file",
        )
    )
    bundle.checks.append(
        limit_check(
            "gemini",
            "gem-instructions.md",
            len(instructions),
            soft_limit,
            "chars",
            hard=False,
            detail=(
                "SOFT target — Google publishes no limit. Over-long instructions are "
                "reported to make a Gem ignore its knowledge files."
            ),
        )
    )
    return bundle


# ======================================================================================
# Target: universal
# ======================================================================================


def build_universal(tree: SourceTree) -> Bundle:
    bundle = Bundle(target="universal", clean_dir="dist/universal")

    @dataclass
    class Section:
        number: int
        title: str
        body: str
        basenames: tuple[str, ...] = ()

    sections: list[Section] = []
    number = 1

    for name, text in tree.core_files():
        stem = Path(name).stem
        sections.append(
            Section(
                number,
                CORE_TITLES.get(stem, stem.replace("-", " ")),
                drop_knowledge_only_markers(text),
                (name,),
            )
        )
        number += 1
    for name, text in tree.reference_files():
        stem = Path(name).stem
        sections.append(
            Section(number, REFERENCE_TITLES.get(stem, stem.replace("-", " ")), text, (name,))
        )
        number += 1
    if tree.rates:
        sections.append(
            Section(
                number,
                f"Rates and thresholds — assessment year {tree.assessment_year}",
                rates_markdown(tree),
                (tree.rates_filename,),
            )
        )
        number += 1
    sections.append(
        Section(
            number,
            "Running the engine",
            engine_usage_markdown(tree, "src/engine", CLONE_LOCATION),
            tuple(tree.engine) + tuple(tree.templates),
        )
    )
    number += 1
    sections.append(Section(number, "Disclaimer / দাবিত্যাগ", DISCLAIMER))

    anchors: dict[str, str] = {}
    headings: dict[int, str] = {}
    for section in sections:
        heading = f"{section.number}. {section.title}"
        headings[section.number] = heading
        anchor = slugify(heading)
        for basename in section.basenames:
            anchors[basename] = anchor

    stop_block = "\n".join(
        [
            "STOP — READ THIS FIRST",
            "",
            f"Assessment year: {tree.assessment_year}. Currency: BDT / টাকা (৳); "
            "1 BDT = 100 paisa.",
            "",
            "1. You must not do arithmetic. The TakaBooks Python engine computes every",
            "   number. If you cannot run it, give the classification, the account codes,",
            "   the tax_tag and the formula in words, then ask the user to run the script",
            "   locally and paste the output back. Do not estimate. Do not add it up",
            "   yourself.",
            "2. Never invent a rate, threshold, deadline or statute number. Every figure",
            "   comes from the rates section of this file. If it carries verified = false,",
            "   repeat that caveat. If it is not in this file, say it is unavailable and",
            "   send the user to NBR. Absent beats wrong.",
            "3. State the assessment year in every tax computation.",
            "4. Give the Bangla statutory term beside the English one: মূসক / VAT,",
            "   উৎসে কর কর্তন / TDS, খতিয়ান / ledger. Reply in the user's language",
            "   (Bangla, Banglish or English); reason in English.",
            "5. End every tax answer with the disclaimer in the last section.",
            "",
            "This file is UTF-8 and contains Bangla text. Paste it whole; do not summarise",
            "it back to yourself.",
        ]
    )

    lines = [
        f"# {PROJECT_NAME} — Bangladeshi bookkeeping & taxation "
        f"(assessment year {tree.assessment_year})",
        "",
        "One paste-anywhere file: double-entry books (খতিয়ান / ledger), VAT / মূসক, "
        "উৎসে কর কর্তন / TDS, VDS, payroll and income tax for Bangladesh.",
        "",
        fenced(stop_block, "text"),
        "",
        "## How to use this file",
        "",
        "- **Any chat model** — paste the whole file as the first message, or upload it as "
        "a knowledge document, then ask your question.",
        "- **Ollama** — put the file inside `SYSTEM \"\"\"...\"\"\"` in a Modelfile.",
        "- **LM Studio** — paste it into the System Prompt field and save it as a preset.",
        "- **Anything with a filesystem** — prefer the platform bundle instead: the Claude "
        "Skill folder, the ChatGPT knowledge set, or the Gemini Gem. They give the model "
        "runnable scripts; this file only describes them.",
        "",
        "Everything below is one document. Cross-references are in-document anchors, "
        "because outside this file nothing exists.",
        "",
        "## Contents",
        "",
    ]
    for section in sections:
        heading = headings[section.number]
        lines.append(f"- [{heading}](#{slugify(heading)})")
    lines.append("")

    for section in sections:
        body = rewrite_links_to_anchors(section.body.strip(), anchors)
        body = shift_headings(body, 3)
        lines.append(f"## {headings[section.number]}")
        lines.append("")
        lines.append(body.strip())
        lines.append("")

    lines += [
        "---",
        "",
        DISCLAIMER,
        "",
        ATTRIBUTION,
        "",
        f"Build id: `{tree.build_id()}`",
    ]

    document = "\n".join(lines).rstrip() + "\n"
    bundle.add("dist/universal/takabooks-complete.md", document)

    # --- the paste-anywhere entry point -------------------------------------------------
    # A model with a 128K context cannot hold takabooks-complete.md.  takabooks-core.md
    # carries the behaviour (which is what must never be dropped) plus a map of what lives
    # in the complete file, so a small-context user pastes this and supplies the one
    # reference section their question needs.
    core_lines = [
        f"# {PROJECT_NAME} — core (small-context edition)",
        "",
        stop_block,
        "",
        "---",
        "",
        compact_core_text(tree),
        "",
        "---",
        "",
        "## What is NOT in this file",
        "",
        "This is the core instruction only. Every rate, threshold, deadline, form number and",
        "statute reference lives in `takabooks-complete.md`, alongside the full reference",
        "documents. **Do not answer a rate question from this file — it contains none.**",
        "Ask the user to paste the section you need, or to attach `takabooks-complete.md`:",
        "",
    ]
    for section in sections:
        core_lines.append(f"- {section.number}. {section.title}")
    core_lines += ["", "---", "", DISCLAIMER, "", ATTRIBUTION, "",
                   f"Build id: `{tree.build_id()}`"]
    core_doc = "\n".join(core_lines).rstrip() + "\n"
    bundle.add("dist/universal/takabooks-core.md", core_doc)

    bundle.checks.append(
        limit_check(
            "universal",
            "takabooks-core.md.tokens",
            estimate_tokens(core_doc),
            UNIVERSAL_CORE_SOFT_TOKENS,
            "est. tokens",
            hard=False,
            detail=(
                "SOFT budget — takabooks-core.md is the paste-anywhere file and must fit "
                "the smallest common context (128K) with room for the answer"
            ),
        )
    )
    bundle.checks.append(
        limit_check(
            "universal",
            "takabooks-core.md.bytes",
            len(core_doc.encode("utf-8")),
            UNIVERSAL_CORE_SOFT_BYTES,
            "bytes",
            hard=False,
            detail="SOFT budget, the same ceiling expressed in UTF-8 bytes",
        )
    )
    bundle.checks.append(
        limit_check(
            "universal",
            "takabooks-complete.md.tokens",
            estimate_tokens(document),
            UNIVERSAL_COMPLETE_SOFT_TOKENS,
            "est. tokens",
            hard=False,
            detail=(
                "SOFT budget — this file is lossless by design (the rates TOML travels "
                "verbatim), so it needs a large-context model or must be attached as a "
                "file. Small-context users take takabooks-core.md instead."
            ),
        )
    )
    bundle.checks.append(
        limit_check(
            "universal",
            "takabooks-complete.md.bytes",
            len(document.encode("utf-8")),
            UNIVERSAL_COMPLETE_SOFT_BYTES,
            "bytes",
            hard=False,
            detail="SOFT budget, the same ceiling expressed in UTF-8 bytes",
        )
    )
    return bundle


# ======================================================================================
# Target: agents-md
# ======================================================================================


def agents_markdown(tree: SourceTree) -> str:
    rates_line = (
        f"`src/data/{tree.rates_filename}` (assessment year {tree.assessment_year})"
        if tree.rates
        else "`src/data/rates-AY<year>.toml`"
    )
    reference_list = ", ".join(f"`{name}`" for name in tree.references) or "_(none yet)_"
    return f"""# {PROJECT_NAME} — instructions for coding agents

{PROJECT_NAME} is an LLM-agnostic bookkeeping and taxation package for **Bangladesh**. It
ships two halves: cited, versioned reference material on Bangladeshi tax, and a
dependency-free Python engine that maintains real double-entry books.

**Prime directive: the LLM never does arithmetic.** Deterministic Python owns every
number; the model owns classification and explanation. Any script that would emit an
unbalanced entry or an unreconciled report must exit non-zero with a clear error. Silent
correction is forbidden. A wrong number filed with the National Board of Revenue (NBR) is
worse than a refusal.

## Non-negotiable rules

1. **Never invent a Bangladeshi tax rate, threshold, deadline or statute number.** Every
   figure lives in {rates_line}, keyed by assessment year, each with a `source` URL and a
   `verified` boolean. If a figure could not be confirmed from a primary source it is
   `verified = false`, and every consumer must surface that caveat. Absent beats wrong.
   This rule has no exceptions.
2. **Standard library only.** No `pip install`, ever — the target user is an SME on an
   office laptop. Floor is Python 3.11 (`tomllib`); fail fast with a clear message below it.
3. **Money is `int` paisa, never `float`.** 1 BDT = 100 paisa. Parse text amounts with
   `decimal.Decimal`; round `ROUND_HALF_UP`, once, at the final step.
4. **`src/` is the source of truth. `dist/` is generated — never hand-edit it**, and never
   hand-edit the root `AGENTS.md` either: both come out of `build/build.py`.
5. **Carry the Bangla statutory term beside the English one** wherever a statutory term
   appears: মূসক / VAT, উৎসে কর কর্তন / TDS, খতিয়ান / ledger. Users need it to find the
   form on the NBR portal.
6. **Every tax output ends with the disclaimer**: not professional advice, verify with a
   licensed Income Tax Practitioner (ITP) or Chartered Accountant (CA) before filing.

## Repository layout

| Path | What it is |
| --- | --- |
| `src/core/` | The always-loaded instruction: identity, workflow, bookkeeping rules, tax routing. |
| `src/references/` | Deep reference, one file per subject: {reference_list} |
| `src/data/` | `rates-AY<year>.toml` — every rate and threshold, machine-readable. |
| `src/engine/` | The Python engine, standard library only. |
| `src/templates/` | `accounts.toml`, `config.toml`, journal header. |
| `build/build.py` | Emits every platform bundle in `dist/`, plus this file. |
| `dist/` | Generated bundles. Attached to releases. |
| `tests/` | `unittest` suite. |

## Setup and build

```bash
python3 build/build.py            # build every target into dist/ (and rewrite AGENTS.md)
python3 build/build.py --check    # verify every platform limit, write nothing
python3 build/build.py --clean    # wipe dist/ first
python3 build/build.py --target chatgpt
```

The build is deterministic and idempotent: the same `src/` bytes produce byte-identical
`dist/` bytes, with no timestamps anywhere, so CI can diff two builds. It assembles every
bundle in memory, checks every platform limit, and only then writes — a build that would
break a cap writes nothing at all.

Hard caps the build enforces: ChatGPT instructions ≤ {CHATGPT_INSTRUCTIONS_MAX_CHARS:,}
characters, ChatGPT knowledge ≤ {CHATGPT_KNOWLEDGE_MAX_FILES} files, Gemini knowledge
≤ {GEMINI_KNOWLEDGE_MAX_FILES} files, Claude Skill `description`
≤ {SKILL_DESCRIPTION_MAX_CHARS} characters, this file ≤ {AGENTS_MD_MAX_BYTES // 1024} KiB.

`src/core/` is the binding constraint: it is concatenated into the ChatGPT instruction
field, so it must fit {CHATGPT_INSTRUCTIONS_MAX_CHARS:,} characters. If a passage is
reference material rather than instruction, wrap it in `{KNOWLEDGE_ONLY_OPEN}` …
`{KNOWLEDGE_ONLY_CLOSE}`: the build then keeps it in the knowledge files and the
single-file bundle but drops it from the two character-capped instruction targets.

## Testing

```bash
python3 -m unittest discover tests
```

Green tests are a release precondition; CI runs them on push. Cover the double-entry
invariant, integer-paisa money and লাখ/কোটি formatting edge cases, tax golden cases with
hand-checked values that cite their rates source, and the build caps.

## Code style

- Standard library only. `decimal.Decimal` for parsing, `int` paisa for arithmetic.
- TOML is read-only to scripts (`tomllib`); humans and the model edit it.
- Every engine script offers `--help`, `--books <dir>` (default `./books`) and `--json`,
  and exits non-zero on any integrity failure.
- Display money in the Bangladeshi লাখ/কোটি grouping by default (`৳ 12,34,567.89`); the
  international grouping (`1,234,567.89`) is available on request. Always state the unit.
- Type hints and `from __future__ import annotations`. Keep modules importable, not
  side-effecting at import time.

## Security

- No real taxpayer data in the repository — no TIN, no BIN, no NID, no bank details.
  Fixtures are synthetic.
- No network calls anywhere in the engine or the build. No telemetry.
- The engine only ever reads TOML and reads/appends CSV under the `--books` directory.
  Never run a write path against a real `books/` directory without an explicit `--books`.

## Commits and pull requests

- Conventional-commit style subject: `feat:`, `fix:`, `docs:`, `build:`, `test:`.
- One logical change per commit. Never commit `dist/` by hand; regenerate it.
- A pull request states which rates file it targets and whether any figure it touches is
  `verified = false`. A PR that changes a tax figure must cite a primary NBR source.

## Note for Claude Code

Claude Code reads `CLAUDE.md`, not `AGENTS.md`. To share this file, put `@AGENTS.md` on
the first line of a root `CLAUDE.md`.

## Attribution

{ATTRIBUTION}
"""


def build_agents_md(tree: SourceTree) -> Bundle:
    """The root ``AGENTS.md`` (where the tools read it) and a copy under ``dist/``.

    The copy is what the npm installer (`bin/takabooks.mjs`) ships and reads first; the
    root file is the one Cursor, Codex and Copilot pick up in a checkout.  Same bytes.
    """
    bundle = Bundle(target="agents-md", clean_dir="dist/agents-md")
    document = agents_markdown(tree)
    bundle.add("AGENTS.md", document)
    bundle.add("dist/agents-md/AGENTS.md", document)
    size = len(document.encode("utf-8"))
    bundle.checks.append(
        limit_check(
            "agents-md",
            "AGENTS.md.bytes",
            size,
            AGENTS_MD_MAX_BYTES,
            "bytes",
            hard=True,
            detail=(
                "Codex stops adding instruction files once the combined size reaches "
                "`project_doc_max_bytes` (32 KiB default) — a larger root file is silently "
                "truncated"
            ),
        )
    )
    bundle.checks.append(
        limit_check(
            "agents-md",
            "AGENTS.md.bytes.target",
            size,
            AGENTS_MD_SOFT_BYTES,
            "bytes",
            hard=False,
            detail="SOFT target, so nested AGENTS.md files still fit inside Codex's budget",
        )
    )
    return bundle


# ======================================================================================
# Assembling, checking and writing
# ======================================================================================


def build_target(name: str, tree: SourceTree, gemini_soft_limit: int) -> Bundle:
    if name == "claude-skill":
        return build_claude_skill(tree)
    if name == "chatgpt":
        return build_chatgpt(tree)
    if name == "gemini":
        return build_gemini(tree, gemini_soft_limit)
    if name == "universal":
        return build_universal(tree)
    if name == "agents-md":
        return build_agents_md(tree)
    raise BuildError(f"Unknown target {name!r}. Known targets: {', '.join(TARGETS)}.")


def _assert_inside(root: Path, path: Path) -> Path:
    """Refuse to touch anything outside the repository root.  Cheap, and worth it."""
    resolved = (root / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise BuildError(f"Refusing to write outside the repository root: {resolved}") from exc
    return resolved


def clean_dist(repo_root: Path) -> bool:
    dist = _assert_inside(repo_root, Path("dist"))
    if dist.exists():
        shutil.rmtree(dist)
        return True
    return False


def write_bundle(bundle: Bundle, repo_root: Path) -> list[str]:
    """Write a checked bundle to disk.  Idempotent: the target directory is replaced."""
    written: list[str] = []
    if bundle.clean_dir:
        target_dir = _assert_inside(repo_root, Path(bundle.clean_dir))
        dist_root = (repo_root / "dist").resolve()
        try:
            target_dir.relative_to(dist_root)
        except ValueError as exc:
            raise BuildError(
                f"A target may only clean paths under dist/, not {target_dir}."
            ) from exc
        if target_dir == dist_root:
            raise BuildError("A target may not clean all of dist/; that is what --clean is for.")
        if target_dir.exists():
            shutil.rmtree(target_dir)

    for relpath in sorted(bundle.files):
        path = _assert_inside(repo_root, Path(relpath))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(bundle.files[relpath], encoding="utf-8", newline="\n")
        if relpath in bundle.executable:
            path.chmod(0o755)
        else:
            path.chmod(0o644)
        written.append(relpath)

    for zip_relpath, folder in bundle.zips:
        written.append(write_zip(bundle, repo_root, zip_relpath, folder))
    return written


# ZIP epoch: the earliest timestamp the format can express.  Fixed, so two builds of the
# same sources produce byte-identical archives.
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)


def write_zip(bundle: Bundle, repo_root: Path, zip_relpath: str, folder: str) -> str:
    """Zip ``folder`` with the folder itself at the archive root.

    claude.ai rejects an archive whose files sit loose at the root, and the same archive
    has to unzip straight into `~/.claude/skills/`.  Both needs are met by keeping the
    `bd-bookkeeping-tax/` prefix on every entry.
    """
    prefix = folder.rstrip("/") + "/"
    members = sorted(name for name in bundle.files if name.startswith(prefix))
    arc_root = Path(folder).name
    path = _assert_inside(repo_root, Path(zip_relpath))
    path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relpath in members:
            arcname = f"{arc_root}/{relpath[len(prefix):]}"
            info = zipfile.ZipInfo(arcname, date_time=ZIP_EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3  # Unix, so the mode bits below are honoured
            mode = 0o755 if relpath in bundle.executable else 0o644
            info.external_attr = (mode << 16) | 0o100000
            archive.writestr(info, bundle.files[relpath].encode("utf-8"))
    return zip_relpath


# ======================================================================================
# Orchestration
# ======================================================================================


@dataclass
class BuildReport:
    targets: list[str]
    checks: list[Check] = field(default_factory=list)
    written: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    missing_sources: list[str] = field(default_factory=list)
    build_id: str = ""
    assessment_year: str = "unknown"
    wrote_anything: bool = False

    @property
    def failures(self) -> list[Check]:
        return [check for check in self.checks if check.hard and not check.ok]

    @property
    def warnings(self) -> list[Check]:
        return [check for check in self.checks if not check.hard and not check.ok]

    def to_dict(self) -> dict[str, object]:
        return {
            "project": PROJECT_NAME,
            "version": PROJECT_VERSION,
            "build_id": self.build_id,
            "assessment_year": self.assessment_year,
            "targets": self.targets,
            "checks": [check.to_dict() for check in self.checks],
            "written": self.written,
            "notes": self.notes,
            "missing_sources": self.missing_sources,
            "ok": not self.failures,
            "wrote_anything": self.wrote_anything,
        }


def run_build(
    repo_root: Path,
    targets: list[str],
    *,
    check_only: bool = False,
    clean: bool = False,
    strict: bool = False,
    gemini_soft_limit: int = GEMINI_INSTRUCTIONS_SOFT_CHARS,
) -> BuildReport:
    """Assemble, check, then (unless ``check_only``) write.  Never writes on a hard failure."""
    repo_root = Path(repo_root).resolve()
    tree = SourceTree.load(repo_root)
    report = BuildReport(
        targets=list(targets),
        build_id=tree.build_id(),
        assessment_year=tree.assessment_year,
        missing_sources=list(tree.missing),
    )

    if tree.missing:
        report.checks.append(
            Check(
                "sources",
                "expected.files",
                len(tree.missing),
                0,
                "missing",
                hard=strict,
                ok=False,
                detail="missing: " + ", ".join(tree.missing),
            )
        )

    bundles: list[Bundle] = []
    for name in targets:
        bundle = build_target(name, tree, gemini_soft_limit)
        bundles.append(bundle)
        report.checks.extend(bundle.checks)
        report.notes.extend(bundle.notes)

    if report.failures or check_only:
        return report

    if clean:
        clean_dist(repo_root)
    for bundle in bundles:
        report.written.extend(write_bundle(bundle, repo_root))
    report.wrote_anything = True
    return report


def _render(report: BuildReport, quiet: bool, check_only: bool) -> None:
    out = sys.stdout
    if not quiet:
        out.write(f"{PROJECT_NAME} {PROJECT_VERSION} — build {report.build_id}\n")
        out.write(f"assessment year: {report.assessment_year}\n")
        out.write(f"targets: {', '.join(report.targets) or '(none)'}\n")
        if report.missing_sources:
            out.write("\nmissing source files:\n")
            for name in report.missing_sources:
                out.write(f"  - {name}\n")
        if report.notes:
            out.write("\nmerge map:\n")
            for note in report.notes:
                out.write(f"  {note}\n")
        out.write("\nlimits:\n")
        for check in report.checks:
            out.write(check.render() + "\n")
        if report.written:
            out.write(f"\nwrote {len(report.written)} files:\n")
            for relpath in report.written:
                out.write(f"  {relpath}\n")

    if report.failures:
        sys.stderr.write("\nBUILD FAILED — a hard platform limit was exceeded:\n")
        for check in report.failures:
            sys.stderr.write(check.render() + "\n")
        sys.stderr.write("\nNothing was written.\n")
    elif not quiet:
        verb = "checked" if check_only else "built"
        warnings = len(report.warnings)
        suffix = f" ({warnings} warning{'s' if warnings != 1 else ''})" if warnings else ""
        out.write(f"\nOK — {verb} {len(report.targets)} target(s){suffix}.\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="build.py",
        description=(
            f"{PROJECT_NAME} build — emit every platform bundle in dist/ from the single "
            "source of truth in src/. Deterministic and idempotent: same input, "
            "byte-identical output."
        ),
        epilog=ATTRIBUTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--target",
        action="append",
        choices=(*TARGETS, "all", "none"),
        help=(
            "target to build; repeat for several. Default: all. "
            "'none' builds nothing (useful with --clean)."
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="build every target — the default, spelled out for CI scripts.",
    )
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="repository root that holds src/ (default: the parent of build/).",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="remove dist/ entirely before building.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="assemble everything and verify every limit, but write nothing.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat a missing expected source file as a build failure (use in release CI).",
    )
    parser.add_argument(
        "--gemini-soft-limit",
        type=int,
        default=GEMINI_INSTRUCTIONS_SOFT_CHARS,
        metavar="N",
        help=(
            "soft character target for gem-instructions.md (default: "
            f"{GEMINI_INSTRUCTIONS_SOFT_CHARS}). Google publishes no limit, so this only "
            "ever warns."
        ),
    )
    parser.add_argument("--json", action="store_true", help="emit the report as JSON.")
    parser.add_argument("--quiet", action="store_true", help="only report failures.")
    return parser


def resolve_targets(requested: list[str] | None) -> list[str]:
    if not requested:
        return list(TARGETS)
    if "none" in requested:
        if len(requested) > 1:
            raise BuildError("--target none cannot be combined with another target.")
        return []
    if "all" in requested:
        return list(TARGETS)
    seen: list[str] = []
    for name in requested:
        if name not in seen:
            seen.append(name)
    return [name for name in TARGETS if name in seen]


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.check and args.clean:
            raise BuildError(
                "--check writes nothing, so --clean would be a contradiction. "
                "Run them separately."
            )
        targets = resolve_targets(["all"] if args.all else args.target)
        repo_root = Path(args.repo_root).resolve()

        if args.check:
            report = run_build(
                repo_root,
                targets,
                check_only=True,
                strict=args.strict,
                gemini_soft_limit=args.gemini_soft_limit,
            )
        else:
            if args.clean and not targets:
                removed = clean_dist(repo_root)
                if not args.quiet:
                    sys.stdout.write(
                        ("removed dist/\n" if removed else "dist/ did not exist\n")
                    )
                return 0
            report = run_build(
                repo_root,
                targets,
                clean=args.clean,
                strict=args.strict,
                gemini_soft_limit=args.gemini_soft_limit,
            )
    except BuildError as exc:
        sys.stderr.write(f"build error: {exc}\n")
        return exc.exit_code

    if args.json:
        sys.stdout.write(json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n")
        if report.failures:
            return 1
        return 0

    _render(report, args.quiet, args.check)
    return 1 if report.failures else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
