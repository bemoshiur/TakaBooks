---
layout: default
title: "TakaBooks — Bangladeshi Bookkeeping & Taxation for Any LLM"
description: "Double-entry bookkeeping, income tax, VAT/মূসক, Mushak forms, TDS/VDS and NBR compliance for assessment year 2026-27. A Claude Skill, a ChatGPT GPT, a Gemini Gem, and a portable bundle for any model. MIT licensed, zero dependencies."
---

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "TakaBooks",
  "alternateName": "টাকাবুকস",
  "applicationCategory": "FinanceApplication",
  "applicationSubCategory": "Accounting and Taxation",
  "operatingSystem": "Cross-platform (Python 3.11+)",
  "softwareVersion": "1.0.0",
  "license": "https://opensource.org/licenses/MIT",
  "url": "https://github.com/bemoshiur/TakaBooks",
  "downloadUrl": "https://github.com/bemoshiur/TakaBooks/releases/latest",
  "codeRepository": "https://github.com/bemoshiur/TakaBooks",
  "programmingLanguage": "Python",
  "inLanguage": ["en", "bn"],
  "countriesSupported": "BD",
  "description": "Bangladeshi bookkeeping and taxation for any large language model: double-entry books, income tax, VAT (মূসক) and Mushak forms, TDS/VDS withholding, payroll and the NBR compliance calendar for assessment year 2026-27.",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
  "author": { "@type": "Person", "name": "Moshiur Rahman", "url": "https://github.com/bemoshiur" },
  "publisher": { "@type": "Organization", "name": "TICON SYSTEM LTD", "url": "https://ticonsys.com" },
  "keywords": "Bangladesh tax, NBR, VAT, মূসক, Mushak, income tax, TDS, VDS, bookkeeping, double-entry, BDT, taka, Claude Skill, ChatGPT, Gemini, LLM, assessment year 2026-27"
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {"@type":"Question","name":"What is the tax-free income threshold in Bangladesh for assessment year 2026-27?",
     "acceptedAnswer":{"@type":"Answer","text":"Tk 4,00,000 for a general taxpayer, under the Finance Act 2026. Tk 4,50,000 for women and senior citizens aged 65 or above; Tk 5,25,000 for persons with disability and third-gender taxpayers; Tk 5,50,000 for gazetted war-wounded freedom fighters and July fighters; plus Tk 50,000 for a parent or legal guardian of a person with disability. Budget-day reporting widely quoted Tk 3,75,000, but that was the un-enacted Finance Bill figure — parliament raised each band before passing the Act."}},
    {"@type":"Question","name":"What is the VAT registration threshold in Bangladesh?",
     "acceptedAnswer":{"@type":"Answer","text":"Tk 50 lakh annual turnover for VAT registration, and Tk 30 lakh for turnover-tax enlistment, since 9 January 2025. Most published sources still print Tk 3 crore and Tk 50 lakh, which have been superseded."}},
    {"@type":"Question","name":"Are Bangladeshi VAT returns monthly or quarterly?",
     "acceptedAnswer":{"@type":"Answer","text":"Quarterly from 1 July 2026, due 15 days after the quarter ends (20 days for government bodies, banks, insurers and nil filers). They were previously monthly."}},
    {"@type":"Question","name":"Which SRO sets Bangladeshi withholding tax rates for FY 2026-27?",
     "acceptedAnswer":{"@type":"Answer","text":"S.R.O. 273-Ain/Aykar-5/2026, gazetted 5 July 2026 and effective 1 July 2026. It repealed S.R.O. 210-Ain/Aykar-1/2026 of 8 June 2026, which carried an identical Bangla title. Most TDS charts circulating online reproduce the repealed SRO 210 and are wrong."}},
    {"@type":"Question","name":"Can I use TakaBooks with ChatGPT or Gemini, or is it only for Claude?",
     "acceptedAnswer":{"@type":"Answer","text":"Any model. It ships as a Claude Skill, a ChatGPT Custom GPT bundle, a Gemini Gem bundle, an AGENTS.md file for Cursor and Copilot, and a single portable Markdown file for Kimi, DeepSeek, Llama or anything else."}},
    {"@type":"Question","name":"Is TakaBooks a substitute for an accountant?",
     "acceptedAnswer":{"@type":"Answer","text":"No. It is not professional advice, it is not affiliated with or endorsed by the National Board of Revenue, and no figure in it has been reviewed by a licensed Income Tax Practitioner or Chartered Accountant. Verify with a licensed ITP or CA before filing."}}
  ]
}
</script>

**Bangladeshi bookkeeping and taxation — for Claude, ChatGPT, Gemini, Kimi, or any LLM.**

Double-entry books, income tax, VAT/মূসক and the Mushak forms, TDS/VDS withholding, payroll and the NBR compliance calendar for **করবর্ষ / assessment year 2026-27** — with a zero-dependency Python engine that owns every calculation.

[⬇ Download v1.0.0](https://github.com/bemoshiur/TakaBooks/releases/latest){: .btn }
[⭐ Star on GitHub](https://github.com/bemoshiur/TakaBooks){: .btn }
[📖 Read the wiki](https://github.com/bemoshiur/TakaBooks/wiki){: .btn }

## Why it exists

Language models invent Bangladeshi tax figures. Confidently.

In a controlled baseline, **25 out of 25** unguided replies to real Bangladeshi tax questions fabricated numbers — giving *three different tax-free thresholds* for the same question, none of them the enacted **Tk 4,00,000**, and producing answers that differed by Tk 72,500 in tax on the same income.

TakaBooks reads every figure from a versioned rates file **at answer time, never from model memory**, and refuses to compute when a figure hasn't been landed.

## What's inside

| | |
|---|---|
| **Engine** | 7 Python modules, standard library only. Money is integer paisa, never float. Amounts print in lakh/crore grouping (৳12,34,567.89). **867 tests.** |
| **Tax data** | 436 rate nodes for AY 2026-27 — each with a source URL, an `as_of` date and a `verified` flag |
| **Bookkeeping** | Double-entry enforced — an unbalanced entry is refused, never silently corrected |
| **Bilingual** | Replies in Bangla, Banglish or English; statutory terms always paired |

## Install

| Platform | How |
|---|---|
| 🤖 Claude (claude.ai) | Upload `bd-bookkeeping-tax.zip` → Settings → Capabilities → Skills |
| 💻 Claude Code | Unzip into `~/.claude/skills/` |
| 💬 ChatGPT | Paste `instructions.md` into a Custom GPT, upload `knowledge/` |
| ✨ Gemini | Paste `gem-instructions.md` into a Gem, upload `knowledge/` |
| 🌏 Kimi · DeepSeek · Llama | Paste `takabooks-core.md` — 11 KB, fits any context |
| ⚙️ Cursor · Codex · Copilot | Drop `AGENTS.md` at your repo root |

## Frequently asked

**What is the tax-free threshold for AY 2026-27?** Tk 4,00,000 for a general taxpayer. Tk 4,50,000 for women and senior citizens 65+, Tk 5,25,000 for persons with disability and third-gender taxpayers, Tk 5,50,000 for gazetted war-wounded freedom fighters and July fighters. Budget-day press widely reported Tk 3,75,000 — that was the Finance *Bill* figure, raised before the Act passed.

**What is the VAT registration threshold?** Tk 50 lakh turnover to register, Tk 30 lakh to enlist for turnover tax, since 9 January 2025. Most sources still print Tk 3 crore.

**Are VAT returns monthly?** Not since 1 July 2026 — they are quarterly, due 15 days after quarter end.

**Which SRO sets FY 2026-27 withholding rates?** S.R.O. 273-Ain/Aykar-5/2026 of 5 July 2026. It repealed SRO 210, which most online TDS charts still reproduce.

**Is this a substitute for an accountant?** No — see the disclaimer below.

## ⚠️ Disclaimer

TakaBooks is **not professional advice**. It is **not affiliated with, endorsed by, or connected to** the National Board of Revenue or any government body. **No figure in it has been reviewed by a licensed Income Tax Practitioner or Chartered Accountant.** Verify with a licensed ITP or CA before filing anything.

এটি পেশাদার পরামর্শ নয় — দাখিলের আগে লাইসেন্সপ্রাপ্ত আইটিপি বা সিএ-এর সঙ্গে যাচাই করুন।

---

MIT licensed · Maintained by [Moshiur Rahman](https://github.com/bemoshiur) at [TICON SYSTEM LTD](https://ticonsys.com)
