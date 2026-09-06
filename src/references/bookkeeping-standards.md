# Bookkeeping standards — হিসাবরক্ষণ মানদণ্ড

**Current as of:** 2026-09-06
**Assessment year:** AY 2026-27 / করবর্ষ ২০২৬-২০২৭. The income-tax provisions below are the Income Tax
Act 2023 as amended by the Finance Act 2026 (Act 96 of 2026), effective 1 July 2026.
**Sources:** primary text first — the **Companies Act 1994** (কোম্পানি আইন, ১৯৯৪) and the **Financial
Reporting Act 2015** (আর্থিক প্রতিবেদন আইন, ২০১৫) read from the enacted **Bangla** text on
bdlaws.minlaw.gov.bd (act-788 and act-1169 respectively), cross-checked against the 1995 authentic
English translation; the Income Tax Act 2023 and Finance Act 2026 on bdlaws and NBR; FRC, RJSC and
ICAB instruments as cited line by line. Professional summaries are used only where named.
**Status:** POPULATED. Every statement below is traceable to a source named on the line. **Not yet
reviewed by a Bangladeshi Chartered Accountant.**

> **How to read the confidence marks.**
> **[PRIMARY]** — read from the enacted text, the gazette, or the regulator's own instrument.
> **[SUMMARY]** — rests on a professional firm's or institute's summary; the source is named.
> **[UNCONFIRMED]** — could not be confirmed, or sources conflict. **Do not state an [UNCONFIRMED]
> item as a rule or a deadline.** Say what is known, say what is not, and send the user to the
> regulator and a licensed CA.
> **[OBSOLETE — STILL CIRCULATING]** — a figure that is wrong today but which the user will find on
> advisory blogs, in press archives, and sometimes on the regulator's own stale pages. Named
> explicitly so you can correct the user instead of agreeing with them.

> **Where the machine-readable numbers live.** Rates and thresholds TakaBooks *computes* with belong
> in `src/data/rates-AY<year>.toml`. Most of what is below is not a computable rate at all — it is a
> statutory duty, a deadline, a retention period or a definitional threshold — so it is stated here
> with its citation. Nothing here is a substitute for a verified TOML node: if the engine has no node,
> the answer to the user is "TakaBooks does not hold a verified figure for this", never a number
> lifted out of this prose.

---

## 1. Books of account — Companies Act 1994, s.181 [PRIMARY]

**s.181(1) — what must be kept.** Every company shall keep proper **হিসাব বহি / books of account** with
respect to:

| Clause | Required records |
|---|---|
| (ক) | All sums of money **received and expended**, and the matters in respect of which the receipt and expenditure took place |
| (খ) | All **sales and purchases of goods** |
| (গ) | All **assets and liabilities** |
| (ঘ) | For companies in **production, distribution, marketing, transportation, processing, manufacturing, milling or crushing, mining and mineral extraction** — particulars of the utilisation of **material, labour and other overhead costs** |

**s.181(2) — the quality test.** Books are **not deemed proper** unless they give a **true and fair
view** of the company's affairs and contain a **sufficient explanation of its transactions**. A ledger
that balances but explains nothing does not satisfy s.181.

**s.181(3) — where they are kept.** At the **registered office**, open to inspection by the directors
at all times during business hours. *Proviso:* by **a decision of the board**, all or any of the books
may be kept at **any other place in Bangladesh for not more than SIX MONTHS**, and the company must
then file written notice with the **Registrar within SEVEN DAYS** of that decision, giving the full
address of the other place.

**s.181(4) — branch offices.** Where a company has a branch in or outside Bangladesh, s.181(1) is
satisfied if proper books of that branch's transactions are kept there **and summarised returns, made
up to date, are sent to the registered office at intervals of not more than THREE MONTHS**.

**s.181(5) — retention: TWELVE YEARS.** Every company shall preserve in good order the books of
account **and the vouchers relevant to any entry in them** for **not less than twelve years
immediately preceding the current year**. *Proviso:* a company incorporated less than twelve years
before the current year preserves them for the **whole period since incorporation**. See §11.

**s.181(6) — penalty.** A person within s.181(7) who fails to take reasonable steps to secure
compliance, or by his own wilful act causes a default, is punishable **for each offence** with
imprisonment up to **six months**, or a fine up to **Tk 5,000**, or both.

**s.181(7) — who carries that liability.** (ক) where there is a managing agent, managing director,
executive director, general manager or manager — that person **and all other officers of the company,
but excluding the bankers, the auditors and the legal advisers**; (খ) where the managing agent is a
firm — **every partner**; (গ) where it is a body corporate — **every director** of it; (ঘ) where there
is no such officer — **every director** of the company.

> ⚠️ **A translation note worth knowing.** The Bangla of s.181(7)(ক) reads oddly — literally "the
> manager and the manager's banker, auditor and legal advisers are excluded". The 1995 authentic
> English resolves it: *"…and all officers **but excluding the bankers, auditors and legal
> advisers**"*. **Use the English reading of this one clause.** It is the only place in s.181 where
> the English is the clearer text; §3 below is the opposite case.

**s.182** provides for inspection of the company's books of account.

---

## 2. ⭐ Language and currency of the books — an honest negative finding

> **There appears to be NO express statutory requirement that books of account be kept in Bangla or in
> English.** No such requirement was found in the **Companies Act 1994**, in the **Income Tax Act 2023
> or its rules**, or in the **VAT & SD Act 2012 or the VAT & SD Rules 2016**.

This contradicts something asserted very widely — including by advisers who state it as settled law.
TakaBooks states the negative finding plainly rather than repeating the folklore. What actually exists
is only this:

| Instrument | What it actually says |
|---|---|
| **Companies Act 1994, s.379(1)(a)** | A **foreign company** must file the certified copy of its charter, statutes or MoA & AoA and, **"if the document is not written in the English or Bangla language, a certified copy of a Bangla or English translation of it"** |
| **Companies Act 1994, s.380(2)** | **"If any document referred to in sub-section (1) is not written in the Bangla or English language, a certified Bangla or English translation shall be annexed to it"** |
| **VAT & SD Act 2012 s.107 and VAT & SD Rules 2016 rule 95** | **NO language requirement.** Rule 95 requires only that records be preserved **at the registered premises on a fiscal-year basis**, so they are not destroyed and can be examined easily, and that **electronic information be preserved with proper security** |
| **Income Tax Act 2023** | Full-text search found **no language requirement** for books of account. s.72(3) empowers the Board to prescribe accounting methods by rules, and **NBR's published Income Tax Rules contain no rule on books of account** |
| **Bengali Language Introduction Act 1987** | Requires Bangla in courts and in government, semi-government and autonomous offices. **It does not by its terms govern a private company's books of account** |

**Both Companies Act provisions are about a foreign company's constitutional documents and its filed
returns — not about the ledgers a Bangladeshi company keeps.**

> ⚠️ **The claim that "the VAT rules contain a specific Bangla-or-English requirement" was NOT
> confirmed.** That formulation appears to originate in the **repealed VAT Rules 1991**, whose text
> could not be retrieved to confirm the rule number or wording. The **VAT & SD Rules 2016**, in force
> since 1 July 2019, contain no such rule. If a Bangla-or-English rule is to be asserted for VAT
> records, it needs a citation nobody has been able to supply. **[UNCONFIRMED]**

**Currency: likewise no express requirement** that accounts be maintained in **টাকা / Taka** was found
in any of the three statutes. The evidence is indirect but converging: Companies Act **Schedules X and
XI are denominated in টাকা throughout**, so the *filed* balance sheet, profit and loss account and
annual return are in Taka; the Income Tax Act computes tax **to the nearest Taka**; and **IAS 21**
functional- and presentation-currency rules apply as an adopted standard. **[UNCONFIRMED as an express
rule; well supported as practice.]**

**What to tell a user.** Keeping books in Bangla or English, in Taka, is unquestionably safe and is
what every filing, return and audit will require in practice. But if someone asks *which section*
compels it, the honest answer is that no such section was found — not that one exists. Do not invent a
citation to close the gap.

---

## 3. Accounts, the AGM, and what goes to RJSC [PRIMARY]

| Obligation | Rule | Section |
|---|---|---|
| **AGM / বার্ষিক সাধারণ সভা** | One in **each Gregorian calendar year**, specified as such in the notice, with **not more than fifteen months** between one AGM and the next. *First proviso:* the **first AGM** may be held **within eighteen months of incorporation**, and if so held no AGM is needed in the year of incorporation or the following year. *Second proviso:* on application to the Registrar **within thirty days** of expiry, the Registrar may extend (**not the first AGM**) by **not more than ninety days**, or **not beyond 31 December** of the calendar year the AGM relates to, **whichever is earlier** | **s.81** |
| **Laying the accounts** | At every AGM the board lays a **balance sheet and profit and loss account** (or, for a non-profit body, an income and expenditure account) | **s.183(1)** |
| **How stale the accounts may be** | First AGM: from incorporation to a date **within nine months before** the meeting. Subsequent AGMs: from the day after the last accounts to a date within the like period. **s.183(2)(b)(ii)** allows **twelve months** instead of nine where the company carries on business or has interests **outside Bangladesh**, and the Registrar may extend by up to **three months** on application made before expiry | **s.183(2)** |
| **Audit is not optional** | The balance sheet and P&L **must be audited by the company's auditor**; the report is **attached or referred to at the foot**, and must be **read at the general meeting and be open to inspection by any member** | **s.183(3)** |
| **Financial year length** | May be **more or less than a calendar year but NOT MORE THAN FIFTEEN MONTHS** — *proviso:* extendable to **eighteen months** with the Registrar's special permission | **s.183(4)** |
| Members' copies | Kept at the registered office for inspection **at least fourteen days before** the meeting (s.183(6)); **sent free of charge, not less than fourteen days before**, to every member, debenture holder and debenture trustee (s.191) | ss.183(6), 191 |
| Directors' report | Board's report accompanies the accounts | **s.184** |
| **Authentication** | For a non-banking company: signed by the managing agent, manager or secretary (if any) **and by not less than two directors, one of whom must be the managing director if there is one**. **s.189(3): the Board must APPROVE the accounts before they are signed and before they go to the auditors for report** | **s.189** |
| Unsigned balance sheet | Issuing one not signed or not accompanied as required — imprisonment up to 6 months, or fine up to **Tk 2,000**, or both | s.189 |
| Holding / subsidiary alignment | Financial-year alignment rules | s.187 |

### s.36 — the annual list of members and summary (Schedule X)

- **s.36(1):** every company having a share capital prepares, **within eighteen months of
  incorporation and thereafter at least once every year**, a list in the form of **SCHEDULE X** of
  persons who were members on the day of the first or only general meeting of that year, and of those
  who ceased to be members since the last return.
- **s.36(2):** contents — names, addresses, nationality and occupation of all past and present
  members; shares held by each present member; dates of registration of transfers; and a **summary**
  of share capital, shares taken, amounts called up and received on calls, amounts unpaid, and
  commissions or discounts on shares or debentures not written off.
- **s.36(3) — DEADLINE:** the list and summary go in a **separate part of the register of members**
  and must be **completed within TWENTY-ONE DAYS after the first or only general meeting of the
  year**; the company must then **forthwith** file a copy of that part with the Registrar, signed by
  **two directors including the managing director** (or by one director where there is none) **and by
  the managing agent, manager or secretary**, with their **certificate** that it states the facts
  correctly as at the date of the return.
- **s.36(4):** a **private company** additionally files a certificate signed by a director or officer
  that no invitation to the public to subscribe has been issued since the last return (or since
  incorporation, for the first return); and where the return shows **more than fifty members**, a
  certificate that the excess persons fall outside the fifty-member limit in s.2(1)(ট)(ই).
- **s.36(5) — penalty:** fine up to **Tk 200 for every day** the contravention continues, on the
  company **and** every officer who knowingly and wilfully authorises or permits it.

### s.190 — filing the balance sheet with the Registrar

- **s.190(1) — DEADLINE:** within **THIRTY DAYS** from the date the balance sheet and profit and loss
  (or income and expenditure) account are **laid before the AGM** — or, where no AGM was held in a
  year, within **thirty days from the last date on or before which it should have been held** — the
  company files with the Registrar **THREE COPIES**, signed by the managing director, managing agent,
  manager or secretary (or, failing all of those, by a director), with everything the Act requires to
  be annexed or attached.
- **s.190(2):** if the balance sheet laid before the AGM was **not adopted**, or no AGM was held, a
  **statement of that fact and the reasons** must be annexed to the balance sheet and to every filed
  copy.
- **s.190(3) — penalty:** fine up to **Tk 100 for every day** the failure continues, on the company
  and on every officer who knowingly and wilfully authorises or permits it.

> ### ⚠️ s.190(1) — the Bangla and English texts diverge, and the Bangla governs
>
> The **enacted Bangla text** of s.190(1) carries a proviso requiring a **private company to file the
> balance sheet and the profit and loss account SEPARATELY**, and a second proviso that for a private
> company which is **not a subsidiary of a public company**, **no person other than a member** may
> inspect or obtain a copy of its profit and loss account.
>
> **The 1995 authentic English translation (S.R.O. 177-Law, 1 October 1995) OMITS the first proviso.**
> The Bangla is the authoritative text and RJSC practice corroborates it — private companies do file
> the two statements separately. **[PRIMARY — Bangla text; the divergence is documented.]**
>
> More generally: **do not treat the 1995 English translation as the current Companies Act.** It
> carries obvious typographical errors and predates every amendment since, including **ss.185(2A) and
> (2B), 190(1A) and 212(5)** inserted by the Financial Reporting Act 2015, and the whole of **Part
> X-A (One Person Company)**. Use the Bangla text at http://bdlaws.minlaw.gov.bd/act-788.html .

**s.190(1A)** *(inserted amendment)*: a company that is a **"public interest entity" as defined in
s.2(8) of the Financial Reporting Act 2015** **may NOT file its financial statements** unless they
were prepared following the standards made by the FRC under **s.40** of that Act. See §8.

**Foreign companies — Part X (ss.379–387).** **s.384** penalises non-compliance with a fine up to
**Tk 5,000** plus **Tk 500 per day** of continuing default. **[UNCONFIRMED — there is no
annual-accounts deadline in the Act for a foreign company.]** s.380(1) says only "in every English
calendar year"; neither the Act nor any RJSC page states a number of days. **Applying s.190's "within
30 days of the AGM" to a foreign company would be an unsupported extrapolation — do not do it.**
Likewise s.379(3) requires change returns "within the prescribed time" and **the prescribing rule was
not located**.

---

## 4. Recurring RJSC filings and their deadlines [PRIMARY — Companies Act]

| Filing | Form | Section | Deadline |
|---|---|---|---|
| Annual summary of share capital and list of members | **Schedule X** | s.36 | **21 days** after the AGM |
| Balance sheet, and (**separately**, for a private company) profit and loss account | prescribed BS / P&L forms | s.190(1) | **30 days** from the date laid at the AGM |
| Auditor's notice of acceptance or refusal of appointment | **Form 23B** | s.210(2) | **30 days** from the auditor receiving intimation |
| Consent of a director to act | **Form IX** | s.92 | 30 days from appointment |
| Situation of, or change in, the registered office | **Form VI** | s.77 | **28 days** |
| Particulars of, or change in, directors, manager or managing agents | **Form XII** | **s.115(2)** | **14 days** |
| Special or extraordinary resolution | **Form VIII** | s.88(1) | **15 days** of passing |
| Return of allotment | **Form XV** | s.151 | **60 days** of allotment |
| Particulars of mortgages and charges | **Form XVIII** | ss.159, 391 | **21 days** of creation |
| Modification of a charge | **Form XIX** | s.167(3) | 21 days |
| Memorandum of satisfaction of a charge | **Form XXVIII** | ss.172, 391 | 21 days |
| Notice of increase of share capital | **Form IV** | s.56 | 15 days |
| Consolidation or division of capital | **Form III** | ss.53, 54 | 15 days |
| **One Person Company** financial statements | — | **s.392ঝ** | **180 days** from financial year end |

> ⚠️ **Form XII is 14 days, not 15.** RJSC's own **Bangla** returns page says "১৫ দিনের মধ্যে". **The
> statute, s.115(2), says চৌদ্দ দিন = 14 days**, and RJSC's English FAQ agrees with the statute.
> **Use 14.** The penalty for failing to file particulars of directors is **Tk 500** per breach
> (s.115(4)).

> ⚠️ **"Form 118" does not exist** in RJSC's catalogue. It is most likely a confusion with **Form 117**
> (Instrument of Transfer of Shares), or an import from Indian practice. If a user cites Form 118, ask
> what they actually need to file.

> ⚠️ **Several RJSC forms carry internal citation errors** — Form XII's printed title omits "CHANGE";
> Form XVIII's header cites ss.159 and 391 while its body says "Sections 169 & 391"; RJSC's pages cite
> "Section 12 & 391" for Form XXVIII where the form itself says ss.172 and 391. Go by the statute.

**Statutory fines for RJSC defaults** (distinct from the administrative fees in §5) are summarised in
`penalties.md`; the headline ones are s.36(5) **Tk 200/day**, s.190(3) **Tk 100/day**, s.82 failure to
hold an AGM **up to Tk 10,000 plus Tk 250/day**, and s.77(4) registered-office particulars **up to
Tk 200/day**.

---

## 5. RJSC fees — the current position, and the obsolete figure everyone quotes

**The governing chain:** **S.R.O. 136-Ain/2016** (22 May 2016) → **S.R.O. 101-Ain/2019** (gazetted
23 April 2019), which substituted Schedule II in full and introduced the **per-year late fee** →
**Ministry of Commerce Notification No. 26.00.0000.096.20.003.22.162** (gazetted 9 July 2023,
**effective 1 July 2023**), which raised the company per-document filing fee from Tk 100 to **Tk 200**
and left the late fee unchanged. **[PRIMARY]**

| Entity | Filing fee (within time) | Late fee ≤ 3 years | Late fee > 3 years |
|---|---|---|---|
| Private and public company | **Tk 200 per document** | **Tk 500 per year or part** | **Tk 700 per year** |
| Foreign company | **Tk 500 per document** | *not stated on RJSC's page* | *not stated* |
| Trade organisation | **Tk 400 per document** (RJSC page; ⚠️ the gazette says Tk 500) | Tk 500 per year or part | Tk 700 per year |
| Society | **Tk 800 per document** | **Tk 5 per day** | — |
| Partnership firm | Forms II / V / VI **Tk 500 each** (RJSC page; ⚠️ the gazette prices s.63 notices at Tk 1,000) | — | — |

Registration fee is **NIL** for nominal capital up to Tk 10 lakh; **Tk 80 per lakh** from Tk 10–50
lakh; **Tk 130 per lakh** above Tk 50 lakh. Name clearance **Tk 500**; inspection of documents
**Tk 500**; **digital certificate supply NIL** since 23 April 2019.
Fee page (updated 26 July 2023): https://roc.gov.bd/pages/static-pages/6922dc05933eb65569e0dfb6 ·
Calculator: https://app.roc.gov.bd/psp/fee_calculator

> ### ⚠️ [OBSOLETE — STILL CIRCULATING] "Tk 2 per day, maximum Tk 1,000"
>
> That late fee is **obsolete for companies** and has been since 2019. It survives only in RJSC's own
> **stale English FAQ** at https://app.roc.gov.bd/Guidlines/faq.html, which also still shows pre-2016
> charge-registration fees. **Do not cite that FAQ for any fee.** The current figures are **Tk 500 per
> year or part** (≤3 years) and **Tk 700 per year** (>3 years).
>
> Note the wider pattern: RJSC's returns-filing page was last content-updated **13 August 2015** and
> its forms pages in 2015–2016. Only the fees page is current. The statutory **deadlines** on those
> old pages are corroborated by the Act (except the Form XII error above); the **fees** are not.

> **[UNCONFIRMED]** Whether the per-year late fee is charged **in addition to** or **instead of** the
> Tk 200 base filing fee is not stated expressly by RJSC's page or by the gazette. The page's layout
> implies additive. Say so rather than quoting a total.

> **[UNCONFIRMED]** Whether RJSC **online filing is mandatory**, and whether a client-side digital
> signature certificate is needed for e-filing, could not be established from a primary RJSC rule. The
> stale FAQ still offers kiosk and manual counter submission.

**Two 2026 developments worth telling a client about.**
1. An **RJSC circular of 6 August 2026** (memo 26.06.0000.001.31.001.21, published 13 August 2026)
   requires the **head of the registered entity, or a duly authorised person, to attend the
   Registrar's office IN PERSON** with board minutes and photo ID to collect the e-services **admin
   user ID and password** — a response to unauthorised use of credentials obtained through nominated
   representatives. **Effective immediately**; credentials can no longer be obtained remotely or
   through an agent.
2. An **Electronic Business Registration System (eBRS)** was announced on **1 September 2026** — with
   real-time pre-verification against NID, e-TIN and mobile number. It is **announced, not launched**,
   and it concerns *registration*, not returns filing.

**RJSC portal:** https://app.roc.gov.bd (corporate site https://roc.gov.bd; note that
**rjsc.gov.bd did not resolve** during this research). Returns filing at
https://app.roc.gov.bd/psp/rf_main .

---

## 6. Statutory audit — who needs one, who may do it [PRIMARY]

**Which entities must be audited?** Under **s.183(3)** the balance sheet and profit and loss account
laid before the AGM **must be audited**, and s.183 applies to **every company** holding an AGM under
s.81, **with no small-company exemption**. **So statutory audit applies to every company registered
under the Companies Act 1994, private limited companies included.** There is no turnover floor below
which a Bangladeshi company escapes audit — the turnover thresholds people remember belong to the
*income tax* rule in §7, which is a different question.

**Appointment — s.210:**

| Sub-s. | Rule |
|---|---|
| 210(1) | Appoint auditor(s) **at each AGM**, to hold office **from the conclusion of that meeting until the conclusion of the next AGM**, and give notice to every auditor appointed **within SEVEN DAYS** |
| 210(2) | The auditor must **inform the Registrar in writing within THIRTY DAYS** of receiving notice, whether he accepts or refuses (Form 23B) |
| 210(3) | A retiring auditor must be re-appointed at the AGM unless specified exceptions apply |
| 210(4) | If no auditor is appointed at the AGM, **the Government may appoint** one |
| 210(5) | The company must notify the Government **within seven days** of that power becoming exercisable; failure — fine up to **Tk 1,000** |
| 210(6) | The **first auditor(s)** must be appointed by the board **within ONE MONTH of the date of registration**, holding office to the conclusion of the first AGM |

**Qualification — s.212(1):** a person **shall not be appointed as auditor of any company unless he is
a "Chartered Accountant" within the meaning of the Bangladesh Chartered Accountants Order 1973 (P.O.
No. 2 of 1973)**. s.212(2)–(3) list disqualifications; **s.212(4)**: an auditor who becomes
disqualified after appointment is **deemed to have vacated office**. **s.212(5)** (inserted by the FRA
2015): a person is **not qualified to audit a public interest entity unless enlisted with the FRC**
under FRA s.31. **s.213** sets out auditors' powers and duties.

**Rotation is not in the Companies Act.** There is **no auditor-rotation rule in the Companies Act
1994**. Rotation is imposed by sectoral regulators:

- **Listed companies — BSEC Notification No. BSEC/CMRRCD/2006-158/208/Admin/81, dated 20 June 2018,
  *Gazette Extraordinary* 8 August 2018**, made under s.2CC of the Securities and Exchange Ordinance
  1969. **Condition 2(2):** *"The company shall not appoint any firm of chartered accountants as its
  statutory auditors for a consecutive period exceeding three years."* Condition 2(3) applies the same
  to the individual auditor or firm. Condition 2(1): the auditor must be on the **BSEC panel**.
  Conditions 2(4)–(5): report per **ISA**, ensuring compliance with the Companies Act 1994, the FRA
  2015 and the securities laws, and with **ISQC** and the **Code of Ethics**.
- **Non-audit services** are restricted by the **BSEC Corporate Governance Code 2018**, condition 7 —
  appraisal or valuation, financial information systems design, bookkeeping, broker-dealer, actuarial,
  internal or special audit, corporate-governance compliance certification, and anything creating a
  conflict of interest. Condition 7(2) bars share ownership by partners, employees and their families;
  7(3) requires the auditor's representative to attend the AGM/EGM; 9(1) requires an annual
  corporate-governance compliance certificate from a practising CA, CMA or Chartered Secretary **other
  than the statutory auditor**.

> ⚠️ **The three-year rotation rule is NOT in the Corporate Governance Code 2018**, contrary to a great
> deal of commentary. It is in the **8 August 2018 financial-reporting notification** cited above.
> Getting the instrument right matters when a client is arguing with an auditor about scope.

**Bank auditors — Bank Company Act 1991 s.39(1):** a bank company's accounts may be audited only by a
person qualified as a company auditor **who is also approved and enlisted by Bangladesh Bank**.
s.39(2) applies the powers, duties, liabilities and penalties of Companies Act s.213 to such an
auditor.

---

## 7. The income-tax audit requirement — ITA 2023 s.73

**s.73 was SUBSTITUTED IN FULL by the Finance Act 2026 (Act 96 of 2026) s.59, with effect from 1 July
2026.** Marginal note: *"কোম্পানি, ইত্যাদি কর্তৃক নিরীক্ষাকৃত আর্থিক প্রতিবেদন এবং আয় পরিগণনাপত্র
দাখিল"*. **[PRIMARY — read from the enacted Bangla text and as substituted into the ITA 2023 on
bdlaws.]**

| Sub-s. | Requirement from 1 July 2026 |
|---|---|
| **s.73(1)** | **All taxpayers falling within "company"**, **any person with income from a long-term contract**, and **all firms, associations of persons, Hindu undivided families and artificial juridical persons with turnover above Tk 10 crore OR capital above Tk 5 crore** — the financial statements filed with the return must be **AUDITED AND CERTIFIED BY A REGISTERED CHARTERED ACCOUNTANT**, and the **Income Computation Sheet** prepared and certified by a registered CA, CMA or ITP |
| **s.73(2)** | **All firms, AOPs, HUFs and artificial juridical persons** — the Income Computation Sheet filed with the return must be prepared and certified by a CA, CMA or ITP |
| **s.73(3)** | Every person in the business of **buying and selling gold, silver, gold or silver ornaments, gems-diamonds or platinum** (s.112A), and every **manufacturer, importer, supplier, distributor or wholesaler / আড়তদার** (s.130A) — must file an Income Computation Sheet certified by a CA, CMA or ITP |
| **s.73(4)** | A **developer or real estate developer** shall follow all conditions of **IFRS** and record revenue per **IFRS 15** |
| **Explanation** | *"Income Computation Sheet"* = a statement computing taxable income and tax by applying and adjusting the incomes in ss.45–48, the business deductions in ss.49–54 and the inadmissible deductions in ss.55–56. *"Financial Statement"* includes the **Statement of Comprehensive Income, Statement of Changes in Equity, Cash Flow Statement, Statement of Financial Position / Balance Sheet, and Notes** |

| Threshold | Enacted Bangla | In Taka | In BDT |
|---|---|---|---|
| Turnover | **১০ (দশ) কোটি টাকার অধিক** | more than **Tk 10 crore** | **more than BDT 100,000,000** |
| Capital | **৫ (পাঁচ) কোটি টাকার অধিক** | more than **Tk 5 crore** | **more than BDT 50,000,000** |

> ### ⚠️ [OBSOLETE — STILL CIRCULATING] PwC is wrong here by a factor of ten
>
> **PwC Bangladesh's *Finance Act 2026: Key Amendments* prints these thresholds as "turnover exceeding
> BDT 10m or capital exceeding BDT 5m".** That is **wrong by a factor of ten**. The enacted Bangla text
> of Finance Act 2026 s.59 says **১০ কোটি** and **৫ কোটি** — Tk 10 crore and Tk 5 crore. Verified
> twice, in the Finance Act 2026 itself and as substituted into the ITA 2023 on bdlaws, and
> independently consistent with **KPMG** (*Bangladesh Tax 2026*, p.31) and **Tuhin & Partners**.
> **Use 10 crore / 5 crore.**
>
> The error matters enormously in the direction it points: at BDT 10m (Tk 1 crore) turnover, a very
> large number of small firms and partnerships would be dragged into a mandatory CA audit they do not
> in fact need. If a client has been told they must have a CA audit because their turnover passed
> Tk 1 crore, check which figure their adviser was reading.

**The immediately preceding version** of s.73 (substituted by **Act 89 of 2026 s.56**, in force
10 April – 30 June 2026) was structurally different, and it is what most secondary commentary still
describes: it applied to *"any person other than a natural person, HUF and fund"* plus long-term
contract earners, with provisos excluding **firms, trusts, AOPs, foundations, societies and
co-operative societies with gross receipts not exceeding Tk 5 crore**, and **educational institutions
engaged only in primary and pre-primary education**. **That version is superseded.**

**Related provisions:**

| Provision | Requirement |
|---|---|
| **s.169(2)** (amended by FA 2026 s.96) | The return **must be accompanied by** (a) the **audited financial statements**; (b) **evidence of compliance with the standards prescribed by the Board, for verification**; (c) the **Income Computation Sheet**; and (d) subject to s.177, **proof of filing / acknowledgement of the withholding tax return** |
| **s.267** | Penalty for not maintaining accounts as prescribed under s.72(3) — up to **1.5× the tax payable** (Tk 5,000 where income is within the tax-free limit); for rental income from tangible property, **50% of the tax on that income or Tk 5,000, whichever is higher** |
| **s.273** | Penalty **on the Chartered Accountant** where the audit report is not certified as having followed **IAS/IFRS** for the accounts and **ISA** for the audit, or is untrue or incorrect: **Tk 50,000 – Tk 200,000** |
| **s.274** | Penalty **on the taxpayer** where the audit report is not signed by a Chartered Accountant or is credibly untrue: **Tk 100,000** for that income year |
| **s.316** | **Criminal** — filing a forged or false audited statement of accounts: rigorous imprisonment **not less than 6 months and up to 5 years** |
| **ss.167(7)–(8), 168(2)–(3)** (added by FA 2026) | Failure to comply with a notice for the **Statement of Assets and Liabilities (SOAL)** or the **Statement of Lifestyle Expenses (SOLE)** renders the filed return an **INCOMPLETE return** |
| **s.256(3)** (added by FA 2026 s.135) | The officer in charge at RJSC issues the order **dissolving a partnership firm** registered with RJSC **only on submission of a TAX CLEARANCE CERTIFICATE issued by the DCT** |

**Deadline cross-reference — ITA 2023 s.170(2):** the return with audited financial statements is due
on the **15th day of the ninth month** following the income year end, or **15 September** if that day
falls earlier. See `compliance-calendar.md`.

---

## 8. The Financial Reporting Act 2015, the FRC, and "public interest entity"

**Financial Reporting Act 2015 — Act No. 16 of 2015**, http://bdlaws.minlaw.gov.bd/act-print-1169.html .
The **Financial Reporting Council (আর্থিক প্রতিবেদন কাউন্সিল / FRC)** was established in 2016 as a
statutory body under the Finance Division. **s.3** establishes the Council; **s.7** its objectives;
**s.8** its powers and functions; **s.40** empowers it to make reporting and auditing standards;
**s.54** constitutes the Appellate Authority.

### "Public interest entity" — জনস্বার্থ সংস্থা, FRA 2015 s.2(8) [PRIMARY, read verbatim]

**(a) An entity satisfying ANY ONE of:**

| # | Criterion |
|---|---|
| (অ) | a **bank company** as defined in s.5(ণ) of the Bank Company Act 1991 |
| (আ) | any **securities issuer** with a reporting obligation to the Securities and Exchange Commission under the BSEC Act 1993 |
| (ই) | a **financial institution** as defined in s.2(খ) of the Financial Institutions Act 1993 |
| (ঈ) | a **microcredit institution** as defined in s.2(21) of the Microcredit Regulatory Authority Act 2006 |
| (উ) | an **insurer** as defined in s.2(25) of the Insurance Act 2010 |
| (ঊ) | an entity whose **annual revenue in the preceding financial year exceeded the limit fixed by the Council by Gazette notification** |
| (ঋ) | an entity satisfying **ANY TWO** of, at the end of the preceding financial year: (1) it employs **at least the minimum number of persons prescribed by regulations**; (2) **total assets** exceed the Council's Gazette limit; (3) **total liabilities excluding shareholders' equity** exceed the Council's Gazette limit |

**(b)** Also caught, where they meet the (a) criteria: state-owned companies or commercial entities;
**statutory authorities**; **NGOs** conducting voluntary activities in the private sector; and any
other similar entity.

### The quantitative thresholds — the CURRENT set [PRIMARY]

| Threshold | Amount | Instrument | Date |
|---|---|---|---|
| **Annual revenue** — s.2(8)(a)(ঊ) | **Tk 50 crore (BDT 500,000,000)** | **S.R.O. No. 34-Ain/2023** | 8 Feb 2023; *Gazette Extraordinary* **16 February 2023**; effective immediately |
| **Total assets** — (ঋ)(2) | **Tk 30 crore (BDT 300,000,000)** | **S.R.O. No. 35-Ain/2023** | same |
| **Total liabilities excluding shareholders' equity** — (ঋ)(3) | **Tk 10 crore (BDT 100,000,000)** | **S.R.O. No. 36-Ain/2023** | same |
| **Minimum manpower** — (ঋ)(1) | **50 persons** | জনস্বার্থ সংস্থা (ন্যূনতম জনবলের ভিত্তিতে) সংজ্ঞা নির্ণায়ক প্রবিধানমালা, ২০২৩, **Reg. 3(1)** | *Gazette Extraordinary* **23 October 2023** |

Index of FRC instruments: https://frc.gov.bd/pages/static-pages/6922dece933eb65569e1d7f8

"Manpower" (Reg. 2(1)(ক)) means persons working in and drawing salary from, or sharing the profit of,
the entity, employed on a **permanent, temporary, casual, contractual or outsourcing** basis — so an
outsourced workforce counts toward the 50. Reg. 3(2)–(4): FRC may call for the manpower list,
appointment rules and register, salary register, payroll, accounts, financial statements, audit
statements and PF/gratuity records, and after verification **enlists the entity as a PIE**.

**Corroborated by FRC itself (November 2025).** The FRC Chairman's presentation to the IFRS Foundation
Emerging Economies Group describes PIEs as (i) *by virtue*: banks, listed companies, NBFIs, microcredit
providers, insurers; and (ii) *by determinants*: companies, SOEs, statutory and autonomous bodies, NGOs
and others, only where **revenue ≥ BDT 500 million** OR **any two of** external liabilities ≥ BDT 100
million, assets ≥ BDT 300 million, workforce ≥ 50. It records **"7,500 plus PIEs under supervision"**.
https://www.ifrs.org/content/dam/ifrs/meetings/2025/november/eeg/ap7-frc-bangladesh-presentation.pdf

> ### ⚠️ [OBSOLETE — STILL CIRCULATING] The Tk 5 crore / 3 crore / 1 crore figures
>
> **FRC Notification 179/FRC/FRM/Prokgapon/2020-01** (11 March 2020, gazetted 29 June 2020) set revenue
> at **Tk 5 crore**, assets at **Tk 3 crore** and liabilities excluding equity at **Tk 1 crore**.
> **Those were superseded by the three 2023 SROs above** — a **ten-fold** increase in revenue and
> assets thresholds. The 2020 figures are still quoted by law-firm blogs and 2020 press, and by
> advisers working from them.
>
> **Using the obsolete set would wrongly classify small companies as public interest entities** — which
> would mean an FRC-enlisted auditor (s.212(5)), FRC standards (s.190(1A)), and RJSC refusing the
> annual report (s.185(2B)). Check the year of any threshold a client shows you.

### What attaches once an entity IS a PIE

| Provision | Obligation |
|---|---|
| **FRA s.44** | A PIE required by any law to prepare financial statements must ensure they are **audited by an auditor enlisted with the Council** and **prepared following the standards, codes, directions, rules or regulations made under the Act** |
| **FRA s.45(1)–(2)** | The Council may **review** FS and annual reports presented to any government office, and require information from officers, directors, the preparer, the auditor or audit firm, and the cost auditor |
| **FRA s.45(3)** | Where a PIE files annual financial statements with any government office, it **shall also present a copy to the Council** in the manner prescribed by regulations |
| **FRA s.45(4)** | The Council may **order any PIE to file its financial statements within a time it fixes** |
| **FRA s.46** | The Council may review an enlisted auditor's practice and inspect records, balance sheets, cash and bank balances, securities and stock |
| **FRA s.47(1)–(2)** | On finding a failure to follow the standards, or a **material misstatement**, the Council may warn or direct correction; the PIE must **amend the FS within 30 days** and **re-present them** |
| **Companies Act s.185(2A)** | A PIE must present its documents together with the **enlisted auditor's report**, prepared per FRC standards under FRA s.40 |
| **Companies Act s.185(2B)** | **RJSC shall NOT accept the annual report of such a company** unless presented with the enlisted auditor's report |
| **Companies Act s.190(1A)** | A PIE **cannot file financial statements** with RJSC unless prepared per FRC standards |
| **Companies Act s.212(5)** | A person is **not qualified to be auditor of a PIE unless enlisted with the FRC** under FRA s.31 |
| **FRA s.48 — PENALTY** | Obtaining registration by breach of conditions, dishonest means or false information, **or contravening any provision of the Act**: imprisonment up to **5 years**, or a fine of **NOT LESS THAN Tk 500,000**, or both |

**FRC enlistment of auditors and audit firms.** **FRA s.31(1):** no auditor or audit firm is qualified
to audit a PIE, or to provide any audit-related service, **without enlistment with the Council**.
**s.31(2):** if an enlisted auditor or partner resigns from or joins an audit firm, the Council must be
**notified in writing within 15 days**. **s.32:** application, certificate, verification, fees and
e-register are prescribed by rules — **ফাইনান্সিয়াল রিপোর্টিং কাউন্সিল (নিরীক্ষক ও নিরীক্ষা ফার্ম
তালিকাভুক্তি) বিধিমালা, ২০২২**, dated 8 November 2022, gazetted **10 November 2022**. Only **ICAB /
ICMAB** enrolled professionals and registered audit firms may apply: https://enlistment.frc.gov.bd/ .
**Renewal is annual, by financial year** — FRC memo **177/FRC/SR/2026/526 dated 14 May 2026** closed
FY2026-27 enlistment and renewal applications on 14 May 2026 at 4:00 pm, with a late-fee window to
7 June 2026, fully online with online payment only, plus an affidavit on a Tk 300 non-judicial stamp
couriered in hard copy.

**Signature format — FRC Notification 146/FRC/SS/Prokgapon/2020/71**, dated 21 December 2020, *Gazette
Extraordinary* **19 January 2021**: auditors of all PIEs must sign in their own name stating (a) the
firm name, (b) the **firm registration number**, (c) the signature, and (d) the auditor's name with
partner or enrolment number.

> ### ⚠️ [UNCONFIRMED] There is NO published FRC deadline for a PIE to file its accounts with the Council
>
> **FRA s.45(3)** says "in the manner prescribed by regulations" and **s.45(4)** allows case-by-case
> orders, but **no regulation prescribing a routine deadline was located**, and **FRC's own November
> 2025 presentation says the PIE report submission portal is still being developed**. **Do not state a
> 90-day or 120-day FRC deadline** — that figure circulates but has no located instrument behind it.

**Sectoral filing deadlines that DO exist (not FRC-issued):**

| Regulator | Requirement |
|---|---|
| **Bangladesh Bank** — Bank Company Act 1991 **s.38** | Every bank company prepares balance sheet, P&L and financial statements **as at the last working day of each English calendar year** — a mandatory **31 December year-end** |
| **Bangladesh Bank** — **s.40** | Three copies filed with Bangladesh Bank **within two months** of period end; extendable by up to **two further months** |
| **NBR (VAT)** — VAT & SD Act 2012 **s.90A** (inserted by Finance Act 2021 s.53) | Every **registered limited company** files its **annual audited financial statements** for the previous year with the **Commissioner within the first six tax periods (six months) of the current financial year**; extendable by up to six further tax periods on application for reasonable cause |
| **NBR (Income Tax)** — ITA 2023 **s.170(2)** | Return with audited FS due on the **15th day of the ninth month** following the income year end, or **15 September** if earlier |

---

## 9. Which accounting standards apply, and to whom

### The naming change, resolved

**The "BFRS / BAS" naming was dropped with effect from annual periods beginning on or after 1 January
2018.** **ICAB Circular Ref: 1/1/ICAB-2017, dated 14 December 2017**, verbatim:

> "The Council of the Institute of Chartered Accountants of Bangladesh (ICAB) has decided to adopt the
> International Financial Reporting Standards (IFRS) and IFRS for SMEs and **to publish IFRS (instead
> of BFRS) and IFRS for SMEs (instead of BFRS for SMEs) which will be effective for annual periods
> beginning on or after 1 January 2018**."

ICAB signed the supply agreement with the IFRS Foundation on 25 September 2017.
https://www.icab.org.bd/icabadmin/uploads/ckeditor/7869Circular%20for%20Adoption%20&%20Publication%20of%20IFRS%20and%20IFRS%20for%20SMEs.pdf

**So standards are cited in Bangladesh today by their international names — IFRS, IAS, IFRIC, SIC,
IFRS for SMEs. The "BAS 1 / BFRS 15" style is legacy.** It is not wrong in a historical sense, and
older financial statements will use it, but a 2026 set of accounts should not.

### Who sets them now — the FRC

| Provision / instrument | Effect |
|---|---|
| **FRA 2015 s.40(1)** | The Council **shall** make and issue (a) **Financial Reporting Standards consistent with the IAS issued by the IASB**, and (b) **Auditing Standards consistent with the ISAs** and the IAASB's assurance and ethics pronouncements |
| **FRA 2015 s.40(4)** | The Council **may make a separate simplified financial reporting framework and standards for small and medium-sized entities**, consistent with international good practice |
| **FRA 2015 s.41** | The Council may **exempt small entities** from the simplified standard |
| **FRA 2015 s.43** | Standards must be pre-published for **60 days** of comment on the FRC website, plus notice on **3 consecutive days in one Bangla and one English national daily** |
| **FRA 2015 s.69** (transitional) | Standards adopted by the professional accountancy body remain in force **as if made under this Act** until the Council makes its own |
| **FRC Notification 146/FRC/Proshashon/Prokgapon/2020/67, 2 November 2020** | **Adopted under s.40 for all PIEs registered in Bangladesh:** the Conceptual Framework; **IAS 1, 2, 7, 8, 10, 12, 16, 19, 20, 21, 23, 24, 26, 27, 28, 29, 32, 33, 34, 36, 37, 38, 39, 40, 41**; **IFRS 1–17**; **SIC 7, 10, 25, 29, 32**; **IFRIC 1, 2, 5, 6, 7, 10, 12, 14, 16, 17, 19, 20, 21, 22, 23**; and **IFRS for SMEs**. Under FRA s.44 all PIEs shall comply |
| **FRC Notification 132/FRC/SS/Prokgapon/2021/199, 4 November 2021** | Adopted the **ISAs** issued by the IAASB and the **IESBA Code of Ethics** |
| **FRC, 25 April 2024** | Financial Reporting Framework for **Statutory Public Authorities** |
| **FRC, 2024** | Adopted **International Valuation Standards (IVS)** |
| **FRC 2026 notifications** | **IFRS 18 and IFRS 19 adopted — mandatory for financial years beginning on or after 1 January 2027**; **IFRS S1 and S2 (sustainability) permitted**; and four **prescribed auditor's report formats**, **mandatory for financial years ending 31 December 2026 or later**, whose signature block ends with a mandatory `DVC: ______` line |

**Income tax cross-references.** **ITA 2023 s.72(4)**: a **company** shall maintain accounts and
prepare financial reports in accordance with **IAS, IFRS and IFRS for SMEs** and the relevant laws in
force in Bangladesh ("IFRS for SMEs" inserted by Act 89 of 2026 s.55). **ITA 2023 s.73(4)**: a
**developer or real estate developer** shall follow all conditions of IFRS and shall record revenue in
accordance with **IFRS 15**.

> ### ⚠️ [UNCONFIRMED] Which SMEs and non-PIEs must apply IFRS for SMEs rather than full IFRS
>
> **No FRC instrument setting quantified applicability criteria was found.** FRC adopted IFRS for SMEs
> in **November 2020 for PIEs** — that notification is about PIEs, not about SMEs — and **FRA ss.40(4)
> and 41** empower a separate simplified framework with small-entity exemptions that the Council **has
> not yet exercised in any located instrument**. The IFRS Foundation's Bangladesh profile (September
> 2020) records the position as **"under review, not yet finalised"**, and nothing later was located.
>
> **So there is no Bangladeshi rule that says "a company with turnover under X applies IFRS for
> SMEs".** What binds a company is **ITA 2023 s.72(4)**, which names IAS, IFRS *and* IFRS for SMEs
> together without allocating between them, and — for a PIE — the FRC's November 2020 adoption. **In
> practice the choice is made by the company and its auditor.** Say that, and do not manufacture a
> threshold.

---

## 10. DVS and the DVC — why every audit report carries a code

| Element | Detail |
|---|---|
| System | **Document Verification System (DVS)**, built by **ICAB jointly with NBR** |
| Portal | https://dvs.icab.org.bd |
| Who generates a DVC | The **practising ICAB member (Certificate of Practice holder)** who signs the audit report, before signing |
| Where it goes | **Printed on the audit report / audited financial statements next to the auditor's signature** |
| Format | **18 characters — 16 digits plus 2 letters.** From the one published specimen `2202241468AS244600`: `220224` = signing date YYMMDD, `1468` = the partner's ICAB enrolment number, `AS` = an undocumented two-letter component, `244600` = sequence. ⚠️ **This decode rests on a single observed specimen; ICAB publishes no format specification** |

**Mandatory since 1 December 2020.** DVS launched **12 November 2020** with the NBR–ICAB MoU signed
the same day. **ICAB Circular Ref 1/1/ICAB-2020/DVS/001** of **24 November 2020** states verbatim that
*"all audit reports **signed on Dec 01, 2020 and onwards must have the Document Verification Code (DVC)
along with the auditor's signature**… **Without mentioning Document Verification Code (DVC), audited
financial statement signed by any practicing member shall be considered as invalid document.**"*
**Management audit and internal audit are carved out.** **NBR Special Order
08.01.0000.030.06.009.20.178** of **26 November 2020** directs that for **all** audited financial
statements filed by company-class taxpayers the **DCT shall verify the DVC at dvs.icab.org.bd**;
where verification shows the statement is **not certified by a Chartered Accountant, i.e. fake**, or
lacks the signatures of an adequate number of directors, the DCT shall **reject the purportedly
audited statement**; the DCT records the auditor's name, the certification date, the DVC and the
signing directors' names **at the head of the assessment order**; and it does not apply to statements
certified before 1 December 2020. **[PRIMARY]**

> **What NBR rejects is the audited accounts, not the return.** The DCT disregards the financial
> statements and proceeds under the method-of-accounting power — the gateway to computing income on a
> basis the DCT determines. That is a much worse outcome for the taxpayer than a late-filing penalty.

**The DVC obligation is administrative, not statutory.** The authentic English text of the Income Tax
Act 2023 contains **zero occurrences of "DVS", "DVC" or "verification code"**. The obligation rests on
the NBR special order, the ICAB circular, regulator MoUs and now the FRC's prescribed report format.
The statutory hooks are **s.169(2)(b)** ("evidence of compliance with the standards prescribed by the
Board, **for verification**"), ss.72–73, and the penalties in ss.273, 274 and 316. **No replacement NBR
special order re-issued under the ITA 2023 was found.**

**The first instrument that hard-codes the DVC into a prescribed format** is **FRC Notification
360/FRC/Prosha/Ain o Bidhi/2026/1349 of 18 August 2026** — four prescribed auditor's report formats
ending with a mandatory `DVC: ______` line, mandatory for financial years ending **31 December 2026**
or later.

> ⚠️ **[UNCONFIRMED] Whether RJSC requires a DVC on s.190 filings.** No RJSC notice, circular,
> reference number or commencement date was found, and no RJSC page fetched mentions DVC or DVS. The
> only verified RJSC link is the **22 December 2024** integration with the Name Clearance Portal,
> which ICAB describes as company data flowing **from RJSC into DVS** — a data lookup, not a filing
> gate. The proposition is widely asserted on advisory blogs; treat it as unproven. **The practical
> effect is nonetheless strong but indirect:** an audit report signed without a DVC is invalid under
> ICAB's own rules, so accounts filed under s.190 will carry one because the **auditor** must.

> ⚠️ **A commonly mis-cited instrument.** FRC Notification **146/FRC/SS/Prokgapon/2020/71** of
> 21 December 2020 concerns the **format of the auditor's signature** on PIE audit reports. **It does
> not mention DVS or DVC at all.** Do not cite it as a DVC instrument.

> ⚠️ **[UNCONFIRMED]** A Bangladesh Bank DVS circular reportedly issued **6 July 2021** could not be
> located — number, department and wording unconfirmed. By contrast **BRPD Circular Letter No. 04 of
> 4 January 2021 IS verified** (banks must obtain and preserve the CA-audited statutory audit report
> when approving or renewing a loan to a PIE) — but **it does not mention DVS or DVC**. **BSEC** has
> only a Letter of Intent with ICAB (10 March 2021), no notification. **BIDA and MRA** appear only in
> ICAB's own list of DVS users, with no instrument found for either.

> ⚠️ **No published ICAB fee for generating a DVC was found** anywhere. Commentary about "rising audit
> fees after DVS" refers to **firms' fees to their clients**, not an ICAB charge. Do not conflate the
> two.

**Consequences of a missing DVC:** *professional* — the audited FS "shall be considered as invalid
document" (ICAB Circular DVS/001); *tax* — the DCT rejects the audited FS, with penalties under ITA
2023 **s.273** (CA: Tk 50,000–200,000), **s.274** (taxpayer: Tk 100,000) and **s.316** (criminal);
*banking* — statements without a valid DVC cannot be relied on in loan files; *disciplinary* — ICAB
Council suspends DVS access and DVC generation as a sanction.

---

## 11. Retention periods at a glance

**The income-tax retention rule is new.** **ITA 2023 s.72A** — *"হিসাব, দলিল, বিল-ভাউচার, ইত্যাদি
সংরক্ষণের মেয়াদ ও পদ্ধতি"* — was **INSERTED by the Finance Act 2026 (Act 96 of 2026) s.58, with effect
from 1 July 2026**: **[PRIMARY]**

> The accounts, documents, supporting documents, bills-vouchers, statements, invoices or documents
> relating to accounts of the income of any business, class of business or other source —
> **(a) shall be preserved: for ALL COMPANIES, for the period mentioned in the Companies Act 1994; and
> for ALL TAXPAYERS OTHER THAN COMPANIES, for 6 (SIX) YEARS; (b) may be preserved in ANALOGUE form or
> in DIGITAL form in accordance with the Information and Communication Technology Act 2006 (Act 39 of
> 2006), or in both.**

**The cross-reference resolves to twelve years** — Companies Act s.181(5). Note limb (b): **digital
retention is expressly permitted**, so a scanned-and-indexed archive satisfies the income-tax rule.

| Regime | Period | Provision |
|---|---|---|
| **Companies Act 1994 — all companies** | **12 years** (books **and vouchers**), or the whole period since incorporation if shorter | **s.181(5)** |
| **Income tax — companies** | **The Companies Act period, i.e. 12 years** | **ITA 2023 s.72A(a)** |
| **Income tax — non-companies** | **6 years** | **ITA 2023 s.72A(a)** |
| **VAT — all registered / enlisted persons** | **5 years**, and notwithstanding that, documents relating to any **unresolved proceeding until it is disposed of** | **VAT Act 2012 s.107(1), (3)** |
| **VDS withholding documents** | at least **5 years** | VDS Rules |
| **Transfer pricing records** | as prescribed by rules (the Board may prescribe the period) | **ITA 2023 s.237** |

> ⚠️ **A deliberate mismatch, to be managed conservatively.** The regimes prescribe 12 / 6 / 5 years,
> while **ITA 2023 s.212(4) proviso** allows undisclosed income, expenses or assets **older than six
> years** to be deemed to relate to the sixth preceding year, and s.212 proceedings are not otherwise
> time-limited. **The safe operating rule for a company is 12 years for everything** — one retention
> policy, not three.

---

## 12. Cash-basis reality vs the accrual requirement

Nothing in the Companies Act permits a company to keep cash-basis books: s.181(2) requires a **true and
fair view** and a **sufficient explanation of transactions**, s.183(3) requires an **audit**, and
s.72(4) of the ITA 2023 requires **IAS / IFRS / IFRS for SMEs**. An SME that records only bank and cash
movement through the year and reconstructs receivables, payables, accruals and stock at year end is not
keeping the books the Act requires — it is producing a year-end estimate that an auditor is then asked
to certify.

The practical consequence sits in three places at once: the auditor's report (s.183(3)), the Chartered
Accountant's personal penalty exposure under **ITA s.273**, and the DCT's power to reject the accounts
and assess on his own basis when the audited statements do not stand up (§10). **The year-end should be
a report on books that already exist, not a reconstruction.** That is the single most useful thing
TakaBooks can tell a Bangladeshi SME about bookkeeping standards.

---

## Still open — do not let these harden into answers

1. **No express Bangla-or-English language requirement for books of account** was found in any of the
   three statutes. State the negative; do not repeat the folklore. §2.
2. **No express currency requirement** that accounts be kept in Taka. §2.
3. **No standing FRC deadline** for a PIE to file audited FS with the Council — do not state 90 or 120
   days. §8.
4. **No FRC instrument sets IFRS-for-SMEs applicability criteria.** §9.
5. **Whether RJSC requires a DVC on s.190 filings** — unproven. §10.
6. **Whether RJSC's per-year late fee is additive to, or replaces, the Tk 200 base fee.** §5.
7. **Whether RJSC online filing is mandatory**, and whether a digital signature certificate is needed.
   §5.
8. **No annual-accounts deadline for a foreign company** in the Act; s.379(3)'s prescribing rule was
   not located. §3.
9. **Trade Organisation Rules 2025** content could not be extracted (font-subset issue in the PDF);
   any periodic return under the Trade Organisation Act 2022 / Rules 2025 is **unresearched**.
10. **Current state of the IFRS roadmap for banks and NBFIs** — whether Bangladesh Bank has withdrawn
    its IFRS departures is unverified; FRC's November 2025 presentation is silent.
11. **Review by a Bangladeshi Chartered Accountant** has not happened for this file.

**Figures corrected in this file that a user is likely to bring you wrong:** the s.73 audit thresholds
(**10 crore / 5 crore**, not 10m / 5m — §7); the FRC public-interest-entity thresholds (**Tk 50cr /
30cr / 10cr**, not 5cr / 3cr / 1cr — §8); the RJSC company late fee (**Tk 500 or Tk 700 per year**,
not Tk 2/day capped at Tk 1,000 — §5); the Form XII deadline (**14 days**, not 15 — §4); and
**"Form 118", which does not exist** (§4).

**Primary sources named in this file** — Companies Act 1994 (Bangla, authoritative):
http://bdlaws.minlaw.gov.bd/act-788.html · Financial Reporting Act 2015:
http://bdlaws.minlaw.gov.bd/act-print-1169.html · Income Tax Act 2023:
http://bdlaws.minlaw.gov.bd/act-details-1429.html · Finance Act 2026 (Act 96 of 2026) gazette:
https://nbr.gov.bd/uploads/acts/Finance_Act_2026.pdf · FRC instruments index:
https://frc.gov.bd/pages/static-pages/6922dece933eb65569e1d7f8 · FRC auditor enlistment:
https://enlistment.frc.gov.bd/ · RJSC fee schedule:
https://roc.gov.bd/pages/static-pages/6922dc05933eb65569e0dfb6 · RJSC portal: https://app.roc.gov.bd ·
ICAB DVS portal: https://dvs.icab.org.bd

---
Maintained by Moshiur Rahman (@bemoshiur) · TICON SYSTEM LTD — https://ticonsys.com · MIT
