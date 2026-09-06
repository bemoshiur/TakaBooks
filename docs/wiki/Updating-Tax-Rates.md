# Updating Tax Rates — করহার হালনাগাদ

This is the most important maintenance page in the wiki. It explains how the versioned rates
file works, what the engine does with a verified, an unverified and a placeholder figure, and
the exact procedure for adding a new করবর্ষ / assessment year after a Finance Act.

> This page contains **no** rate, threshold or deadline, on purpose. It documents the
> mechanism. Every figure lives in `src/data/rates-AY<year>.toml` with a `source` URL and a
> `verified` flag, and nowhere else.

## Why a rates file

The design rule (specification §4.5): **no rate is ever hardcoded in prose or in code.** Every
figure — slabs, thresholds, rebate caps, VAT rates, withholding rates, filing and deposit
deadlines, policy switches — lives in one TOML file per assessment year, and each figure
carries:

- the `source` URL of the **primary** document it was read from,
- the `as_of` date on which it was read,
- a `verified` boolean,
- while the schema is unpopulated, a `placeholder = true` marker.

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

### `[meta]`

```toml
[meta]
assessment_year = "2026-27"
income_year = ""              # the income year this AY assesses
currency = "BDT"
schema_version = 1
status = "placeholder"        # placeholder | partial | verified (free text, for humans)
placeholder = true            # rates.py reads this: the WHOLE FILE is unlanded data
verified = false
authority = "National Board of Revenue (NBR), Bangladesh — জাতীয় রাজস্ব বোর্ড"
authority_url = "https://nbr.gov.bd/"
maintainer = "…"
```

`meta.placeholder = true` marks the entire file as a schema awaiting research. While it is
set, every consumer refuses to compute unless the caller opts in, and then stamps the output
PROVISIONAL. Delete the line — do not set it to `false` — once real figures have landed.

### A rate node

A **rate node** is any table that carries a `value` key. Everything else is structure or
metadata and is not audited. The shape:

```toml
  [vat.rates.standard]
  label_en = "Standard VAT rate"
  label_bn = "প্রমিত মূসক হার"
  value = 0                    # placeholder until landed
  unit = "percent"
  source = "https://nbr.gov.bd/"
  as_of = ""
  verified = false
  placeholder = true
  note = "PLACEHOLDER — standard মূসক / VAT rate is not verified."
```

| Key | Meaning |
| --- | --- |
| `value` | The figure. A whole-taka amount as an integer; anything with decimals as a **quoted string**; a date or policy as text. |
| `unit` | Free text; the file uses `percent`, `BDT`, `date`, `policy`, `count`. `percent` nodes are checked: a value above 100 is rejected as a fraction/percent mix-up. |
| `source` | The exact URL of the primary source — the Finance Act, the SRO, the NBR circular (পরিপত্র), or the NBR page that publishes it. Not a news article, not a blog, not a summary. |
| `as_of` | ISO date (`YYYY-MM-DD`) on which the source was read. |
| `verified` | `true` only when the value was read from `source` on `as_of`. Absent counts as `false`. |
| `placeholder` | `true` while the node is schema, not data. **Delete the line** when landing a figure. |
| `note` | What the figure covers and every condition attached. Rewrite it when the value changes. |
| `label_en`, `label_bn` | Display labels. Extra descriptive keys (`applies_to`, `condition`, `allowed`, `deducted_by`, …) are always permitted and preserved for display. |

Lists of nodes (`[[income_tax.individual.slabs]]`, `[[income_tax.individual.surcharge.bands]]`)
are arrays of tables; each element may nest its own rate nodes (a slab has a `rate` node and
a width). The file header lists every dotted key each engine module reads, so you can see
exactly what a change touches.

### Format rules the loader enforces

These are not conventions; `src/engine/rates.py` raises on violation.

- **Never write a bare TOML float.** `0.5` becomes a binary float, and TakaBooks refuses
  float money. Write `"0.5"`. Any float in a rate node is a `RatesError`.
- **Money is in taka, never paisa.** `123456` or `"123456.50"`. The loader converts to
  integer paisa.
- **Percentages are percent, not fractions.** `10` means ten percent.
- **A missing key is an error, never a default.** There is no `get(key, default)` in the
  loader. A consumer that needs an optional node asks for it by name and says "absent" out
  loud instead of substituting a number.
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
| **Verified** | `verified = true`, no `placeholder` | Used normally. Provenance line printed. |
| **Unverified** | `verified = false` or absent | Used, but the output carries an `UNVERIFIED: <key> …` caveat naming the key and file, and `vat.py --strict` exits non-zero. The assistant must label the figure UNVERIFIED, show `source` and `as_of`, and tell the user to confirm with NBR. |
| **Placeholder** | `placeholder = true` on the node or in `[meta]` | **Refused** (exit 8) unless the caller passes `--allow-placeholder-rates`; then computed, with every result stamped **PROVISIONAL / অস্থায়ী — NOT FOR FILING** and a `PLACEHOLDER: <key> …` caveat per figure. |
| **Absent** | No node at that key | Refused (exit 8) with the key named. Optional keys are reported as `not in rates file`. |

`rates.py` audits a file and counts nodes by state:

```bash
python3 src/engine/rates.py --assessment-year 2026-27          # audit: verified / unverified / placeholder counts
python3 src/engine/rates.py --assessment-year 2026-27 --all    # list every unverified key
python3 src/engine/rates.py --assessment-year 2026-27 --key vat.rates.standard --allow-placeholder-rates
```

The last command prints one node with its full provenance (value, unit, label, verified,
placeholder, source, as-of, note) — the fastest way to answer "where did this figure come
from?".

## Current status

At the time of writing, `rates-AY2026-27.toml` is a **complete schema with no real figure in
it**: every node is a placeholder, and `[meta] placeholder = true`. A separate research pass
is landing verified values from primary sources, with an adversarial review, before any
figure enters the file. Until then, `tax.py` and `vat.py` produce PROVISIONAL walkthroughs of
the method only. Do not trust this paragraph over the file: run the audit above and read the
`[meta]` table — the file is always the authority on its own state.

## Landing a real figure

This is the whole procedure, and it is also written in the file's header:

1. **Replace `value`** with the figure read from a primary source.
2. **Replace `source`** with the exact URL of that primary source — the Finance Act, the SRO,
   the NBR circular, or the NBR page publishing it.
3. **Set `as_of`** to the ISO date on which you read that source.
4. **Set `verified = true` and delete the `placeholder = true` line.**
5. **Rewrite `note`** to say exactly what the figure covers and every condition attached.

If you could not confirm it from a primary source, leave `verified = false` and say so in
`note`. Do not "improve" a placeholder into an unverified guess — an unverified node is
*used*, with a caveat; a placeholder is *refused*. Only promote a node when you have the
source in front of you.

Then:

6. `python3 src/engine/rates.py --assessment-year <AY>` — the count of placeholders should
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

In `[meta]` of the new file set `assessment_year`, set `income_year`, set
`status = "placeholder"`, set `placeholder = true` and `verified = false`. The new file must
start life as a schema, because nothing in it has yet been read from the new Act.

### 3. Mark every node as placeholder again

A figure carried over from last year is not verified for this year — every Finance Act
re-rates something. On every rate node set `verified = false` and add `placeholder = true`
back, so that nothing computes from the new file until someone has actually checked it.
(A short script or a careful editor search does this; the audit in step 6 proves it.)

### 4. Land the figures

Follow *Landing a real figure* above, node by node, from the new Finance Act, the SROs and
the NBR circular for the new year. Where the structure changed — a slab added, a reduced
rate dropped, a new taxpayer category — change the structure: add or remove the
`[[…slabs]]` elements, add or delete `vat.rates.reduced.<key>` nodes, and update
`default_category` / `default_location` if the categories changed. The file header documents
what each module reads, so you can see what a structural change affects.

Delete placeholder example nodes (`placeholder_supply`, `placeholder_service`,
`placeholder_sector`) rather than leaving them as unverified: they are schema illustrations,
not rates.

### 5. Add one compliance-calendar entry

The compliance calendar reference (`src/references/compliance-calendar.md`) has one row per
obligation with what, who, the statutory due date, the primary source and the consequence of
default. Add or update the rows for the new year with their sources, and bump the file's
**Current as of** line. This is the "one calendar entry" of the specification's promise.

### 6. Audit, test, build

```bash
python3 src/engine/rates.py --list                              # both years listed
python3 src/engine/rates.py --assessment-year 2027-28           # placeholder count → 0 when done
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

If a value in a rates file is wrong or outdated, open an issue with the **rate correction**
template at https://github.com/bemoshiur/TakaBooks/issues/new/choose. It asks for the dotted
key, the assessment year, the NBR source URL and the date you read it. Report it **publicly**
— a wrong tax figure is a correctness bug, not a security vulnerability, and hiding it behind
private disclosure would keep exactly the people it endangers from seeing the warning.

## What not to do

- Do not write a rate, threshold, deadline or section number into prose — not in
  `src/core/`, not in a reference file's body, not in a wiki page, not in a docstring, not in
  a test name. The references describe mechanisms and point at the rates file.
- Do not hardcode a figure in Python, "just as a default". The loader has no defaults for a
  reason.
- Do not set `verified = true` on a figure you did not read from the cited source yourself.
- Do not leave `placeholder = true` on a node you have landed (it stays refused), and do not
  delete it from a node you have not (it becomes silently usable).
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
