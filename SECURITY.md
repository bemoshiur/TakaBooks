# Security Policy — নিরাপত্তা নীতি

TakaBooks is a local, standard-library-only Python engine plus reference material that is
loaded into an LLM. It opens no network connection, sends no telemetry, and installs
nothing. That keeps its attack surface small, but not zero — and because its output can
end up in a return filed with the National Board of Revenue (NBR / জাতীয় রাজস্ব বোর্ড),
this project treats one more class of defect with the urgency normally reserved for
security bugs: **a materially wrong tax figure**.

This page covers both, and they are reported through **different** routes. Please read
the two short sections below before choosing one.

## Supported versions

| Version | Supported |
|---|---|
| Latest `1.x` release | Yes — security fixes and rate corrections |
| Older `1.x` releases | Upgrade to the latest `1.x`; fixes are not back-ported |
| Pre-release builds (`-rc`, `-beta`) and unreleased `main` | Best effort only |
| Anything below `1.0.0` | No |

A rate correction always ships as a new patch release of the current minor, with the
changed node named in [`CHANGELOG.md`](CHANGELOG.md).

---

## 1. Reporting a security vulnerability — privately

**Do not open a public issue for a vulnerability.**

Report it privately through GitHub's private vulnerability reporting:

**https://github.com/bemoshiur/TakaBooks/security/advisories/new**

That form is visible only to you and the repository maintainer. If the form is unavailable
(the maintainer has to enable it once in the repository settings), contact the maintainer
through the Ticon Sys website, https://ticonsys.com, and say that you have a security report
for TakaBooks; do not put the details on a public channel.

Please include:

- The version or commit you tested (`python3 src/engine/validate.py --version`).
- Exact steps or a minimal `books/` fixture that reproduces the problem. Strip real names,
  TIN/BIN numbers and amounts first.
- What an attacker gains, and what a user would have to do for it to happen.
- Whether you believe it is already being exploited.

What to expect:

- Acknowledgement within **7 days**.
- A fix or a documented mitigation, and a published advisory, as fast as severity warrants;
  the aim for anything that can alter a figure or touch files outside `books/` is
  **30 days**. You will be told the timeline and asked to keep the report private until
  the fix is released.
- Credit in the advisory and in `CHANGELOG.md` under **Security**, unless you ask not to be
  named.

### What counts as a vulnerability here

TakaBooks runs on the user's own machine with the user's own files, so most classic
web-app categories do not apply. These do:

- **Any path outside `--books` / `--dest` being read, written or deleted** — path traversal
  through `config.toml`, `accounts.toml`, journal file names, `--rates`, `--templates` or
  the installer's `--dist` / `--dest`.
- **The installer overwriting an existing install without `--force`**, or `--dry-run`
  writing anything.
- **Spreadsheet formula injection** — a value in the journal CSV or a report CSV that a
  spreadsheet would execute (cells beginning with `=`, `+`, `-`, `@`) reaching a file that
  TakaBooks wrote. The journal is designed to open in Excel; that is exactly where this
  bites.
- **A crafted TOML or CSV that makes a script emit a wrong figure while exiting 0**, or
  bypasses a refusal (unbalanced entry accepted, unknown account posted, placeholder rate
  used without `--allow-placeholder-rates`, `--strict` not failing when it should).
- **Silent use of `float` in money arithmetic** reachable from user input.
- **Supply chain** — a workflow in `.github/workflows/`, the `@bemoshiur/takabooks` npm
  package, or a release asset that could be substituted or tampered with; a third-party
  dependency appearing anywhere (there must be none).
- **Leaking a user's financial data or TIN/BIN** into any output, log, bundle or report
  where it does not belong.

### Out of scope

- **Wrong answers from an LLM** using a TakaBooks bundle on Claude, ChatGPT, Gemini or any
  other platform — the model inventing a rate, doing its own arithmetic, dropping the
  disclaimer. That is a content and behaviour defect: report it publicly as a
  [bug](https://github.com/bemoshiur/TakaBooks/issues/new/choose), naming the platform,
  model and prompt. It is not a vulnerability in TakaBooks.
- Vulnerabilities in the LLM platform itself, in Python, Node or the operating system.
- Anything that requires an already-compromised machine or account.
- The fact that `books/` is plain text on disk. TakaBooks does not encrypt the ledger;
  protecting that directory is the user's responsibility, like any other business file.

---

## 2. Reporting a materially wrong tax figure — publicly, and just as urgently

If TakaBooks states, or computes from, a **rate, threshold, deadline, form reference or
statute reference that is wrong for the assessment year it claims**, treat it exactly as
seriously as a security bug — and report it **publicly**, not through the private route.

**https://github.com/bemoshiur/TakaBooks/issues/new/choose → Rate correction**

Why public? A private report reaches one maintainer. A public issue is seen at once by
every user who is about to file on that figure, and by every fork and bundle built from it.
Hiding a wrong tax number to protect the project would put the project ahead of the people
it exists for. The reverse trade-off applies to vulnerabilities, which is why those stay
private until fixed.

Please include the same evidence standard that lands a rate in the first place (see
[`CONTRIBUTING.md`](CONTRIBUTING.md)):

- The **primary source** you checked — the Finance Act (অর্থ আইন), the SRO (প্রজ্ঞাপন /
  এসআরও), the NBR paripatra (আয়কর পরিপত্র) or the Act text on `bdlaws.minlaw.gov.bd` — as a
  URL, with the section, paragraph or page.
- The **assessment year (করবর্ষ)** the figure applies to.
- **What TakaBooks says** (file and node key, e.g.
  `src/data/rates-AY2026-27.toml` → `income_tax.individual.thresholds.general`, or the
  passage in `src/references/`) and **what the source says**.
- The date you read the source.

If you only suspect a figure is wrong and cannot find the primary source, say so — that is
still worth an issue. The maintainers would rather mark a node `verified = false` for a
week than leave a wrong number looking verified.

What to expect:

- Acknowledgement within **72 hours**.
- If the figure cannot be confirmed quickly, it is set to `verified = false` immediately,
  so every consumer starts surfacing the caveat. *Absent beats wrong.*
- The corrected figure lands with its source URL and `as_of` date, the matching prose in
  `src/references/` is changed in the same commit, and a **patch release** follows with the
  node key, old → new value, AY and source recorded in `CHANGELOG.md`.
- Credit in the changelog, unless you ask not to be named.

### What the engine already does to limit the damage

- No Bangladeshi figure exists in Python or prose; every one lives in
  `src/data/rates-AY<year>.toml` with `source`, `as_of` and `verified`.
- `src/engine/rates.py` refuses to guess an assessment year, has no default for a missing
  rate, rejects floats, and refuses to hand a `placeholder = true` value to a calculator
  unless the user explicitly opts in — and then stamps the output
  **PROVISIONAL / অস্থায়ী**.
- `vat.py --strict` exits non-zero if any figure it used is unverified, missing or does not
  reconcile. Use it before filing.
- Every tax output states the assessment year and the rates file it used, lists the caveat
  for every unverified figure it touched, and ends with the disclaimer: this is not
  professional advice; verify with a licensed Income Tax Practitioner (ITP) or Chartered
  Accountant (CA) before filing.

---

## Data handling

- TakaBooks reads and writes only under the `--books` directory you name (default
  `./books`) and, for the installer, the `--dest` you name. It never transmits anything.
- The reference material you paste into an LLM, and anything you type into that LLM, is
  governed by that platform's privacy policy, not by this project. Do not paste a real
  ledger, TIN or BIN into a hosted model unless you are comfortable with that platform
  holding it.

## Verifying what you downloaded

- Every GitHub Release ships `SHA256SUMS.txt` next to its assets. Check it:
  `sha256sum -c SHA256SUMS.txt`.
- The npm package `@bemoshiur/takabooks` declares zero dependencies; `npm ls` after install
  should show none.
- The workflows in `.github/workflows/` run with a deny-all `permissions: {}` at the top
  level and opt in per job.

## Disclosure policy

Coordinated disclosure. Security fixes are released with a GitHub Security Advisory; rate
corrections are released with a public changelog entry. Reporters are credited in both
unless they prefer otherwise. We do not pursue good-faith researchers who follow this
policy.

---

Maintained by **Moshiur Rahman** ([@bemoshiur](https://github.com/bemoshiur)) ·
**Ticon Sys** — https://ticonsys.com
