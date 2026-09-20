#!/usr/bin/env python3
"""TakaBooks — harvest Bangladesh primary law from bdlaws.minlaw.gov.bd.

WHY THIS EXISTS.  ``src/data/rates-AY2026-27.toml`` carries 53 nodes marked
``verified = false``.  Their notes say, almost uniformly, that the figure could
not be read from enacted text because the Finance Act 2026 gazette PDF is
typeset in a legacy Bijoy-family Bangla font whose glyphs map to ASCII.

That is true of the PDF.  It is not true of the law.  bdlaws serves the
consolidated statutes as **Unicode Bangla, one page per section**:

    আয়কর আইন, ২০২৩        act-1429    (ITA 2023)
    মূসক ও সম্পূরক শুল্ক আইন, ২০১২  act-1106    (VAT & SD Act 2012)
    অর্থ আইন, ২০২৬          act-1725    (Finance Act 2026, Act 96 of 2026)

so the operative text can simply be read.  This module fetches it, caches it,
and turns it into plain text an evidence check can quote.

WHAT IT DOES NOT SOLVE.  bdlaws exposes the Finance Act's amending *sections*
but not its তফসিল-২ / Schedule 2, where the slab, surcharge and rebate tables
live.  Nodes governed only by Schedule 2 cannot be settled from here; see
``tools/README.md``.

Standard library only, like everything else in this repository — CI refuses any
dependency declaration (spec 4.1), and that applies to research tooling too.
Pages are cached under ``.lawcache/`` (gitignored) so a re-run costs nothing
and bdlaws is asked for each page at most once.
"""

from __future__ import annotations

import argparse
import html
import http.client
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".lawcache"
BASE = "http://bdlaws.minlaw.gov.bd"

#: The acts a TakaBooks figure can be governed by, and how the rates file names them.
ACTS: dict[str, dict[str, str]] = {
    "ita2023": {"id": "act-1429", "bn": "আয়কর আইন, ২০২৩", "en": "Income Tax Act 2023"},
    "vat2012": {"id": "act-1106", "bn": "মূল্য সংযোজন কর ও সম্পূরক শুল্ক আইন, ২০১২",
                "en": "VAT and Supplementary Duty Act 2012"},
    "fa2026": {"id": "act-1725", "bn": "অর্থ আইন, ২০২৬", "en": "Finance Act 2026"},
}

USER_AGENT = "TakaBooks-research/1.1 (+https://github.com/bemoshiur/TakaBooks)"
DELAY_SECONDS = 0.7   # be a polite guest on a government server
MAX_ATTEMPTS = 4
BACKOFF_SECONDS = 3.0


# --------------------------------------------------------------------------------------
# Fetching and decoding
# --------------------------------------------------------------------------------------

def _cache_path(url: str) -> Path:
    slug = re.sub(r"[^A-Za-z0-9._-]", "_", url.replace(BASE, "").strip("/")) or "index"
    return CACHE / f"{slug}.html"


def fetch(url: str, *, refresh: bool = False) -> bytes:
    """GET ``url``, caching the raw bytes.  Decoding is a separate problem."""
    if not url.startswith("http"):
        url = BASE + url
    path = _cache_path(url)
    if path.exists() and not refresh:
        return path.read_bytes()
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    # bdlaws closes connections mid-harvest under sustained load. A 500-page run
    # WILL hit it, so retry with backoff rather than losing the whole harvest —
    # and keep the per-page cache, which makes any re-run resume for free.
    last: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read()
            break
        except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
            last = exc
            if attempt == MAX_ATTEMPTS - 1:
                raise
            time.sleep(BACKOFF_SECONDS * (attempt + 1))
    else:  # pragma: no cover — the loop either breaks or raises
        raise last  # type: ignore[misc]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    time.sleep(DELAY_SECONDS)
    return raw


def decode(raw: bytes) -> str:
    """bdlaws serves UTF-16 with a BOM on some pages and UTF-8 on others.

    Guessing wrong is silent: UTF-16 text read as UTF-8 yields a string with no
    Bengali codepoints at all, which reads as "this page has no Bangla" rather
    than as an error.  That cost an hour once; hence the explicit BOM check.
    """
    if raw[:2] in (b"\xfe\xff", b"\xff\xfe"):
        return raw.decode("utf-16", errors="replace")
    return raw.decode("utf-8", errors="replace")


_TAG = re.compile(r"<[^>]+>")
_DROP = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
#: bdlaws wraps every page in the same chrome; none of it is law.
_CHROME = (
    "Toggle navigation", "Home", "Laws of Bangladesh", "Chronological Index",
    "Alphabetical Index", "Law Search", "Related Links", "Contact Us/Feedback",
    "Old Website", "Help", "How to Search", "How to Print", "Glossary",
    "Roman Number", "বাংলা | English", "প্রিন্ট ভিউ", "[সেকশন সূচি]",
    "Copyright", "Legislative and Parliamentary", "Ministry of Law",
    "Bangladesh Government Official Web Site",
)


def to_text(raw: bytes) -> str:
    """HTML -> the visible text, with the site chrome removed."""
    s = decode(raw)
    s = _DROP.sub(" ", s)
    s = re.sub(r"</(p|div|tr|li|h[1-6])>", "\n", s, flags=re.I)
    s = re.sub(r"</t[dh]>", " │ ", s, flags=re.I)
    s = _TAG.sub(" ", s)
    s = html.unescape(s)
    s = unicodedata.normalize("NFC", s)
    lines = []
    for line in s.split("\n"):
        line = re.sub(r"[ \t ]+", " ", line).strip()
        if not line or any(line.startswith(c) or line == c for c in _CHROME):
            continue
        lines.append(line)
    return "\n".join(lines)


def title_of(raw: bytes) -> str:
    m = re.search(r"<title>([^<]*)</title>", decode(raw))
    return html.unescape(m.group(1)).strip() if m else ""


# --------------------------------------------------------------------------------------
# Walking an act
# --------------------------------------------------------------------------------------

def sections(act_key: str, *, refresh: bool = False) -> list[dict[str, str]]:
    """Every section page of an act, as ``{url, title}``, in the order listed."""
    act = ACTS[act_key]
    raw = fetch(f"/{act['id']}.html", refresh=refresh)
    page = decode(raw)
    pattern = rf'href="(/{act["id"]}/section-\d+\.html)"[^>]*>\s*([^<]{{1,200}}?)\s*<'
    found: list[dict[str, str]] = []
    seen: set[str] = set()
    for url, title in re.findall(pattern, page):
        if url in seen:
            continue
        seen.add(url)
        found.append({"url": url, "title": html.unescape(title).strip()})
    return found


def harvest(act_key: str, *, refresh: bool = False, limit: int | None = None) -> list[dict]:
    """Fetch every section of an act and return it as text with its citation."""
    out: list[dict] = []
    failures: list[str] = []
    listing = sections(act_key, refresh=refresh)
    if limit:
        listing = listing[:limit]
    for n, entry in enumerate(listing, 1):
        try:
            raw = fetch(entry["url"], refresh=refresh)
        except Exception as exc:               # noqa: BLE001 — one bad page is not a failed harvest
            print(f"  !! {entry['url']}: {exc}", file=sys.stderr)
            failures.append(entry["url"])
            continue
        text = to_text(raw)
        if "<title>404" in decode(raw)[:400] or len(text) < 40:
            continue
        out.append({
            "act": act_key,
            "act_bn": ACTS[act_key]["bn"],
            "url": BASE + entry["url"],
            "title": entry["title"],
            "section": _section_number(entry["title"]),
            "text": text,
        })
        if n % 25 == 0:
            print(f"  … {act_key}: {n}/{len(listing)}", file=sys.stderr)
    if failures:
        print(f"  !! {act_key}: {len(failures)} page(s) could not be fetched", file=sys.stderr)
    return out


_BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


def _section_number(title: str) -> str:
    """'৬৪। দাখিলপত্র পেশ' -> '64'.  Returns '' when the title carries no number."""
    m = re.match(r"\s*([০-৯0-9]+[ক-ৎA-Za-z]*)\s*।", title)
    return m.group(1).translate(_BN_DIGITS) if m else ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lawcorpus.py",
        description="Harvest Bangladesh primary law from bdlaws as Unicode Bangla text.",
    )
    parser.add_argument("act", nargs="?", choices=sorted(ACTS), help="which act to harvest")
    parser.add_argument("--list", action="store_true", help="list the acts this tool knows")
    parser.add_argument("--toc", action="store_true", help="list an act's sections, do not fetch them")
    parser.add_argument("--limit", type=int, default=None, help="stop after N sections")
    parser.add_argument("--refresh", action="store_true", help="ignore the cache")
    parser.add_argument("--out", metavar="PATH", help="write the harvest as JSON")
    args = parser.parse_args(argv)

    if args.list or not args.act:
        print("Acts available:")
        for key, act in sorted(ACTS.items()):
            print(f"  {key:<9} {act['id']:<10} {act['bn']}  ({act['en']})")
        print(f"\nCache: {CACHE}")
        return 0

    if args.toc:
        listing = sections(args.act, refresh=args.refresh)
        print(f"{ACTS[args.act]['bn']} — {len(listing)} sections")
        for entry in listing[: args.limit or len(listing)]:
            print(f"  {_section_number(entry['title']) or '—':>6}  {entry['title'][:88]}")
        return 0

    corpus = harvest(args.act, refresh=args.refresh, limit=args.limit)
    chars = sum(len(c["text"]) for c in corpus)
    print(f"{ACTS[args.act]['bn']}: {len(corpus)} sections, {chars:,} characters")
    if args.out:
        Path(args.out).write_text(
            json.dumps(corpus, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"written: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
