# Engine Reference

Every script in `src/engine/`, every flag, with example invocations and what comes back. The
authoritative text is always `python3 src/engine/<script>.py --help`; this page adds the
context the help text cannot.

> The engine states no tax figure. Where an example output shows a percentage in a tax tag,
> the number is illustrative and labelled so. Statutory figures come from the rates file —
> see [Updating Tax Rates](Updating-Tax-Rates).

## Conventions shared by every script

| Convention | Detail |
| --- | --- |
| Python | **3.11 or newer**, standard library only. Below 3.11 the script prints a one-sentence explanation and exits 2 before importing anything else. |
| `--books DIR` | The books directory. Default `./books`. |
| `--json` | Machine-readable JSON on stdout instead of text. Money is emitted as decimal strings (`"11000.00"`), never as JSON floats. |
| `--version` | Prints the engine version. |
| `--help` | Full usage, in Bangla and English where a statutory term appears. |
| Exit status | **0 only when the request was satisfied and every check passed.** Any integrity failure exits non-zero with `error:` and, usually, `hint:` lines on stderr. Nothing is silently corrected. |
| Output footer | Every tax-bearing output ends with the disclaimer (not professional advice; verify with a licensed ITP/CA and against NBR) and the attribution line. |
| Reads | `config.toml`, `accounts.toml`, `journal/*.csv`, and a rates TOML. |
| Writes | Only `post.py` (appends to a journal CSV), `report.py` (CSV files under `reports/`), `vat.py` (`--out`, `--csv-out`) and `init_books.py` (the scaffold). No network, no telemetry. |

### Exit codes

The exceptions in the shared library carry stable codes, so the same failure means the same
number in every script:

| Code | Meaning | Raised for |
| ---: | --- | --- |
| 0 | OK | |
| 1 | General failure | Anything unclassified |
| 2 | Config / usage / Python version | `config.toml` missing or malformed; bad flag combination; interpreter too old |
| 3 | Account | Unknown or duplicate account code; invalid chart |
| 4 | Journal / ledger | Malformed row, bad date, duplicate `entry_id`, missing books directory |
| 5 | Unbalanced | Debits ≠ credits for an entry |
| 6 | Tax tag | `tax_tag` does not match the grammar |
| 7 | Validation findings / several problems | `validate.py` found errors (or warnings without `--allow-warnings`); `post.py` found more than one kind of problem; `vat.py --strict` found unverified figures |
| 8 | Rates | Rates file missing, malformed, placeholder (without opt-in), or lacking a required key |
| 9 | Money | A `float` was offered where money was due; an amount could not be parsed |

## `takabooks.py` — the shared library

Not a command. Every other script imports it. It owns `Money` (integer paisa), `format_bdt`
(লাখ/কোটি and international grouping), `Account` / `ChartOfAccounts`, `TaxTag`, `Posting` /
`Entry` / `Ledger`, `Config`, `RatesTable`, the exception hierarchy above, and the
Bangla/English term pairs (`term("vat")` → `মূসক / VAT`). If you write your own tooling
against the books, import this rather than parsing CSV yourself:

```python
import sys; sys.path.insert(0, "src/engine")
import takabooks as tb
ledger = tb.Ledger.load("books")          # validates as it loads; raises on a broken book
print(tb.format_bdt(ledger.total_debit))  # ৳1,13,200.00
```

The library defines no Bangladeshi rate, threshold, deadline or section number.

## `init_books.py` — scaffold a books directory

Creates `config.toml`, `accounts.toml` (হিসাব তালিকা / chart of accounts), `journal/` and
`reports/`. Statutory values are **never** guessed: `fiscal_year_start` and `assessment_year`
are written only when you pass them, otherwise they are left as commented placeholders and
every script that needs them refuses to run until you fill them in.

```
init_books.py [--books DIR] [--json] [--name TEXT] [--name-bn TEXT]
              [--business-type TEXT] [--tin TIN] [--bin BIN] [--address TEXT]
              [--fiscal-year-start MM-DD] [--assessment-year YYYY-YY] [--rates-file FILE]
              [--vat-registered {yes,no,unknown}]
              [--city-tier {unspecified,dhaka-chattogram-city,other-city,other-area}]
              [--language {en,bn,bn-en}] [--grouping {bd,international}]
              [--digits {latin,bangla}] [--start-month YYYY-MM] [--templates DIR]
              [-i] [--force] [--dry-run]
```

| Flag | Meaning |
| --- | --- |
| `--name`, `--name-bn` | Business name, and in Bangla. |
| `--business-type` | `proprietorship`, `partnership`, `company`, `ngo`, `other`. A label; it drives no figure. |
| `--tin`, `--bin` | করদাতা সনাক্তকরণ নম্বর / TIN and ব্যবসা সনাক্তকরণ নম্বর / BIN. Recorded, never validated against NBR. |
| `--fiscal-year-start MM-DD` | The day your income year opens. Required by `report.py --period FY…` and by the date-range checks in `validate.py`. |
| `--assessment-year YYYY-YY` | করবর্ষ / assessment year as printed on your return. Required by every tax output. |
| `--rates-file FILE` | Pin the rates TOML for that year. |
| `--vat-registered`, `--city-tier` | Labels recorded under `[compliance]` for your reference and the assistant's questions; **no figure is attached to them**. |
| `--language`, `--grouping`, `--digits` | `[locale]`: reply language; `bd` (12,34,567.89) or `international` (1,234,567.89) grouping; Latin or Bangla numerals in reports. |
| `--start-month YYYY-MM` | Also create an empty journal file for that month. |
| `--templates DIR` | Template directory (default `src/templates` if it exists; otherwise a built-in Bangladesh chart). |
| `-i`, `--interactive` | Ask for anything not given on the command line. |
| `--force` | Rewrite `config.toml` and `accounts.toml`. **Journal CSVs are never touched.** |
| `--dry-run` | Show what would be created and write nothing. |

Refuses (exit 2) to overwrite an existing books directory without `--force`. Exit codes: 0 ok
· 1 general · 2 config/usage · 3 account · 4 journal.

Example, and the text it prints:

```bash
python3 src/engine/init_books.py --books ./books \
  --name "Demo Traders" --name-bn "ডেমো ট্রেডার্স" --business-type proprietorship \
  --fiscal-year-start 07-01 --assessment-year 2026-27 --rates-file rates-AY2026-27.toml \
  --vat-registered yes --start-month 2026-07
```

```
TakaBooks — books ready: books
  business        Demo Traders (ডেমো ট্রেডার্স)
  হিসাব তালিকা / chart of accounts  42 accounts from built-in Bangladesh chart of accounts
  income year opens  07-01
  করবর্ষ / assessment year  2026-27
  মূসক / VAT registered  yes
  location        অনির্দিষ্ট / not stated

created:
  books/  books/journal/  books/reports/  books/config.toml  books/accounts.toml  books/journal/2026-07.csv
```

With `--json`: `ok`, `dry_run`, `books_dir`, `created`, `overwritten`, `config_file`,
`accounts_file`, `journal_dir`, `reports_dir`, `templates_dir`, `config_defaults_from`,
`accounts_from`, `accounts` (count), `roles_present`, `warnings`.

## `post.py` — record one journal entry

Validates and appends one জাবেদা / journal entry to `books/journal/YYYY-MM.csv`. Refuses — and
writes nothing — unless debits equal credits, every account exists, the date is ISO and every
`tax_tag` parses. When several things are wrong it reports all of them at once (exit 7).

```
post.py [--books DIR] [--json] [--date YYYY-MM-DD] [--id ENTRY_ID] [--description TEXT]
        [--party TEXT] [--doc-ref TEXT] [--memo TEXT]
        [--debit ACCOUNT=AMOUNT[:TAX_TAG]]... [--credit ACCOUNT=AMOUNT[:TAX_TAG]]...
        [--stdin] [--input FILE] [--dry-run]
```

| Flag | Meaning |
| --- | --- |
| `--date` | Entry date, ISO only. |
| `--id`, `--entry-id` | Your own id. Default: the next `JE-YYYY-MM-NNNN` for that month. |
| `--description` | What the entry records. |
| `--party` | Customer or supplier — a name, not an account. |
| `--doc-ref` | Voucher, চালান, Mushak 6.3 or bill number. |
| `--memo` | Free text, written last. |
| `--debit`, `--credit` | One posting line each, repeatable: `ACCOUNT=AMOUNT` with an optional `:TAX_TAG`. Amounts accept `1,00,000.00`, `৳ 500`, Bangla digits; never exponents. |
| `--stdin` | Read a JSON entry from standard input (implied by `--json` on a pipe when no `--debit/--credit` is given). |
| `--input FILE` | Read a JSON entry from a file (`-` for stdin). |
| `--dry-run` | Validate and print exactly what would be written; write nothing. |

Exit codes: 0 ok · 2 config/usage · 3 unknown or retired account · 4 date, amount or duplicate
id · 5 unbalanced · 6 tax_tag · 7 several problems at once.

Example — a sale with output VAT. The `10` is an **illustrative** number so the arithmetic is
visible; it is not a statutory rate:

```bash
python3 src/engine/post.py --books ./books --date 2026-07-05 --description "Cash sale" \
  --party "Walk-in customer" --doc-ref INV-0001 \
  --debit 1100=11000.00 --credit 4100=10000.00:VAT:OUT:10 --credit 2310=1000.00:VAT:OUT:10
```

```
posted JE-2026-07-0002 → books/journal/2026-07.csv (appended)  [entry_id generated]
  2026-07-05  Cash sale
  party Walk-in customer · doc_ref INV-0001
      account                                    ডেবিট / debit  ক্রেডিট / credit
  Dr  1100 Cash in Hand (হাতে নগদ)                  ৳11,000.00
  Cr  4100 Sales Revenue (বিক্রয় আয়)                                ৳10,000.00  VAT:OUT:10 — output মূসক / VAT at 10%
  Cr  2310 VAT Output Payable (প্রদেয় মূসক)                           ৳1,000.00  VAT:OUT:10 — output মূসক / VAT at 10%
  debits ৳11,000.00 = credits ৳11,000.00 — balanced
  tax tags: VAT:OUT:10
```

JSON entry format and the `--json` response are documented on [Journal Format](Journal-Format).
The response includes `entry_id`, `entry_id_generated`, `balanced`, `total_debit`,
`total_credit`, `postings` (with account names and tag descriptions), `rows` (the CSV cells),
`csv` (the exact text appended) and `warnings`.

## `validate.py` — whole-ledger integrity

Checks the entire খতিয়ান / ledger: config, chart, every journal file, every row. Reports every
problem it can find at once, with file, line and entry id, and exits non-zero unless the books
are clean.

```
validate.py [--books DIR] [--json] [--allow-warnings] [--quiet] [--fy-start YYYY-MM-DD] [--list-checks]
```

| Flag | Meaning |
| --- | --- |
| `--allow-warnings` | Exit 0 when only warnings remain (errors still fail). |
| `--quiet` | Print only the one-line result. |
| `--fy-start YYYY-MM-DD` | Pin the financial year for date-range checks (default: from `books.fiscal_year_start` in `config.toml`). |
| `--list-checks` | Print every check with its id and severity, then exit. |

Exit codes: 0 clean (or only warnings with `--allow-warnings`) · 7 findings reported · 2 config
problem · 4 books directory unreadable.

Findings are **errors** (the books cannot be trusted until fixed) or **warnings** (almost
always a typo or a missing declaration — review before you file). The full list, with ids,
is on [Troubleshooting](Troubleshooting); `--list-checks` prints the same list from the
script itself.

```
RESULT: clean — 8 posting(s) in 3 entry/entries, debits and credits agree at ৳1,13,200.00. (exit 0)
```

With `--json`: `ok`, `assessment_year`, `financial_year`, `journal_files`, `counts` (rows,
postings, entries, errors, warnings), `by_check`, `totals`, `date_range`, `findings` (each
with `check`, `severity`, `file`, `line`, `entry_id`, `message`, `hint`), `notes`.

## `report.py` — financial statements

রেওয়ামিল / trial balance, লাভ-ক্ষতি হিসাব / profit and loss, স্থিতিপত্র / balance sheet — all
three from **one** computation, so they cannot disagree. Markdown on stdout, CSV files in
`<books>/reports/`. Every statement is reconciled before it is printed; a statement that does
not tie is an error, not a report.

```
report.py [--books DIR] [--json] [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--period PERIOD]
          [--statement {all,trial-balance,tb,profit-and-loss,pl,balance-sheet,bs}]
          [--reports-dir DIR] [--no-csv] [--include-unused] [--grouping {bd,international}]
```

| Flag | Meaning |
| --- | --- |
| `--from`, `--to` | Inclusive reporting period. The trial balance and balance sheet are stated *as at* `--to`; the P&L covers the range. |
| `--period` | A month `YYYY-MM`, or a fiscal year `FY2026-27` / `2026-27` (reads `books.fiscal_year_start`). Not combinable with `--from/--to`. |
| `--statement` | Which statement to print (Markdown only; `--json` always carries all three). |
| `--reports-dir` | Where the CSVs go (default `<books>/reports`). |
| `--no-csv` | Print only. |
| `--include-unused` | Also list chart accounts with no postings in the period. |
| `--grouping` | Digit grouping for the Markdown (default from `locale.grouping`, normally `bd`). |

CSV names: `trial-balance_<as-at>.csv`, `profit-and-loss_<from>_<to>.csv`,
`balance-sheet_<as-at>.csv`.

The Markdown ends with a **Reconciliations performed** list — debits equal credits; assets
equal liabilities plus equity; the P&L sections cover every income and expense account; the
accumulated result ties to the ledger — each marked PASS with the figures compared. With
`--json` the keys are `period`, `trial_balance`, `profit_and_loss`, `balance_sheet`,
`reconciliations`, `csv_written`.

## `vat.py` — মূসক / VAT position

The VAT position for a period: output tax, rebateable input tax, net payable or carry-forward,
and উৎসে মূসক কর্তন / VDS withheld, with a control-account reconciliation and an input–output
tie-out per entry.

```
vat.py [--books DIR] [--json] [--period YYYY-MM] [--since YYYY-MM-DD] [--until YYYY-MM-DD]
       [--rates PATH] [--format {markdown,csv,json}] [--out PATH] [--csv-out PATH]
       [--strict] [--allow-ay-mismatch] [--all-caveats]
```

| Flag | Meaning |
| --- | --- |
| `--period` | One calendar month (a monthly return period). |
| `--since`, `--until` | Any inclusive range instead. |
| `--rates` | Rates TOML (default: `books.rates_file`, else the data directory). |
| `--format`, `--out`, `--csv-out` | Output format, and files to write. |
| `--strict` | Exit 7 if any figure is unverified, missing or does not reconcile. |
| `--allow-ay-mismatch` | Permit a rates file whose assessment year differs from `config.toml`. |
| `--all-caveats` | List every unverified figure in the rates file, not only the ones read. |

Sections of the report: return figures (with a TakaBooks `Ref` column that is **not** an NBR
form line number unless the rates file carries an explicit form map); output VAT by rate;
rebateable input VAT by rate; VDS; net position; control-account reconciliation (opening,
tagged movement, other movement, closing, for each role); input–output reconciliation; the
reference figures read from the rates file with their status; notes.

Every rate written in a `tax_tag` is checked against the rates the file declares. Anything
`PLACEHOLDER`, `UNVERIFIED` or `not in rates file` stamps the whole output **PROVISIONAL /
অস্থায়ী — not for filing**; `--strict` turns that into exit 7. Keys read are listed in
`--help`; a missing required key exits 8.

## `tax.py` — আয়কর / income tax for an individual

Progressive slabs, investment rebate, minimum tax and surcharge for an individual করদাতা /
taxpayer, with the full working shown step by step. Every figure comes from the rates file
for the assessment year; nothing is hardcoded. The corporate block of the rates file is
schema for a later module; this script computes the individual liability only.

```
tax.py [--books DIR] [--json] --income BDT [--investment BDT] [--net-wealth BDT]
       [--gross-receipts BDT] [--tax-paid BDT] [--category ID] [--location TIER]
       [--assessment-year AY] [--rates PATH] [--data-dir DIR] [--allow-placeholder-rates]
       [--language {en,bn,bn-en}] [--list-options]
```

| Flag | Meaning |
| --- | --- |
| `--income` | Total taxable income for the income year (required). |
| `--investment` | Allowable investment claimed for the rebate. |
| `--net-wealth` | Net wealth for the surcharge; omit and the surcharge is not assessed. |
| `--gross-receipts` | Gross receipts, for the minimum tax on receipts. |
| `--tax-paid` | Advance tax and TDS already paid. |
| `--category`, `--location` | Taxpayer category and minimum-tax location tier, by id from the rates file. `--list-options` prints the ids the file defines and the defaults. |
| `--assessment-year`, `--rates`, `--data-dir` | Which rates file (see the resolution order on [Updating Tax Rates](Updating-Tax-Rates)). |
| `--allow-placeholder-rates` | Compute from a placeholder file; the output is stamped PROVISIONAL and must not be filed. |
| `--language` | Add the Bangla disclaimer. |

Output: inputs table; Step 1 tax by slab (with a hand-check line: the *taxable in slab*
column sums to the income, the *tax* column to the gross tax); Step 2 investment rebate;
Step 3 minimum tax; Step 4 surcharge; summary with tax paid and net payable or refundable;
the list of every rate used with its status; caveats; disclaimer. `--json` keys: `inputs`,
`threshold`, `slabs`, `gross_tax`, `rebate`, `minimum_tax`, `surcharge`, `summary`,
`rates_used`, `caveats`, `warnings`, `provisional`, `disclaimer`.

Without the opt-in, a placeholder rates file is refused:

```
error: rates-AY2026-27.toml is a schema awaiting verified data — every figure in it is a placeholder.
  hint: … pass --allow-placeholder-rates to compute a clearly-marked PROVISIONAL result that must never be filed.
```

## `rates.py` — inspect and audit a rates file

```
rates.py [--data-dir DIR] [--assessment-year AY] [--rates PATH] [--list] [--key DOTTED.KEY]
         [--all] [--allow-placeholder-rates] [--json]
```

| Flag | Meaning |
| --- | --- |
| `--list` | The assessment years for which a rates file exists, with paths. |
| (no `--key`) | An audit: counts of verified, unverified and placeholder nodes, and the first 15 keys of each (`--all` for every key). |
| `--key` | One node with its full provenance: value, unit, label, verified, placeholder, source, as-of, note, caveat. Refused (exit 8) for a placeholder node without `--allow-placeholder-rates`. |

This is also the library every other script uses to load a rates file, so what it reports is
what they compute from.

## `build/build.py` — the bundles

Not part of the engine, but you will meet it: it emits every platform bundle in `dist/` from
`src/` and regenerates the root `AGENTS.md`. `--check` assembles everything and verifies
every platform limit without writing; `--target` picks a bundle; `--clean` wipes `dist/`
first; `--strict` fails on a missing expected source file. See [Contributing](Contributing).

## `bin/takabooks.mjs` — the installer

A Node script that copies a built bundle to where a platform expects it. Documented on
[Installation](Installation).

## See also

- [Getting Started](Getting-Started) — the scripts in order, on a fresh set of books
- [Journal Format](Journal-Format) · [Chart of Accounts](Chart-of-Accounts)
- [Troubleshooting](Troubleshooting) — every error message, what caused it, what to do
- [Disclaimer](Disclaimer)
