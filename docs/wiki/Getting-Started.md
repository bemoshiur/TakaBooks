# Getting Started — প্রথম হিসাব থেকে প্রথম প্রতিবেদন

First books, first entry, first report, first VAT position — end to end, with the real output
of each step. Fifteen minutes, one terminal, no installation beyond Python.

> **About the numbers on this page.** The amounts are demo figures. Where a VAT tag needs a
> percentage to show the grammar, the walkthrough uses **`10` as an illustrative number** so
> the arithmetic is easy to follow by eye. It is **not** the statutory মূসক / VAT rate, and
> TakaBooks will never tell you the real rate from prose: read it from the assessment-year
> rates file and confirm it with NBR before you post real entries. See
> [Updating Tax Rates](Updating-Tax-Rates) and the [Disclaimer](Disclaimer).

## 0. What you need

- **Python 3.11 or newer.** Check with `python3 --version` (on Windows, `py -3 --version`).
  Nothing else — no `pip install`, ever.
- **A copy of TakaBooks.** Either clone the repository or download a release bundle; the
  engine scripts are the same files in both (see [Installation](Installation)). This page
  assumes you are in the repository root, so the scripts are at `src/engine/`. In a Claude
  Skill bundle they are at `scripts/` and the rates file at `data/`; substitute the paths.
- A terminal that shows Bangla. Most do. If you see boxes instead of letters, the engine
  still works; only the display is affected.

## 1. Create the books

`init_books.py` scaffolds a `books/` directory. It asks nothing statutory of itself: the day
your income year opens and your করবর্ষ / assessment year are written **only if you pass
them**, because TakaBooks never guesses a Bangladeshi tax fact on your behalf.

```bash
python3 src/engine/init_books.py --books ./books \
  --name "Demo Traders" --name-bn "ডেমো ট্রেডার্স" \
  --business-type proprietorship \
  --fiscal-year-start 07-01 \
  --assessment-year 2026-27 --rates-file rates-AY2026-27.toml \
  --vat-registered yes \
  --start-month 2026-07
```

What each flag means:

| Flag | Why it matters |
| --- | --- |
| `--fiscal-year-start 07-01` | The day *your* income year opens, `MM-DD`. The walkthrough uses `07-01`; use the value your business actually runs on, and confirm it with your accountant. Without it, fiscal-year reports refuse to run and date checks are skipped. |
| `--assessment-year 2026-27` | The করবর্ষ as printed on your NBR return. Every tax output must state it, so tax scripts refuse to run without it. |
| `--rates-file rates-AY2026-27.toml` | Pins the rates TOML for that year. |
| `--vat-registered yes` | A label for your own reference and the assistant's questions. No figure is attached to it. |
| `--start-month 2026-07` | Also creates an empty journal file for that month. Optional; `post.py` creates month files as needed. |

Output:

```
TakaBooks — books ready: books
  business        Demo Traders (ডেমো ট্রেডার্স)
  হিসাব তালিকা / chart of accounts  42 accounts from built-in Bangladesh chart of accounts
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

next steps:
  1. Check TIN/BIN and the chart of accounts against your own records.
  2. Record your first entry:  python3 src/engine/post.py --books books --date YYYY-MM-DD --description '...' --debit 1100=1000.00 --credit 4100=1000.00
```

Look at what was written:

```
books/
├── config.toml        business identity, [books] fiscal_year_start / assessment_year / rates_file, [locale]
├── accounts.toml      42 accounts, every Bangladesh-specific one carrying a `role`
├── journal/
│   └── 2026-07.csv    the header row only
└── reports/           empty until report.py runs
```

Open `config.toml`. Add your TIN and BIN under `[business]` when you have them in front of
you; the file says on every line what each key is for, in Bangla and English. Open
`accounts.toml` and skim the codes — the [Chart of Accounts](Chart-of-Accounts) page
explains the blocks and the `role` keys.

Prefer to be asked? `init_books.py -i` prompts for anything you did not pass. Want to see
without writing? Add `--dry-run`.

## 2. The first entry — opening capital

Every entry has two equal sides: debit / ডেবিট (what the business got) and credit / ক্রেডিট
(where it came from). The owner puts money in the bank:

```bash
python3 src/engine/post.py --books ./books --date 2026-07-01 \
  --description "Opening capital" \
  --debit 1110=100000.00 --credit 3100=100000.00
```

```
posted JE-2026-07-0001 → books/journal/2026-07.csv (appended)  [entry_id generated]
  2026-07-01  Opening capital
      account                                  ডেবিট / debit  ক্রেডিট / credit
  Dr  1110 Bank Account (ব্যাংক হিসাব)          ৳1,00,000.00
  Cr  3100 Owner's Capital (মালিকের মূলধন)                        ৳1,00,000.00
  debits ৳1,00,000.00 = credits ৳1,00,000.00 — balanced
```

Notice three things. The id `JE-2026-07-0001` was generated for you. The amount is shown in
লাখ/কোটি grouping — `1,00,000.00` — because that is the default for a Bangladeshi book. And
the last line says *balanced*: had it not been, nothing would have been written and the
script would have exited 5. Try it:

```bash
python3 src/engine/post.py --books ./books --date 2026-07-01 --description "Oops" \
  --debit 1110=100.00 --credit 3100=90.00 --dry-run
```

```
error: Entry 'JE-2026-07-0002' dated 2026-07-01 does not balance: debits ৳100.00 vs credits ৳90.00; ৳10.00 too much debit
  hint: Every entry must have equal debits and credits. TakaBooks never adjusts your numbers for you.
```

## 3. A sale with output VAT

A cash sale where you charged মূসক / VAT. Three rows, one entry: the cash that came in, the
sale itself, and the VAT you now owe. The value line and the tax line **both** carry the same
`tax_tag`, which is how `vat.py` later ties them together.

```bash
python3 src/engine/post.py --books ./books --date 2026-07-05 \
  --description "Cash sale" --party "Walk-in customer" --doc-ref INV-0001 \
  --debit  1100=11000.00 \
  --credit 4100=10000.00:VAT:OUT:10 \
  --credit 2310=1000.00:VAT:OUT:10
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

Again: **`10` here is an illustrative percentage**, chosen so that ৳10,000 × 10% = ৳1,000 is
obvious. In real books the percentage in the tag is the one the rates file declares for the
supply, and `vat.py` will flag any tag whose rate the file does not declare.

`2310` is the account whose `role` is `vat_output`. You never post VAT to "some liability";
you post it to the account that carries the role, and the tax engine finds it by that role.

## 4. A purchase with input VAT

Office rent paid in cash, with rebateable input VAT on the invoice:

```bash
python3 src/engine/post.py --books ./books --date 2026-07-08 \
  --description "July office rent" --party Landlord --doc-ref RCPT-07 \
  --debit  6200=2000.00:VAT:IN:10 \
  --debit  1310=200.00:VAT:IN:10 \
  --credit 1100=2200.00
```

```
posted JE-2026-07-0003 → books/journal/2026-07.csv (appended)  [entry_id generated]
  2026-07-08  July office rent
  party Landlord · doc_ref RCPT-07
      account                                                  ডেবিট / debit  ক্রেডিট / credit
  Dr  6200 Office Rent (অফিস ভাড়া)                                ৳2,000.00                    VAT:IN:10 — rebateable input মূসক / VAT at 10%
  Dr  1310 VAT Input / Rebateable (রেয়াতযোগ্য উপকরণ মূসক)           ৳200.00                    VAT:IN:10 — rebateable input মূসক / VAT at 10%
  Cr  1100 Cash in Hand (হাতে নগদ)                                                   ৳2,200.00
  debits ৳2,200.00 = credits ৳2,200.00 — balanced
  tax tags: VAT:IN:10
```

Input VAT goes to `1310` (role `vat_input`), an **asset** — it is money you may claim back.
It is never netted against output VAT inside the books; that netting is what the return
does, and `vat.py` computes it for you.

Here is the journal file now — plain CSV you can open anywhere:

```
date,entry_id,description,account,debit,credit,party,doc_ref,tax_tag,memo
2026-07-01,JE-2026-07-0001,Opening capital,1110,100000.00,0.00,,,NONE,
2026-07-01,JE-2026-07-0001,Opening capital,3100,0.00,100000.00,,,NONE,
2026-07-05,JE-2026-07-0002,Cash sale,1100,11000.00,0.00,Walk-in customer,INV-0001,NONE,
2026-07-05,JE-2026-07-0002,Cash sale,4100,0.00,10000.00,Walk-in customer,INV-0001,VAT:OUT:10,
2026-07-05,JE-2026-07-0002,Cash sale,2310,0.00,1000.00,Walk-in customer,INV-0001,VAT:OUT:10,
2026-07-08,JE-2026-07-0003,July office rent,6200,2000.00,0.00,Landlord,RCPT-07,VAT:IN:10,
2026-07-08,JE-2026-07-0003,July office rent,1310,200.00,0.00,Landlord,RCPT-07,VAT:IN:10,
2026-07-08,JE-2026-07-0003,July office rent,1100,0.00,2200.00,Landlord,RCPT-07,NONE,
```

## 5. Validate

Before any report, check the whole খতিয়ান / ledger. `validate.py` reads every row of every
file and reports every problem at once:

```bash
python3 src/engine/validate.py --books ./books
```

```
TakaBooks — খতিয়ান যাচাই / ledger validation
==============================================================================
Books directory          : books
Business                 : Demo Traders (ডেমো ট্রেডার্স)
করবর্ষ / assessment year : 2026-27
Financial year           : 2026-07-01 → 2027-06-30 (config fiscal_year_start = 07-01; the year holding all 8 posting(s))
Journal files            : 1 — 2026-07.csv
Rows                     : 8 data row(s) read · 8 posting(s) checked · 3 entry/entries
Date range               : 2026-07-01 → 2026-07-08
Total debits             : ৳1,13,200.00
Total credits            : ৳1,13,200.00
Difference               : ৳0.00

==============================================================================
RESULT: clean — 8 posting(s) in 3 entry/entries, debits and credits agree at ৳1,13,200.00. (exit 0)
```

Make it a habit: **validate after every hand edit, and before every report you rely on.**
Exit 0 means clean; anything else lists the file, the line and the entry that broke, with a
hint.

## 6. The first report

Trial balance, profit and loss, balance sheet — from one computation, so they cannot
disagree with each other:

```bash
python3 src/engine/report.py --books ./books --period 2026-07
```

The Markdown is long; here is the trial balance and the reconciliation footer:

```
## রেওয়ামিল / Trial balance — as at 2026-07-31

| Code | Account | Type | Debit (৳) | Credit (৳) | Balance (৳) |
| :--- | :--- | :--- | ---: | ---: | ---: |
| 1100 | Cash in Hand (হাতে নগদ) | asset | 11,000.00 | 2,200.00 | 8,800.00 |
| 1110 | Bank Account (ব্যাংক হিসাব) | asset | 1,00,000.00 | 0.00 | 1,00,000.00 |
| 1310 | VAT Input / Rebateable (রেয়াতযোগ্য উপকরণ মূসক) | asset | 200.00 | 0.00 | 200.00 |
| 2310 | VAT Output Payable (প্রদেয় মূসক) | liability | 0.00 | 1,000.00 | 1,000.00 |
| 3100 | Owner's Capital (মালিকের মূলধন) | equity | 0.00 | 1,00,000.00 | 1,00,000.00 |
| 4100 | Sales Revenue (বিক্রয় আয়) | income | 0.00 | 10,000.00 | 10,000.00 |
| 6200 | Office Rent (অফিস ভাড়া) | expense | 2,000.00 | 0.00 | 2,000.00 |
|  | **Total (সর্বমোট)** |  | **1,13,200.00** | **1,13,200.00** |  |

**Debits equal credits** — ৳1,13,200.00 debit against ৳1,13,200.00 credit, difference ৳0.00. রেওয়ামিল মিলেছে / the trial balance ties.

### Reconciliations performed

- **PASS** `trial_balance_debits_equal_credits` — total debits ৳1,13,200.00 vs total credits ৳1,13,200.00 — difference ৳0.00
- **PASS** `balance_sheet_assets_equal_liabilities_plus_equity` — assets ৳1,09,000.00 vs liabilities ৳1,000.00 + equity ৳1,08,000.00 — difference ৳0.00
- **PASS** `profit_and_loss_sections_cover_every_income_and_expense_account` — net profit from the sections ৳8,000.00 vs income less expenses straight from the ledger ৳8,000.00
- **PASS** `accumulated_result_ties_to_the_ledger` — brought forward ৳0.00 + period ৳8,000.00 = ৳8,000.00 vs cumulative income less expenses ৳8,000.00

### CSV written

- `books/reports/trial-balance_2026-07-31.csv`
- `books/reports/profit-and-loss_2026-07-01_2026-07-31.csv`
- `books/reports/balance-sheet_2026-07-31.csv`
```

The P&L shows the month's ৳8,000 profit; the balance sheet carries it into equity; the
reconciliations prove the two agree. Use `--period FY2026-27` for the whole income year,
`--statement tb` for one statement, `--grouping international` for `100,000.00`-style
figures, and `--json` for a machine-readable version of all three.

## 7. The VAT position

```bash
python3 src/engine/vat.py --books ./books --period 2026-07
```

The report opens like this:

```
# মূসক / VAT position — Demo Traders (ডেমো ট্রেডার্স)

- **Period:** 2026-07
- **করবর্ষ / assessment year:** 2026-27
- **Rates source: rates-AY2026-27.toml — করবর্ষ / assessment year 2026-27**
- **Postings read:** 8 in 3 entries
- **Filing status:** PROVISIONAL / অস্থায়ী — not for filing

> **PROVISIONAL / অস্থায়ী — NOT FOR FILING.** The rates file is a placeholder schema awaiting
> verified data, so every statutory figure quoted below is unlanded. …
```

and then, from *your* postings — which are facts, not rates — the return figures:

```
| Ref | অঙ্ক / Figure | Key | পরিমাণ / Amount |
| 1 | করযোগ্য সরবরাহের মোট মূল্য / Total value of taxable supplies | output.taxable_value | ৳10,000.00 |
| 2 | প্রদেয় উৎপাদ কর / Output VAT charged on those supplies | output.tax | ৳1,000.00 |
| 3 | রেয়াতযোগ্য উপকরণের মোট মূল্য / Total value of purchases carrying rebateable input VAT | input.taxable_value | ৳2,000.00 |
| 4 | রেয়াতযোগ্য উপকরণ কর / Rebateable input VAT on those purchases | input.tax | ৳200.00 |
| 5 | উৎপাদ কর বাদ উপকরণ কর / Output VAT less rebateable input VAT | net.output_less_input | ৳800.00 |
| 6 | নিট প্রদেয় মূসক / Net VAT payable for the period | net.payable | ৳800.00 |
```

Two things to understand about that PROVISIONAL stamp:

- The **amounts** (৳1,000 output, ৳200 input, ৳800 net) come from your journal and are
  arithmetically exact. The control-account reconciliation and the per-entry input–output
  tie-out further down both pass.
- The **statutory context** — the standard rate the tags should have used, the thresholds,
  the filing deadline — is read from the rates file, and while that file is a placeholder
  schema every such item is marked PLACEHOLDER and the whole output is marked not for
  filing. Once verified figures land in the file (see
  [Updating Tax Rates](Updating-Tax-Rates)), the same command produces a fileable figure set
  with the rate check performed. `--strict` makes any remaining caveat a non-zero exit.

## 8. Income tax — and a refusal that is a feature

```bash
python3 src/engine/tax.py --books ./books --income 500000
```

```
error: rates-AY2026-27.toml is a schema awaiting verified data — every figure in it is a placeholder.
  hint: No Bangladeshi rate has been landed for this assessment year yet. Fill the file in (its header documents the procedure), or pass --allow-placeholder-rates to compute a clearly-marked PROVISIONAL result that must never be filed.
```

That is the engine doing its job. It will not compute a tax liability from figures nobody
has verified. Pass `--allow-placeholder-rates` and it walks through the method — threshold,
slabs, rebate, minimum tax, surcharge — with every step labelled PROVISIONAL and every rate
it used listed with its status. `--list-options` shows the taxpayer categories and location
tiers the rates file defines.

## 9. Now with an assistant

Everything above is what an LLM does *for* you when TakaBooks is installed in it. The
division of labour is fixed by the core instruction:

1. You describe a transaction in Bangla, Banglish or English.
2. The assistant lists the facts it depends on (stated / assumed / needed), decides which
   accounts and which `tax_tag` apply, and — if a rate is involved — names the rates file it
   read it from. It asks at most four questions before it proceeds.
3. It runs `post.py --json` (or prints the exact command for you to run and asks for the
   output back if it cannot execute anything).
4. It quotes the engine's output. It never re-derives a number, and a non-zero exit is
   reported as a refusal, not patched.
5. Every tax reply ends with: verify with a licensed ITP or CA before filing.

If it ever gives you a bold number in the first line, a rate "as I understand it", or a
slab table it did not read this session, that is a red flag the instruction itself names.
Ask it for the source file.

## 10. Where next

- Put `books/` under git. It is plain text and diffs beautifully.
- Read [Journal Format](Journal-Format) before you hand-edit a CSV, and
  [Chart of Accounts](Chart-of-Accounts) before you add an account.
- Keep [Engine Reference](Engine-Reference) open for the flags.
- Read the [Disclaimer](Disclaimer). Then talk to your ITP or CA about what the books should
  look like for *your* business — TakaBooks makes that conversation shorter, not
  unnecessary.
