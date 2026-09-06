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
- **The wiki states no rate, threshold, deadline or statute number.** It documents mechanisms
  — how the rates file works, how a figure is verified, how to run the engine. Every figure
  lives in `src/data/rates-AY<year>.toml` with a `source` URL and a `verified` flag, and the
  wiki points there. If you find a figure on a wiki page, that is a bug; open an issue.

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

**Automated path (CI).** A workflow (`.github/workflows/wiki-sync.yml`, triggered by pushes
to `main` that touch `docs/wiki/**`) checks out `${{ github.repository }}.wiki`, deletes
everything in it except `.git`, copies `docs/wiki/.` in, commits as `github-actions[bot]`,
and pushes with the default `GITHUB_TOKEN` (`permissions: contents: write` is enough for the
wiki repository). It must copy **`docs/wiki/`**, never the whole of `docs/` — `research/` and
`superpowers/` are not wiki pages and would become stray, un-navigable files.

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
2. It contains no tax rate, threshold, deadline or statute number.
3. Bangla statutory terms are paired with English on first use (মূসক / VAT, উৎসে কর কর্তন / TDS).
4. Links to repository files are absolute `https://github.com/bemoshiur/TakaBooks/...` URLs.
5. Links to other wiki pages use the page name, and that page exists.
6. `_Sidebar.md` lists the page if it is meant to be found from the navigation.
7. Every tax-related page ends with, or links to, the [Disclaimer](wiki/Disclaimer.md).

---

TakaBooks — maintained by Moshiur Rahman (@bemoshiur) · Ticon Sys — https://ticonsys.com ·
MIT licensed · https://github.com/bemoshiur/TakaBooks
