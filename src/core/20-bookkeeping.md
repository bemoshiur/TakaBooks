# Bookkeeping

Every entry has two equal sides — debit / ডেবিট (what the business got) and credit / ক্রেডিট
(where it came from); `post.py` refuses otherwise. Blocks: `1xxx` assets · `2xxx` liabilities ·
`3xxx` equity · `4xxx` income · `5xxx` COGS · `6xxx` operating expenses · `7xxx`/`8xxx` other
income/expense · `9xxx` tax. Codes come from `accounts.toml`; tax accounts carry a `role`
(`vat_input`, `vat_output`, `tds_payable`…). Never net input against output মূসক.

Row: `date,entry_id,description,account,debit,credit,party,doc_ref,tax_tag,memo`; rows sharing
an `entry_id` balance; `party` is the customer or supplier, not an account; ask for `doc_ref`
rather than post blank. `tax_tag`: `VAT:OUT:<rate>` · `VAT:IN:<rate>` · `TDS:<section>:<rate>` ·
`VDS:<rate>` · `NONE`, values from the rates file. Owner's personal spending is **drawings, not
an expense**; bKash / Nagad / Rocket is an MFS account, not cash.
