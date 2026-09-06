# Installation — ইনস্টলেশন

TakaBooks is one source tree built into one bundle per platform. This page covers getting a
bundle, then installing it in each LLM, then running the Python engine on your own machine.
Where a screenshot would help and cannot be shown, the screen is described in words.

## Prerequisites

| For | You need |
| --- | --- |
| Any chat platform (Claude, ChatGPT, Gemini, Kimi, DeepSeek, …) | An account on that platform. Nothing to install. |
| The numbers | **Python 3.11 or newer** on your own computer. The engine is standard library only — there is nothing to `pip install`, and nothing is downloaded at run time. Check with `python3 --version` (Windows: `py -3 --version`). Get Python from https://www.python.org/downloads/ if needed. |
| Cursor, Copilot, Codex, Windsurf | The repository checked out; they read `AGENTS.md` at its root. |
| The npm installer (optional) | Node 18 or newer, and a GitHub token (explained below). |

A chat platform without the engine can still classify entries, explain rules and prepare the
exact commands for you to run; it cannot compute a figure. The core instruction tells it to
say so and to ask for the engine's output back rather than do the arithmetic itself.

## Step 1 — get a bundle

### Option A: download from a release (recommended)

Go to https://github.com/bemoshiur/TakaBooks/releases/latest. Each release carries:

| Asset | For |
| --- | --- |
| `bd-bookkeeping-tax-skill-<version>.zip` | Claude (claude.ai upload, Claude Code, Claude API) and every other Agent Skills host (Codex CLI, ChatGPT Skills, Gemini CLI, Cursor, VS Code) |
| `takabooks-chatgpt-<version>.zip` | ChatGPT Custom GPT or Project: `instructions.md`, `knowledge/`, `README-install.md` |
| `takabooks-gemini-<version>.zip` | Gemini Gem: `gem-instructions.md`, `knowledge/`, `README-install.md` |
| `takabooks-complete-<version>.md` | Any other LLM — Kimi, DeepSeek, Llama, Mistral, local models: one paste-anywhere file |
| `AGENTS-<version>.md` | Coding agents: Cursor, Copilot, Codex, Windsurf, Gemini CLI |
| `SHA256SUMS.txt` | Checksums of every asset |

Verify a download before you trust it:

```bash
sha256sum -c SHA256SUMS.txt        # macOS: shasum -a 256 -c SHA256SUMS.txt
```

### Option B: build from source

```bash
git clone https://github.com/bemoshiur/TakaBooks.git
cd TakaBooks
python3 build/build.py             # every bundle into dist/, plus AGENTS.md at the root
```

`python3 build/build.py --check` verifies every platform limit without writing;
`--target chatgpt` (or `claude-skill`, `gemini`, `universal`, `agents-md`) builds one. The
build is deterministic — the same `src/` bytes produce byte-identical `dist/` bytes.

### Option C: the npm installer (GitHub Packages)

The package `@bemoshiur/takabooks` copies a built bundle to where a platform expects it:

```bash
npx @bemoshiur/takabooks install claude        # → ~/.claude/skills/bd-bookkeeping-tax/
npx @bemoshiur/takabooks install chatgpt       # → ./takabooks-chatgpt/
npx @bemoshiur/takabooks install gemini        # → ./takabooks-gemini/
npx @bemoshiur/takabooks install universal     # → ./takabooks-complete.md
npx @bemoshiur/takabooks install agents        # → ./AGENTS.md
npx @bemoshiur/takabooks list
```

Options: `--dest <path>` (install elsewhere), `--dist <path>` (read bundles from a checkout's
`dist/`), `--force` / `-f` (replace an existing install — it deletes the destination first),
`--dry-run` / `-n`, `--json`, `--quiet`, `--no-bangla`, `--help`, `--version`. It never
clobbers an existing install without `--force`, and exits non-zero on any failure.

**The catch:** the package is published to **GitHub Packages, not npmjs.com**, and GitHub
Packages requires authentication even to install a *public* package. On a machine that has
never authenticated, `npx @bemoshiur/takabooks` returns **401**. To use it, put two lines in
your `~/.npmrc`:

```
@bemoshiur:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=${NODE_AUTH_TOKEN}
```

and export `NODE_AUTH_TOKEN` as a GitHub **classic** personal access token with the
`read:packages` scope (fine-grained tokens do not work with the npm registry). If that is
more friction than you want, use Option A — the release assets are the same files.

From a checkout, without any registry: `node bin/takabooks.mjs install claude --dist ./dist`.

## Step 2 — install it where your LLM lives

### Claude Code

The skill folder goes under `skills/`, personal or per project:

```bash
# personal — available in every project
unzip bd-bookkeeping-tax-skill-<version>.zip -d ~/.claude/skills/

# project — checked in with the repository
unzip bd-bookkeeping-tax-skill-<version>.zip -d .claude/skills/
```

Either way you end up with `…/skills/bd-bookkeeping-tax/SKILL.md` plus `references/`,
`scripts/`, `data/`, `templates/`. The zip has the `bd-bookkeeping-tax/` folder at its root,
which is why `-d …/skills/` is the right target. A personal skill overrides a project skill
of the same name; an enterprise-managed one overrides both.

Then, in a project, start Claude Code and ask a Bangladeshi bookkeeping or tax question in
Bangla, Banglish or English — the skill is loaded by its description when the question
matches. The scripts run through Claude Code's shell; only their output enters the
conversation, which is exactly the design.

Claude Code reads `CLAUDE.md`, **not** `AGENTS.md`. To give it the repository's coding-agent
instructions too, create a two-line `CLAUDE.md` at the repository root:

```markdown
@AGENTS.md
```

### claude.ai (the web and desktop apps)

Screen by screen:

1. Open **Settings** (your initials or avatar, bottom-left on the web).
2. Go to **Features** (the section that lists optional capabilities). Make sure **code
   execution** is enabled — skills need it.
3. Find **Skills** and choose **Upload skill** (a button that opens a file picker).
4. Pick `bd-bookkeeping-tax-skill-<version>.zip`. The folder must be at the root of the zip;
   the release asset already is.
5. The skill appears in the list by name (`bd-bookkeeping-tax`) with its description.

Skills uploaded on claude.ai are **per-user**: there is no organisation-wide management, and
they do **not** sync to Claude Code or to the API. Install in each place separately.

### Claude API

Upload the same zip to the Skills endpoint (`/v1/skills`). `bd-bookkeeping-tax/SKILL.md` sits
at the top of a single enclosing folder, which is what the endpoint expects. Versions are
complete snapshots, not deltas — re-upload the whole file set every time. The API sandbox
has no network access and cannot install packages; TakaBooks needs neither.

### ChatGPT — Custom GPT (Free, Plus, Pro)

Unzip `takabooks-chatgpt-<version>.zip`. Then, screen by screen:

1. In ChatGPT, open **Explore GPTs** (left sidebar) and press **Create** (top right).
2. Switch from the *Create* tab to the **Configure** tab — a form with Name, Description,
   Instructions, Conversation starters, Knowledge, Capabilities.
3. **Instructions**: paste the *entire* contents of `instructions.md`. The field accepts
   8,000 characters; the file is built to fit and the build fails rather than produce an
   over-long one. If the field shows a character counter, it should be under the limit
   with a little headroom.
4. **Knowledge**: press **Upload files** and select **every** file in `knowledge/`. A Custom
   GPT holds up to 20 knowledge files; the bundle ships fewer. **Keep the file names** —
   the instruction refers to them by name.
5. **Capabilities**: Code Interpreter is useful (the GPT can run the engine on files you
   upload in a chat), not required.
6. **Save** (top right) → choose who can use it → **Create**.

The rates file is shipped as `rates-AY<year>.md` — Markdown with the TOML inside a fenced
block — because `.toml` is not on any published list of accepted upload types. Its values are
byte-identical to `src/data/`.

The engine scripts are not in the knowledge set: the GPT explains and classifies; the numbers
come from running the scripts locally, as `knowledge/engine-usage.md` describes.

### ChatGPT — Projects

Open a Project → **Project instructions** → paste `instructions.md`. Then **Add files** →
the `knowledge/` files. A project holds fewer files than a Custom GPT (as few as five on the
Free plan), so on a small plan add, in this order: the rates file, `30-tax-overview.md`, then
the reference you need for the task at hand.

### ChatGPT Skills and Codex CLI (Business, Enterprise, Edu)

Both read the open Agent Skills format, so use the **Claude Skill bundle**, not the ChatGPT
one:

- **Codex CLI**: unzip so that `~/.codex/skills/bd-bookkeeping-tax/SKILL.md` exists.
- **ChatGPT Skills**: upload the same zip under **Skills → Upload from your computer**.
  Skills in ChatGPT are limited to Business, Enterprise, Healthcare and Edu plans, and an
  administrator may have to enable them first.

### Gemini — Gems

Unzip `takabooks-gemini-<version>.zip`. Then:

1. Open Gemini → **Gems** (left sidebar) → **New Gem** (or **Gem manager → New Gem**).
2. Give it a name. In **Instructions**, paste the whole of `gem-instructions.md`. It is
   short on purpose — Gems drift away from their knowledge files under long instructions —
   and written in Google's Persona / Task / Context / Format shape.
3. Under **Knowledge**, press **Add files** (or *Upload from computer* / *Add from Drive*) and
   add **every** file in `knowledge/`. A Gem supports up to **10** source documents, which is
   why the bundle's files are merged; it ships exactly ten. The merge is at whole-file level,
   never a truncation, so every `source` URL and `verified` flag survives.
4. **Save**.

Tip for keeping rates current: Gemini reads the latest version of a Google Doc from Drive
automatically, but re-uploads other file types by hand. If you publish the rates knowledge
file as a Google Doc and add it *from Drive*, a rates update reaches every Gem that uses it
without a re-upload.

### Kimi, DeepSeek, Llama, Mistral, any other LLM — the universal file

`takabooks-complete-<version>.md` is one self-contained Markdown file: core instruction,
every reference, the rates table with the TOML in a fenced block, the engine commands with
their output shapes, and the glossary — with every cross-reference an in-document anchor.
Nothing outside the file exists.

- **Chat web apps (Kimi, DeepSeek, …)**: paste the whole file as the first message, or
  upload it as a document if the app supports uploads. It opens with a `STOP — READ THIS
  FIRST` block that the model sees before anything else.
- **Ollama**: put the file inside `SYSTEM """…"""` in a Modelfile, or attach it as context
  in whichever front end you use.
- **LM Studio / Open WebUI**: paste it into the system-prompt field and save it as a preset.

The file tells the model what to do when it **cannot run Python** — give the classification,
the account codes, the `tax_tag` and the rule in words, print the exact command, and ask for
the output back. Small local models (7–13B) follow short instructions better than long ones;
if yours drifts, use the universal file as an uploaded document and a shorter system prompt.

### Cursor, GitHub Copilot, Codex, Windsurf, Gemini CLI — `AGENTS.md`

`AGENTS.md` at the repository root is the cross-agent standard those tools read; the nearest
`AGENTS.md` up the directory tree wins. It is generated by the build and carries the
non-negotiables (never invent a rate; integer paisa; stdlib only; `src/` is the truth;
`dist/` is generated), the layout, the commands, and the content rules. Nothing to install:
check out the repository and the tool finds it. For Claude Code, add the two-line
`CLAUDE.md` shown above.

## Step 3 — the engine on your own machine

Whichever platform you use, the numbers come from Python running locally.

```bash
git clone https://github.com/bemoshiur/TakaBooks.git      # or unzip the skill bundle
cd TakaBooks
python3 src/engine/validate.py --help                     # prints usage → Python is fine
```

In the Claude Skill bundle the same scripts are at `bd-bookkeeping-tax/scripts/` and the
rates file at `bd-bookkeeping-tax/data/`; `scripts/USAGE.md` lists every command.

Windows notes: use `py -3 src\engine\validate.py --help` if `python3` is not on your PATH;
run in Windows Terminal or PowerShell so Bangla renders; the engine itself is unaffected by
what the console can display.

Then follow [Getting Started](Getting-Started).

## Verifying an install

| Platform | How to tell it worked |
| --- | --- |
| Claude Code | `ls ~/.claude/skills/bd-bookkeeping-tax/SKILL.md` exists; a Bangla bookkeeping question makes Claude read the skill and run `scripts/…` |
| claude.ai | The skill is listed under Settings → Features → Skills with the name `bd-bookkeeping-tax` |
| ChatGPT | The Configure tab shows the instructions with no truncation warning and every knowledge file listed |
| Gemini | The Gem shows ten knowledge documents |
| Universal | The model's first reply to "what are your rules?" mentions that it never does arithmetic and names the rates file |
| Engine | `python3 src/engine/validate.py --help` prints usage and exits 0 |

## Updating

Bundles are versioned with the release tag. To update, download the new assets and repeat the
platform steps — every platform above replaces rather than merges, so re-upload the whole
set. Custom skills do not sync across surfaces; update each one. Your `books/` directory is
yours and is never touched by an update.

## See also

- [Getting Started](Getting-Started) · [Engine Reference](Engine-Reference)
- [Troubleshooting](Troubleshooting) — Python version errors, the npm 401, Bangla rendering
- [Disclaimer](Disclaimer)
