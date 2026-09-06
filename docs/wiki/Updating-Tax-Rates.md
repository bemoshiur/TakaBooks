# Updating Tax Rates — করহার হালনাগাদ

This is the most important maintenance page in the wiki. It explains how the versioned rates
file works, what the engine does with a verified, an unverified and a placeholder figure, and
the exact procedure for adding a new করবর্ষ / assessment year after a Finance Act.

> This page quotes **no** rate, threshold or deadline as a statement of Bangladeshi law. Where
> a figure appears below it is inside a shape-of-the-file example or a pasted command output,
> and the point being made is about the *mechanism*. Every figure lives in
> `src/data/rates-AY<year>.toml` with a `source` URL and a `verified` flag, and nowhere else.
> **The file is always the authority on its own state — including over this page.** Run the
> audit rather than trusting a count you read here.

## Why a rates file

The design rule (specification §4.5): **no rate is ever hardcoded in prose or in code.** Every
figure — slabs, thresholds, rebate caps, VAT rates, withholding rates, filing and deposit
deadlines, policy switches — lives in one TOML file per assessment year, and each figure
carries:

- the `source` URL of the document it was read from,
- the `as_of` date on which that instrument takes effect or was published,
- a `verified` boolean — true **only** when the figure was read from primary text,
- a `placeholder` boolean — true while the node is schema rather than data.

Consumers (`tax.py`, `vat.py`, `rates.py`, and the assistant through the bundles) must print
which file they used and must surface every caveat. The point of the discipline:

- **Updating TakaBooks for a new Finance Act = add one file + one calendar entry.** No Python
  changes.
- **A figure nobody has checked can never look checked.** Absent beats wrong.
- **A wrong number is visible, sourced and correctable in one place**, by pull request,
  with the review that a public repository gets.

## The file

### Name and location

```
src/data/rates-AY2026-27.toml
```

The only filename shape the loader recognises is `rates-AY<YYYY>-<YY>.toml` (a four-digit
second half is also accepted). The assessment year in the name is the assessment year of the
file; `rates.py --list` enumerates what exists.

The file opens with a long header comment that is the authoritative version of this page: the
status of the file, the landing procedure, the format rules, **the dotted key paths each
engine module reads**, and a section-by-section map. Read it before editing anything.

### `[meta]`

`[meta]` is what the engine reads to decide whether it may open the file at all. The AY
2026-27 file currently declares:

```toml
[meta]
assessment_year = "2026-27"
income_year = "2025-26"
income_year_start = "2025-07-01"
income_year_end = "2026-06-30"
currency = "BDT"
schema_version = 1
status = "landed"          # free text, for humans
placeholder = false        # rates.py reads this: false = the file may be opened
verified = false           # true only when the audit reports zero unverified nodes
authority = "National Board of Revenue (NBR), Bangladesh — জাতীয় রাজস্ব বোর্ড"
```

Two flags, two different jobs, and conflating them is the commonest mistake:

| Flag | What it controls |
| --- | --- |
| `placeholder` | **Whether the file opens at all.** `true` means the whole file is schema awaiting research: every consumer refuses to compute unless the caller passes `--allow-placeholder-rates`. `false` lets `rates.py` open it — individual nodes still carry their own `placeholder` flag and are still refused one by one. |
| `verified` | **Whether outputs are stamped provisional.** `false` keeps a caveat on every output. Do **not** set it `true` until `rates.py --all` reports zero unverified nodes. |

### A rate node

A **rate node** is any table that carries a `value` key. Everything else is structure or
metadata and is not audited. A landed node looks like this:

```toml
  [vat.rates.standard]
  label_en = "Standard VAT rate"
  label_bn = "প্রমিত মূসক হার"
  value = 15
  unit = "percent"
  source = "http://bdlaws.minlaw.gov.bd/act-1106/section-42308.html"
  as_of = "2019-07-01"
  verified = true
  placeholder = false
  note = """
… what the figure covers, the section that sets it, and every condition attached …
"""
```

and a node still awaiting research looks like this — note that it has a `value`, and is
refused anyway:

```toml
  [vat.rates.reduced.land_developer]
  label_en = "Land developer — NOT CERTIFIED"
  label_bn = "ভূমি উন্নয়নকারী — অনিশ্চিত"
  value = 3
  unit = "percent"
  source = "…"
  as_of = "2026-08-27"
  verified = false
  placeholder = true
  note = """
DO NOT FILE ON THIS FIGURE. … To confirm: read paragraph (3) in the printed gazette …
"""
```

| Key | Meaning |
| --- | --- |
| `value` | The figure. A whole-taka amount as an integer; anything with decimals as a **quoted string**; a date or policy as text. |
| `unit` | Free text; the file uses `percent`, `BDT`, `date`, `policy`, `count` and `cc`. `percent` nodes are checked: a value above 100 is rejected as a fraction/percent mix-up. |
| `source` | The exact URL of the instrument — the Finance Act, the SRO, the NBR পরিপত্র / Paripatra, the statute on bdlaws, or the NBR page that publishes it. Not a news article, not a blog, not a summary. **Not the bare `https://nbr.gov.bd/` homepage either: a URL that does not identify the instrument is not a source.** |
| `as_of` | ISO date (`YYYY-MM-DD`) on which the instrument takes effect or was published. |
| `verified` | `true` **only** when the value was read from primary text. Absent counts as `false`. |
| `placeholder` | `true` while the node is schema, not data. Absent counts as `false`. |
| `note` | What the figure covers and every condition attached. **This text is shown to the end user as a warning, so write it for them.** Rewrite it when the value changes. |
| `label_en`, `label_bn` | Display labels. Extra descriptive keys (`applies_to`, `condition`, `allowed`, `deducted_by`, `covers`, …) are always permitted and preserved for display. |

Lists of nodes (`[[income_tax.individual.slabs]]`,
`[[income_tax.individual.surcharge.bands]]`) are arrays of tables; each element may nest its
own rate nodes — a slab has a `rate` node and a `width`. Some tables are **sections rather
than rates**: `tds.sections.109` describes a withholding section and has no `value`, while the
rate lives one level down at `tds.sections.109.rate`. Asking `rates.py` for the section says
so rather than guessing:

```
error: rates-AY2026-27.toml: tds.sections.109 is a section, not a rate — it has no 'value'.
```

### Format rules the loader enforces

These are not conventions; `src/engine/rates.py` raises on violation.

- **Never write a bare TOML float.** `27.5` becomes a binary float, and TakaBooks refuses
  float money. Write `"27.5"`. Any float in a rate node is a `RatesError` — which is why every
  half-point corporate rate in the file is a quoted string.
- **Money is in taka, never paisa.** `400000` or `"400000.50"`. The loader converts to
  integer paisa.
- **Percentages are percent, not fractions.** `15` means fifteen percent.
- **A missing key is an error, never a default.** There is no `get(key, default)` in the
  loader. A consumer that needs an optional node asks for it by name and says "not in rates
  file" out loud instead of substituting a number.
- **A node without `verified = true` is unverified.** A bare scalar where a node was expected
  is reported unverified too.

## How the engine chooses the file

Every CLI resolves the rates file in this order; the first that applies wins:

1. `--rates PATH` — an explicit file.
2. `--assessment-year AY` — that year's file in the data directory.
3. `books/config.toml` `[books] rates_file` — the books pin their own file. A relative name is
   searched beside `config.toml`, then in the data directory, then in the current directory.
4. `books/config.toml` `[books] assessment_year`.
5. The sole `rates-AY*.toml` in the data directory. **If several exist and no year was named,
   the loader refuses** — a rates file is a legal position for one year, and computing
   against the wrong year silently is exactly what the design forbids.

The data directory defaults to `src/data/` in a checkout and to `data/` beside the scripts in
a built bundle (`--data-dir DIR` overrides). Every output prints
`Rates source: rates-AY<year>.toml — করবর্ষ / assessment year <year>` so the reader knows
which file produced it.

## What each verification state does

| State | How it is marked | What the engine does |
| --- | --- | --- |
| **Verified** | `verified = true`, `placeholder = false` | Used normally. Provenance line printed. |
| **Unverified** | `verified = false` or absent | Used, but the output carries an `UNVERIFIED: <key> …` caveat naming the key and file, the output is stamped PROVISIONAL, and `vat.py --strict` exits non-zero. The assistant must label the figure UNVERIFIED, show `source` and `as_of`, and tell the user to confirm with NBR. |
| **Placeholder** | `placeholder = true` on the node | **Refused** unless the caller passes `--allow-placeholder-rates`; then computed, with every result stamped **PROVISIONAL / অস্থায়ী — NOT FOR FILING** and a `PLACEHOLDER: <key> …` caveat per figure. |
| **Whole file placeholder** | `placeholder = true` in `[meta]` | The file will not open at all (exit 8) without `--allow-placeholder-rates`. |
| **Absent** | No node at that key | Required key: refused (exit 8) with the key named. Optional key: reported as `not in rates file`. |

## Auditing a file

```bash
python3 src/engine/rates.py --assessment-year 2026-27          # counts + first 15 keys of each state
python3 src/engine/rates.py --assessment-year 2026-27 --all     # every unverified and placeholder key
python3 src/engine/rates.py --assessment-year 2026-27 --key vat.rates.standard
python3 src/engine/rates.py --list                              # which years have a file
```

The audit prints a census:

```
| Rate nodes | Count |
| :--- | ---: |
| verified | … |
| unverified | … |
| placeholder | … |
| total | … |
```

then the placeholder keys and the unverified keys by name. `--key` prints one node with its
full provenance — value, unit, label, `verified`, `placeholder`, `source`, `as_of` and the
`note`. That is the fastest way to answer "where did this figure come from?", and it is the
command to run before quoting any figure to anybody.

## Current status of AY 2026-27

**Real figures have been landed.** The file is no longer a schema: `[meta] placeholder` is
`false` and `status` is `"landed"`, so `rates.py` opens it and `tax.py` and `vat.py` compute
against it rather than refusing outright.

`[meta] verified` remains **`false`**, deliberately, and it is not a formality. It records
that some figures rest on professional summaries rather than on enacted text. The reason is
specific and documented in the file header: the Finance Act 2026 gazette PDF is typeset in a
legacy Bijoy-family Bangla font whose glyphs map to ASCII, so its Schedules could not be
text-extracted. Where a figure was instead read from NBR's own আয়কর পরিপত্র ২০২৬-২০২৭, from
bdlaws, or from a gazetted SRO, that node carries `verified = true`.

So three populations coexist in one file, and the engine treats them differently:

- **verified nodes** — read from primary text; used without a caveat.
- **unverified nodes** — landed, but resting on a professional summary; each says why in its
  own `note`; used, with a caveat, and the output is stamped provisional.
- **placeholder nodes** — still schema; refused one by one, and named in the warnings.

Consequences you will see in day-to-day use:

- `tax.py` **runs**. Its banner says how many of the rates it used are soft, for example
  *"3 of the 16 rates used below are unverified or placeholder figures"*, and the *Rates used*
  table at the end gives the status and source of every single one.
- `vat.py` output is stamped **PROVISIONAL** even for a plain standard-rated sale, because it
  reads a wide set of reference figures and several Third Schedule reduced-rate nodes are
  still placeholders. Read the warnings block: if every key it names is irrelevant to your
  supply, the arithmetic above it still stands — but that is a judgement for you or your ITP,
  not for the tool.
- `[meta] verified = true` must **not** be set until `rates.py --all` reports zero unverified
  nodes.

Do not trust the paragraphs above over the file. Run:

```bash
python3 src/engine/rates.py --assessment-year 2026-27 --all
```

The census in the file's own header carries the same warning: the counts go stale the moment
anybody edits a node.

## Landing a real figure

This is the whole procedure, and it is also written in the file's header:

1. **Replace `value`** with the figure read from a primary source.
2. **Replace `source`** with the exact URL of that primary source — the Finance Act, the SRO,
   the NBR Paripatra, or the NBR page publishing it. Not a news article. Not a blog. Not the
   bare NBR homepage.
3. **Set `as_of`** to the ISO date on which that instrument takes effect or was published.
4. **Set `verified = true` only if you read the figure from primary text, and set
   `placeholder = false`.**
5. **Rewrite `note`** to say exactly what the figure covers and every condition attached.

If you could not confirm it from a primary source, leave `verified = false` and say **why** in
`note` — that text is shown to the end user as a warning, so write it for them.

Two failure modes to avoid, in opposite directions:

- Do not "improve" a placeholder into a verified figure because a secondary source agrees with
  it. `verified = true` is a claim about *primary text*.
- Do not leave `placeholder = true` on a node you have actually landed. A placeholder is
  *refused*; an unverified node is *used, with a caveat*. If you have a real figure from a
  professional summary, the honest state is `verified = false, placeholder = false` plus a
  `note` explaining the limitation — not a placeholder.

Then:

6. `python3 src/engine/rates.py --assessment-year <AY> --all` — the placeholder count should
   have dropped by exactly the nodes you landed, and no float error should appear.
7. `python3 -m unittest discover tests` — the tax golden cases in `tests/test_tax.py` carry
   hand-checked expected values that cite their source; if you changed a figure they depend
   on, update the expected value **and the citation** in the same commit.
8. `python3 build/build.py --check` — the bundles embed the rates file (as TOML in the skill,
   as Markdown with a fenced TOML block for ChatGPT and Gemini); the check proves they still
   fit every platform limit.

## Adding a new assessment year after a Finance Act

The procedure is designed to need no Python change at all.

### 1. Create the file

```bash
cp src/data/rates-AY2026-27.toml src/data/rates-AY2027-28.toml
```

Copying the previous year keeps every key path the engine reads and every label pair. Do
**not** delete the previous year's file: the loader can hold several years side by side, and
books configured for the old year keep working.

### 2. Reset the metadata

In `[meta]` of the new file set `assessment_year`, `income_year`, `income_year_start` and
`income_year_end`; set `status = "placeholder"`, `placeholder = true` and `verified = false`.
The new file must start life as a schema, because nothing in it has yet been read from the new
Act, and the file-level `placeholder = true` is what stops anything computing from it in the
meantime.

### 3. Mark every node as placeholder again

A figure carried over from last year is not verified for this year — every Finance Act
re-rates something. On every rate node set `verified = false` and `placeholder = true`, so
that nothing computes from the new file until someone has actually checked it. Also **rewrite
or blank the `note`**: a note that describes last year's conditions, carried into this year's
file, is exactly the kind of stale text that misleads a user who reads the caveat.

Step 6's audit is what proves you did this — the placeholder count should equal the total node
count before you start landing anything.

### 4. Land the figures

Follow *Landing a real figure* above, node by node, from the new Finance Act, the SROs, the
statute as consolidated on bdlaws and the NBR Paripatra for the new year. Read the comment
block at the head of each section first: the instruments differ (an SRO for TDS, the VAT Act
on bdlaws for VAT, NBR's Paripatra for the income tax rate card) and so do the traps each
carries.

Where the structure changed — a slab added, a reduced rate dropped, a new taxpayer category,
a withholding section inserted or repealed — change the structure: add or remove the
`[[…slabs]]` elements, add or delete `vat.rates.reduced.<key>` and `tds.sections.<n>` nodes,
and update `default_category` / `default_location` if the categories changed.

Delete schema-illustration nodes rather than leaving them as unverified: they are examples,
not rates.

### 5. Add one compliance-calendar entry

The compliance calendar reference (`src/references/compliance-calendar.md`) has one row per
obligation with what, who, the statutory due date, the primary source and the consequence of
default. Add or update the rows for the new year with their sources, and bump the file's
**Current as of** line. This is the "one calendar entry" of the specification's promise.

### 6. Audit, test, build

```bash
python3 src/engine/rates.py --list                              # both years listed
python3 src/engine/rates.py --assessment-year 2027-28 --all     # placeholder count → 0 when done
python3 src/engine/tax.py --assessment-year 2027-28 --list-options
python3 -m unittest discover tests
python3 build/build.py --check --strict
```

Add golden test cases for the new year in `tests/test_tax.py` and `tests/test_vat.py`, each
with a hand-checked expected value and its source citation. A rates file with no golden case
is a rates file nobody has exercised.

### 7. Point the books at it

Users switch years in `books/config.toml`:

```toml
[books]
assessment_year = "2027-28"
rates_file = "rates-AY2027-28.toml"
```

or per invocation with `--assessment-year 2027-28`. Because several files now exist, any
invocation that names no year and has no configured year is refused with the list of
available years — that refusal is a feature.

### 8. Update the references' "current as of"

Each `src/references/*.md` opens with **Current as of**, **Sources** and **Status**. Bump the
date on every reference whose content you re-read against the new year, and only those. A
reference you did not re-check keeps its old date, honestly.

### 9. Open the pull request

The PR must state which rates file it targets and whether any figure in it is
`verified = false`. A PR that changes a tax figure must cite the primary NBR source in the
description. Reviewers open the source and read the number; that is the review.

## Reporting a wrong figure

If a value in a rates file is wrong or outdated, open an issue using the **Tax rule update**
template (`.github/ISSUE_TEMPLATE/tax-rule-update.yml`) at
https://github.com/bemoshiur/TakaBooks/issues/new/choose. It asks for the dotted key, the
assessment year, the NBR source URL and the date you read it.

Report it **publicly** — a wrong tax figure is a correctness bug, not a security
vulnerability, and hiding it behind private disclosure would keep exactly the people it
endangers from seeing the warning.

## What not to do

- Do not write a rate, threshold, deadline or section number into prose as a statement of law
  — not in `src/core/`, not in a reference file's body, not in a wiki page, not in a
  docstring, not in a test name. The references describe mechanisms and point at the rates
  file.
- Do not hardcode a figure in Python, "just as a default". The loader has no defaults for a
  reason.
- Do not set `verified = true` on a figure you did not read from primary text yourself.
- Do not leave `placeholder = true` on a node you have landed (it stays refused), and do not
  clear it on a node you have not (it becomes silently usable).
- Do not set `[meta] verified = true` while the audit still reports unverified nodes.
- Do not delete last year's file.
- Do not quote a rate the user, or their accountant, remembers. Say what would verify it.

## See also

- The file itself, whose header is the authoritative version of this page:
  https://github.com/bemoshiur/TakaBooks/blob/main/src/data/rates-AY2026-27.toml
- The loader: https://github.com/bemoshiur/TakaBooks/blob/main/src/engine/rates.py
- Research provenance: https://github.com/bemoshiur/TakaBooks/tree/main/docs/research
- [Engine Reference](Engine-Reference) — `rates.py`, `tax.py`, `vat.py` flags
- [Contributing](Contributing) — the pull-request checklist for a rate change
- [Disclaimer](Disclaimer)
