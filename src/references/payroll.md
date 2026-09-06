# Payroll — বেতন ও শ্রম সংক্রান্ত

**Current as of:** 2026-09-06
**Assessment year:** AY 2026-27 / করবর্ষ ২০২৬-২০২৭, for the income year 1 July 2025 – 30 June 2026.
Deductions being made *today* (income year 2026-27) follow the same Finance Act 2026 rate card, which
is legislated for AY 2026-27 through AY 2030-31.
**Sources:** primary text first — the Income Tax Act 2023 (আয়কর আইন, ২০২৩) and the Bangladesh Labour
Act 2006 on bdlaws.minlaw.gov.bd, the 2026 amending Acts, and NBR's উৎসে কর বিধিমালা, ২০২৬
(SRO 273-আইন/আয়কর-৫/২০২৬). Professional summaries (KPMG / Rahman Rahman Huq, PwC, ACE Advisory) are
used only where the primary text could not be read, and are **named every time they are relied on**.
**Status:** POPULATED. Every statement below is traceable to a source named on the line. Confidence is
marked inline — see "How to read the confidence marks". **Not yet reviewed by a Bangladeshi Income Tax
Practitioner or Chartered Accountant.**

> **How to read the confidence marks.**
> **[PRIMARY]** — read from the gazette, from bdlaws, or from an NBR-published Act/SRO/Paripatra.
> **[SUMMARY]** — rests on one or more professional firms' post-enactment summaries. The Finance Act
> 2026 gazette PDF is typeset in a legacy Bijoy Bangla encoding that does not extract to readable
> text, so anything sourced only to "Finance Act 2026 Schedule" is in this class. State the source to
> the user when you use one of these.
> **[UNCONFIRMED]** — the research could not confirm it, or sources conflict. **Do not present an
> [UNCONFIRMED] item as a rule, a rate or a deadline.** Say what is known, say what is not, and send
> the user to NBR and a licensed ITP/CA.

> **Where the machine-readable numbers live.** Anything TakaBooks *computes* with — the salary
> exemption cap, withholding rates, thresholds — belongs in `src/data/rates-AY<year>.toml`, in the
> `[income_tax…]` and `[tds…]` blocks, which a different maintainer owns. This file explains, cites
> and routes. Where a figure appears below it is here so the reader can check the citation, **not so
> a calculator can read it from prose**. If the corresponding TOML node is missing or still carries
> `placeholder = true`, `src/engine/rates.py` will refuse to compute from it — that refusal is
> correct, and the answer to the user is "TakaBooks does not hold a verified figure for this", never
> a number copied out of this document.

---

## 1. What counts as salary — ITA 2023 s.32 [PRIMARY]

**বেতন খাতে আয় / income from employment** covers monetary receipts, salaries and benefits received or
receivable; income from employee share schemes; untaxed arrear salary; and any amount or benefit from
a **past or future** employer — not only the current one.

The s.32 Explanation defines **"salary" (বেতন)** to include salary, wages and remuneration; any
**ভাতা / allowance**, leave allowance, **ছুটি নগদায়ন / leave encashment**, **বোনাস**, fees, commission,
**অতিরিক্ত সময়ের মজুরি / overtime**; advance salary; gratuities, annuities and pensions;
**আনুষঙ্গিক সুবিধা / perquisites**; and profit in lieu of or in addition to salary.

**"Profit in lieu of salary"** includes termination compensation by whatever name it is called, the
portion of a fund payment excluding the employee's own contribution, and the fair market value of
benefits arising from modified employment terms or from joining.

**"Perquisite" — s.32 Explanation (c).** Any payment or benefit from employer to employee,
**including incentive bonus**, but *excluding*: basic salary, arrears, advance salary, festival
allowance, leave encashment and overtime; and employer contributions to a recognised provident fund,
an approved pension, gratuity or superannuation fund. Act 89 of 2026 added **group insurance premium**
to that exclusion list.

**Statutory exclusions from employment income — s.32(2)**, as amended by Act 89 of 2026 §40:

| Excluded from employment income | Provision |
|---|---|
| Medical expense receipts for **heart, kidney, eye, liver and brain operations, artificial organ transplant, and cancer treatment** — only for an employee who is **not a shareholder director** | s.32(2)(a) as substituted |
| **যাতায়াত ভাতা / conveyance, travelling and daily allowance** incurred *wholly and exclusively* in performing the duties of the employment | s.32(2)(b) |
| **Group insurance premium** paid by the company to an insurer on the employee's behalf | new s.32(2)(c) |
| Medical expenses **reimbursed under a group insurance policy** | Finance Act 2026 change — **[SUMMARY]**, PwC Bangladesh, *Finance Act 2026: Key Amendments*, p.7 |
| Expenses incurred by an employee on official work, where necessary and advantageous to the employer | Sixth Schedule Part 1, para 14 |

**Quick taxability reference.** **[SUMMARY]** — ACE Advisory, *Bangladesh Tax Insights 2026-2027*
(10th ed.), https://aceadvisory.biz/resource/publications/bangladesh-tax-insights-2025-2026 :

| Item | Treatment |
|---|---|
| Basic salary, festival bonus, performance bonus, dearness allowance, leave encashment, leave fare assistance | Fully taxable |
| **Employer's contribution to a recognised provident fund** | **Fully taxable in the employee's hands** |
| Interest income from a recognised PF | Exempt — 6th Sch Pt 1 para 6 |
| Approved gratuity fund | Exempt up to the ceiling at §7 below |
| Group insurance premium; medical reimbursed by the insurer | Exempt |
| **শ্রমিক অংশগ্রহণ তহবিল / WPPF receipts** | **Fully taxable — no exemption limit.** See §8 |
| Telephone / mobile allowance and reimbursements | Tax free so far as they are for official use |
| Other allowances | Fully taxable |

**Employee share schemes — s.34:** taxable on receipt at fair market value less acquisition cost.
Act 89 of 2026 extended s.34 to the **"right to acquire shares"**, not only to shares themselves.

---

## 2. The consolidated salary exemption — one cap, not a list of allowances

> **Sixth Schedule, Part 1, paragraph (27): one-third of income computed under "income from
> employment", OR Tk 500,000 — whichever is LOWER — is excluded from total income.**

This is a **single consolidated cap on employment income as a whole**. It is not a menu of head-by-head
allowances to be claimed separately, and it is applied after the s.32(2) statutory exclusions above,
which are a different relief and stand on their own.

**The cap is Tk 500,000, not Tk 450,000.** The change was made by **Act 89 of 2026 §135(ক)(৭)**, which
substituted **"৫ (পাঁচ) লক্ষ"** for **"৪ (চার) লক্ষ ৫০ (পঞ্চাশ) হাজার"** in paragraph (27).

| What supports it | Type |
|---|---|
| bdlaws — Act 89 of 2026 §135(ক)(৭), the amending text itself — http://bdlaws.minlaw.gov.bd/act-1718/chapter-details-2808.html | **[PRIMARY]** |
| ACE Advisory, *Tax Insights 2026-2027*, citing 6th Sch Pt 1 para 27 | [SUMMARY] |
| PwC Worldwide Tax Summaries, reviewed 31 July 2026 — https://taxsummaries.pwc.com/bangladesh/individual/deductions | [SUMMARY] |
| KPMG / Rahman Rahman Huq, *Bangladesh Tax 2026*, p.45 — https://assets.kpmg.com/content/dam/kpmg/bd/pdf/Tax/Bangladesh_Tax_2026.pdf | [SUMMARY] |

> ⚠️ **NBR's own Authentic English Text of the Income Tax Act 2023** (SRO 404-Law/2025, 8 October
> 2025, https://nbr.gov.bd/uploads/acts/Income_tax_act_2023.pdf) **still prints "4 lakh 50 thousand"**.
> It was published before Act 89 of 2026 and its amendment footnotes stop at the Finance Act 2024.
> **Do not quote that PDF for this figure**, and be careful before treating it as current on any other
> figure either.

> ⚠️ **An internal inconsistency in the research, reported rather than smoothed over.** The research
> document's §5.2 identifies the provision as **Sixth Schedule Part 1 paragraph (27)** on the strength
> of the bdlaws amending text. Its own UNVERIFIED list at **§C7** says the opposite — that "the Sixth
> Schedule paragraph number for the salary allowance exemption was not identified" and that the cap
> "comes from KPMG p.45". §C7 reads like a stale entry left standing after §5.2 was researched
> further, but **nobody has confirmed that reading**. Practical consequence: treat **the Tk 500,000
> amount** as strongly corroborated — four sources, one of them the amending gazette text — and treat
> **"paragraph (27)"** as the weaker half of the claim. If you are drafting a return or a submission
> that must cite the paragraph, verify the number against the consolidated Sixth Schedule first.

---

## 3. Government employees follow a different rule entirely

| | General employees | Government employees |
|---|---|---|
| Relief | Lower of one-third of employment income or Tk 500,000 | **All salary items fully exempt EXCEPT (i) basic salary, (ii) festival allowance, (iii) bonus** |
| The one-third / Tk 500,000 cap | Available | **NOT available** |
| Authority | 6th Sch Pt 1 para 27 | **SRO No. 225-Law/Income Tax-7/2023 dated 13 July 2023** |

**[UNCONFIRMED — the SRO number].** The number 225-Law/Income Tax-7/2023 comes from **ACE Advisory**
plus a corporate social-media post. The *substance* — a July 2023 notification leaving only basic
salary, festival allowance and bonus taxable — is corroborated by New Age
(https://www.newagebd.net/article/207371/income-tax-exemption-for-govt-employees-widened) and Prothom
Alo (https://en.prothomalo.com/business/local/b4d7wqtshz), but **neither of them prints the SRO
number**. Nobody read the SRO itself. Tell a government-employee user the substance, name it as
second-hand, and send them to the SRO before they file on it.

> ⚠️ Do not repeat New Age's line about a separate "house rent allowance (up to Tk 4,50,000 or
> one-third of rent, whichever is lower)". The research assesses that rendering as **garbled**. There
> is no such freestanding house-rent exemption in what was verified.

---

## 4. Perquisites, company car and accommodation — s.33

**Monetary value of perquisites, s.33 Table** — substituted by **Act 89 of 2026 §41**, confirmed
against the bdlaws amending text, PwC Worldwide Tax Summaries and ACE Advisory. **[PRIMARY]**

| Perquisite | Determined value added to taxable salary |
|---|---|
| **Accommodation** | (a) the **annual value**, where the rent is fully paid by the employer or the accommodation is provided by the employer; (b) where it is provided at reduced rent, **the difference** between that annual value and the rent the employee actually pays |
| **Motor vehicle, per vehicle** — engine up to 1,500 cc | Tk 15,000 per month |
| — above 1,500 cc and up to **2,000 cc** | Tk 20,000 per month |
| — above 2,000 cc and up to 2,500 cc | Tk 30,000 per month |
| — above 2,500 cc | Tk 50,000 per month |
| Any other perquisite, allowance or benefit | Monetary value, or fair market value |

> ⚠️ **KPMG's *Bangladesh Tax 2026* car table contains a typo** — it prints overlapping
> "1500 cc to 2500 cc" and "2000 cc to 2500 cc" bands, which makes the middle of the range ambiguous.
> **The table above is the resolved version:** the second band is **1,500–2,000 cc**, per the bdlaws
> amending text, PwC Worldwide Tax Summaries and ACE Advisory, which agree with each other against
> KPMG. If a user shows you a chart with overlapping bands, that is the KPMG typo propagating.

**Employer-side cap — s.55(d).** Perquisites payable to an employee are capped at **Tk 2,500,000 per
year**; any excess is **disallowed in the company's own tax assessment**. The chain is Tk 1,000,000
originally → Tk 2,000,000 by Act 89 of 2026 §50(খ) → **Tk 2,500,000 by the Finance Act 2026**.
**[SUMMARY] for the Tk 2,500,000 step** — that step rests on the professional summaries, because the
Finance Act 2026 gazette text could not be read. The cap does **not** apply where the perquisites were
paid under a Government-gazetted Wage Board recommendation.

**Also disallowed for the employer — s.55(k):** any payment under the head *income from employment*
made **by any means other than bank transfer**. In practice this makes cash salary a deduction risk
for the company, independent of any withholding question.

---

## 5. Deducting tax from salary — s.86

| Item | Rule | Provision |
|---|---|---|
| **The method** | At the time of making payment, deduct at **the AVERAGE of the rates applicable to the payee's ESTIMATED total income** under "income from employment" for the year | **s.86(1)** |
| Government DDOs | Same average-rate method on estimated total income, applied when the salary bill is prepared/signed, where annual taxable salary exceeds the tax-free limit | s.86(3) |
| Mid-year adjustment | The deduction may be increased or decreased to correct an excess or deficiency **of the current income year** — Act 89 of 2026 §61 changed "previous" to "current" | s.86(4) |
| Nil / lower deduction | The DCT may certify nil or a reduced rate for the remainder of the income year, on the employee's application and evidence | s.86(5) |
| MPs' honorarium | Average rate on estimated total honorarium | s.87 |
| Deposit to the Treasury | Within the time prescribed by Rule 9 of SRO 273 — **all deposits by A-Challan**. See `withholding-tds-vds.md` | s.146 |
| Certificate to the employee | **Schedule-1** to SRO 273, within **2 weeks of the month following** the month of deduction, or in time to settle the payee's liability | s.145; SRO 273 Rule 10(1), (5) |

**This is the single most common payroll error in Bangladesh.** ACE Advisory lists it first among SME
pitfalls: deducting at a flat slab rate instead of the average rate on estimated annual income. It
under- or over-withholds all year, and **the employer, not the employee, carries the shortfall**.

**Consequences of under-deduction — s.143.** The employer is deemed an **assessee-in-default**, liable
for the tax not deducted plus **2% per month, capped at 24 months** (s.143(3)–(4)). The organisation
**and** the individuals who approved the payment are **jointly and severally liable** (s.143(6)–(7)).
Issuing a deduction certificate without an actual deduction makes the issuer **personally liable**
(s.144). On top of that, the rebuilt **s.56(1)** makes the payer liable for the shortfall **plus a
further 50% of it — 150% of the tax defaulted**; NBR's own worked example in the Paripatra 2026-27
confirms the arithmetic. Detail and citations live in `withholding-tds-vds.md` and `penalties.md`.

**The PSR uplift — s.142(1).** If a payee who is liable to furnish a **Proof of Submission of Return
(PSR)** fails to furnish it, the withholding rate is **50% higher**. Whether the s.142(1) uplift stacks
with the s.142(2) uplift (payment not made by bank transfer), and whether there is any ceiling, is
**[UNCONFIRMED]** — neither SRO 273 nor the Paripatra 2026-27 contains a worked example applying
either uplift. Do not compute a combined rate; tell the user to seek a ruling.

---

## 6. What the employer files, and the one item you must not turn into a deadline

**The structural change first, because it is easy to get wrong.** The Income Tax Act 2023 does **NOT**
carry forward the old ITO 1984 **s.108** ("Statement regarding payment of salary") or **s.108A**
("Information regarding filing of return by employees") as standalone sections. The full section index
of the Act was checked and no equivalent exists. **[PRIMARY]** The salary reporting obligation is now
discharged through:

1. the **s.145 / Schedule-1 certificate** to each employee (above); and
2. the **quarterly withholding return under s.177** — **25 October, 25 January, 25 April, 25 July**,
   next working day if that falls on a weekly holiday or public holiday, **no extension available**.
   Filers, form and penalties: see `withholding-tds-vds.md` and `compliance-calendar.md`.

> ### ⚠️ The annual salary statement — present this as unconfirmed, never as a deadline
>
> Some compliance calendars show two extra annual statements filed alongside the quarterly return: a
> **statement of yearly salary payments** (employee-wise salary paid and TDS deducted) with the
> Jul–Sep return, and an **employee tax statement** with the Jan–Mar return, on schedules variously
> lettered "Ga"/"Ca" and "Cha".
>
> **[UNCONFIRMED] — this is the weakest item in the whole payroll section, and the research says so.**
> It comes from **one compliance-calendar site** (Khan Akber & Co.,
> https://khanakber.com/bangladesh-annual-compliance-calendar/) plus one corroborating source of the
> same type. It was **not** verified against the TDS Rules 2026 text or against any NBR form. It is
> actively **contradicted elsewhere**: ACE Advisory's own treatment of the quarterly return does not
> mention a separate salary statement at all, and ACE's on-going-obligations page still lists a legacy
> **31 August** annual statement. NBR's public forms portal still serves the obsolete ITO 1984 s.75A
> form. The same compliance-calendar source also carries a pre-Finance Act 2026 advance-tax threshold,
> so its other figures should not be trusted either.
>
> **What IS confirmed:** the Act carries no standalone ss.108/108A equivalent, and the s.177 return
> format comprises four parts **plus two schedules** — which is *consistent with* two annual
> statements but does not prove their content, their schedule letters or their deadlines.
>
> **So: do not put a 25 October or 25 April salary-statement date in anyone's calendar on this
> basis.** Tell the employer the quarterly s.177 return is the confirmed obligation, that additional
> annual salary schedules may form part of that return, and that they should confirm the current
> return format with their circle office or ITP.

**Penalties.** Failure to file the s.177 return — the higher of **10% of the tax on last assessed
income** or **Tk 5,000**, plus **Tk 1,000 per month** of continuing default (s.266(2)(a)). Failure to
furnish the s.145 certificate — up to **Tk 5,000** plus **Tk 1,000 per month** (s.266(2)(b)).

**What replaced the "list of employees who filed returns" — and it bites harder.** Under **s.264(3)**
as wholly substituted by **Act 89 of 2026 §122**, PSR must be furnished by **item 24** — any person
receiving salary and allowances in a **management, administrative or production-supervisory position**
— and **item 25** — **public servants of grade 10 or above**. And **s.55(o)**, as amended,
**disallows as a business expense any sum paid to a person liable to furnish PSR under clauses 24, 26,
27, 33, 36 and 37 who fails to furnish it at the time of payment.** Clause 24 is in that list.

> **Read that consequence plainly to the user:** salary paid to a managerial, administrative or
> supervisory employee who has not produced a PSR is **disallowed in the employer's own assessment** —
> and separately attracts the 50% withholding uplift under s.142(1). Collect PSRs from managerial
> staff *before* the payment, not at year end.

---

## 7. Provident fund and gratuity

### 7.1 Recognised provident fund — Second Schedule, Part 3 [PRIMARY, single reading]

> ⚠️ The research obtained **no independent second reading of the Second Schedule**. The content below
> rests on one careful reading of NBR's authentic English text plus ACE Advisory. Treat fund-structure
> questions as needing a CA's confirmation.

**Recognition conditions:** Part 3 does not apply to a fund governed by the **Provident Funds Act
1925** (para 1). All employees must be employed in Bangladesh, or by an employer whose principal place
of business is in Bangladesh — the Commissioner may recognise a foreign-based employer's fund where
**≤10%** of employees are outside Bangladesh (para 2(a)). The employee contributes a **definite
proportion of salary**, deducted at each periodical payment and credited to an individual account
(para 2(b)). **The employer's contribution shall not exceed the employee's own contribution** in that
year (para 2(c)). The fund vests in **two or more trustees** under an irrevocable trust (para 2(e)).
The employer may not recover anything from the fund except on dismissal for misconduct or on
resignation otherwise than on specified grounds (para 2(f)). Trustees apply in writing to the
**Commissioner of Taxes** with the trust deed and fund rules; ACE Advisory reports recognition takes
effect within **60 days** of application and must fall on or before the last day of the same fiscal
year. **[SUMMARY]** for those timing figures.

**Tax treatment:**

| Party / item | Treatment | Provision |
|---|---|---|
| Employer's contribution — company side | **Deductible** from income, profits and gains | 2nd Sch Pt 3 para 5(1) |
| Employer's contribution — employee side | **Fully taxable as salary.** Do not net it off | s.32 |
| Employee's and employer's contributions | Eligible investment for the **investment tax rebate** | 6th Sch Pt 3 |
| Contributions received by the fund | Exempt in the fund's hands | 6th Sch Pt 1 para 6(a) |
| Income distributed to beneficiaries, already taxed in the fund's hands | Exempt | 6th Sch Pt 1 para 6(b) |
| **Interest / other income from the fund** | Exempt up to **A** where **A < (B × 33%)**; the excess **A − (B × 33%)** is included in income. A = amount received from the fund in the income year; B = income from employment excluding that amount | 2nd Sch Pt 3 para 5(2) |
| **Accumulated balance on withdrawal** | **Exempt** where the employee has rendered **continuous service with the employer of not less than 5 years**. The Commissioner may allow it for shorter service where employment ended through ill health, contraction or discontinuance of the employer's business, or another cause beyond the employee's control | 2nd Sch Pt 3 para 6(1) |
| If the 5-year condition fails | The DCT **recomputes tax for each year as if the fund had never been recognised**; the excess is payable on top of the tax for the year of payment | para 6(2) |
| Withholding on payment of the accumulated balance | Treated as **salary**, deducted at **average rates** | para 6(4) |
| **Unrecognised PF** | Employer contributions are **NOT allowable** — s.55(u) disallows "any contribution to any fund for which there is provision of approval under this Act but no such approval is obtained"; and **no investment rebate** for the employees | s.55(u) |

**Government vs non-government funds.** A PF under the **Provident Funds Act 1925** (GPF and
equivalents) has **all its income exempt** (6th Sch Pt 1 para 7) — a wider exemption than the para 6
treatment of a recognised private fund. An establishment that constitutes a PF under Labour Act s.264
is **deemed a government institution for the purposes of the Provident Funds Act 1925** (Labour Act
s.264(17)).

**Finance Act 2026 changes. [SUMMARY]** — **recognition of the fund is now a PRECONDITION for the
employee's investment tax rebate** on PF contributions, and **premature withdrawal of rebate-earning
investments attracts pro-rated additional tax**. An unrecognised fund now costs the employee as well
as the employer.

**The 2023 "PF taxation" scare — resolved.** ICAB and others warned in 2023 that the ITA 2023 had made
private-sector PF, gratuity and WPPF fund income taxable for the first time (The Daily Star,
20 September 2023, https://www.thedailystar.net/business/economy/news/provident-funds-pay-275-tax-3423051).
ACE Advisory's 2026-27 edition states plainly that **funds are not required to submit annual income
tax returns**, citing s.166(2) — independently confirmed from the bdlaws text of **Act 89 of 2026
§95(খ)**, whose substituted **s.166(2)(ঞ)** exempts **"তহবিল"** (funds) from mandatory return filing.
**[PRIMARY]**

> ### ⚠️ [UNCONFIRMED] The fund-level tax rate — do not pick a number
>
> **Two Daily Star pieces give different rates** for tax on the *investment income* of provident,
> gratuity and WPPF funds, and **no primary charging section was located** for either. The research
> leaves this open on purpose, and so does TakaBooks. **Do not state a fund-level rate, do not average
> the two, and do not pick the one that sounds more likely.** What is confirmed is only that funds are
> outside the mandatory-return net (s.166(2)(ঞ)), which is a filing point and not a charging point.
> Tell the user to get a formal opinion.

### 7.2 When a provident fund becomes MANDATORY — Labour Act s.264 [PRIMARY]

**Labour Act 2006 s.264(10)**, as substituted by the **Bangladesh Labour (Amendment) Act 2026 (Act 43
of 2026) §56(খ)**, read from http://bdlaws.minlaw.gov.bd/act-952/section-26316.html :

> In an establishment with **not less than 100 permanent workers**, the owner **shall be bound** to
> constitute a provident fund if **not less than two-thirds** of the workers demand it by written
> application.

- **s.264(9):** every permanent worker, after **completing one year of service**, contributes monthly
  **not less than 7% and not more than 8% of monthly basic wages** unless otherwise agreed; **the
  employer contributes at the same rate**.
- **s.264(11):** where a demand is made, the owner must frame rules **within six months** of the
  application and start the fund before that period expires.
- **s.264(15):** the fund's audited accounts and audit report go to the **Director of Labour within
  one month** of the audit report being submitted.

> ⚠️ **PwC's Worldwide Tax Summaries is out of date on this trigger.** It states "at least
> three-fourths of the total number of workers" and omits the 100-permanent-worker threshold
> altogether. **The primary Labour Act text as amended in 2026 says two-thirds and ≥100 permanent
> workers.** If a user quotes three-fourths, they are reading the stale PwC page.

**The Universal Pension Scheme is now an express alternative — not a separate mandate.** The marginal
note to s.264 was substituted by Act 43 of 2026 §56(ক) to read *"Provident fund **or participation in
the Universal Pension Scheme** for workers of private sector establishments"*. Under the substituted
s.264(10), the owner is **exempted from the mandatory-PF obligation** if he ensures institutional
participation, for those employees who express written interest, in the National Pension Authority's
**সর্বজনীন পেনশন স্কিম "প্রগতি" (Progoti)**. *Proviso:* in that scheme **the owner pays 50% of the
contribution and the worker 50%**. *Further proviso:* where a worker expresses written unwillingness
to join, the owner is **not bound** to pay his 50%.

> **So: the Universal Pension Scheme is NOT compulsory for private employers in 2026.** It becomes
> relevant only once the ≥100-worker / two-thirds-demand trigger for a mandatory PF is met, at which
> point the employer may elect Progoti instead of a fund.

### 7.3 Gratuity — আনুতোষিক

**Income tax side:**

| Source of gratuity | Exemption | Provision |
|---|---|---|
| **Government Gratuity Fund** | Income up to **Tk 25,000,000** (Tk 2 crore 50 lakh) | 6th Sch Pt 1 para 5 |
| **Any NBR-approved gratuity fund** | Amount received "shall not exceed the limit of Taka 2 crore and 50 lakh" | 6th Sch Pt 1 para 6, proviso |
| **Unapproved / internal gratuity fund** | Employer contributions are **not allowable expenditure** | s.55(u) |

The Tk 25,000,000 figure is confirmed by NBR's authentic English text, ACE Advisory and KPMG.
**[PRIMARY, with a caveat]** — the same NBR English text is demonstrably stale on the salary cap
(§2 above), so it cannot be treated as automatically current; here it is corroborated by two summaries
and no source contradicts it.

**Approved gratuity fund — Second Schedule Part 2.** Para 1 conditions: an irrevocable trust connected
with a trade or undertaking in Bangladesh; **not less than 90%** of employees employed in Bangladesh;
sole purpose is gratuity on retirement, after a specified age, on incapacity, on termination after a
minimum service period, or to widows, children or dependants on death; **the employer must be a
contributor**; all benefits payable only in Bangladesh. Para 2: application in writing by a trustee to
the Commissioner of Taxes with the gratuity deed and rules — ACE Advisory reports approval may be
granted **within 180 days** of receipt **[SUMMARY]**. Para 4: an employer's contribution to an approved
fund **is deducted** in computing income, profits and gains. Para 5: if a contribution with interest is
repaid to the employer, that refund is **income of the employer** in the year of receipt.

**Labour Act entitlement — s.2(10)**, verbatim from http://bdlaws.minlaw.gov.bd/act-952/section-29070.html :

> "গ্রাচুইটি" means, for each **completed year of service, or service in excess of six months**, wages
> of **not less than 30 days** at the worker's **last drawn wage rate**; or, where the service
> **exceeds 10 years**, **45 days'** wages at the last drawn wage rate — payable on termination of
> service.

**The Act does not require a *funded* scheme, but the entitlement itself is compulsory**, because it
appears as a floor in every separation provision:

| Provision | Entitlement |
|---|---|
| **s.2(10)** definition | ≥30 days' wages per completed year (or service exceeding six months); **45 days' per year where service exceeds 10 years** |
| **s.20(2)(c)** retrenchment | ≥1 year's service: 30 days' wages per year, **or gratuity, whichever is higher** (plus 15 days extra if retrenched under s.16(7)) |
| **s.22(2)** discharge for incapacity | 30 days per year, or gratuity, whichever is higher |
| **s.23(3)** dismissal for misconduct | **15 days' wages per year**; nil for theft, fraud, riot etc. (s.23(4)) |
| **s.26(4)** termination by the employer | 30 days per year, or gratuity, whichever is higher; notice 120 / 60 / 30 / 14 days |
| **s.27(4) resignation — REWRITTEN by the Labour (Amendment) Act 2026 §13** | **≤3 years: 7 days' wages per year; >3 and <10 years: 15 days per year; ≥10 years: 30 days per year, or gratuity, whichever is higher.** The old rule gave nothing below 5 years |
| **s.30** | **All dues are payable within 30 WORKING DAYS of cessation of employment** |

**Retirement — s.28:** a worker retires normally on completing **60 years** of age (raised from 57 by
the Labour (Amendment) Act 2010 §2). The date of birth in the service book is proof of age. A retired
worker may be re-engaged on contract.

**Note on the amending instrument.** The 2026 labour changes were first made by the **Bangladesh
Labour (Amendment) Ordinance 2025 (Ordinance 65 of 2025, 17 November 2025)**, which was then repealed
and re-enacted as the **Bangladesh Labour (Amendment) Act 2026 (Act 43 of 2026)**. Cite the Act.

---

## 8. Workers' Profit Participation Fund — WPPF / শ্রমিক অংশগ্রহণ তহবিল

**Labour Act 2006, Chapter XV. All figures below were read from the primary text on bdlaws.
[PRIMARY]**

| Item | Rule | Provision |
|---|---|---|
| **Which companies are covered** | A company or establishment meeting **either** (a) **paid-up capital of not less than Tk 10,000,000** on the last day of an accounting year, **or** (b) **fixed assets of not less than Tk 20,000,000** on that day | **s.232(1)** — http://bdlaws.minlaw.gov.bd/act-952/section-26285.html |
| Extension | Government may apply the Chapter to other companies by gazette notification | s.232(2) |
| Export-oriented / FX sectors | Government shall make rules for a sector-wise **central fund** constituted by buyers and owners | s.232(3) |
| **Establishing the funds** | Within **ONE MONTH** of the Chapter becoming applicable, establish a **Workers' Participation Fund** and a **Workers' Welfare Fund** | **s.234(1)(a)** |
| **Contribution and the split** | Within **nine months of the end of every year**, the owner pays **5% of the previous year's net profit** in the ratio **80 : 10 : 10** to the Participation Fund, the Welfare Fund, and the **Workers Welfare Foundation Fund** under s.14 of the Bangladesh Workers Welfare Foundation Act 2006 | **s.234(1)(b)** — http://bdlaws.minlaw.gov.bd/act-952/section-26287.html |
| Transitional proviso | An owner who was depositing 1% of net profit to the Welfare Fund immediately before this provision took effect — the Trustee Board deposits **50%** of that amount to the Workers Welfare Foundation Fund | s.234(1)(b) proviso |
| Deemed allocation date | Deemed allocated on the **first day of the year immediately following** the year for which it is paid | s.234(2) |
| **Who is a beneficiary** | Anyone employed **≥9 months**, of any rank — **excluding owners, partners and board members**. "Profits" are computed per Companies Act s.119 | **s.233** |
| Trustees | 2 worker nominees + 2 management nominees; the Labour (Amendment) Act 2026 §54 allows the Participation Committee to nominate | **s.235** |
| Share in a year's distribution | The worker must have completed **6 months** in that accounting year | **s.241(2)** |
| Use of the fund | **Two-thirds distributed in cash equally each year; one-third invested** | **s.242** |

> ⚠️ The Bangla of s.234(1)(b) literally reads **"অন্যূন নয় মাসের মধ্যে"** — "within *not less than*
> nine months" — a known drafting oddity. Practitioners uniformly read it as **within nine months of
> the year end** (so 31 March for a 30 June year end). Flag the oddity if a user is arguing about it.

**Penalty — s.236**, substituted by the Labour (Amendment) Act 2013 §67
(http://bdlaws.minlaw.gov.bd/act-952/section-26289.html):

| Sub-s. | Provision |
|---|---|
| 236(1) | On failure to comply with s.234, the **Government may order compliance** within a specified time |
| **236(2)** | On failure to comply with that order, the Government may impose on **every director, manager or officer directly or indirectly responsible for management** (or the trustee board's chairman, members or persons in charge) a fine **not exceeding Tk 100,000**, plus **Tk 5,000 for each day** of continuing failure after the first date, payable within 30 days. **A repeat violation attracts DOUBLE the fine** |
| 236(3) | Unpaid s.234 amounts and fines are **government demands**, recoverable under the Public Demands Recovery Act 1913 |
| 236(4)–(5) | Review application to Government within 30 days; Government decides within 45 days; that order is **final** |

An identical **Tk 100,000 plus Tk 5,000 per day** penalty sits on the trustee board for failing to
remit the 10% Foundation share within 30 days — **Bangladesh Workers Welfare Foundation Act 2006 (Act
25 of 2006), s.14A**. Note that the s.236(2) fine falls **personally on directors and managers**, not
on the company.

### Tax treatment of WPPF — two points practitioners routinely get wrong

| Party | Treatment | Provision |
|---|---|---|
| **The company — deductibility** | An amount **not exceeding 5% of disclosed net business profits** payable to the Workers Participation Fund and Welfare Fund under Labour Act s.234(1)(b), and to the Labour Welfare Foundation Fund under s.14 of the Foundation Act 2006, is an **allowable deduction** | **ITA 2023 s.49(2)(u)** |
| **Withholding — WHO deducts, and WHEN** | **The FUNDS deduct 10% when they pay a beneficiary** — *not* the employer when it pays into the funds. **s.88 was substituted by Act 89 of 2026 §62:** when the Participation Fund, Welfare Fund and Workers Welfare Foundation Fund under Labour Act s.234 pay money to a beneficiary, the person responsible shall deduct **10%** at the time of payment or credit, notwithstanding anything in any other law in force in Bangladesh | **s.88** as substituted |
| **The receiving worker** | **FULLY TAXABLE — there is NO exemption limit** | — |

> ⚠️ **The pre-2026 s.88 in NBR's English text placed the 10% on the employer's payment INTO the
> funds. That version is superseded.** Charts and payroll systems still deducting at the employer end
> are deducting in the wrong place.

> ⚠️ **The old ITO 1984 exemption for WPPF receipts (Tk 50,000) was NOT carried into the Income Tax Act
> 2023.** The whole of Sixth Schedule Part 1 in NBR's authentic English text was searched and **no
> WPPF exemption paragraph exists**; ACE Advisory's 2026-27 taxability table independently confirms
> "WPPF: fully taxable". Note also that the paragraph (22) which Act 89 of 2026 §135(ক)(৫) *deleted*
> from Sixth Schedule Part 1 was an expired handicrafts-export exemption, **not** a WPPF exemption —
> an expired provision being tidied up, not a withdrawal of relief.

> ⚠️ **An unrepealed conflict, and a real one.** Labour Act **s.245** (the funds' income is exempt) and
> **s.246** (sums paid to workers from the funds are exempt from income tax) **remain on the statute
> book**. ITA s.88's "notwithstanding any law in force" clause overrides them in practice, but the
> Labour Act provisions have not been repealed. **Get a formal opinion before relying on either
> side.**

> **[UNCONFIRMED] — the effective date of the s.88 rewrite.** Act 89 of 2026 is dated 10 April 2026
> and states it is "in force immediately", but no commencement clause specific to §62 was found.
> **Whether the rewritten s.88 reaches WPPF payouts made between 1 July 2025 and 10 April 2026 is
> unconfirmed.** For payouts in that window, say so rather than assuming either answer.

**Non-compliance is the norm, not the exception.** An ICAB technical presentation by Snehasish Barua
FCA (Partner, Snehasish Mahmud & Co) reviewing listed companies found all 3 banks, all 3 insurers, all
4 financial institutions, 2 of 3 cement companies, 2 of 4 fuel and power companies and 1 of 3
pharmaceutical companies **non-compliant** with WPPF —
https://www.icab.org.bd/icabadmin/uploads/ckeditor/175029-05-2016Md.%20Aminul%20Islam.pdf . Two known
ambiguities practitioners flag: whether the 9-month beneficiary test runs to year end or to the actual
distribution date (s.233), and the contradiction between s.240(1), which implies the accrued balance is
available to the company, and Rule 236(3), which bars the company from taking loans or advances from
the fund.

---

## 9. Superannuation, pension funds and the Universal Pension Scheme

**Approved superannuation or pension fund — Second Schedule Part 1.** Conditions for approval (para 1);
procedure — application by trustees to the Commissioner (para 2); withdrawal of approval (para 3);
income and subscriptions (para 4); trustees' liabilities on cessation (para 5); particulars to be
furnished (para 6). **Employer contributions are deductible and are excluded from "perquisite"**
(s.32 Explanation (c)(ii)), and the **annual contribution to an approved superannuation fund qualifies
for the investment rebate with no limit**. **Any pension due to or received from the Government or an
approved Pension Fund is exempt** — 6th Sch Pt 1 para 4.

**Universal Pension Scheme — tax treatment**, from the bdlaws text of Act 89 of 2026 §135(ক)(১০) and
(১১). **[PRIMARY]**

| Provision | Effect |
|---|---|
| **6th Sch Pt 1 para (34)**, substituted — *"জাতীয় পেনশন কর্তৃপক্ষের সর্বজনীন পেনশন স্কিম হইতে প্রাপ্ত সুবিধাভোগীর কোনো আয়"* | **Any income of a beneficiary from the National Pension Authority's Universal Pension Scheme is exempt** — broadened from the narrower original, which covered only income arising *as pension* |
| **6th Sch Pt 1 para (34ক)**, new — *"জাতীয় পেনশন কর্তৃপক্ষের আয়"* | **The income of the National Pension Authority itself is exempt** |
| Contributions | **Subscription to the Universal Pension Scheme is an eligible investment for the tax rebate, with NO limit** |

For whether an employer must participate, see §7.2 — the answer for 2026 is no, except as an
alternative once the mandatory-PF trigger is met.

---

## 10. Payroll mistakes that actually cost Bangladeshi SMEs money

Each is attributed; none is invented. Fuller treatment and citations in `penalties.md`.

| # | Mistake | What it costs | Source |
|---|---|---|---|
| 1 | Salary TDS deducted at a **flat slab rate** instead of the **average rate on estimated annual income** (s.86) | Under- or over-withholding all year; the employer remains liable for the shortfall, plus 2%/month and the s.56 150% charge | ACE Advisory |
| 2 | Perquisites not tracked against the **s.55(d) annual cap** | The excess is disallowed in the company's assessment | ACE Advisory |
| 3 | Employer-provided **car and accommodation not valued** under s.33 and not added to taxable salary | Under-withholding, with employer liability | ACE Advisory; PwC WWTS |
| 4 | **PSR not collected from managerial staff and vendors before payment** | 50% higher withholding under s.142(1) **and** s.55(o) expense disallowance | PwC WWTS; The Business Standard |
| 5 | **Late TDS deposit.** Bangladesh Bank issued a circular on 10 August 2026 after finding banks routinely missing the deposit windows | 2% per month up to 24 months (s.143) | https://www.tbsnews.net/economy/banking/bb-warns-banks-over-withholding-tax-deduction-delayed-deposit-1511586 |
| 6 | Missing the **s.177 quarterly return** or the **s.145 certificate** | Higher of 10% of last assessed tax or Tk 5,000 plus Tk 1,000/month; and Tk 5,000 plus Tk 1,000/month | ACE Advisory |
| 7 | Operating an **unrecognised PF** or an **unapproved gratuity fund** | Employer contributions not allowable (s.55(u)); no investment rebate for employees — and under the Finance Act 2026 recognition is now a precondition for the rebate | ACE Advisory; PwC p.6 |
| 8 | **WPPF not established, or paid late** | Fine up to Tk 100,000 plus Tk 5,000/day, **doubled on repeat**, imposed **personally on directors and managers** (Labour Act s.236) | ICAB / Snehasish Barua FCA (SMAC) |
| 9 | **Netting the employer's PF contribution against the employee's** in the books | The employer's contribution is taxable salary in the employee's hands (s.32) and a deductible expense for the company (2nd Sch Pt 3 para 5(1)) — netting destroys both | 2nd Sch Pt 3; s.32 |
| 10 | Paying salary **in cash rather than by bank transfer** | s.55(k) disallows the whole payment in the company's assessment, whatever the withholding position | ITA 2023 s.55(k) |

---

## Still open — do not let these harden into answers

1. **The Sixth Schedule paragraph number** for the salary exemption — the research contradicts itself
   between §5.2 (paragraph 27, from the amending text) and §C7 (not identified). §2 above.
2. **The government-employee SRO number** — 225-Law/Income Tax-7/2023 is second-hand; the substance is
   corroborated, the citation is not. §3.
3. **The annual salary statement** — one weak source, contradicted elsewhere. **Never diarise it.** §6.
4. **The fund-level tax rate** on PF / gratuity / WPPF investment income — two conflicting secondary
   figures, no primary charging section. **Do not pick one.** §7.1.
5. **The effective date of the s.88 WPPF withholding rewrite** for payouts between 1 July 2025 and
   10 April 2026. §8.
6. **Whether the two s.142 uplifts stack, and whether any ceiling exists.** §5.
7. **The Labour Act ss.245–246 vs ITA s.88 conflict** — unrepealed provisions on both sides. §8.
8. **A second reading of the Second Schedule** (PF, gratuity, superannuation) was never obtained. §7.1.
9. **Review by a Bangladeshi ITP or CA** has not happened for this file.

**Sources named in this file** — Income Tax Act 2023: http://bdlaws.minlaw.gov.bd/act-details-1429.html ·
Act 89 of 2026 amending text: http://bdlaws.minlaw.gov.bd/act-1718/chapter-details-2808.html ·
NBR authentic English text of the ITA 2023 (stale in places, see §2):
https://nbr.gov.bd/uploads/acts/Income_tax_act_2023.pdf ·
Finance Act 2026 (Act 96 of 2026) gazette: https://nbr.gov.bd/uploads/acts/Finance_Act_2026.pdf ·
উৎসে কর বিধিমালা, ২০২৬ — SRO 273-আইন/আয়কর-৫/২০২৬: https://nbr.gov.bd/uploads/rules/With_holding_2026.pdf ·
আয়কর পরিপত্র ২০২৬-২০২৭: https://nbr.gov.bd/uploads/paripatra/আয়কর_পরিপত্র_২০২৬-২০২৭.pdf ·
Bangladesh Labour Act 2006: http://bdlaws.minlaw.gov.bd/act-952.html

---
Maintained by Moshiur Rahman (@bemoshiur) · Ticon Sys — https://ticonsys.com · MIT
