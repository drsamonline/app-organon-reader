# The bundled text, and its licence

| | |
|---|---|
| Work | *Organon of Medicine*, sixth edition (completed 1842) |
| Translation | William Boericke, 1922 (English) |
| Source | <https://archive.org/details/organon-of-medicine-6th-edition-completed-1842-german-edition-published-1921-eng> |
| File used | `Organon of Medicine 6th edition ... _djvu.txt`, 532,017 bytes, OCR of the 1922 printing |
| SHA-256 of that file | `9462bf5fd6d3b3e988b737ab7c6ca5b035c2dff27cf5507b43d781a760eaa409` |
| Licence of the TEXT | Public domain — Hahnemann died 1843; the Boericke translation was published 1922, before the 1930 US renewal window for this kind of work |
| Licence of this repo's CODE | PolyForm Noncommercial 1.0.0 |

The Internet Archive item is in its `opensource` collection. The data's licence is
what is recorded here, not the repository's licence: a public-domain text stays
public domain inside a noncommercially-licensed repo.

## What the OCR gave us, honestly

The scan is machine-read, so some section marks are unreadable (`§ 40` is printed as
`§ AO,`, `§ 1` as `Si`). The extractor (`tools/extract.py`) accepts only marks whose
digits it can actually read, and only when they move forward; it never renumbers and
never invents a section. The bundle therefore carries **156 of the book's 291
sections**, and the reader says so on screen and names the sections it is missing.

A second Internet Archive scan (`in.ernet.dli.2015.31779`, the fifth and sixth
editions in one volume) was tried as a cross-check and rejected: its OCR is rougher,
with only a handful of readable section marks in the body, so it could not fill a gap
it cannot read either.

## Rebuilding

    python3 tools/extract.py          # organon.txt -> sections.json   (156 sections)
    python3 tools/build-data.py       # sections.json -> docs/organon-data.js
    node test-node.js                 # the suite

`organon.txt` is not committed (532 KB of OCR, and it is one URL away); the extractor
records the URL and the SHA-256 above, so the input is pinned even though it is absent.
