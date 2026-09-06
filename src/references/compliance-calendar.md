# Compliance calendar — সম্মতি পঞ্জিকা

**Current as of:** 2026-09-06
**Assessment year:** করবর্ষ / assessment year **2026-27** (income year 1 July 2025 – 30 June 2026).
Machine-readable dates live in `data/rates-AY2026-27.toml` under `[deadlines]`; this file is the
prose that explains them.
**Sources:** the consolidated Bangla statutes on **bdlaws.minlaw.gov.bd**, read section by section
on 2026-09-06 — আয়কর আইন, ২০২৩ / Income Tax Act 2023 (act-1429), মূল্য সংযোজন কর ও সম্পূরক শুল্ক
আইন, ২০১২ / VAT and SD Act 2012 (act-1106), কোম্পানী আইন, ১৯৯৪ / Companies Act 1994 (act-788) —
plus **উৎসে কর বিধিমালা, ২০২৬ / TDS Rules 2026 (S.R.O. 273-Ain/Aykar-5/2026)** and NBR's
**আয়কর পরিপত্র ২০২৬-২০২৭ / Income Tax Paripatra 2026-27**. Every date below carries its section.
**Status:** POPULATED. Dates read from primary text unless the line itself says otherwise.

> **Not professional advice.** Verify with a licensed **আয়কর আইনজীবী / Income Tax Practitioner (ITP)**
> or **চার্টার্ড অ্যাকাউন্ট্যান্ট / Chartered Accountant (CA)** before you file or diarise anything here.

## How to read this file

- **Dates appear in this file** — a calendar without dates is useless. Each is also a node in
  `data/rates-AY2026-27.toml` under `[deadlines]`, which is the machine-readable source of truth.
  Penalty amounts are **not** repeated here; they live in `penalties.md`.
- **⚠️ INFERRED** on a line means the date is a reasonable reading, not an enacted date. Confirm it
  before you rely on it. There is exactly one such item in the core calendar: the **VAT quarter
  boundaries**.
- **⚠️ UNRESOLVED** on a line means two readings of the law are in circulation and this package
  cannot choose between them from its permitted sources. It states both and names the one it
  follows. There is exactly one such item: the **individual "specified date" (30 November)**.
- **Not listed = not confirmed.** Several obligations that circulate widely are deliberately absent.
  §10 says which, and why.

## Four things almost every 2026-27 calendar gets wrong — and where this package is unsure

1. ⚠️ **UNRESOLVED — the individual "specified date". It is not 31 December, and it is probably
   30 November.** This package's research document records ITA 2023 **s.2(80A)** —
   রিটার্ন দাখিলের নির্দিষ্ট তারিখ / *specified date for filing the return*, inserted by
   **Act 89 of 2026 §29(ট)** — as **in force**, setting **30 November** following the end of the
   income year for a **স্বাভাবিক ব্যক্তি / natural person** and a **হিন্দু অবিভক্ত পরিবার / HUF**. For
   AY 2026-27 that is **30 November 2026**. The research warns in terms: *do not treat 31 December
   as the statutory deadline.*
   **The contrary reading, and why it is not stated here as fact.** A content pass in this
   repository previously asserted that the same clause, numbered **s.2(80ka)**, was *deleted* by the
   Finance Act 2026 with effect from 1 July 2026, so that **no** individual due date is in force.
   That assertion rested on bdlaws amendment footnotes that appear in **no source this package is
   permitted to rely on** — not in the research, not in NBR's Paripatra 2026-27. It has been
   **retracted**. The research itself could not settle the surrounding drafting (§C10 —
   *"I could not verify the drafting"*).
   **What to do:** diarise **30 November** and have an **ITP or CA confirm it before the filing
   season**. TakaBooks will not tell you that no individual due date exists: if that were wrong, you
   would miss a mandatory statutory date. The **s.170 filing-window ladder in §1 is a separate
   question and is not in doubt** — the incentive, neutral and additional-tax bands stand either way.
   *Both readings are recorded in* `data/rates-AY2026-27.toml` *at*
   `deadlines.income_tax_return_specified_date_status`, *which is* `verified = false`.
2. **The VAT return is quarterly, not monthly**, from 1 July 2026 — s.64 wholly substituted by
   Finance Act 2026 s.11.
3. **31 December is not a deadline either.** It is the last day of the band in which an individual
   pays neither incentive nor additional tax. Filing on 2 January is not "late" against a due date;
   it moves the taxpayer into the 2% / Tk 3,000 band.
4. **Any TDS chart citing S.R.O. 210 of 8 June 2026 is void.** SRO 210 was expressly repealed by
   Rule 14 of **S.R.O. 273-Ain/Aykar-5/2026** (gazetted 5 July 2026, deemed effective 1 July 2026).
   Both SROs carry the identical title উৎসে কর বিধিমালা, ২০২৬.

---

## 1. The individual income tax return is a window, not a date

**ITA 2023 s.170(1)**, wholly substituted by the **Finance Act 2026 s.97**, effective 1 July 2026 —
http://bdlaws.minlaw.gov.bd/act-1429/section-52000.html

A **স্বাভাবিক ব্যক্তি / natural person** and a **হিন্দু অবিভক্ত পরিবার / Hindu Undivided Family** may
file anywhere in the assessment year following the end of the income year. The date filed decides
the consequence, not whether the return is accepted:

| Filed between | Consequence | AY 2026-27 dates |
|---|---|---|
| 1 July – 30 September | **Incentive**: 5% of the tax payable under s.173(2) **or Tk 25,000, whichever is LESS** | 1 Jul 2026 – 30 Sep 2026 |
| 1 October – 31 December | Neither incentive nor additional tax | 1 Oct 2026 – 31 Dec 2026 |
| 1 January – 31 March | **Additional tax**: 2% of tax payable **or Tk 3,000, whichever is HIGHER** | 1 Jan 2027 – 31 Mar 2027 |
| 1 April – 30 June | **Additional tax**: 5% **or Tk 5,000, whichever is HIGHER** | 1 Apr 2027 – 30 Jun 2027 |

Two special clauses in the same sub-section:

- **s.170(1)(kha)** — a natural person who has **never filed before** may file by the **30 June**
  following the end of the income year, paying tax at the rate applicable for the assessment year.
  The clause is drafted as a permission and states no additional tax of its own; whether the ladder
  above also bites on such a filer is not resolved on the face of the section. Ask an ITP.
- **s.170(1)(ga)** — a natural person **residing abroad** files within the **90th day from the day of
  return to Bangladesh**, if abroad on leave for higher education, on deputation or lien, or holding
  a valid visa and work permit for the purpose of earning.

**s.170(3):** where any of those days is a **সরকারি ছুটির দিন / government holiday**, the obligation
falls on the immediately following working day.

⚠️ **The extension power is unresolved.** The research records that the **NBR's** power to extend
the return filing date by one month has been **repealed**, while **s.2(80A)(e)** — inserted by the
same Act 89 of 2026 — gives the **কর কমিশনার / Commissioner of Taxes** power to extend an
individual's specified date by up to **90 days** on written application made before that date for
unavoidable reasons. Whether the Finance Act 2026 removed s.2(80A)(e) is **unconfirmed** (research
§F5); the two powers are different office-holders and different periods, so they may simply
coexist. **Do not plan on an extension without asking an ITP or CA first.** Filing after the
assessment year has ended is a **বিলম্ব রিটার্ন / delayed return** under **s.174** — see
`penalties.md`.

**As at 6 September 2026 the 5% early-filing incentive window for AY 2026-27 is open and closes
30 September 2026.**

## 2. The company income tax return

**ITA 2023 s.170(2)** — same section, same substitution.

> **Deadline = the 15th day of the ninth month following the end of the income year; or, where that
> 15th day falls before 15 September, the 15 September following the end of the income year.**

Count from the month *after* the income year ends: for a 30 June year end, July is month 1 and March
is month 9.

| Income year ends | Return due | Early-filing incentive window closes |
|---|---|---|
| 30 June 2026 (most companies) | **15 March 2027** | **15 January 2027** — 2 months before the deadline |
| 31 December 2025 (banks, insurers, financial institutions) | **15 September 2026** | 15 July 2026 (passed) |

| Filed | Consequence |
|---|---|
| 2 months before the deadline | **Incentive**: 5% of tax payable under s.173(2) **or Tk 25,000, whichever is LESS** |
| In the final 2 months, up to the deadline | Neither |
| After the deadline, still inside the assessment year | **Additional tax**: 2% **or Tk 25,000, whichever is HIGHER** |

The Tk 25,000 entity minimum against Tk 3,000 for individuals is surprising, and it is exactly what
the two sub-sections say. Both were read from the primary Bangla text.

The incentive window is fixed by reference to the deadline, so it **moves with a non-June year end** —
recompute it, do not memorise 15 January.

---

## 3. Every month — উৎসে কর কর্তন / TDS deposit

**Rule 9, উৎসে কর বিধিমালা, ২০২৬ / TDS Rules 2026 (S.R.O. 273-Ain/Aykar-5/2026)** —
https://nbr.gov.bd/uploads/rules/With_holding_2026.pdf · cross-read in Appendix-1 of
https://nbr.gov.bd/uploads/paripatra/আয়কর_পরিপত্র_২০২৬-২০২৭.pdf

All deposits go by **এ-চালান / A-Challan**.

| Deduction or collection made | Deposit by |
|---|---|
| Any day in **July to May** | Within **2 weeks from the end of that month** (a July deduction by 14 August) |
| **1 – 20 June** | Within **7 days** following the day of deduction or collection |
| **Any other day of June** | **The next day** |
| **The last working day of June** | **The same day** |

> The rule says the **last *working* day of June**, not "30 June". Published summaries that render it
> as 30 June are wrong whenever 30 June falls on a weekend or public holiday. Plan the final June
> payment run around this — there is no grace at all.

Late deposit is charged at 2% per month under s.143 — see `penalties.md`.

---

## 4. Month by month — a private limited company, income year 1 July – 30 June, VAT-registered

| Month | Obligation | Due | Authority |
|---|---|---|---|
| **July** | VAT / turnover-tax return, Apr–Jun quarter ⚠️ INFERRED quarter | **15 July** (20 July for government, semi-government and autonomous bodies, banks, insurers and nil filers) | VAT Act s.64(1) |
| | **Withholding tax return, Apr–Jun quarter** | **25 July** | ITA s.177(3) |
| | Individual filing window opens — 5% incentive, capped at Tk 25,000 | 1 July – 30 Sept | ITA s.170(1) |
| | TDS deposit for June deductions | per the June rules in §3 | TDS Rules 2026 r.9 |
| **August** | TDS deposit for July | **14 August** | TDS Rules 2026 r.9 |
| **September** | **অগ্রিম কর / AIT instalment 1 — 25%** | **15 September** | ITA s.155(2) |
| | Company return — banks, insurers, financial institutions (Jan–Dec income year) | **15 September** | ITA s.170(2) |
| | Last day of the individual 5% early-filing incentive window | **30 September** | ITA s.170(1) |
| | TDS deposit for August | **14 September** | TDS Rules 2026 r.9 |
| **October** | VAT return, Jul–Sep quarter ⚠️ INFERRED quarter | **15 October** (20 Oct for the listed bodies) | VAT Act s.64(1) |
| | **Withholding tax return, Jul–Sep quarter** | **25 October** | ITA s.177(3) |
| | TDS deposit for September | **14 October** | TDS Rules 2026 r.9 |
| **November** | ⭐ **Individual / HUF "specified date for filing return"** ⚠️ UNRESOLVED — see the note above the calendar | **30 November** | ITA s.2(80A)(a) |
| | TDS deposit for October | **14 November** | TDS Rules 2026 r.9 |
| **December** | **AIT instalment 2 — 25%** | **15 December** | ITA s.155(2) |
| | End of the individual neutral band — additional tax from 1 January | **31 December** | ITA s.170(1) |
| | **VAT legacy-settlement window closes** (one-off, see §7) | **31 December 2026** | VAT Act s.137A |
| | TDS deposit for November | **14 December** | TDS Rules 2026 r.9 |
| **January** | VAT return, Oct–Dec quarter ⚠️ INFERRED quarter | **15 January** | VAT Act s.64(1) |
| | **Withholding tax return, Oct–Dec quarter** | **25 January** | ITA s.177(3) |
| | Company early-filing incentive window closes (30 June year end) | **15 January** | ITA s.170(2) |
| | Individual filing from 1 Jan attracts additional tax — 2%, minimum Tk 3,000 | 1 Jan – 31 Mar | ITA s.170(1) |
| | TDS deposit for December | **14 January** | TDS Rules 2026 r.9 |
| **February** | TDS deposit for January | **14 February** | TDS Rules 2026 r.9 |
| **March** | **AIT instalment 3 — 25%** | **15 March** | ITA s.155(2) |
| | ⭐ **Company income tax return** (30 June year end) | **15 March** | ITA s.170(2) |
| | End of the individual 2% band | **31 March** | ITA s.170(1) |
| | TDS deposit for February | **14 March** | TDS Rules 2026 r.9 |
| **April** | VAT return, Jan–Mar quarter ⚠️ INFERRED quarter | **15 April** | VAT Act s.64(1) |
| | **Withholding tax return, Jan–Mar quarter** | **25 April** | ITA s.177(3) |
| | Individual filing from 1 Apr attracts additional tax — 5%, minimum Tk 5,000 | 1 Apr – 30 Jun | ITA s.170(1) |
| | TDS deposit for March | **14 April** | TDS Rules 2026 r.9 |
| **May** | TDS deposit for April | **14 May** | TDS Rules 2026 r.9 |
| **June** | **AIT instalment 4 — 25%** | **15 June** | ITA s.155(2) |
| | First-time individual filers' outer date | **30 June** | ITA s.170(1)(kha) |
| | End of the individual 5% band and of the assessment year | **30 June** | ITA s.170(1) |
| | Special June TDS deposit rules apply | see §3 | TDS Rules 2026 r.9 |

### The withholding tax return — quarters are enacted, not inferred

**ITA s.177(3)**, substituted by Act 89 of 2026 s.102(kha) —
http://bdlaws.minlaw.gov.bd/act-1429/section-52007.html — names the months in the statute itself:

| Due | Covers |
|---|---|
| **25 October** | July, August, September |
| **25 January** | October, November, December |
| **25 April** | January, February, March |
| **25 July** | April, May, June |

If the date is a **weekly or government holiday**, the next working day. **s.177 contains no power to
extend these dates** — the next-working-day shift is the only relief in the section. The old
half-yearly return, s.177(4), was deleted by the Finance Act 2024.

Who must file (s.177(1), widened by Finance Act 2026 s.105 from 1 July 2026): any company except
government ministries, divisions, directorates and MPO educational institutions; firms; associations
of persons; private hospitals, clinics and diagnostic centres; public-private partnerships;
e-commerce platforms and online marketplaces with turnover above Tk 1 crore; hotels, resorts, motels,
restaurants, convention and community centres and transport agencies above Tk 1 crore; non-farmer
tobacco-product manufacturers; and **any natural person with business turnover above Tk 10 crore**.

An income tax return is treated as **incomplete** without the acknowledgement copy of the withholding
return.

### ⚠️ The VAT return — the rule is enacted, the quarter boundaries are INFERRED

**VAT Act 2012 s.64**, wholly substituted by **Finance Act 2026 s.11**, effective 1 July 2026 —
http://bdlaws.minlaw.gov.bd/act-1106/section-42360.html

**Enacted, read from primary text:**

- A return is due **within 15 days of the end of every three tax periods**. A **কর মেয়াদ / tax
  period** is one Gregorian calendar month (s.2(30)).
- If the 15th day is a government holiday, the next working day.
- **20 days** instead of 15 for any government, semi-government or autonomous body, bank, insurance
  company, and any person or entity filing a **nil return**.
- **Monthly filing survives only as a voluntary election** (s.64(2)): a person who wishes to may file
  for a single tax period on **any day of the following tax period** — i.e. by the last day of the
  next month. That is looser than the quarterly rule, which is why a business in a steady refund
  position may still want it. Never quote "the 15th of the following month": that rule is gone.
- The Board may extend the deadline by order in the public interest, **without interest or penalty**
  (s.64(3)). Separately the Commissioner may permit late filing on application, but that permission
  **cannot move the actual tax payment date by more than one month and does not alter the liability
  to interest** (s.65 — http://bdlaws.minlaw.gov.bd/act-1106/section-42361.html).
- Turnover tax must be paid **before** the return is filed (s.63(2)).
- Supplementary duty information goes inside the same return (s.64(4)).

**⚠️ INFERRED — confirm before diarising:** s.64(1) says "every three tax periods" and stops there.
It does not say when the cycle starts, and no professional summary states it either. This package
assumes **Q1 = July–September, due 15 October**, then October–December, January–March and
April–June. The assumption rests on the 1 July 2026 commencement and the previous turnover-tax
convention. **Confirm against an NBR General Order, or against the quarter shown on the business's
own BIN profile, before entering these dates in a calendar** — ask the Divisional VAT office. A
missed VAT return costs Tk 2,000 and can get the BIN temporarily locked.

Forms: **মূসক ৯.১ / Mushak 9.1** (input tax credit claimants), **মূসক ৯.১.১ / Mushak 9.1.1** (no
credit claimed), **মূসক ৯.২ / Mushak 9.2** (turnover tax).

---

## 5. অগ্রিম কর / Advance income tax

**ITA 2023 s.155(2)** — http://bdlaws.minlaw.gov.bd/act-1429/section-51985.html

Four **equal instalments of 25% each**, on **15 September, 15 December, 15 March and 15 June** of the
financial year. A date falling on a government holiday moves to the next working day (s.155(3)). A
missed instalment is added to the next one, without prejudice to any other liability (s.155(4)).
Where the taxpayer estimates the instalments will be less **or more** than the s.155(1) computation,
he files an estimate with the **উপ কর কমিশনার / Deputy Commissioner of Taxes** and pays accordingly
(s.155(5); the words "or more" were added by Finance Act 2026 s.88(kha)).

The four dates are original ITA 2023 text and were not changed by the Finance Act 2026.

**Who is liable** is a separate question, governed by **s.154** (existing taxpayers) and **s.156**
(new taxpayers). The Finance Act 2026 raised the threshold, and the exact wording — last assessed
*income* above Tk 10 lakh, or *estimated tax liability* — is reported differently by PwC and KPMG and
was **not settled from primary text here**. Read s.154 before telling a taxpayer they are liable.
Interest on a shortfall sits in **s.162** and is covered in `penalties.md`.

---

## 6. RJSC / কোম্পানী আইন, ১৯৯৪ — Companies Act 1994

Read from the Bangla primary text on bdlaws (act-788). Portal: **https://app.roc.gov.bd**.

| Obligation | Deadline | Section |
|---|---|---|
| **বার্ষিক সাধারণ সভা / AGM** | One in every English calendar year, and **not more than 15 months** after the previous AGM. First AGM within **18 months** of incorporation. | **s.81(1)** — [link](http://bdlaws.minlaw.gov.bd/act-788/section-32905.html) |
| AGM extension | On application to the Registrar **within 30 days** of the period expiring, the Registrar may extend a **subsequent** AGM (never the first) by not more than **90 days**, or to **31 December** of the calendar year it relates to — whichever comes first. | s.81, 2nd proviso |
| Age of the accounts laid | Made up to a date within **9 months** before the meeting; **12 months** where the company has business or interests outside Bangladesh; extendable by the Registrar by up to **3 months** on application made before expiry. | **s.183(2)** — [link](http://bdlaws.minlaw.gov.bd/act-788/section-33572.html) |
| Financial year length | Not more than **15 months**; up to **18 months** with the Registrar's special permission. | s.183(4) |
| Accounts open at the registered office for members | At least **14 days** before the general meeting | s.183(6) |
| Copy sent free to every member, debenture holder and debenture trustee | Not less than **14 days** before the meeting — but if sent later and no member entitled to vote objects at the meeting, the notice is **deemed duly sent** (s.191(1)(ga)) | **s.191(1)** — [link](http://bdlaws.minlaw.gov.bd/act-788/section-33580.html) |
| **Annual return — তফসিল ১০ / Schedule X** (list of members, summary of share capital) | Completed **within 21 days** after the first or only general meeting of the year, and filed with the Registrar **forthwith, within that same period**. First return within **18 months** of incorporation. | **s.36(1), (3)** — [link](http://bdlaws.minlaw.gov.bd/act-788/section-32860.html) |
| **Audited balance sheet and profit and loss account**, three copies | **Within 30 days** from the date they are laid before the AGM — or, where no AGM was held that year, within 30 days from the last date on which it should have been held | **s.190(1)** — [link](http://bdlaws.minlaw.gov.bd/act-788/section-33579.html) |
| Change in directors, manager or managing agent — **Form XII** | **14 days** | **s.115(2)** — [link](http://bdlaws.minlaw.gov.bd/act-788/section-32939.html) |
| Registered office and any change — **Form VI** | **28 days** | **s.77(2)** — [link](http://bdlaws.minlaw.gov.bd/act-788/section-32901.html) |
| **এক ব্যক্তি কোম্পানী / One Person Company** financial statements to the Registrar | **180 days** from the end of the financial year | **s.392(jha)** — [link](http://bdlaws.minlaw.gov.bd/act-788/section-50109.html) |

Notes that matter in practice:

- **Skipping the AGM does not postpone the s.190 filing.** The clock starts from the date the AGM was
  due. Where the balance sheet was not adopted, or no AGM was held, a statement of that fact and the
  reasons must be annexed to every copy filed (s.190(2)).
- **Form XII is 14 days, not 15.** RJSC's own Bangla returns page says ১৫ দিন; the statute says
  **চৌদ্দ দিন** and RJSC's English FAQ agrees. Use 14.
- Three limits bind the AGM at once — the calendar year, the 15-month gap, and the 9-month staleness
  rule on the accounts laid. A company can satisfy one and still breach another.
- Signature on the Schedule X filing: two directors **including the managing director** (or one
  director where there is no MD), plus the managing agent, manager or secretary, with their
  certificate that the facts are correctly stated. A private company also files the s.36(4)
  certificate that no public invitation to subscribe has been issued since the last return.
- **RJSC credentials, from 6 August 2026 — reported, circular text not opened here:** an RJSC
  circular (memo 26.06.0000.001.31.001.21, published 13 August 2026) is reported to require the head
  of the entity or a duly authorised person to attend the Registrar's office **in person**, with
  board minutes and photo ID, to collect the e-services admin user ID and password — credentials can
  no longer be obtained remotely or through an agent. **Confirm with the RJSC office before planning
  around it**, but build the lead time into the timetable ahead of an AGM season if the company has
  never collected its credentials.

---

## 7. One-off window that closes inside AY 2026-27

**VAT legacy settlement — closes 31 December 2026.** New **VAT Act s.137A** (১৩৭ক) opens a special
**interest-waiver scheme for legacy VAT demands** — dues under the repealed **VAT Act 1991** and
specified periods under the **2012 Act** — for a **six-month window from 1 July 2026**. Secondary
reporting gives the hard close as **31 December 2026**.

The waiver is of **interest**; the tax and any penalty are a separate question, and the mechanics of
the scheme (which periods qualify, what has to be paid and by when) were not read from the section
itself. If a client has an old VAT demand, **this is the last quarter to use it — take it to an ITP
or CA now.** `vat-mushak.md` §9 states the same scheme in the same terms.

---

## 8. Non-standard income years, and how the dates move

- **Banks, insurance companies and financial institutions** run a **1 January – 31 December** income
  year. Their s.170(2) return date is **15 September** following the year end, and their early-filing
  incentive window closes two months earlier, on 15 July.
- For any other year end, recompute **both** the s.170(2) deadline (15th day of the ninth month
  following, floored at 15 September) **and** the incentive window (two months before that). Do not
  carry 15 March / 15 January across.
- **AIT instalment dates do not move** with the income year — s.155(2) fixes them to the financial
  year: 15 September, 15 December, 15 March, 15 June.
- **Withholding return dates do not move** — s.177(3) names the calendar quarters.
- **The VAT tax period is a Gregorian calendar month** regardless of the entity's accounting year.

## 9. Holidays

Each Act carries its own next-working-day rule; there is **no general rule** across the statutes, so
do not assume one for an obligation not listed here.

| Obligation | Shift | Provision |
|---|---|---|
| Income tax return (individual, company, first-time, returning resident) | Next working day after a **government holiday** | ITA s.170(3) |
| Advance tax instalment | Next working day after a **government holiday** | ITA s.155(3) |
| Withholding tax return | Next working day after a **weekly or government holiday** | ITA s.177(3) proviso |
| VAT return | Next working day after a **government holiday** | VAT Act s.64(1) |

Bangladesh's government holiday list is published annually by the Ministry of Public Administration
and moves with the lunar calendar. Check the year's list rather than assuming.

---

## 10. Reported but NOT confirmed — do not diarise these without checking

Each of the following circulates in commercial compliance calendars. None could be traced to primary
text, so none is listed as a live obligation above. **Absent beats wrong.**

| Item | What is claimed | Why it is not listed |
|---|---|---|
| **Annual salary statement, 25 October** ("Schedule Ga/Ca" of the s.177 return) | Employee-wise salary paid and TDS deducted, filed with the Jul–Sep quarterly return | Traced to a single commercial compliance-calendar site. **Not verified against the TDS Rules 2026 text or any NBR form.** The Income Tax Act 2023 carries no equivalent of ITO 1984 ss.108/108A; the salary obligation is discharged through the s.145 certificate and the quarterly s.177 return. The same source also publishes a pre-Finance Act 2026 advance-tax threshold, so nothing else from it has been imported either. |
| **Employee tax statement, 25 April** ("Schedule Cha") | Filed with the Jan–Mar quarterly return | Same single source, same caveat. |
| **Audited financial statements to the VAT authority within 6 months of financial year end** (31 December for a June year end) | An annual VAT-side filing | Derived from a professional summary. **The underlying provision in the VAT Act was not identified.** Ask the Divisional VAT office whether it applies to the business. |
| **CA-certified annual VAT statement** | An annual certified statement to the VAT authority | No current provision was found in the VAT Act 2012 section index, and no post-Finance Act 2026 advisory mentions it. Most likely a repealed **VAT Act 1991** relic — but that could not be affirmatively established either, so it is neither listed nor ruled out. |
| **Standalone VAT price declaration** (মূল্য ঘোষণা) | A separate pre-supply price filing | Same position. The live input-side filing is the **উপকরণ-উৎপাদ সহগ / input-output coefficient, মূসক ৪.৩ / Mushak 4.3**, which must be revised when total input cost rises by more than 7.5%. |
| **Trade licence renewal, 30 June** | Annual renewal for the financial year beginning 1 July | Set by each **সিটি কর্পোরেশন / city corporation** or **পৌরসভা / paurashava**, not by a national statute. The date is real for many authorities but is **not uniform** — check the issuing authority's own rule. |
| **DIFE half-yearly return Form-80 (15 July) and annual return Form-81 (15 February)**; trade union annual return (30 April) | Bangladesh Labour Rules 2015 rr.362(2), 176(1) | Sourced only from a **third-party mirror** of the English gazette text, not cross-checked on bdlaws. Treat as a prompt to check, not as a date. |
| Factory licence, fire licence and environmental clearance renewal cycles | Various | Sourced only from commercial compliance-services websites. Excluded entirely. |

Two labour-side obligations that **are** grounded in primary text, for completeness — neither is
month-fixed, so neither appears in the monthly table:

- **শ্রমিক অংশগ্রহণ তহবিল / WPPF** — the owner pays **5% of the previous year's net profit** in the
  ratio **80 : 10 : 10** to the Participation Fund, the Welfare Fund and the Workers Welfare
  Foundation Fund **within nine months of the end of every year** (31 March for a 30 June year end).
  Labour Act 2006 **s.234(1)(b)** — http://bdlaws.minlaw.gov.bd/act-952/section-26287.html. Coverage
  is set by **s.232(1)**: paid-up capital of at least Tk 1 crore, **or** fixed assets of at least
  Tk 2 crore, on the last day of an accounting year. Penalties under s.236 fall **personally** on
  directors and managers.
- **ভবিষ্য তহবিল / Provident fund** — audited accounts and the audit report go to the **Director of
  Labour within one month** of the audit report being submitted (Labour Act s.264(15)).

---

## Where the machine-readable dates live

`data/rates-AY2026-27.toml`, section `[deadlines]`. Each node carries `value`, `source`, `as_of`,
`verified` and `note`. Two nodes in that section are `verified = false`:
`deadlines.vat_quarter_boundaries`, for the reason given in §4, and
`deadlines.income_tax_return_specified_date_status`, which states both readings of the individual
specified date. Re-run `python3 src/engine/rates.py --assessment-year 2026-27 --all` rather than
trusting that count — it goes stale the moment a node is edited.

**Updating after the next Finance Act:** open each section on bdlaws using the URLs above, read the
amendment footnotes at the foot of the page — they name the amending Act and its effective date —
then rewrite the TOML `value`, `source`, `as_of` and `note` together, and update this file. Never
move `as_of` forward without re-reading the section: a stale `as_of` on a changed figure is the most
dangerous state these files can be in.

---
Maintained by Moshiur Rahman (@bemoshiur) · Ticon Sys — https://ticonsys.com · MIT
