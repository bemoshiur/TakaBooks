# docs/

This directory holds the **source of the TakaBooks GitHub Wiki** plus the project's design
and research provenance. Nothing in here is loaded by the engine or shipped in a bundle; it is
documentation for humans.

| Path | What it is | Who edits it |
| --- | --- | --- |
| `wiki/` | The GitHub Wiki, one Markdown file per page. Mirrored to https://github.com/bemoshiur/TakaBooks/wiki | Anyone, by pull request against this directory |
| `superpowers/specs/` | The approved design specification — the binding contract the code is built to | Maintainer |
| `superpowers/skill-tests/` | Micro-test records for the core instruction (`src/core/`) | Maintainer |
| `research/` | Raw research provenance behind `src/data/rates-AY<year>.toml` | Research passes |

## `docs/wiki/` is the wiki

The wiki you read at `github.com/bemoshiur/TakaBooks/wiki` is **generated from
`docs/wiki/`**. The files here are the source of truth; the wiki is a mirror.

Consequences:

- **Edit here, not in the wiki UI.** A mirror run replaces the wiki's working tree wholesale,
  so anything typed into the wiki editor is overwritten by the next sync. `_Footer.md` says so
  on every page, in Bangla and English.
- **Every change goes through a pull request**, so wiki content gets the same review as code.
  A wiki page that stated a tax figure would be the easiest place for a wrong number to hide;
  the review is the guard.
- **The wiki asserts no rate, threshold, deadline or statute number as a statement of law.**
  It documents mechanisms — how the rates file works, how a figure is verified, how to run the
  engine. Every figure lives in `src/data/rates-AY<year>.toml` with a `source` URL and a
  `verified` flag, and the wiki points there.

  The one place a figure may legitimately appear on a page is **inside a pasted command
  transcript**, where it is there because the engine read it out of the rates file and printed
  it. `Getting-Started.md` does this deliberately, and pairs it with the
  `rates.py --key …` command that shows the reader where the figure came from — teaching the
  sourcing habit instead of a number. The test to apply in review is therefore not "does a
  digit appear?" but: **would a reader come away believing this page is the authority for that
  figure?** If yes, that is a bug; open an issue. A rate written into prose as a fact, a slab
  table typed out by hand, or a deadline stated in a sentence all fail that test.

### Page naming — GitHub Wiki rules

GitHub wikis are a **flat namespace**: the page title is the file's basename, and hyphens in
the file name become spaces in the title. `Updating-Tax-Rates.md` is the page "Updating Tax
Rates" at `/wiki/Updating-Tax-Rates`. Files in subdirectories are stored but are **not**
addressable as pages, so `docs/wiki/` must stay flat.

Three file names are reserved and case-sensitive:

| File | Role |
| --- | --- |
| `Home.md` | The landing page. GitHub creates this one when the wiki is first initialised. |
| `_Sidebar.md` | Rendered as the navigation sidebar on every page. |
| `_Footer.md` | Rendered as the footer on every page. |

`_sidebar.md` (lowercase) would be ignored. Both underscore files also appear in the page
list; that is normal.

Links between wiki pages are plain relative links to the page name without extension:
`[Installation](Installation)`. Links to files in the source repository must be **absolute**
(`https://github.com/bemoshiur/TakaBooks/blob/main/src/...`) — a wiki page cannot use a
repository-relative path, because the wiki is a separate git repository.

### How it gets published

Every GitHub wiki is a separate git repository at
`https://github.com/bemoshiur/TakaBooks.wiki.git`. Publishing means copying `docs/wiki/` into
a checkout of that repository and pushing.

**One-time prerequisite, manual, no API exists:** the wiki repository does not exist until a
first page has been created in the web UI. Until then, any clone or push fails with
`fatal: repository 'https://github.com/bemoshiur/TakaBooks.wiki.git/' not found`, and no
token or workflow can get past it. Enabling the wiki in repository settings turns the tab on
but does *not* create the repository. The maintainer does this once: **Wiki tab → Create the
first page → Save.** After that, automation works. Turn on **Restrict editing to
collaborators only** at the same time, or any GitHub user can edit pages that the next sync
silently wipes.

**Automated path (CI).** `.github/workflows/wiki-sync.yml` — the *Wiki sync* workflow — runs
**on push to `main` when the push touches `docs/wiki/**`**, and can also be started by hand
with `workflow_dispatch` (that is how you recover after a bad sync, or publish the first time
straight after initialising the wiki without waiting for the next `docs/wiki/` change).

It checks out the source repository, sanity-checks the tree before touching anything,
confirms the wiki repository actually exists, checks it out, replaces its working tree with
`docs/wiki/`, and commits and pushes. It copies **`docs/wiki/` only** — never the whole of
`docs/`, because `research/` and `superpowers/` are not wiki pages and would become stray,
un-navigable files.

Two details worth knowing if you touch the workflow:

- Permissions are denied at the top level (`permissions: {}`) and the single job opts in to
  `contents: write`, which is what the default `GITHUB_TOKEN` needs to push to the wiki
  repository. No PAT is required.
- A `concurrency` group serialises runs with `cancel-in-progress: false`. Two syncs must never
  race, because each deletes then re-copies the same tree — and a *cancelled* sync could leave
  the wiki emptied, which is why in-progress runs are allowed to finish rather than being
  cancelled.

The workflow cannot create the wiki repository; the manual prerequisite above still has to
happen once first, and the workflow checks for it and fails with a clear message rather than
pushing into nothing.

**Manual path (works without CI, and is how to recover after a bad sync):**

```bash
git clone https://github.com/bemoshiur/TakaBooks.wiki.git /tmp/takabooks-wiki
cd /tmp/takabooks-wiki
find . -mindepth 1 -maxdepth 1 -not -name '.git' -exec rm -rf {} +
cp -R /path/to/TakaBooks/docs/wiki/. .
git add --all
git commit -m "docs: sync wiki from <commit sha>"
git push
```

### Previewing a page before you push

Any Markdown previewer shows the content. Two things differ on the real wiki: `[[Page
Name]]`-style and `[text](Page-Name)` links only resolve there, and the sidebar/footer are
injected by GitHub. Check that every `[text](Page-Name)` target matches an existing file name
in this directory, hyphens included — a link to a page that does not exist renders red on the
wiki.

### Checklist for a wiki change

1. The file is at the top level of `docs/wiki/`, named `Title-With-Hyphens.md`.
2. It asserts no tax rate, threshold, deadline or statute number as a fact of law. Any figure
   that appears sits inside a pasted command transcript and is accompanied by the command that
   reads it from the rates file.
3. **Every command and every block of output was actually run**, and pasted back rather than
   composed. Where a machine-specific absolute path was shortened, the page says so. Invented
   terminal output is the worst defect this wiki can carry: it teaches a workflow that does not
   run, and readers cannot tell it apart from the real thing.
4. Account codes come from `src/templates/accounts.toml` (the 131-account chart that ships) —
   not from the 42-account fallback embedded in `init_books.py`, and not from memory.
5. Bangla statutory terms are paired with English on first use (মূসক / VAT, উৎসে কর কর্তন / TDS).
6. Links to repository files are absolute `https://github.com/bemoshiur/TakaBooks/...` URLs.
7. Links to other wiki pages use the page name, and that page exists.
8. Issue-template references name a template that exists in `.github/ISSUE_TEMPLATE/`.
9. `_Sidebar.md` lists the page if it is meant to be found from the navigation.
10. Every tax-related page ends with, or links to, the [Disclaimer](wiki/Disclaimer.md).

---

TakaBooks — maintained by Moshiur Rahman (@bemoshiur) · TICON SYSTEM LTD — https://ticonsys.com ·
MIT licensed · https://github.com/bemoshiur/TakaBooks
