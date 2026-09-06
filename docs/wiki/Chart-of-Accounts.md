# Chart of Accounts — হিসাব তালিকা

`books/accounts.toml` lists every account the journal may post to. The engine loads it,
validates it, and refuses any posting to a code it cannot find. This page explains the file,
the code blocks, the `role` keys that make the Bangladesh-specific accounts findable, the
**131-account chart that actually ships**, and how to extend it without breaking anything.

## The file

```toml
[[account]]
code = "1100"
name = "Cash in Hand"
name_bn = "হাতে নগদ"
type = "asset"          # asset | liability | equity | income | expense
normal = "debit"        # debit | credit
tags = ["cash"]
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
| `description` | no | Free text for humans and the assistant. Every account in the shipped chart has one. |
| `role` | no | One of the ten Bangladesh-specific roles. This is what the tax engines look up. |
| `tags` | no | A string or list of strings. See *Tags that mean something* below. |

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

### Tags that mean something

Tags are free labels, but the engine and the assistant read a few of them:

| Tag | Effect |
| --- | --- |
| `contra` | The balance runs opposite to its class and is presented as a deduction (`1290` Provision for Doubtful Debts, `1690` Accumulated Depreciation, `4190` Sales Return, `3300` Drawings). |
| `control` | One account standing for many parties. The journal's `party` column keeps the party-wise খতিয়ান / ledger — **never open one account per customer**. |
| `cash`, `bank`, `mfs` | Money accounts. Every posting to one should carry a `doc_ref`. |
| `vds`, `tds`, `withholding` | Tells `validate.py` the account is a tax control account. |
| `inactive`, `archived`, `closed`, `disabled`, `retired` | Retires the account: `post.py` **refuses** a new posting to it (exit 3). |

Tally-era aliases (`sundry-debtors`, `sundry-creditors`, `duties-and-taxes`) are kept as tags
so an assistant can map what an owner says to the right code.

## Code blocks

The leading digit of a code says what kind of account it is. `validate.py` warns
(`chart-block`) when an account's leading digit disagrees with its `type`:

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
| `9xxx` | Tax and statutory accounts | কর হিসাব | asset, liability or expense |

Within a block the numbering is yours. The shipped chart allocates in steps of 5 or 10 so you
can insert your own accounts (`1152 Bank — second account`, `1161 bKash merchant`) without
renumbering anything.

A code that is not four digits (with the optional suffix) is a `chart-code-format` warning.
It still works; it is flagged because the assistant and the reports assume the convention.

**No Bangladeshi authority prescribes account codes.** The codes are this project's; the
*names* carry the weight, and the মূসক / VAT terms in them are the statutory ones. Keep the
names, renumber freely.

## Roles — the accounts Bangladesh needs

Ten accounts are mandatory for a complete chart, and the engine finds them by **`role`, not by
code**. Renumber as you like; keep the role key on whichever account plays the part.
`validate.py` warns `missing-required-role` for each one absent, and two accounts sharing a
role is an error.

| `role` | Type | In the shipped chart | Purpose |
| --- | --- | --- | --- |
| `vat_input` | asset | `9100` | রেয়াতযোগ্য উপকরণ কর — rebateable input VAT you have paid and may claim |
| `vat_output` | liability | `9200` | প্রদেয় উৎপাদ কর — output VAT you have charged and owe |
| `tds_receivable` | asset | `9300` | উৎসে কর্তিত আয়কর (প্রাপ্য) — tax your customers deducted from your invoices |
| `tds_payable` | liability | `9320` | উৎসে কর্তিত আয়কর (প্রদেয়) — tax you deducted from vendors and must deposit |
| `vds_payable` | liability | `9220` | উৎসে কর্তিত মূসক (প্রদেয়) — VAT you deducted at source from suppliers |
| `advance_income_tax` | asset | `9310` | অগ্রিম আয়কর — advance tax paid, to set off against the assessed liability |
| `provident_fund_payable` | liability | `9400` | প্রদেয় ভবিষ্য তহবিল |
| `gratuity_provision` | liability | `9410` | আনুতোষিক (গ্র্যাচুইটি) সংস্থান |
| `wppf_payable` | liability | `9420` | শ্রমিক অংশগ্রহণ তহবিল — Workers' Profit Participation Fund |
| `supplementary_duty_payable` | liability | `9210` | প্রদেয় সম্পূরক শুল্ক — kept apart from VAT, in its own account and return line |

How the roles are used today:

- `vat.py` reads `vat_output`, `vat_input` and `vds_payable` to find the control accounts,
  reconcile their movement against the tagged postings, and build the return figures.
- `validate.py` uses the tax roles to check that a `tax_tag` sits on an account of the
  matching tax (`tax-tag-account-mismatch` otherwise).
- `post.py` shows the account's full name beside each line in its confirmation, so a wrong
  choice is visible before anything is written.

### Two rules that fall out of the 9xxx block

1. **Never net.** `9100` is never netted against `9200` in the ledger, nor `9300` against
   `9320`. মূসক ৯.১ / Mushak 9.1 and the income tax return both want the gross figures, and
   `vat.py` computes the net position for the return — that is where netting belongs.
2. **Every `9xxx` balance must be provable by a document.** `9100` by a মূসক ৬.৩ / Mushak 6.3
   tax invoice entered in মূসক ৬.১ / Mushak 6.1; `9120` by a মূসক ৬.৬ / Mushak 6.6 received;
   `9220` by a Mushak 6.6 issued plus a treasury challan; `9300` by a deduction certificate.

## The chart that ships

`src/templates/accounts.toml` holds **131 accounts**, and `init_books.py` copies it into your
`books/` directory. From then on it is yours — delete what you do not need, add what you do.
The scripts only ever *read* it.

It is a starting point for a Bangladeshi SME — a trading business or a service business — not
a statement of what your books must contain, and it is not blessed by any authority. Every
account carries a one-sentence `description` in the file itself; the tables below give code,
name, type, role and tags.

> **No rate, threshold, deadline or section number appears in `accounts.toml`, by design.**
> Those live in `src/data/rates-AY<year>.toml` with a source URL and a `verified` flag. See
> [Updating Tax Rates](Updating-Tax-Rates).

### `1xxx` — সম্পদ / Assets (32)

| Code | Account | নাম | Type | Role | Tags |
| --- | --- | --- | --- | --- | --- |
| 1100 | Cash in Hand | হাতে নগদ | asset |  | `cash` |
| 1110 | Petty Cash | খুচরা নগদান | asset |  | `cash` |
| 1150 | Cash at Bank — Current Account | ব্যাংক হিসাব — চলতি | asset |  | `bank` |
| 1155 | Cash at Bank — STD / Savings | ব্যাংক হিসাব — এসটিডি/সঞ্চয়ী | asset |  | `bank` |
| 1160 | Mobile Financial Services (bKash / Nagad / Rocket) | মোবাইল আর্থিক সেবা হিসাব (বিকাশ/নগদ/রকেট) | asset |  | `mfs` `bank` |
| 1170 | Fixed Deposit Receipt (FDR) | স্থায়ী আমানত (এফডিআর) | asset |  | `bank` `investment` |
| 1200 | Accounts Receivable — Trade | প্রাপ্য হিসাব — বাণিজ্যিক (দেনাদার) | asset |  | `control` `receivable` `sundry-debtors` |
| 1210 | Receivable from Related Parties | সংশ্লিষ্ট পক্ষের নিকট প্রাপ্য | asset |  | `control` `related-party` |
| 1220 | Other Receivables | অন্যান্য প্রাপ্য | asset |  | `control` |
| 1290 | Provision for Doubtful Debts (contra) | অনাদায়ী পাওনার সংস্থান | asset |  | `contra` |
| 1300 | Advance to Suppliers | সরবরাহকারীকে প্রদত্ত অগ্রিম | asset |  | `control` `advance` |
| 1310 | Advance against Salary | বেতন বাবদ অগ্রিম | asset |  | `control` `advance` `payroll` |
| 1320 | Security Deposit | জামানত জমা | asset |  | `advance` |
| 1330 | Prepaid Expenses | অগ্রিম প্রদত্ত খরচ | asset |  | `advance` |
| 1340 | LC Margin / Advance for Import | ঋণপত্র (এলসি) মার্জিন ও আমদানি অগ্রিম | asset |  | `advance` `import` |
| 1400 | Inventory — Stock in Trade | মজুদ পণ্য | asset |  | `inventory` |
| 1410 | Inventory — Raw Materials | মজুদ — কাঁচামাল | asset |  | `inventory` |
| 1420 | Inventory — Work in Progress | মজুদ — উৎপাদনাধীন পণ্য | asset |  | `inventory` |
| 1430 | Inventory — Finished Goods | মজুদ — প্রস্তুত পণ্য | asset |  | `inventory` |
| 1440 | Inventory — Packing Materials | মজুদ — মোড়কীকরণ সামগ্রী | asset |  | `inventory` |
| 1450 | Inventory — Spare Parts & Consumables | মজুদ — যন্ত্রাংশ ও ভোগ্য সামগ্রী | asset |  | `inventory` |
| 1600 | Land | জমি | asset |  | `fixed-asset` |
| 1610 | Building | দালানকোঠা | asset |  | `fixed-asset` |
| 1620 | Plant & Machinery | কল-কারখানা ও যন্ত্রপাতি | asset |  | `fixed-asset` |
| 1630 | Furniture & Fixtures | আসবাবপত্র ও সরঞ্জামাদি | asset |  | `fixed-asset` |
| 1640 | Office Equipment | অফিস সরঞ্জাম | asset |  | `fixed-asset` |
| 1650 | Computer & ICT Equipment | কম্পিউটার ও আইসিটি সরঞ্জাম | asset |  | `fixed-asset` |
| 1660 | Motor Vehicles | মোটরযান | asset |  | `fixed-asset` |
| 1670 | Capital Work in Progress | নির্মাণাধীন সম্পদ | asset |  | `fixed-asset` |
| 1690 | Accumulated Depreciation (contra) | পুঞ্জীভূত অবচয় | asset |  | `contra` `fixed-asset` |
| 1700 | Intangible Assets — Software & Licences | অমূর্ত সম্পদ — সফটওয়্যার ও লাইসেন্স | asset |  | `fixed-asset` `intangible` |
| 1790 | Accumulated Amortisation (contra) | পুঞ্জীভূত অবলোপন | asset |  | `contra` `intangible` |

### `2xxx` — দায় / Liabilities (12)

| Code | Account | নাম | Type | Role | Tags |
| --- | --- | --- | --- | --- | --- |
| 2100 | Accounts Payable — Trade | প্রদেয় হিসাব — বাণিজ্যিক (পাওনাদার) | liability |  | `control` `payable` `sundry-creditors` |
| 2110 | Payable to Related Parties | সংশ্লিষ্ট পক্ষকে প্রদেয় | liability |  | `control` `related-party` |
| 2120 | Accrued Expenses | বকেয়া ব্যয় | liability |  |  |
| 2130 | Salary & Wages Payable | প্রদেয় বেতন ও মজুরি | liability |  | `payroll` |
| 2140 | Advance from Customers | ক্রেতার নিকট হইতে অগ্রিম | liability |  | `control` |
| 2150 | Utility Bills Payable | প্রদেয় ইউটিলিটি বিল | liability |  |  |
| 2200 | Bank Overdraft | ব্যাংক জমাতিরিক্ত (ওডি) | liability |  | `bank` `loan` |
| 2210 | Short-term Bank Loan / CC (Hypo) | স্বল্পমেয়াদি ব্যাংক ঋণ / সিসি (হাইপো) | liability |  | `loan` |
| 2220 | Long-term Loan | দীর্ঘমেয়াদি ঋণ | liability |  | `loan` |
| 2230 | Lease / Hire-purchase Liability | ইজারা ও কিস্তি-ক্রয় দায় | liability |  | `loan` |
| 2300 | Loan from Directors / Proprietor | পরিচালক/মালিকের নিকট হইতে ঋণ | liability |  | `loan` `related-party` `owner` |
| 2900 | Suspense Account | সাসপেন্স হিসাব | liability |  | `suspense` |

### `3xxx` — মূলধন / Equity (6)

| Code | Account | নাম | Type | Role | Tags |
| --- | --- | --- | --- | --- | --- |
| 3100 | Share Capital / Owner's Capital | শেয়ার মূলধন / মালিকের মূলধন | equity |  | `owner` |
| 3110 | Share Money Deposit | শেয়ার মানি ডিপোজিট | equity |  | `owner` |
| 3200 | Retained Earnings | সংরক্ষিত আয় (অবণ্টিত মুনাফা) | equity |  |  |
| 3210 | Profit / (Loss) for the Year | চলতি বছরের মুনাফা/(ক্ষতি) | equity |  |  |
| 3300 | Drawings | উত্তোলন | equity |  | `owner` `contra` |
| 3400 | Revaluation Reserve | পুনর্মূল্যায়ন সংরক্ষিত তহবিল | equity |  |  |

### `4xxx` — আয় / Income (5)

| Code | Account | নাম | Type | Role | Tags |
| --- | --- | --- | --- | --- | --- |
| 4100 | Sales — Local | বিক্রয় — স্থানীয় | income |  |  |
| 4110 | Sales — Export | বিক্রয় — রপ্তানি | income |  |  |
| 4120 | Service Revenue | সেবা আয় | income |  |  |
| 4130 | Commission Income | কমিশন আয় | income |  |  |
| 4190 | Sales Return & Discount Allowed (contra) | বিক্রয় ফেরত ও প্রদত্ত বাট্টা | income |  | `contra` |

### `5xxx` — বিক্রীত পণ্যের ব্যয় / Cost of goods sold (10)

| Code | Account | নাম | Type | Role | Tags |
| --- | --- | --- | --- | --- | --- |
| 5100 | Purchases — Local | ক্রয় — স্থানীয় | expense |  |  |
| 5110 | Purchases — Import | ক্রয় — আমদানি | expense |  | `import` |
| 5120 | Customs Duty & Regulatory Duty | আমদানি শুল্ক ও নিয়ন্ত্রণমূলক শুল্ক | expense |  | `import` |
| 5130 | C&F, Port & Clearing Charges | সিএন্ডএফ, বন্দর ও খালাস ব্যয় | expense |  | `import` |
| 5140 | Carriage Inward / Freight-in | আগত পরিবহন ব্যয় | expense |  |  |
| 5190 | Purchase Return & Discount Received (contra) | ক্রয় ফেরত ও প্রাপ্ত বাট্টা | expense |  | `contra` |
| 5200 | Direct Wages | প্রত্যক্ষ মজুরি | expense |  | `payroll` |
| 5210 | Factory Overhead | কারখানা উপরিব্যয় | expense |  |  |
| 5220 | Contractual Manufacturing Charges | চুক্তিভিত্তিক উৎপাদন ব্যয় | expense |  |  |
| 5900 | Change in Inventory | মজুদের পরিবর্তন | expense |  | `inventory` |

### `6xxx` — পরিচালন ব্যয় / Operating expenses (34)

| Code | Account | নাম | Type | Role | Tags |
| --- | --- | --- | --- | --- | --- |
| 6100 | Salary & Allowances | বেতন ও ভাতাদি | expense |  | `payroll` |
| 6110 | Festival Bonus | উৎসব বোনাস | expense |  | `payroll` |
| 6120 | Overtime | অতিরিক্ত সময়ের মজুরি | expense |  | `payroll` |
| 6130 | Staff Welfare | কর্মচারী কল্যাণ ব্যয় | expense |  | `payroll` |
| 6140 | Employer Contribution to Provident Fund | ভবিষ্য তহবিলে নিয়োগকর্তার চাঁদা | expense |  | `payroll` |
| 6150 | Gratuity Expense | আনুতোষিক (গ্র্যাচুইটি) ব্যয় | expense |  | `payroll` |
| 6200 | Office Rent | অফিস ভাড়া | expense |  |  |
| 6210 | Godown / Warehouse Rent | গুদাম ভাড়া | expense |  |  |
| 6220 | Electricity Bill | বিদ্যুৎ বিল | expense |  | `utilities` |
| 6230 | Gas & Water Bill | গ্যাস ও পানির বিল | expense |  | `utilities` |
| 6240 | Internet & Telephone | ইন্টারনেট ও টেলিফোন | expense |  | `utilities` |
| 6300 | Conveyance | যাতায়াত ব্যয় | expense |  |  |
| 6310 | Travelling — Local & Foreign | ভ্রমণ ব্যয় — দেশি ও বিদেশি | expense |  |  |
| 6320 | Entertainment | আপ্যায়ন ব্যয় | expense |  |  |
| 6330 | Vehicle Fuel & Maintenance | যানবাহনের জ্বালানি ও রক্ষণাবেক্ষণ | expense |  |  |
| 6400 | Printing & Stationery | মুদ্রণ ও মনিহারি | expense |  |  |
| 6410 | Postage & Courier | ডাক ও কুরিয়ার | expense |  |  |
| 6420 | Repairs & Maintenance | মেরামত ও রক্ষণাবেক্ষণ | expense |  |  |
| 6430 | Office Maintenance & Cleaning | অফিস রক্ষণাবেক্ষণ ও পরিচ্ছন্নতা | expense |  |  |
| 6440 | Security Service | নিরাপত্তা সেবা ব্যয় | expense |  |  |
| 6500 | Advertisement & Publicity | বিজ্ঞাপন ও প্রচার | expense |  |  |
| 6510 | Sales Promotion & Sample | বিক্রয় প্রসার ও নমুনা | expense |  |  |
| 6600 | Audit Fee | নিরীক্ষা ফি | expense |  |  |
| 6610 | Legal & Professional Fees | আইন ও পেশাগত ফি | expense |  |  |
| 6620 | Consultancy Fee | পরামর্শ ব্যয় | expense |  |  |
| 6700 | Bank Charges & Commission | ব্যাংক চার্জ ও কমিশন | expense |  |  |
| 6710 | Insurance Premium | বিমা প্রিমিয়াম | expense |  |  |
| 6720 | Trade Licence, Renewal & Government Fees | ট্রেড লাইসেন্স, নবায়ন ও সরকারি ফি | expense |  |  |
| 6730 | RJSC & Regulatory Filing Fees | আরজেএসসি ও নিয়ন্ত্রক দাখিল ফি | expense |  |  |
| 6740 | Donation & Subscription | অনুদান ও চাঁদা | expense |  |  |
| 6750 | Training & Development | প্রশিক্ষণ ও উন্নয়ন ব্যয় | expense |  |  |
| 6800 | Depreciation | অবচয় | expense |  |  |
| 6810 | Amortisation | অবলোপন | expense |  |  |
| 6900 | Miscellaneous Expenses | বিবিধ ব্যয় | expense |  |  |

### `7xxx` — অন্যান্য আয় / Other income (6)

| Code | Account | নাম | Type | Role | Tags |
| --- | --- | --- | --- | --- | --- |
| 7100 | Interest Income — Bank / FDR | সুদ আয় — ব্যাংক/এফডিআর | income |  |  |
| 7110 | Rental Income | ভাড়া আয় | income |  |  |
| 7120 | Gain on Disposal of Fixed Asset | সম্পদ বিক্রয়জনিত মুনাফা | income |  |  |
| 7130 | Foreign Exchange Gain | বৈদেশিক মুদ্রা বিনিময় লাভ | income |  |  |
| 7140 | Scrap Sale | উচ্ছিষ্ট বিক্রয় | income |  |  |
| 7190 | Sundry Income | বিবিধ আয় | income |  |  |

### `8xxx` — অন্যান্য ব্যয় / Other expenses (6)

| Code | Account | নাম | Type | Role | Tags |
| --- | --- | --- | --- | --- | --- |
| 8100 | Interest on Loan | ঋণের সুদ | expense |  |  |
| 8110 | Loss on Disposal of Fixed Asset | সম্পদ বিক্রয়জনিত ক্ষতি | expense |  |  |
| 8120 | Foreign Exchange Loss | বৈদেশিক মুদ্রা বিনিময় ক্ষতি | expense |  |  |
| 8130 | Bad Debt Written Off | অনাদায়ী পাওনা অবলোপন | expense |  |  |
| 8140 | Fine & Penalty (non-deductible) | জরিমানা ও দণ্ড (অগ্রাহ্য) | expense |  | `non-deductible` |
| 8150 | Prior Year Adjustment | পূর্ববর্তী বছরের সমন্বয় | expense |  |  |

### `9xxx` — কর হিসাব / Tax and statutory (20)

| Code | Account | নাম | Type | Role | Tags |
| --- | --- | --- | --- | --- | --- |
| 9100 | VAT Input / Rebateable | উপকরণ কর (রেয়াতযোগ্য মূসক) | asset | `vat_input` | `mushak` `duties-and-taxes` |
| 9105 | VAT Input — Non-rebateable | অরেয়াতযোগ্য উপকরণ কর | expense |  | `mushak` `duties-and-taxes` |
| 9110 | Advance Tax (AT) at Import | আমদানি পর্যায়ে অগ্রিম কর | asset |  | `mushak` `import` `duties-and-taxes` |
| 9120 | VDS Deducted by Customers | গ্রাহক কর্তৃক উৎসে কর্তিত মূসক | asset |  | `vds` `mushak` `duties-and-taxes` |
| 9130 | VAT Treasury Deposit / Current Account | মূসক চলতি হিসাব ও ট্রেজারি জমা | asset |  | `mushak` `duties-and-taxes` |
| 9200 | VAT Output Payable | প্রদেয় উৎপাদ কর (মূসক) | liability | `vat_output` | `mushak` `duties-and-taxes` |
| 9210 | Supplementary Duty Payable | প্রদেয় সম্পূরক শুল্ক | liability | `supplementary_duty_payable` | `mushak` `duties-and-taxes` |
| 9220 | VDS Payable | উৎসে কর্তিত মূসক (প্রদেয়) | liability | `vds_payable` | `mushak` `duties-and-taxes` |
| 9230 | Excise Duty | আবগারি শুল্ক | expense |  | `duties-and-taxes` |
| 9240 | Surcharges Payable (Development / ICT / Health Care / Environmental Protection) | উন্নয়ন, আইসিটি উন্নয়ন, স্বাস্থ্যসেবা ও পরিবেশ সুরক্ষা সারচার্জ | liability |  | `mushak` `duties-and-taxes` |
| 9300 | TDS Receivable — deducted by customers | গ্রাহক কর্তৃক উৎসে কর্তিত আয়কর (প্রাপ্য) | asset | `tds_receivable` | `duties-and-taxes` |
| 9310 | Advance Income Tax (AIT) | অগ্রিম আয়কর | asset | `advance_income_tax` | `duties-and-taxes` |
| 9320 | TDS Payable — deducted from vendors | সরবরাহকারী হইতে উৎসে কর্তিত আয়কর (প্রদেয়) | liability | `tds_payable` | `duties-and-taxes` |
| 9325 | TDS Payable — Salary | উৎসে কর্তিত আয়কর — বেতন (প্রদেয়) | liability |  | `tds` `withholding` `payroll` `duties-and-taxes` |
| 9330 | Provision for Income Tax | আয়কর সংস্থান | liability |  | `duties-and-taxes` |
| 9340 | Income Tax Payable (net of AIT/TDS) | প্রদেয় আয়কর (নীট) | liability |  | `duties-and-taxes` |
| 9400 | Provident Fund Payable | প্রদেয় ভবিষ্য তহবিল | liability | `provident_fund_payable` | `payroll` `duties-and-taxes` |
| 9410 | Gratuity Provision | আনুতোষিক (গ্র্যাচুইটি) সংস্থান | liability | `gratuity_provision` | `payroll` `duties-and-taxes` |
| 9420 | WPPF Payable | শ্রমিক অংশগ্রহণ তহবিল (প্রদেয়) | liability | `wppf_payable` | `payroll` `duties-and-taxes` |
| 9430 | Workers' Welfare Fund & WWF Payable | শ্রমিক কল্যাণ তহবিল ও শ্রমিক কল্যাণ ফাউন্ডেশন তহবিল (প্রদেয়) | liability |  | `payroll` `duties-and-taxes` |

## The 42-account fallback — and why you probably have not seen it

`init_books.py` embeds a second, much smaller chart of **42 accounts**. It is used **only**
when `src/templates/accounts.toml` cannot be found — a bare copy of the script with no
templates directory beside it — so that the tool still works standalone. In a normal
checkout or a release bundle you will never get it.

You can tell which one you got from the line `init_books.py` prints:

```
হিসাব তালিকা / chart of accounts  131 accounts from /path/to/TakaBooks/src/templates/accounts.toml
```

versus

```
হিসাব তালিকা / chart of accounts  42 accounts from built-in Bangladesh chart of accounts
```

The two charts **use different codes for the tax accounts** — the fallback puts VAT output at
`2310` and VAT input at `1310`, where the shipped chart uses `9200` and `9100`. If you are
following any document that posts VAT to `2310`, it was written against the fallback and the
shipped chart will refuse it (exit 3). Always read the `accounts.toml` in *your* `books/`
directory rather than trusting a code you saw in a guide.

## Extending the chart safely

### Adding an account

1. Pick the block from its type (a new bank account is `1xxx`, a new expense is `6xxx`).
2. Pick a free code inside the block. The shipped chart leaves gaps of 5 or 10 for exactly
   this. Codes only need to be unique; ordering is cosmetic.
3. Write the table with `code`, `name`, `type`, `normal` and, please, `name_bn` and a
   `description`.
4. If the account plays one of the ten roles, add `role`. Two accounts with the same role is
   an error — the engine would not know which control account to reconcile.
5. Run `python3 src/engine/validate.py --books books`. The chart is loaded and checked
   before any journal row is read, so a bad chart fails fast with the line that broke it.

Some choices the core instruction already makes, so make the same ones in the chart:

- **bKash, Nagad, Rocket and other MFS wallets are separate asset accounts**, not cash. The
  shipped chart gives them `1160`; open `1161`, `1162` and so on per wallet if you need to.
- **The owner's personal spending is drawings** — `3300`, an equity account tagged `contra`,
  not an expense.
- **Supplementary duty is not VAT.** It has its own role, its own account (`9210`) and its own
  return line; never fold it into `vat_output`.
- **Advance income tax and TDS receivable are assets** (`9310`, `9300`), not expenses. They
  are money the authority already holds on your behalf.
- **One control account, many parties.** Use the journal's `party` column for the party-wise
  ledger instead of opening `1200.KARIM`, `1200.ASHRAF` and so on.

### Renumbering

Codes are yours. If you renumber, change every journal row that uses the old code too — the
journal stores codes, not names — and re-run `validate.py`. The roles travel with the
accounts, so the tax engines keep working without any change.

### Retiring an account

Do not delete an account that has ever been posted to: every historical row would become
`unknown-account` and the books would stop validating. Instead, tag it:

```toml
[[account]]
code = "6900"
name = "Miscellaneous Expenses"
name_bn = "বিবিধ ব্যয়"
type = "expense"
normal = "debit"
tags = ["inactive"]
```

The account stays loadable and old reports still tie, but a **new** posting to it is refused:

```
error: --debit #1: account 6900 Miscellaneous Expenses (বিবিধ ব্যয়) is tagged 'inactive' in accounts.toml; posting to a retired account is refused.
  hint: Post to its replacement account, or drop the tag from accounts.toml if the account is in use again.
```

Exit code 3. Any of `inactive`, `archived`, `closed`, `disabled` or `retired` has this effect.

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

- The file itself:
  https://github.com/bemoshiur/TakaBooks/blob/main/src/templates/accounts.toml
- [Journal Format](Journal-Format) — the `account` and `tax_tag` columns
- [Getting Started](Getting-Started) — these codes used in a worked walkthrough
- [Engine Reference](Engine-Reference) — `init_books.py --templates`, `--force`, `--dry-run`
- [Troubleshooting](Troubleshooting) — `chart-block`, `chart-code-format`, `missing-required-role`, retired accounts
