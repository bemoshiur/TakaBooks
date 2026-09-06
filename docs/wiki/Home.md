# TakaBooks — টাকাবুকস

**Bangladeshi bookkeeping and taxation for any LLM.** বাংলাদেশের হিসাবরক্ষণ ও কর — যেকোনো LLM-এর জন্য।

TakaBooks gives a capable language model — Claude, ChatGPT, Gemini, Kimi, DeepSeek, Llama,
Copilot, Cursor and others — two things it does not have on its own:

1. **Knowledge** — cited, versioned reference material on Bangladeshi আয়কর / income tax,
   মূসক / VAT (Mushak), উৎসে কর কর্তন / TDS, উৎসে মূসক কর্তন / VDS, statutory bookkeeping,
   payroll and the compliance calendar, with every figure carrying a source URL and a
   `verified` flag.
2. **Tooling** — a dependency-free Python engine that keeps real double-entry books
   (খতিয়ান / ledger) and computes every number deterministically.

The model classifies and explains. Python adds, subtracts, allocates and rounds. That split is
the whole design: **the LLM never does arithmetic**, and no script will ever "fix" an entry
that does not balance — it refuses, loudly, with a non-zero exit code.

> **Read this before anything else.** TakaBooks is not professional advice, has no
> connection with the National Board of Revenue (NBR), and comes with no warranty. Verify
> every figure with a licensed Income Tax Practitioner (ITP) or Chartered Accountant (CA),
> and against NBR, before you file. The full statement is on the [Disclaimer](Disclaimer)
> page. এটি পেশাদার পরামর্শ নয় — দাখিলের আগে লাইসেন্সপ্রাপ্ত আইটিপি বা সিএ-এর সঙ্গে যাচাই করুন।

## Who it is for

| You are… | TakaBooks gives you… |
| --- | --- |
| An SME owner or proprietor keeping your own books | A chart of accounts built for Bangladesh, a journal that cannot go out of balance, monthly রেওয়ামিল / trial balance, লাভ-ক্ষতি হিসাব / profit and loss and স্থিতিপত্র / balance sheet, and an assistant that asks the right questions before it answers |
| A bookkeeper or accountant serving several clients | One `books/` directory per client, plain CSV and TOML you can open in Excel or a text editor, and a VAT position you can reconcile line by line against the return |
| An ITP or CA supporting an assistant | A tool that shows its working, states the assessment year on every output, flags every unverified figure, and ends every tax output with a reminder to verify with you |
| A developer or agent builder | A stdlib-only Python engine with `--json` on every script, an open Agent Skills bundle, and an `AGENTS.md` that any coding agent reads |

TakaBooks is **not** a replacement for a licensed ITP or CA, **not** an e-filing robot — it
prepares figures, humans file them — and **not** a general-purpose accounting suite. It is
Bangladesh-specific and SME-focused.

## What is in the box

| Part | Where | What it does |
| --- | --- | --- |
| Core instruction | [`src/core/`](https://github.com/bemoshiur/TakaBooks/tree/main/src/core) | Identity, workflow rules, bookkeeping rules and the routing table that tells the assistant which reference to read |
| References | [`src/references/`](https://github.com/bemoshiur/TakaBooks/tree/main/src/references) | One file per subject: income tax, VAT / Mushak, TDS / VDS, bookkeeping standards, payroll, compliance calendar, penalties, and a বাংলা ↔ English glossary |
| Rates | [`src/data/rates-AY<year>.toml`](https://github.com/bemoshiur/TakaBooks/tree/main/src/data) | **Every** rate, threshold and deadline, keyed by করবর্ষ / assessment year, each with its source and verification state. Nothing statutory lives anywhere else |
| Engine | [`src/engine/`](https://github.com/bemoshiur/TakaBooks/tree/main/src/engine) | `init_books.py`, `post.py`, `validate.py`, `report.py`, `vat.py`, `tax.py`, `rates.py` and the shared library `takabooks.py` |
| Bundles | `dist/` (generated) and [Releases](https://github.com/bemoshiur/TakaBooks/releases) | One build target per platform: Claude Skill, ChatGPT, Gemini, a single universal file, and `AGENTS.md` |

Python 3.11 or newer, standard library only. There is nothing to `pip install`.

## Where things stand — read the file headers, not this page

TakaBooks is built so that its *status* is visible from the files themselves, and you should
trust those over any summary, including this one:

- The rates file declares its own state in `[meta]` (`status`, `placeholder`, `verified`),
  and every node in it carries `verified` and `source`. Run
  `python3 src/engine/rates.py --assessment-year <AY>` for an audit that counts verified,
  unverified and placeholder nodes. While a file is a placeholder schema, the engine refuses
  to compute from it unless you opt in, and then stamps the output **PROVISIONAL / অস্থায়ী**.
- Every reference file opens with **Current as of**, **Sources** and **Status** lines. A
  reference marked `STUB` carries no verified content, and the assistant is instructed not to
  answer from it.

Absent beats wrong. A figure nobody has checked must never look checked.

## Where to go next

| Page | Read it when… |
| --- | --- |
| [Installation](Installation) | You want TakaBooks inside Claude, ChatGPT, Gemini, Kimi, DeepSeek, a local Llama, Cursor or Copilot |
| [Getting Started](Getting-Started) | You want to create your first books, post your first entry and print your first report, end to end |
| [Chart of Accounts](Chart-of-Accounts) | You need to understand the account codes, the `role` keys, or add accounts of your own |
| [Journal Format](Journal-Format) | You want the CSV schema and the `tax_tag` grammar, documented for humans |
| [Engine Reference](Engine-Reference) | You need every script, every flag, every exit code |
| [Updating Tax Rates](Updating-Tax-Rates) | A Finance Act has passed, a figure is wrong, or you want to know how the rates file works |
| [Contributing](Contributing) | You want to fix something, add a verified figure, or improve a page |
| [FAQ](FAQ) | You have a short question |
| [Troubleshooting](Troubleshooting) | Something exited non-zero and you want to know why |
| [Disclaimer](Disclaimer) | Before you rely on any output |

## Links

- Repository: https://github.com/bemoshiur/TakaBooks
- Releases and bundles: https://github.com/bemoshiur/TakaBooks/releases
- Issues (bug reports and rate corrections): https://github.com/bemoshiur/TakaBooks/issues
- Design specification: https://github.com/bemoshiur/TakaBooks/blob/main/docs/superpowers/specs/2026-09-05-takabooks-design.md
- Maintainer: Moshiur Rahman ([@bemoshiur](https://github.com/bemoshiur)) · Ticon Sys — https://ticonsys.com
- License: MIT
