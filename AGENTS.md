# TakaBooks — instructions for coding agents

TakaBooks is an LLM-agnostic bookkeeping and taxation package for **Bangladesh**. It
ships two halves: cited, versioned reference material on Bangladeshi tax, and a
dependency-free Python engine that maintains real double-entry books.

**Prime directive: the LLM never does arithmetic.** Deterministic Python owns every
number; the model owns classification and explanation. Any script that would emit an
unbalanced entry or an unreconciled report must exit non-zero with a clear error. Silent
correction is forbidden. A wrong number filed with the National Board of Revenue (NBR) is
worse than a refusal.

## Non-negotiable rules

1. **Never invent a Bangladeshi tax rate, threshold, deadline or statute number.** Every
   figure lives in `src/data/rates-AY2026-27.toml` (assessment year 2026-27), keyed by assessment year, each with a `source` URL and a
   `verified` boolean. If a figure could not be confirmed from a primary source it is
   `verified = false`, and every consumer must surface that caveat. Absent beats wrong.
   This rule has no exceptions.
2. **Standard library only.** No `pip install`, ever — the target user is an SME on an
   office laptop. Floor is Python 3.11 (`tomllib`); fail fast with a clear message below it.
3. **Money is `int` paisa, never `float`.** 1 BDT = 100 paisa. Parse text amounts with
   `decimal.Decimal`; round `ROUND_HALF_UP`, once, at the final step.
4. **`src/` is the source of truth. `dist/` is generated — never hand-edit it**, and never
   hand-edit the root `AGENTS.md` either: both come out of `build/build.py`.
5. **Carry the Bangla statutory term beside the English one** wherever a statutory term
   appears: মূসক / VAT, উৎসে কর কর্তন / TDS, খতিয়ান / ledger. Users need it to find the
   form on the NBR portal.
6. **Every tax output ends with the disclaimer**: not professional advice, verify with a
   licensed Income Tax Practitioner (ITP) or Chartered Accountant (CA) before filing.

## Repository layout

| Path | What it is |
| --- | --- |
| `src/core/` | The always-loaded instruction: identity, workflow, bookkeeping rules, tax routing. |
| `src/references/` | Deep reference, one file per subject: `income-tax.md`, `vat-mushak.md`, `withholding-tds-vds.md`, `bookkeeping-standards.md`, `payroll.md`, `compliance-calendar.md`, `penalties.md`, `glossary-bn-en.md` |
| `src/data/` | `rates-AY<year>.toml` — every rate and threshold, machine-readable. |
| `src/engine/` | The Python engine, standard library only. |
| `src/templates/` | `accounts.toml`, `config.toml`, journal header. |
| `build/build.py` | Emits every platform bundle in `dist/`, plus this file. |
| `dist/` | Generated bundles. Attached to releases. |
| `tests/` | `unittest` suite. |

## Setup and build

```bash
python3 build/build.py            # build every target into dist/ (and rewrite AGENTS.md)
python3 build/build.py --check    # verify every platform limit, write nothing
python3 build/build.py --clean    # wipe dist/ first
python3 build/build.py --target chatgpt
```

The build is deterministic and idempotent: the same `src/` bytes produce byte-identical
`dist/` bytes, with no timestamps anywhere, so CI can diff two builds. It assembles every
bundle in memory, checks every platform limit, and only then writes — a build that would
break a cap writes nothing at all.

Hard caps the build enforces: ChatGPT instructions ≤ 8,000
characters, ChatGPT knowledge ≤ 20 files, Gemini knowledge
≤ 10 files, Claude Skill `description`
≤ 200 characters, this file ≤ 32 KiB.

`src/core/` is the binding constraint: it is concatenated into the ChatGPT instruction
field, so it must fit 8,000 characters. If a passage is
reference material rather than instruction, wrap it in `<!-- knowledge-only -->` …
`<!-- /knowledge-only -->`: the build then keeps it in the knowledge files and the
single-file bundle but drops it from the two character-capped instruction targets.

## Testing

```bash
python3 -m unittest discover tests
```

Green tests are a release precondition; CI runs them on push. Cover the double-entry
invariant, integer-paisa money and লাখ/কোটি formatting edge cases, tax golden cases with
hand-checked values that cite their rates source, and the build caps.

## Code style

- Standard library only. `decimal.Decimal` for parsing, `int` paisa for arithmetic.
- TOML is read-only to scripts (`tomllib`); humans and the model edit it.
- Every engine script offers `--help`, `--books <dir>` (default `./books`) and `--json`,
  and exits non-zero on any integrity failure.
- Display money in the Bangladeshi লাখ/কোটি grouping by default (`৳ 12,34,567.89`); the
  international grouping (`1,234,567.89`) is available on request. Always state the unit.
- Type hints and `from __future__ import annotations`. Keep modules importable, not
  side-effecting at import time.

## Security

- No real taxpayer data in the repository — no TIN, no BIN, no NID, no bank details.
  Fixtures are synthetic.
- No network calls anywhere in the engine or the build. No telemetry.
- The engine only ever reads TOML and reads/appends CSV under the `--books` directory.
  Never run a write path against a real `books/` directory without an explicit `--books`.

## Commits and pull requests

- Conventional-commit style subject: `feat:`, `fix:`, `docs:`, `build:`, `test:`.
- One logical change per commit. Never commit `dist/` by hand; regenerate it.
- A pull request states which rates file it targets and whether any figure it touches is
  `verified = false`. A PR that changes a tax figure must cite a primary NBR source.

## Note for Claude Code

Claude Code reads `CLAUDE.md`, not `AGENTS.md`. To share this file, put `@AGENTS.md` on
the first line of a root `CLAUDE.md`.

## Attribution

TakaBooks — maintained by Moshiur Rahman (@bemoshiur) · Ticon Sys — https://ticonsys.com · MIT licensed · https://github.com/bemoshiur/TakaBooks
