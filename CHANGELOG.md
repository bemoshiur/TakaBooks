# Changelog

All notable changes to TakaBooks are recorded in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

TakaBooks — Moshiur Rahman ([@bemoshiur](https://github.com/bemoshiur)) ·
TICON SYSTEM LTD — https://ticonsys.com

## How versions and rate changes are recorded

- **MAJOR** — a change that breaks the journal CSV schema, the `accounts.toml` /
  `config.toml` / rates TOML schema, a script's exit-code contract, or a bundle's layout.
- **MINOR** — a new assessment-year rates file, a new engine capability, a new build target,
  new reference material.
- **PATCH** — a corrected figure, a bug fix, a documentation fix.

**Every change to a tax figure is listed here individually**, naming the rates node key,
the old and new value, the assessment year (করবর্ষ) and the primary source URL. A corrected
figure goes under **Fixed** (or **Security** when the wrong figure could have led to a
material misfiling); a newly verified figure goes under **Added**; a figure that changed
because the law changed goes under **Changed**. The changelog is therefore an audit trail,
not only a release note.

## [Unreleased]

### Added

- **`tools/` — the primary law is readable after all.** Every unverified node blamed the
  Finance Act 2026 gazette being typeset in a legacy Bijoy font that "could not be
  text-extracted". Three things turned out to be so: bdlaws serves ITA 2023, the VAT & SD
  Act 2012 **and the Finance Act 2026 itself** as Unicode Bangla, one page per section,
  amendment footnotes included; the gazette is hotlink-protected (403 without a Referer),
  not missing; and its body defeats extraction for a different reason than assumed — it is
  set in **Nikosh, a Unicode font, declared `WinAnsi`**, so the character codes are gone
  and no transliteration map could ever have recovered them. OCR can, because the glyphs
  are still on the page.
  - `lawcorpus.py` harvests bdlaws (681 sections, ~3 MB of Bangla) with retry and caching.
  - `gazette.py` downloads and OCRs the gazette at 450 dpi, `--psm 4` — which is what holds
    the two-column rate tables together. Corrects one systematic confusion, Bengali ৪ read
    as ASCII `8`, only inside a Bengali numeral run.
  - `bnnum.py` renders a figure the way a statute writes it — `৭,৫০,০০০`, `সাত লক্ষ`, `১০ শতাংশ`.
  - `reconcile.py` puts every unverified node against the corpus and quotes the Bangla.
  - `docs/research/unverified-vs-primary-law.md` — the resulting review queue.
  - Verified end to end against the AY 2026-27 slab ladder on gazette page 142, which the
    pipeline recovers exactly as the rates file and the golden tests hold it: ৪,০০,০০০ nil,
    then ৩,০০,০০০ at ১০%, ৪,০০,০০০ at ১৫%, ৫,০০,০০০ at ২০%, ২০,০০,০০০ at ২৫%, balance at ৩০%.

### Changed

- **`income_tax.individual.environmental_surcharge.exempt_car_rule` — UNCONFIRMED → CONFIRMED.**
  Which car is exempt could not be established: NBR's Paripatra 2026-27 §1.7 says only "each
  car in excess of one". The Act says which. Finance Act 2026, তফসিল-২ তৃতীয় অংশ, proviso (ক):
  *"একাধিক গাড়ির ক্ষেত্রে যে গাড়ির উপর সর্বনিম্ন হারে পরিবেশ সারচার্জ আরোপিত হইবে উক্ত গাড়ি ব্যতীত
  অন্যান্য গাড়ির বিপরীতে পরিবেশ সারচার্জ পরিশোধ করিতে হইবে"* — the exempt car is the one
  attracting the lowest surcharge, which is the reading `tax.py` already applies. Read from
  the gazette by OCR. `tax.py` now states the rule and cites the Schedule instead of warning
  that it is a guess, and no longer blocks `--strict` over it.
  - Two further provisos recorded on the same node: `motor_car_definition` — "মোটর গাড়ি"
    EXCLUDES buses, minibuses, coasters, prime movers, trucks, lorries, tank lorries, pickup
    vans, human haulers, autorickshaws and motorcycles (proviso (ছ)), so a commercial fleet
    attracts none of this charge; and `collection_point` — it is collected at source on
    registration or fitness renewal, and is neither refundable nor adjustable (provisos (খ), (চ)).

### Fixed

- **Three investment-rebate nodes landed from enacted text** — `income_tax.individual.rebate.rate`,
  `.income_cap_percent` and `.absolute_cap`, all `verified = false` since 1.0.0, now
  `verified = true` against ITA 2023 s.78 as consolidated on bdlaws
  (<http://bdlaws.minlaw.gov.bd/act-1429/section-51908.html>): *"(ক) ০.০৩ × ‘ক’; বা (খ) [০.১০] × ‘খ’;
  বা (গ) [৭.৫০ (সাত দশমিক পাঁচ শূন্য)] লক্ষ টাকা, এই তিনটির মধ্যে যাহা কম"*. The section's own
  footnotes date both changes: ০.১০ replaced ০.১৫, and ৭.৫০ replaced ১০ (দশ), by Finance Act
  2026 s.61, effective 1 July 2026. **No value changed** — the three professional summaries the
  nodes rested on were right, and the figures no longer rest on them. Census: 530 nodes, 477
  verified, 50 unverified, 3 placeholder.
  - The two derived nodes stay derived and stay labelled as such: the statute caps the
    *rebate* at 3% of income and Tk 750,000, which at a 10% rebate rate is the same as capping
    eligible *investment* at 30% and Tk 7,500,000. Quote the statutory figures to a taxpayer,
    never the derived ones.

- Retired the `KNOWN BLOCKER` banner at the top of `.github/workflows/publish-packages.yml`.
  It asserted that publishing "FAILS until that scope is granted" and that "no edit here can
  work around it" — but the Actions publish step authenticates with `secrets.GITHUB_TOKEN`,
  which the workflow's own `permissions` block grants `packages: write`, so it never depended
  on any human's personal token scope. Tagging v1.1.1 published
  `@bemoshiur/takabooks@1.1.1` on the first attempt. The genuinely useful half — that a
  hand-run `npm publish` needs a CLASSIC personal access token — is kept.

## [1.1.1] - 2026-09-20

### Added

- **Golden-value regression tests against the shipped rates file** (`TestRealAY2026_27`).
  Every existing test computed against a synthetic FIXTURE, so **no test asserted a single
  real AY 2026-27 amount** and corrupting a verified slab width in
  `src/data/rates-AY2026-27.toml` was caught by nothing. Seven hand-checked totals now pin
  the Paripatra §1.1 ladder (Tk 4,00,000 nil, then 10/15/20/25/30%), together with the slab
  widths, the 30% top rate, the standard VAT rate and both VAT thresholds. The expected
  figures were computed by hand from the Paripatra and then checked against the engine, not
  read off it, and one test deliberately corrupts a slab width to prove the others bite.
- **`tax.py --motor-cars`** — the পরিবেশ সারচার্জ / environmental surcharge is now
  computed. `income_tax.individual.environmental_surcharge` has shipped fully verified
  since 1.0.0 (Tk 25,000–350,000 per motor car per year on each car in excess of one,
  Finance Act 2026 Schedule 2 Part Three via NBR Paripatra 2026-27 §1.7) and **no engine
  read a single one of its nodes**. Pass each car's engine capacity
  (`--motor-cars 1400,1800`) and the charge joins `total_tax`; the working shows the band
  each car fell in and which car was treated as exempt. Reported in `--json` under
  `environmental_surcharge`.
- **`deadlines.vat_legacy_settlement_s137a`** — new rate node, করবর্ষ / AY 2026-27,
  `verified = false`, `unit = "date"`. The VAT Act s.137A legacy-demand interest-waiver
  window, six months from 1 July 2026, closing **31 December 2026**. It previously existed
  only as prose in `src/references/compliance-calendar.md` §7 and inside the `note` on
  `vat.penalties.interest_per_month`, so no engine could surface it and `rates.py --all`
  never listed it — in the quarter the calendar itself calls "the last quarter to use it".
  Marked unverified: the close date rests on secondary reporting and the text of s.137A was
  not read. Source: <http://bdlaws.minlaw.gov.bd/act-1106.html>.
- `vat.py` now reports the window as an optional reference figure, so a plain run raises it
  with an `UNVERIFIED` warning naming the closing date.
- `build/check_census.py` — a guard that re-derives the project version from all four files
  that carry it and the rate-node census from `rates.py`'s own audit, and exits non-zero when
  any published figure disagrees. Wired into `ci.yml` as the `published-figures` job, which
  also posts the census to the run summary. Both drift classes it checks had already
  happened and nothing caught either.

### Changed

- Legal entity name corrected to **TICON SYSTEM LTD** throughout (`5a6e762`). The `v1.1.0`
  tag still carries the earlier "Ticon Sys" wording in `LICENSE`, `package.json` and every
  built bundle, so that tag must not be re-cut — the correction ships from the next one.
- Social preview card gained a credibility strip (`e255fbc`).
- Version strings synchronised at **1.1.1** across `package.json`, `src/engine/takabooks.py`,
  `build/build.py` and `CITATION.cff`, which had drifted to `0.0.0`, `0.1.0`, `1.0.0` and
  `1.0.0` respectively. Every script's `--version` had been reporting a version that never
  shipped.

### Fixed

- **`tax.py` understated a multi-car individual with no warning.** The line labelled
  "Net tax payable / নিট প্রদেয় কর" omitted the environmental surcharge entirely, and the
  Caveats section then said "Every rate used in this computation is marked verified in the
  rates file" — a reassurance about what it *did* use that read as a statement about
  completeness. The charge is now either computed (`--motor-cars`) or its absence is
  stated on every run, and that reassurance can no longer be printed unqualified.
- **Release notes published a fifth set of rate counts.** `release.yml` recounted the
  rates file with its own inline walker, which counted every table carrying a `verified`
  key — including the value-less ones `rates.py` deliberately excludes — and never
  mentioned placeholders at all. The release page would have said "620 sourced figure(s),
  73 marked `verified = false`" where the engine's audit says 530 nodes, 474 verified,
  53 unverified and 3 placeholders. It now calls `rates.py --all`, the only sanctioned
  reader of that file, so the most public surface states the same census as the README,
  the Pages site and CI.
- **Notes are now separated from caveats.** `TaxComputation.notes` carries what the working
  did *not* do; `caveats` and `warnings` continue to carry what is unconfirmed about what it
  *did* use, and only those two are `blocking_problems()`. Without the split, saying "the
  environmental surcharge is not included" would have made `--strict` refuse every
  otherwise-clean computation.
- Where a taxpayer's cars fall in different capacity bands, **which** car is exempt changes
  the answer, and the Paripatra does not say — it gives only "each car in excess of one".
  TakaBooks follows the professional-summary reading (the lowest-surcharge car) and raises a
  caveat naming `income_tax.individual.environmental_surcharge.exempt_car_rule`. Where every
  car sits in one band the reading cannot change the total, and no caveat is raised.
- **`vat.py` reported the superseded monthly filing deadline as *the* deadline.** The required
  reference figure `return_deadline` read `deadlines.vat_return_monthly`, and
  `deadlines.vat_return_quarterly` / `_extended` / `vat_quarter_boundaries` were read by no
  engine module at all. From 1 July 2026 the মূসক return is **quarterly** — VAT Act s.64(1)
  as substituted by the Finance Act 2026, **within 15 days** of the end of every three tax
  periods — so a registered person filing the default return was shown a full month when the
  statute gives 15 days. The monthly node's own text already said "Monthly filing is NO
  LONGER THE DEFAULT". `return_deadline` now reads `deadlines.vat_return_quarterly`
  (required), and the monthly node is retained as an optional
  `return_deadline_monthly_election`, which is what s.64(2) actually makes it. No rate value
  changed; the figure a preparer is shown did.
- `tds.sections.137A` (ITA 2023, withholding on registered club membership) and
  `deadlines.vat_legacy_settlement_s137a` (VAT Act, the waiver window) share a section number
  and nothing else. Each node's `note` now says so, because grepping `137A` returns both and
  could make either look like coverage of the other.
- Rate-node counts corrected in `README.md`, `docs/index.md` and
  `docs/wiki/Troubleshooting.md`. Four mutually inconsistent sets were in circulation
  (436 / 362 / 55 / 19 in the English disclaimer, ৪৩৬ / ৩৬৫ / ৫২ / ১৯ in the Bangla summary,
  and two stale per-area rows). The engine's own audit reports **529 / 474 / 52 / 3**; every
  published figure now states that. No rate value changed — this is a documentation fix.
- `README.md` no longer describes "the twelve `vat.rates.reduced.*` rates" as placeholders;
  eleven were landed in 1.1.0 and only `vat.rates.reduced.digital_advertisement` remains.

*Open workstreams (not yet changes — listed so nobody mistakes this for a filing-ready
release): **52 nodes remain `verified = false`** — read from agreeing professional summaries
rather than enacted text, because the Finance Act 2026 gazette PDF is typeset in a legacy
Bijoy-family Bangla font whose glyphs map to ASCII and so could not be text-extracted (OCR
and glyph transliteration have not been attempted). **3 nodes remain `placeholder = true`**:
the individual and corporate turnover-tax gross-receipts thresholds under ITA 2023 s.163(6),
and `vat.rates.reduced.digital_advertisement`, whose reinstating S.R.O. NBR has never
published. Nothing in the file has been reviewed by an ITP or a CA. The grounding research,
and the list of what could not be confirmed, is in `docs/research/`.*

## [1.1.0] - 2026-09-06

Landed the AY 2026-27 withholding and reduced-rate schedules from primary gazette text.
The file grew from 436 rate nodes to 529; placeholders fell from 19 to 3.

| Rate nodes | 1.0.0 | 1.1.0 |
| :--- | ---: | ---: |
| verified | 362 | 474 |
| unverified | 55 | 52 |
| placeholder | 19 | 3 |
| **total** | **436** | **529** |

### Added

**উৎসে কর কর্তন / TDS — the import, property and developer schedules (`6132ba0`)**

101 new rate nodes under `tds.sections.*`, transcribed from NBR's withholding-rules
compilation (<https://nbr.gov.bd/uploads/rules/With_holding_2026.pdf>) and ITA 2023 as consolidated on bdlaws (<http://bdlaws.minlaw.gov.bd/act-details-1429.html>). Each replaced a
single scalar stub that had been carrying `value = 0` with `placeholder = true`:

- `tds.sections.125.rate` — `0` (placeholder) → removed, replaced by the full property-transfer
  schedule: সারণি-১ (7 serials × 6 floor classes, Tk 25,000–9,00,000 per shatak, at 3% or 5%
  of deed value), সারণি-২ (2 serials, 2% with Tk 500 / Tk 10,000 floors) and the structure
  surcharge (3 serials, Tk 300–800 per m² or 6–8% of deed value). AY 2026-27.
- `tds.sections.126.rate` — `0` (placeholder) → removed, replaced by the developer schedule:
  a per-square-metre residential/commercial matrix over 6 serials (residential Tk 300–1,600;
  commercial Tk 1,000–6,500) plus the land serials at 5% and 3%. AY 2026-27.
- `tds.sections.138.amount` — `0` BDT (placeholder) → removed, replaced by the 15-category
  fixed motor-vehicle table, Tk 7,500 (taxicab non-AC; pickup / human hauler / tractor /
  maxi autorickshaw; truck ≤1.5t) to Tk 50,000 (AC double-decker or sleeper bus; truck ≥20t;
  heavy or special-purpose vehicle). AY 2026-27.
- `tds.sections.138A.amount` — `0` BDT (placeholder) → `tds.sections.138A.helicopter_or_chopper`
  = **Tk 10,00,000**. AY 2026-27.
- `tds.sections.139.amount` — `0` BDT (placeholder) → the vessel schedule:
  **Tk 125 per passenger**, **Tk 170 per gross tonne** (cargo / container / coaster),
  **Tk 125 per gross tonne** (dumb barge). AY 2026-27.

**মূসক / VAT — 11 of the 12 reduced rates (`674e06f`)**

Eleven `vat.rates.reduced.*` nodes moved from `placeholder = true` to `verified = true`,
read from the Third Schedule of the VAT & SD Act 2012 as published on bdlaws (<http://bdlaws.minlaw.gov.bd/upload/act/2026-08-27-12-19-29-মূল্য-সংযোজন-কর-ও-সম্পূরক-শুল্ক-আইন,-২০১২-(1st,-2nd,-3rd-schedule).pdf>,
`as_of` 2026-08-27) and from two gazetted S.R.O. scans (<https://nbr.gov.bd/uploads/sros/IMG_20250213_0014.pdf> and <https://nbr.gov.bd/uploads/sros/IMG_20250213_00151.pdf>, `as_of`
2025-01-22). Ten kept the stand-in value they had been carrying, which the primary text
confirmed; one did not (see **Changed**):

| Node | 1.0.0 | 1.1.0 | Source |
| :--- | ---: | ---: | :--- |
| `vat.rates.reduced.building_construction_large` | 4.5% (placeholder) | 4.5% verified | 3rd Schedule |
| `vat.rates.reduced.building_construction_small` | 2% (placeholder) | 2% verified | 3rd Schedule |
| `vat.rates.reduced.hotel_non_air_conditioned` | 10% (placeholder) | 10% verified | 3rd Schedule |
| `vat.rates.reduced.local_trading_stage` | 7.5% (placeholder) | 7.5% verified | 3rd Schedule |
| `vat.rates.reduced.motor_garage_and_workshop` | 10% (placeholder) | 10% verified | S.R.O. scan |
| `vat.rates.reduced.petroleum_local_trading` | 2% (placeholder) | 2% verified | S.R.O. scan |
| `vat.rates.reduced.restaurant` | 5% (placeholder) | 5% verified | S.R.O. scan |
| `vat.rates.reduced.sweetmeat_shop` | 10% (placeholder) | 10% verified | S.R.O. scan |
| `vat.rates.reduced.medicine_local_trading` | 2.4% (placeholder) | 2.4% verified | S.R.O. scan |
| `vat.rates.reduced.wholesale_business` | 1.5% (placeholder) | 1.5% verified | 3rd Schedule |

`vat.rates.reduced.digital_advertisement` was **not** landed and remains `placeholder = true`:
the reinstating S.R.O. 255-Ain/2026/355-Mushak is not published in NBR's S.R.O. index (all 17
pages, 664 rows, were crawled). Charge 15% on an advertising supply until it is sighted.

### Changed

- **`vat.rates.reduced.land_developer`: 3 percent → 2 percent**, করবর্ষ / AY 2026-27.
  The 1.0.0 stand-in of 3% was not what the Third Schedule says; the gazetted text gives 2%.
  Source: <http://bdlaws.minlaw.gov.bd/upload/act/2026-08-27-12-19-29-মূল্য-সংযোজন-কর-ও-সম্পূরক-শুল্ক-আইন,-২০১২-(1st,-2nd,-3rd-schedule).pdf>, `as_of` 2026-08-27. This is the only figure in 1.1.0 whose **value**
  changed — the other ten reduced rates were confirmed at the value they already held.

### Known limitations

- 52 nodes remain `verified = false` and 3 remain `placeholder = true`; see the
  [Unreleased] open-workstreams note above. This release is **not** filing-ready.
- No figure in the file has been reviewed by an ITP or a CA.

## [1.0.0] - 2026-09-06

Initial public build. Everything below was written against the approved design
specification of 2026-09-05 (`docs/superpowers/specs/2026-09-05-takabooks-design.md`).

**Read the Known limitations section before using this release for anything real.**

### Added

**Engine — `src/engine/`, Python 3.11+, standard library only**

- `takabooks.py` — the shared library: `Money` as integer paisa (1 BDT = 100 paisa) with
  `decimal.Decimal` parsing and a single `ROUND_HALF_UP` at the final step; `Account`,
  `Entry` and `Ledger`; TOML (`tomllib`) and CSV I/O for `config.toml`, `accounts.toml` and
  `books/journal/YYYY-MM.csv`; the `tax_tag` grammar (`VAT:OUT:<rate>`, `VAT:IN:<rate>`,
  `TDS:<section>:<rate>`, `VDS:<rate>`, `NONE`); whole-ledger validation; and both display
  formats — Bangladeshi lakh/crore grouping `12,34,567.89` (default) and international
  `1,234,567.89` — with the `৳` symbol and Bangla digits on request.
- `rates.py` — the only sanctioned reader of `src/data/rates-AY<year>.toml`. Selects the file
  by assessment year and refuses to guess one when several exist; has no `get(key, default)`
  — a missing rate is an error, never a default; rejects bare TOML floats in rate nodes;
  refuses to hand a `placeholder = true` value to a calculator unless the caller opts in;
  and returns one caveat line per unverified figure that was actually used.
- `init_books.py` — scaffolds a `books/` directory from `src/templates/`: `config.toml`,
  the chart of accounts (হিসাব তালিকা) including the Bangladesh-specific accounts the spec
  requires (VAT Input / Rebateable, VAT Output Payable, TDS Receivable, TDS Payable, VDS
  Payable, Advance Income Tax, Provident Fund Payable, Gratuity Provision, WPPF Payable,
  Supplementary Duty Payable), `journal/` and `reports/`. Never guesses the fiscal-year
  start or the assessment year; `--dry-run`, `--force`, interactive mode.
- `post.py` — records one validated জাবেদা / journal entry. Refuses, and writes nothing,
  unless debits equal credits, every account exists, the date is ISO and every `tax_tag`
  parses. Accepts `--debit` / `--credit` lines or a JSON entry on stdin; `--dry-run`.
- `report.py` — রেওয়ামিল / trial balance, লাভ-ক্ষতি হিসাব / profit and loss and স্থিতিপত্র /
  balance sheet from one computation; Markdown on stdout and CSV in `books/reports/`;
  `--period` as a month or a fiscal year; `--grouping bd|international`.
- `vat.py` — মূসক / VAT position for a period: output tax, rebateable input tax, net payable
  or carry-forward, and উৎসে মূসক কর্তন / VDS withheld; Markdown, CSV or JSON; `--strict`
  exits non-zero if any figure used is unverified, missing or fails to reconcile.
- `tax.py` — আয়কর / income tax for an individual করদাতা: progressive slabs, investment
  rebate, minimum tax and surcharge, with the full working, taxpayer category and location
  tier read from the rates file (nothing hardcoded); `--list-options`;
  `--allow-placeholder-rates` is required while the rates file is a placeholder and stamps
  the output PROVISIONAL / অস্থায়ী; output in `en`, `bn` or `bn-en`.
- `validate.py` — whole-ledger (খতিয়ান) integrity: balance per `entry_id`, unknown accounts,
  duplicate ids, date format and order against the financial year, tax tags. Reports every
  finding at once, with distinct exit codes for findings, config problems and unreadable
  books; `--list-checks`.
- Every script: `--help`, `--books <dir>` (default `./books`), `--json`, `--version`, and a
  non-zero exit on any integrity failure. Silent correction does not exist anywhere.

**Content — `src/`, the platform-neutral source of truth**

- `core/` — `00-identity.md` (what TakaBooks is, the disclaimer), `10-workflow.md` (how the
  assistant behaves, including the behavioural counters that stop a model from doing
  arithmetic or inventing a rate), `20-bookkeeping.md` (double-entry rules, chart-of-accounts
  usage), `30-tax-overview.md` (which reference to load when). Sized to fit the 8,000-character
  ChatGPT instruction cap so one core serves every platform.
- `references/` — `income-tax.md`, `vat-mushak.md`, `withholding-tds-vds.md`,
  `bookkeeping-standards.md`, `payroll.md`, `compliance-calendar.md`, `penalties.md`,
  `glossary-bn-en.md`. Bangla statutory terms are carried beside the English throughout —
  মূসক / VAT, উৎসে কর কর্তন / TDS, খতিয়ান / ledger, করবর্ষ / assessment year.
- `data/rates-AY2026-27.toml` — the machine-readable rates schema for assessment year
  2026-27. Every rate node carries `value`, `unit`, `source`, `as_of`, `verified` and `note`;
  money in taka, percentages in percent, decimals as quoted strings. See Known limitations.
- `templates/` — `config.toml`, `accounts.toml` (the default chart of accounts) and
  `journal-header.csv` (the fixed journal schema, spec §4.3): the files `init_books.py`
  scaffolds a new `books/` from.

**Build — `build/build.py`**

- Deterministic, idempotent build from `src/` to `dist/`: `claude-skill`
  (`dist/claude-skill/bd-bookkeeping-tax/` with `SKILL.md` frontmatter, plus a zip with the
  skill folder at its root), `chatgpt` (`instructions.md` capped at 8,000 characters — the
  build fails loudly above it — plus at most 20 knowledge files), `gemini`
  (`gem-instructions.md` + knowledge), `universal` (`takabooks-complete.md`, one paste-anywhere
  file) and `agents-md` (regenerates the root `AGENTS.md`). `--check` verifies every limit
  without writing; `--strict` makes a missing source file a failure; `--clean`; `--json`.

**Distribution**

- `bin/takabooks.mjs` and the npm package `@bemoshiur/takabooks` (GitHub Packages): `install
  claude | chatgpt | gemini | universal | agents`, `list`; Node built-ins only; never
  overwrites an existing install without `--force`; `--dry-run` writes nothing; exit 2 for
  usage errors, 1 for a failed install.
- `.github/workflows/ci.yml` — unit tests on Python 3.11, 3.12 and 3.13 inside an empty
  virtualenv (so no third-party import can pass); a check that no dependency file exists;
  `build.py --check` with the ChatGPT cap; a two-build byte-identity check; the installer
  exercised against the real build and on Linux, macOS and Windows.
- `.github/workflows/release.yml` — on a `vX.Y.Z` tag: tests, full build, zips per target,
  the universal Markdown, `SHA256SUMS.txt`, attached to a GitHub Release (pre-release tags
  marked automatically).
- `.github/workflows/publish-packages.yml` — publishes the npm installer to GitHub Packages
  on the same tag push.
- `.github/workflows/wiki-sync.yml` — on a push to `main` touching `docs/wiki/**`, mirrors
  `docs/wiki/` into the repository wiki, deleting before copying so a page removed from the
  source disappears from the wiki. It refuses to run against a source tree that is missing,
  empty, without `Home.md`, or not flat, rather than emptying the live wiki. The wiki must be
  initialised once through the web UI first — `<repo>.wiki.git` does not exist until a page
  has been saved there, and no token or Action can create it — so the workflow probes for the
  repository and prints that click path instead of git's "not found".

**Tests — `tests/`, `unittest`, standard library only**

- Double-entry invariants (unbalanced entries rejected; reports tie back to the journal);
  Money with no `float` anywhere, `ROUND_HALF_UP`, lakh/crore edge cases (0, negatives,
  exactly 1,00,000, crore boundaries); the tax computation against the rates schema; VAT
  output / input / net position and VDS; validation failures (unknown account, duplicate
  `entry_id`, malformed date, bad `tax_tag`) failing loudly; every build target emitting and
  the 8k cap enforced.

**Documentation and community**

- `README.md`, generated `AGENTS.md`, `CONTRIBUTING.md` (with the evidence standard for a
  verified tax-rule update), `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1), `SECURITY.md`
  (wrong tax figures are reported with the urgency of a security bug — publicly),
  `CITATION.cff`, this changelog, MIT `LICENSE`.
- `docs/research/` — provenance for the AY 2026-27 research pass, including the honest
  list of what could not be confirmed from primary text.
- `assets/` — the hand-written SVG identity (`icon.svg`, `logo.svg`, `logo-dark.svg`,
  `social-preview.svg`) and `social-preview.png`, the 1280 × 640 raster of the card. The PNG
  is committed because GitHub's social-preview uploader accepts PNG/JPG/GIF and not SVG, and
  because no API can set a social preview — it is uploaded by hand, once. `assets/README.md`
  carries the palette with its contrast ratios, the render command, and that click path.

### Known limitations

- **No real Bangladeshi tax figure ships in this release.** `src/data/rates-AY2026-27.toml`
  is a complete schema in which every rate node is `placeholder = true`, `verified = false`,
  `value = 0` (or empty). This is deliberate: verified figures land only after adversarial
  verification against primary sources, one node at a time. Until then `tax.py` refuses to
  compute without `--allow-placeholder-rates`, `vat.py --strict` fails, and every output is
  stamped PROVISIONAL / অস্থায়ী. **Nothing computed from this release may be filed with
  NBR.** Rates in the reference prose are likewise marked unverified where they could not be
  confirmed.
- `tax.py` computes the **individual** liability only. The `[income_tax.corporate]` block in
  the rates file is schema for a later module.
- Installing the npm package from GitHub Packages requires an authenticated registry
  configuration even for public packages; a bare `npx @bemoshiur/takabooks` from a clean
  machine will not authenticate. The Release zips need no account.
- The bundles are measured against a red-team rubric (`docs/superpowers/skill-tests/`), but
  no LLM's behaviour is guaranteed. Every tax output still ends with the disclaimer: not
  professional advice; verify with a licensed ITP or CA before filing.

### Security

- Placeholder guard: a `placeholder = true` rate cannot reach a calculator without an explicit
  opt-in, and then every line of output says so.
- No script opens a network connection or writes outside the `--books` / `--dest` directory
  it was given; there is no telemetry.
- All four workflows run under a top-level `permissions: {}` and opt in per job; release
  assets ship with `SHA256SUMS.txt`.

[Unreleased]: https://github.com/bemoshiur/TakaBooks/compare/v1.1.1...HEAD
[1.1.1]: https://github.com/bemoshiur/TakaBooks/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/bemoshiur/TakaBooks/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/bemoshiur/TakaBooks/releases/tag/v1.0.0
