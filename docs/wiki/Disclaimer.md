# Disclaimer — দাবিত্যাগ

Please read this page in full before relying on anything TakaBooks produces. It is written
carefully and it means what it says.

## 1. Not professional advice

TakaBooks — its reference files, its rates data, its Python engine, every bundle built from
it, and every answer an LLM gives while using it — is **not professional advice**. It is not
tax advice, legal advice, accounting advice or audit advice. It does not create an
adviser–client relationship of any kind with the maintainer, with Ticon Sys, or with any
contributor.

Bangladeshi tax law is decided by the Acts, the Rules, the gazetted SROs and NBR's circulars,
as read by the assessing officer and, on appeal, by the tribunals and courts. A reference file
or a script can summarise a mechanism; it cannot tell you how the law applies to your facts.

**Before you file anything with the National Board of Revenue (NBR), verify every figure with
a licensed Income Tax Practitioner (ITP) or a Chartered Accountant (CA).** That sentence is
printed at the end of every tax output the engine produces, and the core instruction requires
the assistant to end every tax reply with it. It is not a formality. It is the design.

এটি পেশাদার পরামর্শ নয়। জাতীয় রাজস্ব বোর্ডে (NBR) কোনো কিছু দাখিল করার আগে প্রতিটি সংখ্যা
লাইসেন্সপ্রাপ্ত আয়কর আইনজীবী (ITP) বা চার্টার্ড অ্যাকাউন্ট্যান্টের (CA) মাধ্যমে যাচাই করুন।

## 2. No affiliation with NBR or any authority

TakaBooks is an independent open-source project. It is **not** produced, endorsed, reviewed,
approved or certified by the National Board of Revenue (জাতীয় রাজস্ব বোর্ড), the Ministry of
Finance, the Financial Reporting Council, the Registrar of Joint Stock Companies and Firms,
the Institute of Chartered Accountants of Bangladesh, or any other authority or professional
body. Where the project names an NBR form, portal or circular, it does so to help you find the
official source; it makes no claim to represent that source.

## 3. What "verified" means, and what it does not

Every rate, threshold and deadline TakaBooks uses lives in a rates file
(`src/data/rates-AY<year>.toml`) and carries a `source` URL, an `as_of` date and a `verified`
flag. The project's rule is *absent beats wrong*: a figure that could not be confirmed from a
primary source is marked `verified = false`, and the engine surfaces that caveat on every
output that used it.

**`verified = true` means that a contributor read the figure from primary text at the cited
URL on the stated date.** It does not mean the figure is correct for your circumstances, still
in force on the day you file, free of conditions the note does not mention, or immune to the
next Finance Act, SRO or circular. Tax figures in Bangladesh change every year and sometimes
mid-year. The `as_of` date tells you how old the reading is; the `source` URL tells you where
to check it yourself.

**`verified = false` does not mean invented.** It means the figure was landed from a source
that is not primary text — usually a professional summary — and the node's `note` says why.
Such a figure is used, but every output that touches it carries a caveat naming the key. A
node marked `placeholder = true` is different again: it is schema, and the engine refuses it
outright unless you explicitly opt in.

Any output stamped **PROVISIONAL / অস্থায়ী — NOT FOR FILING** is a walkthrough of a method.
It is not a tax liability, a VAT position or a return figure, and it must never be filed. Read
the caveats list that accompanies it: it names every soft figure the computation rested on, so
you and your adviser can see precisely which part of the answer needs checking.

## 4. The engine's guarantees are narrow

The Python engine guarantees a small number of mechanical things: debits equal credits in
every entry it writes; every account it posts to exists in your chart; money is handled as
integer paisa and rounded half-up once; every statement it prints reconciles to the journal
it read, and it exits non-zero when something does not tie. Those guarantees are about the
*arithmetic on the data you gave it*. They say nothing about whether the data is complete,
whether a transaction was classified correctly, whether a tax tag reflects the law, or
whether the resulting figures are what NBR expects.

The classification — which account, which form, which section, which rate — is the part a
language model performs, and language models make mistakes. TakaBooks is built to make those
mistakes visible (facts listed, sources named, assumptions labelled, the tool's output quoted
rather than re-derived), not to prevent them. Read the working. Check the facts. Ask your
ITP or CA.

## 5. No warranty; limitation of liability

TakaBooks is released under the MIT License. The relevant paragraph of that licence applies
in full and is repeated here in substance:

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

In plain words: if you file a wrong figure, pay a penalty, miss a deadline, over- or
under-deduct tax, or suffer any other loss after using TakaBooks, the maintainer, Ticon Sys
and the contributors are not liable for it. The responsibility for what is filed rests with
the person who files it and with the licensed professional who advised them.

## 6. Not an e-filing tool

TakaBooks prepares figures and explains forms. It does **not** submit returns, does not
connect to any NBR system, does not generate a Mushak return or an income tax return in the
authority's official format, and does not assert that its reference numbers correspond to
line numbers on any official form unless the rates file carries an explicit, sourced map for
that form. Filing is a human act, done by you or your adviser on the official channel.

## 7. Your data stays with you — and that is your responsibility too

The engine reads and writes only inside the `--books` directory you point it at. It makes no
network calls, sends no telemetry and phones no one. Whether an LLM you paste your ledger
into keeps that data is governed by *that* provider's terms, not by TakaBooks. Do not paste a
real TIN, BIN, NID, bank account number or client ledger into any service whose data handling
you have not read and accepted. Keep backups of `books/`; it is plain text and versions well
under git.

## 8. Contributions are offered in the same spirit

Figures, references and code in TakaBooks are contributed by volunteers who cite primary
sources and mark what they could not confirm. The project reviews contributions but cannot
audit every figure against every circumstance. If you find a wrong or outdated figure, please
report it through the **Tax rule update** issue template
(`.github/ISSUE_TEMPLATE/tax-rule-update.yml`) with the NBR source and the assessment
year — publicly, so others are warned — as described on the
[Updating Tax Rates](Updating-Tax-Rates) page. A wrong number is a correctness bug, not a
security vulnerability, and it must not be hidden behind private disclosure.

## 9. When in doubt

- If a figure is marked `UNVERIFIED`, `PLACEHOLDER` or `not in rates file`: do not use it.
  Obtain it from NBR or your adviser.
- If an output is stamped `PROVISIONAL / অস্থায়ী`: do not file it.
- If the assistant gives you a number without naming the file it came from: ask it to.
- If the assistant does arithmetic instead of running the engine: stop, run the engine
  yourself, and compare.
- If anything on this page is unclear: treat the strictest reading as the right one.

---

**সংক্ষেপে / In short:** TakaBooks is a tool that keeps your books straight and helps you ask
the right questions. It is not your accountant. Verify with a licensed ITP or CA, and against
NBR, before you file.

TakaBooks — Moshiur Rahman ([@bemoshiur](https://github.com/bemoshiur)) · Ticon Sys — https://ticonsys.com · MIT licensed
