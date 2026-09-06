# Contributing — অবদান

TakaBooks is maintained by Moshiur Rahman ([@bemoshiur](https://github.com/bemoshiur)) at
Ticon Sys and welcomes contributions of every size. This page is the wiki version of the
repository's `CONTRIBUTING.md`; where the two differ, the repository file wins.

## Ways to help, most valuable first

1. **Verify or correct a tax figure.** The rates file is the heart of the project, and a
   figure read from a primary NBR source by someone who checked it is the most valuable
   thing anyone can contribute. Use the *Tax rule update* issue template, or open a pull
   request against `src/data/rates-AY<year>.toml` following
   [Updating Tax Rates](Updating-Tax-Rates).
2. **Populate a reference.** Several `src/references/*.md` files are stubs with a *Scope this
   file will cover* list and a *Definition of done*. Filling one in — mechanisms, forms,
   conditions, each with a primary-source URL and a "current as of" date — is research work
   that a practitioner can do better than anyone.
3. **Report an engine bug.** A balanced entry refused, an unbalanced one accepted, a report
   that does not tie, a formatting edge case in লাখ/কোটি grouping. Use the *bug report*
   template with the command, the input and the output.
4. **Improve the documentation.** This wiki is generated from `docs/wiki/` — edit there.
5. **Review Bangla.** Term pairs, labels, the Bangla disclaimer. The glossary asks for a
   word-by-word review by a Bangladeshi CA or ITP.
6. **Test a platform install.** Confirm the ChatGPT, Gemini, Kimi or DeepSeek path works on a
   fresh account and report what the screens actually look like today.

## The rules that have no exceptions

These come from the design specification and every contribution is reviewed against them.

1. **Never invent a Bangladeshi tax rate, threshold, deadline or statute number.** Every
   figure lives in the rates file with a `source` URL and a `verified` flag. If it could not
   be confirmed from a primary source it is `verified = false` and the prose says so.
   *Absent beats wrong.* A wrong number that reaches NBR is worse than an absent one.
2. **The LLM never does arithmetic.** Python owns every number. A script that would emit an
   unbalanced entry or an unreconciled report exits non-zero with a clear error. Silent
   correction is forbidden.
3. **Standard library only.** No `pip install`, ever. Python 3.11 is the floor (`tomllib`);
   below it, fail fast with a clear message.
4. **Money is `int` paisa, never `float`.** Parse text with `decimal.Decimal`; round
   `ROUND_HALF_UP`, once, at the final step.
5. **`src/` is the source of truth; `dist/` and the root `AGENTS.md` are generated** by
   `build/build.py` and are never hand-edited.
6. **Bangla statutory terms alongside English** wherever one appears: মূসক / VAT,
   উৎসে কর কর্তন / TDS, খতিয়ান / ledger, করবর্ষ / assessment year.
7. **Every tax output ends with the disclaimer** — not professional advice; verify with a
   licensed ITP or CA before filing.
8. **No real taxpayer data in the repository.** No TIN, BIN, NID, bank details or client
   ledgers. Fixtures are synthetic.

## Setting up

```bash
git clone https://github.com/bemoshiur/TakaBooks.git
cd TakaBooks
python3 --version                              # 3.11 or newer
python3 -m unittest discover tests             # the whole suite, a few seconds
python3 build/build.py --check                 # every bundle assembled in memory, every limit verified, nothing written
```

There is no virtual environment to create and nothing to install. If `--check` reports a
missing expected source file (for instance `src/templates/`), that is a warning, not a
failure, and `--strict` turns it into one for release builds.

## Repository map

| Path | What it is | Edit it? |
| --- | --- | --- |
| `src/core/` | The always-loaded instruction: identity, workflow, bookkeeping rules, routing table. **Concatenated into the ChatGPT instruction field, so the four files together must fit 8,000 characters.** Reference prose goes in `<!-- knowledge-only -->` … `<!-- /knowledge-only -->` so the build keeps it in the knowledge files but drops it from the capped targets. | Yes, carefully |
| `src/references/` | One file per subject. Opens with *Current as of*, *Sources*, *Status*. | Yes — with primary sources |
| `src/data/` | `rates-AY<year>.toml`. | Yes — see [Updating Tax Rates](Updating-Tax-Rates) |
| `src/engine/` | The Python engine and its shared library. | Yes |
| `src/templates/` | `accounts.toml`, `config.toml`, the journal header. | Yes |
| `build/build.py` | Emits `dist/` and `AGENTS.md`. | Yes |
| `dist/`, `AGENTS.md` | Generated. | **Never by hand** |
| `tests/` | `unittest` suite. | Yes — every change ships with tests |
| `docs/wiki/` | This wiki. | Yes |
| `docs/superpowers/specs/` | The design specification. | Maintainer |
| `docs/research/` | Research provenance for the rates file. | Research passes |
| `.github/` | CI, release, package publishing, issue and PR templates. | Yes |

## Making a change

### Engine code

- Keep the shared library free of Bangladeshi figures. It defines *no* rate, threshold,
  deadline or section number, and neither should any script; they read the rates file.
- Every script offers `--help`, `--books <dir>`, `--json`, `--version`, and exits non-zero on
  any integrity failure with a stable code (see [Engine Reference](Engine-Reference)).
- Type hints and `from __future__ import annotations`. Modules are importable without side
  effects.
- Money passes through `Money`; a `float` anywhere near it is a bug the library will catch,
  so do not fight the library.
- Bangla / English term pairs come from `takabooks.term("vat")` and friends, not from string
  literals scattered through the code.
- Add or extend tests in `tests/`. The suite covers the double-entry invariant, money and
  formatting edge cases (zero, negatives, exactly one lakh, crore boundaries), golden tax
  and VAT cases citing their rates source, validation failures, and the build caps. A change
  without a test is not finished.

### Core instruction and references

- The 8,000-character cap on `src/core/` is binding. `build.py --check` prints the count and
  the headroom on every run; watch it.
- References describe mechanisms and *point at* the rates file; they never carry a figure.
  When you fill one in, bump *Current as of*, list *Sources* (primary only), and change
  *Status* honestly — `STUB`, `PARTIAL`, `POPULATED`.
- The core instruction is micro-tested against adversarial prompts (records under
  `docs/superpowers/skill-tests/`). If you change how the assistant is told to behave, expect
  to be asked how it was tested.

### Rates

The full procedure — landing a figure, adding an assessment year — is on
[Updating Tax Rates](Updating-Tax-Rates). In short: primary source URL, `as_of` date,
`verified = true` **only if you read it from primary text**, `placeholder = false`, rewrite
`note` for the end user who will see it as a warning, run the audit, update the golden tests,
cite the source in the PR.

If your source is a professional summary rather than enacted text, the honest state is
`verified = false, placeholder = false` with the reason in `note` — not `verified = true`, and
not a placeholder. To report a figure you believe is wrong, use the **Tax rule update** issue
template (`.github/ISSUE_TEMPLATE/tax-rule-update.yml`), publicly.

### Documentation

The wiki is mirrored from `docs/wiki/`; edits made in the wiki UI are overwritten. Pages are
flat (`Title-With-Hyphens.md`), link to each other by page name, link to repository files by
absolute URL, and state no figure. The full checklist is in
[`docs/README.md`](https://github.com/bemoshiur/TakaBooks/blob/main/docs/README.md).

## Commits and pull requests

- Conventional-commit subjects: `feat:`, `fix:`, `docs:`, `build:`, `test:`, `data:` for a
  rates change.
- One logical change per commit. Never commit `dist/` by hand — regenerate it.
- Run the suite and `build.py --check` before you push; CI runs both on every push, on
  Python 3.11, 3.12 and 3.13, inside an empty virtual environment that proves nothing beyond
  the standard library is imported.
- A pull request states **which rates file it targets** and **whether any figure it touches is
  `verified = false`**. A PR that changes a tax figure **must cite a primary NBR source** in
  its description. Reviewers open the source and read the number.
- Fill in the PR template. It exists so that the review can be fast.

## Reporting a wrong tax figure

Open an issue with the **Tax rule update** template
(`.github/ISSUE_TEMPLATE/tax-rule-update.yml`, offered at
https://github.com/bemoshiur/TakaBooks/issues/new/choose). It asks for the dotted key in
the rates file, the assessment year, the NBR source URL and the date you read it.

**Do this publicly.** A wrong or outdated rate is a correctness bug, not a security
vulnerability. The repository's `SECURITY.md` says the same: private disclosure is for
things like a script writing outside `--books` or a bundle that leaks data — never for a
number, because hiding a wrong number keeps the warning from the people it endangers.

## Security

Report genuine vulnerabilities as `SECURITY.md` describes. The engine's security posture is
simple and worth keeping: it reads TOML, reads and appends CSV under the `--books`
directory, makes no network calls, and sends no telemetry. A change that adds a network
call, an environment lookup, or a write outside `--books` needs a very good reason and a
loud comment.

## Release notes for maintainers

Two steps in a release cannot be automated and are recorded here so they are not forgotten:

- **Social preview image** (`assets/social-preview.png`, 1280×640) is uploaded by hand under
  *Settings → General → Social preview*. No API exists. The PNG is the raster of
  `assets/social-preview.svg`; keep the SVG as the editable source, but upload the **PNG** —
  GitHub's uploader does not accept SVG.
- **The wiki repository** must be initialised once by creating a first page in the web UI
  before any sync can push to it, and *Restrict editing to collaborators only* should be
  set at the same time. See `docs/README.md`.

Publishing the npm package to GitHub Packages needs the `write:packages` scope on the
token; in CI the default `GITHUB_TOKEN` with `packages: write` suffices.

## Code of conduct and licence

Be kind, be precise, cite your sources. The repository's `CODE_OF_CONDUCT.md` applies to every
interaction. Contributions are accepted under the MIT License and credit Ticon Sys
(https://ticonsys.com) as the project's home.
