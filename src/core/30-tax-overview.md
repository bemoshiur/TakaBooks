# Which reference to load

Load the smallest file that answers the question; never answer from memory when a reference
exists. Files below live in `references/`; every rate comes from `data/rates-AY<year>.toml`.

| Question about | Load |
|---|---|
| Income tax: slabs, rebate, minimum tax, surcharge, corporate rate | `income-tax.md` |
| মূসক / VAT: rates, registration, Mushak forms, input rebate | `vat-mushak.md` |
| উৎসে কর কর্তন / TDS on a payment, VDS on a supply, deposit duties | `withholding-tds-vds.md` |
| Salary tax, provident fund, gratuity, WPPF, welfare fund | `payroll.md` |
| Which books to keep, audit, accounting standards | `bookkeeping-standards.md` |
| "When is it due?" — any recurring return, deposit or renewal | `compliance-calendar.md` |
| Late filing or deposit, interest, penalty exposure | `penalties.md` |
| A Bangla term in English, or one to search on the NBR portal | `glossary-bn-en.md` |

## Routing rules
- **Two taxes, two Acts.** মূসক / VAT and income tax have separate rates, returns, deadlines and
  registration numbers (BIN vs TIN). Decide which is meant; ask if ambiguous.
- **"Advance tax" is ambiguous.** Advance tax at import is VAT-side, recovered inside the VAT
  return; অগ্রিম আয়কর / AIT is income-tax-side, set off against assessed tax. Confirm which.
- **Withholding has two sides.** Deducted *from* the user = a receivable plus a certificate to
  collect; deducted *by* the user = a liability plus a deposit and a certificate to issue.
- **Deadlines travel with penalties**; a broad question ("what do I owe this month?") starts at
  the compliance calendar, then opens only what it points to.
- **Nothing covers it?** Say so, point at NBR (https://nbr.gov.bd) and a licensed ITP/CA, and do
  not improvise a figure.
