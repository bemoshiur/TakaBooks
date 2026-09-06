<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/logo.svg">
    <img alt="TakaBooks — টাকাবুকস" src="assets/logo.svg" width="420">
  </picture>
</p>

<h1 align="center">TakaBooks · টাকাবুকস</h1>

<p align="center">
  <strong>Bangladeshi bookkeeping and taxation for any LLM.</strong><br>
  Double-entry books · income tax · VAT / মূসক · TDS / উৎসে কর কর্তন · payroll · NBR compliance calendar<br>
  Deterministic Python, zero dependencies. Works with Claude, ChatGPT, Gemini, Kimi, DeepSeek, Cursor, Copilot — anything that reads Markdown.
</p>

<p align="center">
  <a href="https://github.com/bemoshiur/TakaBooks/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/bemoshiur/TakaBooks/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/bemoshiur/TakaBooks/releases/latest"><img alt="Release" src="https://img.shields.io/github/v/release/bemoshiur/TakaBooks?sort=semver&label=release"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-green.svg"></a>
  <a href="https://www.python.org/"><img alt="Python 3.11+" src="https://img.shields.io/badge/python-3.11%2B-blue.svg?logo=python&logoColor=white"></a>
  <a href="#quickstart"><img alt="Dependencies: none" src="https://img.shields.io/badge/dependencies-none-brightgreen.svg"></a>
  <a href="#any-llm"><img alt="Works with Claude, ChatGPT, Gemini, any LLM" src="https://img.shields.io/badge/works%20with-Claude%20%C2%B7%20ChatGPT%20%C2%B7%20Gemini%20%C2%B7%20any%20LLM-7c3aed.svg"></a>
  <a href="CONTRIBUTING.md"><img alt="PRs welcome" src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg"></a>
  <a href="src/data/rates-AY2026-27.toml"><img alt="Assessment year 2026-27" src="https://img.shields.io/badge/AY-2026--27-orange.svg"></a>
</p>

---

**TakaBooks** turns any capable AI assistant into a careful Bangladeshi bookkeeper. It packages two things: cited, versioned **reference knowledge** on Bangladesh income tax (আয়কর), VAT / মূসক and the Mushak forms, TDS / VDS withholding, payroll and the NBR compliance calendar — and a dependency-free **Python engine** that keeps real double-entry books in plain CSV, prints amounts in taka the Bangladeshi way (৳ 12,34,567.89) and computes every figure itself. The LLM classifies and explains; Python does the arithmetic. If an entry does not balance, the engine refuses. It never "fixes" your numbers, and it never invents a tax rate.

> [!CAUTION]
> **TakaBooks is not professional advice, and it is not affiliated with, endorsed by or connected to the National Board of Revenue (NBR) or any government body.** Verify every figure with a licensed Income Tax Practitioner (ITP) or Chartered Accountant (CA) before you file anything.
> এটি পেশাদার পরামর্শ নয় — দাখিলের আগে লাইসেন্সপ্রাপ্ত আইটিপি বা সিএ-এর সঙ্গে যাচাই করুন। Full [disclaimer](#disclaimer) below.

> [!NOTE]
> **Where the project stands (September 2026).** The bookkeeping engine is complete and tested. The income-tax and VAT engines are complete, but the rates file for assessment year 2026-27 is still a schema of placeholders: no Bangladeshi rate, threshold or deadline has yet been landed from a primary source, and the engine refuses to compute from placeholders. A separate research pass is verifying the real figures. Details in [What it covers](#covers).

## 📑 Contents

- [🤖 Works with any LLM](#any-llm)
- [🚀 Quickstart](#quickstart)
- [🧮 The engine](#engine)
- [📚 What it covers — and what is still being verified](#covers)
- [⚠️ Disclaimer](#disclaimer)
- [🗓️ How the rates stay current after each Finance Act](#rates)
- [🧭 Repository layout](#layout)
- [🏗️ Design principles](#design)
- [🤝 Contributing](#contributing)
- [🇧🇩 বাংলায় সংক্ষেপে](#bangla)
- [📄 License and credits](#license)

<a id="any-llm"></a>
## 🤖 Works with any LLM

TakaBooks is **LLM-agnostic by design**. One source tree (`src/`) is built into a bundle for every major platform, and the Claude Skill is just one of those targets — not the identity of the project. Pick your assistant, run one command, and the same rules, the same chart of accounts and the same rates file travel with you.

| Platform | You install | Exact steps |
| :--- | :--- | :--- |
| 🟠 **Claude** — claude.ai, Claude Code, Claude Desktop | Claude Skill `bd-bookkeeping-tax/` (open [Agent Skills](https://agentskills.io) format) | `npx @bemoshiur/takabooks install claude` → lands in `~/.claude/skills/bd-bookkeeping-tax/`. Restart Claude and ask *"Set up my books with TakaBooks."* On **claude.ai**: Settings → Features → upload `bd-bookkeeping-tax-skill-<version>.zip` from [Releases](https://github.com/bemoshiur/TakaBooks/releases/latest). |
| 🟢 **ChatGPT** — Custom GPT | `instructions.md` (built to fit the 8,000-character cap) + `knowledge/` (≤ 20 files) | `npx @bemoshiur/takabooks install chatgpt` → `./takabooks-chatgpt/`. Open the [GPT editor](https://chatgpt.com/gpts/editor) → **Configure** → paste `instructions.md` into *Instructions* (do not append to it) → upload every file in `knowledge/` under *Knowledge*. |
| 🔵 **Gemini** — Gem | `gem-instructions.md` + `knowledge/` (exactly ≤ 10 files, merged by the build) | `npx @bemoshiur/takabooks install gemini` → `./takabooks-gemini/`. Open [Gems](https://gemini.google.com/gems/create) → paste `gem-instructions.md` → attach every file in `knowledge/`. |
| 🟣 **Kimi, DeepSeek, Mistral, Qwen, Llama — any chat** | `takabooks-complete.md` — one self-contained file, every cross-reference is an in-file anchor | `npx @bemoshiur/takabooks install universal` → `./takabooks-complete.md`. Paste it as the system prompt or first message, or upload it as a document. Web chats cannot run Python, so the bundle tells the model to hand you the command and ask for the output back — it must not do the sums itself. |
| ⚫ **Ollama, LM Studio, self-hosted** | the same `takabooks-complete.md` | Use it as the Modelfile `SYSTEM` prompt or a saved system-prompt preset. Small local models follow short instructions better: attach the file as a document and keep the system prompt to the rules at its top. |
| 🟡 **Cursor, GitHub Copilot, OpenAI Codex, Windsurf, Zed, Aider, Jules…** | `AGENTS.md` (the [agents.md](https://agents.md) cross-agent standard) | `npx @bemoshiur/takabooks install agents` → `./AGENTS.md` in your project root. Tools that follow the standard read it automatically. **Claude Code** reads `CLAUDE.md` instead: put `@AGENTS.md` on the first line of a root `CLAUDE.md`. |
| 🧩 **Codex CLI, Gemini CLI and other Agent Skills readers** | the same skill folder | Unzip `bd-bookkeeping-tax/` into that tool's skills directory (Codex CLI: `~/.codex/skills/`). `SKILL.md` carries only `name`, `description`, `license`, `compatibility` and `metadata`, so it is valid everywhere. |

> [!TIP]
> **Custom skills do not sync across surfaces.** claude.ai, the Claude API and Claude Code are three separate installs; a Custom GPT and a ChatGPT Project are two. Install once per place you work.

### Three ways to get the bundles

**1 · The installer (Node 18+).** The npm package is published to **GitHub Packages**, which requires a GitHub token even for public packages — a machine that has never authenticated gets a `401`. One-time setup:

```ini
# ~/.npmrc
@bemoshiur:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=${NODE_AUTH_TOKEN}
```

```bash
export NODE_AUTH_TOKEN="$(gh auth token)"      # any token with read:packages
npx @bemoshiur/takabooks list                  # what is available and where it goes
npx @bemoshiur/takabooks install claude        # or chatgpt · gemini · universal · agents
```

The installer is a single dependency-free script, never overwrites an existing install without `--force`, supports `--dest`, `--dry-run` and `--json`, and works on macOS, Linux and Windows.

**2 · Download — no account, no Node.** Every [release](https://github.com/bemoshiur/TakaBooks/releases/latest) attaches `bd-bookkeeping-tax-skill-<version>.zip`, `takabooks-chatgpt-<version>.zip`, `takabooks-gemini-<version>.zip`, `takabooks-complete-<version>.md`, `AGENTS-<version>.md` and a `SHA256SUMS.txt` to verify them.

**3 · Build from source.** `python3 build/build.py` regenerates everything into `dist/` from `src/` — deterministically, byte-identical on every run — then `node bin/takabooks.mjs install <target> --dist ./dist`, or copy the files by hand.

<a id="quickstart"></a>
## 🚀 Quickstart

You need **Python 3.11 or newer** and nothing else. No `pip install`, no virtualenv, no compiler, no network — TakaBooks is standard-library only, on purpose, because the target user is an SME owner or bookkeeper on an ordinary office laptop.

```bash
git clone https://github.com/bemoshiur/TakaBooks.git
cd TakaBooks
python3 --version        # 3.11+ — the engine fails fast with a clear message below that
```

**1 · Open a set of books.** The scaffold ships a 42-account Bangladeshi chart of accounts (হিসাব তালিকা) with Bangla and English names, including the VAT, TDS, VDS, advance-income-tax, provident-fund, gratuity, WPPF and supplementary-duty accounts an NBR-facing business needs.

```bash
python3 src/engine/init_books.py --books ./books \
    --name "Padma Traders" --name-bn "পদ্মা ট্রেডার্স" \
    --business-type proprietorship --vat-registered yes
```

```text
TakaBooks — books ready: ./books
  business        Padma Traders (পদ্মা ট্রেডার্স)
  হিসাব তালিকা / chart of accounts  42 accounts from built-in Bangladesh chart of accounts
  income year opens  (not set — fill it in before any report)
  করবর্ষ / assessment year  (not set — fill it in before any tax output)
  মূসক / VAT registered  yes
```

TakaBooks will not guess your income year or your assessment year (করবর্ষ) — you set them in `books/config.toml`, and every tax output states which one it used.

**2 · Post an entry.** Debits and credits, in taka. The engine converts to integer paisa internally, so nothing is ever a floating-point number.

```bash
python3 src/engine/post.py --books ./books --date 2026-07-15 \
    --description "Cash sale of goods" --party "Rahim Store" --doc-ref INV-0001 \
    --debit 1100=1234567.89 --credit 4100=1234567.89
```

```text
posted JE-2026-07-0002 → ./books/journal/2026-07.csv (appended)  [entry_id generated]
  2026-07-15  Cash sale of goods
  party Rahim Store · doc_ref INV-0001
      account                              ডেবিট / debit  ক্রেডিট / credit
  Dr  1100 Cash in Hand (হাতে নগদ)         ৳12,34,567.89
  Cr  4100 Sales Revenue (বিক্রয় আয়)                       ৳12,34,567.89
  debits ৳12,34,567.89 = credits ৳12,34,567.89 — balanced
```

Notice the **lakh / crore grouping** — `৳12,34,567.89`, not `1,234,567.89`. It is the default everywhere; `--grouping international` switches it, and `digits = "bangla"` in `config.toml` prints `১২,৩৪,৫৬৭.৮৯`. A line that carries tax takes a structured `tax_tag` — `VAT:OUT:<rate>`, `VAT:IN:<rate>`, `TDS:<section>:<rate>`, `VDS:<rate>` — which is what the VAT and withholding reports are derived from. The rate itself is always read from the rates file for your assessment year, never typed from memory.

**3 · Try to post something wrong.**

```bash
python3 src/engine/post.py --books ./books --date 2026-07-22 \
    --description "Internet bill" --debit 6400=3500.00 --credit 1100=3000.00
```

```text
error: Entry 'JE-2026-07-0004' dated 2026-07-22 does not balance: debits ৳3,500.00 vs credits ৳3,000.00; ৳500.00 too much debit
  hint: Every entry must have equal debits and credits. TakaBooks never adjusts your numbers for you.
```

Exit code `5`. Nothing was written. That refusal is the whole design: the assistant reports it and stops; it does not "help" by moving ৳500 somewhere.

**4 · Check the whole ledger and run the statements.**

```bash
python3 src/engine/validate.py --books ./books
python3 src/engine/report.py --books ./books --from 2026-07-01 --to 2026-07-31 --statement tb
```

```text
TakaBooks — খতিয়ান যাচাই / ledger validation
Journal files            : 1 — 2026-07.csv
Rows                     : 6 data row(s) read · 6 posting(s) checked · 3 entry/entries
Total debits             : ৳37,79,567.89
Total credits            : ৳37,79,567.89
Difference               : ৳0.00
WARNINGS — review these; they are usually a typo or a missing declaration (2)
  1. [config-assessment-year] books/config.toml
     books.assessment_year (করবর্ষ / assessment year) is not set. Every tax output must state the year it was computed for.
     hint: Add assessment_year = "YYYY-YY" under [books]. TakaBooks will not assume one for you.
  ...
RESULT: 0 error(s), 2 warning(s) — no errors, but the ledger is not fully clean. (exit 7; pass --allow-warnings to accept warnings)
```

| Code | Account | Type | Debit (৳) | Credit (৳) | Balance (৳) |
| :--- | :--- | :--- | ---: | ---: | ---: |
| 1100 | Cash in Hand (হাতে নগদ) | asset | 12,34,567.89 | 0.00 | 12,34,567.89 |
| 1110 | Bank Account (ব্যাংক হিসাব) | asset | 25,00,000.00 | 45,000.00 | 24,55,000.00 |
| 3100 | Owner's Capital (মালিকের মূলধন) | equity | 0.00 | 25,00,000.00 | 25,00,000.00 |
| 4100 | Sales Revenue (বিক্রয় আয়) | income | 0.00 | 12,34,567.89 | 12,34,567.89 |
| 6200 | Office Rent (অফিস ভাড়া) | expense | 45,000.00 | 0.00 | 45,000.00 |
|  | **Total (সর্বমোট)** |  | **37,79,567.89** | **37,79,567.89** |  |

```text
**Debits equal credits** — ৳37,79,567.89 debit against ৳37,79,567.89 credit, difference ৳0.00. রেওয়ামিল মিলেছে / the trial balance ties.
- PASS trial_balance_debits_equal_credits
- PASS balance_sheet_assets_equal_liabilities_plus_equity — assets ৳36,89,567.89 vs liabilities ৳0.00 + equity ৳36,89,567.89
```

The profit and loss account (লাভ-ক্ষতি হিসাব) and balance sheet (স্থিতিপত্র) come from the same computation — `--statement pl`, `--statement bs`, or `--statement all` — and each run writes matching CSVs to `books/reports/`. Every report ends with the reconciliations it performed; if one fails, the script exits non-zero instead of printing a statement that does not tie.

**5 · Or just talk to your assistant.** With a bundle installed, the same flow is a conversation (illustrative):

```text
You:   Padma Traders sold goods for cash today, invoice INV-0001, ৳12,34,567.89. Record it.
LLM:   Facts — stated: date, cash, amount, invoice number. Needed: did the invoice carry মূসক / VAT?
       Classification: Dr 1100 Cash in Hand (হাতে নগদ) · Cr 4100 Sales Revenue (বিক্রয় আয়).
       Running: python3 src/engine/post.py --books ./books --date 2026-07-15 ... --json
       posted JE-2026-07-0002 — debits ৳12,34,567.89 = credits ৳12,34,567.89 — balanced.
```

The assistant picks the accounts, asks the one question that gates the entry, runs the script and quotes its output. It does not compute the total, and it does not state a VAT rate it has not read from the rates file.

### Your books are just files

```text
books/
├── config.toml          business name, TIN/BIN, income year, করবর্ষ, locale — edited by you
├── accounts.toml        chart of accounts with Bangla + English names and engine roles
├── journal/2026-07.csv  one row per posting line, human-readable BDT, opens in Excel
└── reports/             CSV output of every report you run
```

```csv
date,entry_id,description,account,debit,credit,party,doc_ref,tax_tag,memo
2026-07-15,JE-2026-07-0002,Cash sale of goods,1100,1234567.89,0.00,Rahim Store,INV-0001,NONE,
2026-07-15,JE-2026-07-0002,Cash sale of goods,4100,0.00,1234567.89,Rahim Store,INV-0001,NONE,
```

No database, no lock-in, nothing leaves your machine. Put `books/` in git, in Dropbox, or on a pen drive for your accountant.

<a id="engine"></a>
## 🧮 The engine

Seven scripts, standard library only. Every one offers `--help`, `--books <dir>` (default `./books`) and `--json` for machine-readable output, and every one exits non-zero — with a distinct exit code — on any integrity failure. Silent correction is forbidden.

| Script | Bangla | What it does |
| :--- | :--- | :--- |
| `init_books.py` | হিসাব খোলা | Scaffold `books/` — config, chart of accounts, journal and reports directories. Never guesses a statutory value. |
| `post.py` | জাবেদা | Validate and append one journal entry from flags or JSON. Refuses unbalanced, unknown-account, bad-date, bad-`tax_tag` or duplicate-id entries and writes nothing. |
| `validate.py` | খতিয়ান যাচাই | Whole-ledger integrity: 20 error checks and 14 warning checks, all reported at once (`--list-checks`). |
| `report.py` | রেওয়ামিল · লাভ-ক্ষতি · স্থিতিপত্র | Trial balance, profit and loss, balance sheet — Markdown to stdout and CSV to `reports/`, from one computation, with its reconciliations printed. |
| `vat.py` | মূসক | VAT position for a return period: output tax, rebateable input tax, net payable or carry-forward, VDS withheld, and the Mushak 9.1 line mapping — cross-checked against the ledger entry by entry. |
| `tax.py` | আয়কর | Individual income tax for an assessment year: progressive slabs, investment rebate, minimum tax and surcharge, with the full working shown. |
| `rates.py` | হারের নিরীক্ষা | Inspect a rates file: list assessment years, print one rate with its full provenance, audit how many figures are verified. |

**Money is integer paisa, never `float`.** Amounts are parsed with `decimal.Decimal`, rounded `ROUND_HALF_UP` once at the final step, and displayed with the ৳ symbol and the unit stated. The shared library `takabooks.py` — Money, Account, Entry, Ledger, TOML/CSV I/O, validation and Bangladeshi formatting — carries 230 unit tests of its own; the whole suite is over 570 tests and runs on Python 3.11, 3.12 and 3.13 in CI inside an empty virtualenv, so an accidental third-party import cannot slip through.

<a id="covers"></a>
## 📚 What it covers — and what is still being verified

Honesty about status matters more here than anywhere else in the README, because a wrong number that reaches NBR is worse than an absent one.

| Area | বাংলা | Engine | Reference text | Rates data (AY 2026-27) |
| :--- | :--- | :---: | :---: | :---: |
| Double-entry bookkeeping — journal, ledger, trial balance, P&L, balance sheet, 42-account BD chart | জাবেদা · খতিয়ান · রেওয়ামিল | ✅ complete | ✅ core rules shipped | n/a |
| Income tax — slabs, rebate, minimum tax, surcharge; corporate schema | আয়কর | ✅ `tax.py` complete | 🚧 scope drafted, figures pending | 🔴 placeholders |
| VAT / Mushak — position, input/output reconciliation, VDS, Mushak 9.1 figures | মূসক · মূসক ৯.১ | ✅ `vat.py` complete | 🚧 scope drafted, figures pending | 🔴 placeholders |
| Withholding — TDS and VDS via `tax_tag`, dedicated payable/receivable accounts | উৎসে কর কর্তন · উৎসে মূসক কর্তন | ✅ accounts and tags | 🚧 rate matrix pending | 🔴 placeholders |
| Payroll — salary, provident fund, gratuity, WPPF accounts | বেতন · ভবিষ্য তহবিল · গ্র্যাচুইটি | ✅ accounts | 🚧 scope drafted | 🔴 placeholders |
| Compliance calendar — every recurring NBR deadline | সম্মতি পঞ্জিকা | ✅ schema in rates file | 🚧 scope drafted | 🔴 placeholders |
| Penalties and interest exposure | জরিমানা ও সুদ | — | 🚧 scope drafted | 🔴 placeholders |
| Bookkeeping standards — Companies Act 1994, FRA 2015, IFRS/IAS | হিসাবরক্ষণ মানদণ্ড | — | 🚧 scope drafted | n/a |
| Glossary — Bangla ↔ English statutory and accounting terms | শব্দকোষ | — | ✅ about 200 term pairs | n/a |

**What "placeholders" means in practice.** `src/data/rates-AY2026-27.toml` is a complete schema — every slab, threshold, rebate rule, VAT rate, VDS service, TDS section and deadline has a named node — but every node is marked `placeholder = true`, `verified = false`, with an empty `as_of`. The research that lands the real figures from primary sources (the Finance Act, SROs, NBR circulars and the আয়কর পরিপত্র) is tracked in [`docs/research/`](docs/research/), and it is adversarially checked before it is merged. Until it lands, this is what the engine does:

```bash
python3 src/engine/tax.py --books ./books --income 1000000 --assessment-year 2026-27
```

```text
error: rates-AY2026-27.toml is a schema awaiting verified data — every figure in it is a placeholder.
  hint: No Bangladeshi rate has been landed for this assessment year yet. Fill the file in (its header documents the procedure), or pass --allow-placeholder-rates to compute a clearly-marked PROVISIONAL result that must never be filed.
```

That is deliberate. TakaBooks would rather give you no number than a number nobody checked. The bookkeeping half — everything in the Quickstart — needs no rates at all and is ready to use today.

<a id="disclaimer"></a>
## ⚠️ Disclaimer

Please read this before relying on anything TakaBooks produces.

- **Not professional advice.** TakaBooks is software plus reference text. It is not a licensed Income Tax Practitioner (ITP), Chartered Accountant (CA), lawyer or tax adviser, and nothing it outputs — a journal entry, a report, a tax computation, a deadline — is advice. **Verify every figure with a licensed ITP or CA before you file.**
- **Not affiliated with NBR or any government body.** TakaBooks is an independent open-source project. It is not affiliated with, endorsed by, sponsored by or connected to the National Board of Revenue (জাতীয় রাজস্ব বোর্ড), the Ministry of Finance, the Registrar of Joint Stock Companies, or any other authority of the Government of Bangladesh. Form names such as *Mushak 6.3* or *Mushak 9.1* are used only to refer to the public statutory forms they name.
- **Not an e-filing tool.** TakaBooks prepares figures and explains forms. Humans file returns.
- **Rates change, and some are unverified.** Every Finance Act re-rates something. Each figure in the rates file carries a source URL, an `as_of` date and a `verified` flag, and the engine labels anything unverified. Check the flag before you rely on a number, and check it again after a new Finance Act.
- **The assistant can still be wrong.** TakaBooks stops the LLM from doing arithmetic and from inventing rates, but the LLM still chooses which accounts a transaction hits and which rule applies. Review every classification. You are responsible for your books and your return.
- **No warranty.** Provided "as is" under the [MIT License](LICENSE), without warranty of any kind. The authors and Ticon Sys accept no liability for any loss arising from its use.

> **দাবিত্যাগ:** টাকাবুকস পেশাদার পরামর্শ নয় এবং এটি জাতীয় রাজস্ব বোর্ড (NBR) বা বাংলাদেশ সরকারের কোনো সংস্থার সঙ্গে সম্পৃক্ত, অনুমোদিত বা যুক্ত নয়। রিটার্ন দাখিলের আগে প্রতিটি সংখ্যা লাইসেন্সপ্রাপ্ত আয়কর আইনজীবী (ITP) বা চার্টার্ড অ্যাকাউন্ট্যান্ট (CA)-এর সঙ্গে যাচাই করুন।

<a id="rates"></a>
## 🗓️ How the rates stay current after each Finance Act

**No rate is ever hardcoded in prose or in code.** Every rate, threshold, slab, rebate rule, VDS service, TDS section and deadline lives in one machine-readable file per assessment year, `src/data/rates-AY<year>.toml`, and every consumer — the engine, the Claude Skill, the ChatGPT knowledge files, the Gemini Gem, the universal bundle — reads from it and prints which assessment year it used.

Each rate node looks like this (quoted verbatim from the current file, still a placeholder):

```toml
[deadlines.vat_return_monthly]
label_en = "Monthly VAT return (Mushak 9.1) filing deadline"
label_bn = "মাসিক মূসক দাখিলপত্র (মূসক ৯.১) দাখিলের সময়সীমা"
value = ""
unit = "date"
source = "https://nbr.gov.bd/"
as_of = ""
verified = false
placeholder = true
```

The format is enforced by `rates.py`, not merely recommended: money is in whole taka or a quoted decimal string (never a TOML float), percentages are percent (not fractions), and a `placeholder` node is refused unless the caller opts in explicitly.

**When a new Finance Act arrives:** copy the file to `rates-AY<next>.toml`, land the new figures, add one compliance-calendar entry. No Python changes. `rates.py --list` shows every assessment year available, and `config.toml` says which one your books use.

**Landing or correcting a figure** is the most valuable contribution you can make, and the bar is fixed:

1. Read the figure from a **primary source** — the Finance Act, the SRO, the NBR circular or paripatra, or the NBR page that publishes it. Not a news article, not a blog, not memory.
2. Set `value`, the exact `source` URL, the ISO `as_of` date you read it, `verified = true`, delete `placeholder = true`, and rewrite `note` to state every condition attached.
3. If you could not confirm it, leave `verified = false` and say so in `note`. A figure nobody checked must never look checked.
4. Open a PR that touches only the TOML, or an issue using the **Rate correction** template at [issues/new/choose](https://github.com/bemoshiur/TakaBooks/issues/new/choose) with the source URL and the assessment year. An incorrect rate is a *correctness* report, not a security one — please keep it public so everyone benefits.

Audit the current state at any time:

```bash
python3 src/engine/rates.py --assessment-year 2026-27         # verified / unverified / placeholder counts
python3 src/engine/rates.py --assessment-year 2026-27 --key vat.rates.standard   # one figure, full provenance
```

<a id="layout"></a>
## 🧭 Repository layout

```text
TakaBooks/
├── src/                        SOURCE OF TRUTH — platform-neutral
│   ├── core/                   identity, workflow, bookkeeping rules, tax routing (fits the 8k ChatGPT cap)
│   ├── references/             income-tax · vat-mushak · withholding-tds-vds · payroll · compliance-calendar
│   │                           penalties · bookkeeping-standards · glossary-bn-en
│   ├── data/                   rates-AY2026-27.toml — every figure, with source URL and verified flag
│   ├── engine/                 takabooks.py + init_books · post · validate · report · vat · tax · rates
│   └── templates/              accounts.toml, config.toml, journal header
├── build/build.py              one command → every bundle in dist/ + the root AGENTS.md
├── dist/                       generated, never hand-edited; attached to releases
├── bin/takabooks.mjs           the npx installer (Node built-ins only)
├── tests/                      unittest suite, stdlib only
├── docs/                       wiki source (mirrored to the GitHub Wiki) and research provenance
├── assets/                     logo.svg, logo-dark.svg, icon.svg, social preview
├── AGENTS.md                   generated — instructions for coding agents
└── .github/workflows/          ci.yml · release.yml · publish-packages.yml
```

Build targets: `claude-skill` · `chatgpt` · `gemini` · `universal` · `agents-md`. `python3 build/build.py --check` assembles everything in memory and verifies every platform limit without writing a byte; a build that would break a cap writes nothing at all.

<a id="design"></a>
## 🏗️ Design principles

| The LLM does | Python does |
| :--- | :--- |
| Decide which accounts a transaction hits | Add, subtract, allocate, round |
| Pick the right Mushak form or TDS section | Enforce debits = credits |
| Explain a rule and cite the statute | Compute slabs, rebates, VAT, TDS |
| Ask clarifying questions | Validate the entire ledger |

1. **The LLM never does arithmetic.** Deterministic Python owns every number; the model owns classification and explanation. A non-zero exit is a refusal, not a suggestion.
2. **Never invent a number.** A rate that could not be confirmed from a primary source is `verified = false`, and every consumer surfaces that caveat. Absent beats wrong.
3. **Integer paisa, never float.** `decimal.Decimal` in, `int` paisa inside, `ROUND_HALF_UP` once at the end.
4. **Standard library only, Python 3.11+.** Nothing to install on the SME's laptop, no network, no telemetry.
5. **Bangla beside English** for every statutory term — মূসক / VAT, উৎসে কর কর্তন / TDS, খতিয়ান / ledger — so users can find the form on the NBR portal. Replies come in the user's language: Bangla, Banglish or English.
6. **State the assessment year** on every tax output, and **end every tax output with the disclaimer**.
7. **One source, many bundles.** `src/` is the truth; `dist/` and `AGENTS.md` are generated, deterministic and byte-identical on every build.

Fuller context — the spec, the research provenance and the recovered AY 2026-27 research notes — lives in [`docs/`](docs/).

<a id="contributing"></a>
## 🤝 Contributing

Contributions are welcome: rate verifications, reference text, chart-of-accounts refinements, translations, bug reports, and real-world SME workflows we have not thought of. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md) first.

```bash
python3 -m unittest discover tests -v      # the suite must stay green
python3 build/build.py --check             # every bundle must still fit its platform cap
python3 build/build.py                     # regenerate dist/ and AGENTS.md
```

The non-negotiables, in one breath: no third-party Python dependency, ever; no `float` near money; no tax figure without a primary-source URL and a `verified` flag; never hand-edit `dist/` or the root `AGENTS.md`; no real taxpayer data (TIN, BIN, NID, bank details) anywhere in the repository — fixtures are synthetic. A pull request that changes a tax figure states which rates file it targets and cites its source. Security issues go through [SECURITY.md](SECURITY.md); wrong rates go through the public rate-correction template.

If TakaBooks helped you close your books, a ⭐ helps other Bangladeshi businesses find it.

<a id="bangla"></a>
## 🇧🇩 বাংলায় সংক্ষেপে

**টাকাবুকস** বাংলাদেশের ছোট ও মাঝারি ব্যবসার জন্য একটি ওপেন-সোর্স হিসাবরক্ষণ ও কর সহায়ক প্যাকেজ, যা যেকোনো AI সহকারীর সঙ্গে কাজ করে — Claude, ChatGPT, Gemini, Kimi, DeepSeek, Cursor, Copilot, যেটি আপনি ব্যবহার করেন।

- **দুতরফা দাখিলা পদ্ধতির হিসাব** — জাবেদা, খতিয়ান, রেওয়ামিল, লাভ-ক্ষতি হিসাব ও স্থিতিপত্র। সব হিসাব সাধারণ CSV ফাইলে থাকে, Excel-এ খোলা যায়, আপনার কম্পিউটারের বাইরে কিছুই যায় না।
- **AI কখনো নিজে অঙ্ক কষে না।** প্রতিটি সংখ্যা পাইথন ইঞ্জিন হিসাব করে; AI শুধু লেনদেন শ্রেণিবদ্ধ করে ও ব্যাখ্যা দেয়। ডেবিট-ক্রেডিট না মিললে ইঞ্জিন এন্ট্রি প্রত্যাখ্যান করে — কখনো নিজে থেকে সংখ্যা "ঠিক" করে না।
- **কোনো করহার, সীমা বা সময়সীমা বানিয়ে বলা হয় না।** প্রতিটি হার `src/data/rates-AY<করবর্ষ>.toml` ফাইলে থাকে, সঙ্গে উৎসের লিংক, তারিখ ও `verified` চিহ্ন। যাচাই না হওয়া হার থাকলে ইঞ্জিন তা স্পষ্টভাবে জানিয়ে দেয়।
- **বর্তমান অবস্থা (সেপ্টেম্বর ২০২৬):** হিসাবরক্ষণের অংশ সম্পূর্ণ ও পরীক্ষিত। ২০২৬-২৭ করবর্ষের হারের ফাইলটি এখনো শুধু কাঠামো — অর্থ আইন, এসআরও ও এনবিআর পরিপত্র থেকে যাচাই করে প্রকৃত হার যুক্ত করার কাজ চলছে। যাচাইয়ের আগে ইঞ্জিন কোনো কর হিসাব দেয় না।
- **টাকার অঙ্ক** লাখ/কোটি রীতিতে দেখানো হয় — ৳12,34,567.89 — আর `config.toml`-এ `digits = "bangla"` দিলে বাংলা অঙ্কে: ১২,৩৪,৫৬৭.৮৯।
- **ভাষা:** বাংলা, বাংলিশ বা ইংরেজি — যে ভাষায় প্রশ্ন করবেন, সেই ভাষায় উত্তর। প্রতিটি আইনি শব্দ বাংলা ও ইংরেজি দুইভাবেই থাকে (মূসক / VAT, উৎসে কর কর্তন / TDS), যাতে এনবিআর পোর্টালে ফরম খুঁজে পেতে সুবিধা হয়।

> **সতর্কতা:** টাকাবুকস পেশাদার পরামর্শ নয়। এটি জাতীয় রাজস্ব বোর্ড (NBR) বা কোনো সরকারি সংস্থার সঙ্গে সম্পৃক্ত বা অনুমোদিত নয়। রিটার্ন দাখিলের আগে লাইসেন্সপ্রাপ্ত আয়কর আইনজীবী (ITP) বা চার্টার্ড অ্যাকাউন্ট্যান্ট (CA)-এর সঙ্গে প্রতিটি সংখ্যা যাচাই করুন।

**শুরু করতে:** কম্পিউটারে Python 3.11 বা নতুন সংস্করণ থাকলেই যথেষ্ট — আর কিছু ইনস্টল করতে হবে না। উপরের [Quickstart](#quickstart) অনুসরণ করুন, আর আপনার AI সহকারীর জন্য বান্ডেল নিন [Works with any LLM](#any-llm) অংশ থেকে।

<a id="license"></a>
## 📄 License and credits

Released under the [MIT License](LICENSE). Use it, fork it, ship it inside your own tools — just keep the notice.

TakaBooks is maintained by **Moshiur Rahman** ([@bemoshiur](https://github.com/bemoshiur)) at **[Ticon Sys](https://ticonsys.com)** — a system-integration and software company founded in 2007, with its head office in Suwon, South Korea, an R&D centre in Dhaka, Bangladesh and a US office in Tysons Corner, Virginia, building AI, streaming, IoT, business-intelligence and cloud ERP solutions for enterprise and government clients. Ticon Sys is credited in every built bundle, and the project's homepage is [ticonsys.com](https://ticonsys.com).

If you cite TakaBooks in a paper, a practice note or a training course, use the **Cite this repository** button on GitHub, which reads [`CITATION.cff`](CITATION.cff).

<p align="center">
  <sub>TakaBooks · টাকাবুকস — Bangladeshi bookkeeping and taxation for any LLM · মূসক / VAT · উৎসে কর কর্তন / TDS · খতিয়ান / Ledger<br>
  Moshiur Rahman (@bemoshiur) · Ticon Sys — <a href="https://ticonsys.com">ticonsys.com</a> · MIT</sub>
</p>
