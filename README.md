<p align="center">
  <img src="docs/badges/live.svg" alt="live: online">
  <img src="docs/badges/tests.svg" alt="tests: 20/20">
  <img src="docs/badges/offline.svg" alt="offline: 0 requests">
  <img src="docs/badges/deps.svg" alt="deps: 0">
  <img src="docs/badges/sections.svg" alt="sections: 156/291">
  <img src="docs/badges/licence.svg" alt="licence: PolyForm Noncommercial">
</p>

# Organon Reader

**The Organon of Medicine, sixth edition, in the 1922 Boericke translation — searchable, bookmarkable and readable with the network off.** No account, no server, no telemetry. Open the page and read.

- **App:** <https://drsamonline.github.io/app-organon-reader/>
- **The text:** *Organon of Medicine*, 6th edition (completed 1842), translated by William Boericke, 1922 — public domain, from the Internet Archive scan.
- **Built with:** `web-kit`'s storage model, and nothing else. No CDN, no build step, no dependencies.

## What it does

It is a reader, not an interpreter. It presents the text, finds a phrase in it instantly, and keeps your bookmarks and notes on your own device. It does not summarise, advise, or explain Hahnemann.

Search is phrase search over the bundled text. Type `vital force` and every section that contains it is listed, best match first, each with its section number and the line it matched. Open a section and you can bookmark it or write a note; both are stored locally and both come back on the next visit.

## What it refuses to do

- **It does not renumber the book.** The scan's OCR loses some section marks — `§ 40` is printed as `§ AO,`, `§ 1` as `Si`. The extractor accepts only marks whose digits it can read, so the bundle carries **156 of the 291 sections**, and the reader says that on screen and names the sections it is missing. A reader that quietly renumbered the rest would be worse than a reader with gaps.
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

## Run it

Open `docs/index.html` — that is the whole app. It works from `file://` and from GitHub Pages, because everything it needs sits beside it.

```
node test-node.js        # the suite: 20 assertions, no dependencies
python3 scripts/badges.py   # redraw the badges above from the suite's own numbers
```

Rebuilding the bundled text from the scan is described in [`data/README.md`](data/README.md), which also records the source URL, the SHA-256 of the file used, and why a second scan was rejected as a cross-check.

## Licence

Code: PolyForm Noncommercial 1.0.0 — free for any noncommercial use; commercial use needs a licence from the author.
Text: public domain (Hahnemann d. 1843; Boericke translation 1922). The text's licence is not the repository's licence, and both are recorded in `data/README.md`.
