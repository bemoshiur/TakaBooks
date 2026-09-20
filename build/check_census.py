#!/usr/bin/env python3
"""TakaBooks — published-figure guard.

Two kinds of number drift out of step with the code, and both have happened:

  1. **Version strings.** ``package.json``, ``src/engine/takabooks.py``,
     ``build/build.py`` and ``CITATION.cff`` each carry the project version.
     They once read 0.0.0, 0.1.0, 1.0.0 and 1.0.0 at the same time, so every
     script's ``--version`` reported a version that never shipped.

  2. **The rate-node census.** ``README.md``, ``docs/index.md`` and the Bangla
     summary each quote how many rate nodes are verified. They once carried
     four mutually inconsistent sets while the engine reported a fifth.

This script re-derives both from the source of truth — the files themselves and
``rates.py``'s own audit — and fails if any published figure disagrees.
Standard library only, like every other TakaBooks script.

Exit codes:  0 all figures agree · 1 a figure disagrees · 2 usage or missing file
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src" / "engine"))

BANGLA_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")


def bn(n: int) -> str:
    """Render an integer in Bangla digits, as the Bangla summary writes them."""
    return str(n).translate(BANGLA_DIGITS)


def read(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"error: {path} does not exist")
    return path.read_text(encoding="utf-8")


def collect_versions() -> dict[str, str]:
    """Every place the project version is written down."""
    found: dict[str, str] = {}

    pkg = json.loads(read(ROOT / "package.json"))
    found["package.json"] = pkg.get("version", "")

    m = re.search(r'^__version__ = "([^"]+)"', read(ROOT / "src/engine/takabooks.py"), re.M)
    found["src/engine/takabooks.py"] = m.group(1) if m else ""

    m = re.search(r'^PROJECT_VERSION = "([^"]+)"', read(ROOT / "build/build.py"), re.M)
    found["build/build.py"] = m.group(1) if m else ""

    m = re.search(r'^version: "([^"]+)"', read(ROOT / "CITATION.cff"), re.M)
    found["CITATION.cff"] = m.group(1) if m else ""

    return found


def census() -> dict[str, int]:
    """The engine's own audit of the shipped rates file — the source of truth."""
    import rates as rt  # noqa: PLC0415 — path is set up above

    files = sorted((ROOT / "src" / "data").glob("rates-AY*.toml"))
    if not files:
        raise SystemExit("error: no src/data/rates-AY*.toml found")
    audit = rt.RateSet.from_path(files[-1], allow_placeholders=True).audit()

    by_prefix: dict[str, dict[str, int]] = {}
    for bucket in ("verified", "unverified", "placeholder"):
        for key in audit[bucket]:
            row = by_prefix.setdefault(key.split(".")[0], {})
            row[bucket] = row.get(bucket, 0) + 1
            row["total"] = row.get("total", 0) + 1

    return {
        "total": audit["total_rate_nodes"],
        "verified": audit["verified_count"],
        "unverified": audit["unverified_count"],
        "placeholder": audit["placeholder_count"],
        "by_prefix": by_prefix,  # type: ignore[dict-item]
    }


def check() -> list[str]:
    """Return one problem string per disagreement; empty means everything agrees."""
    problems: list[str] = []

    # ---- 1. the four version strings ------------------------------------------------
    versions = collect_versions()
    distinct = set(versions.values())
    if len(distinct) != 1:
        detail = ", ".join(f"{k} = {v or '(unreadable)'}" for k, v in versions.items())
        problems.append(f"version strings disagree: {detail}")
    only = next(iter(distinct)) if len(distinct) == 1 else None
    if only in {"", "0.0.0"}:
        problems.append(
            f"project version is {only!r} — a real version must be set before publishing"
        )

    # ---- 2. the rate-node census as published ---------------------------------------
    c = census()
    total, ver, unv, ph = c["total"], c["verified"], c["unverified"], c["placeholder"]
    by = c["by_prefix"]  # type: ignore[assignment]

    readme = read(ROOT / "README.md")
    index = read(ROOT / "docs/index.md")

    # The English disclaimer sentence.
    if f"**{ver} of its {total} figures are verified" not in readme:
        problems.append(
            f"README.md disclaimer does not state '{ver} of its {total} figures are verified'"
        )

    # The `rates.py` transcript README presents as live output.
    transcript = (
        f"| verified | {ver} |\n| unverified | {unv} |\n| placeholder | {ph} |\n| total | {total} |"
    )
    if transcript not in readme:
        problems.append(
            f"README.md rates.py transcript is stale — expected verified {ver}, "
            f"unverified {unv}, placeholder {ph}, total {total}"
        )

    # The Bangla summary.
    if f"মোট **{bn(total)}টি নোডের মধ্যে {bn(ver)}টি" not in readme:
        problems.append(
            f"README.md Bangla summary does not state মোট {bn(total)}টি / {bn(ver)}টি verified"
        )

    # The Pages landing page.
    if f"{total} rate nodes" not in index:
        problems.append(f"docs/index.md does not state '{total} rate nodes'")

    # PRESENCE IS NOT ENOUGH. Every check above asks whether the CORRECT figure appears.
    # None of them asks whether a STALE one still does, so a second sentence quoting an
    # older census passes silently — which is exactly what happened: the guard reported
    # OK while README's headline still said "529 rate nodes: 474 verified, 52 unverified".
    # So: any three-digit number sitting next to "rate nodes", or in a "N verified"
    # phrase, must be one the audit actually reports.
    allowed = {str(total), str(ver), str(unv), str(ph)} | {
        str(row.get(k, 0)) for row in by.values() for k in ("total", "verified", "unverified", "placeholder")
    }
    for name, body in (("README.md", readme), ("docs/index.md", index)):
        for pattern, what in (
            (r"(\d{3,4})\s+rate nodes", "rate nodes"),
            (r"\*\*(\d{3,4}) rate nodes:", "rate-node census"),
            (r"(\d{3,4}) verified", "verified count"),
            (r"(\d{2,4}) unverified", "unverified count"),
        ):
            for found in re.findall(pattern, body):
                if found not in allowed:
                    problems.append(
                        f"{name} states '{found} {what}', which the audit does not report "
                        f"(total {total}, verified {ver}, unverified {unv}, placeholder {ph})"
                    )

    # The per-area table: every prefix the table names must match the audit.
    for prefix, label in (
        ("income_tax", "income tax"),
        ("vat", "VAT"),
        ("tds", "TDS"),
        ("vds", "VDS"),
        ("deadlines", "compliance calendar"),
    ):
        row = by.get(prefix)
        if not row:
            continue
        n_total = row.get("total", 0)
        n_ver = row.get("verified", 0)
        n_unv = row.get("unverified", 0)
        n_ph = row.get("placeholder", 0)
        if n_unv == 0 and n_ph == 0:
            expected = f"{n_total} nodes — all {n_total} verified"
        elif n_ph == 0:
            expected = f"{n_total} nodes — {n_ver} verified · {n_unv} unverified"
        else:
            expected = (
                f"{n_total} nodes — {n_ver} verified · {n_unv} unverified · {n_ph} placeholder"
            )
        if expected not in readme:
            problems.append(
                f"README.md per-area table: {label} row should read '{expected}'"
            )

    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check_census.py",
        description=(
            "Verify that every published version string and rate-node count matches "
            "the code and the engine's own audit."
        ),
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    try:
        problems = check()
        data = {"versions": collect_versions(), **{k: v for k, v in census().items() if k != "by_prefix"}}
    except SystemExit as exc:  # a missing or unreadable file
        print(exc, file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"ok": not problems, "problems": problems, **data}, indent=2, ensure_ascii=False))
        return 1 if problems else 0

    print("# TakaBooks — published-figure guard\n")
    print(f"Project version: {next(iter(set(data['versions'].values())), '(disagreeing)')}")
    print(
        f"Rate nodes: {data['total']} total — {data['verified']} verified, "
        f"{data['unverified']} unverified, {data['placeholder']} placeholder\n"
    )
    if problems:
        print(f"{len(problems)} published figure(s) disagree with the code:\n")
        for p in problems:
            print(f"  - {p}")
        print(
            "\nCorrect the published figure, or re-run the build, so the documentation "
            "states what the engine reports."
        )
        return 1
    print("OK — every published version string and rate count matches the code.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
