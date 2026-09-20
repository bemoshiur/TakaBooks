# VAT — মূসক (মূল্য সংযোজন কর)

**Current as of:** 2026-09-06
**Assessment year context:** AY 2026-27. VAT does not run on the assessment year at all — it
runs on the **tax period (কর মেয়াদ)**, which is one Gregorian calendar month (s.2(30)), and from
1 July 2026 the return covers **three of them**. Every rate, threshold, deadline and monetary
amount lives in `data/rates-AY<year>.toml` under `[vat]`, never in this file.
**Sources:** the Bangla statute — মূল্য সংযোজন কর ও সম্পূরক শুল্ক আইন, ২০১২ (Act 47 of 2012) at
http://bdlaws.minlaw.gov.bd/act-1106.html, which is current through the Finance Act 2026 and
carries an amendment footnote on every section; the VAT & SD Rules 2016 gazette,
**SRO No. 333-Ain/2016/1-Mushak** dated 3 November 2016, at
https://nbr.gov.bd/uploads/rules/VATR2016.pdf; the consolidated Schedules PDF generated
27 August 2026 and linked from the act-1106 page under "তফসিল"; the Bangladesh Gazette
Extraordinary of 22 January 2025 for **S.R.O. 39-Ain/2025/275-Mushak** (p.448),
**S.R.O. 40-Ain/2025/276-Mushak** (p.449) and **S.R.O. 41-Ain/2025/277-Mushak** (p.450), and the
FY2026-27 exemption gazette **S.R.O. 127-Ain/2026/332-Mushak**, all from NBR's VAT-SRO index at
https://nbr.gov.bd/regulations/sros/vat-sros/eng; and NBR's VAT-2012 forms index
at https://nbr.gov.bd/form/vat/vat-2012/eng. Secondary summaries (PwC Bangladesh, KPMG /
Rahman Rahman Huq, Tuhin & Partners) are used only where marked, and only to locate or
corroborate — never to state a figure as settled.
**Status:** POPULATED — researched from the sources above, with every gap named rather than
smoothed over.

> ⚠️ **Never cite NBR's own VAT FAQ page** (https://nbr.gov.bd/faq/vat-faq/eng). It is years out
> of date — it still shows a Tk 80 lakh registration threshold, a Tk 30 lakh *registration*
> figure, 3% turnover tax and monthly returns, all pre-2019 positions. It is the likely origin
> of several wrong figures circulating in secondary write-ups. This is an official page that is
> wrong; being official does not make it current.

**What this file contains.** How Bangladeshi VAT works, which instrument sets each rule, which
Mushak form carries it, and where a figure is not settled. **It contains no rate and no
monetary amount** — those live in `[vat]` in the rates TOML, each with its own `source`,
`as_of`, `verified` and `note`. Where a figure is wanted, this file names the TOML key.
Three kinds of numeral do appear below, and only these three: **form numbers**, **day-counts and
statutory periods** (a form catalogue without them is useless), and **figures being corrected** —
where naming the wrong number that circulates, and the right one beside it, is the entire point
of the warning. In every case the TOML key is cited alongside, and the TOML is the authority.

**Sourcing markers**, used in the tables below:

| Marker | Meaning |
|---|---|
| **✔** | Read from primary text — the Bangla statute on bdlaws, an SRO gazette, the consolidated Schedules PDF, or a form NBR itself publishes. |
| **⚠** | Not settled. Either it rests on a professional summary, or the research pack lists it in **UNVERIFIED / CONFLICTING**. Say so out loud before anyone files on it. |

---

## 1. Two tiers, and the figures almost everyone gets wrong

Bangladesh runs two tiers below the standard regime, and the boundary between them moved on
**9 January 2025** — not at a budget, which is why so many charts missed it. The VAT & SD
(Amendment) Act 2026 (**Act 77 of 2026**) ratified the 9 January 2025 ordinance *retrospectively*,
substituting s.2(48) and s.2(57).

| Band | Obligation | Regime | TOML key |
|---|---|---|---|
| Below the enlistment threshold | Neither register nor enlist | — | `vat.thresholds.turnover_tax_enlistment` **✔** |
| Enlistment threshold to registration threshold | **Turnover tax enlistment** (তালিকাভুক্তি) | Turnover tax on gross turnover, **no input credit at all** | `vat.turnover_tax.rate` **✔** |
| Above the registration threshold | **Mandatory VAT registration** (নিবন্ধন) | Standard rate with input tax credit | `vat.thresholds.registration` **✔** · `vat.rates.standard` **✔** |

> ⚠️ **The widely circulated "Tk 50 lakh enlistment / Tk 3 crore registration" pair is out of
> date, and so is the Tk 80 lakh figure from NBR's stale FAQ.** The statute is unambiguous and
> the amendment footnotes on bdlaws show the substitution. If a client's adviser quotes the old
> pair, show them s.2(48) and s.2(57).

The Finance Bill 2026 proposed **deleting** the enlistment threshold, so that any turnover up to
the registration threshold would require enlistment. **That was not enacted** — the floor stands.
This is one of many places where a budget-day news report describes the Bill, not the Act.

**Turnover tax has two traps of its own** (s.63): an enlisted person may take **no input tax
credit and no decreasing adjustment** (s.63(4)) — the tax is on gross turnover with nothing
recoverable — and the tax must be **paid before the return is submitted**, not with it
(s.63(2)). New under the Finance Act 2026: the Government may notify a region- and
sector-specific **fixed** turnover tax instead of the percentage, capped at
`vat.turnover_tax.sector_fixed_cap` **✔**. **Until such a notification issues, the percentage
continues**, and none had been traced as at 5 September 2026.

## 2. Who must register — s.4

**s.4(1)** — registrable from the first day of a month if turnover in the **preceding 12 months**
exceeded the registration threshold, **or** if estimated turnover for the **next 12 months** will
exceed it. Either limb is enough.

**s.4(2)** (substituted by Finance Act 2022 s.57) — registration is mandatory **irrespective of
turnover**, and the threshold does not apply at all (proviso to s.2(57)), for a person who:

- supplies, manufactures or imports **supplementary-duty-liable** goods or services;
- supplies goods or services **through a tender, contract or work order**;
- is engaged in **import-export** business;
- establishes a **branch, liaison or project office** of a foreign entity;
- is appointed a **VAT agent**; or
- operates in a **Board-specified geographic area**, or in specified goods or services.

A small consultancy that wins one government work order is inside s.4(2) on day one. This is the
most-missed registration trigger in practice.

**s.4(3) — NEW, inserted by Finance Act 2026 s.3, effective 1 July 2026.** A BIN or proof of
enlistment is now **mandatory** for: opening or operating a **current or STD bank account**;
taking a **loan** from a bank, NBFI or financial institution; **trade licence renewal**; opening
an **MFS merchant account**; obtaining or renewing **trade association membership**; **electricity
and gas connections**; and **BRTA vehicle registration** in the business's name. In practice this
turns VAT registration into a precondition for operating at all. **✔**

**Enlistment timing — s.10, replaced by Finance Act 2026 s.4.** A person who crosses the
enlistment threshold within 12 months but stays below the registration threshold must apply
**within 30 days**, through the **eVAT system**. If the application is in order, eVAT
**auto-approves and issues the certificate immediately (তাৎক্ষণিকভাবে)**. **✔**

**BIN issue — s.6.** The officer registers the applicant and issues a **registration certificate
bearing the Business Identification Number (BIN)**; if the application is not in order the
applicant is notified with reasons. For FY2026-27 the whole cycle is automated in the e-VAT
system: BIN issued immediately to the registered email address on submission of valid
information, with **physical inspection following approval rather than preceding it**. **✔**

## 3. Central registration vs unit registration — s.5

| Position | Rule |
|---|---|
| **s.5(1)** (subst. FA 2022 s.58) **✔** | A person supplying **identical or similar** goods or services from one or more places, who keeps **all** accounts, tax payment and records **centrally in a software-based automated system**, may take **one central registration**. |
| **Proviso to s.5(1)** **✔** | Even for identical or similar supplies, if **any unit keeps its accounts and records separately**, that unit needs its **own registration**. The test is where the books are, not what is sold. |
| **s.5(1a)** **✔** | Central registration does **not** apply to the supply of **tobacco products** under the s.58 special scheme. |
| **s.5(2)** **✔** | A person supplying **different** goods or services from two or more places must take a **separate registration for each place**. |
| **s.5(3)** **✔** | Movement or transfer of goods or services **between units of a centrally registered person is NOT a supply** — no output tax, and no input tax credit, arises on it. Move it on a **Mushak 6.5**, not a Mushak 6.3. |

Conditions for central registration: **SRO No. 263-Ain/2019/79-Mushak dated 18 August 2019**.

## 4. Rates — and where they actually live

The standard rate sits in **s.15(3)**; the first proviso lets the Government fix a **reduced rate
or a specific (fixed) amount** for anything listed in the **Third Schedule (তৃতীয় তফসিল)**; and
the second proviso lets a registered person **elect to pay the standard rate instead** of a
Third Schedule reduced or specific rate. That election is not perverse: **s.46(1)(tha) denies
input tax credit on inputs to any supply taxed below the standard rate**, exports excepted. For a
business with heavy creditable inputs, electing up is often cheaper. Keys: `vat.rates.standard`
**✔**, `vat.rates.zero_rated` **✔**, `vat.rates.imported_services` **✔**, and one node per
reduced rate under `vat.rates.reduced.*`.

**Zero-rated is not exempt.** A **zero-rated** supply (ss.21–24) carries no output VAT and the
input credit **survives**. An **exempt (অব্যাহতি)** supply carries no output VAT and the input
credit **dies** (s.46(1)(jha)). Getting these two confused is the commonest conceptual error in
Bangladeshi VAT bookkeeping, and it moves real money.

**Imported services** are taxable under **s.20, replaced by the Finance Act 2026**: the
**recipient** accounts for the VAT as output tax under the reverse charge. At remittance the bank
or authorised dealer deposits it by **a-challan** under the importer's circle and economic codes,
and that challan serves as **both** the tax invoice and the input tax credit document —
but **s.46(1)(kha) denies the credit if the recipient does not separately show the output tax in
the return**. **✔**

### 4.1 Two traps in the Third Schedule — read this before quoting any reduced rate

Both traps are real and both are now **resolved against primary text**, on 6 September 2026. The
resolution needed one technique worth recording, because it will be needed again: **the Bangla in
both source documents does not text-extract, but it renders perfectly.** The consolidated
Schedules PDF uses a broken legacy font mapping, and NBR's SRO scans carry an OCR text layer that
is Latin gibberish. Both were therefore **rendered to high-resolution images and read from the
rendering** rather than from `pdftotext`. Anything below marked **✔** was read that way.

**Trap 1 — several headline rates do not live in the Schedule at all.** The Schedule shows
**S001** (hotel and restaurant), **S014** (indenting), **S022** (sweetmeat shop) and **S078**
(ready-made garment marketing) as **deleted** — S001 from Table-1 Part খ (footnote 71) and from
Table-2 Part খ (footnote 87), S022 by footnote 89 and S078 by footnote 94, all by **Act 77 of
2026 s.4**. Restaurant, non-AC hotel, motor garage and sweetmeat rates are nevertheless current,
because **S.R.O. 39-Ain/2025/275-Mushak of 22 January 2025** sets them by notification under
**s.126(1)**, and **S.R.O. 40-Ain/2025/276-Mushak of the same date** caps medicines at the trader
stage. **Both S.R.O.s have now been opened and read in full** from NBR's gazette scans
(https://nbr.gov.bd/uploads/sros/IMG_20250213_0014.pdf and `…IMG_20250213_00151.pdf`), and all
five rates are landed as `verified = true`. **✔**

> **Finding them took a trick.** NBR's VAT-SRO listing at
> `https://nbr.gov.bd/regulations/sros/vat-sro/eng` — the path in general circulation, and the one
> earlier TakaBooks research used — returns a **PHP error page with an empty table**, which is why
> a targeted search found nothing and the rates sat unverified. The working path is the **plural**
> `https://nbr.gov.bd/regulations/sros/vat-sros/eng`, paginated as `/vat-sros/<offset>/eng`. All
> 17 pages and 664 rows were crawled.

> ⚠️ **Two service codes in wide circulation are wrong, including in earlier TakaBooks drafts.**
> **Motor garage and workshop is S003.10, not S022.00.** **The sweetmeat shop is S022.00, not
> S078.00** — S078.00 is *ready-made garment marketing*. The S003.10 attribution is confirmed
> three times: the S.R.O. 39 row, S.R.O. 41-Ain/2025/277-Mushak of the same date (which
> substitutes the matching VDS serial), and serial 03 of the current VDS gazette. Note also that
> **S003.20 (dockyard) is a different service at the standard rate**, and that a **restaurant
> inside a three-star-or-above listed residential hotel, a restaurant inside a hotel with a liquor
> bar, and any restaurant with a liquor bar are excluded** from the reduced restaurant rate.
> Keys: `vat.rates.reduced.restaurant`, `.hotel_non_air_conditioned`,
> `.motor_garage_and_workshop`, `.sweetmeat_shop` — all **✔**.

> ⚠️ **An air-conditioned hotel gets no reduction.** S.R.O. 39 lists only the *non-AC* hotel; the
> VDS gazette draws the same distinction, carrying AC and non-AC as two separate lines under the
> one code S001.10. The code alone does not tell you the rate.

**Trap 2 — the local trader rate has moved, and one item has silently left the reduced list.**
Footnote 121 of the consolidated Schedules PDF confirms **paragraph (3) of the Third Schedule was
substituted by Act 77 of 2026 s.4(ছ)**, and the paragraph has now been read in full from a
rendering of page 86. The **local trading stage rate rose from 5% to 7.5%**. Every paragraph-3
figure, and the paragraph-4 wholesale figure, is now `verified = true`: general trading stage,
building sale at either size band, medicines, the fuel list, land developers, and wholesale.
Keys: `vat.rates.reduced.local_trading_stage`, `.building_construction_small`,
`.building_construction_large`, `.medicine_local_trading`, `.petroleum_local_trading`,
`.land_developer`, `.wholesale_business` — all **✔**. This is not a rounding difference; it is the
rate on a trading business's whole turnover, and a business still charging the old figure is
under-collecting.

> ⚠️ **LP gas has been dropped from the reduced fuel list.** Footnote 121 prints both texts. The
> superseded one read "ডিজেল, কেরোসিন, অকটেন, পেট্রোল, ফার্নেস অয়েল ও **এলপি গ্যাস**"; the
> substituted one omits LP gas. So an LP gas trader is **no longer on the low fuel rate** — LP gas
> now takes the general local-trading rate. Any chart still listing LP gas with the other fuels is
> quoting repealed text. See `vat.rates.reduced.petroleum_local_trading`.

> ⚠️ **The Schedule and the S.R.O. disagree on medicines, and the S.R.O. wins.** Paragraph (3) as
> substituted sets a *higher* trader-stage rate for medicines than S.R.O. 40 allows to be
> collected; S.R.O. 40 is a standing s.126(1) exemption that caps the charge, and nothing repeals
> it. The FY2026-27 exemption gazette **S.R.O. 127-Ain/2026/332-Mushak of 7 June 2026 was opened
> and read**, and its clause 5 repeals only S.R.O. 160-Ain/2025/288-Mushak. The TOML holds the
> capped figure and its note carries the Schedule figure beside it, so that if the S.R.O. is ever
> withdrawn a reader knows what it reverts to. See `vat.rates.reduced.medicine_local_trading`.

> ⚠️ **The land developer rate is lower than the figure in circulation**, and **re-registration of
> a building of any size takes the small-building rate, not the large-building rate** — a resale
> of a large flat is not at the large-building rate. Both points are read from the
> paragraph itself. See `vat.rates.reduced.land_developer` and `.building_construction_small`.

**What is still NOT verified.** Service codes, rate figures, amendment footnotes, paragraph (3)
and paragraph (4) are all read. The item-by-item **goods** lists are **not** — they do not text-
extract, and the page-by-page rendering that recovered the rates above was not carried through the
goods tables, which run to dozens of pages and were not needed for any rate node. So the goods
lists remain a known gap, and it is a gap of effort rather than of possibility: the same rendering
technique would recover them. The illustrative goods examples that circulate (newsprint, thread,
bricks, SIM cards) come from a secondary pre-Finance Act 2026 chart and are **deliberately not
held** in TakaBooks. One more gap is named on
`vat.rates.reduced.wholesale_business`: **the rate is certified but the entitlement is not** —
paragraph (4) applies it to *certain* wholesale businesses "subject to compliance with the
prescribed conditions and procedure", and neither the qualifying class nor the conditions were
traced. Do not assume a wholesale business qualifies.

**Finance Act 2026 s.22 — read in clean Unicode from bdlaws, unusually for this Act.** It deleted
heading S026 from Table-1 Part খ, inserted new fixed amounts into Table-4 Part ক (foreign liquor,
unprocessed tobacco, scrap and the M.S. product range), replaced Table-4 Part খ with the S026.00
jewellery amounts, and deleted the Explanation at the end of paragraph (3). Keys:
`vat.fixed_amounts.*` **✔**.

> ⚠️ **Correction to PwC on diamond.** PwC's table prints the diamond fixed VAT **per bhori**.
> **The gazette says প্রতি গ্রাম — per GRAM.** A bhori is about 11.66 grams, so PwC's version
> understates the charge by roughly a factor of twelve. A jeweller's return prepared from that
> table is materially wrong. See `vat.fixed_amounts.diamond_per_gram`.

> ⚠️ **S037.00 যোগানদার (procurement provider) is 10%, not 5%.** The gazette reads
> "২২. S০৩৭.০০ যোগানদার (Procurement Provider) ১০%". The 5% figure in circulation is wrong, and
> this is one of the commonest supplies an SME makes to a withholding entity. See
> `vat.rates.reduced.procurement_provider` **✔**.

> ⚠️ **ICAB's "S004.00 stays at the lower rate for contracts signed before 30 June 2025" is not
> in the SRO.** The full text of SRO 182-Ain/2025/310-Mushak was searched and contains no such
> proviso. Treat it as a practice position and get it in writing from the circle.

### 4.2 ⚠️ Announced measures that are not in any gazette

A post-budget SRO wave exists that **NBR has not uploaded**. NBR's VAT-SRO index was crawled in
full on 6 September 2026 — all 17 pages and 664 rows of the working plural path
`https://nbr.gov.bd/regulations/sros/vat-sros/eng` — and the newest VAT SRO published on it is
**SRO 148-Ain/2026/353-Mushak of 11 June 2026**. PwC cites **SRO 255-Ain/2026/355-Mushak of
30 June 2026**; it is not there, and neither is anything else in the gap above SRO 148. This is
now a *complete* search of NBR's own index rather than a failed one, so the absence is a fact
about NBR's publishing, not about the search. Four announced VAT measures are therefore **not
traceable to any gazette**:

1. the **digital-advertising 5% rate and its claimed service code S007.20** — the VDS rules,
   which *were* read from the gazette, still carry a single S007.00 advertising-agency entry at
   the standard rate and no S007.20 anywhere (`vat.rates.reduced.digital_advertisement`,
   `placeholder = true`);
2. the **double-cabin pickup / microbus** cut;
3. the **BTRC revenue-sharing VDS exemption**;
4. the **input-output-coefficient relaxation**.

Until the notification is sighted, an advertising supply is at the standard rate. Do not charge
the announced rate on the strength of a budget speech.

Note also: **"SRO 258-Law/2026/358-VAT does not exist."** That citation circulates on practitioner
blogs and is wrong; every probe of the 149–266 range returns 404. The real FY2026-27 VDS
amendment is **SRO 140-Ain/2026/345-Mushak of 7 June 2026**.

## 5. Input tax credit — উপকরণ কর রেয়াত (s.46)

The credit is the whole point of registration, and it is lost more often to paperwork than to
law. **s.46(1)** grants it subject to fifteen disallowances; **s.46(2)** is an absolute bar;
**s.46(3)** lists the supporting documents.

### 5.1 ⭐ The six-tax-period window — and why every book says four

**s.46(1)(ga):** the credit must be taken in the tax period in which the input was purchased or
acquired — per the tax invoice or the goods declaration — **or within the following six tax
periods**. Changed **from four to six** by the Finance (FY2025-26) Act 2026 (**Act 89 of 2026**)
s.5(a)(i). Key: `vat.input_tax_credit.time_limit_tax_periods` **✔**.

> ⚠️ **Almost every published source, including the ICAB CA manual, still says four.** TakaBooks
> follows the statute and its amendment footnote. Expect to have to show the footnote to a
> reviewer. If you are reopening a period between 1 July 2025 and April 2026, check which window
> applied then — the research could not establish a commencement date specific to that clause.

**A missed window cannot be cured.** **Rule 49(1A)**, inserted by SRO 135/2023, expressly bars
using an amended return to capture a rebate that was not claimed in time. A credit that ages out
is gone. Reconcile the purchase book monthly, not annually.

### 5.2 The conditions that actually kill claims

| Clause | What kills the credit | TOML key |
|---|---|---|
| **(ka)** **✔** | Value of a taxable supply above the threshold and the **entire** consideration paid **outside a banking or mobile banking channel**. Carved out: purchases between a registered supplier and recipient **under the same ownership**. | `vat.input_tax_credit.banking_channel_threshold` |
| (kha) **✔** | Imported services where the recipient did not separately show the output tax in the return under s.20 | — |
| (gha) **✔** | VAT on goods or services in another's possession, custody or control — **except contract manufacturing** | — |
| (uma) **✔** | Goods or services **not entered in the prescribed purchase book** (Mushak 6.1, or 6.2.1 for traders) | — |
| **(cha)** **✔** | Tax invoice not stating the **name, address and BIN of BOTH buyer and seller** | `vat.thresholds.tax_invoice_buyer_bin` ⚠ |
| (chha) **✔** | Importer's invoice omitting the **goods declaration number**, or a description that does not properly match commercially | — |
| (ja) **✔** | Inputs released against a **bank guarantee**, until final settlement. Proviso (Act 89 of 2026 s.5(a)(iii)): credit allowed within six tax periods from the **later** of guarantee release or final duty/tax payment | `vat.input_tax_credit.bank_guarantee_time_limit_tax_periods` |
| (jha) **✔** | Inputs used to produce **exempt** goods or supply exempt services | — |
| (yna) / (ta) **✔** | **Turnover tax** paid; **supplementary duty** paid on inputs | — |
| (tha) **✔** | Inputs to a supply taxed **below the standard rate** or at a **specific** rate — **exports excepted** | — |
| (da) **✔** | Inputs **not declared in the input-output coefficient** (Mushak 4.3) — except Board-determined fields (inserted by FA 2026 s.8(a)(ii)) and except the supply of services | — |
| (dha) **✔** | Total input value moves by more than the tolerance and **no fresh Mushak 4.3 is filed** → the input tax above the tolerance is **cancelled** | `vat.input_tax_credit.input_value_change_tolerance` |
| **(na)** **✔** | Supplies at **less than input value**. **Substituted by Finance Act 2026 s.8(a)(iii): previously the whole credit died; now only the input tax in excess of the output tax payable is disallowed.** A genuine improvement — proportionate credit survives | — |
| **s.46(2)** **✔** | **Absolute bar**: passenger vehicles, their spare parts and their repair or maintenance (unless dealing, hiring out or transport is the person's economic activity **and** the vehicle was acquired for it); **entertainment** (unless providing entertainment is the economic activity, given in the normal course); **membership or right of entry to a sports, social or recreational club, society or association**. Clause (gha) was **deleted** by FA 2026 s.8(b) | — |

**⭐ Labour is now an input.** Finance Act 2026 s.2(a) **deleted "শ্রম" (labour) from the negative
list** in the definition of "input" at s.2(18A), effective 1 July 2026 — so labour and
manpower-supply costs can now qualify and carry credit. **✔** Still not inputs: land; buildings;
office equipment and fixtures; construction, renovation, modernisation, replacement, extension or
repair of buildings or infrastructure; furniture, office supplies, stationery, refrigerators and
freezers, air conditioners, fans, lighting, generators and their repair; interior design and
architectural planning; purchase, rent or lease of vehicles; travel, entertainment, employee
welfare and development work; and **rent of business premises, office or showroom**.

**Documents that support a claim — s.46(3)** **✔**: for an **import**, the **goods declaration**
bearing the importer's name, address and BIN; for a **supply**, the **tax invoice (Mushak 6.3)**;
for s.20(2), the **treasury challan** (substituted FA 2026 s.8(c)); for **gas, water,
electricity, bank, insurance, port and telephone** services, the provider's **bill**, treated as
an invoice; and for electricity bills, invoices issued by banks, MFS providers and digital
payment gateways.

**Mixed supplies:** where a person makes both taxable and exempt supplies, **s.47**
(আংশিক উপকরণ কর রেয়াত) governs the apportionment —
http://bdlaws.minlaw.gov.bd/act-1106/section-42343.html

## 6. Returns and payment — the change that catches everyone

> ⚠️ **The old rule — one return per month, by the 15th of the following month — is superseded.**
> **s.64 was wholly substituted by Finance Act 2026 s.11**, effective 1 July 2026.

| Item | Position from 1 July 2026 | TOML key |
|---|---|---|
| **Default frequency** | **Quarterly** — one return for every three tax periods | `vat.filing.frequency` **✔** |
| **Deadline** | Within **15 days** of the end of every three tax periods; if the 15th is a public holiday, the **next working day** | `vat.filing.due_days_after_quarter` **✔** |
| **Extended deadline** | **20 days** for government, semi-government and **autonomous bodies, banks, insurance companies**, and for **anyone filing a NIL return** | `vat.filing.due_days_extended` **✔** |
| **Monthly option** | **s.64(2)** — a person may **voluntarily** file per tax period, on **any day of the following tax period** (i.e. by the last day of the next month) — more generous than the old rule | `vat.filing.monthly_option` **✔** |
| **Payment** | Aligned with the return deadline. Turnover tax must be paid **before** filing (s.63(2)). The Bill's proposal for monthly deposits on prior-period liability was **not enacted** | — |
| **Board extension** | **s.64(3)** — the Board may extend in the public interest, **without interest or penalty** | — |
| **SD integrated** | **s.64(4)** — supplementary duty information goes in the VAT return | — |
| **E-filing** | **s.64(5)** — the Board may mandate electronic filing | — |
| **Which form** | **Mushak 9.1** (credit claimants) · **Mushak 9.1.1** ⚠ (no credit) · **Mushak 9.2** (turnover tax) | — |

> ⚠️ **The quarter boundaries are an inference, not an NBR-stated fact.** Neither the amended
> s.64, nor PwC, nor Tuhin & Partners says whether the quarters run July–September /
> October–December / January–March / April–June. TakaBooks assumes they do, following the
> 1 July 2026 commencement and the previous turnover-tax convention — so the first return under
> the new regime covers July–September 2026. **Confirm against an NBR General Order before you
> diarise a year of deadlines**: a business that guesses the wrong quarter start files late every
> quarter. Key: `vat.filing.quarter_boundaries`, marked `verified = false`.

**Late filing — s.65.** On application (**Mushak 9.3**, Rule 48) the Commissioner may permit late
filing, but the permission **cannot move the actual payment date by more than one month** and
**does not alter the interest liability**. Key:
`vat.filing.late_permission_max_extension_months` **✔**.

> ⚠️ **KPMG and s.65 appear to conflict.** KPMG describes a one-month extension whose interest
> "may be waived at the discretion of the VAT authority". **s.65 contains no waiver power.** A
> waiver power does exist, but in **s.64(3)**, where it belongs to the **Board** — not the local
> VAT circle — and extends the deadline without interest or penalty. The two look conflated. Do
> not plan on a circle-level waiver.

**Amended return — s.66.** On application (**Mushak 9.4**, Rule 49) the Commissioner may permit
correction of **clerical errors**. Interest is payable on the difference. ⚠ KPMG adds a
four-year outer limit and "before a VAT audit commences", at `vat.filing.amended_return_years`,
unverified. **And an amended return cannot rescue a missed rebate — Rule 49(1A).**

**Enforcement.** ⚠ Where a return is late the VAT authority issues a notice; if the business is
still non-compliant after 21 days an assessment order issues and NBR may **temporarily lock the
BIN**, suspending import and export activity. The BIN unlocks automatically within two days of
the return being filed. Key: `vat.filing.bin_lock_notice_days`, unverified (KPMG). The fee for a
late return is small; a stopped shipment is not.

**Audit timelines, codified by FA 2026** **✔**: documents due within **2 months** of notice, a
**1-month** extension may be available, and the audit must conclude **within 1 year** of document
submission, failing which best-judgment consequences may arise. **ERP and software records are
accepted as valid documents and may be submitted online.**

## 7. The Mushak form series — মূসক ফরম

Rule numbers are taken from the primary Rules gazette, **SRO No. 333-Ain/2016/1-Mushak dated
3 November 2016**, made under s.135 of the Act.

> ⚠️ **The commonly cited "SRO 186-Ain/2016" for the VAT Rules is a wrong citation.**

> ⚠️ **Rule numbers for Mushak 4.3, 4.3.1, 6.2.1 and 9.1.1 are not established.** The NBR-hosted
> Rules PDF is the **original 3 November 2016 gazette** and does not contain Mushak 4.3 or 6.2.1
> at all — both were added by later amending SROs that could not be located. Rule numbers for the
> two new FY2026-27 forms (4.3.1, 9.1.1) are simply unknown. **TakaBooks leaves them blank rather
> than guessing.** The form numbers themselves are certain for 4.3 and 6.2.1 — NBR publishes both
> forms on its VAT-2012 forms index — and rest on professional summaries for 4.3.1 and 9.1.1.

> ⚠️ **The Bangla form names below are renderings** decoded from rule headings and the ICAB
> manual. Check them against the form schedule in the amended Rules before printing one.

| Form | Bangla name | English | Purpose | Who files or issues | When | Rule | Src |
|---|---|---|---|---|---|---|---|
| **2.1** | নিবন্ধন/তালিকাভুক্তির আবেদনপত্র | Application for registration or turnover tax enlistment | Obtain a BIN or enlistment | Registrable / enlistable person | Registration: on becoming registrable. **Enlistment: within 30 days** of crossing the threshold (s.10(1)) | Rule 4 (reg.) · Rule 5 (enlist.) | **✔** |
| 2.2 | অনাবাসিক ব্যক্তির নিবন্ধন | Registration — non-resident | Non-resident registration via a VAT agent | Non-resident / VAT agent | On becoming registrable | Rule 4 · Rule 17 | **✔** |
| **2.3** | নিবন্ধন সনদপত্র / তালিকাভুক্তি সনদপত্র | Registration / enlistment certificate | Evidence of the BIN or enlistment — **must be displayed** | Issued by NBR (eVAT, immediately) | On approval | Rule 4 / Rule 5 | **✔** |
| 2.4 | নিবন্ধন বা তালিকাভুক্তি বাতিলের আবেদন | Application for cancellation | Cancel on cessation | Registered / enlisted person | On cessation | Rule 8 (VAT) · Rule 9 (turnover tax) | **✔** |
| 2.5 | তথ্য পরিবর্তন | Change or addition of information | Notify changed particulars | Registered / enlisted person | **Within 15 days** of the change (s.14) | Rules 8, 9, 12 | **✔** |
| 4.1 | আগাম কর ফেরত/সমন্বয় | Adjustment or refund of Advance Tax paid at import | Reclaim AT | Importer | On claim | Rule 19 | **✔** |
| 4.2 | চলমান ব্যবসা হস্তান্তর | Joint application — transfer of a running business | Transfer liabilities on sale of a going concern | Buyer **and** seller jointly | **At least 15 days *before* the sale** | Rule 22 | **✔** |
| **4.3** | উপকরণ-উৎপাদ সহগ ঘোষণা | **Declaration of Input-Output Coefficient** | Declare the input-output ratio per product | Registered manufacturer | After manufacturing but **before supply** (FA 2026 clarification); filed with the divisional VAT office **within 15 days of the first taxable supply**; resubmitted if total input cost moves beyond the tolerance | **rule number not established** | ⚠ |
| **4.3.1** | *(official title unknown)* | Input-output coefficient — **traders** (NEW FY2026-27) | For traders supplying goods fully or partly exempt at the manufacturing stage; supports the s.32(6) value-addition route | Traders | Filed in the **e-VAT system**, within 15 days | **rule number not established** | ⚠ |
| 4.4 / 4.5 / 4.6 | *(titles unknown)* | Disposal of unused or unusable input; goods damaged or destroyed in an accident; wastage or by-products | Stock adjustments | Registered person | On the event | **not established** | ⚠ |
| **6.1** | ক্রয় হিসাব পুস্তক | **Purchase account book** | Record every purchase — **s.46(1)(uma) denies credit on anything not entered here** | Registered person; enlisted person per Rule 41 | Contemporaneously | **Rule 40** (VAT) · Rule 41 (turnover tax) | **✔** |
| **6.2** | বিক্রয় হিসাব পুস্তক | **Sales account book** | Record every sale | Registered person | Contemporaneously | **Rule 40** · Rule 41 | **✔** |
| **6.2.1** | ক্রয়-বিক্রয় হিসাব পুস্তক | **Purchase-sales account book** | Combined register for **traders** supplying goods without processing | Trader | Contemporaneously | **rule number not established** | ⚠ |
| **6.3** | কর চালানপত্র | **Tax invoice** | The primary VAT invoice, and **the** input tax credit document | Registered supplier | **Two copies**, on or before VAT becomes payable on the supply | **Rule 40** | **✔** |
| 6.4 | চুক্তিভিত্তিক উৎপাদনের চালানপত্র | Invoice for **contractual (toll) manufacturing** | Movement or supply under contract manufacture | Contract manufacturer | Per transaction | **Rule 40** | **✔** |
| 6.5 | কেন্দ্রীয় নিবন্ধিত প্রতিষ্ঠানের পণ্য স্থানান্তর চালানপত্র | Invoice for **inter-unit transfer** | Stock transfer between units of a centrally registered entity — **not a supply**, s.5(3) | Centrally registered person | Per transfer | **Rule 40** | **✔** |
| **6.6** | উৎসে কর কর্তন সনদপত্র | **VDS certificate** | Evidence for the supplier's decreasing adjustment | **Withholding entity → supplier** | **Registered** entity: within **3 working days of filing its return**. **Unregistered** entity: within **3 working days of depositing** the withheld VAT. **Three copies** | **Rule 40**; mandated by **s.53** | **✔** |
| 6.7 | ক্রেডিট নোট | **Credit note** | Decreasing adjustment | Supplier | On the adjustment event | **Rule 40**; s.52 | **✔** |
| 6.8 | ডেবিট নোট | **Debit note** | Increasing adjustment | Supplier | On the adjustment event | **Rule 40**; s.52 | **✔** |
| 6.9 | টার্নওভার কর চালানপত্র | **Turnover tax invoice** | The invoice an **enlisted** person issues — **no credit against it**, s.46(1)(yna) | Enlisted person | Per supply | **Rule 41** | **✔** |
| 6.10 | ক্রয়-বিক্রয়ের তথ্য দাখিল | **Statement of large purchase and sale invoices** | Report transactions above the prescribed value | Registered or enlisted person | With, or alongside, the return | **Rule 42** | **✔** |
| 7.1 | সম্পূরক শুল্ক সমন্বয়ের আবেদন | Application for adjustment of supplementary duty | SD adjustment | Registered person | **Within 6 months** of the relevant date | s.62 (rule number not recorded) | **✔** |
| **9.1** | মূল্য সংযোজন কর দাখিলপত্র | **VAT return** | The main return; input tax credit is claimed here | Manufacturers, service providers, and **traders availing credit** | **Quarterly** — see §6 | **Rule 47** | **✔** |
| **9.1.1** | *(official title unknown)* | **VAT return without input tax credit** (NEW FY2026-27) | For registered persons **not** availing credit: traders not taking credit, commercial importers supplying under final settlement, traders paying VAT on actual value addition | Those persons | Same deadlines as 9.1 | **rule number not established** | ⚠ |
| **9.2** | টার্নওভার কর দাখিলপত্র | **Turnover tax return** | Return for enlisted persons | Enlisted person | **Quarterly** — tax paid **before** filing (s.63(2)) | **Rule 47** | **✔** |
| 9.3 | বিলম্বে দাখিলপত্র পেশের আবেদন | Application for late submission | Seek the Commissioner's permission (s.65) | Registered / enlisted person | Before or at late filing | Rule 48 | **✔** |
| 9.4 | দাখিলপত্র সংশোধনের আবেদন | Application for amendment of return | Correct clerical errors (s.66) | Taxpayer | On discovery | Rule 49 | **✔** |

**Other forms in the Rules 2016, with verified rule numbers** (not catalogued in the TOML,
because the research recorded the rule number but not enough detail to describe them honestly):
3.1 / 3.2 VAT agent appointment and certificate (Rule 16); 10.1 / 10.2 / 10.3 refunds to
diplomatic and international bodies, foreign tourist refund and tourist refund certificate
(Rules 55, 56, 57); 12.x seizure, freeze and penalty (Rules 60–65); 13.1–13.3 supervised supply
and surveillance (Rule 66); 14.1–14.14 arrears recovery (Rules 68–91); 16.1 / 16.2 offence
investigation (Rule 96); 17.1–17.3 alternative dispute resolution (Rules 99, 102); 18.1 VAT
consultant licence (Rule 109); 18.2 certified copies (Rule 115); 18.3–18.5 VAT clearance and
honour certificate (Rule 116); 18.6 declaration of the balance in the VAT Act 1991 current
account (Rule 118). **Sector variants:** **Mushak 6.3(ka)** (chronological tax invoice) and
**Mushak 6.2.1(ka)** apply to certain specified sectors.

### 7.1 Mushak 6.3 — the operational points that decide whether a credit survives

**Required contents:** date **and time** of issue; the supplier's name, address and BIN; the
**buyer's** name, address and BIN where the supply value exceeds
`vat.thresholds.tax_invoice_buyer_bin` ⚠; description; quantity; value excluding VAT; the VAT
rate; and the VAT amount. **s.46(1)(cha) kills the buyer's credit outright** where the invoice
omits either party's name, address or BIN — so this is the buyer's problem as much as the
seller's.

**What is allowed for FY2026-27** **✔**: two copies for all supplies; **a commercial invoice can
serve as a Mushak 6.3** if it carries all the prescribed particulars; it may be issued through the
entity's **ERP and preserved electronically** (Rule 40); and for **mobile financial services**,
online notifications or statements can be treated as a Mushak 6.3.

### 7.2 Mushak 4.3 — the coefficient, and the two ways it costs money

A fresh **Mushak 4.3** is triggered where product prices or total material costs move beyond
`vat.input_tax_credit.input_value_change_tolerance` **✔** (VSR 2016 Rule 9; SRO 254/2026; General
Order 05/2026). Two separate consequences of getting it wrong: **s.46(1)(da)** denies credit on
any input not declared in the coefficient, and **s.85(1)(ঢ)** charges a penalty for filing it
late.

⚠ **Commercial importers and traders may be excused** where value addition is at least
`vat.input_tax_credit.coefficient_exemption_value_addition` and the supply is at the standard
rate — but that rests on PwC and Tuhin & Partners describing SRO 254/2026 and General Order
05/2026, **neither of which was opened**, and SRO 254 sits inside the range NBR has not uploaded.
⚠ Whether **service industries** must declare a coefficient at all **sits uneasily with Rule 21
and awaits NBR clarification**.

## 8. Records and retention — s.107

**What must be kept — s.107(2)** **✔**: purchase statements for goods, services or immovable
property (**taxable or exempt**) with their invoices; sales statements; tax invoices, credit and
debit notes **issued and received**, and **VDS certificates**; customs documents for imports and
exports; supply prices, the **input-output coefficient**, and records of discounts and rebates
given by the manufacturer; records of SD-liable services supplied or SD-liable goods
manufactured; **treasury challans** and other proof of tax deposit; **the return for every tax
period**; and anything else prescribed.

**How long — s.107(1)**: `vat.record_retention.years` **✔**. That is a **floor, not a ceiling**:
under **s.107(3)** (added FA 2019 s.96), documents relating to an **unresolved proceeding must be
kept until that proceeding concludes**, however long it runs. The VAT period is not the same as
the income-tax period — check `bookkeeping-standards.md` before destroying anything.

**⭐ Electronic records are now expressly good — s.107(2A), substituted by Finance Act 2026 s.14.**
A registered person may keep tax documents, accounts and other records **on a server via ERP
software or Board-prescribed VAT software** with proper security; such records are **legally
admissible evidence** and may be **presented electronically** to the VAT authorities. **✔** Key:
`vat.record_retention.electronic_records`.

⚠ **Software mandate:** a business above `vat.thresholds.vat_software_mandatory` is said to have
to keep its VAT books in NBR-compliant VAT software (KPMG p.71) — **the underlying provision was
not identified**. ⚠ **Audited accounts to the VAT authority** within
`vat.record_retention.audited_accounts_to_vat_authority_months` (KPMG p.70) — again, **no
provision identified**. Ask the circle which rule imposes each before treating either as hard.

⚠ **Two things that could NOT be traced to any current provision** and are probably repealed VAT
Act 1991 relics: a **chartered-accountant-certified annual VAT statement**, and a standalone VAT
**price declaration (মূল্য ঘোষণা)**. If someone asks TakaBooks to prepare either, say the
provision could not be found.

## 9. Penalties and interest — s.85 and s.127

Figures live in `vat.penalties.*` and `vat.appeals.*`. Two corrections matter more than the rest:

> ⚠️ **The late-return fee is not Tk 10,000.** It is the amount at
> `vat.penalties.late_return_fee` **✔** — s.85(1)(চ), reduced by Act 89 of 2026 s.16(ক). The
> Tk 10,000 figure that circulates belongs to **other** s.85 items: failing to apply for
> registration in time, failing to display the certificate, failing to notify a change of
> information, failing to issue a tax invoice / credit note / debit note / VDS certificate,
> failing to keep prescribed records, and filing the input-output coefficient late.

> ⚠️ **Interest is 1% per month, not 2%.** `vat.penalties.interest_per_month` **✔** — s.127(1).
> The rate was 2% until the Finance Act 2021 halved it. Accrual is capped at
> `vat.penalties.interest_max_months` **✔**. VDS arrears run on a different basis:
> `vat.penalties.vds_arrears_interest_per_half_year` **✔**.

Structural points worth knowing **✔**: penalty is payable **in addition to** the VAT, SD, turnover
tax, interest and fine (s.85(5)); a hearing must precede every penalty **except** one for late
filing (s.85(4)); **no penalty arises where the shortfall came from mistake or misinterpretation
and the final tax with interest is subsequently paid** (s.85(2ক)); and no late-filing penalty
arises for tax periods during a **temporary shutdown for want of supplies** (s.85(4A)).

**New under the Finance Act 2026:** overstating a decreasing adjustment or understating an
increasing one is now penalised in its own right (s.85(1)(ঝ)); tobacco-product evasion via fake or
absent stamp or band roll, or storage outside registered premises, is penalised up to **double**
the evaded tax (s.85(1)(ত)); and **tampering with NBR-approved VAT software** is penalised up to
double the evaded tax with **both the software provider and the user liable** (s.85(1)(থ)). Act 89
of 2026 s.25 also extended s.127(1) interest to cover **irregularly taken rebates and decreasing
adjustments** — so a wrong credit now costs interest as well as a penalty.

**VDS failure is personal — s.85(1A)** **✔**. Unwithheld or undeposited VAT is recovered from the
withholder **as if he were the supplier**, with s.127 interest, **plus a personal fine on the
deductor, on the person responsible for depositing, and on the entity's chief executive**.

**Appeals got much cheaper.** Pre-deposits on the disputed tax (excluding penalty) were all cut
from a tenth by Finance Act 2026 §§15–17: `vat.appeals.commissioner_appeals_predeposit`,
`vat.appeals.appellate_tribunal_predeposit`, `vat.appeals.high_court_predeposit` — all **✔**.

**Closing window:** the **legacy VAT interest-waiver scheme under new s.137A** (১৩৭ক), for demands
under the repealed VAT Act 1991 and specified periods under the 2012 Act, runs for **six months
from 1 July 2026**, with secondary reporting giving a hard close of **31 December 2026**. If a
client has an old VAT demand, this is the last quarter to use it. The waiver is of **interest**;
the tax and any penalty are a separate question, and the mechanics of the scheme were not read
from the section itself. `compliance-calendar.md` §7 states this in the same terms.

## 10. What `vat.py` must tie out, and what to do on a break

The ledger, the registers and the return are three views of the same money. A VAT run is only
finished when all three agree:

1. **Ledger → register.** Every line hitting a `vat_output` account must appear in the sales
   book (Mushak 6.2, or 6.2.1 for a trader); every line hitting a `vat_input` account must appear
   in the purchase book (Mushak 6.1 / 6.2.1). A `vat_input` line with no purchase-book entry is
   **not a credit** — s.46(1)(uma) — and must be reported as such, not netted off.
2. **Register → return.** The output and input totals for the three tax periods in the quarter
   must equal the corresponding Mushak 9.1 figures. Supplementary duty rides in the same return
   (s.64(4)) but keeps its **own ledger account and its own line** — it is never creditable
   (s.46(1)(ta)).
3. **Rate check.** Every rate written in a journal `tax_tag` must match a rate the rates file
   actually declares under `vat.rates.*`. A tagged rate that matches nothing declared is a
   warning, **never** a silent acceptance; and where every candidate node is a placeholder, the
   run must say the check was **skipped**, not that it passed.
4. **VDS.** Withheld VAT is a **deposit obligation with its own deadline**, not a reduction of the
   supplier's output tax in your books. The supplier's relief comes through the **decreasing
   adjustment** supported by the **Mushak 6.6** certificate.

**On a break, refuse.** Do not adjust a figure to make a reconciliation close. Report the break,
name the account and the period, and stop — a wrong number filed with NBR is worse than a
refusal.

## 11. What TakaBooks deliberately does NOT hold

Stated plainly, so nobody assumes silence means zero:

- **The Third Schedule goods lists.** The consolidated PDF's Bangla text layer does not decode
  goods descriptions. The illustrative goods examples in circulation (newsprint, thread, bricks,
  SIM cards) come from a secondary pre-Finance Act 2026 chart and are not held.
- **Which wholesale businesses qualify for the paragraph-4 rate, and on what conditions.** The
  rate itself is now held and verified, but paragraph (4) grants it only to *certain*
  wholesale businesses "subject to compliance with the prescribed conditions and procedure", and
  the instrument that prescribes them was not traced. TakaBooks holds the rate and **not** the
  entitlement test. See `vat.rates.reduced.wholesale_business`.
- **A node for ready-made garment marketing (S078.00).** S.R.O. 39-Ain/2025/275-Mushak gives it
  two rates — one for own-brand marketing and a lower one for non-own-brand — and both were read,
  but no TOML node exists for them yet. Take them from the S.R.O. directly.
- **A node for re-registration of a building**, which paragraph (3) sets at the small-building
  rate irrespective of size. The figure is quoted in the note on
  `vat.rates.reduced.building_construction_small`; there is no key of its own.
- **The digital-advertising rate and service code S007.20.** Announced, not gazetted. Still
  `placeholder = true`; the engine refuses it, and an advertising supply stays at the standard
  rate until the notification is sighted.
- **The exemption list.** The FY2026-27 exemption SRO is **SRO 127-AIN/2026/332-Musak dated
  7 June 2026** (replacing SRO 160-AIN/2025/288-Musak of 27 May 2025), amended by
  **SRO 255-Ain/2026/355-Mushak dated 30 June 2026** — and SRO 255 has not been uploaded by NBR,
  so the amended text could not be read. Ask NBR or the circle for the current consolidated
  exemption SRO before treating any supply as exempt. Only two exemption items are held, both
  unverified: `vat.exemptions.registered_startup_supplies` and
  `vat.exemptions.content_creator_freelancer`.
- **The Second Schedule (supplementary duty) in general**, and the import-stage SD figures for
  nicotine and heated-tobacco products, which exceed what a `unit = "percent"` node may hold.
- **Any Mushak 9.1 return-line number.** TakaBooks asserts none of its own; if you want a line
  map, take it from the form PDF and put it in `[[vat.return_form.line]]`.
- **A new service code S083.00** (semiconductor assembly, testing and packaging) was introduced
  for FY2026-27 and put on the mandatory VDS list — verified in SRO 140-Ain/2026/345-Mushak — but
  that is a withholding-side figure and belongs in the `[vds]` section, not here.

---

**Disclaimer.** This file is reference material, not professional advice. Nothing in it is a
substitute for reading the instrument, and no figure here or in the rates file should be relied on
for a filing without checking it against the current gazette. **Verify with a licensed Income Tax
Practitioner (ITP) or Chartered Accountant (CA) before you file anything with the National Board
of Revenue.** Anything marked **⚠** above is unsettled in the source pack — say so rather than
smoothing it over. **Absent beats wrong.**

Maintained by Moshiur Rahman (@bemoshiur) · TICON SYSTEM LTD — https://ticonsys.com · MIT
