#!/usr/bin/env python3
"""TakaBooks — reconcile unverified rate nodes against harvested primary law.

For every node in ``src/data/rates-AY2026-27.toml`` marked ``verified = false``
or ``placeholder = true``, search the primary text harvested by
``tools/lawcorpus.py`` for the figure the node claims, and report what the
statute actually says — with the Bangla quoted and its section URL beside it.

EVIDENCE, NOT STRING MATCHING.  A bare ``১৫`` occurs in hundreds of places; the
fact that it appears somewhere in an Act is worth nothing.  A hit counts only
when the numeral appears in a section this node is plausibly *about*, which is
established two ways:

  CITED    the node's own ``note`` names the provision (e.g. "ITA 2023 s.78"),
           and the numeral is found in that very section.  Strongest evidence.
  KEYWORD  the numeral is found in a section whose text carries the node's own
           subject words.  Supporting evidence, never conclusive on its own.

Anything weaker is reported as a LEAD, not a finding.  The rates file's rule is
that absent beats wrong, so this tool proposes and quotes; it never decides a
figure is verified on a coincidence.

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src" / "engine"))
sys.path.insert(0, str(ROOT / "tools"))

import bnnum  # noqa: E402

RATES = ROOT / "src" / "data" / "rates-AY2026-27.toml"

#: Subject words worth searching on, per rates-file section prefix.  Bangla only:
#: the statutes are Bangla, and an English word in a Bangla Act is noise.
SUBJECT_HINTS = {
    "rebate": ("রেয়াত", "বিনিয়োগ"),
    "surcharge": ("সারচার্জ",),
    "minimum_tax": ("ন্যূনতম কর",),
    "capital_gains": ("মূলধনি", "মূলধনী"),
    "dividend": ("লভ্যাংশ",),
    "turnover": ("টার্নওভার", "টার্ন ওভার"),
    "registration": ("নিবন্ধন",),
    "advance_tax": ("অগ্রিম কর",),
    "supplementary_duty": ("সম্পূরক শুল্ক",),
    "deadlines": ("দাখিল", "সময়সীমা", "তারিখ"),
    "exemptions": ("অব্যাহতি", "রেয়াতি"),
    "thresholds": ("সীমা",),
    "penalties": ("জরিমানা", "দণ্ড"),
    "interest": ("সুদ",),
}

#: 'ITA 2023 s.78', 's.163(6)', 'VAT Act s.31' — the shapes the notes really use.
_CITE = re.compile(r"\bs\.\s?(\d{1,3}[A-Za-z]{0,2})\b")

#: WHICH ACT a bare section number belongs to.  This is not pedantry: ITA 2023
#: s.78 is the investment rebate and VAT Act s.78 is the VAT authority, so a
#: citation matched against the wrong Act "confirms" a rebate rate from an
#: administrative clause. An early run of this tool did exactly that.
_ACT_WORDS = (
    ("ita2023", ("ITA 2023", "ITA2023", "Income Tax Act", "আয়কর আইন")),
    ("vat2012", ("VAT Act", "VAT & SD", "VAT and SD", "মূল্য সংযোজন", "VAT & SD Act")),
    ("fa2026", ("Finance Act 2026", "Act 96 of 2026", "অর্থ আইন")),
)
#: With no Act named, the rates-file section the node lives in decides.
_KEY_ACT = (("income_tax.", "ita2023"), ("tds.", "ita2023"),
            ("vat.", "vat2012"), ("vds.", "vat2012"))


def act_for_citation(note: str, key: str, position: int) -> str:
    """The act a section citation refers to — named in the note, else inferred.

    ``position`` is where the citation sits, so the nearest preceding Act name
    wins when a note discusses more than one statute.
    """
    best, best_at = "", -1
    for act, words in _ACT_WORDS:
        for word in words:
            at = note.rfind(word, 0, position)
            if at > best_at:
                best, best_at = act, at
    if best:
        return best
    for prefix, act in _KEY_ACT:
        if key.startswith(prefix):
            return act
    return ""


def load_nodes() -> list[dict]:
    """Every unverified or placeholder node, with its value, unit, note and key."""
    sys.path.insert(0, str(ROOT / "src" / "engine"))
    import rates as rt  # noqa: PLC0415

    audit = rt.RateSet.from_path(RATES, allow_placeholders=True).audit()
    raw = tomllib.loads(RATES.read_text(encoding="utf-8"))

    def at(key: str):
        cur = raw
        for part in key.split("."):
            m = re.match(r"([^\[]+)(?:\[(\d+)\])?$", part)
            if not m:
                return None
            cur = cur.get(m.group(1)) if isinstance(cur, dict) else None
            if cur is None:
                return None
            if m.group(2) is not None:
                idx = int(m.group(2))
                cur = cur[idx] if isinstance(cur, list) and idx < len(cur) else None
        return cur

    out = []
    for state in ("unverified", "placeholder"):
        for key in audit[state]:
            node = at(key)
            if not isinstance(node, dict):
                continue
            out.append({
                "key": key,
                "state": state,
                "value": node.get("value"),
                "unit": node.get("unit", ""),
                "label_en": node.get("label_en", ""),
                "label_bn": node.get("label_bn", ""),
                "note": node.get("note", "") or "",
                "source": node.get("source", "") or "",
            })
    return out


def load_corpus(paths: list[Path]) -> list[dict]:
    corpus: list[dict] = []
    for path in paths:
        if path.exists():
            corpus.extend(json.loads(path.read_text(encoding="utf-8")))
    return corpus


def hints_for(key: str) -> tuple[str, ...]:
    words: list[str] = []
    for token, hint in SUBJECT_HINTS.items():
        if token in key:
            words.extend(hint)
    return tuple(dict.fromkeys(words))


def cited_sections(note: str, key: str) -> set[tuple[str, str]]:
    """``{(act, section)}`` — a section number is meaningless without its Act."""
    out = set()
    for m in _CITE.finditer(note):
        act = act_for_citation(note, key, m.start())
        if act:
            out.add((act, m.group(1)))
    return out


def context(text: str, needle: str, width: int = 180) -> str:
    i = text.find(needle)
    if i < 0:
        return ""
    start, end = max(0, i - width), min(len(text), i + len(needle) + width)
    return re.sub(r"\s+", " ", text[start:end]).strip()


def reconcile(node: dict, corpus: list[dict]) -> dict:
    forms = bnnum.forms_for(node["value"], node["unit"])
    hints = hints_for(node["key"])
    cites = cited_sections(node["note"], node["key"])
    findings: list[dict] = []

    for entry in corpus:
        text = entry["text"]
        for form in forms:
            if form not in text:
                continue
            in_cited = (entry["act"], entry.get("section", "")) in cites
            keyword = next((h for h in hints if h in text), "")
            if not in_cited and not keyword:
                grade = "LEAD"
            elif in_cited:
                grade = "CITED"
            else:
                grade = "KEYWORD"
            findings.append({
                "grade": grade, "form": form, "url": entry["url"],
                "act": entry["act"], "section": entry.get("section", ""),
                "title": entry["title"], "keyword": keyword,
                "quote": context(text, form),
            })
            break

    order = {"CITED": 0, "KEYWORD": 1, "LEAD": 2}
    findings.sort(key=lambda f: order[f["grade"]])
    verdict = findings[0]["grade"] if findings else "NOT FOUND"
    return {"node": node, "forms": forms,
            "cites": sorted(f"{a} s.{n}" for a, n in cites),
            "findings": findings, "verdict": verdict}


def render(results: list[dict]) -> str:
    counts: dict[str, int] = {}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1

    lines = [
        "# TakaBooks — unverified nodes against primary law",
        "",
        "Every node in `src/data/rates-AY2026-27.toml` marked `verified = false` or",
        "`placeholder = true`, searched against the Bangla text of ITA 2023, the VAT & SD",
        "Act 2012 and the Finance Act 2026 as published on bdlaws.minlaw.gov.bd.",
        "",
        "| Verdict | Meaning | Nodes |",
        "| :--- | :--- | ---: |",
        f"| CITED | the figure appears in the very section the node's note names | {counts.get('CITED', 0)} |",
        f"| KEYWORD | the figure appears in a section carrying the node's subject words | {counts.get('KEYWORD', 0)} |",
        f"| LEAD | the figure appears somewhere, with nothing to tie it to this node | {counts.get('LEAD', 0)} |",
        f"| NOT FOUND | the figure does not appear in the harvested text at all | {counts.get('NOT FOUND', 0)} |",
        "",
        "**A CITED verdict is evidence, not a decision.** Read the quoted Bangla before",
        "flipping any node to `verified = true`; a figure can appear in the right section",
        "and still be the wrong limb of it.",
        "",
    ]
    for grade in ("CITED", "KEYWORD", "LEAD", "NOT FOUND"):
        group = [r for r in results if r["verdict"] == grade]
        if not group:
            continue
        lines += [f"## {grade} ({len(group)})", ""]
        for r in group:
            node = r["node"]
            lines.append(f"### `{node['key']}`")
            lines.append("")
            lines.append(f"- **Value:** `{node['value']}` {node['unit']} — currently *{node['state']}*")
            lines.append(f"- **Label:** {node['label_bn']} / {node['label_en']}")
            if r["cites"]:
                lines.append(f"- **Note cites:** {', '.join(r['cites'])}")
            lines.append(f"- **Searched for:** {', '.join('`' + f + '`' for f in r['forms']) or '_no form generated_'}")
            for f in r["findings"][:3]:
                lines.append(f"- **{f['grade']}** — {f['act']} s.{f['section'] or '?'} · [{f['title'][:70]}]({f['url']})")
                if f["keyword"]:
                    lines.append(f"  - matched subject word `{f['keyword']}`")
                lines.append(f"  - > …{f['quote']}…")
            if not r["findings"]:
                lines.append("- _No occurrence in the harvested corpus._")
            lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reconcile.py", description=__doc__.split("\n")[0])
    parser.add_argument("--corpus-dir", required=True, help="directory of <act>.json harvests")
    parser.add_argument("--out", help="write the review queue here")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    corpus = load_corpus(sorted(Path(args.corpus_dir).glob("*.json")))
    if not corpus:
        print(f"error: no corpus in {args.corpus_dir} — run tools/lawcorpus.py first", file=sys.stderr)
        return 2
    nodes = load_nodes()
    results = [reconcile(n, corpus) for n in nodes]

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=1))
        return 0

    report = render(results)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"corpus: {len(corpus)} sections · nodes: {len(nodes)} · written: {args.out}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
