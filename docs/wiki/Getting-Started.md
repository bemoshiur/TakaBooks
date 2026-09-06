# Getting Started — প্রথম হিসাব থেকে প্রথম প্রতিবেদন

First books, first entry, first report, first VAT position — end to end. Every command and
every block of output on this page was run against the templates that ship in this
repository, and pasted back verbatim. Fifteen minutes, one terminal, no installation beyond
Python.

> **About the numbers on this page.** The amounts (৳5,00,000 of capital, a ৳3,00,000 sale)
> are invented demo figures — they are just arithmetic. The **percentages in the tax tags are
> not invented, and they are not this page telling you a rate.** Step 3 shows you the command
> that reads the rate out of the assessment-year rates file, with its source URL and its
> `verified` flag, and the tag then carries whatever that file said. That is the only way a
> rate is ever allowed to reach a posting. Do the same thing for your own supply — yours may
> be a reduced rate, a specific amount, or exempt — and confirm it with NBR or your adviser
> before you post real entries. See [Updating Tax Rates](Updating-Tax-Rates) and the
> [Disclaimer](Disclaimer).

## 0. What you need

- **Python 3.11 or newer.** Check with `python3 --version` (on Windows, `py -3 --version`).
  Nothing else — no `pip install`, ever.
- **A copy of TakaBooks.** Either clone the repository or download a release bundle; the
  engine scripts are the same files in both (see [Installation](Installation)). This page
  assumes you are in the repository root, so the scripts are at `src/engine/` and the chart
  template at `src/templates/`. In a Claude Skill bundle the scripts are at `scripts/` and the
  rates file at `data/`; substitute the paths.
- A terminal that shows Bangla. Most do. If you see boxes instead of letters, the engine
  still works; only the display is affected.

## 1. Create the books

`init_books.py` scaffolds a `books/` directory. It asks nothing statutory of itself: the day
your income year opens and your করবর্ষ / assessment year are written **only if you pass
them**, because TakaBooks never guesses a Bangladeshi tax fact on your behalf.

```bash
python3 src/engine/init_books.py --books books \
  --name "Rahman Traders" --name-bn "রহমান ট্রেডার্স" \
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

next steps:
  1. Check TIN/BIN and the chart of accounts against your own records.
  2. Record your first entry:  python3 src/engine/post.py --books books --date YYYY-MM-DD --description '...' --debit 1100=1000.00 --credit 4100=1000.00

TakaBooks — Moshiur Rahman (@bemoshiur) · Ticon Sys (https://ticonsys.com)
```

The template path is printed in full and is absolute; `/path/to/TakaBooks` above stands in
for wherever you cloned the repository. That substitution is the only edit made to any output
on this page.

**131 accounts** is the chart that ships in `src/templates/accounts.toml`. Read it before you
post anything: the [Chart of Accounts](Chart-of-Accounts) page walks the blocks, and the
`9xxx` কর হিসাব / tax block is the part that makes these books Bangladeshi rather than
generic.

Look at what was written:

```
books/
├── config.toml        business identity, [books] fiscal_year_start / assessment_year / rates_file, [locale]
├── accounts.toml      131 accounts, the ten Bangladesh roles each on exactly one account
├── journal/
│   └── 2026-07.csv    the header row only
└── reports/           empty until report.py runs
```

Open `config.toml`. Add your TIN and BIN under `[business]` when you have them in front of
you; the file says on every line what each key is for, in Bangla and English.

Prefer to be asked? `init_books.py -i` prompts for anything you did not pass. Want to see
without writing? Add `--dry-run`.

## 2. The first entry — opening capital

Every entry has two equal sides: debit / ডেবিট (what the business got) and credit / ক্রেডিট
(where it came from). The owner puts money in the bank. In the shipped chart the current
account is **1150** — `1110` is Petty Cash, and `1100` is Cash in Hand:

```bash
python3 src/engine/post.py --books books --date 2026-07-01 \
  --description "Owner's capital into the current account" \
  --doc-ref BR-2026-07-01 \
  --debit 1150=500000.00 --credit 3100=500000.00
```

```
posted JE-2026-07-0001 → books/journal/2026-07.csv (appended)  [entry_id generated]
  2026-07-01  Owner's capital into the current account
  doc_ref BR-2026-07-01
      account                                                                 ডেবিট / debit  ক্রেডিট / credit
  Dr  1150 Cash at Bank — Current Account (ব্যাংক হিসাব — চলতি)                ৳5,00,000.00
  Cr  3100 Share Capital / Owner's Capital (শেয়ার মূলধন / মালিকের মূলধন)                        ৳5,00,000.00
  debits ৳5,00,000.00 = credits ৳5,00,000.00 — balanced
```

Notice three things. The id `JE-2026-07-0001` was generated for you. The amount is shown in
লাখ/কোটি grouping — `5,00,000.00` — because that is the default for a Bangladeshi book. And
the last line says *balanced*: had it not been, nothing would have been written. Try it:

```bash
python3 src/engine/post.py --books books --date 2026-07-01 --description "Oops" \
  --debit 1150=100.00 --credit 3100=90.00 --dry-run
```

```
error: Entry 'JE-2026-07-0002' dated 2026-07-01 does not balance: debits ৳100.00 vs credits ৳90.00; ৳10.00 too much debit
  hint: Every entry must have equal debits and credits. TakaBooks never adjusts your numbers for you.
```

Exit code 5, and nothing written.

## 3. Read the rate before you use it

Before a tag carries a percentage, find out what the percentage *is* and where it came from.
This is the habit the whole project is built around, so learn it here rather than later:

```bash
python3 src/engine/rates.py --assessment-year 2026-27 --key vat.rates.standard
```

```
Rates source: rates-AY2026-27.toml — করবর্ষ / assessment year 2026-27

| Field | Value |
| :--- | :--- |
| key | vat.rates.standard |
| value | 15 |
| unit | percent |
| label | প্রমিত মূসক হার / Standard VAT rate |
| verified | yes |
| placeholder | no |
| source | http://bdlaws.minlaw.gov.bd/act-1106/section-42308.html |
| as of | 2019-07-01 |
```

A `note` follows, giving the section, what the figure covers and every condition attached —
here, that the Government may fix a reduced rate or a specific amount for Third Schedule
goods and services, and that a registered person may elect the standard rate instead in order
to keep full input tax credit. **Read the note.** `verified | yes` means a contributor read
that value from that URL on that date. It does not mean it applies to *your* supply.

Rahman Traders is a trading business selling at the standard rate, so the tags below carry
what the file just reported. If your supply is a Third Schedule item, run the same command
against the `vat.rates.reduced.<key>` node instead — and note that several of those nodes are
still marked `PLACEHOLDER`, which means the engine refuses them rather than guessing.

## 4. A sale with output VAT

A cash sale where you charged মূসক / VAT. Three rows, one entry: the money that came in, the
sale itself, and the VAT you now owe. The value line and the tax line **both** carry the same
`tax_tag`, which is how `vat.py` later ties them together.

```bash
python3 src/engine/post.py --books books --date 2026-07-12 \
  --description "Cash sale with output VAT" \
  --party "Walk-in customer" --doc-ref MUSHAK-6.3/RT/0007 \
  --debit  1150=345000.00 \
  --credit 4100=300000.00:VAT:OUT:15 \
  --credit 9200=45000.00:VAT:OUT:15
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

`9200` is the account whose `role` is `vat_output`. You never post VAT to "some liability";
you post it to the account that carries the role, and the tax engine finds it by that role,
not by its number. Renumber the chart if you like — the role travels with the account.

**A code that is not in the chart is a refusal, not a guess.** This is worth seeing once:

```bash
python3 src/engine/post.py --books books --date 2026-07-18 --description "Cash sale" \
  --debit 1100=11500.00 --credit 4100=10000.00 --credit 2310=1500.00:VAT:OUT:15
```

```
error: --credit #3: account code '2310' is not in accounts.toml.
  hint: Did you mean 2300 Loan from Directors / Proprietor (পরিচালক/মালিকের নিকট হইতে ঋণ), 2230 Lease / Hire-purchase Liability (ইজারা ও কিস্তি-ক্রয় দায়), 2220 Long-term Loan (দীর্ঘমেয়াদি ঋণ)? Add the account to accounts.toml or use an existing code; TakaBooks never posts to an account it cannot name.
```

Exit code 3. If you have followed an older guide that used `2310` for output VAT, that is
exactly what you will see — the shipped chart puts tax accounts in the `9xxx` block.

## 5. A purchase with input VAT

Stock bought on credit, with rebateable input VAT on the supplier's মূসক ৬.৩ / Mushak 6.3:

```bash
python3 src/engine/post.py --books books --date 2026-07-18 \
  --description "Credit purchase of stock" \
  --party "Karim Enterprise" --doc-ref MUSHAK-6.3/KE/0412 \
  --debit  5100=200000.00:VAT:IN:15 \
  --debit  9100=30000.00:VAT:IN:15 \
  --credit 2100=230000.00
```

```
posted JE-2026-07-0003 → books/journal/2026-07.csv (appended)  [entry_id generated]
  2026-07-18  Credit purchase of stock
  party Karim Enterprise · doc_ref MUSHAK-6.3/KE/0412
      account                                                                  ডেবিট / debit  ক্রেডিট / credit
  Dr  5100 Purchases — Local (ক্রয় — স্থানীয়)                                 ৳2,00,000.00                    VAT:IN:15 — rebateable input মূসক / VAT at 15%
  Dr  9100 VAT Input / Rebateable (উপকরণ কর (রেয়াতযোগ্য মূসক))                   ৳30,000.00                    VAT:IN:15 — rebateable input মূসক / VAT at 15%
  Cr  2100 Accounts Payable — Trade (প্রদেয় হিসাব — বাণিজ্যিক (পাওনাদার))                        ৳2,30,000.00
  debits ৳2,30,000.00 = credits ৳2,30,000.00 — balanced
  tax tags: VAT:IN:15
```

Input VAT goes to `9100` (role `vat_input`), an **asset** — it is money you may claim back.
It is never netted against `9200` inside the books; that netting is what the return does, and
`vat.py` computes it for you.

## 6. A payment with উৎসে কর কর্তন / TDS deducted

Shop rent, where you are the person paying and must withhold income tax at source. Three rows
again: the expense at its gross amount, the tax you withheld and must deposit, and the net
cash that actually left the bank.

```bash
python3 src/engine/post.py --books books --date 2026-07-28 \
  --description "Shop rent for July, TDS deducted at source" \
  --party "Ashraf Ali" --doc-ref PV-2026-07-014 \
  --debit  6200=25000.00:TDS:109:10 \
  --credit 9320=2500.00:TDS:109:10 \
  --credit 1150=22500.00
```

```
posted JE-2026-07-0004 → books/journal/2026-07.csv (appended)  [entry_id generated]
  2026-07-28  Shop rent for July, TDS deducted at source
  party Ashraf Ali · doc_ref PV-2026-07-014
      account                                                                                    ডেবিট / debit  ক্রেডিট / credit
  Dr  6200 Office Rent (অফিস ভাড়া)                                                                 ৳25,000.00                    TDS:109:10 — উৎসে কর কর্তন / TDS under section 109 at 10%
  Cr  9320 TDS Payable — deducted from vendors (সরবরাহকারী হইতে উৎসে কর্তিত আয়কর (প্রদেয়))                           ৳2,500.00  TDS:109:10 — উৎসে কর কর্তন / TDS under section 109 at 10%
  Cr  1150 Cash at Bank — Current Account (ব্যাংক হিসাব — চলতি)                                                       ৳22,500.00
  debits ৳25,000.00 = credits ৳25,000.00 — balanced
  tax tags: TDS:109:10
```

The `TDS:109:10` tag names both the **section** and the **rate**, and both came out of the
rates file the same way the VAT rate did — `rates.py --key tds.sections.109.rate` prints the
value, the source and the `verified` flag, and the section's own node carries `applies_to`,
`deducted_by` and the conditions attached. Whether *you* are a person who must deduct at all
is a question about your business, not about this page: ask your ITP or CA.

`9320` is `tds_payable` — money you are holding for the treasury. Depositing it later is a
separate entry that debits `9320` and credits the bank, and carries `NONE`, because a deposit
is a payment, not a deduction.

Here is the journal file now — plain CSV you can open anywhere:

```
date,entry_id,description,account,debit,credit,party,doc_ref,tax_tag,memo
2026-07-01,JE-2026-07-0001,Owner's capital into the current account,1150,500000.00,0.00,,BR-2026-07-01,NONE,
2026-07-01,JE-2026-07-0001,Owner's capital into the current account,3100,0.00,500000.00,,BR-2026-07-01,NONE,
2026-07-12,JE-2026-07-0002,Cash sale with output VAT,1150,345000.00,0.00,Walk-in customer,MUSHAK-6.3/RT/0007,NONE,
2026-07-12,JE-2026-07-0002,Cash sale with output VAT,4100,0.00,300000.00,Walk-in customer,MUSHAK-6.3/RT/0007,VAT:OUT:15,
2026-07-12,JE-2026-07-0002,Cash sale with output VAT,9200,0.00,45000.00,Walk-in customer,MUSHAK-6.3/RT/0007,VAT:OUT:15,
2026-07-18,JE-2026-07-0003,Credit purchase of stock,5100,200000.00,0.00,Karim Enterprise,MUSHAK-6.3/KE/0412,VAT:IN:15,
2026-07-18,JE-2026-07-0003,Credit purchase of stock,9100,30000.00,0.00,Karim Enterprise,MUSHAK-6.3/KE/0412,VAT:IN:15,
2026-07-18,JE-2026-07-0003,Credit purchase of stock,2100,0.00,230000.00,Karim Enterprise,MUSHAK-6.3/KE/0412,NONE,
2026-07-28,JE-2026-07-0004,"Shop rent for July, TDS deducted at source",6200,25000.00,0.00,Ashraf Ali,PV-2026-07-014,TDS:109:10,
2026-07-28,JE-2026-07-0004,"Shop rent for July, TDS deducted at source",9320,0.00,2500.00,Ashraf Ali,PV-2026-07-014,TDS:109:10,
2026-07-28,JE-2026-07-0004,"Shop rent for July, TDS deducted at source",1150,0.00,22500.00,Ashraf Ali,PV-2026-07-014,NONE,
```

The description of the last entry is quoted because it contains a comma — that is ordinary
CSV, written by the standard-library writer, and read back the same way.

## 7. Validate

Before any report, check the whole খতিয়ান / ledger. `validate.py` reads every row of every
file and reports every problem at once:

```bash
python3 src/engine/validate.py --books books
```

```
TakaBooks — খতিয়ান যাচাই / ledger validation
TakaBooks — Moshiur Rahman (@bemoshiur) · Ticon Sys (https://ticonsys.com)
==============================================================================
Books directory          : books
Business                 : Rahman Traders (রহমান ট্রেডার্স)
করবর্ষ / assessment year : 2026-27
Financial year           : 2026-07-01 → 2027-06-30 (config fiscal_year_start = 07-01; the year holding all 11 posting(s))
Journal files            : 1 — 2026-07.csv
Rows                     : 11 data row(s) read · 11 posting(s) checked · 4 entry/entries
Date range               : 2026-07-01 → 2026-07-28
Total debits             : ৳11,00,000.00
Total credits            : ৳11,00,000.00
Difference               : ৳0.00

==============================================================================
RESULT: clean — 11 posting(s) in 4 entry/entries, debits and credits agree at ৳11,00,000.00. (exit 0)

This output is generated by TakaBooks and is not professional advice. Verify every figure with a licensed Income Tax Practitioner (ITP) or Chartered Accountant, and against the National Board of Revenue (NBR), before you file.
```

Make it a habit: **validate after every hand edit, and before every report you rely on.**
Exit 0 means clean; anything else lists the file, the line and the entry that broke, with a
hint.

## 8. The first report

Trial balance, profit and loss, balance sheet — from one computation, so they cannot
disagree with each other:

```bash
python3 src/engine/report.py --books books --period 2026-07
```

The Markdown is long. Here is the trial balance:

```
## রেওয়ামিল / Trial balance — as at 2026-07-31

| Code | Account | Type | Debit (৳) | Credit (৳) | Balance (৳) |
| :--- | :--- | :--- | ---: | ---: | ---: |
| 1150 | Cash at Bank — Current Account (ব্যাংক হিসাব — চলতি) | asset | 8,45,000.00 | 22,500.00 | 8,22,500.00 |
| 2100 | Accounts Payable — Trade (প্রদেয় হিসাব — বাণিজ্যিক (পাওনাদার)) | liability | 0.00 | 2,30,000.00 | 2,30,000.00 |
| 3100 | Share Capital / Owner's Capital (শেয়ার মূলধন / মালিকের মূলধন) | equity | 0.00 | 5,00,000.00 | 5,00,000.00 |
| 4100 | Sales — Local (বিক্রয় — স্থানীয়) | income | 0.00 | 3,00,000.00 | 3,00,000.00 |
| 5100 | Purchases — Local (ক্রয় — স্থানীয়) | expense | 2,00,000.00 | 0.00 | 2,00,000.00 |
| 6200 | Office Rent (অফিস ভাড়া) | expense | 25,000.00 | 0.00 | 25,000.00 |
| 9100 | VAT Input / Rebateable (উপকরণ কর (রেয়াতযোগ্য মূসক)) | asset | 30,000.00 | 0.00 | 30,000.00 |
| 9200 | VAT Output Payable (প্রদেয় উৎপাদ কর (মূসক)) | liability | 0.00 | 45,000.00 | 45,000.00 |
| 9320 | TDS Payable — deducted from vendors (সরবরাহকারী হইতে উৎসে কর্তিত আয়কর (প্রদেয়)) | liability | 0.00 | 2,500.00 | 2,500.00 |
|  | **Total (সর্বমোট)** |  | **11,00,000.00** | **11,00,000.00** |  |

**Debits equal credits** — ৳11,00,000.00 debit against ৳11,00,000.00 credit, difference ৳0.00. রেওয়ামিল মিলেছে / the trial balance ties.
```

Both VAT control accounts appear on the face of the trial balance, on opposite sides,
unnetted. That is the point of the `9xxx` block.

The profit and loss for the month:

```
## লাভ-ক্ষতি হিসাব / Profit and loss — 2026-07-01 → 2026-07-31

| Code | Item | Amount (৳) |
| :--- | :--- | ---: |
|  | **আয় / Revenue** |  |
| 4100 | Sales — Local (বিক্রয় — স্থানীয়) | 3,00,000.00 |
|  | **Total revenue (মোট আয়)** | **3,00,000.00** |
|  | **বিক্রিত পণ্যের ব্যয় / Cost of Goods Sold** |  |
| 5100 | Purchases — Local (ক্রয় — স্থানীয়) | 2,00,000.00 |
|  | **Total cost of goods sold (মোট বিক্রিত পণ্যের ব্যয়)** | **2,00,000.00** |
|  | **Gross profit (মোট মুনাফা)** | **1,00,000.00** |
|  | **পরিচালন ব্যয় / Operating Expenses** |  |
| 6200 | Office Rent (অফিস ভাড়া) | 25,000.00 |
|  | **Total operating expenses (মোট পরিচালন ব্যয়)** | **25,000.00** |
|  | **Operating profit (পরিচালন মুনাফা)** | **75,000.00** |
|  | **Net profit for the period (সময়কালের নিট মুনাফা)** | **75,000.00** |
```

Note that the rent sits in the P&L at its **gross** ৳25,000, not at the ৳22,500 that left the
bank. The ৳2,500 withheld is a liability you owe the treasury, not a discount you received.

And the footer that proves the three statements agree:

```
### Reconciliations performed

- **PASS** `trial_balance_debits_equal_credits` — total debits ৳11,00,000.00 vs total credits ৳11,00,000.00 — difference ৳0.00
- **PASS** `balance_sheet_assets_equal_liabilities_plus_equity` — assets ৳8,52,500.00 vs liabilities ৳2,77,500.00 + equity ৳5,75,000.00 — difference ৳0.00
- **PASS** `profit_and_loss_sections_cover_every_income_and_expense_account` — net profit from the sections ৳75,000.00 vs income less expenses straight from the ledger ৳75,000.00
- **PASS** `accumulated_result_ties_to_the_ledger` — brought forward ৳0.00 + period ৳75,000.00 = ৳75,000.00 vs cumulative income less expenses ৳75,000.00

### CSV written

- `books/reports/trial-balance_2026-07-31.csv`
- `books/reports/profit-and-loss_2026-07-01_2026-07-31.csv`
- `books/reports/balance-sheet_2026-07-31.csv`
```

Use `--period FY2026-27` for the whole income year, `--statement tb` for one statement,
`--grouping international` for `100,000.00`-style figures, and `--json` for a
machine-readable version of all three.

## 9. The VAT position

```bash
python3 src/engine/vat.py --books books --period 2026-07
```

The report opens like this:

```
# মূসক / VAT position — Rahman Traders (রহমান ট্রেডার্স)

- **Period:** 2026-07
- **Dates covered:** 2026-07-01 → 2026-07-31 (inclusive)
- **করবর্ষ / assessment year:** 2026-27
- **Books:** `books`
- **Rates source: rates-AY2026-27.toml — করবর্ষ / assessment year 2026-27**
- **Postings read:** 11 in 4 entries
- **Filing status:** PROVISIONAL / অস্থায়ী — not for filing

> **PROVISIONAL / অস্থায়ী — NOT FOR FILING.** 12 rate(s) the file declares are still placeholders, so their values are withheld and the journal's tagged rates could not be checked against them (`vat.rates.reduced.building_construction_large`, …, `vat.rates.reduced.wholesale_business`); see the warnings below. Confirm every flagged item with the National Board of Revenue (NBR) before this figure set is used.
```

(the banner names all twelve keys in full; the list is elided here only for width).

Then a **সতর্কতা / Warnings** block giving one line per flagged key, each saying what the key
is and that its percentage is **withheld** rather than shown:

```
- **PLACEHOLDER: vat.rates.reduced.local_trading_stage (স্থানীয় ব্যবসায় পর্যায় — সাধারণ (তৃতীয় তফসিল, অনুচ্ছেদ ৩) — অনিশ্চিত / Local trading stage — general (Third Schedule para 3) — NOT CERTIFIED) in rates-AY2026-27.toml is schema awaiting research (placeholder = true), not a declared rate. Its percentage is withheld; pass --allow-placeholder-rates to see it.**
```

That withholding is deliberate: an unconfirmed percentage is not shown at all, so it cannot be
copied out of a warning and used by mistake.

And then, from *your* postings — which are facts, not rates — the return figures:

```
| Ref | অঙ্ক / Figure | Key | পরিমাণ / Amount |
| 1 | করযোগ্য সরবরাহের মোট মূল্য / Total value of taxable supplies | `output.taxable_value` | ৳3,00,000.00 |
| 2 | প্রদেয় উৎপাদ কর / Output VAT charged on those supplies | `output.tax` | ৳45,000.00 |
| 3 | রেয়াতযোগ্য উপকরণের মোট মূল্য / Total value of purchases carrying rebateable input VAT | `input.taxable_value` | ৳2,00,000.00 |
| 4 | রেয়াতযোগ্য উপকরণ কর / Rebateable input VAT on those purchases | `input.tax` | ৳30,000.00 |
| 5 | উৎপাদ কর বাদ উপকরণ কর / Output VAT less rebateable input VAT | `net.output_less_input` | ৳15,000.00 |
| 6 | নিট প্রদেয় মূসক / Net VAT payable for the period | `net.payable` | ৳15,000.00 |
| 7 | জের টানা উদ্বৃত্ত উপকরণ কর / Excess input VAT carried forward | `net.carry_forward` | ৳0.00 |
| 8 | উৎসে কর্তনের আওতাধীন সরবরাহের মূল্য / Value of supplies on which VDS was applied | `vds.supply_value` | ৳0.00 |
| 9 | উৎসে কর্তিত মূসক / VDS withheld from suppliers and payable to the treasury | `vds.withheld` | ৳0.00 |
```

The `Ref` column is a TakaBooks reference, **not** an NBR form line number.

Then a control-account reconciliation that proves nothing moved those accounts except the
postings you tagged:

```
| Role | Code | হিসাব / Account | প্রারম্ভিক / Opening | Tagged | Other | সমাপনী / Closing |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| vat_output | 9200 | VAT Output Payable (প্রদেয় উৎপাদ কর (মূসক)) | ৳0.00 | ৳45,000.00 | ৳0.00 | ৳45,000.00 |
| vat_input | 9100 | VAT Input / Rebateable (উপকরণ কর (রেয়াতযোগ্য মূসক)) | ৳0.00 | ৳30,000.00 | ৳0.00 | ৳30,000.00 |
| vds_payable | 9220 | VDS Payable (উৎসে কর্তিত মূসক (প্রদেয়)) | ৳0.00 | ৳0.00 | ৳0.00 | ৳0.00 |
```

Two things to understand about that PROVISIONAL stamp:

- The **amounts** (৳45,000 output, ৳30,000 input, ৳15,000 net) come from your journal and are
  arithmetically exact. The control-account reconciliation and the per-entry input–output
  tie-out both pass.
- The stamp is about the **statutory context**, not your arithmetic. `vat.py` reads a wide set
  of reference figures — reduced rates, thresholds, filing deadlines — and several of the
  Third Schedule reduced-rate nodes are still `PLACEHOLDER` because no SRO has been traced for
  them. One flagged key anywhere in what was read stamps the whole output. So read the
  warnings block: if every key it names is irrelevant to your supply, the figures above are
  still the figures — but it is you, or your ITP, who decides that, not the tool. `--strict`
  turns any remaining caveat into a non-zero exit; `--all-caveats` lists every unverified
  figure in the file rather than only the ones this run touched.

> ⚠️ **Do not read `--period YYYY-MM` as a statement about your filing frequency.** It
> computes one calendar month because a tax period is a calendar month. How often you must
> actually file, and by when, are statutory figures: read them out of the rates file
> (`deadlines.*`) and confirm them with NBR. Use `--since`/`--until` for any other range.

## 10. Income tax

```bash
python3 src/engine/tax.py --books books --income 800000 --investment 60000 --tax-paid 20000
```

This runs, and prints the full working — the slab table with a hand-check line, the
investment rebate with each cap shown, the minimum tax floor, the surcharge (not assessed
unless you pass `--net-wealth`), and a summary ending in net tax payable. It also prints
**every rate it used, with its status**, and a caveats list. The header says how soft the
answer is:

```
**Filing status:** PROVISIONAL / অস্থায়ী — not for filing

> **PROVISIONAL / অস্থায়ী — NOT FOR FILING.**  3 of the 16 rates used below are not confirmed against a primary NBR source. The arithmetic is right; the figures it rests on are not yet final. See *Caveats* at the end.
```

That is the honest summary of the state of the data, and note what it does *not* say: it does
not say the sum is wrong. **The arithmetic is right; the figures it rests on are not yet
final.** Thirteen of the sixteen rates this computation used were read from primary text; three
were not. The *Rates used* table at the end lists all sixteen keys with `verified` or
`UNVERIFIED` against each and the source URL for every one, so you can see exactly which part
of the answer is soft — and the *Caveats* section repeats each unverified key by name. Never
file from an output carrying that banner; take it, and its rates table, to your ITP or CA.

`--list-options` prints the taxpayer categories and location tiers the rates file defines,
which is also the fastest way to see whether a category you expected exists:

```bash
python3 src/engine/tax.py --books books --list-options
```

## 11. Now with an assistant

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

## 12. Where next

- Put `books/` under git. It is plain text and diffs beautifully.
- Read [Journal Format](Journal-Format) before you hand-edit a CSV, and
  [Chart of Accounts](Chart-of-Accounts) before you add an account.
- Keep [Engine Reference](Engine-Reference) open for the flags.
- Read [Updating Tax Rates](Updating-Tax-Rates) to understand what `verified`, `UNVERIFIED`
  and `PLACEHOLDER` commit the project to — and what they do not.
- Read the [Disclaimer](Disclaimer). Then talk to your ITP or CA about what the books should
  look like for *your* business — TakaBooks makes that conversation shorter, not
  unnecessary.
