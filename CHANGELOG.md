# Changelog

All notable changes to TakaBooks are recorded in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

TakaBooks — Moshiur Rahman ([@bemoshiur](https://github.com/bemoshiur)) ·
Ticon Sys — https://ticonsys.com

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

No changes since 1.0.0.

*Open workstreams (not yet changes — listed so nobody mistakes 1.0.0 for a filing-ready
release): landing verified AY 2026-27 figures in `src/data/rates-AY2026-27.toml` from
primary sources, node by node, per the evidence standard in `CONTRIBUTING.md`; the grounding
research is in `docs/research/`.*

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

[Unreleased]: https://github.com/bemoshiur/TakaBooks/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/bemoshiur/TakaBooks/releases/tag/v1.0.0
