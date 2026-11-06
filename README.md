<p align="center">
  <img src="docs/badges/live.svg" alt="live: online">
  <img src="docs/badges/tests.svg" alt="tests: 35/35">
  <img src="docs/badges/offline.svg" alt="offline: 0 requests">
  <img src="docs/badges/deps.svg" alt="deps: 0">
  <img src="docs/badges/editions.svg" alt="editions: 2 · 291+294">
  <img src="docs/badges/licence.svg" alt="licence: PolyForm Noncommercial">
</p>

# Organon Reader

[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/license-PolyForm%20Noncommercial%201.0.0-blue)](LICENSE)

**The Organon of Medicine in two editions — Boericke\u2019s sixth (1922) and Dudgeon\u2019s fifth (1849) — searchable, bookmarkable and readable with the network off, and switchable while you read.** No account, no server, no telemetry. Open the page and read.

- **App:** <https://drsamonline.github.io/app-organon-reader/>
- **The text — sixth edition:** *Organon of Medicine*, 6th edition (completed 1842), translated by William Boericke, 1922 — public domain. The reading text comes from the **Médi-T transcription** (homeoint.org) of that translation; it is corroborated, section by section, against **three OCR scans** of the printed book, and `tools/extract.py` refuses anything that fails either test. **All 291 sections are present.**
- **The text — fifth edition:** *Organon of Medicine*, 5th edition (1833), translated by R. E. Dudgeon, 1849 — public domain. Built by `tools/build-organon5.py` from the **same fifteen Médi-T pages**, which print both editions side by side; the sixth-edition parser skips the fifth-edition blocks by design, and this one keeps them. Corroborated against **three Dudgeon scans** (Wellcome 1893, Internet Archive 1849, Google 1849): median **0.979**, minimum **0.745**, every one of its **294 sections** above the 0.60 floor. **They are different books:** 74 sections are worded differently and §292–§294 exist only in the fifth.
- **Built with:** `web-kit`'s storage model, and nothing else. No CDN, no build step, no dependencies.

## What it does

**Two editions, and it never confuses them.** The edition selector in the header switches the whole book — text, section list, search and bookmarks. Every section says how the two editions stand: *only in the fifth edition*, *wording differs from the sixth edition*, or *same wording in both editions*. Each edition keeps its own bookmarks and notes, because a note on §153 means a different paragraph in each.

It is a reader, not an interpreter. It presents the text, finds a phrase in it instantly, and keeps your bookmarks and notes on your own device. It does not summarise, advise, or explain Hahnemann.

Search is phrase search over the bundled text. Type `vital force` and every section that contains it is listed, best match first, each with its section number and the line it matched. Every section is in the left-hand list — click one, or type a number into the § box to jump. In the text you can walk the book with **Next / Previous**, or the ← and → keys, and the reader steps over a section it does not carry rather than stopping dead at the gap. Open a section and you can bookmark it or write a note; both are stored locally and both come back on the next visit. Under each section number the reader names the scan that section was read from.

## What it refuses to do

- **It does not merge the editions.** The two bundles are separate files with separate provenance; nothing is blended into one "best" text, and a section is never silently swapped for its counterpart in the other edition.

- **It does not renumber the book.** A section exists only where a section mark can be read, and every section records where its text came from. OCR alone reached 255 of 291 — three scans of the same printing lose *different* marks — so the remaining 36 come from the transcription, each accepted only because its wording is found verbatim in the scans (median 98% of its word-runs). Nothing was renumbered, nothing was reconstructed, nothing was taken from another edition or another translation.
- **It does not invent a section to fill a gap.** Nothing in the text is paraphrased, reconstructed or generated.
- **It does not fetch anything.** No `fetch`, no `XMLHttpRequest`, no beacon, no socket, no off-origin `<script>`. The suite asserts all five, and that the bundle hashes the same on a second load.

## When things go wrong

| Situation | What happens |
|---|---|
| A search term of one character | It says the term is too short to search for — not "no matches", which would read as "this phrase is not in the book" |
| A phrase the text does not contain | It says no carried section contains it, and says how many sections it carries |
| Storage full or blocked | The bookmark or note is reported as **not saved**, and is never shown as kept; the write is read back to prove it |
| A corrupt saved file | It is reported, offered back for export, and the text still opens — the bundled text is read-only |
| No network | Nothing changes. There is nothing to fetch. |
| A section number the bundle does not carry | It says so and opens the next section it does carry — it never silently shows you the wrong aphorism |

## Run it

Open `docs/index.html` — that is the whole app. It works from `file://` and from GitHub Pages, because everything it needs sits beside it.

```
node test-node.js        # the suite: 29 assertions, no dependencies
python3 scripts/badges.py   # redraw the badges above from the suite's own numbers
```

Rebuilding the bundled text from the scans is described in [`data/README.md`](data/README.md), which records the three items used, the SHA-256 of each OCR file, the 36 sections that remain unreadable, and why two other scans were rejected (one cannot read its own marks; the other is a different translation).

## Licence

Code: PolyForm Noncommercial 1.0.0 — free for any noncommercial use; commercial use needs a licence from the author.
Text: public domain (Hahnemann d. 1843; Boericke translation 1922). The text's licence is not the repository's licence, and both are recorded in `data/README.md`.
