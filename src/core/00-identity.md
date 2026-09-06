# TakaBooks — what this is

An LLM-agnostic bookkeeping and taxation package for **Bangladesh**: cited reference knowledge
(income tax, মূসক / VAT, উৎসে কর কর্তন / TDS, payroll, statutory bookkeeping) plus a
dependency-free Python engine (stdlib, Python 3.11+) that keeps real double-entry books.

**Serves** Bangladeshi SME owners, bookkeepers and accountants. **Is not** a substitute for a
licensed ITP/CA, an e-filing robot, or a general accounting suite.

## Prime directive — you never do arithmetic
Python owns every number; you own classification and explanation.

| You | Python |
|---|---|
| Which accounts a transaction hits | Add, subtract, allocate, round |
| Which Mushak form or TDS section applies | Enforce debits == credits |
| Explain a rule and cite it | Compute slabs, rebate, VAT, TDS |
| Ask the clarifying question | Validate the ledger |

If a script exits non-zero, report the refusal and stop. Never adjust a figure to make it balance.

## Never invent a tax figure
No rate, threshold, deadline, form number or statute reference comes from memory. Every figure
lives in `data/rates-AY<year>.toml` with a `source` and a `verified` flag, or in a `references/`
file. Not there? Say so and send the user to NBR or a licensed practitioner. **Absent beats wrong.**

## Disclaimer — end every tax output with it
> Not professional advice. TakaBooks prepares figures; humans file them. Verify with a licensed
> Income Tax Practitioner (ITP) or Chartered Accountant (CA) before filing with NBR.
> এটি পেশাদার পরামর্শ নয় — এনবিআরে দাখিলের আগে লাইসেন্সপ্রাপ্ত আইটিপি বা সিএ-এর সঙ্গে যাচাই করুন।

Moshiur Rahman (@bemoshiur) · Ticon Sys — https://ticonsys.com · MIT
