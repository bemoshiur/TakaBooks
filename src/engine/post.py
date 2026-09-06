#!/usr/bin/env python3
"""TakaBooks ``post.py`` — record one validated journal entry (জাবেদা / journal).

One invocation appends **one** balanced entry — several posting lines sharing one
``entry_id`` — to ``books/journal/YYYY-MM.csv``.  The file is chosen by the entry date
and gets its header row written when it does not exist yet.  This is the gate through
which new rows enter the books, so it refuses, exits non-zero and writes **nothing**
when:

* debits do not equal credits, to the paisa                 -> BalanceError        exit 5
* a line names an account code that is not in accounts.toml -> UnknownAccountError exit 3
  or one that accounts.toml tags inactive / closed          -> AccountError        exit 3
* the date is not a strict ISO ``YYYY-MM-DD`` calendar date -> JournalError        exit 4
* an amount is unreadable, negative, zero or finer than one paisa, or a line carries
  both a debit and a credit                                 -> JournalError        exit 4
* a ``tax_tag`` breaks the grammar, or sits on the control account of a *different*
  tax                                                       -> TaxTagError         exit 6
* the ``entry_id`` you chose is already used in these books -> DuplicateEntryError exit 4
* several of the above are wrong at once — every problem is listed together so one
  round trip fixes them all                                 -> ValidationError     exit 7

Nothing is ever corrected silently (spec §2).  ``--dry-run`` performs every check and
prints the exact CSV that would be appended, without touching the books.

Two ways to describe the entry, which may be combined:

**Command line** — one ``--debit`` / ``--credit`` per line, ``ACCOUNT=AMOUNT[:TAX_TAG]``::

    python3 src/engine/post.py --books books --date 2026-07-15 \\
        --description "Sale to Rahim Traders" --party "Rahim Traders" --doc-ref INV-0012 \\
        --debit  1200=11500.00 \\
        --credit 4100=10000.00 \\
        --credit 2310=1500.00:VAT:OUT:15

**JSON** — ``--stdin``, ``--input FILE``, or simply ``--json`` with a pipe on stdin::

    {
      "date": "2026-07-15",
      "description": "Sale to Rahim Traders",
      "party": "Rahim Traders",
      "doc_ref": "INV-0012",
      "lines": [
        {"account": "1200", "debit": "11500.00"},
        {"account": "4100", "credit": "10000.00"},
        {"account": "2310", "credit": "1500.00", "tax_tag": "VAT:OUT:15"}
      ]
    }

Amounts are BDT strings (``"1,00,000.00"``, ``"৳ 500"``, ``"১২৩৪.৫৬"`` all read) or whole
integers — JSON floats are refused, because a float has already lost the paisa.  Each
line carries exactly one of ``debit`` / ``credit``; ``tax_tag`` defaults to ``NONE``;
``description`` / ``party`` / ``doc_ref`` / ``memo`` on a line override the entry-level
value for that row only.  Command-line flags override same-named JSON fields, and
command-line lines are appended after the JSON lines.  Rows are written debits first,
then credits, each group in the order given.

``entry_id`` is optional.  When omitted it is generated **deterministically** from the
books alone — ``JE-YYYY-MM-NNNN``, the next unused sequence number for that month — so
re-running the same command on the same books always yields the same id.  No clock,
no randomness.

This script defines **no Bangladeshi tax rate, threshold, deadline or statute number**.
The ``tax_tag`` carries whatever rate you wrote; the rates live in ``src/data/rates-AY*.toml``.

TakaBooks — Moshiur Rahman (@bemoshiur) · TICON SYSTEM LTD — https://ticonsys.com
MIT licensed · https://github.com/bemoshiur/TakaBooks
"""

from __future__ import annotations

import argparse
import csv
import datetime
import difflib
import io
import json
import re
import sys
from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

_ENGINE_DIR = Path(__file__).resolve().parent
if str(_ENGINE_DIR) not in sys.path:  # pragma: no cover - import plumbing
    sys.path.insert(0, str(_ENGINE_DIR))

import takabooks as tb  # noqa: E402  (must follow the sys.path bootstrap above)

__all__ = [
    "PROG",
    "ENTRY_ID_PREFIX",
    "ENTRY_ID_WIDTH",
    "INACTIVE_TAGS",
    "SIDE_DEBIT",
    "SIDE_CREDIT",
    "SIDES",
    "ENTRY_KEYS",
    "LINE_KEYS",
    "JSON_SHAPE_HINT",
    "LINE_ARG_HINT",
    "LineSpec",
    "EntrySpec",
    "BuiltEntry",
    "parse_amount",
    "parse_line_arg",
    "parse_json_entry",
    "entry_spec_from_args",
    "generate_entry_id",
    "build_entry",
    "post_entry",
    "render_csv",
    "render_text",
    "build_parser",
    "main",
]

PROG = "post.py"

#: Generated ids look like ``JE-2026-07-0001``: prefix, month, zero-padded sequence.
ENTRY_ID_PREFIX = "JE"
ENTRY_ID_WIDTH = 4

SIDE_DEBIT = "debit"
SIDE_CREDIT = "credit"
SIDES: tuple[str, ...] = (SIDE_DEBIT, SIDE_CREDIT)

#: Mirrors ``validate.py`` — an account carrying one of these tags is retired, and
#: a *new* posting to it is refused here (validate.py only warns about old ones).
INACTIVE_TAGS: tuple[str, ...] = ("inactive", "archived", "closed", "disabled", "retired")

# Which chart roles a tax_tag kind belongs with.  Mirrors validate.py so that a row
# this script writes is never one validate.py then rejects.
_KIND_ROLES: dict[str, tuple[str, ...]] = {
    tb.TAG_VAT_OUT: (tb.ROLE_VAT_OUTPUT,),
    tb.TAG_VAT_IN: (tb.ROLE_VAT_INPUT,),
    tb.TAG_TDS: (tb.ROLE_TDS_PAYABLE, tb.ROLE_TDS_RECEIVABLE),
    tb.TAG_VDS: (tb.ROLE_VDS_PAYABLE,),
}
_CONTROL_ROLES: frozenset[str] = frozenset(
    role for roles in _KIND_ROLES.values() for role in roles
)
_KIND_TAGS: dict[str, tuple[str, ...]] = {
    tb.TAG_VAT_OUT: ("vat", "vat_output", "output_vat"),
    tb.TAG_VAT_IN: ("vat", "vat_input", "input_vat"),
    tb.TAG_TDS: ("tds", "withholding"),
    tb.TAG_VDS: ("vds", "withholding"),
}
_KIND_TERM: dict[str, str] = {
    tb.TAG_VAT_OUT: tb.term("vat"),
    tb.TAG_VAT_IN: tb.term("vat"),
    tb.TAG_TDS: tb.term("tds"),
    tb.TAG_VDS: tb.term("vds"),
}

#: Keys accepted at the top of a JSON entry, and on each line.
ENTRY_KEYS: tuple[str, ...] = ("date", "entry_id", "description", "party", "doc_ref", "memo", "lines")
LINE_KEYS: tuple[str, ...] = (
    "account", "debit", "credit", "tax_tag", "description", "party", "doc_ref", "memo",
)
_ENTRY_ALIASES = {"id": "entry_id", "postings": "lines", "narration": "description"}
_LINE_ALIASES = {"code": "account", "tag": "tax_tag"}

JSON_SHAPE_HINT = (
    'JSON entry shape: {"date": "YYYY-MM-DD", "description": "...", "party": "", '
    '"doc_ref": "", "memo": "", "entry_id": "(optional)", "lines": ['
    '{"account": "1200", "debit": "11500.00"}, '
    '{"account": "4100", "credit": "10000.00", "tax_tag": "NONE"}]} '
    "— amounts as strings or whole integers, never floats."
)
LINE_ARG_HINT = (
    "Write each line as ACCOUNT=AMOUNT[:TAX_TAG], e.g. --debit 1100=1000.00 or "
    "--credit 2310=1500.00:VAT:OUT:15."
)

_SEQUENCE_RE = re.compile(r"^[0-9]+$")


# ======================================================================================
# What the user said — before any validation
# ======================================================================================


@dataclass(frozen=True)
class LineSpec:
    """One posting line as given.  ``debit`` / ``credit`` are still *raw* here — text,
    int, Decimal or :class:`tb.Money` — and are parsed in :func:`build_entry`, so every
    bad amount in an entry can be reported together."""

    account: str
    debit: Any = None
    credit: Any = None
    tax_tag: str | None = None
    description: str | None = None
    party: str | None = None
    doc_ref: str | None = None
    memo: str | None = None
    origin: str = ""  # "--debit #1", "stdin lines[2]" — used in messages only


@dataclass(frozen=True)
class EntrySpec:
    """One journal entry as given: header fields plus its lines."""

    date: str = ""
    lines: tuple[LineSpec, ...] = ()
    entry_id: str = ""
    description: str = ""
    party: str = ""
    doc_ref: str = ""
    memo: str = ""
    source: str = "command line"


@dataclass(frozen=True)
class BuiltEntry:
    """A fully validated entry, ready to write."""

    entry: tb.Entry
    generated_id: bool
    warnings: tuple[str, ...] = ()


# ======================================================================================
# Parsing
# ======================================================================================


def parse_amount(value: Any, *, what: str = "amount", where: str = "") -> tb.Money:
    """Read a taka amount from CLI text or a JSON value as exact :class:`tb.Money`.

    ``None``, ``""`` and ``"-"`` mean ৳0.00.  Sub-paisa input is refused rather than
    rounded, floats and booleans are refused outright, and a :class:`tb.MoneyError`
    becomes a :class:`tb.JournalError` that names the line.
    """
    prefix = f"{where}: " if where else ""
    if value is None:
        return tb.Money.zero()
    if isinstance(value, tb.Money):
        return value
    if isinstance(value, bool):
        raise tb.JournalError(f"{prefix}{what} {value!r} is not an amount.", hint=JSON_SHAPE_HINT)
    if isinstance(value, float):
        raise tb.JournalError(
            f"{prefix}{what} {value!r} arrived as a float; write amounts as strings "
            f'("{value}") or whole integers so nothing is rounded on the way in.',
            hint=JSON_SHAPE_HINT,
        )
    try:
        if isinstance(value, str):
            text = value.strip()
            if text in ("", "-"):
                return tb.Money.zero()
            return tb.Money.from_str(text, exact=True, what=what)
        if isinstance(value, (int, Decimal)):
            return tb.Money.from_taka(value, exact=True, what=what)
    except tb.MoneyError as exc:
        raise tb.JournalError(f"{prefix}{exc.message}", hint=exc.hint) from None
    raise tb.JournalError(
        f"{prefix}{what}: cannot read a {type(value).__name__} as an amount.",
        hint=JSON_SHAPE_HINT,
    )


def parse_line_arg(text: str, side: str, *, origin: str = "") -> LineSpec:
    """Parse one ``--debit`` / ``--credit`` value: ``ACCOUNT=AMOUNT[:TAX_TAG]``.

    Only the *shape* is checked here; the amount and tag are validated with the rest
    of the entry in :func:`build_entry`.
    """
    if side not in SIDES:
        raise ValueError(f"side must be one of {SIDES}, got {side!r}")
    label = origin or f"--{side} {text!r}"
    raw = str(text or "").strip()
    if "=" not in raw:
        raise tb.JournalError(
            f"{label}: expected ACCOUNT=AMOUNT[:TAX_TAG], got {raw!r}.", hint=LINE_ARG_HINT
        )
    account, _, rest = raw.partition("=")
    account = account.strip()
    if not account:
        raise tb.JournalError(f"{label}: the account code before '=' is blank.", hint=LINE_ARG_HINT)
    amount_text, _, tag_text = rest.partition(":")
    amount_text = amount_text.strip()
    if not amount_text:
        raise tb.JournalError(f"{label}: no amount after '='.", hint=LINE_ARG_HINT)
    tag = tag_text.strip() or tb.TAG_NONE
    return LineSpec(
        account=account,
        debit=amount_text if side == SIDE_DEBIT else None,
        credit=amount_text if side == SIDE_CREDIT else None,
        tax_tag=tag,
        origin=label,
    )


def _text_field(value: Any, *, key: str, where: str) -> str:
    """Coerce a JSON scalar to text; reject structures."""
    if value is None:
        return ""
    if isinstance(value, bool) or isinstance(value, (list, dict)):
        raise tb.JournalError(
            f"{where}: {key} must be text, got {type(value).__name__}.", hint=JSON_SHAPE_HINT
        )
    return value.strip() if isinstance(value, str) else str(value).strip()


def _normalise_keys(
    data: Mapping[str, Any], *, allowed: Sequence[str], aliases: Mapping[str, str], where: str
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    unknown: list[str] = []
    for key, value in data.items():
        name = aliases.get(str(key), str(key))
        if name not in allowed:
            unknown.append(str(key))
            continue
        out[name] = value
    if unknown:
        raise tb.JournalError(
            f"{where}: unknown key(s) {', '.join(repr(k) for k in unknown)}; "
            f"allowed: {', '.join(allowed)}.",
            hint=JSON_SHAPE_HINT,
        )
    return out


def parse_json_entry(
    document: "str | bytes | Mapping[str, Any] | Sequence[Any]", *, where: str = "JSON entry"
) -> EntrySpec:
    """Build an :class:`EntrySpec` from JSON text or an already-decoded object.

    Floats are decoded as :class:`~decimal.Decimal` so no amount ever passes through a
    binary float.  A bare list is taken as ``lines`` (the header fields must then come
    from the command line).
    """
    if isinstance(document, (str, bytes)):
        text = document.decode("utf-8") if isinstance(document, bytes) else document
        if not text.strip():
            raise tb.JournalError(
                f"{where}: no JSON entry was received (empty input).", hint=JSON_SHAPE_HINT
            )
        try:
            obj: Any = json.loads(text, parse_float=Decimal)
        except json.JSONDecodeError as exc:
            raise tb.JournalError(
                f"{where}: not valid JSON — {exc.msg} at line {exc.lineno} column {exc.colno}.",
                hint=JSON_SHAPE_HINT,
            ) from None
    else:
        obj = document

    if isinstance(obj, (list, tuple)):
        obj = {"lines": list(obj)}
    if not isinstance(obj, Mapping):
        raise tb.JournalError(
            f"{where}: the top level must be a JSON object with date, description and lines; "
            f"got {type(obj).__name__}.",
            hint=JSON_SHAPE_HINT,
        )
    if "account" in obj and "lines" not in obj and "postings" not in obj:
        raise tb.JournalError(
            f"{where}: this looks like a single posting line, not an entry. Put the lines "
            'under "lines": [...] so they can be balanced against each other.',
            hint=JSON_SHAPE_HINT,
        )

    head = _normalise_keys(obj, allowed=ENTRY_KEYS, aliases=_ENTRY_ALIASES, where=where)
    raw_lines = head.get("lines")
    if raw_lines is None:
        raise tb.JournalError(f'{where}: "lines" is missing.', hint=JSON_SHAPE_HINT)
    if not isinstance(raw_lines, (list, tuple)):
        raise tb.JournalError(
            f'{where}: "lines" must be a list of objects, got {type(raw_lines).__name__}.',
            hint=JSON_SHAPE_HINT,
        )

    lines: list[LineSpec] = []
    for index, item in enumerate(raw_lines):
        label = f"{where} lines[{index}]"
        if not isinstance(item, Mapping):
            raise tb.JournalError(
                f"{label}: each line must be an object such as "
                f'{{"account": "1100", "debit": "1000.00"}}; got {type(item).__name__}.',
                hint=JSON_SHAPE_HINT,
            )
        fields = _normalise_keys(item, allowed=LINE_KEYS, aliases=_LINE_ALIASES, where=label)

        def optional(key: str) -> str | None:
            return _text_field(fields[key], key=key, where=label) if key in fields else None

        lines.append(
            LineSpec(
                account=_text_field(fields.get("account"), key="account", where=label),
                debit=fields.get("debit"),
                credit=fields.get("credit"),
                tax_tag=optional("tax_tag"),
                description=optional("description"),
                party=optional("party"),
                doc_ref=optional("doc_ref"),
                memo=optional("memo"),
                origin=label,
            )
        )

    return EntrySpec(
        date=_text_field(head.get("date"), key="date", where=where),
        lines=tuple(lines),
        entry_id=_text_field(head.get("entry_id"), key="entry_id", where=where),
        description=_text_field(head.get("description"), key="description", where=where),
        party=_text_field(head.get("party"), key="party", where=where),
        doc_ref=_text_field(head.get("doc_ref"), key="doc_ref", where=where),
        memo=_text_field(head.get("memo"), key="memo", where=where),
        source=where,
    )


def _stream_is_tty(stream: Any) -> bool:
    try:
        return bool(stream.isatty())
    except (AttributeError, ValueError):
        return False


def entry_spec_from_args(args: argparse.Namespace, *, stdin: Any = None) -> EntrySpec:
    """Combine ``--debit/--credit`` flags, ``--input FILE`` / ``--stdin`` JSON and the
    header flags into one :class:`EntrySpec`.  Reads stdin only when asked to, or when
    ``--json`` is set, no lines were given on the command line and stdin is a pipe."""
    stream = stdin if stdin is not None else sys.stdin
    pairs = list(getattr(args, "lines", None) or [])
    cli_lines = [
        parse_line_arg(text, side, origin=f"--{side} #{number}")
        for number, (side, text) in enumerate(pairs, 1)
    ]

    document: str | None = None
    source = "command line"
    input_path = getattr(args, "input", None)
    wants_stdin = bool(getattr(args, "stdin", False)) or input_path == "-"
    if input_path is not None and input_path != "-":
        path = Path(input_path)
        try:
            document = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise tb.JournalError(f"--input {path} is not UTF-8: {exc}") from None
        except OSError as exc:
            raise tb.JournalError(f"Could not read --input {path}: {exc}") from None
        source = str(path)
    elif wants_stdin or (
        getattr(args, "json", False) and not cli_lines and not _stream_is_tty(stream)
    ):
        document = stream.read()
        source = "stdin"

    base: EntrySpec | None = None
    if document is not None:
        base = parse_json_entry(document, where=source)

    if base is None and not cli_lines:
        raise tb.JournalError(
            "No entry given: add --debit/--credit lines, or pipe a JSON entry with --stdin "
            "(or --input FILE).",
            hint=LINE_ARG_HINT + " " + JSON_SHAPE_HINT,
        )

    spec = base if base is not None else EntrySpec(source=source)

    def pick(flag: str, current: str) -> str:
        value = getattr(args, flag, None)
        return str(value).strip() if value is not None else current

    combined_source = spec.source
    if base is not None and cli_lines:
        combined_source = f"{spec.source} + command line"
    return replace(
        spec,
        date=pick("date", spec.date),
        entry_id=pick("entry_id", spec.entry_id),
        description=pick("description", spec.description),
        party=pick("party", spec.party),
        doc_ref=pick("doc_ref", spec.doc_ref),
        memo=pick("memo", spec.memo),
        lines=tuple(spec.lines) + tuple(cli_lines),
        source=combined_source,
    )


# ======================================================================================
# Validation
# ======================================================================================


def generate_entry_id(when: "datetime.date | str", existing_ids: Iterable[str]) -> str:
    """``JE-YYYY-MM-NNNN`` — the next unused sequence number for that month.

    Depends only on the date and the ids already in the books: no clock, no random
    component, so the same books plus the same entry always produce the same id.
    """
    if not isinstance(when, datetime.date):
        when = tb.parse_date(when)
    prefix = f"{ENTRY_ID_PREFIX}-{when.year:04d}-{when.month:02d}-"
    highest = 0
    for entry_id in existing_ids:
        text = str(entry_id)
        if text.startswith(prefix):
            tail = text[len(prefix):]
            if _SEQUENCE_RE.match(tail):
                highest = max(highest, int(tail))
    return f"{prefix}{highest + 1:0{ENTRY_ID_WIDTH}d}"


def _raise_problems(problems: Sequence[tb.TakaBooksError]) -> None:
    """One problem is raised as itself (precise class and exit code); several become one
    :class:`tb.ValidationError` that lists them all."""
    if not problems:
        return
    if len(problems) == 1:
        raise problems[0]
    lines = [str(p.message) for p in problems]
    raise tb.ValidationError(
        f"The entry has {len(problems)} problems and was not written:\n  - "
        + "\n  - ".join(lines),
        problems=tuple(lines),
        hint="Fix every line above and post again. Nothing was written.",
    )


def _suggest_accounts(code: str, chart: tb.ChartOfAccounts) -> str:
    """'Did you mean …?' for an unknown account code."""
    codes = chart.codes()
    matches: list[str] = []
    if _SEQUENCE_RE.match(code):
        numeric = [(abs(int(c) - int(code)), c) for c in codes if _SEQUENCE_RE.match(c)]
        matches = [c for _, c in sorted(numeric)[:3]]
    if not matches:
        matches = difflib.get_close_matches(code, codes, n=3, cutoff=0.5)
    if not matches:
        lowered = code.lower()
        matches = [a.code for a in chart if lowered and lowered in a.name.lower()][:3]
    if not matches:
        return ""
    return "Did you mean " + ", ".join(chart.get(c).label for c in matches) + "?"


def _account_matches_kind(account: tb.Account, kind: str) -> bool:
    roles = _KIND_ROLES.get(kind, ())
    if account.role and account.role in roles:
        return True
    wanted = {tag.lower() for tag in _KIND_TAGS.get(kind, ())} | set(roles)
    return any(tag.strip().lower() in wanted for tag in account.tags)


def _entry_warnings(entry: tb.Entry, chart: "tb.ChartOfAccounts | None") -> list[str]:
    """Advisory notes that do not block the write (mirrors validate.py's warnings)."""
    warnings: list[str] = []
    if not entry.description:
        warnings.append(
            f"entry {entry.entry_id} has no description; future you will not remember "
            "what it was for."
        )
    for posting in entry.postings:
        if not posting.tax_tag.is_none and not posting.doc_ref:
            warnings.append(
                f"account {posting.account} carries {posting.tax_tag} but no doc_ref — a tax "
                "line should cite its চালান / invoice or Mushak document number."
            )
    if chart is not None:
        accounts = [chart.get(code) for code in entry.accounts if chart.has(code)]
        seen: set[str] = set()
        for posting in entry.postings:
            kind = posting.tax_tag.kind
            if kind == tb.TAG_NONE or kind in seen:
                continue
            seen.add(kind)
            declared = [role for role in _KIND_ROLES.get(kind, ()) if chart.by_role(role)]
            if not declared:
                continue
            if any(_account_matches_kind(account, kind) for account in accounts):
                continue
            expected = ", ".join(
                account.label for role in declared for account in chart.by_role(role)
            )
            warnings.append(
                f"entry {entry.entry_id} carries {posting.tax_tag} ({_KIND_TERM.get(kind, kind)}) "
                f"but no line posts to the matching tax account ({expected}); validate.py "
                "will flag it as a tax-tag orphan."
            )
    return warnings


def build_entry(
    spec: EntrySpec,
    *,
    chart: "tb.ChartOfAccounts | None" = None,
    existing: "Mapping[str, tb.Entry] | Iterable[str]" = (),
) -> BuiltEntry:
    """Validate everything about ``spec`` and return the :class:`tb.Entry` to write.

    Every structural problem (date, amounts, tags, accounts) is collected first so
    they can all be reported at once; then the id is settled and the entry is required
    to balance.  Raises a :class:`tb.TakaBooksError` subclass — never returns a bad entry.
    """
    problems: list[tb.TakaBooksError] = []
    source = spec.source or "entry"

    # -- date ------------------------------------------------------------------------
    date: datetime.date | None = None
    if not str(spec.date or "").strip():
        problems.append(
            tb.JournalError(
                f"{source}: date is required.",
                hint='Pass --date YYYY-MM-DD, or put "date": "YYYY-MM-DD" in the JSON entry.',
            )
        )
    else:
        try:
            date = tb.parse_date(spec.date, where=source)
        except tb.JournalError as exc:
            problems.append(exc)

    # -- entry id shape --------------------------------------------------------------
    entry_id = str(spec.entry_id or "").strip()
    if entry_id and any(ch in entry_id for ch in "\r\n"):
        problems.append(tb.JournalError(f"{source}: entry_id must be a single line of text."))

    # -- lines -----------------------------------------------------------------------
    if not spec.lines:
        problems.append(
            tb.JournalError(
                f"{source}: no posting lines were given; an entry needs at least a debit "
                "and a credit.",
                hint=LINE_ARG_HINT,
            )
        )

    chart_name = (
        chart.source_path.name if chart is not None and chart.source_path else tb.ACCOUNTS_FILENAME
    )
    checked: list[tuple[LineSpec, str, tb.Money, tb.Money, tb.TaxTag]] = []
    for index, line in enumerate(spec.lines, 1):
        label = line.origin or f"line {index}"
        ok = True

        account = str(line.account or "").strip()
        if not account:
            problems.append(tb.JournalError(f"{label}: account code is blank."))
            ok = False

        debit = credit = tb.Money.zero()
        try:
            debit = parse_amount(line.debit, what="debit", where=label)
        except tb.JournalError as exc:
            problems.append(exc)
            ok = False
        try:
            credit = parse_amount(line.credit, what="credit", where=label)
        except tb.JournalError as exc:
            problems.append(exc)
            ok = False

        if ok:
            for side, amount in ((SIDE_DEBIT, debit), (SIDE_CREDIT, credit)):
                if amount.is_negative():
                    problems.append(
                        tb.JournalError(
                            f"{label} (account {account}): {side} "
                            f"{tb.format_bdt(amount, symbol=True)} is negative. Reverse the "
                            "sides instead of using a negative amount."
                        )
                    )
                    ok = False
        if ok:
            if debit.is_zero() and credit.is_zero():
                problems.append(
                    tb.JournalError(
                        f"{label} (account {account}): amount is zero — every line must carry "
                        "a debit or a credit."
                    )
                )
                ok = False
            elif not debit.is_zero() and not credit.is_zero():
                problems.append(
                    tb.JournalError(
                        f"{label} (account {account}): debit "
                        f"{tb.format_bdt(debit, symbol=True)} and credit "
                        f"{tb.format_bdt(credit, symbol=True)} are both set. Split it into "
                        "two lines."
                    )
                )
                ok = False

        tag: tb.TaxTag | None = None
        try:
            tag = tb.TaxTag.parse(line.tax_tag if line.tax_tag is not None else "", where=label)
        except tb.TaxTagError as exc:
            problems.append(exc)
            ok = False

        if account and chart is not None:
            if not chart.has(account):
                suggestion = _suggest_accounts(account, chart)
                problems.append(
                    tb.UnknownAccountError(
                        f"{label}: account code {account!r} is not in {chart_name}.",
                        code=account,
                        hint=(suggestion + " " if suggestion else "")
                        + "Add the account to accounts.toml or use an existing code; "
                        "TakaBooks never posts to an account it cannot name.",
                    )
                )
                ok = False
            else:
                account_obj = chart.get(account)
                retired = [t for t in account_obj.tags if t.strip().lower() in INACTIVE_TAGS]
                if retired:
                    problems.append(
                        tb.AccountError(
                            f"{label}: account {account_obj.label} is tagged {retired[0]!r} in "
                            f"{chart_name}; posting to a retired account is refused.",
                            hint="Post to its replacement account, or drop the tag from "
                            "accounts.toml if the account is in use again.",
                        )
                    )
                    ok = False
                if (
                    tag is not None
                    and not tag.is_none
                    and account_obj.role in _CONTROL_ROLES
                    and account_obj.role not in _KIND_ROLES.get(tag.kind, ())
                ):
                    problems.append(
                        tb.TaxTagError(
                            f"{label}: tax_tag {tag} ({_KIND_TERM.get(tag.kind, tag.kind)}) sits "
                            f"on {account_obj.label}, which {chart_name} declares as role "
                            f"{account_obj.role!r} — a different tax.",
                            hint=tb.TAX_TAG_GRAMMAR,
                        )
                    )
                    ok = False

        if ok and tag is not None:
            checked.append((line, account, debit, credit, tag))

    _raise_problems(problems)
    assert date is not None  # guaranteed by the checks above

    # -- entry id -----------------------------------------------------------------------
    existing_map: "Mapping[str, tb.Entry] | None" = (
        existing if isinstance(existing, Mapping) else None
    )
    existing_ids = (
        set(existing_map.keys()) if existing_map is not None else {str(i) for i in existing}
    )
    generated = False
    if not entry_id:
        entry_id = generate_entry_id(date, existing_ids)
        generated = True
    elif entry_id in existing_ids:
        where = ""
        if existing_map is not None:
            previous = existing_map[entry_id]
            where = f" — dated {previous.date.isoformat()}"
            if previous.location:
                where += f" at {previous.location}"
        raise tb.DuplicateEntryError(
            f"entry_id {entry_id!r} is already used in these books{where}.",
            entry_id=entry_id,
            hint=f"Leave the id out to have the next {ENTRY_ID_PREFIX}-YYYY-MM-NNNN generated, "
            "or choose an unused one. To fix an earlier entry, post a reversing entry; "
            "never reuse its id.",
        )

    # -- postings: debits first, then credits, each in the order given ------------------
    ordered = [c for c in checked if not c[2].is_zero()] + [c for c in checked if c[2].is_zero()]

    def choose(own: "str | None", default: str) -> str:
        return own if own is not None else default

    postings = [
        tb.Posting(
            date=date,
            entry_id=entry_id,
            description=choose(line.description, spec.description),
            account=account,
            debit=debit,
            credit=credit,
            party=choose(line.party, spec.party),
            doc_ref=choose(line.doc_ref, spec.doc_ref),
            tax_tag=tag,
            memo=choose(line.memo, spec.memo),
        )
        for line, account, debit, credit, tag in ordered
    ]
    entry = tb.Entry.from_postings(postings)
    entry.require_balanced()  # BalanceError (exit 5) with both totals and the difference
    return BuiltEntry(
        entry=entry, generated_id=generated, warnings=tuple(_entry_warnings(entry, chart))
    )


# ======================================================================================
# Writing
# ======================================================================================


def render_csv(postings: Iterable[tb.Posting], *, header: bool) -> str:
    """Exactly the text :func:`tb.append_journal_csv` will add for these postings."""
    handle = io.StringIO(newline="")
    writer = csv.writer(handle, lineterminator="\n")
    if header:
        writer.writerow(tb.JOURNAL_COLUMNS)
    writer.writerows(posting.to_cells() for posting in postings)
    return handle.getvalue()


def post_entry(
    books_dir: "Path | str",
    spec: EntrySpec,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Validate ``spec`` against the books and append it (unless ``dry_run``).

    Returns the result mapping that ``--json`` prints.  Raises a
    :class:`tb.TakaBooksError` — and writes nothing — on any refusal.
    """
    root = Path(books_dir)
    config = tb.Config.load(root)
    chart = tb.ChartOfAccounts.from_toml_path(root / config.accounts_file)
    journal_directory = tb.journal_dir(root, config.journal_dirname)

    warnings: list[str] = []
    existing: dict[str, tb.Entry] = {}
    ledger: "tb.Ledger | None" = None
    if journal_directory.is_dir():
        # Tolerant of *old* problems (validate.py reports those); strict about parsing,
        # because an unreadable file means entry ids cannot be checked.
        ledger = tb.Ledger.load(
            root, require_balanced=False, strict_accounts=False, config=config, chart=chart
        )
        existing = {entry.entry_id: entry for entry in ledger.entries}
    else:
        warnings.append(
            f"{journal_directory} does not exist yet; it "
            f"{'would be' if dry_run else 'was'} created."
        )

    built = build_entry(spec, chart=chart, existing=existing)
    entry = built.entry
    warnings.extend(built.warnings)

    path = tb.journal_path_for(root, entry.date, config.journal_dirname)
    creates_file = not path.exists() or path.stat().st_size == 0

    if ledger is not None:
        broken = ledger.unbalanced_entries()
        if broken:
            ids = ", ".join(e.entry_id for e in broken[:5])
            more = f" and {len(broken) - 5} more" if len(broken) > 5 else ""
            noun = "entry" if len(broken) == 1 else "entries"
            warnings.append(
                f"these books already hold {len(broken)} unbalanced {noun} ({ids}{more}); "
                "run validate.py. This new entry balances and is recorded regardless."
            )
        same_file = [p for p in ledger.postings if Path(p.source_file).name == path.name]
        if same_file and entry.date < same_file[-1].date:
            warnings.append(
                f"{path.name}: this entry is dated {entry.date.isoformat()} but the last row in "
                f"the file is dated {same_file[-1].date.isoformat()}; validate.py will note it "
                "as out of order (back-dated entries are allowed)."
            )

    csv_text = render_csv(entry.postings, header=creates_file)
    tax_tags: list[str] = []
    for posting in entry.postings:
        canonical = str(posting.tax_tag)
        if not posting.tax_tag.is_none and canonical not in tax_tags:
            tax_tags.append(canonical)

    def describe(posting: tb.Posting) -> dict[str, Any]:
        account = chart.get(posting.account) if chart.has(posting.account) else None
        return {
            "account": posting.account,
            "account_name": account.name if account else "",
            "account_name_bn": account.name_bn if account else "",
            "side": SIDE_DEBIT if posting.is_debit else SIDE_CREDIT,
            "amount": posting.amount,
            "amount_formatted": config.format_money(posting.amount, symbol=True),
            "tax_tag": str(posting.tax_tag),
            "tax_tag_description": posting.tax_tag.describe(),
            "description": posting.description,
            "party": posting.party,
            "doc_ref": posting.doc_ref,
            "memo": posting.memo,
        }

    result: dict[str, Any] = {
        "ok": True,
        "dry_run": bool(dry_run),
        "books_dir": str(root),
        "business": config.display_name,
        "file": str(path),
        "month": entry.postings[0].month,
        "created_file": creates_file,
        "entry_id": entry.entry_id,
        "entry_id_generated": built.generated_id,
        "date": entry.date,
        "description": entry.description,
        "party": spec.party,
        "doc_ref": spec.doc_ref,
        "memo": spec.memo,
        "lines": len(entry.postings),
        "total_debit": entry.total_debit,
        "total_credit": entry.total_credit,
        "total_debit_formatted": config.format_money(entry.total_debit, symbol=True),
        "total_credit_formatted": config.format_money(entry.total_credit, symbol=True),
        "balanced": entry.is_balanced,
        "postings": [describe(p) for p in entry.postings],
        "rows": [p.to_row() for p in entry.postings],
        "csv": csv_text,
        "tax_tags": tax_tags,
        "source": spec.source,
        "warnings": warnings,
        "attribution": tb.ATTRIBUTION,
    }
    if dry_run:
        return result

    tb.append_journal_csv(path, entry.postings)

    # Read it back: never report success on something the ledger cannot read.
    written = tb.read_journal_csv(path, chart=chart, relative_to=root.parent)
    mine = tuple(p for p in written if p.entry_id == entry.entry_id)
    if mine != tuple(entry.postings):
        raise tb.LedgerError(
            f"{path}: entry {entry.entry_id} did not read back exactly as written; inspect "
            "the file before posting again."
        )
    tb.Entry.from_postings(mine).require_balanced()
    return result


# ======================================================================================
# Output
# ======================================================================================


def render_text(result: Mapping[str, Any]) -> str:
    """Human rendering of a :func:`post_entry` result."""
    lines: list[str] = []
    dry = bool(result.get("dry_run"))
    how = "new file, header written" if result["created_file"] else "appended"
    if dry:
        lines.append(
            f"dry run — would post {result['entry_id']} → {result['file']} ({how}); "
            "nothing was written"
        )
    else:
        lines.append(f"posted {result['entry_id']} → {result['file']} ({how})")
    if result.get("entry_id_generated"):
        lines[-1] += "  [entry_id generated]"

    date_value = result["date"]
    date_text = date_value if isinstance(date_value, str) else date_value.isoformat()
    head = f"  {date_text}"
    if result.get("description"):
        head += f"  {result['description']}"
    lines.append(head)
    meta = []
    if result.get("party"):
        meta.append(f"party {result['party']}")
    if result.get("doc_ref"):
        meta.append(f"doc_ref {result['doc_ref']}")
    if result.get("memo"):
        meta.append(f"memo {result['memo']}")
    if meta:
        lines.append("  " + " · ".join(meta))

    postings = list(result.get("postings", []))
    labels = []
    for p in postings:
        label = f"{p['account']} {p['account_name']}".rstrip()
        if p.get("account_name_bn"):
            label += f" ({p['account_name_bn']})"
        labels.append(label)
    width = max((len(lbl) for lbl in labels), default=len("account"))
    amount_width = max((len(p["amount_formatted"]) for p in postings), default=0)
    amount_width = max(amount_width, len(f"{tb.term('debit')}"), len(f"{tb.term('credit')}"))
    lines.append(
        f"      {'account'.ljust(width)}  {tb.term('debit').rjust(amount_width)}  "
        f"{tb.term('credit').rjust(amount_width)}"
    )
    for p, label in zip(postings, labels):
        is_debit = p["side"] == SIDE_DEBIT
        debit_cell = p["amount_formatted"] if is_debit else ""
        credit_cell = "" if is_debit else p["amount_formatted"]
        row = (
            f"  {'Dr' if is_debit else 'Cr'}  {label.ljust(width)}  "
            f"{debit_cell.rjust(amount_width)}  {credit_cell.rjust(amount_width)}"
        )
        if p["tax_tag"] != tb.TAG_NONE:
            row += f"  {p['tax_tag']} — {p['tax_tag_description']}"
        lines.append(row.rstrip())
    lines.append(
        f"  debits {result['total_debit_formatted']} = credits "
        f"{result['total_credit_formatted']} — balanced"
    )
    if result.get("tax_tags"):
        lines.append("  tax tags: " + ", ".join(result["tax_tags"]))
    if dry:
        lines.append("")
        lines.append(f"would append to {result['file']}:")
        lines.extend("  " + row for row in str(result["csv"]).splitlines())
    return "\n".join(lines)


# ======================================================================================
# CLI
# ======================================================================================


class _LineAction(argparse.Action):
    """Collect ``--debit`` / ``--credit`` values into one list, in command-line order."""

    def __call__(self, parser, namespace, values, option_string=None):  # type: ignore[override]
        items = list(getattr(namespace, self.dest, None) or [])
        items.append((self.const, values))
        setattr(namespace, self.dest, items)


def build_parser() -> argparse.ArgumentParser:
    parser = tb.common_parser(
        PROG,
        f"Record one validated {tb.term('journal')} entry in books/journal/YYYY-MM.csv. "
        "Refuses — and writes nothing — unless debits equal credits, every account exists, "
        "the date is ISO and every tax_tag parses.",
        epilog=(
            "examples:\n"
            "  post.py --books books --date 2026-07-15 --description 'Cash sale' \\\n"
            "      --debit 1100=11500.00 --credit 4100=10000.00 --credit 2310=1500.00:VAT:OUT:15\n"
            "  cat entry.json | post.py --books books --json\n"
            "  post.py --books books --input entry.json --dry-run\n\n"
            "JSON entry: {\"date\", \"description\", \"party\", \"doc_ref\", \"memo\", "
            "\"entry_id\", \"lines\": [{\"account\", \"debit\" | \"credit\", \"tax_tag\", ...}]}\n"
            "amounts as strings (\"1,00,000.00\", \"৳ 500\") or whole integers — never floats.\n\n"
            "exit codes: 0 ok · 2 config/usage · 3 unknown or retired account · 4 date, amount "
            "or duplicate id · 5 unbalanced · 6 tax_tag · 7 several problems at once\n\n"
            f"{tb.ATTRIBUTION}"
        ),
    )
    parser.add_argument("--date", default=None, metavar="YYYY-MM-DD", help="entry date (ISO only)")
    parser.add_argument(
        "--id", "--entry-id", dest="entry_id", default=None, metavar="ENTRY_ID",
        help=f"entry id; default: next {ENTRY_ID_PREFIX}-YYYY-MM-NNNN for that month",
    )
    parser.add_argument(
        "--description", default=None, metavar="TEXT", help="what the entry records"
    )
    parser.add_argument(
        "--party", default=None, metavar="TEXT", help="customer or supplier (not an account)"
    )
    parser.add_argument(
        "--doc-ref", dest="doc_ref", default=None, metavar="TEXT",
        help="voucher, চালান, Mushak 6.3 or bill number",
    )
    parser.add_argument("--memo", default=None, metavar="TEXT", help="free text, written last")
    parser.add_argument(
        "--debit", dest="lines", action=_LineAction, const=SIDE_DEBIT, default=None,
        metavar="ACCOUNT=AMOUNT[:TAX_TAG]", help="a debit line (repeatable)",
    )
    parser.add_argument(
        "--credit", dest="lines", action=_LineAction, const=SIDE_CREDIT, default=None,
        metavar="ACCOUNT=AMOUNT[:TAX_TAG]", help="a credit line (repeatable)",
    )
    parser.add_argument(
        "--stdin", action="store_true",
        help="read a JSON entry from standard input (implied by --json when stdin is a pipe "
        "and no --debit/--credit is given)",
    )
    parser.add_argument(
        "--input", default=None, metavar="FILE",
        help="read a JSON entry from FILE ('-' for standard input)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="validate and show exactly what would be written; write nothing",
    )
    return parser


def main(argv: "list[str] | None" = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    with tb.cli_guard(json_output=args.json):
        spec = entry_spec_from_args(args)
        result = post_entry(args.books, spec, dry_run=args.dry_run)
        for warning in result["warnings"]:
            sys.stderr.write(f"warning: {warning}\n")
        if args.json:
            sys.stdout.write(tb.json_dumps(result) + "\n")
        else:
            sys.stdout.write(render_text(result) + "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
