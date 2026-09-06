<!--
TakaBooks pull request — Moshiur Rahman (@bemoshiur) · TICON SYSTEM LTD — https://ticonsys.com
Keep what applies, delete what does not. The checklist is what CI and the reviewer will
look for; ticking it honestly saves a round-trip.
-->

## What this changes

<!-- One paragraph: the problem, the change, and why this way. Link the issue: "Closes #123". -->

## Type

- [ ] Engine (`src/engine/`)
- [ ] Rates data (`src/data/rates-AY<year>.toml`)
- [ ] Reference material (`src/core/`, `src/references/`)
- [ ] Templates (`src/templates/`)
- [ ] Build / bundles / installer (`build/`, `bin/`, `.github/`)
- [ ] Tests only
- [ ] Docs only

## Checklist — every PR

- [ ] `python3 -m unittest discover tests` passes locally (stdlib only, Python 3.11+).
- [ ] `python3 build/build.py --check` passes — every bundle still builds and the ChatGPT
      8,000-character instruction cap holds.
- [ ] **Standard library only.** No `pip install`, no new import outside the stdlib, no
      `requirements.txt` (CI refuses them).
- [ ] **Money is `int` paisa.** No `float` touches an amount; text is parsed with
      `decimal.Decimal`; rounding is `ROUND_HALF_UP`, once, at the end.
- [ ] **No tax figure in prose or code.** Every rate, threshold, deadline and section number
      is read from `rates-AY<year>.toml`. Nothing new is hardcoded.
- [ ] Bangla / English term pairs kept wherever a statutory term appears
      (মূসক / VAT, উৎসে কর কর্তন / TDS, খতিয়ান / ledger).
- [ ] Any script that could emit an unbalanced entry or an unreconciled figure exits
      non-zero with a clear message — no silent correction.
- [ ] Attribution to Moshiur Rahman (@bemoshiur) and TICON SYSTEM LTD is intact in anything
      generated or bundled.
- [ ] `CHANGELOG.md` updated if a user would notice the change.

## Checklist — tax content (rates, thresholds, deadlines, forms, sections)

<!-- Delete this section if the PR touches no tax content. -->

- [ ] Assessment year / করবর্ষ stated: `____-__`
- [ ] Statute / SRO / NBR circular reference: `________`
- [ ] Primary source URL recorded in the rates node's `source` field: `https://…`
- [ ] `as_of` set to the date the source was read.
- [ ] `verified = true` **only** because the primary text was read; otherwise
      `verified = false` and the note says what could not be confirmed.
- [ ] The prose agrees with the data: `src/references/*.md` and
      `src/references/compliance-calendar.md` updated to match.
- [ ] Golden test cases in `tests/` updated, each citing its rates source.
- [ ] No real TIN, BIN, return or bank data anywhere in the diff.

## How to verify

<!-- Commands a reviewer can run, and what they should see. Fake amounts only. -->

```bash
python3 -m unittest discover tests
python3 build/build.py --check
```

## Notes for the reviewer

<!-- Trade-offs, things you were unsure about, follow-ups you deliberately left out. -->

---

TakaBooks is not professional advice. Verify every figure with a licensed ITP or CA before filing.
