# Chart of Accounts — হিসাব তালিকা

`books/accounts.toml` lists every account the journal may post to. The engine loads it,
validates it, and refuses any posting to a code it cannot find. This page explains the file,
the code blocks, the `role` keys that make the Bangladesh-specific accounts findable, and how
to extend the chart without breaking anything.

## The file

```toml
[[account]]
code = "1100"
name = "Cash in Hand"
name_bn = "হাতে নগদ"
type = "asset"          # asset | liability | equity | income | expense
normal = "debit"        # debit | credit
```

One `[[account]]` table per account. Allowed keys — anything else is an error, so a typo
like `nmae` cannot slip through silently:

| Key | Required | Meaning |
| --- | :---: | --- |
| `code` | yes | The posting code. Four digits, optionally followed by `.` or `-` and up to six alphanumerics (`1100`, `1100.01`, `1100-BKASH`). Unique across the file. |
| `name` | yes | English name. |
| `name_bn` | no | Bangla name. Shown in every report beside the English (`1100 Cash in Hand (হাতে নগদ)`). |
| `type` | yes | One of `asset`, `liability`, `equity`, `income`, `expense`. |
| `normal` | yes | `debit` or `credit`. Must agree with `type` (below). |
| `description` | no | Free text for humans and the assistant. |
| `role` | no | One of the ten Bangladesh-specific roles. This is what the tax engines look up. |
| `tags` | no | A string or list of strings. `inactive`, `archived`, `closed`, `disabled` or `retired` mark an account as retired. |

### Type and normal balance

Double-entry books stay readable because each account has a *normal* side. The engine
enforces the pairing and rejects a chart that disagrees with it:

| `type` | `normal` | Bangla | Appears on |
| --- | --- | --- | --- |
| `asset` | `debit` | সম্পদ | স্থিতিপত্র / balance sheet |
| `liability` | `credit` | দায় | balance sheet |
| `equity` | `credit` | মূলধন | balance sheet |
| `income` | `credit` | আয় | লাভ-ক্ষতি হিসাব / profit and loss |
| `expense` | `debit` | ব্যয় | profit and loss |

Reports state every balance positively in the account's normal direction, so a liability
with a credit balance shows as a positive figure, and an asset that has gone into credit
(an overdrawn bank account, say) shows as negative.

## Code blocks

The leading digit of a code says what kind of account it is. The blocks are a convention
from the design specification, and `validate.py` warns (`chart-block`) when an account's
leading digit disagrees with its `type`:

| Block | Holds | Bangla | Allowed types |
| --- | --- | --- | --- |
| `1xxx` | Assets | সম্পদ | asset |
| `2xxx` | Liabilities | দায় | liability |
| `3xxx` | Equity | মূলধন | equity |
| `4xxx` | Income | আয় | income |
| `5xxx` | Cost of goods sold | বিক্রিত পণ্যের ব্যয় | expense |
| `6xxx` | Operating expenses | পরিচালন ব্যয় | expense |
| `7xxx` | Other income | অন্যান্য আয় | income |
| `8xxx` | Other expenses | অন্যান্য ব্যয় | expense |
| `9xxx` | Tax accounts | কর হিসাব | asset, liability or expense |

Within a block, the numbering is yours. The built-in chart leaves gaps of a hundred between
groups precisely so you can insert (`1120 Bank — second account`, `1111 bKash`).

A code that is not four digits (with the optional suffix) is a `chart-code-format` warning.
It still works; it is flagged because the assistant and the reports assume the convention.

## Roles — the accounts Bangladesh needs

Ten accounts are mandatory for a complete chart, and the engine finds them by **`role`, not by
code**. Renumber as you like; keep the role key on whichever account plays the part.
`validate.py` warns `missing-required-role` for each one absent.

| `role` | Type | Purpose |
| --- | --- | --- |
| `vat_input` | asset | রেয়াতযোগ্য উপকরণ মূসক — rebateable input VAT you have paid and may claim |
| `vat_output` | liability | প্রদেয় মূসক — output VAT you have charged and owe |
| `tds_receivable` | asset | প্রাপ্য উৎসে কর্তিত কর — tax your customers deducted from your invoices |
| `tds_payable` | liability | প্রদেয় উৎসে কর্তিত কর — tax you deducted from vendors and must deposit |
| `vds_payable` | liability | প্রদেয় উৎসে কর্তিত মূসক — VAT you deducted at source from suppliers |
| `advance_income_tax` | asset | অগ্রিম আয়কর — advance tax paid, to set off against the assessed liability |
| `provident_fund_payable` | liability | প্রদেয় ভবিষ্য তহবিল |
| `gratuity_provision` | liability | গ্র্যাচুইটি সঞ্চিতি |
| `wppf_payable` | liability | প্রদেয় শ্রমিক অংশগ্রহণ তহবিল — Workers' Profit Participation Fund |
| `supplementary_duty_payable` | liability | প্রদেয় সম্পূরক শুল্ক — kept apart from VAT, in its own account and return line |

How the roles are used today:

- `vat.py` reads `vat_output`, `vat_input` and `vds_payable` to find the control accounts,
  reconcile their movement against the tagged postings, and build the return figures.
- `validate.py` uses all five tax roles to check that a `tax_tag` sits on an account of the
  matching tax (`tax-tag-account-mismatch` otherwise).
- `post.py` shows the role beside the account in its confirmation so a wrong choice is visible
  before anything is written.

Never net input VAT against output VAT inside the books. They are two accounts with two
roles; `vat.py` computes the net position for the return, and the return is where the netting
happens.

## The built-in chart

When `src/templates/accounts.toml` is not present, `init_books.py` scaffolds this chart. It is
a starting point for a Bangladeshi SME, not a statement of what your books must contain.

| Code | Account | নাম | Type | Role |
| --- | --- | --- | --- | --- |
| 1100 | Cash in Hand | হাতে নগদ | asset | |
| 1110 | Bank Account | ব্যাংক হিসাব | asset | |
| 1200 | Accounts Receivable | প্রাপ্য হিসাব | asset | |
| 1250 | Inventory | মজুদ পণ্য | asset | |
| 1310 | VAT Input / Rebateable | রেয়াতযোগ্য উপকরণ মূসক | asset | `vat_input` |
| 1320 | TDS Receivable | প্রাপ্য উৎসে কর্তিত কর | asset | `tds_receivable` |
| 1330 | Advance Income Tax | অগ্রিম আয়কর | asset | `advance_income_tax` |
| 1400 | Prepaid Expenses | অগ্রিম প্রদত্ত খরচ | asset | |
| 1500 | Furniture and Fixtures | আসবাবপত্র | asset | |
| 1510 | Office Equipment | অফিস সরঞ্জাম | asset | |
| 2100 | Accounts Payable | প্রদেয় হিসাব | liability | |
| 2200 | Salaries Payable | প্রদেয় বেতন | liability | |
| 2310 | VAT Output Payable | প্রদেয় মূসক | liability | `vat_output` |
| 2320 | TDS Payable | প্রদেয় উৎসে কর্তিত কর | liability | `tds_payable` |
| 2330 | VDS Payable | প্রদেয় উৎসে কর্তিত মূসক | liability | `vds_payable` |
| 2340 | Supplementary Duty Payable | প্রদেয় সম্পূরক শুল্ক | liability | `supplementary_duty_payable` |
| 2410 | Provident Fund Payable | প্রদেয় ভবিষ্য তহবিল | liability | `provident_fund_payable` |
| 2420 | Gratuity Provision | গ্র্যাচুইটি সঞ্চিতি | liability | `gratuity_provision` |
| 2430 | WPPF Payable | প্রদেয় শ্রমিক অংশগ্রহণ তহবিল | liability | `wppf_payable` |
| 2500 | Loans Payable | প্রদেয় ঋণ | liability | |
| 3100 | Owner's Capital | মালিকের মূলধন | equity | |
| 3200 | Retained Earnings | সংরক্ষিত মুনাফা | equity | |
| 4100 | Sales Revenue | বিক্রয় আয় | income | |
| 4200 | Service Revenue | সেবা আয় | income | |
| 5100 | Purchases | ক্রয় | expense | |
| 5200 | Cost of Goods Sold | বিক্রিত পণ্যের ব্যয় | expense | |
| 5300 | Direct Wages | প্রত্যক্ষ মজুরি | expense | |
| 6100 | Salaries and Wages | বেতন ও মজুরি | expense | |
| 6200 | Office Rent | অফিস ভাড়া | expense | |
| 6300 | Utilities | ইউটিলিটি বিল | expense | |
| 6400 | Telephone and Internet | টেলিফোন ও ইন্টারনেট | expense | |
| 6500 | Repairs and Maintenance | মেরামত ও রক্ষণাবেক্ষণ | expense | |
| 6600 | Depreciation Expense | অবচয় ব্যয় | expense | |
| 6700 | Professional Fees | পেশাদার ফি | expense | |
| 6800 | Bank Charges | ব্যাংক চার্জ | expense | |
| 6900 | Trade Licence and Government Fees | ট্রেড লাইসেন্স ও সরকারি ফি | expense | |
| 7100 | Interest Income | সুদ আয় | income | |
| 7200 | Other Income | অন্যান্য আয় | income | |
| 8100 | Interest Expense | সুদ ব্যয় | expense | |
| 8200 | Penalties and Fines | জরিমানা ও দণ্ড | expense | |
| 9100 | Income Tax Expense | আয়কর ব্যয় | expense | |
| 9200 | Provision for Income Tax | আয়কর সঞ্চিতি | liability | |

If a `src/templates/accounts.toml` exists in the checkout you run from, `init_books.py` copies
that instead and says so in its output (`accounts_from`). Pass `--templates DIR` to use a
chart of your own as the template for every new set of books.

## Extending the chart safely

### Adding an account

1. Pick the block from its type (a new bank account is `1xxx`, a new expense is `6xxx`).
2. Pick a free code inside the block. Codes only need to be unique; ordering is cosmetic.
3. Write the table with `code`, `name`, `type`, `normal` and, please, `name_bn`.
4. If the account plays one of the ten roles, add `role`. Two accounts with the same role is
   an error — the engine would not know which control account to reconcile.
5. Run `python3 src/engine/validate.py --books ./books`. The chart is loaded and checked
   before any journal row is read, so a bad chart fails fast with the line that broke it.

Some choices the core instruction already makes, so make the same ones in the chart:

- **bKash, Nagad, Rocket and other MFS wallets are separate asset accounts**, not cash. Give
  each its own `1xxx` code.
- **The owner's personal spending is drawings** — an equity account (`3xxx`), not an expense.
- **Supplementary duty is not VAT.** It has its own role, its own account and its own return
  line; never fold it into `vat_output`.
- **Advance income tax and TDS receivable are assets**, not expenses. They are money the
  authority already holds on your behalf.

### Renumbering

Codes are yours. If you renumber, change every journal row that uses the old code too — the
journal stores codes, not names — and re-run `validate.py`. The roles travel with the
accounts, so the tax engines keep working without any change.

### Retiring an account

Do not delete an account that has ever been posted to: every historical row would become
`unknown-account` and the books would stop validating. Instead:

```toml
[[account]]
code = "6900"
name = "Old Sundry Expense"
type = "expense"
normal = "debit"
tags = ["inactive"]
```

The account stays loadable, old reports still tie, and any *new* posting to it is a warning
(`inactive-account`) that points you at the replacement.

### Deleting an account

Only if no journal row has ever used it. Run `validate.py` afterwards; it is the check.

## Re-scaffolding

`init_books.py --force` rewrites `config.toml` and `accounts.toml` from the templates and
**never touches** journal CSVs. Use it to reset a chart you have made a mess of, but take a
copy first — hand-added accounts are lost, and any journal row that referenced them will fail
validation until you add them back.

## Questions the assistant will ask

When an LLM works with your books, the core instruction tells it to decide *which* accounts
an entry hits and then to run `post.py`. It will read `accounts.toml` to do that. Good names,
Bangla names and a short `description` on unusual accounts make its classification better
and its questions fewer. The assistant is told never to net input against output VAT, never
to post an owner's spending as an expense, and never to invent an account: an unknown code
is a refusal, not a guess.

## See also

- [Journal Format](Journal-Format) — the `account` and `tax_tag` columns
- [Engine Reference](Engine-Reference) — `init_books.py --templates`, `--force`, `--dry-run`
- [Troubleshooting](Troubleshooting) — `chart-block`, `chart-code-format`, `missing-required-role`, `inactive-account`
