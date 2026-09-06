# TakaBooks brand assets — টাকাবুকস

The visual identity of TakaBooks: a ledger (খতিয়ান / ledger) carrying the Bangladeshi
taka sign (৳). Every file in this directory is hand-written SVG — no embedded fonts,
no external images, no scripts — so it renders identically on GitHub, npm, PyPI-style
package pages, forks, release tarballs and offline previews.

Maintained by Moshiur Rahman (@bemoshiur) · Ticon Sys — https://ticonsys.com

## Files

| File | Size | What it is | Use it for |
| --- | --- | --- | --- |
| `icon.svg` | 64 × 64 | The mark alone: green ledger, red ribbon bookmark, white ৳. | Favicon, app icon, avatar, anywhere square. Legible from 16 px up. |
| `logo.svg` | 524 × 128 | Horizontal lockup: mark + "TakaBooks" wordmark, for **light** backgrounds. | README header, docs, slides on white. |
| `logo-dark.svg` | 524 × 128 | The same lockup recoloured for **dark** backgrounds. | GitHub dark theme, dark slides. |
| `social-preview.svg` | 1280 × 640 | Source of the GitHub social card. | Edit this, then render the PNG (below). |
| `social-preview.png` | 1280 × 640 | Rendered card, uploaded by hand to GitHub. | See *Social preview* below. |

The mark and the wordmark are pure vector paths drawn on a 100-unit grid: the ৳ is a
round-capped monoline stroke, the wordmark is a geometric monoline sans drawn by hand.
Only the social card contains `<text>` (its tagline and Bangla lines), because Bangla
conjuncts must come from a real Bangla font.

## The mark

- **Cover** — a rounded ledger cover in Taka Green with a Deep Green spine on the left.
  The spine is what makes it read as a book rather than a tile.
- **Ribbon** — a small Bangladesh Red bookmark ribbon at the top right. It is the only
  red in the whole identity: a ledger's ribbon, not a flag.
- **৳** — the taka sign (U+09F3) in white, drawn as one stroke: the left-curling hook
  at the top of the stem, the crossbar reaching right, and the bowl sweeping down and
  back up. It is a drawn mark, not a font glyph, so it carries no font licence.

Together they say **money + books** — টাকা + বই — at a glance, including at favicon size.

## Palette

| Name | Hex | Role |
| --- | --- | --- |
| Taka Green | `#006A4E` | Primary. Ledger cover; "Taka" in the light wordmark. |
| Deep Green | `#004B37` | Ledger spine. |
| Night Green | `#0B2E24` | Social card background. |
| Mint | `#4FD1A1` | "Taka" in the dark wordmark; the highlighted pill on the social card. |
| Bangladesh Red | `#F42A41` | The ribbon bookmark. Nothing else. |
| Ink | `#10241C` | "Books" in the light wordmark. Green-black, not pure black. |
| Paper | `#F4F8F5` | "Books" in the dark wordmark; primary text on the card. |
| Slate | `#9DB0A8` | Secondary text on dark surfaces. |
| White | `#FFFFFF` | The ৳ on the cover. |

Taka Green and Bangladesh Red are the Bangladesh flag values (`#006A4E` / `#F42A41`).
They are used with restraint: green carries the identity, red appears once, in the
ribbon. Do not add more red, and do not place red and green text side by side.

Contrast (WCAG 2.x): white ৳ on Taka Green 6.6 : 1; Ink on white 16.3 : 1; Taka Green on
white 6.6 : 1; Paper on Night Green 13.7 : 1; Mint on Night Green 7.7 : 1; Slate on
Night Green 6.4 : 1. Every pairing used for text passes AA; all but Slate pass AAA.

## Usage rules

1. **Pick the file by background.** `logo.svg` on light, `logo-dark.svg` on dark. In a
   GitHub README use both, so the viewer's theme picks one:

   ```html
   <p align="center">
     <picture>
       <source media="(prefers-color-scheme: dark)"  srcset="assets/logo-dark.svg">
       <source media="(prefers-color-scheme: light)" srcset="assets/logo.svg">
       <img alt="TakaBooks — টাকাবুকস" src="assets/logo.svg" width="420">
     </picture>
   </p>
   ```

   The `<img>` fallback is mandatory and must point at the light file — it is what
   renderers without `<picture>` support (npm, most static site generators) show.
2. **Minimum sizes.** Mark: 16 px. Lockup: 120 px wide. Below that use the mark alone.
3. **Clear space.** Keep a margin of at least one quarter of the mark's height on every
   side of the lockup, free of other logos, text and edges.
4. **Do not** recolour, stretch, rotate, outline, add a drop shadow, or redraw the ৳.
   The mark is the same in light and dark mode on purpose; only the wordmark changes.
5. **Do not put any tax rate, threshold, deadline or statute number on a brand asset.**
   An image cannot carry a source URL or a `verified` flag and cannot be corrected when
   the Finance Act changes. Rates live in `src/data/rates-AY*.toml` only.
6. **Do not** use the mark in a way that implies endorsement by the National Board of
   Revenue (NBR) or the Government of Bangladesh. TakaBooks is an independent project.
7. **Favicon.** Modern browsers accept the SVG directly:
   `<link rel="icon" type="image/svg+xml" href="assets/icon.svg">`. If a raster favicon
   is needed, render `icon.svg` at 32 × 32 and 16 × 16 with the same command as the
   social card, adjusting `--window-size`.

## Social preview

GitHub's rules for the repository social card: **at least 640 × 320 px, 1280 × 640 px
for best display, under 1 MB, PNG / JPG / GIF.** `social-preview.svg` is drawn at
exactly 1280 × 640 (2 : 1). All text sits inside a centred 1100 × 500 safe area, so
nothing important is lost when X, LinkedIn, Slack or Discord crop to 1.91 : 1.

What the card carries: the mark, the "TakaBooks" wordmark, টাকাবুকস, the tagline
*Bangladeshi bookkeeping & taxation for any LLM*, the statutory term pairs
মূসক / VAT · উৎসে কর কর্তন / TDS · খতিয়ান / Ledger, a row of the LLMs it targets ending
in *any LLM*, and the Ticon Sys credit. No rates, no deadlines (rule 5 above).

### 1. Render the PNG

The card's Bangla lines use this font stack: Noto Sans Bengali, Kohinoor Bangla,
Bangla Sangam MN, Bangla MN, SolaimanLipi, Nirmala UI, Vrinda. Render on a machine
that has one of them — macOS ships Kohinoor Bangla and Bangla Sangam MN, Windows ships
Nirmala UI and Vrinda, on Debian/Ubuntu `apt install fonts-noto-core` provides Noto
Sans Bengali. **Open the PNG and check the Bangla before uploading**: hollow boxes,
broken conjuncts or a dotted-circle glyph mean the font was missing.

Headless Chrome / Chromium (no extra tools; verified to produce exactly 1280 × 640):

```sh
# macOS
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new \
  --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
  --window-size=1280,640 --screenshot=assets/social-preview.png \
  "file://$PWD/assets/social-preview.svg"

# Linux: replace the binary with google-chrome or chromium
# Windows: "C:\Program Files\Google\Chrome\Application\chrome.exe" with the same flags
```

Alternatives, if installed: `rsvg-convert -w 1280 -h 640 assets/social-preview.svg
-o assets/social-preview.png` or `inkscape assets/social-preview.svg
--export-type=png --export-filename=assets/social-preview.png`.

Check the result before committing it:

```sh
python3 -c "import struct,sys;b=open('assets/social-preview.png','rb').read();print(struct.unpack('>II',b[16:24]),len(b),'bytes')"
# expect: (1280, 640) and well under 1000000 bytes
```

Commit the PNG next to the SVG so it is versioned, reviewable, and re-uploadable
after any accidental reset.

### 2. Upload it — by hand, there is no API

GitHub has no REST or GraphQL endpoint, no `gh` flag and no Action that sets the
social preview. `Repository.openGraphImageUrl` in GraphQL is read-only, and
`gh repo edit` wraps a REST endpoint that has no such field. GitHub staff confirmed
this on community discussion #172072 (2025-09-04). Do not add a workflow step that
pretends to do it; it cannot.

Click path, once per repository:

1. Open https://github.com/bemoshiur/TakaBooks.
2. Click **Settings** (the gear tab on the repository, not the account settings).
3. Stay on the **General** page that opens.
4. Scroll to the **Social preview** section.
5. Click **Edit**, then **Upload an image…**.
6. Choose `assets/social-preview.png`. The card updates as soon as the upload finishes;
   there is no separate save step.

Redo this after the repository is transferred or recreated, or if someone clicks
*Remove image*. Social networks cache the card; after a change, re-share the link or
run it through the platform's card debugger to refresh.

Until an image is uploaded GitHub serves an auto-generated card built from the owner
avatar, repository name, description and counts — usable, but generic, which is one
more reason the repository description must be strong.

## Editing the SVGs

- Keep them hand-editable and small: today every file is under 4 KB.
- Validate after every change: `xmllint --noout assets/*.svg`.
- Never add `<script>`, `<image href="http…">`, `<foreignObject>`, CSS `@import` or a
  web-font `@font-face`. GitHub strips them from SVG shown in Markdown and the file
  renders broken.
- Paths and inline attributes only; no `<style>` block, so the files behave the same
  inside an `<img>`, an `<object>` and when inlined.
- Re-render `social-preview.png` whenever `social-preview.svg` changes, and re-upload
  it (step 2 above). The upload does not track the repository.

## Licence and credit

The files here are part of the TakaBooks repository and carry its MIT licence. The
TakaBooks name and mark identify a project of **Ticon Sys** — https://ticonsys.com —
maintained by Moshiur Rahman (@bemoshiur). Use them to refer to TakaBooks; do not use
them to name a different product or to suggest endorsement by any government body.
