# Journal Format — জাবেদা / journal CSV

The journal is the only thing TakaBooks writes to your books. Everything else — the
রেওয়ামিল / trial balance, the স্থিতিপত্র / balance sheet, the মূসক / VAT position — is
recomputed from it every time. This page documents the file, the row, the amounts and the
`tax_tag` grammar exactly as the engine enforces them.

> No tax rate on this page is a statutory rate. Where a tag needs a number to show the
> grammar, the number is written `<rate>`, or is an obviously illustrative figure and is
> labelled as such. Real rates come from the rates file — see
> [Updating Tax Rates](Updating-Tax-Rates).

## Files

```
books/
└── journal/
    ├── 2026-07.csv
    ├── 2026-08.csv
    └── …
```

- **One file per calendar month**, named `YYYY-MM.csv`. The name is checked: anything else in
  `journal/` is reported by `validate.py` (`journal-filename` for a wrongly named CSV,
  `journal-stray-file` for a non-CSV).
- A row belongs in the file of its own month. A row dated in a different month is a
  `misfiled-posting` warning, not an error — the books still balance, but the file no longer
  reads as a month.
- A month with no transactions needs no file. `validate.py` notes a gap between two existing
  months so you can confirm it was really empty.
- **UTF-8, no BOM.** Bangla in `description`, `party` and `memo` is expected and fine. A BOM
  on the header line is tolerated on read but do not add one.
- Plain `\n` or `\r\n` line endings both read correctly.

## The header

The first line of every journal file must be exactly:

```
date,entry_id,description,account,debit,credit,party,doc_ref,tax_tag,memo
```

`validate.py` reports a missing or altered header as `journal-header`. `init_books.py
--start-month YYYY-MM` writes an empty file with just this line; `post.py` creates the file
with this header the first time it writes to a new month.

## The row

**One row per posting line.** A journal entry (জাবেদা দাখিলা) with a debit and a credit is two
rows; a sale with output VAT is three. Rows that share an `entry_id` are one entry, and the
rows of one entry must sit together, on one date.

| # | Column | Required | Meaning |
| ---: | --- | :---: | --- |
| 1 | `date` | yes | Strict ISO `YYYY-MM-DD`. `2026-7-6` and `06/07/2026` are rejected (`bad-date`). |
| 2 | `entry_id` | yes | Groups rows into one entry. Unique across the whole `books/` directory, not just the file. |
| 3 | `description` | yes | What the entry records. Repeated on every row of the entry. |
| 4 | `account` | yes | An account **code** from `accounts.toml`. A code not in the chart is a hard error (`unknown-account`). |
| 5 | `debit` | yes* | Decimal BDT. Exactly one of `debit` / `credit` is non-zero on each row. |
| 6 | `credit` | yes* | Decimal BDT. The unused side is written `0.00`; on read, blank and `-` also mean zero. |
| 7 | `party` | no | The customer or supplier — a name, **not** an account. |
| 8 | `doc_ref` | no | Voucher, চালান / invoice, Mushak 6.3, bill or receipt number. Ask for it rather than post blank. |
| 9 | `tax_tag` | no | Structured tag that drives মূসক / VAT and উৎসে কর কর্তন / TDS derivation. Blank reads as `NONE`; write `NONE` explicitly. |
| 10 | `memo` | no | Free text. Deliberately the last column so a stray comma survives. |

The first six columns are mandatory on every data row (`row-fields` if fewer). Trailing
optional columns may be omitted entirely on read; the engine always writes all ten.

### Invariants the engine enforces

- **Every entry balances.** For each `entry_id`, the sum of `debit` equals the sum of `credit`,
  compared in integer paisa. `post.py` refuses an unbalanced entry (exit 5) and writes
  nothing; `validate.py` reports `unbalanced-entry`.
- **An entry has at least two rows.** A lone row can never balance: `orphan-entry`.
- **An `entry_id` is used once.** The same id on rows that are not one entry — different
  dates, or separated by other entries — is `duplicate-entry-id`. Fix an earlier entry by
  posting a **reversing entry**, never by reusing or editing its id.
- **One side per row.** Both `debit` and `credit` non-zero is `both-sides`; both zero is
  `no-amount`.
- **Amounts are not negative.** A negative amount is `negative-amount`; reverse the sides
  instead.
- **The account exists and is active.** Unknown is an error; an account tagged inactive in
  the chart is a warning (`inactive-account`).

### `entry_id`

When you let `post.py` generate the id, it is `JE-YYYY-MM-NNNN` — the month, then a
four-digit sequence that continues from the highest number already in that month's file
(`JE-2026-07-0001`, `JE-2026-07-0002`, …). You may supply your own ids (`--id`), for instance
to carry a voucher series; they must still be unique across the books. Case and spacing are
preserved exactly as written.

### Amounts

Amounts are written as human-readable BDT decimals so the CSV opens correctly in a
spreadsheet, and are converted to integer paisa on read. Internally the engine never uses a
floating-point number for money; it parses with `decimal.Decimal`, converts to paisa, and
rounds once, half-up, only where a percentage is applied.

Accepted on the command line and in JSON input (all mean the same amount):

```
100000
100000.00
1,00,000.00        লাখ/কোটি grouping
100,000.00         international grouping
৳ 1,00,000.00      currency symbol, BDT, Tk, Taka are stripped
১,০০,০০০.০০        Bangla digits are converted
```

Not accepted: exponent notation (`1e3`), more than two decimal places where a CSV cell is
expected to be exact, or any `float` offered through the library API. The journal itself is
always written with two decimals and no grouping (`100000.00`), which is what Excel, Google
Sheets and LibreOffice read back cleanly.

### Spreadsheets

Opening a journal file in a spreadsheet is fine; **saving from one is where the damage
happens**. Before you save back to `YYYY-MM.csv`:

- Keep the `date` column as text. Spreadsheets love to rewrite `2026-07-05` as `7/5/2026`,
  which the engine rejects.
- Keep `account` as text. `1100` must not become `1,100`.
- Save as "CSV UTF-8". A CSV saved in a legacy Windows code page turns Bangla into `?`.
- Do not let the tool add a thousands separator to `debit` / `credit`.

Then run `python3 src/engine/validate.py --books ./books`. It reads every row and tells you
exactly which line broke.

### Bangla and commas

`description`, `party` and `memo` may contain Bangla, punctuation and commas. The engine
writes proper CSV (a field with a comma or a quote is quoted), and `memo` is last so that
even a hand-edited row with an unquoted comma keeps its first nine columns intact.

## The `tax_tag` grammar

`tax_tag` is how the books tell `vat.py` and future withholding tooling what a posting means
for tax. It is structured text, parsed strictly, and a malformed tag is a hard error (`post.py`
exit 6; `validate.py` `bad-tax-tag`).

| Form | Meaning | Bangla |
| --- | --- | --- |
| `VAT:OUT:<rate>` | Output VAT — VAT you charged on a supply you made | প্রদেয় মূসক |
| `VAT:IN:<rate>` | Rebateable input VAT — VAT you paid on a purchase you may claim | রেয়াতযোগ্য উপকরণ মূসক |
| `TDS:<section>:<rate>` | Tax deducted at source under a section of the income tax law | উৎসে কর কর্তন |
| `VDS:<rate>` | VAT deducted at source from a supplier's payment | উৎসে মূসক কর্তন |
| `NONE` | The line is not tax-relevant | কর-অপ্রাসঙ্গিক |

Rules:

- **`<rate>` is a percentage, never a fraction.** `10` means ten percent. Up to three
  digits before the point and up to four after; an optional trailing `%` is accepted
  (`<rate>%`). A value above 100 is rejected as a fraction/percent mix-up.
- **The value of `<rate>` comes from the rates file**, never from memory. `vat.py` checks
  every VAT and VDS rate written in a tag against the rates declared for the assessment year
  and flags any tag whose rate the file does not declare.
- **`<section>`** is the section reference of the income tax law under which the deduction
  was made, exactly as printed on the deduction certificate: digits, optionally followed by
  letters, optionally with a bracketed sub-clause. The parser accepts that shape and
  upper-cases the letters; it does not know which sections exist — that is what the
  withholding reference and the rates file are for.
- **Case-insensitive on input, canonical on output.** `vat:out:<rate>` is accepted and written
  back as `VAT:OUT:<rate>`. Trailing zeros in the rate are normalised (`<rate>.00` → `<rate>`).
- **Blank, `-`, `--`, `n/a` and `na` all read as `NONE`** in a CSV cell. Write `NONE` so the
  intent is visible.
- **`NONE` takes nothing after it.** `NONE:0` is malformed.
- **Any other leading word is malformed.** There is no `SD:` tag; supplementary duty is posted
  to its own account with `NONE`.

### Which rows carry the tag

A tax tag describes a *relationship* between two rows of the same entry: the line that
carries the taxable value, and the line that carries the tax. **Tag both.** The engine finds
the tax line by the account's `role` in `accounts.toml` (`vat_output`, `vat_input`,
`vds_payable`, `tds_payable`, `tds_receivable`) and treats every other line with the same
tag as the taxable value.

A cash sale with output VAT — three rows, one entry. The `10` is an **illustrative** number
chosen so the arithmetic is visible; it is not a statutory rate:

```
2026-07-05,JE-2026-07-0002,Cash sale,1100,11000.00,0.00,Walk-in customer,INV-0001,NONE,
2026-07-05,JE-2026-07-0002,Cash sale,4100,0.00,10000.00,Walk-in customer,INV-0001,VAT:OUT:10,
2026-07-05,JE-2026-07-0002,Cash sale,2310,0.00,1000.00,Walk-in customer,INV-0001,VAT:OUT:10,
```

- Row 1 (`1100` Cash) is the money that moved; it carries `NONE`.
- Row 2 (`4100` Sales) is the taxable value; it carries the tag.
- Row 3 (`2310` VAT Output Payable, role `vat_output`) is the tax; it carries the same tag.

`vat.py` cross-checks each entry: the tax line's amount must equal the taxable value times
the tag's rate, rounded half-up once. A break is reported, not corrected.

What goes wrong when only one row is tagged:

- Tag on the control account only (say, a VAT deposit to the treasury tagged `VAT:OUT:…`):
  the taxable value reads as ৳0.00 — `tax-tag-control-only`. A pure deposit or adjustment
  should use `NONE`.
- Tag on the value line only, with no tax-role account in the entry: `tax-tag-orphan`.
- A VAT tag sitting on a TDS account, or vice versa: `tax-tag-account-mismatch`, an error,
  because the tag and the account disagree about which tax this is.

### TDS and VDS

The same two-row pattern applies. For a payment from which you deducted tax at source, the
expense line carries `TDS:<section>:<rate>` and the `tds_payable` line carries the same tag;
for VAT deducted at source the `vds_payable` line carries `VDS:<rate>`. When a **customer**
deducts tax from *your* invoice, the amount they withheld is posted to your `tds_receivable`
account with the tag, so it can be set off later.

Withholding is where the classification is hardest — which section, whether the payee's
status changes the rate, whether the deposit deadline has passed — and every one of those
answers lives in the withholding reference and the rates file, not in the tag grammar.

## JSON input for `post.py`

`post.py` accepts an entry as JSON on standard input (`--stdin`, implied by `--json` on a
pipe) or from a file (`--input FILE`). Amounts are strings or whole integers, never JSON
floats.

```json
{
  "date": "2026-07-09",
  "description": "Bank charge",
  "party": "",
  "doc_ref": "",
  "memo": "",
  "entry_id": "",
  "lines": [
    {"account": "6800", "debit": "50.00", "tax_tag": "NONE"},
    {"account": "1110", "credit": "50.00"}
  ]
}
```

`entry_id` may be omitted or empty to have one generated. `tax_tag` may be omitted on a
line. The response (`--json`) echoes the rows exactly as they will be — or, with
`--dry-run`, would be — written, plus the CSV text itself, so an assistant can show the user
what is about to go into the books before it happens.

## Editing the journal by hand

You can. It is a text file and it was designed to be readable. Two habits keep you safe:

1. **Never edit a posted entry to fix it — reverse it.** Post an entry that mirrors the
   wrong one (debits and credits swapped, same accounts, `doc_ref` pointing at the original)
   and then post the correct entry. The trail stays intact and the ids stay unique.
2. **Run `validate.py` after every hand edit.** It reads every row of every file and reports
   every problem it can find at once, with the file, line and entry id. Only when it says
   *clean* should you trust a report.

## See also

- [Chart of Accounts](Chart-of-Accounts) — the codes and roles the `account` column refers to
- [Engine Reference](Engine-Reference) — every flag of `post.py` and `validate.py`
- [Troubleshooting](Troubleshooting) — the validation findings, one by one
- [Disclaimer](Disclaimer)
