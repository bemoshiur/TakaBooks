# Troubleshooting — সমস্যা সমাধান

Organised by what you see. Every engine message below is the real text the script prints,
so you can search this page for it. A non-zero exit is never a crash to be worked around; it
is the engine telling you something is wrong with the data or the request, and the fix is
always in the data or the request — never in the script.

## Reading an error

```
error: <what is wrong, with the file, line or flag that caused it>
  hint: <what to do about it>
```

Then an exit code. The codes are stable across scripts:

| Exit | Meaning |
| ---: | --- |
| 0 | OK |
| 1 | General failure |
| 2 | Config, usage, or Python too old |
| 3 | Account — unknown code or invalid chart |
| 4 | Journal — bad row, bad date, duplicate id, missing books directory |
| 5 | Unbalanced entry |
| 6 | Malformed `tax_tag` |
| 7 | Validation findings; several problems at once; `vat.py --strict` caveats |
| 8 | Rates file — missing, malformed, placeholder, or key absent |
| 9 | Money — `float` offered, or amount unparseable |

## Python and the environment

**`TakaBooks needs Python 3.11 or newer (tomllib lives in the standard library from 3.11). You are running Python 3.x …`**
Exit 2, before anything else runs. Install a newer Python from
https://www.python.org/downloads/ and run with `python3.11 …` (or `py -3.11 …` on Windows).
Nothing in TakaBooks can be made to work on an older interpreter, because the TOML parser
it uses is part of the 3.11 standard library.

**`python3: command not found`** (Windows)
Use `py -3 src\engine\validate.py --help`. If `py` is missing too, Python is not installed
or not on the PATH; the installer has a checkbox for that.

**`ModuleNotFoundError: No module named 'takabooks'`**
You are running a script from outside its directory *and* the shared library is not beside
it. The scripts locate `takabooks.py` next to themselves, so keep `src/engine/` intact (or
`scripts/` in a skill bundle). Do not copy one script out on its own.

**Bangla shows as boxes or question marks.**
The console font lacks Bengali glyphs, or the terminal is not UTF-8. The engine is
unaffected — files are written correctly. On Windows use Windows Terminal; on any system set
the locale to a UTF-8 one. The npm installer accepts `--no-bangla` for a legacy console; the
engine has no such flag because its output is data, not decoration.

**I ran `pip install` and something changed.**
Nothing in TakaBooks needs anything installed; CI proves the suite passes in an empty
virtual environment. If a third-party package is on your path it is irrelevant to the engine.

## Books and configuration

**`Books directory not found: <dir>`** (exit 4)
`--books` points at a directory that does not exist. Run `init_books.py --books <dir>` to
create it, or fix the path. The default is `./books` relative to where you run the command.

**`Config not found: <path>`** (exit 2)
The directory exists but has no `config.toml`. Scaffold with `init_books.py`, or copy a
`config.toml` in.

**`<dir> already holds books (config.toml, accounts.toml, …); refusing to overwrite them.`** (exit 2)
`init_books.py` will not clobber a books directory. Pass `--force` to rewrite `config.toml`
and `accounts.toml` (journal CSVs are never touched), or use another `--books DIR`.

**`config.toml: books.fiscal_year_start is not set.`** (exit 2)
You asked for something that needs the income year — `report.py --period FY…`, or the
date-range checks — and TakaBooks will not guess when your year opens. Add
`fiscal_year_start = "MM-DD"` under `[books]`. In `validate.py` the same situation is a
warning, `config-fiscal-year`, and date-range checks are skipped.

**`config.toml: books.assessment_year is not set.`** (exit 2)
Every tax output must state its করবর্ষ / assessment year. Add `assessment_year = "YYYY-YY"`
under `[books]`, or pass `--assessment-year`.

**`books.fiscal_year_start = '…' must be written MM-DD`** / **`locale.grouping = '…' must be 'bd' or 'international'`** / **`books.currency = '…'; TakaBooks keeps books in BDT only`**
`config.toml` has a value outside the allowed set; the message names the key. `init_books.py`
writes every key with a comment listing its allowed values.

## Chart of accounts

**`Account code '9999' is not in accounts.toml.`** (exit 3)
The journal row or `--debit/--credit` names a code the chart does not have. `post.py`
suggests near matches (`Did you mean 2310 VAT Output Payable …?`). Use an existing code or
add the account — see [Chart of Accounts](Chart-of-Accounts). Never post to an account you
cannot name.

**`Account <code> (<name>) is type 'asset' so its normal balance must be 'debit', not 'credit'.`** (exit 3)
`type` and `normal` disagree. Assets and expenses are debit-normal; liabilities, equity and
income are credit-normal.

**`account <code> has unknown key(s): …`** (exit 3)
A typo in `accounts.toml`. Allowed keys: `code`, `name`, `name_bn`, `type`, `normal`,
`description`, `role`, `tags`.

**`accounts.toml … duplicate codes`** (exit 3)
Two `[[account]]` tables share a `code`. Codes must be unique.

**Warning `missing-required-role`**
One of the ten Bangladesh-specific roles is not declared on any account. The engines that
need it (VAT reconciliation, tag/account matching) cannot find the control account. Add the
`role` key to the account that plays the part.

**Warning `chart-block` / `chart-code-format`**
An account's leading digit disagrees with its type, or the code is not four digits (plus
optional suffix). Both still work; they are flagged because reports and the assistant assume
the convention.

**Warning `inactive-account`**
A row posts to an account tagged `inactive` (or `archived`, `closed`, `disabled`, `retired`).
Post to the replacement, or drop the tag if the account is in use again.

## Posting entries

**`Entry '<id>' dated <date> does not balance: debits ৳100.00 vs credits ৳90.00; ৳10.00 too much debit`** (exit 5)
The single most important refusal in TakaBooks. Correct the amounts. The engine never adjusts
your numbers for you, and it wrote nothing.

**`malformed tax_tag 'VAT:10': expected VAT:OUT:<rate> or VAT:IN:<rate>.`** (exit 6)
The tag does not match the grammar. The hint prints the whole grammar. Common slips: `VAT:`
without `OUT`/`IN`; `TDS:` without a section; a rate written as a fraction (`0.10`) or above
100; `NONE:0`. See [Journal Format](Journal-Format).

**`entry_id '<id>' is already used in these books — dated <date> at <file> lines N–M.`** (exit 4)
Ids are unique across the whole books directory. Leave `--id` out to have one generated, or
pick an unused one. To fix an earlier entry, post a reversing entry; never reuse its id.

**`date '10/07/2026' is not an ISO date.`** (exit 4)
Dates are `YYYY-MM-DD`, always. `2026-7-6` (no zero padding) is also rejected.

**`debit '1e3' is not a valid BDT amount.`** (exit 4)
Amounts are plain decimals: `1234.56`, `1,00,000.00`, `৳ 500`, Bangla digits. No exponent
notation, no `float`.

**`--debit #1: …` / `--credit #3: …`**
The number is the position of that flag on the command line, counting debits and credits
separately, so you can find the offending line quickly.

**`The entry has N problems and was not written:`** (exit 7)
More than one kind of problem at once. Each is listed; fix every line and post again.

**I posted the wrong thing and it succeeded.**
Do not edit the CSV row and do not reuse the id. Post a reversing entry (same accounts,
sides swapped, `doc_ref` pointing at the original), then the correct one. Run `validate.py`.

## Validation findings

`validate.py --list-checks` prints every check with its id. What each means and what to do:

| Finding | Severity | Cause → fix |
| --- | --- | --- |
| `config-unreadable`, `accounts-unreadable` | error | `config.toml` / `accounts.toml` missing or invalid → fix the file; the message names the line |
| `journal-missing`, `journal-unreadable` | error | No `journal/` directory, or a file could not be read (encoding, permissions) → create it; save as UTF-8 |
| `journal-header` | error | First line is not the exact ten-column header → restore it |
| `row-fields`, `row-invalid` | error | A row has fewer than six columns, or was rejected by the schema → check for a stray line break or a missing cell |
| `bad-date` | error | Not strict ISO → rewrite as `YYYY-MM-DD` (spreadsheets do this to you) |
| `missing-entry-id`, `missing-account` | error | Blank cell → fill it |
| `bad-amount`, `negative-amount`, `both-sides`, `no-amount` | error | Unparseable, negative, both sides set, or neither → one positive amount on exactly one side |
| `bad-tax-tag` | error | Grammar → see [Journal Format](Journal-Format) |
| `unknown-account` | error | Code not in the chart → fix the code or add the account |
| `tax-tag-account-mismatch` | error | A VAT tag on a TDS-role account or vice versa → put the tag on the right control account |
| `unbalanced-entry` | error | Debits ≠ credits for one `entry_id` → correct the rows |
| `orphan-entry` | error | An `entry_id` with a single row → add the other side, or fix the id |
| `duplicate-entry-id` | error | One id on rows that are not one entry (different dates, or separated by other entries) → give each transaction its own id |
| `no-journal-files` | warning | Nothing to validate |
| `journal-filename`, `journal-stray-file` | warning | A file in `journal/` not named `YYYY-MM.csv`, or not a CSV → rename or remove |
| `config-fiscal-year`, `config-assessment-year` | warning | Not set → set them; date checks are skipped / tax outputs will refuse |
| `missing-required-role`, `chart-code-format`, `chart-block`, `inactive-account` | warning | See *Chart of accounts* above |
| `date-outside-financial-year` | warning | A row falls outside the year being validated → keep one income year per `books/`, or `--fy-start` |
| `date-out-of-order` | warning | Dates run backwards inside a file → keep chronological order |
| `misfiled-posting` | warning | A row's month is not the file's month → move it to the right `YYYY-MM.csv` |
| `tax-tag-orphan` | warning | A tag with no matching tax-role account in the entry → tag the control line too |
| `tax-tag-control-only` | warning | A tag only on the control account, so the taxable value reads ৳0.00 → tag the value line too, or use `NONE` for a pure deposit/adjustment |

`RESULT: N error(s), M warning(s) — do not file or report from these books until the errors are fixed. (exit 7)`
Fix the errors first; the *NOTES* section says which entries were skipped because a row could
not be read, and which duplicate ids would balance if they were one entry. Warnings alone
still exit 7 unless you pass `--allow-warnings`.

## Reports

**`Books directory not found`** / **`fiscal_year_start is not set`** — see above.

**The trial balance does not tie / a reconciliation shows FAIL.**
`report.py` reconciles before it prints and exits non-zero on a break, so this means the
journal itself is broken. Run `validate.py`; it will name the entry.

**Figures look wrong by a factor of 100.**
An amount was entered in paisa instead of taka. The journal is in taka with two decimals.

**Grouping looks foreign.**
`12,34,567.89` is লাখ/কোটি grouping and is the default. `--grouping international` or
`locale.grouping = "international"` gives `1,234,567.89`.

## VAT

**`Filing status: PROVISIONAL / অস্থায়ী — not for filing`**
The rates file read is, or contains, a placeholder or unverified figure. Your journal
amounts are exact; the statutory context is what is flagged, item by item under
*Warnings*. When verified figures land in the rates file the stamp clears.
[Updating Tax Rates](Updating-Tax-Rates).

**`--strict` exits 7.**
That is what `--strict` is for: any PLACEHOLDER, UNVERIFIED, missing or non-reconciling
figure is fatal. Use it in a script that must never file a provisional number.

**`RATE CHECK SKIPPED: … declares no usable VAT rate under vat.rates …`**
The file has no verified VAT rate to check your tags against. Once one lands, every tagged
rate is compared with the declared set and unknown rates are flagged.

**`no value for '<key>'`** (exit 8)
A required key is absent from the rates file. TakaBooks will not substitute a guess. Add the
node with its source, or use a file that has it.

**The control-account reconciliation shows movement under *Other*.**
Something moved `vat_output` / `vat_input` / `vds_payable` that carried no VAT tag — a
treasury deposit, an adjustment, or a mistake. Deposits and adjustments are expected there;
a mistake is a row that should have been tagged.

**`--allow-ay-mismatch`**
The rates file's assessment year differs from `config.toml`'s. Usually a mistake; the flag
exists for deliberate comparisons.

## Income tax

**`rates-AY<year>.toml is a schema awaiting verified data — every figure in it is a placeholder.`** (exit 8)
The file declares `[meta] placeholder = true`. Land verified figures (see
[Updating Tax Rates](Updating-Tax-Rates)), or pass `--allow-placeholder-rates` for an
explicitly PROVISIONAL walkthrough that must never be filed.

**`<key> is a placeholder awaiting verified data.`** (exit 8)
One node, same story, same two options.

**`No rates file for করবর্ষ / assessment year <AY> in <dir>.`** (exit 8)
The year you named has no file. The hint lists the years that exist. Check `--data-dir`.

**`<dir> holds N rates files; name the assessment year.`** (exit 8)
Several years exist and none was named. Pass `--assessment-year`, or set
`books.assessment_year` / `books.rates_file` in `config.toml`. Refusing to guess the year is
deliberate.

**`config.toml names rates_file = '…', which was not found.`** (exit 8)
The hint lists where it looked: beside `config.toml`, in the data directory, in the current
directory. Fix the name or the path.

**`<key> is written as a TOML float (0.5).`** (exit 8)
A rates file author wrote a bare decimal. Quote it: `value = "0.5"`. TakaBooks refuses float
money.

**`--category` / `--location` not recognised.**
Run `tax.py --list-options` for the ids the rates file defines and their defaults.

## The assistant

**It gave me a number without running anything.**
That violates its own instruction. Ask it to run the engine (or to print the command for
you), and compare. If it computed by hand, do not use the figure.

**It stated a rate "as I understand it".**
A named red flag in the core instruction. Ask which file it read the rate from this
session. If it cannot name one, the figure is memory, not data.

**It asked eight questions.**
It should ask at most four, leading with the fact that gates the computation. Answer the
gating one and tell it to proceed.

**It refused to give a slab table.**
Correct behaviour: the table is the number. It names the file instead. Read the file.

**It answered from a reference marked STUB.**
It should not — a stub carries no verified content. Tell it to say so and point you to NBR
and a licensed ITP/CA.

## Installing and building

**`npx @bemoshiur/takabooks` → 401**
GitHub Packages requires authentication even for a public package. Configure `~/.npmrc` with
a `read:packages` classic token, or download the release assets — same files.
[Installation](Installation).

**`No built bundles found at <dir>`**
The installer looked for `dist/`. Build first (`python3 build/build.py`) or pass `--dist`.

**The ChatGPT instructions field rejects the paste.**
The build refuses to emit an instruction over 8,000 characters, so a rejection means the
file was edited after building, or the paste picked up extra text. Re-copy `instructions.md`
exactly.

**Gemini says too many files.**
A Gem takes ten documents; the bundle ships exactly ten. Add only the files in `knowledge/`.

**`build.py --check` warns `missing: src/templates/`.**
The templates directory is absent from the checkout, so `init_books.py` uses its built-in
chart. A warning, not a failure; `--strict` makes it fatal for release builds.

**`chatgpt/instructions.md: N chars (limit 8,000)` failed.**
`src/core/` grew past the cap. Move reference prose into `<!-- knowledge-only -->` blocks or
into a reference file. The check prints per-file counts and the headroom.

**The wiki does not update after I pushed.**
Either the wiki repository was never initialised (create a first page in the web UI once),
or the change was outside `docs/wiki/`. See
[`docs/README.md`](https://github.com/bemoshiur/TakaBooks/blob/main/docs/README.md).

## Still stuck

Open an issue at https://github.com/bemoshiur/TakaBooks/issues with the exact command, the
exact output, `python3 --version`, and — if it is about the books — a minimal `books/` that
reproduces it with **synthetic** data. Never attach a real TIN, BIN, NID or client ledger.
