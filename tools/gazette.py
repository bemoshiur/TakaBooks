#!/usr/bin/env python3
"""TakaBooks — read the Finance Act 2026 gazette that "could not be text-extracted".

THE PROBLEM, AND WHY THE OLD ANSWER WAS HALF RIGHT.  Every unverified node in
``src/data/rates-AY2026-27.toml`` blames the same obstacle: the Finance Act 2026
gazette PDF is typeset in a legacy Bijoy-family Bangla font whose glyphs map to
ASCII, so its Schedules could not be read.  Both halves of that are true of
*text extraction* and neither is a reason the figures are unreadable:

  - The masthead is set in SutonnyMJ and extracts as Bijoy ASCII
    (``evsjv‡`k †M‡RU`` is বাংলাদেশ গেজেট), which a transliteration map recovers.
  - The BODY is set in Nikosh — a Unicode font — but declared ``WinAnsi``, so
    pdftotext drops most glyphs entirely and returns fragments. No
    transliteration can rescue that: the character codes are gone.

So the text layer is a dead end for the Schedules, and OCR is not.  The glyphs
are on the page; rendering and reading them recovers the tables outright.

WHAT THIS DOES.  Downloads the gazette (it is hotlink-protected — a plain GET
returns 403, so a Referer is required), renders a page range at 450 dpi and OCRs
it with tesseract's Bengali model in ``--psm 4``, which is what holds the rate
tables' two columns together.

ACCURACY.  Verified against the AY 2026-27 slab ladder on page 142, which this
recovers exactly as the rates file and the golden tests hold it: ৪,০০,০০০ nil,
then ৩,০০,০০০ at ১০%, ৪,০০,০০০ at ১৫%, ৫,০০,০০০ at ২০%, ২০,০০,০০০ at ২৫%,
balance at ৩০%.  One systematic confusion is known and corrected below: Bengali
৪ is read as ASCII ``8``.  OCR output is EVIDENCE TO READ, never a figure to
land unseen.

Requires: poppler (pdftoppm) and tesseract with ben.traineddata.  No Python
dependencies — CI refuses them (spec 4.1).
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".lawcache" / "gazette"
GAZETTE_URL = "https://nbr.gov.bd/uploads/acts/Finance_Act_2026.pdf"
REFERER = "https://nbr.gov.bd/"
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0 Safari/537.36"
)
DPI = 450
PSM = "4"

#: Bengali ৪ (U+09EA) and ASCII 8 are near-identical at this weight, and
#: tesseract prefers the ASCII. Inside a Bengali numeral run it is always ৪ —
#: "8,০০,০০০" is ৪,০০,০০০, never eight lakh. Fixed only where a Bengali digit
#: or a Bengali comma-group sits adjacent, so a real ASCII 8 is left alone.
_EIGHT_IN_BENGALI = re.compile(r"(?<=[০-৯,])8|8(?=[০-৯])|(?<![0-9A-Za-z])8(?=,[০-৯])")


def repair(text: str) -> str:
    """Correct the one systematic OCR confusion, and nothing else."""
    return _EIGHT_IN_BENGALI.sub("৪", text)


def need(binary: str) -> str:
    path = shutil.which(binary)
    if not path:
        raise SystemExit(
            f"error: {binary} is not installed.\n"
            f"  hint: brew install {'poppler' if binary.startswith('pdf') else 'tesseract'}"
        )
    return path


def tessdata() -> Path:
    """Where ben.traineddata lives; downloaded on first use."""
    target = CACHE / "tessdata"
    blob = target / "ben.traineddata"
    if not blob.exists():
        target.mkdir(parents=True, exist_ok=True)
        url = ("https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/"
               "main/ben.traineddata")
        print(f"  fetching Bengali OCR model → {blob}", file=sys.stderr)
        with urllib.request.urlopen(url, timeout=300) as response:
            blob.write_bytes(response.read())
    return target


def download(refresh: bool = False) -> Path:
    """The gazette PDF.  403s without a browser User-Agent AND a Referer."""
    CACHE.mkdir(parents=True, exist_ok=True)
    pdf = CACHE / "Finance_Act_2026.pdf"
    if pdf.exists() and not refresh:
        return pdf
    request = urllib.request.Request(
        GAZETTE_URL, headers={"User-Agent": BROWSER_UA, "Referer": REFERER}
    )
    print(f"  downloading {GAZETTE_URL}", file=sys.stderr)
    with urllib.request.urlopen(request, timeout=300) as response:
        pdf.write_bytes(response.read())
    return pdf


def ocr_pages(first: int, last: int, *, refresh: bool = False) -> dict[int, str]:
    """Render and read pages ``first``..``last`` inclusive."""
    need("pdftoppm")
    need("tesseract")
    pdf = download(refresh=refresh)
    images = CACHE / "pages"
    images.mkdir(parents=True, exist_ok=True)
    env_prefix = str(tessdata())

    out: dict[int, str] = {}
    for page in range(first, last + 1):
        cached = CACHE / f"page-{page:03d}.txt"
        if cached.exists() and not refresh:
            out[page] = cached.read_text(encoding="utf-8")
            continue
        stem = images / f"p{page:03d}"
        subprocess.run(
            [need("pdftoppm"), "-r", str(DPI), "-png", "-f", str(page), "-l", str(page),
             str(pdf), str(stem)],
            check=True, capture_output=True,
        )
        rendered = sorted(images.glob(f"p{page:03d}*.png"))
        if not rendered:
            continue
        result = subprocess.run(
            [need("tesseract"), str(rendered[0]), "-", "-l", "ben", "--psm", PSM],
            check=True, capture_output=True, text=True,
            env={"TESSDATA_PREFIX": env_prefix, "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"},
        )
        text = repair(result.stdout)
        cached.write_text(text, encoding="utf-8")
        out[page] = text
        print(f"  page {page} read ({len(text):,} chars)", file=sys.stderr)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gazette.py", description=__doc__.split("\n")[0])
    parser.add_argument("--pages", default="140-152", help="page range, e.g. 142 or 139-151")
    parser.add_argument("--grep", help="print only lines containing this text")
    parser.add_argument("--out", help="write the pages here as one file")
    parser.add_argument("--refresh", action="store_true", help="ignore the cache")
    args = parser.parse_args(argv)

    m = re.fullmatch(r"(\d+)(?:-(\d+))?", args.pages.strip())
    if not m:
        print("error: --pages must be N or N-M", file=sys.stderr)
        return 2
    first = int(m.group(1))
    last = int(m.group(2) or m.group(1))

    pages = ocr_pages(first, last, refresh=args.refresh)
    chunks = []
    for page in sorted(pages):
        body = pages[page]
        if args.grep:
            body = "\n".join(l for l in body.split("\n") if args.grep in l)
            if not body.strip():
                continue
        chunks.append(f"\n=============== gazette page {page} ===============\n{body}")
    text = "\n".join(chunks)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"written: {args.out} ({len(pages)} pages)")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
