# tools/ — reading the primary law

Research tooling. **Not** part of the shipped engine and not in any bundle; nothing
in `src/` imports it. Standard library only, like everything else here — CI refuses
a dependency declaration anywhere in the repo (spec 4.1).

## Why this exists

Every unverified node in `src/data/rates-AY2026-27.toml` blamed one obstacle:

> the Finance Act 2026 gazette PDF is typeset in a legacy Bijoy-family Bangla font
> whose glyphs map to ASCII, so its Schedules could not be text-extracted

That is true, and it is not a reason the figures are unreadable. Three things turned
out to be so:

1. **bdlaws serves the consolidated statutes as Unicode Bangla, one page per section** —
   ITA 2023, the VAT & SD Act 2012 and the Finance Act 2026 itself. No OCR needed, and
   the amendment footnotes come with it, which is what dates a figure.
2. **The gazette is hotlink-protected, not missing.** A plain GET returns 403; with a
   browser `User-Agent` *and* a `Referer` it returns 200.
3. **The gazette's body defeats text extraction for a different reason than assumed.**
   The masthead is SutonnyMJ and extracts as recoverable Bijoy ASCII, but the body is
   set in **Nikosh — a Unicode font — declared `WinAnsi`**, so pdftotext drops the
   glyphs entirely. No transliteration map can rescue that; the character codes are
   gone. OCR can, because the glyphs are still on the page.

## The tools

| | |
| :--- | :--- |
| `lawcorpus.py` | Harvest bdlaws into a local corpus. `python3 tools/lawcorpus.py ita2023 --out ita.json` |
| `gazette.py` | Download and OCR the Finance Act 2026 gazette. `python3 tools/gazette.py --pages 142` |
| `bnnum.py` | Bangla numerals as statutes write them — `৭,৫০,০০০`, `সাত লক্ষ`, `১০ শতাংশ` |
| `reconcile.py` | Every unverified node against the corpus, with the Bangla quoted |

`gazette.py` needs poppler (`pdftoppm`) and tesseract; it fetches `ben.traineddata`
itself on first use. Both tools cache under `.lawcache/` (gitignored), so a re-run
costs nothing and bdlaws is asked for each page once.

## Reading the output

`reconcile.py` grades evidence, and the grades mean what they say:

- **CITED** — the figure appears in the very section the node's note names, *in the
  right Act*. ITA 2023 s.78 is the investment rebate and VAT Act s.78 is the VAT
  authority; an early version of this tool matched section numbers across Acts and
  "confirmed" a rebate rate from an administrative clause. Citations are bound to
  their Act now.
- **KEYWORD** — the figure is in a section carrying the node's subject words. Support,
  never proof.
- **LEAD** / **NOT FOUND** — a coincidence, or nothing.

**No grade is a decision.** A figure can appear in the right section and still be the
wrong limb of it. Read the quoted Bangla, then land the node by hand under the
evidence standard in `CONTRIBUTING.md`. The output of an OCR pass is evidence to read,
never a figure to ship unseen.

## What this cannot reach

bdlaws exposes the Finance Act's 179 amending **sections** but not its **তফসিল-২**,
where the slab, surcharge, rebate and corporate rate tables live. Those come only from
the gazette, via `gazette.py`. Use `--psm 4` at 450 dpi: the rate tables are two
columns and lower settings drop the rate column silently. One systematic OCR confusion
is corrected in code — Bengali ৪ reads as ASCII `8` — and only inside a Bengali numeral
run, so a real `8` is left alone.
