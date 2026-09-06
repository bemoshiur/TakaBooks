# TakaBooks templates — হিসাব তালিকা, কনফিগ ও জাবেদা / chart, config and journal

These three files are what `init_books.py` copies into a fresh `books/` directory. After
that they belong to the business: edit them by hand, or let the assistant edit them. Every
TakaBooks script only ever *reads* them.

| File | Becomes | What it is |
|---|---|---|
| `accounts.toml` | `books/accounts.toml` | হিসাব তালিকা / chart of accounts for a Bangladeshi SME — trading or service |
| `config.toml` | `books/config.toml` | Who the business is, when its year runs, how it reports |
| `journal-header.csv` | first line of every `books/journal/YYYY-MM.csv` | The exact column header from spec §4.3 |

**No rate, threshold, deadline or section number appears in any template.** Those live in
`src/data/rates-AY<year>.toml`, each with a source URL and a `verified` flag. A template that
carried a number would be a number nobody checked.

---

## `accounts.toml` — the chart of accounts

### Reading a line

```toml
[[account]]
code = "9100"
name = "VAT Input / Rebateable"
name_bn = "উপকরণ কর (রেয়াতযোগ্য মূসক)"
type = "asset"
normal = "debit"
role = "vat_input"
description = "The মূসক / VAT you paid a supplier that you may set off …"
tags = ["mushak", "duties-and-taxes"]
```

| Key | Required | Meaning |
|---|---|---|
| `code` | yes | Unique 4-digit code. First digit is the class (below). Gaps of 5–10 are left so you can insert your own accounts without renumbering. |
| `name` | yes | English name — what appears in reports. |
| `name_bn` | no (always filled here) | Bangla name — how the bookkeeper reads the voucher. |
| `type` | yes | `asset` · `liability` · `equity` · `income` · `expense` |
| `normal` | yes | `debit` for asset/expense, `credit` for liability/equity/income. The engine enforces this pairing. |
| `description` | no (always filled here) | One plain sentence an owner can act on. |
| `role` | on ten accounts | The engine's lookup key — see below. |
| `tags` | no | Free labels; a few have meaning — see below. |

Any other key is rejected when the file is loaded.

### Code blocks (spec §4.4)

| Block | Class | বাংলা |
|---|---|---|
| `1xxx` | assets | সম্পদ |
| `2xxx` | liabilities | দায় |
| `3xxx` | equity | মালিকানা স্বত্ব / মূলধন |
| `4xxx` | income | আয় |
| `5xxx` | cost of goods sold | বিক্রীত পণ্যের ব্যয় |
| `6xxx` | operating expenses | পরিচালন ব্যয় |
| `7xxx` | other income | অন্যান্য আয় |
| `8xxx` | other expenses | অন্যান্য ব্যয় |
| `9xxx` | tax and statutory accounts (assets, liabilities *and* expenses) | শুল্ক ও কর সংক্রান্ত হিসাব |

No Bangladeshi authority prescribes account codes. The codes are TakaBooks' own convention;
the **names** carry the weight, and the মূসক / VAT names in the 9xxx block are the statutory
ones. Renumber freely — but keep the roles.

### The ten roles the engine looks up

Spec §4.4 lists Bangladesh-specific accounts that must exist. The engine finds them by
`role`, not by code, so each role must sit on exactly one account:

| `role` | Template account | Purpose |
|---|---|---|
| `vat_input` | 9100 VAT Input / Rebateable | উপকরণ কর — rebateable input মূসক |
| `vat_output` | 9200 VAT Output Payable | উৎপাদ কর — output মূসক collected |
| `tds_receivable` | 9300 TDS Receivable | উৎসে কর কর্তন deducted *from you* by customers |
| `tds_payable` | 9320 TDS Payable — deducted from vendors | উৎসে কর কর্তন you deducted from suppliers |
| `vds_payable` | 9220 VDS Payable | উৎসে মূসক কর্তন you deducted from suppliers |
| `advance_income_tax` | 9310 Advance Income Tax (AIT) | অগ্রিম আয়কর |
| `provident_fund_payable` | 9400 Provident Fund Payable | প্রদেয় ভবিষ্য তহবিল |
| `gratuity_provision` | 9410 Gratuity Provision | আনুতোষিক সংস্থান |
| `wppf_payable` | 9420 WPPF Payable | শ্রমিক অংশগ্রহণ তহবিল |
| `supplementary_duty_payable` | 9210 Supplementary Duty Payable | প্রদেয় সম্পূরক শুল্ক |

`validate.py` reports a missing role as a finding; `vat.py` refuses to run without the VAT
roles.

### Tags that mean something

| Tag | Effect |
|---|---|
| `contra` | The balance runs opposite to its class and is shown as a deduction (see next section). |
| `control` | One account for many parties. The journal's `party` column keeps the party-wise খতিয়ান / ledger; never create one account per customer or supplier. |
| `cash` · `bank` · `mfs` | Money accounts. Every posting to them should carry a `doc_ref`; bKash / Nagad / Rocket balances are `mfs`, not cash. |
| `vds` · `tds` · `withholding` | Tells `validate.py` the account is a tax control for that tag kind, on accounts that carry no `role` (9120, 9325). |
| `inactive` (also `archived`, `closed`, `disabled`, `retired`) | Retire an account. `validate.py` warns if anything is still posted to it. |
| `sundry-debtors` · `sundry-creditors` · `duties-and-taxes` | Tally-era aliases owners still say aloud, kept so the assistant maps them to the right code. |
| `inventory` · `fixed-asset` · `payroll` · `import` · `advance` · `loan` · `owner` · `related-party` · `suspense` · `non-deductible` | Grouping hints for the assistant and for reports. |

### Contra accounts — how they are modelled

The engine insists that an asset is `debit`-normal and an income account `credit`-normal.
A contra account (accumulated depreciation, provision for doubtful debts, sales returns,
purchase returns, drawings) legitimately runs the other way. In this chart they keep the
`type` and `normal` of the class they belong to, carry the `contra` tag, and simply show a
balance in the opposite direction — negative in the trial balance column you would expect.
They are:

| Code | Account | Deducted from |
|---|---|---|
| 1290 | Provision for Doubtful Debts | 1200 Accounts Receivable |
| 1690 | Accumulated Depreciation | 16xx fixed assets |
| 1790 | Accumulated Amortisation | 1700 Intangible assets |
| 3300 | Drawings | owner's equity |
| 4190 | Sales Return & Discount Allowed | 41xx sales |
| 5190 | Purchase Return & Discount Received | 51xx purchases |

### Two rules that fall out of the 9xxx block

1. **Never net.** 9100 is never netted against 9200 in the ledger, nor 9300 against 9320.
   মূসক ৯.১ / Mushak 9.1 and the income tax return both demand the gross figures; netting
   guarantees the return cannot be tied back to the books.
2. **Every 9xxx balance is provable by a document.** 9100 → a মূসক ৬.৩ / Mushak 6.3 tax
   invoice entered in মূসক ৬.১ / Mushak 6.1 · 9120 → a মূসক ৬.৬ / Mushak 6.6 received ·
   9220 → a Mushak 6.6 issued plus a treasury challan · 9300 → a deduction certificate ·
   9130 → treasury challans and the return's closing balance.

### Trimming it for your business

A service business can delete the inventory accounts (1400–1450, 5900), the import block
(1340, 5110–5130, 9110) and the factory lines (5200–5220). A trader that never imports can
drop the import block. A proprietorship without staff can drop the payroll block (6100–6150,
2130, 1310, 9325, 9400–9430) — but keep every account that carries a `role`, or give the
role to another account.

---

## `config.toml` — who, when and how

Four tables. The engine reads `[business]`, `[books]` and `[locale]`; `[compliance]` is
recorded for the assistant and for you.

| Table | Key | What to put there |
|---|---|---|
| `[business]` | `name`, `name_bn` | Legal name in English and Bangla, as on the trade licence |
| | `type` | `proprietorship` · `partnership` · `company` · `ngo` · `other` |
| | `tin`, `bin` | Exactly as printed on your NBR e-TIN and মূসক / VAT registration certificates; blank until you have them |
| | `address`, `trade_licence`, `registration_no` | Informational |
| `[books]` | `currency` | Always `"BDT"` |
| | `fiscal_year_start` | `MM-DD`, the day your income year opens. **Commented out in the template** — TakaBooks never guesses it |
| | `fiscal_year_end` | `MM-DD`, informational; the engine closes the year the day before the next opening |
| | `assessment_year` | `YYYY-YY` as printed on your NBR return. **Commented out in the template** |
| | `rates_file` | `rates-AY<year>.toml` for that assessment year |
| | `accounts_file`, `journal_dir` | Leave as they are |
| `[locale]` | `language` | `en` · `bn` · `bn-en` |
| | `grouping` | `bd` (12,34,567.89 — লাখ/কোটি, default) · `international` (1,234,567.89) |
| | `digits` | `latin` · `bangla` |
| `[compliance]` | `vat_registered` | `yes` · `no` · `unknown` |
| | `turnover_tax_enlisted` | `yes` · `no` · `unknown` |
| | `withholding_entity` | `yes` · `no` · `unknown` — must you deduct VDS/TDS from suppliers? |
| | `city_tier` | `unspecified` · `dhaka-chattogram-city` · `other-city` · `other-area` — a label only; whether it changes any figure is decided by the rates file |
| | `accounting_basis` | `accrual` (what TakaBooks maintains) · `cash` (you convert at year-end — say so, and the assistant will ask about accruals before a report) |

`init_books.py` inherits the non-statutory defaults (`currency`, `locale.*`, file names) from
this template and asks you for everything else. It deliberately refuses to copy
`fiscal_year_start` or `assessment_year` out of a template, and warns if a template sets
them — copying a statutory value from a template is exactly the kind of guess this project
forbids.

---

## `journal-header.csv` — the column header

```csv
date,entry_id,description,account,debit,credit,party,doc_ref,tax_tag,memo
```

`init_books.py` cross-checks this file against the schema in the library and refuses to
scaffold if they differ, so the file holds the header row and nothing else. Column meanings
(spec §4.3):

| Column | Rule |
|---|---|
| `date` | ISO `YYYY-MM-DD` |
| `entry_id` | Groups rows into one entry; **all rows sharing an `entry_id` must balance** |
| `description` | What happened, in words |
| `account` | A `code` from `accounts.toml`; an unknown code is a hard error |
| `debit` / `credit` | Decimal BDT (`1000.00`); exactly one of the two is non-zero on each row |
| `party` | The customer, supplier, employee or landlord — a name, never an account |
| `doc_ref` | Voucher, receipt, মূসক ৬.৩ / Mushak 6.3 or challan number. Near-mandatory: ask for it rather than post blank |
| `tax_tag` | `VAT:OUT:<rate>` · `VAT:IN:<rate>` · `TDS:<section>:<rate>` · `VDS:<rate>` · `NONE` — rates and sections from the rates file |
| `memo` | Free text; always last so a comma in it survives |

### Worked examples

Three balanced entries using the template chart. **Every amount is a round, obviously
fake number, and every rate and section is a placeholder** — `10`, `5` and `0XX` are
*not* Bangladeshi rates or sections. Before you post a real entry, read the real figures from
`rates-AY<year>.toml` (`vat.rates.standard`, `tds.sections.<id>`) and, if they are still
marked `verified = false`, confirm them with your ITP/CA.

How the tag is placed: the **value** line (sales, purchase, rent) and the **tax** line
(9200, 9100, 9320) carry the same tag; the cash / bank / receivable / payable line is `NONE`.
`vat.py` and `validate.py` reconcile value × rate against the tax actually posted.

```csv
date,entry_id,description,account,debit,credit,party,doc_ref,tax_tag,memo
2026-07-01,EX-0001,EXAMPLE cash sale with output VAT,1100,1100.00,,Walk-in customer,MUSHAK-6.3-EXAMPLE-0001,NONE,EXAMPLE ONLY — fake amounts; gross cash received into the till
2026-07-01,EX-0001,EXAMPLE cash sale with output VAT,4100,,1000.00,Walk-in customer,MUSHAK-6.3-EXAMPLE-0001,VAT:OUT:10,EXAMPLE ONLY — 10 is an illustrative rate; read vat.rates.standard from rates-AY<year>.toml
2026-07-01,EX-0001,EXAMPLE cash sale with output VAT,9200,,100.00,Walk-in customer,MUSHAK-6.3-EXAMPLE-0001,VAT:OUT:10,EXAMPLE ONLY — output VAT held for the treasury until the return
2026-07-02,EX-0002,EXAMPLE credit purchase with rebateable input VAT,5100,1000.00,,Example Supplier Ltd,MUSHAK-6.3-EXAMPLE-S-0007,VAT:IN:10,EXAMPLE ONLY — value excluding VAT; enter this row in Mushak 6.1
2026-07-02,EX-0002,EXAMPLE credit purchase with rebateable input VAT,9100,100.00,,Example Supplier Ltd,MUSHAK-6.3-EXAMPLE-S-0007,VAT:IN:10,EXAMPLE ONLY — rebateable only with a valid Mushak 6.3 showing both BINs
2026-07-02,EX-0002,EXAMPLE credit purchase with rebateable input VAT,2100,,1100.00,Example Supplier Ltd,MUSHAK-6.3-EXAMPLE-S-0007,NONE,EXAMPLE ONLY — gross owed to the supplier
2026-07-03,EX-0003,EXAMPLE rent paid by bank transfer with TDS deducted,6200,1000.00,,Example Landlord,PV-EXAMPLE-0003,TDS:0XX:5,EXAMPLE ONLY — 0XX and 5 are placeholders; the section id and rate come from tds.sections in rates-AY<year>.toml
2026-07-03,EX-0003,EXAMPLE rent paid by bank transfer with TDS deducted,9320,,50.00,Example Landlord,PV-EXAMPLE-0003,TDS:0XX:5,EXAMPLE ONLY — deposit to the treasury and issue the landlord a deduction certificate
2026-07-03,EX-0003,EXAMPLE rent paid by bank transfer with TDS deducted,1150,,950.00,Example Landlord,PV-EXAMPLE-0003,NONE,EXAMPLE ONLY — net paid through the banking channel
```

What each entry does:

| Entry | Dr | Cr | Bangla / English |
|---|---|---|---|
| `EX-0001` cash sale | 1100 Cash 1,100 | 4100 Sales 1,000 · 9200 VAT Output 100 | নগদ বিক্রয়, উৎপাদ কর সহ / cash sale with output মূসক |
| `EX-0002` credit purchase | 5100 Purchases 1,000 · 9100 VAT Input 100 | 2100 Payable 1,100 | বাকিতে ক্রয়, রেয়াতযোগ্য উপকরণ কর / purchase with rebateable input মূসক |
| `EX-0003` rent with TDS | 6200 Rent 1,000 | 9320 TDS Payable 50 · 1150 Bank 950 | উৎসে কর কর্তন সহ ভাড়া পরিশোধ / rent paid net of TDS |

To try them: scaffold a directory, paste the block into `books/journal/2026-07.csv`, then run
`validate.py` and `vat.py`:

```bash
python3 src/engine/init_books.py --books /tmp/demo-books --name "Example Traders" \
    --fiscal-year-start 07-01 --start-month 2026-07
# paste the CSV block above into /tmp/demo-books/journal/2026-07.csv
python3 src/engine/validate.py --books /tmp/demo-books
python3 src/engine/vat.py --books /tmp/demo-books
```

(`--fiscal-year-start 07-01` here is only so the example dates fall inside a period; use
the day *your* income year actually opens.) `validate.py` reports the three entries clean
at ৳3,200 = ৳3,200; `vat.py` flags the illustrative rates because the rates file does not
declare them — that flag is the design working, not a bug. Because the demo starts from
empty books, 1150 Bank shows a negative balance after the rent payment; real books carry an
opening balance, and a cash or bank balance below zero on any day is the classic sign of an
unrecorded receipt — check it before you close a month.

---

## Rules the templates follow (spec §4, §6)

- Standard library only; TOML is read with `tomllib`, so Python 3.11 or newer.
- Money is integer paisa inside the engine; the CSV carries human-readable BDT decimals.
- Bangla and English together wherever a statutory term appears: মূসক / VAT, উৎসে কর কর্তন /
  TDS, উৎসে মূসক কর্তন / VDS, খতিয়ান / ledger, জাবেদা / journal.
- Nothing in a template is a tax fact. If you are about to type a rate here, stop — it goes
  in `rates-AY<year>.toml` with its source URL.

---

TakaBooks — Moshiur Rahman ([@bemoshiur](https://github.com/bemoshiur)) · **Ticon Sys** —
https://ticonsys.com · MIT licensed. Not professional advice: verify with a licensed ITP or
CA before filing. এটি পেশাদার পরামর্শ নয় — দাখিলের আগে লাইসেন্সপ্রাপ্ত আইটিপি বা সিএ-এর সঙ্গে
যাচাই করুন।
