# Income tax — আয়কর

**Current as of:** 6 September 2026 (figures researched to 5 September 2026).
**Assessment year:** **করবর্ষ / AY 2026-27**, assessing **আয়বর্ষ / income year 1 July 2025 – 30
June 2026**. For banks, insurance companies and finance companies the income year is
1 January – 31 December 2025. Machine-readable figures live in
`src/data/rates-AY2026-27.toml`; **that file is authoritative and this document mirrors it.**
Change them together or they will drift apart.
**Governing law:** আয়কর আইন, ২০২৩ / Income Tax Act 2023 (Act 12 of 2023) as amended by
**অর্থ আইন, ২০২৬ / Finance Act 2026 (Act No. 96 of 2026)** — presidential assent and publication
in the *Bangladesh Gazette, Extraordinary* on **30 June 2026**, effective **1 July 2026**. The
Finance Act 2026 legislates income tax rates for **five assessment years, AY 2026-27 to
AY 2030-31** — the first time Bangladesh has done so.
**Status:** RESEARCHED AND LANDED for AY 2026-27, **not professionally reviewed.** Most figures
below were read from NBR's own primary text; the remainder rest on professional summaries and are
marked ⚠️ in every place they appear.

> ### ⚠️ This is not professional advice
>
> TakaBooks is bookkeeping and taxation software, not a tax adviser. Nothing in this file is
> professional advice, and nothing computed from it may be filed with NBR without review.
> **Have a Bangladeshi Income Tax Practitioner (ITP) or Chartered Accountant check any return
> before it is submitted.** Where this document says a figure is unverified, say so to the user —
> do not present it as settled.

## Sources and how to read the markers

Every figure below carries one of two markers. **Never quote a ⚠️ figure without its warning.**

| Marker | Meaning |
|---|---|
| ✅ | Read from **primary text** — NBR's own **আয়কর পরিপত্র ২০২৬-২০২৭** (Income Tax Paripatra 2026-27), a gazetted SRO, or the enacted statute on bdlaws. |
| ⚠️ | Read from a **post-enactment professional summary** only. **The Finance Act 2026 gazette PDF is typeset in a legacy Bijoy-family Bangla font whose glyphs map to ASCII, so its Schedules could not be text-extracted.** Where three independent firms agree, the figure is probably right — but it has not been checked against enacted text, and this document will not pretend otherwise. |

| Key | Source |
|---|---|
| **[PARI]** | NBR, **আয়কর পরিপত্র ২০২৬-২০২৭** (Income Tax Paripatra 2026-27), file no. 08.01.0000.000.030.03.029.26.112, dated **2 September 2026** — https://nbr.gov.bd/uploads/paripatra/আয়কর_পরিপত্র_২০২৬-২০২৭.pdf |
| **[ACT]** | আয়কর আইন, ২০২৩ on bdlaws, current through the Finance Act 2026 — http://bdlaws.minlaw.gov.bd/act-details-1429.html |
| **[FA2026]** | অর্থ আইন, ২০২৬ (Act 96 of 2026) gazette PDF — https://nbr.gov.bd/uploads/acts/Finance_Act_2026.pdf *(body text not machine-readable)* |
| **[PwC]** | PwC Bangladesh, *Finance Act, 2026: Key Amendments* (June 2026) — https://www.pwc.com/bd/en/assets/pdfs/budget/finance-act-2026-key-amendments.pdf |
| **[PwC-WWTS]** | PwC Worldwide Tax Summaries — Bangladesh, reviewed 31 July 2026 — https://taxsummaries.pwc.com/bangladesh/corporate/taxes-on-corporate-income |
| **[KPMG]** | KPMG Bangladesh / Rahman Rahman Huq, *Bangladesh Tax 2026* (16 July 2026) — https://assets.kpmg.com/content/dam/kpmg/bd/pdf/Tax/Bangladesh_Tax_2026.pdf |
| **[TNP]** | Tuhin & Partners, *The Finance Act 2026: A Practitioner's Guide* (July 2026) — https://tnp.legal/wp-content/uploads/2026/07/TNP_Finance_Act_2026_Briefing.pdf |

## Four traps that make most published FY2026-27 charts wrong

1. **Budget-day reporting quotes the Finance *Bill*, not the Act.** News coverage of 11 June 2026
   gives a general threshold of Tk 375,000, Tk 425,000 for women and seniors, Tk 500,000 for
   persons with disability. **Parliament raised every band by one step before passing the Act.**
   The enacted figures are 400,000 / 450,000 / 525,000. ✅ [PARI §1.1]
2. **The location-based minimum tax is abolished.** The Tk 5,000 / 4,000 / 3,000 scale by area no
   longer exists. It is a **flat Tk 5,000** (Tk 1,000 for new taxpayers). ✅ [PARI §1.1]
3. **The top rate for AY 2026-27 is 30%, not 35%.** The 35% band first applies in **AY 2028-29**.
   A chart showing 35% for this year has read the wrong column of the five-year card. ✅ [PARI §1.1]
4. **Withholding tax rates come from SRO 273 of 5 July 2026, not SRO 210 of 8 June 2026.** Two
   SROs carry the identical title উৎসে কর বিধিমালা, ২০২৬; SRO 210 was repealed by Rule 14 of
   SRO 273. See `src/references/withholding-tds-vds.md`.

---

## 1. Individual slab rates — AY 2026-27 ✅

আয়কর আইন, ২০২৩ read with Finance Act 2026 Schedule 2, reproduced at [PARI §1.1]. Applies to
every resident individual, every Hindu Undivided Family (হিন্দু অবিভক্ত পরিবার) and every
non-resident Bangladeshi.

| Slice of total income | Rate |
|---|---|
| Up to the taxpayer's tax-free threshold (§2 below) | **0%** |
| Next Tk 300,000 | **10%** |
| Next Tk 400,000 | **15%** |
| Next Tk 500,000 | **20%** |
| Next Tk 2,000,000 | **25%** |
| Balance | **30%** |

The slab **widths** are the same for every taxpayer category. Only the width of the nil slab — the
tax-free threshold — changes.

**Worked example (general taxpayer, total income Tk 1,000,000):** 400,000 @ 0% = 0; 300,000 @ 10%
= 30,000; the remaining 300,000 @ 15% = 45,000. **Tax before rebate = Tk 75,000.**

**The five-year rate card.** ✅ [PARI §§1.1–1.3] The Finance Act 2026 fixed rates through
AY 2030-31. TakaBooks models AY 2026-27 only; the later years are recorded here so a maintainer
does not have to re-research them.

| | AY 2026-27 & 2027-28 | AY 2028-29 & 2029-30 | AY 2030-31 |
|---|---|---|---|
| Nil band (general taxpayer) | 400,000 | 450,000 | 500,000 |
| 10% / 15% / 20% / 25% bands | 300k / 400k / 500k / 2,000k | same | same |
| 30% | **balance (top rate)** | next 26,350,000 | next 26,300,000 |
| 35% | **does not exist** | remainder | remainder |

**Two kinds of income never touch this table:** ✅ [PARI §§1.1, 1.4]

- **Tobacco manufacturing.** Income from manufacturing cigarettes, bidi, zarda, gul or any tobacco
  product is excluded from the slab table *irrespective of the taxpayer's status*, and is taxed at
  **45%**. A sole trader in that business does not get the slabs.
- **Non-residents who are not non-resident Bangladeshis.** A non-resident who is not a company,
  firm or association of persons pays a **flat 30% with no threshold and no slabs**.

---

## 2. Tax-free threshold by taxpayer category ✅ [PARI §1.1]

করমুক্ত আয়সীমা. The whole table is primary-verified.

| Category | AY 2026-27 threshold |
|---|---|
| General taxpayer / সাধারণ করদাতা | **Tk 400,000** |
| Female taxpayer / নারী করদাতা | **Tk 450,000** |
| Senior citizen, aged **65 or above** / ৬৫ বছর বা তদূর্ধ্ব | **Tk 450,000** |
| Person with disability / প্রতিবন্ধী ব্যক্তি | **Tk 525,000** |
| Third gender taxpayer / তৃতীয় লিঙ্গের করদাতা | **Tk 525,000** |
| Gazetted war-wounded freedom fighter / গেজেটভুক্ত যুদ্ধাহত মুক্তিযোদ্ধা | **Tk 550,000** |
| **Gazetted "July fighter"** injured in the July 2024 uprising / গেজেটভুক্ত জুলাই যোদ্ধা | **Tk 550,000** |
| Non-resident individual who is not a non-resident Bangladeshi | **no threshold** — flat 30% |

**The "July fighter" (জুলাই যোদ্ধা) band is new.** [PARI §1.1] item 3 names war-wounded gazetted
freedom fighters and gazetted July fighters in the *same* band. Gazetted status is the test. A
person answering both descriptions gets Tk 550,000 once, not twice.

### Parent or legal guardian of a person with disability — an ADDITION, not a replacement ✅

[PARI §1.1]: *"কোনো প্রতিবন্ধী ব্যক্তির পিতামাতা বা আইনানুগ অভিভাবকের প্রত্যেক প্রতিবন্ধী
সন্তান/পোষ্যের জন্য করমুক্ত আয়ের সীমা ৫০,০০০ টাকা বেশি হবে।"*

- **Tk 50,000 is ADDED** to whatever threshold otherwise applies to that taxpayer.
- It is granted **for each** disabled child or dependant, so two disabled children means
  Tk 100,000.
- **Where both parents are taxpayers, only one of them may claim it.**

So a general taxpayer with one disabled child has a threshold of Tk 450,000; a **woman** with one
disabled child has Tk 500,000, not Tk 450,000. TakaBooks exposes a
`parent_or_guardian_of_person_with_disability` category holding the **general-taxpayer case only**
(400,000 + 50,000 = 450,000) and marks it unverified precisely because it is a derived convenience
figure. Compute the other combinations by hand.

**Not sourced:** the date on which age is tested for the 65+ band, the certification required to
claim the person-with-disability band, and how long a taxpayer counts as "new" for the reduced
minimum tax. NBR practice exists for all three; none of it is in the text read here. Ask the tax
circle.

---

## 3. Minimum tax — ন্যূনতম কর ✅ [PARI §1.1]

| | AY 2026-27 | AY 2025-26 (repealed) |
|---|---|---|
| Taxpayer whose total income exceeds the tax-free threshold | **Tk 5,000, anywhere in Bangladesh** | Tk 5,000 Dhaka/Chattogram city corporations · Tk 4,000 other city corporations · Tk 3,000 elsewhere |
| **New / first-time taxpayer** | **Tk 1,000** | Tk 1,000 |

**The location split is gone.** Guides still publishing the three-tier scale for AY 2026-27 are out
of date, and TakaBooks has deliberately deleted the old tier ids so `--location other_area` now
fails loudly rather than quietly returning a stale figure.

**The floor bites even when the rebate wipes the liability out.** [PARI §1.1]: *"…বিনিয়োগজনিত কর
রেয়াত বিবেচনার পর প্রদেয় আয়করের পরিমাণ ন্যূনতম আয়করের চেয়ে কম, শূন্য বা ঋণাত্মক হলেও তাকে
প্রযোজ্য ন্যূনতম আয়কর পরিশোধ করতে হবে"* — if tax after rebate is less than, equal to, or below
zero, the minimum tax is still payable. It does **not** apply to a taxpayer whose income is at or
below the threshold.

---

## 4. Surcharge — now TWO separate levies

The Finance Act 2026 split the single old concept into a **tax (wealth) surcharge** and a new
**environmental surcharge** (ITA 2023 ss.2(14), 2(21), 2(86Kha)). There are also two 2.5%
additions on particular income. All four are separate charges; more than one can apply at once.

### 4.1 Wealth surcharge ✅ [PARI §1.6]

Charged **on the income tax**, not on the wealth. Net wealth means the total acquisition value of
net assets shown in the statement of assets and liabilities under **ITA 2023 s.167**.

| Net assets / trigger | Surcharge |
|---|---|
| Up to Tk 4 crore (40,000,000) | **Nil** |
| Above Tk 4 crore to Tk 10 crore; **OR** ownership of **more than one motor car** in own name; **OR** ownership of house property exceeding **8,000 sq ft** in aggregate within a city corporation area | **10%** |
| Above Tk 10 crore to Tk 20 crore | **20%** |
| Above Tk 20 crore to Tk 50 crore | **30%** |
| Above Tk 50 crore | **35%** |

> ### ⚠️ TakaBooks tests net wealth only
>
> The 10% band has **three alternative triggers** and the engine checks only the first. A taxpayer
> with modest net assets but **two cars**, or a **large flat in a city corporation**, owes 10% and
> TakaBooks will not detect it. **Ask the user about cars and floor area.**

**"Motor car" excludes** bus, minibus, coaster, prime mover, truck, lorry, tank lorry, dump truck,
covered van, cargo van, pickup van, human hauler, tractor, maxi or auto rickshaw, crane, excavator,
bulldozer, roller, concrete mixer, heavy motor vehicle, taxicab and motorcycle.
✅ [PARI §1.6, explanation (2)]

> ### ⚠️ Which figure the percentage multiplies is not exactly modelled
>
> [PARI §1.6] charges surcharge on *"করযোগ্য আয়ের উপর … কর হার প্রয়োগ করিয়া পরিগণিত অঙ্কের
> উপর"* — the amount produced by applying the Schedule 2 rates to **taxable income**, i.e. the tax
> **before** the investment rebate. TakaBooks can only charge it on tax **after** rebate. For a
> taxpayer who claims a rebate *and* is in a surcharge band, TakaBooks may therefore compute a
> **slightly lower** surcharge than a literal reading gives. Have such a case checked.

### 4.2 Environmental surcharge — per motor car in excess of one ✅ [PARI §1.7]

**New.** Payable by an individual who owns more than one motor car, for **each car in excess of
one**, per year, as a flat taka amount. It is due whether or not any wealth surcharge is payable.

| Engine capacity | Surcharge per car per year |
|---|---|
| Up to 1,500 cc | **Tk 25,000** |
| Above 1,500 cc up to 2,000 cc | **Tk 50,000** |
| Above 2,000 cc up to 2,500 cc | **Tk 75,000** |
| Above 2,500 cc up to 3,000 cc | **Tk 150,000** |
| Above 3,000 cc up to 3,500 cc | **Tk 200,000** |
| Above 3,500 cc | **Tk 350,000** |

The same vehicle exclusions as §4.1 apply. ⚠️ **Which car is the exempt one is not settled:**
[KPMG p.48] and [TNP p.26] say the car attracting the *lowest* surcharge is exempt; [PARI §1.7]
says only "each car in excess of one" and does not identify it. The difference matters only when
the cars sit in different capacity bands.

### 4.3 The two 2.5% additions ⚠️

| Trigger | Rate | Source |
|---|---|---|
| Income of manufacturers of tobacco products (cigarette, bidi, zarda, gul) | 2.5% | ⚠️ [KPMG p.19]; [TNP p.25] |
| Income of an educational institution failing to provide legally required accessibility for persons with disabilities | 2.5% | ⚠️ [TNP p.25] — **single source, uncorroborated** |

Neither appears in the Paripatra rate excerpt held here. Confirm against Finance Act 2026
Schedule 2 before charging either.

---

## 5. Investment tax rebate — ITA 2023 s.78 ⚠️ (REDUCED by the Finance Act 2026)

**Rebate = the LOWEST of the three limbs.** ⚠️ [KPMG p.47]; [PwC p.6]; [TNP p.12] — three agreeing
summaries, but **not read from enacted text.**

| Limb | AY 2026-27 | AY 2025-26 |
|---|---|---|
| (a) Percentage of total taxable income | 3% | 3% |
| (b) Percentage of the eligible investment actually made | **10%** *(cut from 15%)* | 15% |
| (c) Absolute ceiling on the rebate itself | **Tk 750,000** *(cut from Tk 1,000,000)* | Tk 1,000,000 |

The 3% limb is computed on total taxable income **excluding** income that is exempt, taxed at a
reduced rate or taxed as final tax, and excluding a share of income from a firm or association of
persons. TakaBooks applies it to whatever income figure the user supplies — **reduce the income
before running the calculation if any of those apply.**

**Practical effect of the cut:** a taxpayer must invest roughly 50% more to obtain the same rebate,
and a top-bracket taxpayer loses up to Tk 250,000 of maximum rebate. [TNP p.12]

**Worked example:** total income Tk 1,000,000, eligible investment Tk 200,000 → lowest of
(3% × 1,000,000 = 30,000), (10% × 200,000 = **20,000**), (750,000) = **Tk 20,000 rebate.**

**Two true consequences of the limbs, useful when advising:** investing more than **30% of taxable
income**, or more than **Tk 7,500,000**, buys no additional rebate (10% × 30% = the 3% limb;
10% × 7,500,000 = the Tk 750,000 ceiling). Those two numbers are how `rates-AY2026-27.toml`
parameterises the rebate for the engine — **they are derived, and must not be quoted to a taxpayer
as statutory figures.** Quote 3% / 10% / Tk 750,000.

### Eligible investments — Sixth Schedule Part 3 ⚠️ [KPMG p.47] unless noted

- Life insurance premium.
- Contribution to a provident fund, both employee and employer contribution. ⚠️ **New under the
  Finance Act 2026: the fund must be a *recognised* provident fund** — "approved" is no longer
  enough. [PwC p.6]
- Deposit pension scheme / monthly savings scheme with a scheduled bank or financial institution,
  **maximum Tk 120,000**.
- Investment in **government securities, maximum Tk 500,000**.
- Unit certificates, mutual funds, ETFs and collective investment scheme units, including
  certificates of finance companies, asset managers, fund managers and ICB. ⚠️ **The Tk 500,000 cap
  on this category has been REMOVED by the Finance Act 2026** — charts still showing it are out of
  date.
- Any new sum invested in shares of a listed company.
- Donation to a national-level institution set up in memory of the Liberation War.
- Donation to a government-approved public welfare or educational institution.
- Donation to a Zakat Fund or a charitable fund under the Zakat Fund; the Finance Act 2026 added
  the **Centre for Zakat Management**.
- Donations to **eleven named charities**, 1 July 2026 – 30 June 2030, under SRO
  213-AIN/Income Tax-4/2026: ASHIC Foundation for Childhood Cancer; Bangladesh Cancer Aid Trust
  (BANCAT); Al-Markazul Islami; Disabled Child Foundation; Sherpur Diabetic Association;
  Mawna/Magura Diabetic Association *(⚠️ sources differ on this name)*; Bangladesh Thalassemia
  Society; Autism Welfare Foundation; BRAC; Ramakrishna Math and Ramakrishna Mission, Dhaka;
  Chattogram Maa-O-Shishu Hospital. The SRO itself was not read.

> ### ⚠️ New clawback
>
> Where a rebate-earning investment — notably a **deposit pension scheme** or **government
> securities** — is encashed before the prescribed holding period, the rebate previously allowed is
> charged back as **additional tax, pro-rated, in the year of encashment**. [PwC p.6]; [TNP p.22]

---

## 6. Capital gains and dividends ⚠️ [KPMG p.52] unless noted

| Taxpayer / asset | Rate |
|---|---|
| Companies, trusts and associations of persons — all capital assets | 15% |
| Individual — shares of a listed company | 15% |
| Individual — other assets held **more than 5 years** | 15% |
| Individual — other assets held **5 years or less** | **ordinary slab rate** |
| Individual — gold, silver, precious metals, diamonds, coins (traders excluded) | **5%, final** (Seventh Schedule) — also [TNP p.22]; [PwC p.6] |
| Landowner receiving cash and/or constructed units from a developer under a specified contract | 15% on total benefits less land acquisition cost, payable in **three equal annual instalments** (s.58(3)) — [TNP p.10] |
| **Dividend income of an individual** | **15% flat, final** (Seventh Schedule) — [TNP p.22]; [PwC p.5] |

**Exclusion:** capital gains **up to Tk 5,000,000** on transfer of shares or units of a listed
company, or of any BSEC-approved fund, are excluded from income — but **only for persons other
than sponsors, directors and placement shareholders**. [KPMG p.49]

**The definition of a capital asset was widened (s.2(77))** to include personally held gold, silver
and other precious metals, gold and silver ornaments, gems, diamonds, coins, paintings, antiques,
digital coins and **club memberships**. Business inventory and a vehicle for personal use remain
outside. [TNP p.7]; [KPMG p.52]; [PwC p.6]

**Firm-to-company conversion (s.61(4)-(6))** is now expressly exempt on four conditions: all assets
and liabilities transfer; partners become shareholders in the same capital proportions; partners
receive no consideration other than shares; and the existing partners retain at least 50% of voting
power for five years. Breach withdraws the exemption. [TNP p.10]

---

## 7. Corporate and other-entity rates — AY 2026-27 to AY 2030-31

### 7.1 Companies ✅ [PARI §1.5]

| Company | Standard | With banking-channel compliance |
|---|---|---|
| Publicly traded, **at least 10%** of paid-up capital transferred through IPO, direct listing, rights issue or RPO | **22.5%** | **20%** |
| Publicly traded, **less than 10%** so transferred | **25%** | **22.5%** |
| **Non-publicly traded** — every other company defined in the ITA 2023 | **27.5%** | **25%** |
| Publicly traded bank, insurer or finance company (**merchant banks excluded**) | **37.5%** | not available |
| Non-publicly traded bank, insurer or finance company | **40%** | not available |
| Company manufacturing tobacco products | **45%** *(+ 2.5% surcharge ⚠️)* | not available |
| Publicly traded mobile phone operator (became listed by transferring ≥10% through the stock exchange, pre-IPO placement not exceeding 5%) | **40%** | see rebate below |
| Non-publicly traded mobile phone operator | **45%** | not available |

**Mobile operator IPO rebate** ✅ [PARI §1.5]: a mobile phone operator that transfers **at least
20%** of paid-up capital through IPO gets a **10% rebate on the income tax applicable in the year
of that transfer** — a rebate on the tax, not a 10% rate.

**27.5% is the rate most TakaBooks users need**: an ordinary Bangladeshi private limited company
that is not listed.

### 7.2 Other entities ✅ [PARI §1.4]

| Taxpayer | Rate |
|---|---|
| Firm, association of persons, artificial juridical person, **trust** | **27.5%** |
| Co-operative society registered under the Co-operative Societies Act 2001 | **20%** |
| Private university; private medical, dental or engineering college; private college teaching only IT subjects | **5%** *(cut from 15%)* |
| Taxpayer that is **not a company** but manufactures tobacco products | **45%** |
| Non-resident (not a non-resident Bangladeshi) that is not a company, firm or AOP | **30%** |

This settles an old open question: **the individual slabs do not apply to a firm or an association
of persons.** They pay a flat 27.5%.

### 7.3 The banking-channel ("cashless") condition — ⚠️ the most commercially material open question

The 2.5-percentage-point reduction is available to **general companies only** (the first three rows
of §7.1) — the Paripatra marks the conditional column *শর্ত প্রযোজ্য নয়* ("condition not
applicable") for banks, insurers, finance companies, tobacco manufacturers and non-listed mobile
operators. [KPMG p.19] confirms both listed and non-listed general companies may take it.

**What the condition says** ✅ [PARI §1.5], stated below the rate table:
*"শর্ত: বিবেচ্য আয়বর্ষে সকল ধরনের লেনদেন ব্যাংক ট্রান্সফারের মাধ্যমে সম্পন্ন করতে হবে"* — in the
income year concerned, **all kinds of transactions** must be completed through bank transfer.
[PwC-WWTS] states it as two limbs with no threshold: *all transactions to be undertaken through
bank transfer*, and *all income is received through bank transfer*. **A single non-compliant cash
transaction forfeits the reduced rate for the entire year.** [TNP p.24]

> ### ⚠️ Do the old Tk 500,000 / Tk 3,600,000 de-minimis thresholds survive? UNCONFIRMED.
>
> Under the pre-Finance-Act-2026 rule only a **single transaction above Tk 500,000** or an **annual
> aggregate above Tk 3,600,000** had to be routed through banking channels. Secondary commentary
> still repeats those figures for FY2026-27. PwC and KPMG state the condition with **no
> threshold**, and KPMG flags the move to "**all** transactions" as the change the Finance Act 2026
> made — but **the enacted Schedule 2 condition could not be read**, and a one-line Paripatra
> summary is not the enacted text.
>
> **This decides a 2.5-percentage-point rate difference.** Assume the unqualified 100% requirement,
> which is the conservative reading, and **do not rely on any de-minimis without reading Finance
> Act 2026 Schedule 2 first.**

### 7.4 Entity types reported but not confirmed ⚠️

| Entity | Reported rate | Why it is flagged |
|---|---|---|
| **Merchant bank** | **27.5%**, cut from 37.5% | [TNP p.24], corroborated by Jural Acuity (https://juralacuity.com/bangladesh-finance-act/) — two sources of similar type, not independent confirmation. Neither PwC nor KPMG lists merchant banks separately. What [PARI §1.5] *does* confirm is that merchant banks are **excluded** from the 37.5% row, which is consistent with a separate rate existing without saying what it is. |
| **One Person Company (OPC)** | **27.5%** *regardless* of banking-channel compliance, up from 22.5%/20% | Same two sources. Note that 27.5% is what an OPC would pay anyway as a non-listed company; what is specifically unconfirmed is the **loss of the 25% banking-channel rate**. |
| **Funds** | **15%** | ⚠️ **Single source, [TNP p.24].** Not in PwC, KPMG or the Paripatra excerpt. The alternative — that a fund falls in the 27.5% trust / artificial juridical person row — cannot be ruled out. |

### 7.5 Reduced rates, exemptions and incentives ⚠️ [KPMG] / [PwC] / [TNP] — none read from enacted text

| Item | Treatment |
|---|---|
| Export income — individual, firm, Hindu Undivided Family | **50% of export income exempt** [KPMG p.25] |
| Export income — other exporters | **12%** [KPMG p.25] |
| Export income — LEED-certified exporters, and jute products | **10%** [KPMG p.25] |
| Manufacturers of freezers and spare parts, refrigerators, motorcycles, air conditioners, compressors | **20%**, AY 2025-26 to 30 June 2032, on conditions not transcribed [KPMG p.26] |
| Asset management company — mutual fund management fee income | **15%, applicable only up to AY 2026-27** — check for extension before AY 2027-28 [KPMG p.26] |
| SME registered with the SME Foundation producing goods | Exempt where annual turnover ≤ **Tk 5,000,000**; **≤ Tk 7,000,000** for an SME owned by a woman **or, newly under FA 2026, by a person with disability** [KPMG p.26]; [PwC p.12] |
| Registered startup (Eighth Schedule Part 2) | Nine-year growth period: **0% turnover tax**, no expense disallowances, no 50% additional tax for withholding non-compliance, losses carried forward nine years despite a shareholding change. Turnover ceiling **Tk 1,000,000,000** [KPMG p.25]; [TNP p.23] |
| Software development / ITES by a resident or non-resident Bangladeshi individual | Exempt to **30 June 2027** [KPMG p.24] |
| Freelancing and content creation income | Exempt; KPMG puts content creation as exempt **until June 2027** [PwC p.12]; [TNP p.22] |
| Solar power producers (self-funded, own solar centres) | 100% exemption. ⚠️ **End date disputed:** PwC says to 30 June 2035, TNP says 1 July 2026 – 30 June 2035, **KPMG says 30 June 2036**. Unresolved. |
| Edible oil from locally grown oilseeds | 100% years 1–5, 50% years 6–8, 25% years 9–10 (SRO 212-AIN/Income Tax-3/2026). ⚠️ The 5/3/2 tranche pattern is agreed; the outer date is not. |

> ### ⚠️ Textile sector — the 15% reduced rate has almost certainly lapsed, but no NBR notification confirms it
>
> The 15% rate came from **SRO 159/2022 of 1 June 2022** and ran to **30 June 2025**. Trade press
> (Bangladesh Textile Journal, 19 May 2025; The Business Standard) reports withdrawal with no
> renewal, which puts textile companies on the standard **27.5% / 22.5%** from AY 2025-26. **No NBR
> notification confirming non-renewal was located**, and none of PwC, KPMG or TNP mentions textiles
> either way — itself weak evidence the concession is gone, since a live concession would normally
> be listed. **Treat the lapse as probable but unconfirmed:** tell a textile client the standard
> rate applies, and ask to see a renewal SRO before using any reduced rate.
> `rates-AY2026-27.toml` deliberately records this with **no usable rate value**.

---

## 8. Turnover tax, and the withdrawal of the minimum-tax character of TDS

### 8.1 The structural change ⚠️ [TNP p.17]; [PwC pp.3, 11–13]; [KPMG p.4]

**The rule that treated tax deducted at source under ss.89–151 as a non-refundable minimum tax has
been WITHDRAWN** (ITA 2023 ss.163(1)-(2); s.164 repealed). Loss-making and thin-margin businesses
whose withholding exceeded their regular liability can now obtain **refunds**, or carry the excess
forward. NBR's own illustration: a supplier with Tk 5 crore of source tax against a Tk 2.5 crore
regular liability now pays Tk 2.5 crore and receives Tk 2.5 crore back. **This is the single
biggest change of the Finance Act 2026 for ordinary trading businesses.**

What remains **final tax**: collection from commercial motor vehicles (s.138) and inland water
vessels (s.139) — but if tax on the declared income is higher, the higher amount is payable; all
Part 7 withholding suffered by a person exempt from filing under s.166(2); and withholding suffered
by a non-resident with no permanent establishment in Bangladesh.

⚠️ **A sequencing trap.** Act 89 of 2026 §94 (April 2026) rewrote s.163 and listed certain
withholdings as *minimum tax*. **Act 96 of 2026 (the Finance Act 2026) §91 then replaced s.163
again**, with effect from 1 July 2026, and §92 repealed s.164 — and the replacement has **no
"minimum tax" limb** at all. Any source describing a s.163(2) minimum-tax list is reading the
superseded April 2026 version.

### 8.2 Turnover tax on gross receipts — ITA 2023 s.163(6) ⚠️

| Category | Rate on gross receipts |
|---|---|
| Tobacco product manufacturers | 3% [TNP p.17] |
| Carbonated / sweetened beverage manufacturers | **2.5%**, cut from 3% [PwC p.13]; [TNP p.17] |
| Mobile phone operators and (newly) NTTN operators | 1.5% [PwC p.13]; [TNP p.17] |
| Industrial undertakings manufacturing goods (other than specified industries), first three income years from commercial production | **0.2%**, raised from 0.1% [PwC p.13]; [KPMG p.20] |
| Registered startups during the growth years | 0% [TNP p.23] |
| **All other cases** | **1%** ⚠️ **single source, [TNP p.17]** |

**Does not apply at all to:** government bodies and state-owned enterprises importing, distributing
or selling fertiliser, seed or daily-essential consumer commodities; commission business; delivery
order (DO) business; money exchange business; and trading in gold, silver, ornaments, gems,
diamonds or platinum. [PwC p.11]; [TNP p.17] Excess turnover tax over the regular liability may now
be **carried forward and set off**. Trusts, firms and associations of persons are liable
**irrespective of the gross-receipts threshold**. [TNP p.17]

> ### ⚠️ The gross-receipts threshold could not be sourced — TakaBooks refuses rather than guesses
>
> No source read gives the level of gross receipts at which turnover tax engages for taxpayers
> other than trusts, firms and AOPs. `rates-AY2026-27.toml` keeps
> `minimum_tax.on_gross_receipts.applies_above` as a **placeholder**, so supplying
> `--gross-receipts` makes the engine **refuse to compute** instead of inventing a threshold.
> **Absent beats wrong.** To land it, read ITA 2023 s.163(6) as amended at
> http://bdlaws.minlaw.gov.bd/act-details-1429.html.

---

## 9. Advance income tax (AIT) — অগ্রিম আয়কর

| Item | Position | Source |
|---|---|---|
| Instalments | **15 September, 15 December, 15 March, 15 June — 25% each** | [KPMG p.20]; [PwC-WWTS] |
| Liability threshold, existing taxpayers | Last assessed **income** exceeds **Tk 1,000,000** (raised from Tk 600,000) | [KPMG p.20]; [PwC p.11] |
| Liability threshold, new taxpayers | Estimated income likely to exceed **Tk 600,000**; the estimate goes to the DCT before 15 June (s.156) | [KPMG p.20] |
| Exclusion | Taxpayer whose only income is agricultural income up to **Tk 800,000** | [KPMG p.20] |
| Missed instalment | May be paid with the next instalment | [KPMG p.20] |
| Shortfall interest | Additional interest at **50%** on the advance-tax shortfall, now triggered **only if the return is filed after the end of the assessment year** | [PwC p.9] |
| Cigarette manufacturers | Separate monthly advance payment regime | [KPMG p.20] |

⚠️ **Sources conflict on whether the Tk 1,000,000 test is income or tax liability.** PwC's summary
says "BDT 1m of the estimated **tax liability**"; KPMG and PwC-WWTS both say prior-year **income**.
Two to one favours income, and that matches the structure of s.154 — but the section was not read.

---

## 10. Filing deadlines, the incentive ladder and additional tax — RESTRUCTURED

The Finance Act 2026 replaced the old fixed deadline plus 2%-per-month penalty with a sliding
window. ⚠️ **NBR's power to extend the return filing date by one month has been repealed.**
[PwC p.7]

### 10.1 Individuals and Hindu Undivided Families — ITA 2023 s.170(1) ⚠️ [PwC p.7]; [KPMG p.45]; [TNP p.18]

| Return filed (income year ended 30 June) | Consequence |
|---|---|
| **1 July – 30 September** | **Rebate: 5% of tax payable, capped at Tk 25,000** |
| 1 October – 31 December | Neutral — no rebate, no additional tax |
| 1 January – 31 March | Additional tax: **higher of 2% of tax payable or Tk 3,000** |
| 1 April – 30 June | Additional tax: **higher of 5% of tax payable or Tk 5,000** |

> ### ⚠️ UNRESOLVED — the statutory due date, and why it is not 31 December
>
> **Two readings are in circulation and TakaBooks cannot choose between them from its permitted
> sources.** The reading below — the research document's — is the one this package follows and
> states. The contrary reading is named at the foot of this box. `compliance-calendar.md`
> ("Four things almost every 2026-27 calendar gets wrong", item 1) and
> `data/rates-AY2026-27.toml` at `deadlines.income_tax_return_specified_date_status`
> (`verified = false`) say exactly the same thing. **Confirm with an ITP or CA before the filing
> season.**
>
> "Tax Day" (কর দিবস) has been replaced by **"রিটার্ন দাখিলের নির্দিষ্ট তারিখ"** — the *specified
> date for filing return* — at **s.2(80A)**, inserted by Act 89 of 2026 §29(ট):
>
> | Taxpayer | Specified date |
> |---|---|
> | Individual and Hindu Undivided Family | **30 November** following the end of the income year |
> | Any other taxpayer | **15th day of the ninth month** after the income year end; or, where that falls before 15 September, **15 September** |
> | Individual who has **never filed before** | **30 June** following the income year end |
> | Individual residing abroad (higher education, deputation or lien, or valid visa and work permit) | **90th day** from the date of return to Bangladesh |
> | Public holiday | The next working day |
>
> So for an individual the **specified date is 30 November**, yet no additional tax arises until
> **1 January**. A return filed on 10 December costs nothing in cash but is still filed **after the
> specified date**, which matters for provisions keyed to that date — notably the s.162
> advance-tax interest uplift and "delayed return" characterisation. **Do not tell a user that
> 31 December is the statutory deadline.**
>
> ⚠️ **Unresolved — the extension power:** PwC says the **NBR's** one-month extension power is
> repealed, yet s.2(80A)(e) gives the **Commissioner of Taxes** power to extend by up to **90 days**
> on written application made before the specified date for unavoidable reasons. Whether the Finance
> Act 2026 removed s.2(80A)(e) is unconfirmed. Do not plan on an extension.
>
> ⚠️ **Unresolved — the drafting:** whether the replacement clause is s.2(80A) or s.2(80Ka), and
> whether the Finance Ordinance 2025 or the Finance Act 2026 made the change, could not be verified.
> The *operative effect* above is well established; the section numbering is not. Note separately
> that the Finance Act 2026 introduces a ceremonial **"National Tax Day"** at s.2(22) — an awareness
> observance, not a deadline.
>
> ⚠️ **The contrary reading — RETRACTED, not adopted.** A content pass in this repository asserted
> that the clause above, numbered **s.2(80ka)**, was **deleted** by the Finance Act 2026 with effect
> from 1 July 2026, so that **no statutory individual due date is in force** for AY 2026-27. It
> cited bdlaws amendment footnotes that appear in **no source this package is permitted to rely on**
> — not in the research document, not in NBR's Paripatra 2026-27. That claim has been retracted from
> every file in this package. It is recorded here so a reader who meets it elsewhere knows it was
> considered and **not** adopted: absent beats wrong, and a user told there is no due date at all
> would miss a mandatory one if this reading is right.

**As at 6 September 2026 an individual filing for AY 2026-27 is inside the 5% early-filing rebate
window, which closes 30 September 2026.**

### 10.2 Companies and other entities — ITA 2023 s.170(2)

**Due date = the later of** (i) the 15th day of the ninth month following the income year end, and
(ii) 15 September following the income year end. [KPMG p.13]

- 30 June 2026 year end → **due 15 March 2027**.
- Bank / insurer / finance company with a 31 December 2025 year end → **due 15 September 2026**.

| Return filed | Consequence |
|---|---|
| More than **2 months before** the due date | Rebate: lower of 5% of the tax under s.173(2) or **Tk 25,000** |
| Within the final 2 months up to the due date | Neutral |
| After the due date but within the assessment year (to 30 June) | Additional tax: **higher of 2% of tax payable or Tk 25,000** |

⚠️ [KPMG p.13]; [PwC p.11]; [TNP p.18]. The Tk 25,000 entity minimum is **not** a transcription
error for the individuals' Tk 3,000 — TNP and KPMG both give Tk 25,000 for entities. Foreign
companies get a shorter 15-day incentive window at the start of their cycle. [TNP p.18]

### 10.3 Returns delayed beyond the assessment year — s.174 ⚠️ [PwC p.14]; [TNP p.18]

The old 2%-per-month charge (max 24 months) is replaced:

| Situation | Additional tax |
|---|---|
| Voluntary (suo motu) delayed return | Higher of **10%** of net tax payable or **Tk 5,000** |
| Return filed in response to a s.212(1) reassessment notice | Higher of **15%** of tax payable or **Tk 10,000** |

NBR's illustration: on the same facts, additional tax falls from Tk 40,200 to Tk 8,375.

### 10.4 Return completeness — a return can be treated as never filed ⚠️ [PwC p.13]; [TNP p.19]

A return is incomplete or defective, and can be **cancelled under s.176(3)**, if it is not
accompanied by the acknowledgement copy of the **withholding tax return**, or if the Statement of
Assets and Liabilities (**IT-10B**) or the Statement of Lifestyle Expenses (**IT-10BB**) is
defective and a s.176(2) resubmission notice is not complied with.

### 10.5 Universal self-assessment and automated refunds ⚠️ [PwC p.6]; [TNP p.18]

Universal self-assessment (s.170Ka) is now **mandatory for individuals**. Automated refunds are
available where income comprises only employment, financial assets and/or agriculture: the DCT
processes within **120 days** of filing and the refund is paid electronically within **60 days** of
the refund application. **Any other head of income — house property, for instance — routes the
return to assessment under s.183 instead**, and the automated refund is lost.

### 10.6 Special-circumstance returns — s.172 ⚠️ [PwC p.6]; [TNP p.19]

A return is required outside the normal cycle on business closure or transfer of ownership during
the year (listed companies excepted), on a person leaving Bangladesh, in evasion cases, on a change
in a partnership's constitution, and on business or firm succession. Specified Bangladeshi
individuals returning from abroad must file within **90 days** of return.

---

## 11. e-Return, PSR and who must file

### 11.1 e-Return — https://etaxnbr.gov.bd

Online filing **is mandatory for general individual taxpayers** by NBR special order; the portal
opened for AY 2026-27 on **22 July 2026**. Payment by bank transfer, debit or credit card, bKash,
Rocket or Nagad; the acknowledgement slip and income tax certificate issue instantly. NBR call
centre 09643717171. 4.7 million individuals filed online in tax year 2025-26.
(Dhaka Tribune, 22 July 2026 — https://www.dhakatribune.com/business/415724/nbr-begins-e-return-submission-service-for-2026-27 ;
Financial Express, 22 July 2026 — https://thefinancialexpress.com.bd/trade/nbr-launches-e-return-service-for-fy27)

**May still file on paper:** taxpayers aged 65 or above; physically disabled or special-needs
taxpayers on submission of a certificate; Bangladeshi taxpayers residing abroad; legal
representatives of deceased taxpayers; foreign nationals working in Bangladesh. A general taxpayer
unable to file online because of e-Return registration problems may file on paper **with the prior
approval of the concerned Additional or Joint Commissioner of Taxes**.

### 11.2 Mandatory filing ⚠️ [KPMG p.29]

**Filing is compulsory for** anyone who: earns income above the exemption threshold; was assessed in
any one of the three preceding income years; is a company; is a shareholder director or shareholder
employee of a company; is a firm; is a partner of a firm; is an association of persons; holds an
executive or management position in a business or profession; is a public servant; is a
non-resident with a permanent establishment in Bangladesh; is subject to a tax exemption or lower
rate; is required to be registered as a taxpayer; or is required to furnish PSR.

**Filing is NOT mandatory for**, among others: Bengali-version primary and pre-primary schools,
government secondary and higher secondary schools, MPO institutions without an English-version
curriculum; public universities; Bangladesh Bank; local authorities; BTRC; BSEC; cantonment boards;
statutory bodies not carrying on commercial activity and receiving regular government funding;
orphanages and religious institutions; funds; and — **new under the Finance Act 2026** —
**non-resident individuals having no permanent establishment in Bangladesh**.

### 11.3 Proof of Submission of Return (PSR) — ITA 2023 s.264

PSR is (a) the acknowledgement receipt of the return, (b) a system-generated tax certificate, or
(c) a certificate issued by the DCT — each showing name, TIN and the assessment year. [KPMG p.30]

**Finance Act 2026 changes** ⚠️ [TNP p.19]: the ambit of s.264 is "rationalised"; PSR is **newly
required** from resident **directors and sponsor shareholders**, from **candidates for Union
Parishad chairman**, and from **educational institutions seeking renewal**; taxpayers must
**display their latest PSR at their business premises**; and a TIN is mandatory for registration,
transfer and fitness renewal of **motorcycles of 150cc and above**.

> ### ⚠️ The list of services requiring PSR is OUT OF DATE and is not reproduced here
>
> The commonly circulated list of 43 items is the **Finance Act 2024** version. **No source
> reproducing s.264 as amended by the Finance Act 2026 could be obtained.** Do not answer a "does
> this service need PSR?" question from a 2024 list. Read the current s.264 at
> http://bdlaws.minlaw.gov.bd/act-details-1429.html, or tell the user TakaBooks does not hold a
> current list.

---

## 12. Other Finance Act 2026 changes worth knowing ⚠️ [TNP p.9]; [PwC p.13]; [KPMG]

- **Withholding default penalty, completely restructured.** Failing to deduct tax at source used to
  disallow the **entire expense** — an effective cost of about 27.5% of the payment. **That is
  abolished.** Under the new s.56(1)(Ka) the deductor pays the undeducted tax **plus 50%**, i.e.
  150% of the defaulted tax, and **the expense remains fully deductible**. NBR's worked example:
  the cash cost of a missed 5% deduction on a Tk 1,000 expense falls from Tk 275 to roughly
  Tk 75–148. See `src/references/withholding-tds-vds.md`.
- **Appeal pre-deposits slashed:** Commissioner (Appeals) 0% → **1%** of disputed tax (10% where no
  return was filed); Taxes Appellate Tribunal 10% → **3%**; High Court Division 15%/25% → **10%**.
  **Waiver facilities are withdrawn**, so the smaller deposit is now unavoidable.
- **Digital permanent establishment (s.2(92)):** a non-resident with **100,000 or more** digital or
  online customers or subscribers in Bangladesh has a PE.
- **Loans, advances and deposits received by individuals (s.67(13)):** aggregate receipts above
  **Tk 500,000** are taxed as income from other sources if received outside banking channels; or,
  if received through banking channels from a person other than a bank, finance or leasing company,
  if still unpaid after **six years**.
- **Interest on loans to associated enterprises:** if charged below **12% p.a.**, the difference is
  taxed as business income (banks, finance and leasing companies excluded). The
  associated-enterprise debt threshold falls from **50% to 35%** of the book value of total assets.
- **Rental income (ss.35–39):** warehouse rent moves into the rent head; salami/premium moves from
  other sources into rental income; **10% of the year-end closing balance** of adjustable advances
  and refundable deposits is included annually as "special rental income"; non-adjustable advances
  are spread over the tenure or five years, whichever is lower; refundable deposits not refunded
  within six years are taxed as other income.
- **Depreciation:** the maximum depreciable value of a motor vehicle rises from **Tk 3,000,000 to
  Tk 6,000,000**; accelerated depreciation outside the Dhaka and Chattogram city corporations is
  now **60% year 1 / 40% year 2**, extended to tourism and sports ventures.
- **Expense disallowance thresholds:** excess perquisite Tk 2,000,000 → **Tk 2,500,000**;
  entertainment simplified to 4% of the first Tk 1,000,000 of computed business income; promotional
  expenses other than advertisement 0.5% → **1% of business turnover**.
- **Assessment time limits tightened** to the assessment year plus 12 months (previously two
  years); arm's-length price determinations extend to five years.
- **Employing a non-Bangladeshi citizen without approval:** additional tax of 50% of tax payable or
  Tk 500,000, whichever is higher — retained, but the taxpayer must now be heard first.

---

## 13. What this file does NOT hold — say so rather than improvise

- **The current s.264 PSR service list** (§11.3).
- **The gross-receipts threshold for turnover tax** (§8.2).
- **Whether the corporate banking-channel de-minimis survives** (§7.3).
- **Merchant bank, OPC and fund rates** beyond two similar-type sources (§7.4).
- **Whether the textile 15% rate was renewed** (§7.5).
- **The solar and edible-oil exemption end dates**, where sources conflict (§7.5).
- **Withholding (TDS) rates** — a separate instrument, SRO 273 of 5 July 2026. See
  `src/references/withholding-tds-vds.md`.
- **Salary computation, perquisites, provident fund, gratuity and WPPF** — see
  `src/references/payroll.md`. Note that the consolidated salary exemption (**lower of one-third of
  employment income or Tk 500,000**, Sixth Schedule Part 1 para 27) is applied *before* income
  reaches the slab table here.
- **Penalties and interest, and the compliance calendar** — see `src/references/penalties.md` and
  `src/references/compliance-calendar.md`.

If a user asks something on that list, **say TakaBooks does not hold verified content on it**, point
them to NBR and a licensed ITP or CA, and do not improvise a figure. **Absent beats wrong.**

---

## Definition of done — status against it

1. ✅ Every figure carries a source and a "current as of" date.
2. ⚠️ **Deliberately departed from.** The original stub said no number should appear in this prose.
   Figures ARE reproduced here so that a reader can check the machine-readable file against a cited
   narrative; `src/data/rates-AY2026-27.toml` remains authoritative and the engine reads only from
   it. **The two must be edited together.**
3. ✅ Anything unconfirmed from primary text is `verified = false` in the rates file and is marked
   ⚠️ here.
4. ✅ Statutory terms appear as Bangla ∥ English pairs.
5. ❌ **Not yet reviewed by a Bangladeshi Income Tax Practitioner or Chartered Accountant.** This is
   the outstanding item before release.
6. ✅ Header block replaced — "Current as of", "Sources" and "Status" filled in.

---
Maintained by Moshiur Rahman (@bemoshiur) · TICON SYSTEM LTD — https://ticonsys.com · MIT
