# Engine Reference

Every script in `src/engine/`, every flag, with example invocations and what comes back. The
authoritative text is always `python3 src/engine/<script>.py --help`; this page adds the
context the help text cannot. Every usage block below is the real `--help` synopsis, and every
output block was produced by running the command shown.

> The engine states no tax figure. Where an example output carries a percentage, it is a
> percentage the engine **read out of the rates file** for assessment year 2026-27, not a
> figure this page asserts. Run `rates.py --key <dotted.key>` to see any of them with its
> source URL and `verified` flag — see [Updating Tax Rates](Updating-Tax-Rates).

## Conventions shared by every script

| Convention | Detail |
| --- | --- |
| Python | **3.11 or newer**, standard library only. Below 3.11 the script prints a one-sentence explanation and exits 2 before importing anything else. |
| `--books DIR` | The books directory. Default `./books`. |
| `--json` | Machine-readable JSON on stdout instead of text. Money is emitted as decimal strings (`"11000.00"`), never as JSON floats. |
| `--version` | Prints the engine version — `TakaBooks 0.1.0` from every script, because they all report `takabooks.__version__`. |
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
| 3 | Account | Unknown, duplicate or **retired** account code; invalid chart |
| 4 | Journal / ledger | Malformed row, bad date, duplicate `entry_id`, missing books directory |
| 5 | Unbalanced | Debits ≠ credits for an entry |
| 6 | Tax tag | `tax_tag` does not match the grammar |
| 7 | Validation findings / several problems | `validate.py` found errors (or warnings without `--allow-warnings`); `post.py` found more than one kind of problem; `vat.py --strict` found unverified figures |
| 8 | Rates | Rates file missing, malformed, placeholder (without opt-in), or lacking a required key |
| 9 | Money | A `float` was offered where money was due; an amount could not be parsed |

## `takabooks.py` — the shared library

Not a command you run against books, though `python3 src/engine/takabooks.py --version` does
print a version banner. Every other script imports it. It owns `Money` (integer paisa),
`format_bdt` (লাখ/কোটি and international grouping), `Account` / `ChartOfAccounts`, `TaxTag`,
`Posting` / `Entry` / `Ledger`, `Config`, `RatesTable`, the exception hierarchy above, and the
Bangla/English term pairs (`term("vat")` → `মূসক / VAT`). If you write your own tooling
against the books, import this rather than parsing CSV yourself:

```python
import sys; sys.path.insert(0, "src/engine")
import takabooks as tb
ledger = tb.Ledger.load("books")          # validates as it loads; raises on a broken book
print(tb.format_bdt(ledger.total_debit))  # ৳11,00,000.00
```

The library defines no Bangladeshi rate, threshold, deadline or section number. It does define
`REQUIRED_ROLES` — the ten roles a complete chart must carry — and `ACCOUNT_BLOCKS`, the
`1xxx`–`9xxx` convention.

## `init_books.py` — scaffold a books directory

Creates `config.toml`, `accounts.toml` (হিসাব তালিকা / chart of accounts), `journal/` and
`reports/`. Statutory values are **never** guessed: `fiscal_year_start` and `assessment_year`
are written only when you pass them, and every script that needs them refuses to run until
you fill them in.

```
init_books.py [-h] [--books DIR] [--json] [--version] [--name TEXT]
              [--name-bn TEXT] [--business-type TEXT] [--tin TIN]
              [--bin BIN] [--address TEXT] [--fiscal-year-start MM-DD]
              [--assessment-year YYYY-YY] [--rates-file FILE]
              [--vat-registered {yes,no,unknown}]
              [--city-tier {unspecified,dhaka-chattogram-city,other-city,other-area}]
              [--language {en,bn,bn-en}]
              [--grouping {bd,international}] [--digits {latin,bangla}]
              [--start-month YYYY-MM] [--templates DIR] [-i] [--force]
              [--dry-run]
```

| Flag | Meaning |
| --- | --- |
| `--name`, `--name-bn` | Business name, and in Bangla. |
| `--business-type` | `proprietorship`, `partnership`, `company`, `ngo`, `other`. A label; it drives no figure. |
| `--tin`, `--bin` | করদাতা সনাক্তকরণ নম্বর / TIN and ব্যবসা সনাক্তকরণ নম্বর / BIN. Recorded, never validated against NBR. |
| `--address` | Business address, recorded under `[business]`. |
| `--fiscal-year-start MM-DD` | The day your income year opens. Required by `report.py --period FY…` and by the date-range checks in `validate.py`. |
| `--assessment-year YYYY-YY` | করবর্ষ / assessment year as printed on your return. Required by every tax output. |
| `--rates-file FILE` | Pin the rates TOML for that year. |
| `--vat-registered`, `--city-tier` | Labels recorded for your reference and the assistant's questions; **no figure is attached to them**. Note that `--city-tier` is a label only — the location basis for minimum tax is not something this flag decides. |
| `--language`, `--grouping`, `--digits` | `[locale]`: reply language; `bd` (12,34,567.89) or `international` (1,234,567.89) grouping; Latin or Bangla numerals in reports. |
| `--start-month YYYY-MM` | Also create an empty journal file for that month. |
| `--templates DIR` | Template directory. Defaults to `src/templates` resolved beside the script; if that directory is missing, a 42-account chart embedded in the script is used instead (see [Chart of Accounts](Chart-of-Accounts)). |
| `-i`, `--interactive` | Ask for anything not given on the command line. |
| `--force` | Rewrite `config.toml` and `accounts.toml`. **Journal CSVs are never touched.** |
| `--dry-run` | Show what would be created and write nothing. |

Refuses to overwrite an existing books directory without `--force`. Exit codes: 0 ok · 1
general · 2 config/usage · 3 account · 4 journal.

Example, and the text it prints:

```bash
python3 src/engine/init_books.py --books books \
  --name "Rahman Traders" --name-bn "রহমান ট্রেডার্স" --business-type proprietorship \
  --fiscal-year-start 07-01 --assessment-year 2026-27 --rates-file rates-AY2026-27.toml \
  --vat-registered yes --start-month 2026-07
```

```
TakaBooks — books ready: books
  business        Rahman Traders (রহমান ট্রেডার্স)
  হিসাব তালিকা / chart of accounts  131 accounts from /path/to/TakaBooks/src/templates/accounts.toml
  income year opens  07-01
  করবর্ষ / assessment year  2026-27
  মূসক / VAT registered  yes
  location        অনির্দিষ্ট / not stated

created:
  books/
  books/journal/
  books/reports/
  books/config.toml
  books/accounts.toml
  books/journal/2026-07.csv
```

**131 accounts** is the chart that ships in `src/templates/accounts.toml`. The template path
is printed absolute; `/path/to/TakaBooks` above stands in for your checkout.

With `--json`: `ok`, `dry_run`, `books_dir`, `created`, `overwritten`, `config_file`,
`accounts_file`, `journal_dir`, `reports_dir`, `templates_dir`, `config_defaults_from`,
`accounts_from`, `accounts` (count), `roles_present`, `missing_roles`, `fiscal_year_start`,
`assessment_year`, `vat_registered`, `city_tier`, `business_name`, `warnings`, `attribution`,
`config_preview`, `accounts_preview_lines`.

## `post.py` — record one journal entry

Validates and appends one জাবেদা / journal entry to `books/journal/YYYY-MM.csv`. Refuses — and
writes nothing — unless debits equal credits, every account exists and is not retired, the
date is ISO and every `tax_tag` parses. When several things are wrong it reports all of them
at once (exit 7).

```
post.py [-h] [--books DIR] [--json] [--version] [--date YYYY-MM-DD]
        [--id ENTRY_ID] [--description TEXT] [--party TEXT]
        [--doc-ref TEXT] [--memo TEXT]
        [--debit ACCOUNT=AMOUNT[:TAX_TAG]]
        [--credit ACCOUNT=AMOUNT[:TAX_TAG]] [--stdin] [--input FILE]
        [--dry-run]
```

| Flag | Meaning |
| --- | --- |
| `--date` | Entry date, ISO only. |
| `--id`, `--entry-id` | Your own id. Default: the next `JE-YYYY-MM-NNNN` for that month. |
| `--description` | What the entry records. |
| `--party` | Customer or supplier — a name, not an account. |
| `--doc-ref` | Voucher, চালান, Mushak 6.3 or bill number. |
| `--memo` | Free text, written last. |
| `--debit`, `--credit` | One posting line each, repeatable: `ACCOUNT=AMOUNT` with an optional `:TAX_TAG`. Amounts accept `1,00,000.00`, `৳ 500`, Bangla digits; never exponents, never floats. |
| `--stdin` | Read a JSON entry from standard input (implied by `--json` on a pipe when no `--debit/--credit` is given). |
| `--input FILE` | Read a JSON entry from a file (`-` for stdin). |
| `--dry-run` | Validate and print exactly what would be written; write nothing. |

Exit codes: 0 ok · 2 config/usage · 3 unknown or retired account · 4 date, amount or duplicate
id · 5 unbalanced · 6 tax_tag · 7 several problems at once.

Example — a sale with output VAT, tagged at the rate the rates file declares for a standard
supply:

```bash
python3 src/engine/post.py --books books --date 2026-07-12 \
  --description "Cash sale with output VAT" \
  --party "Walk-in customer" --doc-ref MUSHAK-6.3/RT/0007 \
  --debit 1150=345000.00 --credit 4100=300000.00:VAT:OUT:15 --credit 9200=45000.00:VAT:OUT:15
```

```
posted JE-2026-07-0002 → books/journal/2026-07.csv (appended)  [entry_id generated]
  2026-07-12  Cash sale with output VAT
  party Walk-in customer · doc_ref MUSHAK-6.3/RT/0007
      account                                                       ডেবিট / debit  ক্রেডিট / credit
  Dr  1150 Cash at Bank — Current Account (ব্যাংক হিসাব — চলতি)      ৳3,45,000.00
  Cr  4100 Sales — Local (বিক্রয় — স্থানীয়)                                          ৳3,00,000.00  VAT:OUT:15 — output মূসক / VAT at 15%
  Cr  9200 VAT Output Payable (প্রদেয় উৎপাদ কর (মূসক))                                  ৳45,000.00  VAT:OUT:15 — output মূসক / VAT at 15%
  debits ৳3,45,000.00 = credits ৳3,45,000.00 — balanced
  tax tags: VAT:OUT:15
```

`9200` is the account carrying `role = "vat_output"` in the shipped chart. The engine finds
the control account by its role, not by its number.

Two refusals worth seeing once:

```bash
python3 src/engine/post.py --books books --date 2026-07-18 --description "Cash sale" \
  --debit 1100=11500.00 --credit 4100=10000.00 --credit 2310=1500.00:VAT:OUT:15
```

```
error: --credit #3: account code '2310' is not in accounts.toml.
  hint: Did you mean 2300 Loan from Directors / Proprietor (পরিচালক/মালিকের নিকট হইতে ঋণ), 2230 Lease / Hire-purchase Liability (ইজারা ও কিস্তি-ক্রয় দায়), 2220 Long-term Loan (দীর্ঘমেয়াদি ঋণ)? Add the account to accounts.toml or use an existing code; TakaBooks never posts to an account it cannot name.
```

(exit 3 — near matches are suggested, nothing is guessed), and:

```
error: Entry 'JE-2026-07-0002' dated 2026-07-01 does not balance: debits ৳100.00 vs credits ৳90.00; ৳10.00 too much debit
  hint: Every entry must have equal debits and credits. TakaBooks never adjusts your numbers for you.
```

(exit 5).

JSON entry format is documented on [Journal Format](Journal-Format). The `--json` response
carries `ok`, `dry_run`, `books_dir`, `business`, `file`, `month`, `created_file`, `entry_id`,
`entry_id_generated`, `date`, `description`, `party`, `doc_ref`, `memo`, `lines`,
`total_debit`, `total_credit`, `total_debit_formatted`, `total_credit_formatted`, `balanced`,
`postings` (with account names and tag descriptions), `rows` (the CSV cells), `csv` (the exact
text appended), `tax_tags`, `source`, `warnings` and `attribution`.

## `validate.py` — whole-ledger integrity

Checks the entire খতিয়ান / ledger: config, chart, every journal file, every row. Reports every
problem it can find at once, with file, line and entry id, and exits non-zero unless the books
are clean.

```
validate.py [-h] [--books DIR] [--json] [--version] [--allow-warnings]
            [--quiet] [--fy-start YYYY-MM-DD] [--list-checks]
```

| Flag | Meaning |
| --- | --- |
| `--allow-warnings` | Exit 0 when only warnings remain (errors still fail). |
| `--quiet` | Print only the one-line result (text output only). |
| `--fy-start YYYY-MM-DD` | Pin the financial year for date-range checks (default: from `books.fiscal_year_start` in `config.toml`). |
| `--list-checks` | Print every check with its id and severity, then exit. |

Exit codes: 0 clean (or only warnings with `--allow-warnings`) · 7 findings reported · 2 config
problem · 4 books directory unreadable.

Findings are **errors** (the books cannot be trusted until fixed) or **warnings** (almost
always a typo or a missing declaration — review before you file). `--list-checks` prints the
list from the script itself; it opens:

```
TakaBooks validate.py — checks performed (খতিয়ান যাচাই / ledger validation)
------------------------------------------------------------------------------
ERRORS
  config-unreadable            books/config.toml is missing or invalid
  accounts-unreadable          accounts.toml is missing, invalid, or has duplicate codes
  journal-missing              the journal directory does not exist
  journal-unreadable           a journal file could not be read (encoding or permissions)
  journal-header               a journal file has a missing or wrong header row
  row-fields                   a row has fewer columns than the journal schema needs
  row-invalid                  a row was rejected by the journal schema
  bad-date                     the date is not a strict ISO YYYY-MM-DD calendar date
  missing-entry-id             entry_id is blank, so the row belongs to no entry
  missing-account              the account code cell is blank
  bad-amount                   a debit/credit cell is not a readable amount
  negative-amount              a debit or credit is negative; reverse the sides instead
  both-sides                   debit and credit are both non-zero on one row
  no-amount                    neither debit nor credit is set on the row
  bad-tax-tag                  the tax_tag cell does not match the tax_tag grammar
  unknown-account              the account code is not in accounts.toml
  tax-tag-account-mismatch     a tax tag sits on the control account of a different tax
```

A clean run:

```
==============================================================================
RESULT: clean — 11 posting(s) in 4 entry/entries, debits and credits agree at ৳11,00,000.00. (exit 0)
```

With `--json`: `ok`, `tool`, `takabooks_version`, `books`, `business`, `assessment_year`,
`financial_year`, `journal_files`, `counts` (rows, postings, entries, errors, warnings),
`by_check`, `totals`, `date_range`, `findings` (each with `check`, `severity`, `file`, `line`,
`entry_id`, `message`, `hint`), `notes`, `summary`, `exit_code`, `attribution`, `disclaimer`.

## `report.py` — financial statements

রেওয়ামিল / trial balance, লাভ-ক্ষতি হিসাব / profit and loss, স্থিতিপত্র / balance sheet — all
three from **one** computation, so they cannot disagree. Markdown on stdout, CSV files in
`<books>/reports/`. Every statement is reconciled before it is printed; a statement that does
not tie is an error, not a report.

```
report.py [-h] [--books DIR] [--json] [--version] [--from YYYY-MM-DD]
          [--to YYYY-MM-DD] [--period PERIOD]
          [--statement {all,trial-balance,tb,profit-and-loss,pl,balance-sheet,bs}]
          [--reports-dir DIR] [--no-csv] [--include-unused]
          [--grouping {bd,international}]
```

| Flag | Meaning |
| --- | --- |
| `--from`, `--to` | Inclusive reporting period. The trial balance and balance sheet are stated *as at* `--to`; the P&L covers the range. |
| `--period` | A month `YYYY-MM`, or a fiscal year `FY2026-27` / `2026-27` (reads `books.fiscal_year_start`). Not combinable with `--from/--to`. |
| `--statement` | Which statement to print (Markdown only; `--json` always carries all three). |
| `--reports-dir` | Where the CSVs go (default `<books>/reports`). |
| `--no-csv` | Print only; write no CSV. |
| `--include-unused` | Also list chart accounts with no postings in the period. |
| `--grouping` | Digit grouping for the Markdown (default from `locale.grouping`, normally `bd`). |

CSV names, as actually written:

```
books/reports/trial-balance_2026-07-31.csv
books/reports/profit-and-loss_2026-07-01_2026-07-31.csv
books/reports/balance-sheet_2026-07-31.csv
```

The Markdown ends with a **Reconciliations performed** list, each marked PASS with the figures
compared:

```
- **PASS** `trial_balance_debits_equal_credits` — total debits ৳11,00,000.00 vs total credits ৳11,00,000.00 — difference ৳0.00
- **PASS** `balance_sheet_assets_equal_liabilities_plus_equity` — assets ৳8,52,500.00 vs liabilities ৳2,77,500.00 + equity ৳5,75,000.00 — difference ৳0.00
- **PASS** `profit_and_loss_sections_cover_every_income_and_expense_account` — net profit from the sections ৳75,000.00 vs income less expenses straight from the ledger ৳75,000.00
- **PASS** `accumulated_result_ties_to_the_ledger` — brought forward ৳0.00 + period ৳75,000.00 = ৳75,000.00 vs cumulative income less expenses ৳75,000.00
```

With `--json` the keys are `ok`, `project`, `version`, `books`, `business`,
`assessment_year`, `period`, `trial_balance`, `profit_and_loss`, `balance_sheet`, `checks`,
`files`, `attribution`, `disclaimer_en`, `disclaimer_bn`.

## `vat.py` — মূসক / VAT position

The VAT position for a period: output tax, rebateable input tax, net payable or carry-forward,
and উৎসে মূসক কর্তন / VDS withheld, with a control-account reconciliation and an input–output
tie-out per entry.

```
vat.py [-h] [--books DIR] [--json] [--version] [--period YYYY-MM]
       [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--rates PATH]
       [--format {markdown,csv,json}] [--out PATH] [--csv-out PATH]
       [--strict] [--allow-ay-mismatch] [--all-caveats]
```

| Flag | Meaning |
| --- | --- |
| `--period` | One calendar month — a tax period. This is a period selector, **not** a claim about how often you must file. |
| `--since`, `--until` | Any inclusive range instead. |
| `--rates` | Rates TOML (default: `books.rates_file`, else the data directory). |
| `--format`, `--out`, `--csv-out` | Output format, and files to write. `--json` is equivalent to `--format json`. |
| `--strict` | Exit 7 if any figure is unverified, missing or does not reconcile. |
| `--allow-ay-mismatch` | Permit a rates file whose assessment year differs from `config.toml`. |
| `--all-caveats` | List every unverified figure in the rates file, not only the ones read here. |

The report has nine numbered sections: return figures; output VAT by rate; rebateable input
VAT by rate; VDS; net position; control-account reconciliation (opening, tagged movement,
other movement, closing, per role); input–output reconciliation; the reference figures read
from the rates file with their status; notes. A সতর্কতা / Warnings block precedes them
whenever anything is flagged.

The `Ref` column in the return figures is a **TakaBooks** reference, not an NBR form line
number, unless the rates file carries an explicit `[[vat.return_form.line]]` map.

Every rate written in a `tax_tag` is checked against the rates the file declares; a tagged
rate the file does not declare is flagged. Anything `PLACEHOLDER`, `UNVERIFIED` or `not in
rates file` stamps the whole output **PROVISIONAL / অস্থায়ী — not for filing**, and `--strict`
turns that into exit 7. Keys read are listed in `--help`; a missing **required** key exits 8,
while a missing optional key is reported as "not in rates file" rather than defaulted.

With `--json`: `ok`, `tool`, `project`, `version`, `attribution`, `business`, `books_dir`,
`assessment_year`, `period`, `filing_status`, `provisional`, `rates`, `counts`, `figures`,
`output`, `input`, `vds`, `net`, `control_accounts`, `reconciliation`, `reference_figures`,
`declared_rates`, `return_form`, `warnings`, `notes`, `disclaimer_en`, `disclaimer_bn`.

## `tax.py` — আয়কর / income tax for an individual

Progressive slabs, investment rebate, minimum tax and surcharge for an individual করদাতা /
taxpayer, with the full working shown step by step. Every figure comes from the rates file
for the assessment year; nothing is hardcoded. The corporate block of the rates file is
schema for a later module; this script computes the individual liability only.

```
tax.py [-h] [--books DIR] [--json] [--version] [--income BDT]
       [--investment BDT] [--net-wealth BDT] [--gross-receipts BDT]
       [--tax-paid BDT] [--category ID] [--location TIER]
       [--assessment-year AY] [--rates PATH] [--data-dir DIR]
       [--allow-placeholder-rates] [--language {en,bn,bn-en}]
       [--list-options]
```

| Flag | Meaning |
| --- | --- |
| `--income` | Total taxable income for the income year (required for a computation). |
| `--investment` | Allowable investment claimed for the rebate (default 0). |
| `--net-wealth` | Net wealth for the surcharge. **Omit and the surcharge is not assessed** — it is not assumed to be zero, and the output says so. |
| `--gross-receipts` | Gross receipts, for the minimum tax on receipts. Omitted means not assessed. |
| `--tax-paid` | Advance tax and TDS already paid (default 0). |
| `--category`, `--location` | Taxpayer category and minimum-tax location tier, by id from the rates file. |
| `--assessment-year`, `--rates`, `--data-dir` | Which rates file (see the resolution order on [Updating Tax Rates](Updating-Tax-Rates)). |
| `--allow-placeholder-rates` | Compute from a placeholder file; the output is stamped PROVISIONAL and must not be filed. |
| `--language` | Add the Bangla disclaimer (`bn`, `bn-en`). |
| `--list-options` | List the taxpayer categories and location tiers the rates file defines, then exit. |

`--list-options` is the honest way to discover what the file supports, rather than assuming a
category exists:

```bash
python3 src/engine/tax.py --books books --list-options
```

```
Taxpayer categories / করদাতার শ্রেণি (--category):
  general                                          সাধারণ করদাতা / General taxpayer
  female                                           নারী করদাতা / Female taxpayer
  senior_citizen                                   প্রবীণ নাগরিক (৬৫ বছর বা তদূর্ধ্ব) / Senior citizen
  person_with_disability                           প্রতিবন্ধী ব্যক্তি / Person with disability
  third_gender                                     তৃতীয় লিঙ্গের করদাতা / Third gender taxpayer
  gazetted_war_wounded_freedom_fighter             গেজেটভুক্ত যুদ্ধাহত মুক্তিযোদ্ধা / Gazetted war-wounded freedom fighter
  gazetted_july_fighter                            গেজেটভুক্ত জুলাই যোদ্ধা (জুলাই গণঅভ্যুত্থান ২০২৪-এ আহত) / Gazetted July fighter (injured in the July 2024 uprising)
  parent_or_guardian_of_person_with_disability     একজন প্রতিবন্ধী ব্যক্তির পিতা-মাতা বা আইনানুগ অভিভাবক (সাধারণ করদাতা) / General taxpayer who is parent or legal guardian of ONE person with disability

Location tiers / এলাকা (--location):
  all_areas                                        বাংলাদেশের যেকোনো এলাকা (এলাকাভিত্তিক বিভাজন বিলুপ্ত) / Any area of Bangladesh (the location split is abolished)
  new_taxpayer                                     নতুন করদাতা (যেকোনো এলাকা) / New / first-time taxpayer (any area)

Defaults: --category general --location all_areas
```

Output of a computation: inputs table; Step 1 tax by slab (with a hand-check line — the
*taxable in slab* column sums to the income, the *tax* column to the gross tax); Step 2
investment rebate showing each cap; Step 3 minimum tax; Step 4 surcharge; Step 5 summary with
tax paid and net payable; then **Rates used**, a table of every key the computation touched
with its value, unit, `verified` status, `as_of` date and source URL; then **Caveats**, naming
each unverified key; then the disclaimer.

The banner at the top states exactly how much of the answer is soft, and is careful to
separate the arithmetic from the figures:

```
> **PROVISIONAL / অস্থায়ী — NOT FOR FILING.**  3 of the 16 rates used below are not confirmed against a primary NBR source. The arithmetic is right; the figures it rests on are not yet final. See *Caveats* at the end.
```

A rates **file** declaring itself a placeholder (`[meta] placeholder = true`) is refused
outright with exit 8 unless `--allow-placeholder-rates` is passed. The AY 2026-27 file no
longer declares itself a placeholder, so `tax.py` runs against it — the banner above reflects
individual nodes, not the whole file.

`--json` keys: `ok`, `tool`, `version`, `assessment_year`, `rates_source`, `rates_file`,
`provisional`, `currency`, `amounts`, `taxpayer`, `inputs`, `threshold`, `slabs`, `gross_tax`,
`rebate`, `minimum_tax`, `surcharge`, `summary`, `rates_used`, `caveats`, `warnings`,
`disclaimer`, `attribution`.

## `rates.py` — inspect and audit a rates file

```
rates.py [-h] [--books DIR] [--json] [--version] [--data-dir DIR]
         [--assessment-year AY] [--rates PATH] [--list]
         [--key DOTTED.KEY] [--all] [--allow-placeholder-rates]
```

| Flag | Meaning |
| --- | --- |
| `--list` | The assessment years for which a rates file exists, with paths. |
| (no `--key`) | An audit: counts of verified, unverified and placeholder nodes, and the first 15 keys of each. |
| `--all` | List every unverified and placeholder key instead of the first 15. |
| `--key` | One node with its full provenance: value, unit, label, verified, placeholder, source, as-of, note. Refused (exit 8) for a placeholder node without `--allow-placeholder-rates`. |
| `--assessment-year`, `--rates`, `--data-dir` | Which file to read. |

The audit is the fastest way to see the state of a year's data:

```bash
python3 src/engine/rates.py --assessment-year 2026-27
```

```
# TakaBooks — rates audit

Rates source: rates-AY2026-27.toml — করবর্ষ / assessment year 2026-27

| Rate nodes | Count |
| :--- | ---: |
| verified | 365 |
| unverified | 52 |
| placeholder | 19 |
| total | 436 |
```

followed by the placeholder keys and the unverified keys by name, and a closing line about
whether the file is ready to produce a fileable figure.

Those counts were true when this page was written and **go stale the moment anybody edits a
node** — the file's own header says the same. Run the command; do not quote the numbers above.

`--key` answers "where did this figure come from?" — value, unit, `verified`, `placeholder`,
`source` URL, `as_of` date and a `note` giving the section and every condition attached:

```bash
python3 src/engine/rates.py --assessment-year 2026-27 --key vat.rates.standard
```

Note the shape of the key space: a `tds.sections.<n>` node is a *section*, not a rate, and
asking for it directly is an error that tells you so —

```
error: rates-AY2026-27.toml: tds.sections.109 is a section, not a rate — it has no 'value'.
```

The rate lives one level down, at `tds.sections.109.rate`.

With `--json` (audit mode): `ok`, `rates_source`, `file`, `assessment_year`,
`file_is_placeholder`, `total_rate_nodes`, `verified`, `unverified`, `placeholder`,
`verified_count`, `unverified_count`, `placeholder_count`, `usable`.

This is also the library every other script uses to load a rates file, so what it reports is
what they compute from.

## `build/build.py` — the bundles

Not part of the engine, but you will meet it: it emits every platform bundle in `dist/` from
`src/` and regenerates the root `AGENTS.md`.

```
build.py [-h] [--target {claude-skill,chatgpt,gemini,universal,agents-md,all,none}]
         [--all] [--repo-root REPO_ROOT] [--clean] [--check] [--strict]
         [--gemini-soft-limit N] [--json] [--quiet]
```

| Flag | Meaning |
| --- | --- |
| `--target` | Which bundle to build; repeatable. Default `all`. `none` builds nothing, which is useful with `--clean`. |
| `--all` | Build every target — the default, spelled out for CI scripts. Equivalent to `--target all`. |
| `--check` | Assemble everything and verify every platform limit, writing nothing. |
| `--clean` | Remove `dist/` entirely before building. |
| `--strict` | Treat a missing expected source file as a build failure (use in release CI). |
| `--repo-root` | Repository root holding `src/` (default: the parent of `build/`). |
| `--gemini-soft-limit N` | Soft character target for `gem-instructions.md`. Google publishes no limit, so this only ever warns. |
| `--json`, `--quiet` | JSON report; failures only. |

`--all` and `--target all` are two spellings of the same default. See
[Contributing](Contributing).

## `bin/takabooks.mjs` — the installer

A Node script that copies a built bundle to where a platform expects it. Documented on
[Installation](Installation).

## See also

- [Getting Started](Getting-Started) — the scripts in order, on a fresh set of books
- [Journal Format](Journal-Format) · [Chart of Accounts](Chart-of-Accounts)
- [Updating Tax Rates](Updating-Tax-Rates) — what `verified`, `UNVERIFIED` and `PLACEHOLDER` mean
- [Troubleshooting](Troubleshooting) — every error message, what caused it, what to do
- [Disclaimer](Disclaimer)
