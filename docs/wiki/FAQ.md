# FAQ — সচরাচর জিজ্ঞাসা

Short answers. Each one links to the page with the long answer.

## About the project

**What is TakaBooks, in one sentence?**
A portable, LLM-agnostic Bangladeshi bookkeeping and taxation package: cited reference
material plus a dependency-free Python engine that keeps double-entry books and computes
every number. See [Home](Home).

**Is it a Claude thing?**
No. The Claude Skill is one build target among five. The same source builds a ChatGPT
bundle, a Gemini bundle, a single universal file for any LLM, and an `AGENTS.md` for coding
agents. Portability is the identity; see [Installation](Installation).

**Is it free?**
Yes. MIT licensed, maintained by Moshiur Rahman (@bemoshiur) at TICON SYSTEM LTD
(https://ticonsys.com).

**Can I use it for my business right now?**
You can keep books with it right now — the journal, validation and financial statements are
complete and do not depend on any tax figure. Tax computations depend on the rates file, and
you must check its verification state before relying on one: see
[Updating Tax Rates](Updating-Tax-Rates) and the [Disclaimer](Disclaimer).

**Is it an accountant?**
No. It is not professional advice, has no connection with NBR, and every tax output ends by
telling you to verify with a licensed ITP or CA before filing. [Disclaimer](Disclaimer).

**Can it file my return?**
No. It prepares figures and explains forms; humans file. It does not connect to any NBR
system and does not assert official form line numbers unless the rates file carries a
sourced map for that form.

## Tax figures

**Where are the tax rates?**
In `src/data/rates-AY<year>.toml`, one file per করবর্ষ / assessment year, every node with a
`source` URL, an `as_of` date and a `verified` flag. Nowhere else — not in prose, not in
code, not on this wiki. [Updating Tax Rates](Updating-Tax-Rates).

**Why does the wiki never state a rate?**
Because a page cannot carry a `verified` flag and cannot be corrected in one place when the
Finance Act changes. The wiki documents mechanisms and points at the file. If you find a
figure on a wiki page, it is a bug — open an issue.

**Why is my VAT output stamped PROVISIONAL?**
Because the rates file it read contains a placeholder or unverified figure among the ones it
read, and the engine will not let such a figure look final. The *amounts* from your journal
are exact; the statutory context is what is flagged. Read the warnings block — it names every
key. If none of them touches your supply, the arithmetic still stands, but that judgement is
yours or your ITP's, not the tool's. [Getting Started](Getting-Started), step 9.

**Does `tax.py` refuse to run?**
Not against the AY 2026-27 file. It refuses outright (exit 8) only when a rates **file**
declares itself a schema with `[meta] placeholder = true`, and that file no longer does — real
figures have been landed. It does still refuse an individual node that is marked
`placeholder = true`, and it stamps the whole output PROVISIONAL while any figure it used is
unverified, saying in the banner how many. `--allow-placeholder-rates` opts in to placeholder
nodes and produces a walkthrough of the method that must never be filed.
[Updating Tax Rates](Updating-Tax-Rates).

**What does `verified = true` actually promise?**
That a contributor read that value from primary text at the cited URL on the stated date. Not
that it applies to your facts, is still in force today, or survived the latest SRO. Check the
`as_of` date and the source yourself. [Disclaimer](Disclaimer), section 3.

**And what does `verified = false` mean — is the figure made up?**
No. It means the figure was landed from a source that is not primary text — typically a
professional summary — and the node's own `note` says why. It is used, with a caveat, rather
than refused. A `placeholder` node is the one that is refused. The distinction matters:
absent beats wrong, but "sourced but not primary" beats absent.

**A figure is wrong. Where do I report it?**
Publicly, using the **Tax rule update** issue template
(`.github/ISSUE_TEMPLATE/tax-rule-update.yml`), giving the dotted key, the assessment year,
the NBR source URL and the date you read it. A wrong figure is a correctness bug, not a
security issue. [Contributing](Contributing).

**A new Finance Act passed. What changes?**
One new rates file and one compliance-calendar entry, by design. No Python. The exact
procedure is on [Updating Tax Rates](Updating-Tax-Rates).

**My accountant told me a rate. Can the assistant use it?**
The core instruction says no: it will neither confirm nor lean toward a remembered figure. It
will say what would verify it and ask whether the accountant is a licensed ITP or CA. Put the
figure, with its source, into the rates file and it becomes usable.

## Books and the engine

**Do I need to install anything?**
Python 3.11 or newer. That is all — no `pip install`, no network at run time. On Windows,
`py -3` works where `python3` is not on the PATH. [Installation](Installation).

**Where do my books live?**
In a `books/` directory you choose (`--books DIR`, default `./books`): `config.toml`,
`accounts.toml`, `journal/YYYY-MM.csv`, `reports/`. Plain text; put it under git.

**Can I open the journal in Excel?**
Yes; amounts are human-readable BDT decimals for exactly that reason. Be careful *saving*
from a spreadsheet — dates and account codes get reformatted. [Journal Format](Journal-Format)
has the checklist; `validate.py` catches what slipped through.

**Why integer paisa?**
Because floating-point money drifts and a ledger must not. Every internal amount is an `int`
number of paisa; text is parsed with `decimal.Decimal`; rounding is half-up, once, at the end.

**Why `12,34,567.89` and not `1,234,567.89`?**
লাখ/কোটি grouping is how figures are written in Bangladesh, so it is the default. Switch with
`locale.grouping = "international"` in `config.toml` or `--grouping international` on
`report.py`. Bangla numerals: `locale.digits = "bangla"`.

**Why did `post.py` refuse my entry?**
Because something was wrong and TakaBooks never fixes an entry for you: debits ≠ credits
(exit 5), an unknown account (3), a malformed `tax_tag` (6), a bad date or duplicate id (4),
or several at once (7). The message names the line. [Troubleshooting](Troubleshooting).

**How do I correct a mistake I already posted?**
Post a reversing entry, then the correct one. Never edit or reuse the id of a posted entry.
[Journal Format](Journal-Format).

**What is a `tax_tag`?**
Structured text on a journal row — `VAT:OUT:<rate>`, `VAT:IN:<rate>`,
`TDS:<section>:<rate>`, `VDS:<rate>` or `NONE` — that tells `vat.py` which rows are taxable
value and which are tax. Tag both the value line and the tax-control line of an entry.
[Journal Format](Journal-Format).

**What is a `role` in `accounts.toml`?**
A key on the ten Bangladesh-specific accounts (`vat_output`, `vat_input`, `tds_payable`, …)
that lets the engine find them whatever code you gave them. Renumber freely; keep the roles.
[Chart of Accounts](Chart-of-Accounts).

**Can I add accounts?**
Yes. Pick the block by type, a free code, add `name_bn`, run `validate.py`. Retire accounts
with `tags = ["inactive"]` rather than deleting them. [Chart of Accounts](Chart-of-Accounts).

**Does `report.py` need a fiscal year?**
Only for `--period FY…`. TakaBooks never assumes when your income year opens; set
`books.fiscal_year_start` in `config.toml`. Month periods and `--from/--to` work without it.

**Can I run the engine from an LLM?**
Claude Code and other Agent Skills hosts run `scripts/*.py` directly; only the output enters
the conversation. Chat-only platforms cannot execute anything: the assistant gives you the
exact command and asks for the output back. [Getting Started](Getting-Started), step 11.

**Does the engine phone home?**
No. No network calls, no telemetry. It reads TOML and reads/appends CSV under `--books`.
What an LLM provider does with text you paste into it is governed by that provider's terms.

## Platforms

**Which LLM works best?**
Any capable model works; the differences are in packaging. Claude Code runs the engine
itself. ChatGPT and Gemini get the knowledge files and prepare commands. Kimi, DeepSeek and
local models get the single universal file. [Installation](Installation) has the table.

**Why is the ChatGPT instruction limited to 8,000 characters?**
That is the Custom GPT instruction field's cap (community-confirmed; OpenAI publishes no
official page for it). The core instruction is designed to fit, and the build fails rather
than emit an over-long file.

**Why does the Gemini bundle merge files?**
A Gem supports ten source documents. The merge is at whole-file level, never a truncation,
so every source URL and `verified` flag survives.

**`npx @bemoshiur/takabooks` gives 401.**
GitHub Packages requires authentication even for public packages. Either configure
`~/.npmrc` with a `read:packages` token, or download the release assets — same files.
[Installation](Installation).

**Skills on claude.ai do not appear in Claude Code.**
Correct: custom skills do not sync across surfaces. Install in each place.

**Does Claude Code read `AGENTS.md`?**
No — it reads `CLAUDE.md`. Put `@AGENTS.md` on the first line of a root `CLAUDE.md`.

## Contributing

**What is the most useful thing I can contribute?**
A tax figure read from a primary NBR source, with the URL and the date. Then a populated
reference. Then a bug report with a reproducible command. [Contributing](Contributing).

**I edited a wiki page in the browser and it vanished.**
The wiki is mirrored from `docs/wiki/` in the repository and the next sync overwrote it.
Open a pull request against `docs/wiki/` instead.

**Where is the design spec?**
https://github.com/bemoshiur/TakaBooks/blob/main/docs/superpowers/specs/2026-09-05-takabooks-design.md
— it is the binding contract for everything here.
