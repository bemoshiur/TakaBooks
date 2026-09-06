# Contributing to TakaBooks — টাকাবুকস-এ অবদান রাখা

Thank you for helping. TakaBooks is a portable, LLM-agnostic bookkeeping and taxation
package for Bangladesh, maintained by Moshiur Rahman ([@bemoshiur](https://github.com/bemoshiur))
at [Ticon Sys](https://ticonsys.com) and released under the MIT license.

Two things make this project different from most open-source repositories, and both shape
how contributions are reviewed:

1. **Its output can end up in a return filed with the National Board of Revenue (NBR /
   জাতীয় রাজস্ব বোর্ড).** A wrong number here is worse than a missing one.
2. **The LLM never does arithmetic.** Deterministic Python owns every figure; the model owns
   classification and explanation. Anything that would let a model "help" with a number is
   a bug, not a feature.

Please read [`docs/superpowers/specs/2026-09-05-takabooks-design.md`](docs/superpowers/specs/2026-09-05-takabooks-design.md)
before a substantial change. It is the binding design contract; pull requests that redesign
it will be asked to become a design discussion first.

---

## The contribution we value most: a verified tax-rule update

Bangladesh changes its tax rules every year — the annual **অর্থ আইন / Finance Act**, then a
stream of **প্রজ্ঞাপন / এসআরও (SRO)** gazette notifications, and NBR's explanatory
**আয়কর পরিপত্র / income tax paripatra**. TakaBooks is only useful while its figures track
those instruments. Keeping them current is the single most valuable thing you can do for
every user of this project, and it needs no Python at all.

The rule that governs this work has no exceptions:

> **Never invent a Bangladeshi tax rate, threshold, deadline or statute number.** A figure
> that could not be confirmed from a primary source is recorded as `verified = false` and
> every consumer surfaces that caveat. *Absent beats wrong.*

### The evidence standard

A rate-rule pull request (or a [**Tax rule update / কর বিধি হালনাগাদ**
issue](https://github.com/bemoshiur/TakaBooks/issues/new?template=tax-rule-update.yml) if you
would rather not edit TOML) must carry **all** of the following. A reviewer will
open your source and read the figure themselves before merging; make that easy.

| Required | What it means | Example of what satisfies it |
|---|---|---|
| **Primary source URL** | The instrument itself, published by the authority that issued it | A page or PDF on `nbr.gov.bd` (Finance Act, SRO, paripatra, form), the Act text on `bdlaws.minlaw.gov.bd`, or the *Bangladesh Gazette* |
| **Statute / SRO / paripatra reference** | Exactly where in that source the figure appears | Act name + section (ধারা) + schedule/paragraph; SRO number and date; paripatra paragraph or page |
| **Assessment year (করবর্ষ)** | Which AY the figure applies to, and from which date | "AY 2026-27, effective 1 July 2026" |
| **Old value → new value** | What TakaBooks says now and what the source says | `value = 0` (placeholder) → the figure as printed in the source, with its unit |
| **Date you read the source** | Goes into `as_of` | ISO date, `YYYY-MM-DD` |
| **Every condition attached** | Who it applies to, exemptions, caps, interactions | Goes into `note` (and `condition` where the node has one) |

**Acceptable only as a cross-check, never as the sole source:** newspaper reports, blog
posts, practitioner or Big-4 summaries, slide decks, and anything an LLM told you. The
research pass in [`docs/research/`](docs/research/) records how secondary summaries were
used to triangulate when a primary PDF was unreadable — and lists every figure that could
not be confirmed under **UNVERIFIED / CONFLICTING**. Follow the same discipline.

**Budget-day numbers are a known trap.** The Finance *Bill* presented in June and the
Finance *Act* passed by Parliament can differ. Cite the enacted Act or the gazette, never
the bill or the budget-speech coverage.

### Where the figure lives

Every rate, threshold, deadline and policy switch lives in exactly one place:
[`src/data/rates-AY2026-27.toml`](src/data/rates-AY2026-27.toml) (one file per assessment
year). No rate is ever written into Python or into prose. A rate node looks like this:

```toml
[income_tax.individual.thresholds.general]
label_en = "General taxpayer"
label_bn = "সাধারণ করদাতা"
value = <figure as printed in the source>   # whole taka as an integer; decimals as a quoted string
unit = "BDT"                                # "percent" | "BDT" | "date" | "policy" | "count"
source = "<exact URL of the primary source>"
as_of = "<YYYY-MM-DD you read it>"
verified = true                             # only after you read it in the primary source
note = "<what the figure covers and every condition attached>"
```

To land a figure, follow the procedure printed at the top of the rates file:

1. Replace `value` with the figure read from the primary source.
2. Replace `source` with the exact URL of that source.
3. Set `as_of` to the ISO date on which you read it.
4. Set `verified = true` and **delete** the `placeholder = true` line.
5. Rewrite `note` to say exactly what the figure covers and every condition attached.

If you could not confirm it from a primary source, leave `verified = false`, say so in
`note`, and stop. A figure nobody checked must never look checked.

Format rules that `src/engine/rates.py` enforces (a PR that breaks them fails the tests):

- Money is in **taka**, never paisa: whole taka as an integer (`400000`), anything with
  decimals as a **quoted string** (`"400000.50"`).
- Percentages are **percent**, never fractions: `15` means 15 %. Above 100 in a
  `unit = "percent"` node is rejected as a fraction/percent mix-up.
- **Never write a bare TOML float.** `7.5` becomes a binary float and TakaBooks refuses to
  do money arithmetic with floats. Write `"7.5"`.
- Extra descriptive keys (`label_en`, `label_bn`, `condition`, `applies_to`, …) are welcome
  and are preserved for display.

### The prose must move with the number

Spec §6 requires every rate, threshold and deadline in the reference material to carry a
source URL and a "current as of" date. When you change a node, update the matching passage
in `src/references/` (for example `income-tax.md`, `vat-mushak.md`,
`withholding-tds-vds.md`, `compliance-calendar.md`) **in the same pull request**, with the
same source and date. Keep the Bangla statutory term beside the English one — মূসক / VAT,
উৎসে কর কর্তন / TDS, খতিয়ান / ledger — so users can find the form on the NBR portal.

### A new assessment year

Updating TakaBooks for a new Finance Act is deliberately small (spec §4.5):

1. Copy `src/data/rates-AY<current>.toml` to `src/data/rates-AY<next>.toml`.
2. Land the new figures node by node, to the evidence standard above.
3. Add one entry to `src/references/compliance-calendar.md`.

No Python changes. If you find yourself editing the engine to land a rate, stop and open an
issue — that is a schema gap, and it is worth fixing properly.

### Rate PR checklist

Copy this into your pull request description and tick every line:

- [ ] Every changed node cites a **primary** source URL that I opened myself.
- [ ] The statute / SRO / paripatra reference and the assessment year are in the PR body.
- [ ] Old value → new value is stated for every node, with its unit.
- [ ] `as_of` is the date I read the source; `verified = true` only where I read it there.
- [ ] `placeholder = true` is deleted from every node I landed, and kept on every node I did not.
- [ ] The matching prose in `src/references/` changed in this PR, with the same source and date.
- [ ] `python3 -m unittest discover tests -v` and `python3 build/build.py --check --strict` pass.
- [ ] `CHANGELOG.md` has an entry naming the node key, old → new value, AY and source.

A rate change is merged only after a maintainer has personally opened the cited primary
source and read the figure. This is slow on purpose.

---

## Other ways to contribute

- **Engine bugs** — a wrong total, an entry that should have been refused, a report that
  does not tie back to the journal, a rounding that is not `ROUND_HALF_UP`. Open a
  [bug report](https://github.com/bemoshiur/TakaBooks/issues/new/choose) with the exact
  command, a minimal `books/` fixture and the output. A failing test is the best bug report.
- **Content clarity** — a reference passage that a small-business owner would misread, a
  missing Bangla term, an ambiguous form name. The Bangla ↔ English glossary in
  `src/references/glossary-bn-en.md` is a good place to start.
- **Bangla translations and Banglish phrasing** — the assistant replies in the user's
  language (spec §6.5). Native review of `label_bn` values and Bangla output strings is
  always welcome.
- **LLM-platform reports** — you tried the Claude, ChatGPT, Gemini or universal bundle and
  the model tried to compute a number, skipped the disclaimer, or invented a rate. Report
  it with the platform, the model, your prompt and the reply. These reports drive the
  behavioural counters in `src/core/10-workflow.md`.
- **Tests** — spec §7 lists what must be covered. More edge cases for lakh/crore
  formatting, tax tags, and period boundaries are welcome at any time.
- **Docs and wiki** — `docs/` is the wiki source and is mirrored to the GitHub Wiki. Edit
  `docs/`, not the wiki; wiki edits are overwritten on the next sync.

If you are unsure whether something is wanted, open an issue first. A short conversation
beats a large rejected PR.

---

## Development setup

### Requirements

- **Python 3.11 or newer** — the floor exists for `tomllib`, which is in the standard
  library from 3.11. Nothing older is supported, and the scripts fail fast with a clear
  message below it.
- **Nothing to install.** TakaBooks is standard-library only. There is no
  `requirements.txt`, and CI fails if one appears. Do not `pip install` anything to make a
  change work; if a change needs a third-party package, it is the wrong change.
- **Node.js 18 or newer** — only if you are working on the installer CLI
  (`bin/takabooks.mjs`). It also uses only Node built-ins.
- `git`.

### Get the code and run the tests

```bash
git clone https://github.com/bemoshiur/TakaBooks.git
cd TakaBooks

# The whole suite, verbose. This is exactly what CI runs.
python3 -m unittest discover tests -v

# Prove no third-party import crept in: run the suite inside an EMPTY virtualenv
# (no pip, no site-packages). CI does this on Python 3.11, 3.12 and 3.13.
python3 -m venv --without-pip .venv-clean
.venv-clean/bin/python -m unittest discover tests -v
```

### Build the bundles

```bash
# Assemble every target and verify every platform limit — writes nothing.
# Enforces the 8,000-character ChatGPT instruction cap (spec §5).
python3 build/build.py --check

# Same, but a missing expected source file is a failure. CI uses this on main;
# release.yml always uses it.
python3 build/build.py --check --strict

# The real build: writes dist/ and regenerates AGENTS.md at the repo root.
python3 build/build.py --target all --clean

# One target only.
python3 build/build.py --target chatgpt
```

`build.py` is deterministic: two consecutive builds must produce byte-identical `dist/`.
CI checks that. If your change makes the output depend on time, ordering of a `set`, or the
environment, CI will fail — sort, and stamp nothing that is not in `src/`.

`dist/` and the root `AGENTS.md` are **generated**. Never hand-edit them; edit `src/` and
rebuild. Do not commit `dist/` — release assets are built and attached by
`.github/workflows/release.yml`.

### Try the engine

```bash
python3 src/engine/init_books.py --books ./books --assessment-year 2026-27 --fiscal-year-start 07-01
python3 src/engine/post.py --books ./books --date 2026-07-01 --description "Owner capital" \
    --debit 1100=100000 --credit 3100=100000
python3 src/engine/validate.py --books ./books
python3 src/engine/report.py --books ./books --period 2026-07
python3 src/engine/vat.py --books ./books --period 2026-07
python3 src/engine/tax.py --books ./books --income 1000000 --list-options
```

Every script accepts `--help`, `--books <dir>` (default `./books`), `--json` and
`--version`, and exits non-zero on any integrity failure. Account codes above come from the
default chart in `src/templates/accounts.toml`; check `books/accounts.toml` for the chart you
actually have.

While `rates-AY2026-27.toml` still holds placeholder values, `tax.py` refuses to compute
unless you pass `--allow-placeholder-rates`, and then stamps every line
**PROVISIONAL / অস্থায়ী**. That is correct behaviour, not a bug. Nothing computed from a
placeholder may be filed with NBR.

### Installer CLI

```bash
node bin/takabooks.mjs list
node bin/takabooks.mjs install claude --dist dist --dest /tmp/takabooks-test --dry-run
```

---

## Coding rules

These are the hard contracts from spec §2 and §4. Pull requests that break one are not
merged, however good the rest is.

1. **Standard library only.** No third-party imports anywhere in `src/`, `build/` or
   `tests/`. Python floor 3.11.
2. **Money is `int` paisa, never `float`.** 1 BDT = 100 paisa. Parse text amounts with
   `decimal.Decimal`, convert to int paisa, and never let a `float` touch money. Round
   `ROUND_HALF_UP`, once, at the final step.
3. **Refuse, do not correct.** A script that would emit an unbalanced entry, an
   unreconciled report or an unknown account exits non-zero with a clear error. Silent
   correction is forbidden.
4. **No rate in code or prose.** Every figure comes from the assessment-year rates file
   through `src/engine/rates.py`, which has no `get(key, default)` on purpose. A missing
   rate is an error, never a default. Every consumer states which AY file it used and
   surfaces `verified = false` caveats.
5. **`src/` is the source of truth.** `dist/` and the root `AGENTS.md` are generated.
6. **Bangla beside English** wherever a statutory term appears.
7. **Every tax output ends with the disclaimer**: not professional advice; verify with a
   licensed Income Tax Practitioner (ITP) or Chartered Accountant (CA) before filing.
8. **Both display formats, lakh/crore by default**: `12,34,567.89` for users,
   `1,234,567.89` on request. Currency symbol `৳`; always state the unit.
9. **Journal CSV schema is fixed** (spec §4.3):
   `date,entry_id,description,account,debit,credit,party,doc_ref,tax_tag,memo`. `memo` is
   last so commas in it survive.
10. **Keep the core instruction small.** The ChatGPT 8,000-character cap on
    `src/core/` is the binding constraint for every platform; push detail into
    `src/references/`.

Style: readable over clever, docstrings on public functions, type hints where they help,
no formatter is mandated. Match the file you are in.

## Tests

`unittest`, standard library only, discovered from `tests/`. Add tests with every change:

- Engine: the double-entry invariants (unbalanced rejected; every report ties to the
  journal), Money edge cases (0, negatives, exactly `1,00,000`, crore boundaries), tax
  tags, validation failures (unknown account, duplicate `entry_id`, malformed date, bad
  `tax_tag`) — all must fail loudly.
- Tax and VAT: **golden cases with hand-checked expected values, each citing the rates
  source it was checked against.** A golden case whose expected value came from a
  spreadsheet nobody can reproduce is not a golden case.
- Build: every target emits; caps are enforced.

Green tests on Python 3.11, 3.12 and 3.13 are a merge precondition.

---

## Pull request process

1. **Open an issue first** for anything larger than a typo, unless it is a rate update with
   full evidence (those can go straight to a PR).
2. **Branch from `main`.** One concern per pull request: a rate update, an engine fix and a
   README rewrite are three PRs.
3. **Title the PR by area**, for example `rates: land AY 2026-27 general threshold`,
   `engine: reject duplicate entry_id across months`, `content: clarify Mushak 6.3
   wording`, `build: …`, `ci: …`, `docs: …`.
4. **Fill in the PR template.** For rate changes, include the checklist above.
5. **CI must be green**: unit tests on 3.11/3.12/3.13 in an empty venv, `build.py --check`,
   the determinism check and the installer matrix on Linux, macOS and Windows.
6. **Update `CHANGELOG.md`** under `Unreleased`. Every rate change names the node key,
   old → new value, assessment year and source URL, so the changelog is itself an audit
   trail.
7. **Review.** Expect questions. A rate change waits until a maintainer has opened the
   primary source. Engine changes are read for the money rules first.
8. PRs are squash-merged with the PR title as the commit subject.

By contributing you agree that your contribution is licensed under the
[MIT License](LICENSE) that covers the project, and you confirm that you have the right to
contribute it. Please do not paste text from a copyrighted commentary or a paid summary
into `src/references/`; cite the primary instrument in your own words.

---

## Reporting problems

- **A wrong tax figure** (rate, threshold, deadline, statute reference): open a public
  [**Tax rule update / কর বিধি হালনাগাদ**
  issue](https://github.com/bemoshiur/TakaBooks/issues/new?template=tax-rule-update.yml) with
  the evidence above. It is handled with the urgency of a security bug — see
  [`SECURITY.md`](SECURITY.md) for why it is deliberately public.
- **A security vulnerability**: report privately per [`SECURITY.md`](SECURITY.md).
- **Anything else**: a [bug report or feature request](https://github.com/bemoshiur/TakaBooks/issues/new/choose).

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md) in every project space.

---

## Maintainer notes: cutting a release

For the record, so that a release is reproducible by anyone with write access:

1. Confirm `main` is green on CI and `python3 build/build.py --check --strict` passes locally.
2. Move the `Unreleased` block in `CHANGELOG.md` under the new version and date; leave an
   empty `Unreleased` section; update the comparison links at the bottom.
3. Bump `__version__` in `src/engine/takabooks.py` and `version` / `date-released` in
   `CITATION.cff` to the same value. `package.json` stays at `0.0.0`; the publish workflow
   sets it from the tag.
4. Tag `vX.Y.Z` on `main` and push the tag. `release.yml` runs the suite, builds every
   bundle, and attaches the zips, the universal `.md` and `SHA256SUMS.txt` to a GitHub
   Release. `publish-packages.yml` publishes `@bemoshiur/takabooks` to GitHub Packages on
   the same tag push (it needs the `packages: write` permission in the workflow; manual
   publishing needs a classic PAT with `write:packages`).
5. A pre-release tag (`v1.1.0-rc.1`) is marked pre-release automatically.

One-time manual steps that **no API can perform** (documented so nobody wastes an
afternoon looking for one):

- **Social preview image** — repo → Settings → General → Social preview → upload
  `assets/social-preview.png` (1280 × 640 px, under 1 MB). There is no REST, GraphQL or
  `gh` route for this. The PNG is committed, so there is nothing to render first; regenerate
  it from `assets/social-preview.svg` only when the card changes, with the command in
  [`assets/README.md`](assets/README.md) — GitHub's uploader does not accept SVG.
- **Wiki** — the first wiki page must be created once in the web UI before
  [`.github/workflows/wiki-sync.yml`](.github/workflows/wiki-sync.yml) can mirror
  `docs/wiki/` to it; `<repo>.wiki.git` does not exist until a page has been saved, and no
  token or Action can create it. The workflow detects this and prints the click path rather
  than failing with git's "repository not found". Restrict wiki editing to collaborators at
  the same time, since each sync replaces the wiki's working tree and would wipe manual edits.
- **Private vulnerability reporting** — repo → Settings → Code security → enable *Private
  vulnerability reporting*, otherwise the private route in `SECURITY.md` is not reachable.
- **Repository description, homepage and topics** — can be set with `gh repo edit`.

---

Maintained by **Moshiur Rahman** ([@bemoshiur](https://github.com/bemoshiur)) ·
**Ticon Sys** — https://ticonsys.com · MIT licensed.
