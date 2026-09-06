# Bookkeeping

## Double-entry, plainly
Every transaction is written twice: what the business **got** (debit / ডেবিট) and where it **came
from** (credit / ক্রেডিট). The sides are equal; rows sharing an `entry_id` are one entry and must
balance or `post.py` refuses them. Assets and expenses grow by debit; liabilities, equity and
income grow by credit.

## Account codes
`1xxx` assets · `2xxx` liabilities · `3xxx` equity · `4xxx` income · `5xxx` cost of goods sold ·
`6xxx` operating expenses · `7xxx` other income · `8xxx` other expense · `9xxx` tax and statutory.
Read real codes and Bangla names from `accounts.toml`; an unknown code is a hard error.
**Never net the `9xxx` block** — উপকরণ কর / input VAT stays separate from উৎপাদ কর / output VAT,
TDS receivable from TDS payable. Both returns want gross figures.

## The journal row
`date,entry_id,description,account,debit,credit,party,doc_ref,tax_tag,memo`
- `date` is ISO `YYYY-MM-DD`; amounts are decimal BDT, exactly one of debit/credit non-zero.
- `party` is the customer or supplier — not an account. One control account per class.
- `doc_ref` is the voucher, চালান, Mushak 6.3 or bill number. Ask for it rather than posting blank
  on any line touching cash, bank or a `9xxx` account.
- `tax_tag` is `VAT:OUT:<rate>` · `VAT:IN:<rate>` · `TDS:<section>:<rate>` · `VDS:<rate>` · `NONE`,
  every `<rate>` and `<section>` taken from the rates file, never from memory.

## Classifying a BD SME transaction
- Owner's personal spending is **drawings (3xxx), not an expense** — the commonest error here.
- bKash / Nagad / Rocket belong in the MFS account, not "cash".
- Import duty, C&F, port, clearing and carriage inward are cost of goods, not operating expense.
- আবগারি শুল্ক / excise duty debited by a bank is its own `9xxx` line, not bank charges.
- Unidentified money goes to suspense with a memo — never into cash to balance the day.
- Unclear? Ask. A guessed classification becomes a wrong return.

Journals live at `books/journal/YYYY-MM.csv`. Run `validate.py` before trusting any report, and
never hand-edit a posted journal — post a correcting entry, dated today, with a memo.
