# Withholding — উৎসে কর কর্তন (TDS) ও উৎসে মূসক কর্তন (VDS)

**Current as of:** 6 September 2026 · assessment year 2026-27 (করবর্ষ ২০২৬-২৭), income year
1 July 2025 – 30 June 2026. Deductions being made *today* follow Finance Act 2026 and the
উৎসে কর বিধিমালা ২০২৬ rates below.
**Assessment year:** machine-readable figures live in `data/rates-AY2026-27.toml` under `[tds]`
and `[vds]`. The rate matrix is reproduced here for reading; the TOML is what the engine
computes from. **Change one and you must change the other.**
**Sources:** primary only.
· **[SRO273]** উৎসে কর বিধিমালা, ২০২৬ = এস.আর.ও. নং ২৭৩-আইন/আয়কর-৫/২০২৬, gazetted 5 July 2026 —
  <https://nbr.gov.bd/uploads/rules/With_holding_2026.pdf>
· **[PARI]** আয়কর পরিপত্র ২০২৬-২০২৭, 2 September 2026 —
  <https://nbr.gov.bd/uploads/paripatra/আয়কর_পরিপত্র_২০২৬-২০২৭.pdf>
· **[ACT]** আয়কর আইন, ২০২৩, consolidated through Finance Act 2026 —
  <http://bdlaws.minlaw.gov.bd/act-details-1429.html>
· **[SRO182]** উৎসে মূসক কর্তন ও আদায় বিধিমালা, ২০২৫ = এস.আর.ও. ১৮২-আইন/২০২৫/৩১০-মূসক, 27 May 2025 —
  <https://nbr.gov.bd/uploads/sros/VATSRO-1822.pdf>
· **[SRO140]** এস.আর.ও. ১৪০-আইন/২০২৬/৩৪৫-মূসক, 7 June 2026 —
  <https://nbr.gov.bd/uploads/sros/VAT_SRO-140.pdf>
· **[VATACT]** মূল্য সংযোজন কর ও সম্পূরক শুল্ক আইন, ২০১২ — <http://bdlaws.minlaw.gov.bd/act-1106.html>
**Status:** POPULATED. Every TDS and VDS rate below was read from primary text — the SRO
gazettes, NBR's own Paripatra, and the consolidated statute on bdlaws. Rules 6, 7 and 8 of
SRO 273 — property transfer, developers, and the import-stage HS-code schedules — were
transcribed from the gazette page images and are no longer out of scope; the fixed amounts under
ss.138, 138A and 139 come from the Act's own tables, because **SRO 273 does not contain them**.
The one figure that is **not** primary-verified, and the two questions the gazette itself does not
settle, are named explicitly in [§13](#13-what-this-file-does-not-hold). Nothing here is inferred
from a practitioner chart.

> **Not professional advice.** Verify with a licensed Income Tax Practitioner (ITP) or Chartered
> Accountant (CA) before you deduct, deposit or file. A short deduction costs the payer 150% of
> the tax under s.56(1); a missed deduction costs the same.

---

## 1. Read this before you use any rate

### 1.1 Which instrument actually sets the TDS rates — the single biggest trap of FY2026-27

| Instrument | What it is | Status |
|---|---|---|
| আয়কর আইন, ২০২৩ Part 7, ss.86–153 | Charging provisions and statutory ceilings | In force, text current through Finance Act 2026 |
| অর্থ আইন, ২০২৬ (Act 96 of 2026) | Amends the ITA 2023 | Effective **1 July 2026** |
| অর্থ (২০২৫-২০২৬ অর্থ বৎসর) আইন, ২০২৬ (Act 89 of 2026) | Separate, earlier 2026 Act for FY2025-26 | Its amendments are in the current text and remain in force |
| **এস.আর.ও. ২৭৩-আইন/আয়কর-৫/২০২৬ — উৎসে কর বিধিমালা, ২০২৬** | **The rules that actually set most rates**, made under s.343 | Gazetted **5 July 2026**, deemed effective **1 July 2026** |
| এস.আর.ও. ২১০-আইন/আয়কর-১/২০২৬ (8 June 2026) | Earlier rules of the **identical title** | **REPEALED** by Rule 14 of SRO 273 |

> ⚠️ **Two SROs of 2026 carry the same title, উৎসে কর বিধিমালা ২০২৬.** SRO 210 of 8 June 2026 was
> expressly repealed by Rule 14 of SRO 273 of 5 July 2026. **Nearly every FY2026-27 TDS chart in
> circulation reproduces the repealed SRO 210** — taxvatpoint.com, caripon.com, taxpertbd.com,
> SlideShare and Facebook decks among them. The divergence is material: under SRO 210 the
> catering / PR / event management / creative media group was **4% on gross**; under the operative
> SRO 273 catering is **2% on total bill** and creative media is **10% on commission or 1% on gross
> bill, higher of**. **Discard any chart citing SRO 210.** When a supplier's figure disagrees with
> this file, ask which SRO their chart cites before assuming this file is wrong.

Two more citation defects worth recognising:

- **"SRO No. 273-Law/Income Tax-5/2028, dated 30 June 2026"** is wrong twice over. The instrument
  is ২৭৩-আইন/আয়কর-**৫/২০২৬** and it was gazetted **5 July 2026**.
- **NBR's own download page mislabels the SRO 273 PDF** "The Withholding Tax Rules, 2026
  (Amendment)". It is a complete standalone re-enactment, not an amendment.

### 1.2 Which instrument sets the VDS rates

উৎসে মূল্য সংযোজন কর কর্তন ও আদায় বিধিমালা, ২০২৫ = **SRO 182-Ain/2025/310-Mushak** of 27 May 2025
(commenced 1 July 2025; repealed the 2021 Rules), **as amended by SRO 140-Ain/2026/345-Mushak** of
7 June 2026 (commences 1 July 2026). Both made under VAT Act ss.135, 49 and 127খ.

> ⚠️ **"SRO 258-Law/2026/358-VAT" does not exist.** That citation circulates on practitioner blogs.
> NBR's VAT-SRO index tops out at SRO 148 of 11 June 2026 and every probe of the 149–266 range
> returns 404. The real FY2026-27 VDS amendment is **SRO 140**.
>
> ⚠️ **NBR's own VAT FAQ page is years out of date and must never be cited.** It still publishes
> pre-2019 thresholds, a 3% turnover tax and monthly returns by the 15th.

### 1.3 Five structural changes that invalidate FY2025-26 templates

1. **Withholding is no longer broadly minimum tax.** s.163 was replaced and s.164 repealed by the
   Finance Act 2026. Excess withholding is now **refundable or carry-forward adjustable**. Only
   ss.138 and 139 remain final tax. → [§7](#7-final-tax-and-minimum-tax)
2. **The withholding return is QUARTERLY.** There is no half-yearly return (s.177(4) was deleted by
   the Finance Act 2024) and no separate annual salary statement. → [§9](#9-returns-and-certificates)
3. **Board meeting fees doubled, 10% → 20%.** → [§3.2](#32-s90--services-professional-and-technical-fees)
4. **Property rent doubled, 5% → 10%,** under both s.109 and s.110. → [§3.3](#33-rent-of-property-and-of-event-space)
5. **Disallowance of the expense on a TDS default is abolished** (s.55(a) deleted). The cost is now
   150% of the tax under s.56(1), and the expense stands. → [§10](#10-what-a-failure-costs)

### 1.4 The two sides — never conflate them

| | Tax deducted **from** you | Tax deducted **by** you |
|---|---|---|
| What it is | An advance against **your own** liability | **Somebody else's money** you are holding |
| Ledger | **Receivable / asset** — `tds_receivable` | **Liability** — `tds_payable`, `vds_payable` |
| Your duties | Collect the certificate; claim the credit in your return | Deposit by the deadline; issue the certificate; report it in the quarterly return |
| If it goes wrong | You lose a credit you paid for | You owe the tax **plus 50% of it**, and named individuals are personally liable |

A journal tag records which side you are on: `TDS:<section>:<rate>` and `VDS:<rate>`, posted to
`tds_receivable` or to `tds_payable` / `vds_payable`. See
[bookkeeping-standards.md](bookkeeping-standards.md).

---

## 2. Who must deduct

### 2.1 Income tax — the "specified person", s.140(3)

Withholding under most of Part 7 is triggered only where the **payer** is a *specified person*.
The Finance Act 2026 widened the definition:

> **s.140(3)(j), new — any natural person with business turnover exceeding Tk 10,00,00,000
> (Tk 10 crore) is now a specified person.**

A sole proprietor over that turnover is now a **withholding agent** with a deposit duty, a
certificate duty and a quarterly return. Many proprietors of that size have never withheld
anything and do not know this changed. The same figure is the threshold at which a natural person
must file the s.177 withholding return.

### 2.2 VAT — the "withholding entity", VAT Act s.2(21)

| Clause | Who |
|---|---|
| (a) | Any **government entity** |
| (b) | Any **NGO** approved by the NGO Affairs Bureau or the Department of Social Services |
| (c) | Any **bank, insurance company or similar financial institution** |
| (d) | Any **secondary or higher-level educational institution** |
| (e) | **Any limited company** — at any turnover |
| (f) | **Any person or entity with annual turnover exceeding Tk 10,00,00,000 (Tk 10 crore)** — inserted by the Finance Act 2024 (Act 5 of 2024) s.4(a), effective 1 July 2024 |

Clause (e) is the one SMEs miss: **every limited company is a VAT withholding entity regardless of
size.** Clause (f) catches large unincorporated businesses.

---

## 3. TDS rate matrix — resident payments

> Rates below carry **no PSR uplift**. Where the payee is required to furnish proof of submission
> of return and fails to, or does not take payment by bank transfer, the rate is **50% higher —
> multiply by 1.5, do not add 50 points**. See [§6](#6-the-psr-uplift--s142).

### 3.1 s.89 — supply of goods, procurement and execution of contract · Rule 3(1) of SRO 273

**Statutory ceiling 10%.** Applies to **any amount** of base value — *যে-কোনো পরিমাণ ভিত্তিমূল্যের
উপর*. **The payment-size slabs no longer exist**; the old 2%/3%/5% Tk 50 lakh / Tk 2 crore slabs
were abolished by the TDS Rules 2024 (SRO 161/2024) from 1 July 2024, so a "slab" chart is at
least two years stale.

| # | Item | Rate | TOML key under `tds.sections.89` |
|---|---|---|---|
| 1 | MS billet manufacturing industry; locally purchased MS scrap | **0.5%** | `ms_billet_and_scrap` |
| 2 | Oil supplied by an oil-marketing company (petroleum oil & lubricant) | **0.6%** | `oil_marketing_company` |
| 3 | Oil supplied by a dealer/agent of a petroleum oil-marketing company | **1%** | `oil_dealer_or_agent` |
| 4 | Essential goods basket † | **0.5%** | `essential_goods` |
| 5 | Gold, silver, gold ornaments, gems/diamond — **supply** | **0.5%** | `gold_silver_gems_supply` |
| 6 | Yarn | **1%** | `yarn` |
| 7 | All kinds of fruit | **2%** | `fruit` |
| 8 | Sub-contract given by a 100% export-oriented garments industry | **1%** | `rmg_subcontract` |
| 9 | Cement, iron or iron products, ferro-alloy (other than MS billet) | **2%** | `cement_iron_ferro_alloy` |
| 10 | Oil supplied by a company engaged in oil refinery | **1%** | `oil_refinery` |
| 11 | Company engaged in gas **transmission** | **3%** | `gas_transmission` |
| 12 | Company engaged in gas **distribution** | **0.6%** | `gas_distribution` |
| 13 | 33 KV–500 KV EHV power cable, own local Vertical Continuous Vulcanization line | **3%** | `ehv_power_cable` |
| 14 | **Books** supplied to any person **other than** Government or a Government body ‡ | **3%** | `books` |
| 15 | Recycled plastic, polythene, battery, lead, electrical, electronics, paper, glass and all recyclable goods | **1%** | `recyclable_goods` |
| 16 | Raw material used in the **recycling** industry | **1%** | `recycling_raw_material` |
| 17 | Raw material used in industrial production **and packing material** | **3%** | `industrial_raw_material_and_packing` |
| 18 | **Manufacturing, process or conversion, civil work, construction, engineering or similar** | **5%** | `manufacturing_and_civil_work` |
| 19 | Tobacco raw material supplied to cigarette, bidi, zarda and gul industry | **10%** | `tobacco_raw_material` |
| 20 | (a) all goods not in serials 1–19; (b) **all other cases under s.89** — catches "execution of contract" and printing/packaging/binding | **5%** | `all_other_supply_and_contracts` |

† paddy, rice bran, rice, fortified rice kernel, wheat, potato, cattle, cattle bone, poultry, fish,
meat, onion, garlic, peas, gram, lentil, ginger, turmeric, dried chilli, pulses, maize, atta,
maida, iodised salt, edible oil, sugar, seeds, jute, jute stick, cotton, mustard, sesame, raw tea
leaf, black pepper, cardamom, cinnamon, clove, bay leaf, eggs, vegetables, lemon, green chilli,
liquid milk, saw-mill bran, poultry feed (incl. pelleted), mushroom, honey, molasses, leaves and
bark of trees other than tobacco, creepers, chitagur, oil cake, soybean meal, de-oiled rice bran,
raw hide, organic fertiliser, organic pesticide. If your goods are not on that list, 0.5% is not
your rate.

‡ the exclusion covers Government, a Government authority, corporation or agency and its attached
and subordinate offices — books supplied **to those** fall to serial 20(a) at 5%. The carve-out
runs the opposite way to intuition.

**Provisos and adjustments**

- **No deduction** on supply of oil or gas **by a petrol pump or CNG station**.
- **Rule 3(2)** — goods already taxed on import under s.120 and then supplied: deduct **(B − A)**,
  where A = the s.120 tax already paid and B = what s.89 would take.
- **Rule 3(3)** — goods already taxed under s.94: deduct **(B − A)**; for distributors,
  B = {company's sale price to the distributor} × 5% × 10%.
- **Rule 3(4)** — the Board may certify nil or reduced deduction on written application.

**Contractors** have no table of their own. Construction and civil-works contractors sit at
serial 18 (5%); any other execution of contract sits at serial 20(b) (also 5%). The only
contractor rate that is not 5% is a sub-contract from a 100% export-oriented garments industry
(serial 8, 1%).

### 3.2 s.90 — services, professional and technical fees · Rule 4 of SRO 273

**Statutory ceiling 20%.**

| # | Service | Basis | Rate |
|---|---|---|---|
| 1 | Advisory or consultancy fee | natural person | **15%** |
| | | other than natural person | **7.5%** |
| 2 | **Professional service fee** (doctors, lawyers, other professionals) | natural person | **15%** |
| | | other than natural person | **7.5%** |
| 3 | Technical services, technical know-how or technical assistance fee | natural person | **15%** |
| | | other than natural person | **10%** ← not 7.5% |
| 4 | (a) Cleaning (b) Private security (c) Manpower supply **(d) Creative media (e) Print & electronic media agency service** | on commission | **10%** |
| | | on gross bill | **1%** |
| 5 | (a) Catering (b) Public relations (c) Event management (d) Training/workshop management (e) Courier (f) Packing & shifting (g) Collection & recovery agency (h) other services of the same nature | on total bill | **2%** ⚠️ |
| 6 | **Indenting commission** | | **7.5%** |
| 7 | **Meeting fee, training fee or honorarium** | on bill | **20%** ⚠️ |
| 8 | Service provided by a mobile network operator | on bill | **10%** |
| 9 | Credit rating agency | on bill | **10%** |
| 10 | Motor garage or workshop | on bill | **5%** |
| 11 | Private container port or dockyard | on bill | **5%** |
| 12 | **Shipping agency** | on commission | **10%** |
| | | on gross bill | **1%** |
| 13 | Stevedoring / berth operator / terminal operator / ship handling operator | on commission | **10%** |
| | | on gross bill | **5%** ← not 1% |
| 14 | (1) Transport, vehicle rental, carrying, repair & maintenance; (2) ride sharing, working-space supply, accommodation supply, any sharing-economy platform | on total bill | **2%** |
| 15 | Wheeling charge for electricity transmission | on total bill | **3%** |
| 16 | Internet service | on bill | **5%** |
| 17 | Commission to an agent, distributor, agency or channel partner of an MFS provider | on commission | **10%** |
| 18 | Freight forward (commission-inclusive or -exclusive gross bill) | on commission | **10%** |
| | | on gross bill | **1%** |
| 19 | **Any other service** not in serials 1–18 and not deductible under any other section | | **10%** |

⚠️ **Serial 5 is the most misquoted rate of FY2026-27.** The repealed SRO 210 put this group at
**4% on gross**; SRO 273 says **2% on total bill**.

⚠️ **Serial 7 doubled from 10%.** **Board meeting attendance fees fall here.** A FY2025-26
board-fee template still deducting 10% is under-deducting by half, and the payer carries the
shortfall plus 50% of it.

**Proviso (a)** — other than serials 1–18, a service rendered by a **bank, insurance company,
financial institution or MFS provider** attracts **no deduction** under this rule. The exclusion
stops the residual serial 19 reaching ordinary bank, insurance, NBFI and MFS charges; it says
nothing about s.102 or s.104, which have their own rules. Note it does **not** protect commission
paid **to** an MFS provider's agents — that is serial 17.

**Proviso (b) — the higher-of rule.** For **serials 4, 12, 13 and 18**, where **both** a
commission/fee **and** a gross bill are shown, tax = **the HIGHER of** (tax on commission at its
rate) and (tax on gross bill at its rate). It is not a choice and it is not the sum.

> Worked shape: commission ৳ 1,00,000 at 10% = ৳ 10,000; gross bill ৳ 15,00,000 at 1% = ৳ 15,000;
> **deduct ৳ 15,000**. Where only one of the two figures is shown, only that limb can be computed
> — TakaBooks will not infer the other.

> **The 0.65% media buying agency rate is gone.** An agency's own charge is now serial 4.

### 3.3 Rent of property and of event space

| Item | Rate | Section |
|---|---|---|
| Rent of house property; hotel or guest house; vacant space, plant or machinery; any water body other than a government water body; **any building used entirely as a warehouse/godown** | **10%** ⚠️ | s.109 |
| Convention hall, conference centre, room/hall, hotel, community centre or restaurant — rent or space use | **10%** ⚠️ | s.110 |

⚠️ **Both doubled from 5% to 10%** by Act 89 of 2026, ss.70(a) and 71 — confirmed by the amendment
footnotes on the bdlaws consolidated text.

- The **warehouse/godown limb, s.109(1)(ঙ), is a new insertion.** Warehousing arrangements that
  previously escaped s.109 are now inside it.
- **s.109(3):** the DCT may certify no deduction where the owner has no taxable income.
- **"Rent" is defined widely, s.109(4):** any payment under a lease, tenancy or other arrangement
  for use of a building with its furniture, fixtures and appurtenant land. A service charge dressed
  up as something else is still rent.
- A s.110 booking also attracts **VDS**: community centre 15% (S017.00), restaurant 5% (S001.20),
  hotel 15% AC / 10% non-AC (S001.10).

### 3.4 Salary — s.86

**There is no fixed salary TDS rate.** s.86(1) requires deduction at the **average rate of tax
applicable to the recipient's *estimated* total income under "Income from employment"**, at the
time of payment.

| Rule | Effect | Section |
|---|---|---|
| Method | Average rate on estimated total employment income for the year | s.86(1) |
| Government DDO | Same method at the time of preparing/signing the bill, where annual salary exceeds the tax-free limit | s.86(3) |
| In-year correction | The deduction may be increased or decreased to adjust excess or deficiency **of the current income year** — not a prior year | s.86(4) |
| Nil / lower deduction | The DCT may certify no deduction or a reduced rate for the remainder of the year | s.86(5) |
| MPs' honorarium | Average rate on estimated total honorarium | s.87 |

Compute the annual tax from the individual slabs for this assessment year, divide by estimated
total employment income, apply that average rate to each payment. See [payroll.md](payroll.md)
and [income-tax.md](income-tax.md).

### 3.5 Interest, profit and securities

| Item | Rate | Section |
|---|---|---|
| Interest/profit on any deposit paid by a bank, insurer, leasing/financing/postal-banking/co-operative or **MFS** entity, or any person paying profit on a deposit — recipient is a **trust, association of persons, or company** | **20%** | s.102 Table |
| Same — **all other cases**, including individuals | **10%** | s.102 Table |
| Interest/profit paid by a *specified person* on a loan, to anyone other than a bank or finance company | **10%** | s.104 |
| **Profit on savings certificates (sanchayapatra)** | **10%** | s.105(1) |
| — Pensioner Sanchayapatra, cumulative investment ≤ **৳ 5,00,000** | **Nil** | s.105(2) |
| — Wage Earner Development Bond; US Dollar Premium/Investment Bond; Euro Premium/Investment Bond; Pound Sterling Investment/Premium Bond | **Nil** | s.105(3) |
| Interest/discount on **government or approved securities** — **company** holder | **15%** | s.106 Table |
| Same — **non-company** holder | **10%** | s.106 Table |
| Discount on the real value of Bangladesh Bank bills | **maximum applicable rate** | s.107 |

> ⚠️ **The old "with TIN / without TIN" split in s.102 is gone.** The table is now split by **type of
> recipient**. The return-filing uplift lives solely in s.142. Charts printing a 10%/15% TIN split
> for s.102 are out of date.
>
> ⚠️ **Sanchayapatra profit is no longer final tax.** Bring it into total income and treat the 10%
> as an advance.

### 3.6 Dividends — s.117 (replaced by Finance Act 2026 s.72)

| Payee | Rate | Provision |
|---|---|---|
| Resident **natural person** shareholder / unit holder | **15%** | s.117(a) |
| Resident **person other than a natural person**, including resident companies | **20%** | s.117(b) |
| **Non-resident** — company, fund or trust | **20%** | s.119, Rule 5 serial 21(1) |
| **Non-resident** — other than a company, fund or trust | **25%** | s.119, Rule 5 serial 21(2) |

s.117 does not apply to a company's distribution of a **tax dividend** exempt under the Sixth
Schedule Part 1 clause (32). Note the inversion for non-residents: an **individual** non-resident
shareholder pays **more** (25%) than a corporate one (20%) — the reverse of the resident position.

### 3.7 Export proceeds — s.123

| Item | Rate |
|---|---|
| Bank crediting export proceeds to an exporter's account — on **gross export proceeds** | **1%** |
| Where the Board certifies the exporter's income is exempt or taxable at a reduced rate | nil, or the certified reduced rate (s.123(2)) |

The 1% is the rate **in the Act itself**, not an SRO-reduced rate. *Caveat:* the research pass did
not exhaustively search NBR's SRO index for an instrument reducing it further for FY2026-27, and
none was found in force. If an exporter shows you a lower rate, ask for the SRO number.

**Related:** cash export subsidy (s.112) **fell from 10% to 5%** and is **no longer final tax**.

### 3.8 Commission, discount and fees to agents and distributors

| Item | Rate | Section |
|---|---|---|
| Commission, discount, fee, incentive, performance allowance or benefit of like nature paid by a **company or firm** to a distributor or any other person for supply/marketing of goods or services | **10%** | s.94(1) |
| Payment by a company/firm to a person engaged in **distribution or marketing** of its goods | **1.5%** | s.94(2) |
| Company/firm (not an oil-marketing company) selling goods to a distributor below its fixed retail price — collect on **B × C**, where B = sale price to distributor, C = 5% | **5% of (B × 5%)** ⚠️ | s.94(3) |
| — **Cigarette manufacturers**: on the **difference** between the sale price to the distributor and the fixed retail price | **3%** | s.94(3) proviso |
| **Commission on letters of credit** (person responsible for opening an import LC) | **5%** | s.96 |
| **Insurance commission** — soliciting/procuring, or continuance/renewal/revival | **5%** | s.100 |
| General insurance **surveyors'** fees | **15%** | s.101 |
| Payment exceeding premium on a life insurance policy (nil on death of the policyholder) | **5%** | s.99 |
| Travel agent — on gross amount convertible via passenger ticket sales | **0.3%** | s.95(1) |
| Commission/remuneration to an **agent of a foreign buyer** (paid via bank on an export) | **7.5%** | s.116 |
| Commission/discount/fee on sale of government stamps, court fees, cartridge paper | **10%** | s.127 |
| Manpower export agency — service charge or fee | **10%** | s.121(a) |

⚠️ **s.94(3) is not 5% of the invoice.** The base is **B × 5%**, so the collection is 5% of (sale
price × 5%). Applying 5% directly to B overstates the deduction twentyfold.

**Local LC and other financing — s.97** (distinct from s.96, which taxes the **commission** on an
import LC):

| Item | Rate | Section |
|---|---|---|
| Local LC or other financing for purchase of goods in Bangladesh for resale after process/conversion | **3%** | s.97(1) |
| Distributor financing arrangement | **1.5%** | s.97(2) |
| All kinds of fruit; computer or computer parts | **2%** | s.97(3) |
| Yarn | **1%** | s.97(4) |
| Essential-goods basket, **including handicraft goods** | **0.5%** | s.97(5) |
| **Cement, iron or iron products, ferro-alloy other than MS billets** — *new, FA 2026* | **2%** | s.97(5A) |

Handicraft goods appear in the s.97(5) basket but **not** in the s.89 serial-4 basket.

### 3.9 Advertising, media and intangibles

| Item | Rate | Section |
|---|---|---|
| Payment by a *specified person* to a newspaper, magazine, private TV channel, private radio station **or any other person (excluding a media buying agent)** for advertisement or broadcast | **5%** | s.92 |
| Purchase of a film, drama, TV or radio programme, part or full | **10%** | s.93(1) |
| Payment to a person for **acting** in a film, drama, advertisement, TV or radio programme | **10%** | s.93(2) |
| Print and electronic **media agency service** / creative media | **10% on commission or 1% on gross bill, higher of** | s.90, Rule 4 serial 4 |
| Royalty, franchise, licence, trademark, patent, copyright, industrial design, plant variety, GI or other intangible | **10%** | s.91 |

A royalty to a **non-resident** is **20%** under s.119 / Rule 5 serial 11. A **non-resident** artist,
singer or player is **30%** under serial 22. Check residence before applying a resident rate.

### 3.10 C&F agency commission — s.122

| Item | Rate |
|---|---|
| **Commissioner of Customs** collects on the commission receivable by a **clearing & forwarding agent** licensed under the Customs Act 1969, on import or export | **10%** |

Note **who** deducts: the Commissioner of Customs collects this at the customs stage, so an
importer paying a C&F agent does **not** deduct it again. Keep the customs collection record —
it is the agent's credit, not yours.

### 3.11 New and changed items under the Finance Act 2026

| Item | Old | **From 1 July 2026** | Section |
|---|---|---|---|
| Lottery, crossword, card games, **online games** and similar | 20% | **25%** | s.118 |
| Cash export subsidy | 10% | **5%** (and no longer final tax) | s.112 |
| Purchase of electricity, incl. from captive generators | 4% | **3%** | s.114 |
| Inward remittance for fee / service charge / remuneration / revenue sharing | 7.5% | **5%** | s.124 |
| **Purchase of gold, silver, ornaments, gems-diamond or platinum** — collected **from the seller** by a person in that trade | — | **0.5%** | **s.112A** (new) |
| **Advance tax from retail traders** — collected by a manufacturer, importer, supplier, distributor or **arotdar** on direct sale/supply to a retailer; creditable to the retailer; if borne by the collector it is an **allowable expense** | — | **0.2%** | **s.130A** (new) |
| **Registered club membership** — admission, renewal, transfer or change | — | **10%** | **s.137A** (new) |
| Cement, iron/iron products, ferro-alloy (other than MS billets) via local LC or other financing | — | **2%** | s.97(5A) (new) |
| Freight forward / shipping agent **inward remittance** | — | **1% of gross bill**, or **10% of commission** if shown separately, **whichever is higher** | s.124 proviso (1) |
| Civil aircraft — advance tax at registration / fitness renewal | — | **৳10,00,000** for a helicopter or chopper, the সারণি's only row — [§3.14](#314-ss138-138a-139--fixed-amount-advance-taxes) | **s.138A** (new) |
| Revenue share, licence fee or any fee/charge paid by a cellular mobile phone operator or tower-sharing company | withheld | **no longer withheld** | — |
| Compensation for compulsory acquisition of immovable property | unchanged | **6%** inside a city corporation / municipality / cantonment board area; **3%** outside | s.111 |
| Real estate developer's payment to a land owner (signing money, subsistence money, house rent) | unchanged | **15%** | s.115 |
| IGW international phone calls | unchanged | **1.5%** (IGW deposits) / **7.5%** (ICX, ANS, BTRC) | s.108 |
| Lease of immovable property for ≥ 10 years | unchanged | **4%** | s.128 |
| Share transfer in an unlisted company / sponsor-director-placement securities / stock exchange shareholders | unchanged | **15%** | ss.134, 135, 136 |
| Stock exchange members | unchanged | **0.03%** | s.137 |
| Participation Fund / Welfare Fund / Workers' Welfare Foundation Fund payments (WPPF) | unchanged | **10%** | s.88 |
| Import stage collection | unchanged ceiling | **0% / 1% / 2% / 3% / 4% / 5% / 20% / ৳600 per tonne** by HS code under Rule 8 — all 345 rows landed, [§3.12](#312-s120--collection-at-the-import-stage--rule-8-of-sro-273) | s.120 |

⚠️ **s.112A runs the opposite way to s.89 serial 5.** s.89 serial 5 deducts on the **supply** of
gold and gems at 0.5%; s.112A **collects from the seller** on the **purchase** of the same goods,
also at 0.5%. A jeweller can be on both sides in one week.

⚠️ **s.130A at 0.2% is two tenths of one percent, not 2%.** The base is the whole supply, so it
lands hard on high-volume, low-margin distribution. The retailer gets a **credit** and must be
given evidence of it; a collector who absorbs it gets a **deduction**, not a disallowance.

---

### 3.12 s.120 — collection at the IMPORT STAGE · Rule 8 of SRO 273

Rule 8 is now transcribed in full. **All 345 HS-code rows** of its seven সারণী are in
`rates-AY2026-27.toml` at `[tds.sections.120.hs_schedule].rows`, each row carrying its সারণী, its
rate and the gazette page it was read from. The statutory ceiling is **20%** (s.120) and সারণী-৬
reaches it, so nothing at import may be charged above 20%.

**The base — get this right before the rate.** Rule 8(4): "আমদানিকৃত পণ্যের মূল্য" is the value of
the imported goods determined under **section 27 of the Customs Act, 2023** (Act No. 57 of 2023) —
the customs assessable value. Not the invoice, not the LC amount, not the landed cost. সারণী-৭ is
the single exception: it is charged **per tonne**, so weight is the base there.

| সারণী | Rate | Base | Who / what it covers | Rows | Gazette pages |
|---|---|---|---|---:|---|
| **১** | **0%** | value | Food staples, edible oils, fertiliser inputs, medical devices; serial 77 is "Capital machinery, not imported for commercial purpose" and carries no HS code | 77 | 20693–20699 |
| **২** | **0%** | value | **Goods imported FROM BHUTAN only** — country of origin is part of the rule | 32 | 20699–20701 |
| **৩** | **1%** | value | Industrial intermediates — adhesives, graphite, solder flux, plasticisers, cast polypropylene film, carded cotton, springs, inductors, mobile-phone PCB and component sets | 42 | 20701–20704 |
| **৪** | **2%** | value | Pulses, wheat, maize, oil-cake and feed inputs, raw hides, wood pulp, computers and computer parts, transmission apparatus, monitors | 131 | 20704–20713 |
| **৫** | **3%** | value | **Only where the importer is a মূসক-registered manufacturer holding an industrial IRC** — milk powder, quartz, clays, dolomite, aluminium tape, zinc, battery chargers, lithium-ion cells | 48 | 20714–20717 |
| *(proviso)* | **4%** | value | Same importer class — industrial-IRC মূসক-registered manufacturer — on goods **outside সারণী-৫** | — | 20717 |
| **৬** | **20%** | value | Undenatured and denatured ethyl alcohol, spirits, whisky, rum, gin, vodka, liqueurs, other spirituous beverages, perfumes and toilet waters | 10 | 20717–20718 |
| **৭** | **৳600 per tonne** | **weight** | Sponge iron and direct-reduced ferrous products, ferrous waste and scrap, iron and non-alloy steel ingots, semi-finished iron/steel, vessels for breaking up | 5 | 20718 |
| *(residual)* | **5%** | value | **Rule 8(2)** — everything in none of the seven tables. This is the rate most consignments take | — | 20718 |

**How to pick a rate.** Find the 8-digit HS code in the schedule. If it is there, its সারণী gives
the rate — but check the two status conditions first: সারণী-২ needs **Bhutan origin**, সারণী-৫ needs
an **industrial-IRC মূসক-registered manufacturer**. If the code is in no table, Rule 8(2) charges
**5%**.

Rule 8(3): on the importer's written application the Board **may certify** collection at a nil or
reduced rate for an income year where the import income is exempt or taxable at a reduced rate.

> ⚠️ **The reach of the 4% proviso is not settled by the text.** The proviso after সারণী-৫ reads
> "সারণী-৫ এ বর্ণিত পণ্য ব্যতীত অন্য কোনো পণ্য আমদানীর ক্ষেত্রে ইন্ডাস্ট্রিয়াল আইআরসি ধারী কোনো মূসক নিবন্ধিত
> উৎপাদক কর্তৃক আমদানিকৃত পণ্য মূল্যের উপর ৪% (চার শতাংশ) হারে উৎসে কর সংগ্রহ করিবে". Read literally that
> is **every** good other than সারণী-৫'s, which would displace সারণী-১'s 0% and সারণী-৪'s 2% for this
> importer. Read as a proviso to clause (ঙ) it only fills the gap between সারণী-৫ and the 5%
> residual. **The gazette settles neither reading.** TakaBooks holds both figures as read and does
> not choose. Put the question to the Commissioner of Customs before clearing on either.

> ⚠️ **A drafting error in the gazette itself.** Clause (ছ) at page 20718 says "নিম্নবর্ণিত সারণী-৬"
> but the table printed under it is captioned **"সারণী-৭"**, and সারণী-৬ already has its 20% from
> clause (চ) on the previous page. The ৳600-per-tonne charge plainly belongs to **সারণী-৭**. Recorded
> that way here, with the error stated rather than silently corrected.

> ⚠️ **HS codes move.** The schedule keys off the First Schedule of the Customs Act 2023. A code
> reclassified after 5 July 2026 will not match. Read the code off the bill of entry.

Remember **Rule 3(2)**: goods taxed at import under s.120 and then supplied locally are deducted at
**(B − A)** under s.89 — see [§3.1](#31-s89--supply-of-goods-procurement-and-execution-of-contract--rule-31-of-sro-273).

---

### 3.13 ss.125–126 — property transfer and developers · Rules 6 and 7 of SRO 273

Both rules are now transcribed. Neither is a mouza-by-mouza list: Rule 6 groups whole **thanas**,
so a seller who knows the thana can place the land. Mouza-level *valuation* is a separate matter
for the registering office and is not in these rules.

**s.125 · Rule 6(1) সারণী-১ — land.** Every cell reads "**দলিলে উল্লিখিত ভূমির মূল্যের X% বা শতকপ্রতি Y
টাকা, যাহা অধিক**" — a percentage of the land value stated in the deed **OR** a floor in taka per
**শতক** (decimal, 1/100 acre ≈ 40.46 m²), **whichever is higher**. On a low paper value the floor is
what binds, which is the point of the design.

| # | Area (all mouzas of the named thanas) | % | ক | খ | গ | ঘ | ঙ | চ |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | **Dhaka** — Gulshan, Banani, Motijheel, Tejgaon | 5% | 9,00,000 | 3,50,000 | 9,00,000 | 3,50,000 | 5,00,000 | 3,00,000 |
| 2 | **Dhaka** — Dhanmondi, Wari, Tejgaon Shilpanchal, Shahbagh, Ramna, Paltan, Bangshal, New Market, Kalabagan | 5% | 6,50,000 | 3,00,000 | 6,50,000 | 3,00,000 | 3,00,000 | 2,00,000 |
| 3 | **Dhaka** — Kafrul, Mohammadpur, Sutrapur, Jatrabari, Uttara Model, Cantonment, Chakbazar, Kotwali, Lalbagh, Khilgaon, Shyampur, Gendaria | 5% | 4,00,000 | 1,75,000 | 4,00,000 | 1,75,000 | 1,75,000 | 85,000 |
| 4 | **Dhaka** — Khilkhet, Biman Bandar, Uttara Paschim, Mugda, Rupnagar, Bhashantek, Badda, Pallabi, Bhatara, Shahjahanpur, Mirpur Model, Darus Salam, Dakshinkhan, Uttarkhan, Turag, Shah Ali, Sabujbagh, Kadamtali, Kamrangirchar, Hazaribagh, Demra, Adabor; **Narayanganj** Sadar | 5% | 3,50,000 | 1,50,000 | 3,50,000 | 1,50,000 | 1,50,000 | 75,000 |
| 5 | **Chattogram** — Khulshi, Panchlaish, Pahartali, Halishahar, Kotwali; **Narayanganj** — Sonargaon, Fatullah, Siddhirganj, Bandar; **Gazipur** — Sadar, Basan, Konabari, Gachha, Tongi Purba, Tongi Paschim | 3% | 1,75,000 | 70,000 | 1,75,000 | 70,000 | 70,000 | 35,000 |
| 6 | **Dhaka** — Dohar, Nawabganj, Keraniganj, Savar, Dhamrai; **Chattogram** — Akbar Shah, EPZ, Karnaphuli, Chakbazar, Chandgaon, Double Mooring, Patenga, Panchlaish, Bandar, Bakalia, Bayezid Bostami, Sadarghat; **Gazipur** — Joydebpur, Kaliganj; **Narayanganj** — Rupganj, Araihazar | 3% | 1,25,000 | 60,000 | 1,25,000 | 60,000 | 60,000 | 30,000 |
| 7 | Not in 1–6 but in a city corporation other than Dhaka South, Dhaka North, Chattogram, Narayanganj, Gazipur, or under any other development authority; and all mouzas of every **district-headquarters pourashava** | 3% | 1,00,000 | 50,000 | 1,00,000 | 50,000 | 50,000 | 25,000 |

Floors are **taka per শতক**. **সারণী-২** catches the rest: any **other pourashava** — **2%** or
**৳10,000** per শতক; all **upazila** areas outside pourashavas — **2%** or **৳500** per শতক.

**The six plot classes — Rule 6(8).** ক and খ are **commercial** and **residential** plots inside an
area controlled by a listed development authority (জাতীয় গৃহায়ন কর্তৃপক্ষ, গণপূর্ত অধিদপ্তর, ক্যান্টনমেন্ট
বোর্ড, রাজউক, CDA, GDA, KDA, RDA, কক্সবাজার উন্নয়ন কর্তৃপক্ষ, or any similar authority under the Ministry
of Housing and Public Works). গ and ঘ are **commercial** and **residential** plots **outside** any such
authority but in an area **established by a developer**. ঙ is **every industrial plot**. চ is
everything else.

**Rule 6(2) — the structure surcharge, charged ON TOP.** If a স্থাপনা, বাড়ি, ফ্ল্যাট, অ্যাপার্টমেন্ট or
ফ্লোর স্পেস stands on the land:

| Where the land is | Per square metre | or % of the deed value of the structure | whichever |
|---|---:|---:|---|
| Class **ক to ঘ** | ৳800 | 8% | higher |
| Class **ঙ**, and the mouzas at সারণী-২ serial 1 | ৳500 | 6% | higher |
| All other cases | ৳300 | 6% | higher |

**s.126 · Rule 7 — developers.** Two limbs, and Rule 7 stacks on Rule 6.

| # | Area | Residential /m² | Commercial /m² |
|---:|---|---:|---:|
| 1 | **Dhaka** — Gulshan, Banani, Motijheel, Tejgaon | ৳1,600 | ৳6,500 |
| 2 | **Dhaka** — Dhanmondi, Wari, Tejgaon Shilpanchal, Shahbagh, Ramna, Paltan, Bangshal, New Market, Kalabagan | ৳1,500 | ৳5,000 |
| 3 | **Dhaka** — Khilkhet, Kafrul, Mohammadpur, Sutrapur, Jatrabari, Uttara Model, Cantonment, Chakbazar, Kotwali, Lalbagh, Khilgaon, Shyampur, Gendaria | ৳1,400 | ৳4,000 |
| 4 | **Dhaka** — Biman Bandar, Uttara Paschim, Mugda, Rupnagar, Bhashantek, Badda, Pallabi, Bhatara, Shahjahanpur, Mirpur Model, Darus Salam, Dakshinkhan, Uttarkhan, Turag, Shah Ali, Sabujbagh, Kadamtali, Chakbazar, Kamrangirchar, Kotwali, Lalbagh, Hazaribagh, Demra, Adabor; **Chattogram** — Khulshi, Panchlaish, Pahartali, Halishahar, Kotwali; **Gazipur** — Sadar, Basan, Konabari, Gachha, Tongi Purba, Tongi Paschim, Joydebpur, Kaliganj; **Narayanganj** — Sadar, Fatullah, Siddhirganj, Bandar, Rupganj, Sonargaon | ৳1,300 | ৳3,500 |
| 5 | **Dhaka** — Dohar, Nawabganj, Keraniganj, Savar, Dhamrai; **Chattogram** — Akbar Shah, EPZ, Karnaphuli, Chakbazar, Chandgaon, Double Mooring, Patenga, Panchlaish, Bandar, Bakalia, Bayezid Bostami, Sadarghat; **Narayanganj** — Araihazar; and all mouzas in any city corporation other than Dhaka South, Dhaka North, Chattogram, Narayanganj, Gazipur | ৳700 | ৳2,000 |
| 6 | All areas not in 1–5 | ৳300 | ৳1,000 |

Rule 7(2) charges the **land** separately: **5%** of the land value stated in the deed in **Dhaka,
Gazipur, Narayanganj, Munshiganj, Manikganj, Narsingdi and Chattogram** districts; **3%** in any
other district.

> ⚠️ **The stacking rule people get wrong.** Rule 7(5): when collecting under Rule 7 the registering
> officer must **also** collect the **Rule 6(1)** land charge — "তবে শর্ত থাকে যে, বিধি ৬ এর উপ-বিধি (২)
> অনুযায়ী উৎসে কর সংগ্রহ করা যাইবে না", i.e. **the Rule 6(2) structure surcharge is NOT collected**. So a
> developer sale carries Rule 7(1) per m² **+** Rule 7(2) on the land **+** Rule 6(1) on the land, and
> **not** Rule 6(2).

Distinct from **s.115**, which taxes the developer's payment **to the land owner** at **15%** —
different payer, different event.

**Machinery common to both rules.** The deed's **মন্তব্য কলাম must state** whether the property is
residential, commercial or industrial; without it, Rule 6(3) deems the collection **not correctly
made**. Both rules reach transfers by statutory government authorities. In city corporation,
pourashava and cantonment board areas **PSR of both donor and recipient** is required — including
for a বায়নানামা or আমমোক্তারনামা. The tax must reach the treasury by a **separate A-Challan before
registration**.

Rule 6(5) exempts: a **mortgage** deed; transfer by the **UN**, its organs, or a foreign embassy or
mission; a **না-দাবি** deed that does not extinguish title; a **বণ্টননামা** (partition); a **waqf or
debottar** gift; and a deed carrying no consideration — **will, অছিয়ত, এওয়াজ or exchange**.

---

### 3.14 ss.138, 138A, 139 — fixed-amount advance taxes

> ⚠️ **These are NOT in SRO 273.** The withholding rules do not touch them. The amounts sit in the
> **Income Tax Act 2023's own সারণি inside each section** [ACT]. Anyone looking for them in the SRO
> will not find them.

**s.138 — commercially operated motor vehicles**, collected by the BRTA at registration or fitness
renewal. Substituted in full by **Finance Act 2026 s.81**, effective 1 July 2026.

| # | Vehicle | ৳ | | # | Vehicle | ৳ |
|---:|---|---:|---|---:|---|---:|
| 1 | Bus, more than 52 seats | 25,000 | | 9 | Truck / dump truck / covered van / prime mover / lorry / tank lorry, payload ≥ 20 t | 50,000 |
| 2 | Bus, not more than 52 seats | 20,000 | | 10 | Truck / covered van / cargo van / lorry / tank lorry, payload > 1.5 t ≤ 5 t | 15,000 |
| 3 | Air-conditioned bus | 50,000 | | 11 | Truck / lorry / tank lorry, payload ≤ 1.5 t | 7,500 |
| 4 | Double-decker bus (non-AC) | 25,000 | | 12 | Pickup van, human hauler, tractor, maxi, auto rickshaw | 7,500 |
| 5 | AC double-decker / sleeper bus | 50,000 | | 13 | Crane, excavator, dredger, roller, concrete mixer and all heavy or special-purpose vehicles | 50,000 |
| 6 | AC minibus / coaster | 25,000 | | 14 | Air-conditioned taxicab | 15,000 |
| 7 | Non-AC minibus / coaster | 12,500 | | 15 | Non-AC taxicab | 7,500 |
| 8 | Truck / dump truck / covered van / prime mover / lorry / tank lorry, payload > 5 t < 20 t | 30,000 | | | | |

> ⚠️ **Do not confuse s.138 with s.153.** s.153 also taxes motor vehicles at registration and
> fitness renewal, but on **engine capacity (cc)** at ৳25,000 to ৳5,00,000 — and s.153(8)(ক)
> expressly excludes "ধারা ১৩৮ এ উল্লিখিত কোনো মোটরযান" and motorcycles. **s.138 is the commercial
> fleet; s.153 is the private car.** A commercially operated vehicle is charged under s.138 only.

**s.138A — civil aircraft**, *new*, inserted by **Finance Act 2026 s.82**. The section heading is
বেসামরিক আকাশযান — civil **aircraft**, wider than "helicopter" — but its সারণি has a single row:

| # | Aircraft | ৳ |
|---:|---|---:|
| 1 | **হেলিকপ্টার বা চপার** — helicopter or chopper | **10,00,000** |

A fixed-wing civil aircraft is therefore not priced by the table as gazetted. **s.138A is not in
the s.163(3) final-tax list** — it is an ordinary creditable advance tax.

**s.139 — inland vessels**, collected by the Department of Shipping on issue or renewal of a survey
certificate under ss.9 and 12 of the Inland Shipping Ordinance, 1976. **Unchanged** by the Finance
Act 2026 — no amendment footnote on bdlaws. Charged on **capacity, not income**:

| # | Vessel | ৳ |
|---:|---|---:|
| 1 | Inland passenger vessel — per passenger of **daytime** carrying capacity | 125 |
| 2 | Cargo, container (multipurpose) or coaster — per **gross tonne** of goods capacity | 170 |
| 3 | Dumb barge — per **gross tonne** of goods capacity | 125 |

All three sections share the same machinery: where registration, fitness or the survey certificate
is granted for **more than one year**, the later years' tax is due **on or before 30 June** of each
such year; a missed year is not forgiven but rolls forward as **ক + খ**. ss.138 and 138A carry an
exemption list — government; a government or local-government project; foreign diplomats,
diplomatic missions, the UN and its organs; foreign development partners; taxpayers exempt from
filing under s.166(2); and any entity holding a Board certificate that no advance tax is payable.

**ss.138 and 139 remain FINAL TAX** under s.163(3) — see
[§7](#7-final-tax-and-minimum-tax). s.138A does not.

---

## 4. TDS rate matrix — payments to NON-RESIDENTS · s.119, Rule 5 of SRO 273

s.119(1) now sets only a ceiling: deduct at the **prescribed rate, not exceeding 30%**. The
category table sits in Rule 5.

| # | Payment | Rate |
|---|---|---|
| 1 | Advisory or consultancy fee — natural person | **20%** |
| | — other than natural person | **10%** |
| 2 | Pre-shipment inspection | **20%** |
| 3 | Professional service fee — natural person | **20%** |
| | — other than natural person | **10%** |
| 4 | Technical services / technical know-how / technical assistance fee — natural person | **20%** |
| | — other than natural person | **10%** |
| 5 | Architecture, interior design, landscape design, fashion design or process design | **15%** |
| 6 | Certification, rating etc. fee | **15%** |
| 7 | Rent or other charge for **satellite, airtime or frequency**, or channel broadcast | **20%** |
| 8 | Legal service fee | **20%** |
| 9 | Management service including **event management** | **20%** |
| 10 | Commission | **15%** |
| 11 | **Royalty, licence fee or payment for intangible property** | **20%** |
| 12 | **Interest** | **10%** |
| 13 | Advertisement **broadcasting** | **15%** |
| 14 | Advertisement **making and digital marketing** | **10%** |
| 15 | Air transport or water transport (other than cases under ss.259 and 260) | **6%** |
| 16 | Contractor, sub-contractor and sub-sub-contractor — manufacturing, process or conversion, civil work, construction, engineering or similar | **6%** |
| 17 | **Supply of goods** | **6%** |
| 18 | **Capital gain** | **15%** |
| 19 | Insurance premium | **5%** |
| 20 | Rent of machinery, equipment etc. | **7.5%** |
| 21 | **Dividend** — received by a company, fund or trust | **20%** |
| | — received by a person other than a company, fund or trust | **25%** |
| 22 | Artist, singer or player | **30%** |
| 23 | Salary or remuneration | **30%** |
| 24 | Exploration or drilling in petroleum operations | **5.25%** |
| 25 | Survey for coal, oil or gas exploration | **15%** |
| 26 | Surveyor's fee etc. of a general insurance company | **5.25%** |
| 27 | Any service for making a connection between an oil/gas field and its export point | **5.25%** |
| 28 | **Bandwidth** payment | **10%** |
| 29 | Courier service | **10%** |
| 30 | **Any other payment** | **20%** |

**Rule 5(3) — nine outbound payments requiring NO deduction.** A closed list; a payment that
merely resembles one of these is not excluded.

(ক) payment to a **government authority of a foreign state**; (খ) **subscription fee to an
internationally recognised professional body**; (গ) **liaison office or branch office expenses**;
(ঘ) **tuition fees** per Bangladesh Bank's *Guidelines for Foreign Exchange Transactions*, verified
by an Authorised Dealer; (ঙ) **international marketing expense and product development expense**;
(চ) **any kind of security deposit**; (ছ) **arbitration fee**; (জ) **money remitted for Hajj**;
(ঝ) **payment for a priority pass**.

**Three things that change the answer completely**

1. **s.119(3), new (FA 2026 s.74)** — tax withheld from a **non-resident with no permanent
   establishment in Bangladesh** is that recipient's **FINAL TAX** and **cannot be adjusted against
   any claim**. PE and residence are determined under the applicable DTAA, or under the ITA 2023
   where there is none. A non-resident who over-suffers has **no Bangladeshi refund route**.
2. **s.119(2)** — on application with documents, the Board must within **30 days** certify nil or
   reduced deduction under a tax treaty or otherwise. **Get the certificate before remitting.**
   There is no fixing it afterwards.
3. **The s.142 uplift does not reach s.119.** s.142(1) opens *"ধারা ১১৯ এর ব্যতিক্রম সাপেক্ষে"* —
   subject to the exception of s.119 — so non-resident payments sit outside the PSR uplift.

**s.119(4)** — a share transfer giving rise to a non-resident capital gain **may not be registered**
until the tax is paid. Registration block, not penalty, is the enforcement mechanism.

**Resident vs non-resident gaps worth pricing into a contract**

| Service | Resident | Non-resident |
|---|---|---|
| Event / management service | **2%** (s.90 serial 5) | **20%** (Rule 5 serial 9) |
| Courier | **2%** (s.90 serial 5) | **10%** (Rule 5 serial 29) |
| Royalty / intangible | **10%** (s.91) | **20%** (Rule 5 serial 11) |
| Acting / performing | **10%** (s.93(2)) | **30%** (Rule 5 serial 22) |
| General insurance surveyor | **15%** (s.101) | **5.25%** (Rule 5 serial 26) |
| Salary | average rate (s.86) | **flat 30%** (Rule 5 serial 23) |

Residence status can change mid-year. Recompute rather than assuming.

---

## 5. What the tax is charged **on** — base value and gross-up

### 5.1 Base value (ভিত্তিমূল্য) — s.140(5)

> **Base value = the HIGHEST of the contract value, the bill or invoice amount, or the payment.**

This is the single most under-applied rule in Bangladeshi withholding. Deducting on the **payment
alone** is wrong whenever the contract value or the invoice is higher — a part payment against a
larger contract still bears tax computed on the contract value. **Record all three figures in the
journal narration** so the base can be justified in a s.147 verification.

### 5.2 Gross-up for a tax-free payment — s.141 with Rule 12 of SRO 273

> **C = (100 × A) ÷ (100 − B)**
> A = the tax-free payment agreed with the payee · B = the applicable rate · C = the grossed-up
> amount on which tax is computed.

**Where the payee fails PSR or does not take payment by bank transfer, B is the *uplifted* rate.**
A "net of tax" contract with a non-filing supplier therefore costs the payer materially more than
the headline rate suggests. Price that risk in, or require PSR as a condition of payment.

---

## 6. The PSR uplift — s.142

> ⚠️ **The rule is framed around *proof of submission of return* (PSR), not around possession of a
> TIN.** A payee may hold a TIN and still trigger the uplift by failing to furnish PSR.

| Rule | Trigger | Effect | Section |
|---|---|---|---|
| **PSR uplift** | Payee is **required to furnish PSR and fails to** | Rate is **50% higher than the applicable rate** | **s.142(1)** |
| **Bank-transfer uplift** | Payee **does not receive** the contract value, bill, rent, fee, charge, remuneration, salary or other payment **through bank transfer** | Rate is **50% higher than the applicable rate** | **s.142(2)** |

### 6.1 "50% higher" means × 1.5 — not +50 points

| Applicable rate | With one uplift |
|---|---|
| 1% | **1.5%** |
| 2% | **3%** |
| 3% | **4.5%** |
| 5% | **7.5%** |
| 7.5% | **11.25%** |
| 10% | **15%** |
| 15% | **22.5%** |
| 20% | **30%** |

This is the most common arithmetic error in Bangladeshi withholding. A 5% rate becomes **7.5%**,
not 55%.

### 6.2 What counts as PSR — s.264

(a) the **acknowledgement receipt** of the income tax return; (b) a **system-generated tax
certificate**; or (c) a **certificate issued by the Deputy Commissioner of Taxes** — each bearing
the payee's **name, TIN and the assessment year** the return was submitted for. **A bare TIN
certificate is not PSR.** For certain services a system-generated certificate carrying only name
and TIN may be submitted in lieu of PSR. Persons not required to submit a return are excluded.

The Finance Act 2026 "rationalised" the ambit of s.264 and added triggers — PSR is newly required
from resident **directors and sponsor shareholders**, from candidates for **Union Parishad
chairman**, and from **educational institutions seeking renewal**; taxpayers must **display their
latest PSR at their business premises**.

⚠️ **The full current s.264 service list could not be obtained.** The 43-item list in circulation is
the Finance Act 2024 version. Do not treat any published list as complete or current. See
[income-tax.md](income-tax.md).

### 6.3 Carve-outs from s.142(1) — check these before you uplift

- **s.119 payments to non-residents** are excluded by the opening words of s.142(1).
- **Proviso (added by Act 89 of 2026 s.88):** the uplift does **not** apply to a person for whom
  filing is not mandatory under **s.166(2)**, nor to a person the Board has exempted from
  furnishing PSR under **s.264(4)**.

### 6.4 Whether the two uplifts STACK is genuinely unresolved — TakaBooks will not choose

Both s.142(1) and s.142(2) independently say the rate is "50% higher than the applicable rate"
(*প্রযোজ্য হার*). **Neither cross-refers to the other. There is no stated maximum anywhere in the
Act or the Rules. Neither SRO 273 nor the Paripatra 2026-27 contains a single worked example
applying either uplift, let alone both.**

Three readings are all arguable:

| Reading | Combined multiplier | 5% becomes |
|---|---|---|
| (a) uplifts do not compound — one 50% uplift is the maximum | **× 1.5** | 7.5% |
| (b) additive on the base rate (+100%) | **× 2.0** | 10% |
| (c) multiplicative (1.5 × 1.5) | **× 2.25** | 11.25% |

**What to do:** apply **one** uplift, **disclose the second trigger to the taxpayer in writing**,
and **seek a ruling from NBR** before settling on a combined rate. Do not let a spreadsheet
silently compound them — that is how a payer ends up either under-deducting (and owing the
shortfall plus 50% of it under s.56(1)) or over-deducting from a supplier who cannot easily
recover it.

**What would confirm it:** an NBR clarification, a worked example in a future Paripatra, or an
amendment inserting a maximum into s.142. None existed as at 5 September 2026. This is recorded in
the rates file as `tds.sections.142.uplift_stacking` with `verified = false`.

---

## 7. Final tax and minimum tax

**The biggest structural change of the Finance Act 2026.** The marginal note of the replaced s.163
is *"অগ্রিম কর, চূড়ান্ত কর এবং টার্নওভার ট্যাক্স"* — advance tax, final tax and turnover tax.
**There is no "minimum tax" limb.**

| Provision | Effect | Section |
|---|---|---|
| Withholding in **excess** of assessed tax is **REFUNDABLE**, or carried forward and adjusted against prior/subsequent years | The old broad minimum-tax character of withholding is abolished | s.163(1)–(2) |
| **Only** tax under **s.138 (commercial motor vehicles)** and **s.139 (inland vessels)** is **final tax** for those sources | | s.163(3) |
| …but if tax at the applicable rate on the **declared income** exceeds that final tax, the **higher** amount is payable | | s.163(5) |
| For a person **exempt from filing under s.166(2)**, **all** Part 7 withholding is final tax | | s.163(4) |
| Non-resident **without a PE** — withholding is final tax and cannot be adjusted | | s.119(3) |
| **s.164 repealed** (excess/short withholding not to be minimum tax) | | FA 2026 s.92 |

**No longer final or minimum tax:** profit on **sanchayapatra**; capital gain on compensation for
compulsory acquisition; capital gain on transfer of property; **cash incentive/subsidy against
export**. Every one of those must now be brought into total income.

> ⚠️ **A sequencing trap.** **Act 89 of 2026 §94** (April 2026) rewrote s.163 and listed certain
> withholdings — including the 10% on WPPF payouts under s.88 — as **minimum tax**. **Act 96 of
> 2026 (the Finance Act 2026) §91 then replaced s.163 again**, effective 1 July 2026, and §92
> repealed s.164. **Any source describing a s.163(2) minimum-tax list is reading the superseded
> April 2026 version.** Verify against the current consolidated text before treating any
> withholding as minimum tax.

---

## 8. Deposit — Rule 9 of SRO 273

All deposits are made **through A-Challan (এ-চালানের মাধ্যমে)**. Enabling provision s.146(1);
**s.146(2) forbids anyone from withholding tax otherwise than under the Act** — you may not "hold"
a deduction pending a dispute.

| Row | When deducted / collected | Deposit by |
|---|---|---|
| ক | Any deduction/collection in **July to May** | Within **2 weeks from the end of the month** of deduction/collection |
| খ | Any day from the **1st to the 20th day of June** | Within **7 days** following the day of deduction/collection |
| গ | **Any other day of June** | The **next day** |
| ঘ | The **last working day of June** | The **same day** |

> ⚠️ **Row ঘ turns on the last *working* day of June, not on 30 June.** The Bangla reads
> *"অর্থবৎসরের জুন মাসের **শেষ কর্মদিবসে** কর কর্তন বা সংগ্রহের ক্ষেত্রে"* → *"কর্তন বা সংগ্রহের দিন"*.
> This matters whenever 30 June falls on a weekend or a public holiday: the same-day rule attaches
> to the last **working** day, which may be 28 or 29 June. **KPMG's published summary renders rows
> গ and ঘ as "21–29 June / 30 June", which is a simplification** and will mislead you in such a
> year.

---

## 9. Returns and certificates

| Obligation | Form | Deadline | Authority |
|---|---|---|---|
| **Withholding tax return — QUARTERLY** | **Schedule-4** to SRO 273 | **25 October** (Jul–Sep) · **25 January** (Oct–Dec) · **25 April** (Jan–Mar) · **25 July** (Apr–Jun). Weekly or public holiday → **next working day**. **NO TIME EXTENSION IS AVAILABLE.** | s.177(3); Rule 13 |
| Certificate of deduction — **salary** (not government-paid salary) | **Schedule-1** | Within **2 weeks of the month following** the month of deduction, or in time to settle the payee's liability | s.145; Rule 10(1), (5) |
| Certificate of deduction — **all sections other than s.86** | **Schedule-2** | as above | s.145; Rule 10(2) |
| Certificate of **collection** under Part 7 | **Schedule-3** | as above | s.145; Rule 10(3) |
| A-Challan for the deposit **must accompany** the certificate | — | — | Rule 10(4) |
| Bill of entry, registration deed, bank statement, payment document or deduction/collection particulars may serve as the certificate — **not for salary** | — | — | Rule 10(6)–(7) |

**Who must file the s.177 return** (as amended by FA 2026 s.105): any **company** (except
Government ministries, divisions, directorates and MPO educational institutions); **firm**;
**association of persons**; private hospital, clinic or diagnostic centre; **public-private
partnership**; **e-commerce platform or online marketplace with turnover > ৳ 1 crore**; **hotel,
resort, motel, restaurant, convention centre, community centre or transport agency with turnover
above ৳ 1 crore**; a non-farmer manufacturing tobacco leaf, cigarettes, bidi, zarda, gul or other
tobacco products; and **any natural person with business turnover exceeding ৳ 10 crore**.

**Points that catch people out**

- ⚠️ **There is NO half-yearly withholding return.** s.177(4) was deleted by the Finance Act 2024.
- ⚠️ **There is no separate annual "statement of salary"** equivalent to the old ITO 1984 ss.108 /
  108A. The salary obligation is discharged through the **s.145 / Schedule-1 certificate** plus the
  **quarterly s.177 return**. (Compliance-calendar sites listing a 25 October "Schedule Ga/Ca"
  salary statement and a 25 April "Schedule Cha" employee statement rest on **one** source and were
  **not** verified against the TDS Rules 2026 or any NBR form — see [payroll.md](payroll.md).)
- An **income tax return is incomplete** if not accompanied by the acknowledgement copy of the
  withholding tax return.
- **s.147(4), new:** a withholding verification may cover only the relevant financial year and **at
  most the 2 preceding financial years** — three years in total. A demand reaching further back is
  outside the section.

---

## 10. What a failure costs

### 10.1 The withholding agent's own liability — s.143

| Default | Consequence | Section |
|---|---|---|
| Failure to deduct/collect; deducting at a lower rate or amount; failure to deposit or depositing less; any other non-compliance | Treated as a **defaulting taxpayer** | s.143(1) |
| | Liable for the amount not deducted/collected, the shortfall, or the amount not deposited | s.143(2)(a)–(c) |
| Failure to comply with any other provision | Up to **৳ 10,00,000 (Tk 10 lakh)** | s.143(2)(d) |
| **Additional amount** on the sums in s.143(2)(a)–(c) | **2% per month** | s.143(3) |
| Period for that 2% | From the **due date of deduction/collection to the date of deposit**, **capped at 24 months** — so it tops out at **48%** of the tax | s.143(4) |
| Liability | **Government bodies:** the individuals responsible for approving payment or issuing a clearance/registration/licence/permit are **jointly and severally** liable. **Others:** the entity itself **and** the individuals responsible for approving payment | s.143(6)–(7) |
| No recovery if the **payee** has already paid everything under s.143(2) and (3) | A real defence — but it must be **established**, not assumed | s.143(8) |
| Issuing a certificate of deduction/collection/payment **without** actual deduction, collection or payment | **Personally liable** for the amount | s.144 |
| Obstructing a withholding verification | Up to **৳ 50,00,000 (Tk 50 lakh)** | s.147(2) |

**Never issue a Schedule-1, -2 or -3 certificate before the A-Challan exists.** s.144 makes the
signatory personally liable.

### 10.2 The additional tax charge on the payer — new architecture under FA 2026

| Provision | Effect | Section |
|---|---|---|
| Business or profession | Where Part 7 withholding is not complied with, the amount short-deducted/collected/paid **plus a further 50% of it** is payable — **150% of the tax defaulted** | **s.56(1)(a)** |
| | If tax paid via s.143 proceedings is less than that, the shortfall **plus 50% of it** is payable | **s.56(1)(b)** |
| Agriculture | Identical rule | **s.41(6)(a)–(b)** |
| **Acquisition of capital assets** for a business or profession | Identical rule — new | **s.56A (৫৬ক)** |
| **Disallowance of the related expenditure — ABOLISHED** | s.55(a), which disallowed the expense on a TDS default, was **deleted** by FA 2026 s.48(b) | **s.55** |

**NBR's own worked example** in the Paripatra 2026-27: applicable TDS ৳ 4,00,000, deducted
৳ 2,00,000, shortfall ৳ 2,00,000 → payable = 2,00,000 + (2,00,000 × 50%) = **৳ 3,00,000**.

> The old advice that "a TDS failure costs you twice — the tax and the deduction" is **no longer
> right**. It now costs **150% of the tax**, and the expense stands.

---

## 11. VDS — উৎসে মূসক কর্তন

### 11.1 How the obligation arises

Deduction is mandatory on a supply under a tender, contract or work order
*"মূসক চালানপত্র থাকুক বা না থাকুক"* — **whether or not a Mushak 6.3 exists**. Alongside that,
**Rule 6(1)** says that if the supplier issues no Mushak 6.3 the withholding entity **must not
accept the supply or pay for it**. The two are not in conflict: you may not transact without the
challan, and if you somehow did, you still owe the deduction.

**Structural point:** the SRO has **one** rate column — *মূসক উৎসে কর্তনের হার*. There is **no
separate "VAT rate" column**. Charts printing paired VAT/VDS columns are reconstructing, not
quoting.

**Legal framework:** **s.49** (deduction at source and the withholder's increasing adjustment);
**s.50** (the supplier's decreasing adjustment); **s.53** (VDS certificate, Mushak 6.6).

### 11.2 Complete Rule 3(1) VDS rate table, FY2026-27 — 45 serials after SRO 140 renumbering

| Sl. | Code | Service | VDS rate |
|---|---|---|---|
| 01 | S001.10 | **AC hotel** (এসি হোটেল) | **15%** |
| 01 | S001.10 | **Non-AC hotel** | **10%** |
| 01 | S001.20 | **Restaurant** † | **5%** |
| 02 | S002.00 | Decorators and caterers | 15% |
| 03 | S003.10 | Motor garage and workshop | **10%** |
| 04 | S003.20 | Dockyard | 15% |
| 05 | S004.00 | Construction firm (নির্মাণ সংস্থা) | **10%** |
| 06 | S007.00 | Advertising agency (বিজ্ঞাপনী সংস্থা) | **15%** |
| 07 | S008.10 | Printing press | 15% |
| 08 | S009.00 | Auctioneer | 15% |
| 09 | S010.10 | Land development organisation | **2%** |
| 10 | S010.20 | Building construction (ক) 1–1,600 sq ft | **2%** |
| 10 | S010.20 | (খ) 1,601 sq ft and above | **4.5%** |
| 10 | S010.20 | (গ) re-registration, any size | **2%** |
| 11 | S014.00 | Indenting organisation | 15% |
| 12 | S015.10 | Freight forwarders | 15% |
| 13 | S017.00 | Community centre | 15% |
| 14 | S020.00 | Survey agency | 15% |
| 15 | S021.00 | Plant or capital machinery rental | 15% |
| 16 | S024.00 | (ক) Furniture manufacturer ‡ | **7.5%** |
| 16 | S024.00 | (খ) Furniture sales centre § | **7.5%** |
| 17 | S028.00 | Courier and express mail service | 15% |
| 18 | S031.00 | Repair or servicing of taxable goods for consideration | 15% |
| 19 | S032.00 | Consultancy firm and supervisory firm | 15% |
| 20 | S033.00 | Izaradar (lessor) | 15% |
| 21 | S034.00 | Audit and accounting firm | 15% |
| **22** | **S037.00** | **Procurement provider (যোগানদার)** | **10%** ⚠️ |
| 23 | S040.00 | Security service | 15% |
| 24 | S043.00 | Supplier of programmes through television and online broadcast media | 15% |
| 25 | S045.00 | Legal adviser | 15% |
| 26 | S048.00 | Transport contractor (ক) **petroleum products** | **5%** |
| 26 | S048.00 | (খ) other goods | 15% |
| 27 | S049.00 | Vehicle rental (rent-a-car) | 15% |
| 28 | S050.10 | Architect, interior designer / decorator | 15% |
| 29 | S050.20 | Graphic designer | 15% |
| 30 | S051.00 | Engineering firm | 15% |
| 31 | S052.00 | Sound and lighting equipment rental | 15% |
| 32 | S053.00 | **Board meeting attendee** | **15%** |
| 33 | S054.00 | Advertisement broadcast via satellite channel | 15% |
| 34 | S058.00 | Chartered aircraft or helicopter rental | 15% |
| 35 | S060.00 | Purchaser of auctioned goods | 15% |
| 36 | S065.00 | Building, floor and premises cleaning or maintenance | 15% |
| 37 | S066.00 | Lottery ticket seller | 15% |
| 38 | S067.00 | Immigration adviser | 15% |
| 39 | S071.00 | Event organiser | 15% |
| 40 | S072.00 | Human resource supply or management organisation | 15% |
| **41** | **S083.00** | **Semiconductor assembly, testing and packaging — NEW from 1 July 2026** | **15%** |
| 42 *(was 41)* | S099.10 | IT-enabled services (ITES) | **5%** |
| 43 *(was 42)* | S099.20 | Other miscellaneous services | 15% |
| 44 *(was 43)* | S099.30 | Sponsorship services | 15% |
| 45 *(was 44)* | S099.50 | Credit rating agency | 15% |

† excluding restaurants in three-star and above listed residential hotels, restaurants in hotels
having a liquor bar, and any restaurant having a liquor bar.
‡ 15% instead where the supply runs **direct from factory to consumer**.
§ 7.5% is **conditional on holding the 7.5% production-stage challan**; without it, 15%.

**SRO 140's only change to this table** is inserting S083.00 as serial 41 and renumbering the old
serials 41–44 to 42–45.

### 11.3 Three VDS figures in wide circulation that are wrong

1. **There is no S007.10 / S007.20 split and no 5% online-advertisement VDS in any gazette.**
   SRO 182 carries a single **S007.00 বিজ্ঞাপনী সংস্থা at 15%**. A VAT-rate cut for digital
   advertising was announced at Bill passage, but **no gazette on nbr.gov.bd creates the S007.20
   code**. The likely explanation is a post-budget SRO wave NBR has not uploaded — PwC cites
   **SRO 255-Ain/2026/355-Mushak of 30 June 2026**, inside the un-served 149–266 range. Four
   announced VAT measures are untraceable for the same reason: the double-cabin pickup / microbus
   cut from 15% to 5%, the BTRC revenue-sharing VDS exemption, this digital-advertising rate and
   its S007.20 code, and the input-output-coefficient relaxation. **Do not print S007.20 at 5%.**
2. **S037.00 Procurement Provider is 10%, not 5%.** The gazette reads
   *"২২. S০৩৭.০০ যোগানদার (Procurement Provider) ১০%"*.
3. **ICAB's "S004.00 remains 7.5% for contracts signed before 30 June 2025" is not in SRO 182.**
   The full text was searched and no such proviso exists. Treat it as a practice position someone
   must justify to you from a gazette.

### 11.4 How goods enter the VDS net — there is no separate goods table

- **S037.00 যোগানদার at 10%.** Rule 4(2): everyone **other than a manufacturer** supplying goods or
  services to a withholding entity against a tender or work order **is** a procurement provider,
  unless the service has its own definition in the table.
  **New FY2026-27 carve-out (SRO 140, rule 4(2)):** a **trader** who supplies goods through a
  Mushak 6.3 **having paid 15% VAT is NOT a procurement provider.** Ask for the Mushak 6.3 first.
- **S060.00** purchaser of auctioned goods — 15%.
- **S024.00** furniture — 7.5%.

### 11.5 VDS charges arising outside the Rule 3(1) table

| Rule | Charge | Rate |
|---|---|---|
| **3(2)** | Import of a service by an **unregistered** person — the remitting bank collects and makes an increasing adjustment **in the bank's own return** | **15%** |
| **3(3)** | Import by a **registered** person — the bank remits **without deduction** against a treasury challan; where there is none or the payment is short, the bank deducts and adjusts | — |
| **3(3ক)** — new | The registered importer shows the service as **both output tax and input tax** (ss.20, 46) and the 15% treasury-challan amount at **Note 58, Part-9** of the return; no "input tax" line where s.46 bars the rebate | — |
| **3(4)** | Licence, permit or registration fee, revenue sharing, royalty, commission, charge or fee collected by **any issuing authority** | **15%** |
| **3(5)** — **replaced** | **Premises rent: EVERY tenant, registered or not, pays 15% by A-Challan or e-payment** and shows the payment evidence in the **treasury-deposit section** of the return | **15%** |

> ⚠️ **The registered-tenant increasing-adjustment route for rent is GONE.** PwC's statement that
> VAT on premises rent is "reported as an increasing adjustment in the VAT return" is **wrong
> against the gazette**. Follow the gazette.

### 11.6 Rule 5 — when NO VDS is required

(ক) a **manufacturer** supplying via Mushak 6.3 stating the 15%, reduced or specific rate;
(খ) a **trader** supplying via Mushak 6.3 at 15%, on producing an **eVAT** (formerly IVAS)
regular-filing certificate or a **মূসক সম্মাননাপত্র**, failing which a Divisional Officer's
certificate; (গ) **services outside the Rule 3(1) table** supplied via Mushak 6.3; (ঘ) fuel oil,
gas, water (WASA), electricity, telephone and mobile bills; (ঙ) **First Schedule (exempt)
supplies**; (চ) **zero-rated supplies** under s.21; (ছ) advertising agencies and TV/online
programme suppliers producing a Mushak 6.3 certified by the Revenue Officer or ARO; (জ) furniture
manufacturers producing a certified Mushak 6.3 at 15%; (ঝ) **EFD / SDC / PKI / POS fiscal receipts
stating the buyer's name and BIN**; (ঞ) purchase of **locally made medicine from a trader**;
**(ট) NEW — any supply by a registered startup.**

**Almost every limb turns on a document the supplier must produce. No document, no exclusion:
deduct.** Limb (ঝ) in particular fails if the fiscal receipt does not carry the **buyer's name and
BIN**, which most retail receipts do not.

### 11.7 Deposit, certificate and adjustment

| Party | Obligation |
|---|---|
| **Registered withholder** | **No cash deposit** — an **increasing adjustment** in the return for the tax period in which the consideration was **paid**. **Mushak 6.6 in triplicate within 3 working days of *filing the return*** — original to the VAT Circle, one to the supplier, one retained **5 years** |
| **Unregistered withholder** | **Deposit within 15 days** of paying the supplier; **Mushak 6.6 within 3 working days of the deposit**. A-Challan economic code `<circle>/1100000000/11001000/1141101`; LTU (VAT) `1110204102025` |
| **Accounts Officer route** | Rules 6(5)–(7), acting within 3 working days under rule 38(4) of the VAT & SD Rules 2016 |
| **Supplier** | **Decreasing adjustment only on receipt of Mushak 6.6**, in that tax period or the following **6 tax periods**, then **time-barred** (rule 7(4)) |

> ⚠️ **The Mushak 6.6 clock starts from a different event for each party** — the registered
> withholder counts 3 working days from **filing the return**, the unregistered one from **the
> deposit**.
>
> ⚠️ **From 1 July 2026 the VAT return is QUARTERLY, not monthly.** A registered withholder's
> increasing adjustment therefore sits in a quarterly return. Do not assume a monthly settlement
> cycle when planning cash flow or reconciling the VDS control account. See
> [vat-mushak.md](vat-mushak.md).
>
> The supplier's copy of Mushak 6.6 is the **only** thing that unlocks their decreasing adjustment.
> Withhold it and you have taken their money twice over. Chase a missing 6.6 immediately — six
> quarterly tax periods is a long time in months but a small number of filings.

### 11.8 VDS liability and penalties — Rule 8

- **Withholder and supplier are jointly and severally liable.** NBR may recover the whole amount
  from whichever party is easier to reach; the buyer cannot point at the supplier and the supplier
  cannot point at the buyer.
- Failure → recovery under **s.85(1ক)** with **s.127 interest**, **plus a personal fine of up to
  ৳ 25,000** on the **deductor**, the **person responsible for deposit**, **and the chief
  executive** — three people, each personally.

### 11.9 Subcontractors and commercial importers

- **s.49(5):** the non-deduction facility for subcontractors, agents and other service renderers
  engaged to deliver part of a project is **restricted to the FIRST TIER ONLY**. VDS **must** be
  deducted from payments to lower-tier subcontractors. A main contractor applying first-tier relief
  down the whole chain is under-deducting at every level below the first.
- **Commercial importers:** an importer paying **Advance Tax at 7.5%** at import need not pay VAT
  again on the first sale, provided (a) value addition on the first sale is **not more than 50%**
  and (b) a tax invoice is issued in the prescribed manner — final settlement of AT under **s.31**.

---

## 12. Where TDS and VDS both bite

The two systems are independent. The same invoice can carry both, at different rates, on different
bases, with different deadlines and different certificates.

| Transaction | TDS (income tax) | VDS (VAT) |
|---|---|---|
| Board meeting attendance fee | **20%** — s.90 Rule 4 serial 7 | **15%** — S053.00 |
| Caterer's bill | **2%** — s.90 Rule 4 serial 5 | **15%** — S002.00 |
| Event organiser's bill | **2%** — s.90 Rule 4 serial 5 | **15%** — S071.00 |
| Motor garage / workshop | **5%** — s.90 Rule 4 serial 10 | **10%** — S003.10 |
| Credit rating agency | **10%** — s.90 Rule 4 serial 9 | **15%** — S099.50 |
| Private security service | **10% on commission or 1% on gross, higher of** — serial 4 | **15%** — S040.00 |
| Community centre hire | **10%** — s.110 | **15%** — S017.00 |
| Construction contract | **5%** — s.89 serial 18 | **10%** — S004.00 |

Post them as separate tax lines. Never net one against the other, and never let one certificate
stand for both.

---

## 13. What this file does not hold

Absent beats wrong. What remains here is **real obligations whose figures are not settled by the
primary text**, plus the parts of SRO 273 that are procedure rather than rates. Nothing in this
section is guessed at.

### 13.1 No longer missing — Rules 6, 7 and 8, and the fixed amounts

The five obligations this section used to list as `placeholder = true` have been landed:

| Obligation | Now at | Source read |
|---|---|---|
| **s.125** collection on transfer of property | [§3.13](#313-ss125126--property-transfer-and-developers--rules-6-and-7-of-sro-273) | Rule 6 of SRO 273, gazette pages 20684–20690 |
| **s.126** collection from real estate / land developers | [§3.13](#313-ss125126--property-transfer-and-developers--rules-6-and-7-of-sro-273) | Rule 7 of SRO 273, gazette pages 20690–20693 |
| **s.120** collection at the import stage | [§3.12](#312-s120--collection-at-the-import-stage--rule-8-of-sro-273) | Rule 8 of SRO 273, gazette pages 20693–20718 — all 345 HS rows |
| **s.138** commercially operated motor vehicles | [§3.14](#314-ss138-138a-139--fixed-amount-advance-taxes) | ITA 2023 s.138 সারণি — **not in SRO 273** |
| **s.138A** civil aircraft — **new** | [§3.14](#314-ss138-138a-139--fixed-amount-advance-taxes) | ITA 2023 s.138A সারণি — **not in SRO 273** |
| **s.139** inland vessels | [§3.14](#314-ss138-138a-139--fixed-amount-advance-taxes) | ITA 2023 s.139 সারণী — **not in SRO 273** |

Rules 6 and 7 turned out **not** to be mouza-by-mouza lists at all — they group whole **thanas**,
which is why they fit on nine gazette pages rather than the "dozens" this file once assumed.

**What is still not held from SRO 273:** Rules 10–13 and তফসিল-১ … তফসিল-৪ — the withholding-return
format, the certificate of deduction, the monthly and annual statements and the register a
withholding entity must keep. These are **procedural layouts, not rates**, and nothing computes
from them. Read the SRO's তফসিল pages (gazette 20721 onward) when preparing an actual return.

### 13.2 Two questions Rule 8 does not settle

Both are recorded in the rates file rather than resolved, because the gazette does not resolve
them:

1. **The reach of the 4% industrial-IRC proviso.** Read literally it covers every good outside
   সারণী-৫, displacing the 0%, 1% and 2% tables for that class of importer; read as a proviso to
   clause (ঙ) it only fills the gap before the 5% residual. Ask the Commissioner of Customs.
2. **The gazette misnumbers সারণী-৭ as "সারণী-৬"** in clause (ছ) while captioning the table below it
   সারণী-৭. The ৳600-per-tonne charge belongs to সারণী-৭; the error is the gazette's.

Both are set out at [§3.12](#312-s120--collection-at-the-import-stage--rule-8-of-sro-273).

Where a figure here and the collecting authority disagree — the registering officer, the
Commissioner of Customs, the BRTA, the Department of Shipping — **the authority's line governs the
transaction**. Take the SRO or the section with you rather than a secondary chart.

### 13.3 Landed but `verified = false` — the s.142 stacking question

See [§6.4](#64-whether-the-two-uplifts-stack-is-genuinely-unresolved--takabooks-will-not-choose).

### 13.4 Sourcing limit worth stating plainly

The s.89, s.90 and s.119 tables rest on **two primary renderings that agree with each other** — the
SRO 273 gazette (legacy-Bijoy encoding, decoded) and NBR's own Paripatra 2026-27 Appendix-1 (clean
Unicode) — plus an independent reading of the gazette page images. **No third-party professional
publication reflecting SRO 273 was found**; PwC's *Finance Act 2026: Key Amendments* predates it
and covers only Act-level changes. So there is **no professional cross-check** on those three
tables. That is a stronger position than any secondary chart offers, but it is not a triple
confirmation, and it is stated here rather than glossed over.

One immaterial transcription note: serial 4 of the Rule 3 goods list renders a token as "আয়োডিন"
between "ময়দা" and "লবণ", almost certainly **আয়োডিনযুক্ত লবণ** (iodised salt) split across a line
break. It does not affect any rate; confirm against a clean copy before coding the goods list
itself.

---

## 14. Answering a withholding question — the order that avoids the traps

1. **Which side is the user on?** Deducted *from* them (receivable) or *by* them (liability plus
   duties)? → [§1.4](#14-the-two-sides--never-conflate-them)
2. **Is the payer a specified person / withholding entity at all?** If not, there is no obligation.
   → [§2](#2-who-must-deduct)
3. **Is the payee resident or non-resident?** Non-resident goes to s.119 / Rule 5, and the s.142
   uplift does not apply. → [§4](#4-tds-rate-matrix--payments-to-non-residents--s119-rule-5-of-sro-273)
4. **Which section authorises the deduction?** Check the specific serials before the residuals
   (s.89 serial 20, s.90 serial 19 and Rule 5 serial 30 are all fallbacks, and two of the three
   are high).
5. **What is the base?** Highest of contract value, invoice, payment — s.140(5). Gross up if the
   payment is tax-free. → [§5](#5-what-the-tax-is-charged-on--base-value-and-gross-up)
6. **Does the PSR or bank-transfer uplift apply?** × 1.5, not +50 points. If both trigger, apply
   one, disclose the other, seek a ruling. → [§6](#6-the-psr-uplift--s142)
7. **Does VDS apply to the same invoice?** Separate rate, separate deposit, separate certificate.
   → [§11](#11-vds--উৎসে-মূসক-কর্তন)
8. **State the deposit deadline and the certificate deadline in the same answer.** A deduction the
   user does not deposit is worse for them than one they never made.
9. **Cite the instrument** — SRO 273 rule and serial, or the ITA 2023 section — and say whether the
   figure is verified. Where the rates file says `verified = false`, **read that caveat aloud**.
10. **End with the disclaimer.**

---

## 15. Definition of done — status against the original criteria

1. ✅ Every figure carries a primary-source URL and a "current as of" date, in
   `data/rates-AY2026-27.toml` and in the source block at the top of this file.
2. ⚠️ **Amended deliberately.** The original criterion said no rate belongs in this prose. The rate
   matrix is the reason this file exists, so it is reproduced here. **`data/rates-AY2026-27.toml`
   remains the machine-readable source of truth and the only thing the engine computes from.**
   Tables here name their TOML keys. **Change one and you must change the other**, in the same
   commit.
3. ✅ Anything not confirmed from primary text is `verified = false` or `placeholder = true` in the
   rates file and is flagged in [§13](#13-what-this-file-does-not-hold).
4. ✅ Statutory terms appear as Bangla ∥ English pairs.
5. ⬜ **Not yet reviewed by a Bangladeshi ITP or CA.** Required before release.
6. ✅ Header block filled in.

**Updating after the next Finance Act:** find the new উৎসে কর বিধিমালা SRO on
<https://nbr.gov.bd/regulations/sros/income-tax>, **check its number and date against any earlier
SRO of the same title in the same year, and read its repeal rule** — this has now happened twice.
Cross-read every rate against that year's আয়কর পরিপত্র. Replace `value`, `source` and `as_of` node
by node; do not bulk-edit. Anything you could not read from primary text stays `verified = false`
with a note saying exactly what is missing.

---

> **Disclaimer.** This is reference material, not professional advice. Bangladeshi withholding
> changes by SRO between Finance Acts, and two SROs of 2026 share a title. **Verify with a licensed
> Income Tax Practitioner (ITP) or Chartered Accountant (CA), and against the gazette, before you
> deduct, deposit or file.**

**See also:** [income-tax.md](income-tax.md) · [vat-mushak.md](vat-mushak.md) ·
[payroll.md](payroll.md) · [compliance-calendar.md](compliance-calendar.md) ·
[penalties.md](penalties.md) · [glossary-bn-en.md](glossary-bn-en.md)

---
Maintained by Moshiur Rahman (@bemoshiur) · Ticon Sys — https://ticonsys.com · MIT
