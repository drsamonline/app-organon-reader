<!-- badges:start -->
<p align="center">
  <img src="docs/badges/live.svg" alt="live: online">
  <img src="docs/badges/tests.svg" alt="tests: 86/88">
  <img src="docs/badges/offline.svg" alt="offline: 0 requests">
  <img src="docs/badges/deps.svg" alt="deps: 0">
  <img src="docs/badges/editions.svg" alt="editions: 6 editions">
  <img src="docs/badges/translations.svg" alt="translations: 4 English · 2 machine">
  <img src="docs/badges/sections.svg" alt="sections: 1082/1148">
  <img src="docs/badges/licence.svg" alt="licence: PolyForm NC">
</p>
<!-- badges:end -->

# Organon Reader

[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/license-PolyForm%20Noncommercial%201.0.0-blue)](LICENSE)


![Screenshot](docs/shot.png)
**The Organon of Medicine in four English editions — Wheeler’s first (1913), Devrient’s fourth (1833), Dudgeon’s fifth (1849) and Boericke’s sixth (1922) — plus the second and third editions in Hahnemann’s German, Brunnow’s French of 1824, and a clearly labelled machine translation of each German edition. Searchable, bookmarkable and readable with the network off, and switchable while you read.** No account, no server, no telemetry. Open the page and read.

- **App:** <https://drsamonline.github.io/app-organon-reader/>
- **The text — sixth edition:** *Organon of Medicine*, 6th edition (completed 1842), translated by William Boericke, 1922 — public domain. The reading text comes from the **Médi-T transcription** (homeoint.org) of that translation; it is corroborated, section by section, against **three OCR scans** of the printed book, and `tools/extract.py` refuses anything that fails either test. **All 291 sections are present.**
- **The text — fifth edition:** *Organon of Medicine*, 5th edition (1833), translated by R. E. Dudgeon, 1849 — public domain. Built by `tools/build-organon5.py` from the **same fifteen Médi-T pages**, which print both editions side by side; the sixth-edition parser skips the fifth-edition blocks by design, and this one keeps them. Corroborated against **three Dudgeon scans** (Wellcome 1893, Internet Archive 1849, Google 1849): median **0.979**, minimum **0.745**, every one of its **294 sections** above the 0.60 floor. **They are different books:** 74 sections are worded differently and §292–§294 exist only in the fifth.
- **The text — fourth edition:** *Organon of the Healing Art*, 4th edition (1829), translated by Charles H. Devrient, 1833 — the first English Organon, with Samuel Stratten's notes. Built by `tools/build-organon4.py` from **four scans** of the 1833 printing. The book numbers its paragraphs in Roman numerals and OCR loses some of them, so **241 of the 292 are carried** (median coverage **1.0**, minimum **0.962**); the 51 lost marks are named in the list, never filled or renumbered. This is the edition that first carries the chronic miasms.
- **The text — first edition:** *Organon of the Rational Art of Healing*, 1st edition (1810), translated by C. E. Wheeler, 1913 — the only English translation of the first edition. Built by `tools/build-organon1.py` from **two scans** of the 1913 Everyman's printing: **256 of the 271 aphorisms** (median **1.0**, minimum **0.934**), with the 15 lost marks named. Wheeler omitted Hahnemann's Introduction and most of his footnotes; that omission is his, and the reader does not fill it.
- **The text — second edition:** *Organon der Heilkunst*, 2nd edition, 1819, in **Hahnemann's German** — the book's printed **Inhaltsanzeige**, the list of numbered rubrics it sets before the Einleitung. Built by `tools/build-organon2.py` from **two copies** of the 1819 printing: **98 blocks covering 280 of the 318 numbered paragraphs**, with the rest named. A number is printed singly or as a range where several paragraphs share one thought (`§90–105`), so blocks are shown as ranges. The paragraphs themselves are not carried: both surviving scans of the 1819 body misorder its pages, so they cannot be set without inventing the joins — Brunnow's French beside it has them whole.
- **The text — third edition:** *Organon der Heilkunst*, 3rd edition, 1824, in **Hahnemann's German**. Built by `tools/build-organon3.py` from two copies of the 1824 printing: **297 blocks covering 307 of its 320 numbered paragraphs** (median corroboration **1.0**, minimum **0.956**), with the 13 lost numbers named.
- **The text — Brunnow's French, 1824:** *Organon de l'art de guérir*, the second edition as French readers had it, in the language it was printed in. Built by `tools/build-organon2-fr.py` from two copies: **314 blocks covering 314 of 318 numbered paragraphs**. Nothing in it is generated.
- **No English translation of editions 2 and 3 exists.** They were translated into French (Brunnow, 1824), Italian and other languages, but never into English. The reader therefore carries the German and the French **as printed**, and offers English only as a **machine translation built once at build time** (`tools/translate-mt.py`), in its own bundle, labelled *machine translation* on every section it appears on, with its own store key so a bookmark cannot cross into a published edition. It is generated text, not Hahnemann's English, and the German beside it is the authority.
- **Built with:** `web-kit`'s storage model, and nothing else. No CDN, no build step, no dependencies.

## What it does

**Nine books, and it never confuses them.** The edition selector in the header switches the whole book — text, section list, search and bookmarks. Between the English editions, every section says how it stands against the edition it is read beside: *only in the fifth edition*, *wording differs from the sixth edition*, or *same wording as the sixth edition*. A German, French or machine-translated book is not compared by wording with an English one — that would report every section as different and mean nothing — so it says what it is instead: *Hahnemann's German of 1819 — this edition has no English translation*, or *machine translation — generated text*. Each book keeps its own bookmarks and notes, because a note on §153 means a different paragraph in each.

**The numbering, mapped.** One view sets the books' paragraph numbers beside one another, 1 to 320 — the widest book — and says which editions print each number. Each cell opens that book at the block that prints it, including a block printed as a range (`§90–105`). It is a map, not a merged text: nothing is filled in from another edition, so a number a book does not carry stays empty, and a machine translation takes no column of its own because it covers exactly its German blocks.

It is a reader, not an interpreter. It presents the text, finds a phrase in it instantly, and keeps your bookmarks and notes on your own device. It does not summarise, advise, or explain Hahnemann.

Search is phrase search over the bundled text. Type `vital force` and every section that contains it is listed, best match first, each with its section number and the line it matched. Every section is in the left-hand list — click one, or type a number into the § box to jump. In the text you can walk the book with **Next / Previous**, or the ← and → keys, and the reader steps over a section it does not carry rather than stopping dead at the gap. Open a section and you can bookmark it or write a note; both are stored locally and both come back on the next visit. Under each section number the reader names the scan that section was read from.

## What it refuses to do

- **It does not merge the editions.** The nine bundles are separate files with separate provenance; nothing is blended into one "best" text, and a section is never silently swapped for its counterpart in another edition. The machine translations are a tenth and eleventh file again, flagged section by section.
- **It does not pass generated text off as Hahnemann's.** The machine bundles carry `mt: true` on every section, name the engine and the date in `meta.machine_translation`, and the reader prints *machine translation* above the text and in the footer of that book.

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
node test-node.js        # the suite: 88 assertions, no dependencies
python3 scripts/badges.py   # redraw the badges above, and the block in this file, from the books' own numbers
node tools/fingerprint.js check   # the carried text still matches data/fingerprints.json
```

Rebuilding the bundled text from the scans is described in [`data/README.md`](data/README.md), which records every item used, the SHA-256 of each OCR file, the sections that remain unreadable in each edition, and why other scans were rejected (one cannot read its own marks; another is a different translation).

<!-- support:sweep -->
## Support

| | |
|---|---|
| UPI (India) | `drsohilboi@ybl` — payee Dr Sohil Momin, open amount, or scan [the QR](docs/assets/upi-qr.svg) |
| GitHub Sponsors | [github.com/sponsors/drsamonline](https://github.com/sponsors/drsamonline) |
| Ko-fi | [ko-fi.com/matneo](https://ko-fi.com/matneo) |
| PayPal | [paypal.me/drsohilmomin](https://paypal.me/drsohilmomin?locale.x=en_GB&country.x=IN) |
| My books | [Amazon author store](https://www.amazon.com/stores/author/B08ZT331LY/allbooks?ccs_id=aed72b9f-71d9-41dc-adee-e9368a317acc) |
| More apps | [drsamonline.github.io](https://drsamonline.github.io/) |
| Email | [sohilmomin2000@gmail.com](mailto:sohilmomin2000@gmail.com) |

## Licence

Code: PolyForm Noncommercial 1.0.0 — free for any noncommercial use; commercial use needs a licence from the author.
Text: public domain in every edition carried (Hahnemann d. 1843; translations published 1833–1922). The text's licence is not the repository's licence, and both are recorded in `data/README.md`.
