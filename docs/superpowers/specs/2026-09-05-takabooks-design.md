# TakaBooks — Design Specification

**Status:** Approved 2026-09-05 · **Branch:** `build/v1` · **Repo:** https://github.com/bemoshiur/TakaBooks
**Maintainer:** Moshiur Rahman (@bemoshiur) · **Company:** TICON SYSTEM LTD — https://ticonsys.com

---

## 1. What TakaBooks is

A portable, LLM-agnostic bookkeeping and taxation package for **Bangladesh**. It gives any
capable LLM (Claude, ChatGPT, Gemini, Kimi, DeepSeek, Llama, Copilot, Cursor…) two things:

1. **Knowledge** — accurate, cited, versioned reference material on Bangladeshi income tax,
   VAT/Mushak, TDS/VDS, statutory bookkeeping, payroll and the compliance calendar.
2. **Tooling** — a dependency-free Python engine that maintains real double-entry books and
   computes every number deterministically.

It ships a Claude Skill as **one build target among several**. The Claude Skill is not the
identity of the project; portability is.

### Non-goals
- Not a replacement for a licensed Income Tax Practitioner or Chartered Accountant.
- Not an e-filing robot. It prepares figures and forms; humans file them.
- Not a general-purpose accounting suite. Bangladesh-specific, SME-focused.

---

## 2. Prime directive: the LLM never does arithmetic

**Deterministic Python owns every number. The LLM owns classification and explanation.**

| LLM does | Python does |
|---|---|
| Decide which accounts a transaction hits | Add, subtract, allocate, round |
| Pick the right Mushak form / TDS section | Enforce debits == credits |
| Explain a rule, cite the statute | Compute slabs, rebates, VAT, TDS |
| Ask clarifying questions | Validate the entire ledger |

Any script that would emit an unbalanced entry or an unreconciled report **must exit non-zero
with a clear error**. Silent correction is forbidden. A wrong number filed with NBR is worse
than a refusal.

---

## 3. Repository layout

```
TakaBooks/
├── README.md  LICENSE  CHANGELOG.md  AGENTS.md
├── CONTRIBUTING.md  CODE_OF_CONDUCT.md  SECURITY.md  CITATION.cff
├── assets/                       logo.svg, logo-dark.svg, social-preview.png, icon.svg
├── src/                          ← SOURCE OF TRUTH, platform-neutral
│   ├── core/
│   │   ├── 00-identity.md        who/what TakaBooks is, the disclaimer
│   │   ├── 10-workflow.md        how the assistant should behave
│   │   ├── 20-bookkeeping.md     double-entry rules, chart of accounts usage
│   │   └── 30-tax-overview.md    routing: which reference to load when
│   ├── references/
│   │   ├── income-tax.md         slabs, rebate, minimum tax, surcharge, corporate
│   │   ├── vat-mushak.md         rates, thresholds, every Mushak form
│   │   ├── withholding-tds-vds.md  full rate matrix + deposit deadlines
│   │   ├── bookkeeping-standards.md  Companies Act 1994, FRA 2015, IFRS/IAS
│   │   ├── payroll.md            salary tax, PF, gratuity, WPPF
│   │   ├── compliance-calendar.md  every recurring deadline
│   │   ├── penalties.md          interest + penalty exposure
│   │   └── glossary-bn-en.md     Bangla ↔ English term pairs
│   ├── data/
│   │   └── rates-AY2026-27.toml  EVERY rate/threshold, machine-readable
│   ├── engine/                   Python, stdlib only
│   └── templates/                accounts.toml, config.toml, journal header
├── build/build.py                emits dist/ from src/
├── dist/                         generated; attached to releases
├── docs/                         wiki source (mirrored to GitHub Wiki)
├── tests/                        unittest suite
└── .github/workflows/            release.yml, publish-packages.yml, ci.yml
```

---

## 4. Hard technical contracts

### 4.1 Python
- **Standard library only.** No pip install, ever. Target user is an SME on an office laptop.
- **Floor: Python 3.11** (for `tomllib`). Declare it; fail fast with a clear message below it.
- Config/accounts/rates use **TOML** (`tomllib` reads it; it is in the stdlib — PyYAML is not).
  Scripts only ever *read* TOML. Humans and the LLM edit it.

### 4.2 Money — integer paisa, never float
- 1 BDT = 100 paisa. **All internal arithmetic is `int` paisa.**
- Parse CSV amounts with `decimal.Decimal`, then convert to int paisa. Never `float`.
- Rounding: `ROUND_HALF_UP` (the commercial convention), applied once, at the final step.
- Two display formats, both required:
  - International: `1,234,567.89`
  - **Bangladeshi lakh/crore grouping: `12,34,567.89`** ← default for user-facing output
- Currency symbol `৳` (BDT). Always state the unit.

### 4.3 Journal CSV schema
Path: `books/journal/YYYY-MM.csv`. One row per **posting line**. Human-readable BDT decimals
(so it opens correctly in Excel), converted to paisa on read.

```
date,entry_id,description,account,debit,credit,party,doc_ref,tax_tag,memo
```

- `date` — ISO `YYYY-MM-DD`
- `entry_id` — groups rows into one journal entry; **all rows sharing an entry_id must balance**
- `account` — code from accounts.toml; unknown code is a hard error
- `debit` / `credit` — decimal BDT, exactly one of the two non-zero per row
- `tax_tag` — structured, drives VAT/TDS derivation. Grammar:
  - `VAT:OUT:<rate>` output VAT · `VAT:IN:<rate>` rebateable input VAT
  - `TDS:<section>:<rate>` tax deducted · `VDS:<rate>` VAT deducted at source
  - `NONE` when not tax-relevant
- `memo` — free text, always last so commas in it are survivable

### 4.4 Chart of accounts (`accounts.toml`)
```toml
[[account]]
code = "1100"
name = "Cash in Hand"
name_bn = "হাতে নগদ"
type = "asset"          # asset|liability|equity|income|expense
normal = "debit"        # debit|credit
```
Code blocks: `1xxx` assets · `2xxx` liabilities · `3xxx` equity · `4xxx` income ·
`5xxx` COGS · `6xxx` operating expenses · `7xxx` other income · `8xxx` other expense ·
`9xxx` tax accounts.

**Bangladesh-specific accounts that MUST exist** (codes indicative, names normative):
VAT Input / Rebateable (asset) · VAT Output Payable (liability) · TDS Receivable — tax
deducted by customers (asset) · TDS Payable — deducted from vendors (liability) ·
VDS Payable · Advance Income Tax (asset) · Provident Fund Payable · Gratuity Provision ·
WPPF Payable · Supplementary Duty Payable.

### 4.5 Rates data (`rates-AY2026-27.toml`)
**No rate is ever hardcoded in prose or in code.** Every figure lives here, keyed by assessment
year, each with a `source` URL and a `verified` boolean. Consumers must print which AY file
they used. A rate that could not be confirmed from a primary source is marked
`verified = false` and every consumer must surface that caveat to the user.

Updating TakaBooks for a new Finance Act = add one file + one calendar entry. Nothing else.

### 4.6 Engine modules and file ownership
| File | Responsibility |
|---|---|
| `src/engine/takabooks.py` | Shared library: Money, Account, Entry, Ledger, TOML/CSV IO, validation, BD formatting |
| `src/engine/init_books.py` | Scaffold a `books/` directory from templates |
| `src/engine/post.py` | Validate + append a journal entry; refuse if unbalanced |
| `src/engine/report.py` | Trial balance, P&L, balance sheet — Markdown + CSV from one computation |
| `src/engine/vat.py` | VAT position, input/output reconciliation, Mushak 9.1 figures |
| `src/engine/tax.py` | Income tax: slabs, rebate, minimum tax, surcharge; reads rates TOML |
| `src/engine/validate.py` | Whole-ledger integrity: balance, unknown accounts, date order, duplicate ids |

Every script: `--help`, `--books <dir>` (default `./books`), `--json` for machine output,
non-zero exit on any integrity failure.

---

## 5. Build targets (`build/build.py`)

One source of truth → many bundles. `build.py` must be deterministic and re-runnable.

| Target | Output | Notes |
|---|---|---|
| `claude-skill` | `dist/claude-skill/bd-bookkeeping-tax/` + `.zip` | `SKILL.md` with YAML frontmatter (`name`, `description`). Zip has the skill folder at root so it works for both claude.ai upload and `~/.claude/skills/`. |
| `chatgpt` | `dist/chatgpt/instructions.md` + `knowledge/` | **Instructions must fit 8000 characters** — build fails loudly if exceeded. Knowledge files ≤ 20. |
| `gemini` | `dist/gemini/gem-instructions.md` + `knowledge/` | Gem instruction limits respected. |
| `universal` | `dist/universal/takabooks-complete.md` | Single paste-anywhere file for Kimi, DeepSeek, Llama, any LLM. |
| `agents-md` | `AGENTS.md` at repo root | Cross-agent standard: Cursor, Codex, Copilot, etc. |

The 8k ChatGPT cap is the binding constraint on the core instruction. Design the core to fit
it; push all detail into loadable references. This also produces good progressive disclosure
for Claude, so one discipline serves both.

---

## 6. Content rules (non-negotiable)

1. **Every rate, threshold and deadline carries a source URL and a "current as of" date.**
2. **Never invent a number.** If it could not be verified, mark it `verified = false`, say so
   in the prose, and tell the user to confirm with NBR. Absent beats wrong.
3. State the **assessment year** in any tax computation output.
4. Carry **Bangla statutory terms alongside English** — মূসক (VAT), উৎসে কর কর্তন (TDS),
   খতিয়ান (ledger) — so users can find forms on the NBR portal.
5. Reply in the user's language: Bangla, Banglish, or English. Reason in English.
6. Every tax output ends with the disclaimer: this is not professional advice; verify with a
   licensed ITP/CA before filing.

---

## 7. Testing

`unittest`, stdlib only, run via `python3 -m unittest discover tests`.

- Double-entry invariants: unbalanced entries rejected; every report ties back to the journal.
- Money: no float anywhere; ROUND_HALF_UP; lakh/crore formatting incl. edge cases
  (0, negatives, exactly 1,00,000, crore boundaries).
- Tax: golden cases with hand-checked expected values, each citing its rates source.
- VAT: output/input/net position, VDS.
- Validation: unknown account, duplicate entry_id, malformed date, bad tax_tag all fail loudly.
- Build: every target emits; ChatGPT 8k cap enforced.

CI runs the suite on push. Green tests are a release precondition.

---

## 8. Distribution

- **Releases** — tag `vX.Y.Z` → Action builds all bundles → attaches zips to the GitHub Release.
- **Packages** — npm package on GitHub Packages: `npx @bemoshiur/takabooks install <platform>`.
  *Requires the `write:packages` token scope; publishing fails until it is granted.*
- **Wiki** — `docs/` mirrored to the GitHub Wiki.
- **SEO** — repo description, up to 20 topics, homepage `https://ticonsys.com`, social preview,
  and full GitHub community-standards set.

---

## 9. Attribution

Maintained by **Moshiur Rahman** (@bemoshiur) · **TICON SYSTEM LTD** — https://ticonsys.com
Licensed MIT. Credit TICON SYSTEM LTD in README, LICENSE, AGENTS.md, docs and every built bundle.
