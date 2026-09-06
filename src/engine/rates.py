#!/usr/bin/env python3
"""TakaBooks — versioned rates loader (spec §4.5).

``src/data/rates-AY<year>.toml`` is the single home of every Bangladeshi rate, threshold,
deadline and policy switch.  This module is the only sanctioned way to read one.

What it guarantees, and why each guarantee exists:

* **It says which assessment year (করবর্ষ / assessment year) it loaded.**  Selecting the file
  by name is this module's job: :func:`find_rates_file` turns ``"2026-27"`` into
  ``rates-AY2026-27.toml``.  When several files exist and the caller named no year, it
  refuses to pick one — guessing an assessment year is exactly the silent wrongness the spec
  forbids.
* **A missing rate is an error, never a default.**  There is no ``get(key, default)`` here.
  If you want an optional node, ask for it by name with :meth:`RateSet.optional_rate`, which
  says "absent" out loud instead of substituting a number.
* **Every value carries its verification state.**  :class:`RateEntry` exposes ``verified``,
  ``placeholder``, ``source`` and ``as_of``, and :meth:`RateSet.caveats` returns one warning
  line per unverified figure the caller actually used — so a consumer can surface exactly the
  caveats that touched its answer.
* **Placeholder data cannot reach a calculator by accident.**  While
  ``rates-AY2026-27.toml`` is a schema awaiting research, every node carries
  ``placeholder = true``.  A :class:`RateSet` built with the default
  ``allow_placeholders=False`` raises :class:`takabooks.RatesError` the moment such a value is
  requested.  Opting in is explicit and stamps the output PROVISIONAL.
* **No float ever touches money.**  A bare TOML float (``7.5``) is a binary float, so this
  module rejects it and tells the author to quote it (``"7.5"``).  Decimals are parsed with
  :class:`decimal.Decimal`; taka become :class:`takabooks.Money` int paisa.

TakaBooks defines **no** Bangladeshi figure in Python.  Everything below is structure.

TakaBooks — Moshiur Rahman (@bemoshiur) · Ticon Sys — https://ticonsys.com
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

import takabooks as tb  # noqa: E402  (path must be set first)

__all__ = [
    "DATA_DIRNAME",
    "RATES_FILENAME_RE",
    "PLACEHOLDER_FLAG",
    "UNIT_PERCENT",
    "UNIT_BDT",
    "UNIT_DATE",
    "UNIT_POLICY",
    "default_data_dir",
    "normalise_assessment_year",
    "rates_filename",
    "assessment_year_from_filename",
    "available_rate_files",
    "available_assessment_years",
    "find_rates_file",
    "RateEntry",
    "RateSet",
    "load_rates",
    "resolve_rates",
    "main",
]

# --------------------------------------------------------------------------------------
# File naming
# --------------------------------------------------------------------------------------

#: Directory under ``src/`` that holds the rates files.
DATA_DIRNAME = "data"

#: ``rates-AY2026-27.toml`` — the only filename shape this loader recognises.
RATES_FILENAME_RE = re.compile(r"(?i)^rates-AY(\d{4})-(\d{2}|\d{4})\.toml$")

#: Key that marks a node as unlanded schema rather than a researched figure.
PLACEHOLDER_FLAG = "placeholder"

UNIT_PERCENT = "percent"
UNIT_BDT = "BDT"
UNIT_DATE = "date"
UNIT_POLICY = "policy"

_AY_RE = re.compile(r"(?i)^(?:AY[\s:_-]*)?(\d{4})\s*[-–—/_]\s*(\d{2}|\d{4})$")


def default_data_dir() -> Path:
    """``src/data`` relative to this module — where the shipped rates files live."""
    return Path(__file__).resolve().parent.parent / DATA_DIRNAME


def normalise_assessment_year(text: Any) -> str:
    """Canonicalise an assessment year to ``"2026-27"``.

    Accepts ``2026-27``, ``2026-2027``, ``AY2026-27``, ``ay 2026/27`` and en-dash variants.
    Anything else raises :class:`takabooks.RatesError` — TakaBooks will not guess which year
    a mistyped করবর্ষ meant.
    """
    if text is None:
        raise tb.RatesError("No assessment year was given.")
    raw = tb.to_latin_digits(str(text)).strip()
    match = _AY_RE.match(raw)
    if not match:
        raise tb.RatesError(
            f"{text!r} is not an assessment year.",
            hint='Write it as "2026-27" (four-digit year, hyphen, two-digit year).',
        )
    start, end = match.group(1), match.group(2)
    if len(end) == 4:
        if int(end) != int(start) + 1:
            raise tb.RatesError(
                f"Assessment year {text!r} does not span consecutive years.",
                hint='An assessment year runs across two consecutive years, e.g. "2026-27".',
            )
        end = end[-2:]
    elif int(end) != (int(start) + 1) % 100:
        raise tb.RatesError(
            f"Assessment year {text!r} does not span consecutive years.",
            hint='An assessment year runs across two consecutive years, e.g. "2026-27".',
        )
    return f"{start}-{end}"


def rates_filename(assessment_year: Any) -> str:
    """``"2026-27"`` -> ``"rates-AY2026-27.toml"``."""
    return f"rates-AY{normalise_assessment_year(assessment_year)}.toml"


def assessment_year_from_filename(name: "Path | str") -> str | None:
    """Canonical assessment year encoded in a filename, or ``None``."""
    match = RATES_FILENAME_RE.match(Path(name).name)
    if not match:
        return None
    try:
        return normalise_assessment_year(f"{match.group(1)}-{match.group(2)}")
    except tb.RatesError:
        return None


def available_rate_files(data_dir: "Path | str | None" = None) -> list[Path]:
    """Every ``rates-AY*.toml`` in ``data_dir``, sorted by assessment year."""
    directory = Path(data_dir) if data_dir is not None else default_data_dir()
    if not directory.is_dir():
        raise tb.RatesError(
            f"Rates directory not found: {directory}",
            hint="Pass --data-dir, or point --rates straight at a rates-AY<year>.toml file.",
        )
    found = [p for p in directory.iterdir() if p.is_file() and RATES_FILENAME_RE.match(p.name)]
    return sorted(found, key=lambda p: (assessment_year_from_filename(p) or "", p.name))


def available_assessment_years(data_dir: "Path | str | None" = None) -> list[str]:
    """Canonical assessment years for which a rates file exists."""
    years = []
    for path in available_rate_files(data_dir):
        year = assessment_year_from_filename(path)
        if year and year not in years:
            years.append(year)
    return years


def find_rates_file(
    assessment_year: Any = None,
    *,
    data_dir: "Path | str | None" = None,
) -> Path:
    """Locate the rates file for ``assessment_year`` (or the only one present).

    With no assessment year and more than one file available this raises rather than
    picking "the newest": a rates file is a legal position for one year, and quietly
    computing tax against the wrong year is worse than refusing.
    """
    directory = Path(data_dir) if data_dir is not None else default_data_dir()
    candidates = available_rate_files(directory)
    if assessment_year not in (None, ""):
        year = normalise_assessment_year(assessment_year)
        path = directory / rates_filename(year)
        if path.is_file():
            return path
        known = available_assessment_years(directory)
        raise tb.RatesError(
            f"No rates file for {tb.term('assessment_year')} {year} in {directory}.",
            hint=(
                "Available: " + ", ".join(known)
                if known
                else f"{directory} contains no rates-AY<year>.toml at all."
            ),
        )
    if not candidates:
        raise tb.RatesError(
            f"{directory} contains no rates-AY<year>.toml file.",
            hint="Rates live in src/data/. Add the file for the assessment year you need.",
        )
    if len(candidates) > 1:
        raise tb.RatesError(
            f"{directory} holds {len(candidates)} rates files; name the assessment year.",
            hint="Available: "
            + ", ".join(available_assessment_years(directory))
            + ". Pass --assessment-year, or set books.assessment_year in config.toml.",
        )
    return candidates[0]


# --------------------------------------------------------------------------------------
# Value coercion — Decimal only, float refused
# --------------------------------------------------------------------------------------


def _reject_float(value: Any, *, key: str) -> None:
    if isinstance(value, float):
        raise tb.RatesError(
            f"{key} is written as a TOML float ({value!r}).",
            hint='tomllib turns 7.5 into a binary float and TakaBooks refuses float money. '
            'Quote it in the TOML: value = "7.5".',
        )


def _to_decimal(value: Any, *, key: str) -> Decimal:
    """Coerce a rates value to :class:`~decimal.Decimal`.  Never touches float."""
    _reject_float(value, key=key)
    if isinstance(value, bool):
        raise tb.RatesError(f"{key} is a boolean ({value!r}), not a number.")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str):
        text = tb.to_latin_digits(value).strip().replace(",", "").replace("_", "")
        if text.endswith("%"):
            text = text[:-1].strip()
        if not text:
            raise tb.RatesError(f"{key} is blank; it has no value yet.")
        try:
            return Decimal(text)
        except InvalidOperation:
            raise tb.RatesError(f"{key} is {value!r}, which is not a number.") from None
    raise tb.RatesError(
        f"{key} is a {type(value).__name__}; expected a number or a quoted decimal string."
    )


# --------------------------------------------------------------------------------------
# One value, with its provenance
# --------------------------------------------------------------------------------------

_ENTRY_META_KEYS = frozenset(
    {"value", "unit", "source", "as_of", "verified", PLACEHOLDER_FLAG, "note",
     "label_en", "label_bn"}
)


@dataclass(frozen=True)
class RateEntry:
    """One rates value together with everything needed to judge whether to trust it."""

    key: str
    value: Any
    unit: str = ""
    source: str = ""
    as_of: str = ""
    verified: bool = False
    placeholder: bool = False
    note: str = ""
    label_en: str = ""
    label_bn: str = ""
    origin: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    # -- provenance --------------------------------------------------------------------

    @property
    def is_verified(self) -> bool:
        return bool(self.verified) and not self.placeholder

    @property
    def is_placeholder(self) -> bool:
        return bool(self.placeholder)

    @property
    def is_provisional(self) -> bool:
        """True when a consumer must not present this figure as final."""
        return not self.is_verified

    @property
    def label(self) -> str:
        """Bangla / English label pair, falling back to the dotted key."""
        if self.label_bn and self.label_en:
            return f"{self.label_bn} / {self.label_en}"
        return self.label_en or self.label_bn or self.key

    def caveat(self) -> str:
        """The sentence a consumer must show for this figure ("" when verified)."""
        where = f" in {self.origin}" if self.origin else ""
        if self.placeholder:
            return (
                f"PLACEHOLDER: {self.key}{where} has no researched value — it is schema "
                "awaiting verified data. Any figure computed from it is meaningless."
            )
        if not self.verified:
            return (
                f"UNVERIFIED: {self.key}{where} is not confirmed against a primary source. "
                "Confirm it with the National Board of Revenue (NBR) before you file."
            )
        return ""

    def provenance(self) -> str:
        """One human line: value, source, as-of date, verification state."""
        state = "verified" if self.is_verified else ("PLACEHOLDER" if self.placeholder else "UNVERIFIED")
        bits = [f"{self.key} = {self.value!r}"]
        if self.unit:
            bits.append(self.unit)
        bits.append(state)
        if self.as_of:
            bits.append(f"as of {self.as_of}")
        if self.source:
            bits.append(self.source)
        return " · ".join(bits)

    # -- typed access ------------------------------------------------------------------

    def as_decimal(self) -> Decimal:
        return _to_decimal(self.value, key=self.key)

    def as_percent(self) -> Decimal:
        """A percentage (``15`` means 15%).  Refuses a value outside 0–100."""
        number = self.as_decimal()
        if number < 0:
            raise tb.RatesError(f"{self.key} is a negative percentage ({number}).")
        if number > 100:
            raise tb.RatesError(
                f"{self.key} is {number}, which is not a percentage.",
                hint="Percentages in the rates TOML are percent, not fractions: write 15 for "
                "15%, not 0.15 and not 1500.",
            )
        return number

    def as_fraction(self) -> Decimal:
        """The percentage expressed as a fraction (15% -> ``Decimal('0.15')``)."""
        return self.as_percent() / Decimal(100)

    def as_money(self, *, allow_negative: bool = False) -> tb.Money:
        """The value read as taka (BDT) and held as int paisa."""
        _reject_float(self.value, key=self.key)
        try:
            amount = tb.Money.from_taka(self.value, what=f"rate {self.key}")
        except tb.MoneyError as exc:
            raise tb.RatesError(f"{self.key}: {exc.message}", hint=exc.hint) from None
        if amount.is_negative() and not allow_negative:
            raise tb.RatesError(f"{self.key} is a negative amount ({amount.bdt}).")
        return amount

    def as_text(self) -> str:
        _reject_float(self.value, key=self.key)
        if isinstance(self.value, bool) or not isinstance(self.value, (str, int)):
            raise tb.RatesError(f"{self.key} is not text (got {type(self.value).__name__}).")
        return str(self.value).strip()

    def as_choice(self, allowed: Sequence[str]) -> str:
        """A policy switch: text that must be one of ``allowed``.

        Declared ``allowed`` values inside the node are cross-checked, so a rates file that
        offers an option the engine cannot implement fails at read time, not silently.
        """
        text = self.as_text()
        declared = self.extra.get("allowed")
        if isinstance(declared, (list, tuple)):
            unknown = [str(v) for v in declared if str(v) not in allowed]
            if unknown:
                raise tb.RatesError(
                    f"{self.key} declares option(s) {', '.join(unknown)} that TakaBooks does "
                    "not implement.",
                    hint="Implemented options: " + ", ".join(allowed) + ".",
                )
        if text not in allowed:
            raise tb.RatesError(
                f"{self.key} is {text!r}, which TakaBooks does not implement.",
                hint="Allowed values: " + ", ".join(allowed) + ".",
            )
        return text


# --------------------------------------------------------------------------------------
# The loaded file
# --------------------------------------------------------------------------------------

_MISSING = object()


class RateSet:
    """A loaded rates file, gated so unlanded data cannot silently become a tax figure.

    ``allow_placeholders`` is the single switch that lets placeholder schema through; it
    exists so a caller can produce an explicitly PROVISIONAL result for testing or for a
    walkthrough, never so it can be forgotten.
    """

    def __init__(self, table: tb.RatesTable, *, allow_placeholders: bool = False) -> None:
        if not isinstance(table, tb.RatesTable):
            raise tb.RatesError("RateSet needs a takabooks.RatesTable.")
        self.table = table
        self.allow_placeholders = bool(allow_placeholders)
        self._used: dict[str, RateEntry] = {}

    # -- construction ------------------------------------------------------------------

    @classmethod
    def from_path(cls, path: "Path | str", *, allow_placeholders: bool = False) -> "RateSet":
        return cls(tb.RatesTable.from_toml_path(Path(path)), allow_placeholders=allow_placeholders)

    @classmethod
    def load(
        cls,
        assessment_year: Any = None,
        *,
        data_dir: "Path | str | None" = None,
        allow_placeholders: bool = False,
    ) -> "RateSet":
        return cls.from_path(
            find_rates_file(assessment_year, data_dir=data_dir),
            allow_placeholders=allow_placeholders,
        )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"RateSet(AY={self.assessment_year}, path={self.path}, used={len(self._used)})"

    # -- identity ----------------------------------------------------------------------

    @property
    def path(self) -> Path | None:
        return self.table.source_path

    @property
    def filename(self) -> str:
        return self.path.name if self.path else "rates file"

    @property
    def assessment_year(self) -> str | None:
        """The করবর্ষ / assessment year this file states (or the one in its name)."""
        return self.table.assessment_year

    def require_assessment_year(self) -> str:
        year = self.assessment_year
        if not year:
            raise tb.RatesError(
                f"{self.filename} does not state an assessment year.",
                hint='Add [meta] assessment_year = "2026-27", or name the file '
                "rates-AY2026-27.toml. Every tax output must state the করবর্ষ it used.",
            )
        return year

    def provenance(self) -> str:
        """The line every consumer must print (spec §4.5)."""
        return self.table.provenance()

    @property
    def meta(self) -> Mapping[str, Any]:
        node = self.table.raw.get("meta")
        return node if isinstance(node, Mapping) else {}

    @property
    def file_is_placeholder(self) -> bool:
        """True when the file itself declares ``[meta] placeholder = true``."""
        return bool(self.meta.get(PLACEHOLDER_FLAG, False))

    def require_usable(self) -> None:
        """Refuse a placeholder file unless the caller opted in.

        Consumers call this before computing anything, so the refusal names the file rather
        than surfacing as a confusing failure on whichever key happened to be read first.
        """
        if self.file_is_placeholder and not self.allow_placeholders:
            raise tb.RatesError(
                f"{self.filename} is a schema awaiting verified data — every figure in it is "
                "a placeholder.",
                hint="No Bangladeshi rate has been landed for this assessment year yet. "
                "Fill the file in (its header documents the procedure), or pass "
                "--allow-placeholder-rates to compute a clearly-marked PROVISIONAL result "
                "that must never be filed.",
            )

    # -- lookup ------------------------------------------------------------------------

    def has(self, key: str) -> bool:
        return self.table.has(key)

    def _node(self, key: str) -> Any:
        node: Any = self.table.raw
        for part in str(key).split("."):
            if not isinstance(node, Mapping) or part not in node:
                return _MISSING
            node = node[part]
        return node

    def entry_from_node(self, node: Any, key: str) -> RateEntry:
        """Build a :class:`RateEntry` from an already-extracted node.

        Needed for members of an array-of-tables (a slab, a surcharge band), which have no
        dotted key of their own.  Gating and usage tracking apply exactly as for
        :meth:`rate`.
        """
        if isinstance(node, Mapping):
            if "value" not in node:
                raise tb.RatesError(
                    f"{self.filename}: {key} is a section, not a rate — it has no 'value'."
                )
            entry = RateEntry(
                key=key,
                value=node["value"],
                unit=str(node.get("unit", "")),
                source=str(node.get("source", "")),
                as_of=str(node.get("as_of", "")),
                verified=bool(node.get("verified", False)),
                placeholder=bool(node.get(PLACEHOLDER_FLAG, False)),
                note=str(node.get("note", "")),
                label_en=str(node.get("label_en", "")),
                label_bn=str(node.get("label_bn", "")),
                origin=self.filename,
                extra={k: v for k, v in node.items() if k not in _ENTRY_META_KEYS},
            )
        else:
            # A bare scalar carries no provenance at all, so it can never count as verified.
            entry = RateEntry(key=key, value=node, origin=self.filename)
        _reject_float(entry.value, key=entry.key)
        if entry.placeholder and not self.allow_placeholders:
            raise tb.RatesError(
                f"{self.filename}: {key} is a placeholder awaiting verified data.",
                hint="TakaBooks will not substitute a guessed figure. Land the real value "
                "(see the file header), or pass --allow-placeholder-rates for an explicitly "
                "PROVISIONAL result.",
            )
        self._used[entry.key] = entry
        return entry

    def rate(self, key: str) -> RateEntry:
        """The value at ``key`` with its provenance.  A missing key is an error."""
        node = self._node(key)
        if node is _MISSING:
            raise tb.RatesError(
                f"{self.filename}: no value for {key!r}.",
                hint="TakaBooks never substitutes a default for a missing rate. Add the "
                "figure to the rates TOML with its source URL, or tell the user it is "
                "unavailable for this assessment year.",
            )
        return self.entry_from_node(node, key)

    def optional_rate(self, key: str) -> RateEntry | None:
        """The value at ``key``, or ``None`` when the node is genuinely absent.

        Use this only where absence is *meaningful* (an open-ended top slab has no width).
        It is deliberately not a default: it returns nothing, not zero.
        """
        if self._node(key) is _MISSING:
            return None
        return self.rate(key)

    # -- typed shortcuts ---------------------------------------------------------------

    def decimal(self, key: str) -> Decimal:
        return self.rate(key).as_decimal()

    def percent(self, key: str) -> Decimal:
        return self.rate(key).as_percent()

    def fraction(self, key: str) -> Decimal:
        return self.rate(key).as_fraction()

    def money(self, key: str, *, allow_negative: bool = False) -> tb.Money:
        return self.rate(key).as_money(allow_negative=allow_negative)

    def text(self, key: str) -> str:
        return self.rate(key).as_text()

    def choice(self, key: str, allowed: Sequence[str]) -> str:
        return self.rate(key).as_choice(allowed)

    def section(self, key: str) -> Mapping[str, Any]:
        """A table that groups rates (no ``value`` of its own)."""
        node = self._node(key)
        if node is _MISSING:
            raise tb.RatesError(
                f"{self.filename}: no section {key!r}.",
                hint="Check the key map in the header of the rates file.",
            )
        if not isinstance(node, Mapping):
            raise tb.RatesError(f"{self.filename}: {key!r} is not a section.")
        return node

    def items(self, key: str) -> list[Mapping[str, Any]]:
        """An array of tables (slabs, surcharge bands), in file order."""
        node = self._node(key)
        if node is _MISSING:
            raise tb.RatesError(
                f"{self.filename}: no list at {key!r}.",
                hint="Check the key map in the header of the rates file.",
            )
        if not isinstance(node, list) or not all(isinstance(item, Mapping) for item in node):
            raise tb.RatesError(f"{self.filename}: {key!r} is not an array of tables.")
        if not node:
            raise tb.RatesError(
                f"{self.filename}: {key!r} is empty.",
                hint="An empty list is not a rate of zero — land the entries or say the "
                "figures are unavailable.",
            )
        return list(node)

    def option_keys(self, key: str) -> list[str]:
        """Sub-keys of a section, in file order — e.g. the taxpayer categories on offer.

        This is how a consumer stays free of hardcoded Bangladeshi categories: the rates
        file decides which categories and location tiers exist.
        """
        return [str(k) for k, v in self.section(key).items() if isinstance(v, Mapping) and "value" in v]

    # -- verification reporting ---------------------------------------------------------

    def used(self) -> tuple[RateEntry, ...]:
        """Every entry handed out so far, in first-use order."""
        return tuple(self._used.values())

    def unverified_used(self) -> tuple[RateEntry, ...]:
        return tuple(e for e in self._used.values() if not e.is_verified)

    def placeholders_used(self) -> tuple[RateEntry, ...]:
        return tuple(e for e in self._used.values() if e.is_placeholder)

    @property
    def is_provisional(self) -> bool:
        """True when any figure used so far is unverified or placeholder."""
        return bool(self.unverified_used()) or self.file_is_placeholder

    def caveats(self) -> list[str]:
        """One warning line per unverified figure that was actually used."""
        lines: list[str] = []
        if self.file_is_placeholder:
            lines.append(
                f"PLACEHOLDER FILE: {self.filename} is a schema awaiting verified data. "
                "Every figure it contains is a placeholder and nothing computed from it may "
                "be filed with NBR."
            )
        for entry in self.unverified_used():
            caveat = entry.caveat()
            if caveat:
                lines.append(caveat)
        return lines

    def file_caveats(self) -> list[str]:
        """One warning line per unverified figure anywhere in the file."""
        return self.table.caveats()

    def audit(self) -> dict[str, Any]:
        """Whole-file verification census — the data behind ``rates.py`` on the CLI."""
        verified: list[str] = []
        unverified: list[str] = []
        placeholders: list[str] = []

        def walk(node: Any, prefix: str) -> None:
            if isinstance(node, Mapping):
                if "value" in node:
                    if bool(node.get(PLACEHOLDER_FLAG, False)):
                        placeholders.append(prefix)
                    elif bool(node.get("verified", False)):
                        verified.append(prefix)
                    else:
                        unverified.append(prefix)
                    return
                for key, child in node.items():
                    walk(child, f"{prefix}.{key}" if prefix else str(key))
            elif isinstance(node, list):
                for index, child in enumerate(node):
                    walk(child, f"{prefix}[{index}]")

        walk(self.table.raw, "")
        total = len(verified) + len(unverified) + len(placeholders)
        return {
            "file": str(self.path) if self.path else None,
            "assessment_year": self.assessment_year,
            "file_is_placeholder": self.file_is_placeholder,
            "total_rate_nodes": total,
            "verified": sorted(verified),
            "unverified": sorted(unverified),
            "placeholder": sorted(placeholders),
            "verified_count": len(verified),
            "unverified_count": len(unverified),
            "placeholder_count": len(placeholders),
            "usable": total > 0 and not placeholders and not unverified,
        }


# --------------------------------------------------------------------------------------
# Resolution helpers used by every calculator
# --------------------------------------------------------------------------------------


def load_rates(
    assessment_year: Any = None,
    *,
    data_dir: "Path | str | None" = None,
    allow_placeholders: bool = False,
) -> RateSet:
    """Load the rates file for an assessment year (see :func:`find_rates_file`)."""
    return RateSet.load(
        assessment_year, data_dir=data_dir, allow_placeholders=allow_placeholders
    )


def resolve_rates(
    *,
    path: "Path | str | None" = None,
    assessment_year: Any = None,
    config: "tb.Config | None" = None,
    data_dir: "Path | str | None" = None,
    allow_placeholders: bool = False,
) -> RateSet:
    """Pick a rates file the way every TakaBooks CLI should, in this order:

    1. ``--rates PATH`` — an explicit file always wins.
    2. ``--assessment-year`` — name the করবর্ষ, get that file.
    3. ``books/config.toml`` ``[books] rates_file`` — the book pins its own file.
    4. ``books/config.toml`` ``[books] assessment_year``.
    5. the sole rates file in the data directory; several files without a stated year is an
       error, because guessing the year is not a service.
    """
    if path not in (None, ""):
        return RateSet.from_path(path, allow_placeholders=allow_placeholders)
    if assessment_year not in (None, ""):
        return RateSet.load(
            assessment_year, data_dir=data_dir, allow_placeholders=allow_placeholders
        )
    if config is not None and config.rates_file:
        candidate = Path(config.rates_file)
        searched: list[Path] = []
        if candidate.is_absolute():
            searched.append(candidate)
        else:
            if config.source_path is not None:
                searched.append(config.source_path.parent / candidate)
            searched.append((Path(data_dir) if data_dir else default_data_dir()) / candidate)
            searched.append(Path.cwd() / candidate)
        for option in searched:
            if option.is_file():
                return RateSet.from_path(option, allow_placeholders=allow_placeholders)
        raise tb.RatesError(
            f"config.toml names rates_file = {config.rates_file!r}, which was not found.",
            hint="Looked in: " + ", ".join(str(p) for p in searched),
        )
    if config is not None and config.assessment_year:
        return RateSet.load(
            config.assessment_year, data_dir=data_dir, allow_placeholders=allow_placeholders
        )
    return RateSet.load(None, data_dir=data_dir, allow_placeholders=allow_placeholders)


def _load_config_if_present(books_dir: "Path | str") -> "tb.Config | None":
    """Read ``books/config.toml`` when there is one; a calculator may run without books.

    Only a *missing* config is skipped.  A config that exists but is broken raises
    :class:`takabooks.ConfigError` — silently ignoring it could pick the wrong year's
    rates file.
    """
    if not tb.config_path(books_dir).is_file():
        return None
    return tb.Config.load(books_dir)


# --------------------------------------------------------------------------------------
# CLI — inspect a rates file and audit its verification state
# --------------------------------------------------------------------------------------


def _render_audit(rate_set: RateSet, *, show_all: bool) -> str:
    audit = rate_set.audit()
    lines = [
        f"# {tb.PROJECT_NAME} — rates audit",
        "",
        rate_set.provenance(),
        f"File: {audit['file']}",
        "",
    ]
    if audit["file_is_placeholder"]:
        lines += [
            "> **PLACEHOLDER FILE — অস্থায়ী**  This rates file is a schema awaiting verified",
            "> data. Nothing computed from it may be filed with NBR.",
            "",
        ]
    lines.append(
        tb.markdown_table(
            ["Rate nodes", "Count"],
            [
                ["verified", str(audit["verified_count"])],
                ["unverified", str(audit["unverified_count"])],
                ["placeholder", str(audit["placeholder_count"])],
                ["total", str(audit["total_rate_nodes"])],
            ],
            aligns=["l", "r"],
        )
    )
    lines.append("")
    for title, keys in (
        ("Placeholder keys", audit["placeholder"]),
        ("Unverified keys", audit["unverified"]),
    ):
        if not keys:
            continue
        shown = keys if show_all else keys[:15]
        lines.append(f"## {title} ({len(keys)})")
        lines += [f"- `{key}`" for key in shown]
        if len(keys) > len(shown):
            lines.append(f"- …and {len(keys) - len(shown)} more (pass --all to list them)")
        lines.append("")
    if audit["usable"]:
        lines.append("Every rate node in this file is marked verified.")
    else:
        lines.append(
            "This file is NOT ready to produce a fileable figure. See its header for the "
            "procedure that lands a verified value."
        )
    lines.append("")
    lines.append(tb.ATTRIBUTION)
    return "\n".join(lines)


def _render_entry(entry: RateEntry) -> str:
    rows = [
        ["key", entry.key],
        ["value", repr(entry.value)],
        ["unit", entry.unit or "—"],
        ["label", entry.label],
        ["verified", "yes" if entry.is_verified else "no"],
        ["placeholder", "yes" if entry.is_placeholder else "no"],
        ["source", entry.source or "—"],
        ["as of", entry.as_of or "—"],
    ]
    out = [tb.markdown_table(["Field", "Value"], rows)]
    if entry.note:
        out += ["", "**Note.** " + " ".join(entry.note.split())]
    caveat = entry.caveat()
    if caveat:
        out += ["", "> " + caveat]
    return "\n".join(out)


def build_parser() -> "tb.argparse.ArgumentParser":  # type: ignore[name-defined]
    parser = tb.common_parser(
        "rates.py",
        "Inspect a TakaBooks rates file and audit which figures are verified.",
    )
    parser.add_argument("--data-dir", metavar="DIR", default=None,
                        help="directory holding rates-AY<year>.toml (default: src/data)")
    parser.add_argument("--assessment-year", metavar="AY", default=None,
                        help='assessment year / করবর্ষ to load, e.g. "2026-27"')
    parser.add_argument("--rates", metavar="PATH", default=None,
                        help="load this rates file directly, ignoring --assessment-year")
    parser.add_argument("--list", action="store_true",
                        help="list the assessment years for which a rates file exists")
    parser.add_argument("--key", metavar="DOTTED.KEY", default=None,
                        help="print one rate with its full provenance")
    parser.add_argument("--all", action="store_true",
                        help="list every unverified key instead of the first 15")
    parser.add_argument("--allow-placeholder-rates", action="store_true",
                        help="permit reading placeholder values (they stay marked PLACEHOLDER)")
    return parser


def main(argv: "Sequence[str] | None" = None) -> int:
    args = build_parser().parse_args(argv)
    with tb.cli_guard(json_output=args.json):
        if args.list:
            years = available_assessment_years(args.data_dir)
            files = available_rate_files(args.data_dir)
            if args.json:
                print(tb.json_dumps({"ok": True, "assessment_years": years,
                                     "files": [str(p) for p in files]}))
            elif not files:
                print("No rates-AY<year>.toml found.")
            else:
                for path in files:
                    print(f"{assessment_year_from_filename(path) or '?'}  {path}")
            return 0

        rate_set = resolve_rates(
            path=args.rates,
            assessment_year=args.assessment_year,
            config=_load_config_if_present(args.books),
            data_dir=args.data_dir,
            allow_placeholders=True,  # auditing must be able to see placeholder nodes
        )
        if args.key:
            reader = RateSet(rate_set.table, allow_placeholders=args.allow_placeholder_rates)
            entry = reader.rate(args.key)
            if args.json:
                print(tb.json_dumps({"ok": True, "assessment_year": reader.assessment_year,
                                     "rates_source": reader.provenance(),
                                     "rate": entry, "caveat": entry.caveat()}))
            else:
                print(reader.provenance())
                print()
                print(_render_entry(entry))
            return 0

        audit = rate_set.audit()
        if args.json:
            print(tb.json_dumps({"ok": True, "rates_source": rate_set.provenance(), **audit}))
        else:
            print(_render_audit(rate_set, show_all=args.all))
        return 0


if __name__ == "__main__":  # pragma: no cover - exercised via subprocess in tests
    tb.check_python_or_exit()
    raise SystemExit(main())
