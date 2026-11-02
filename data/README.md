# The text, its sources, and how each one was checked

| | |
|---|---|
| Work | *Organon of Medicine*, sixth edition (completed 1842) |
| Translation | William Boericke, 1922 (English) |
| Licence of the TEXT | Public domain — Hahnemann died 1843; the Boericke translation was published 1922 |
| Licence of this repo's CODE | PolyForm Noncommercial 1.0.0 |

**The bundle now carries all 291 sections.** Two kinds of source make that possible, and
they check each other.

## 1. The reading text — a transcription (no OCR damage)

Médi-T's transcription of the sixth edition on homeoint.org, section by section
(`organ001.htm … organ280.htm`, fifteen pages, retrieved through the Internet Archive
Wayback Machine). Those pages print **both** editions: where the fifth and sixth differ
they carry `§ N Fifth Edition` and `§ N Sixth Edition` one after the other, and where they
agree a bare `§ N`. `tools/parse-homeoint.py` takes the sixth-edition block, takes a bare
heading (it is the same text in both editions), and **never** takes a fifth-edition block.

## 2. The verification corpus — three OCR scans of the printed book

| scan | Internet Archive item | OCR file | sections on its own |
|---|---|---|---|
| `IA-1842-1922` | `organon-of-medicine-6th-edition-completed-1842-german-edition-published-1921-eng` | 532,017 bytes | 170 |
| `Wellcome-0001` | `b3135452x_0001` (Wellcome Library, Boericke & Tafel 1922) | 609,973 bytes | 165 |
| `Wellcome-0002` | `b3135452x_0002` (the same edition, a second copy) | 610,585 bytes | 155 |

## How a section earns its place

1. **Edition guard.** A scan is refused unless its own front matter declares the *sixth
   edition in Boericke's translation* (`require_sixth_edition()`).
2. **Mark guard.** In a scan, a section exists only where a section mark can actually be
   read — digits only, OCR's `O→0 / l→1 / S→5 / B→8 / g→9` confusions mapped *inside the
   mark only* — and only inside a forward-moving run, so a stray page number cannot
   become a section.
3. **Corroboration.** For every transcription section, `tools/extract.py` measures the
   fraction of its 12-letter sequences that appear **verbatim** in the scans. A paraphrase
   or a different translation scores near zero; this transcription scores **median 0.976,
   minimum 0.729** across all 291 sections. Anything below 0.60 is refused and the scan's
   text is used instead.
4. **Provenance.** Every section carries `from` (`MediT`, or a scan label) and its
   `corroboration` figure. The reader prints both under the section number, so any line
   can be traced and checked.

SHA-256 of every OCR file used, and the edition evidence line, are recorded in
`sections.json` → `scans`; the fifteen transcription pages are pinned in
`homeoint_pages.json`.

## The sources that were offered and refused, with reasons

- **`drcherylkasdorf.com/…/Organon-of-Medicine-6th-edition.pdf`** — this is *not* the
  Boericke translation. Its title page reads: *"A new translation by Jost Künzli, M.D.,
  Alain Naudé and Peter Pendleton"*, **translation copyright © 1982 The Hahnemann
  Foundation**, all rights reserved. It is the sixth edition, but a different and
  in-copyright translation: unusable, and mixing its wording in would have broken the
  rule that this reader presents Boericke.
- **`archive.org/details/in.ernet.dli.2015.31779`** — *Organon of Medicine (fifth and
  sixth edition)* with introduction and commentary by **B. K. Sarkar**: a different book,
  carrying both editions plus commentary, and its OCR cannot read its own section marks
  (a handful of readable marks in the body). Refused on both counts.
- **Dudgeon's fifth edition** and the 1913 *Organon of the rational art of healing* —
  different editions/translations, refused by the edition guard rather than merely unused.
- **homeopathyworld.in** per-aphorism pages — convenient, but they drop the footnotes and
  garble at least one aphorism (`§150`), so they were not used.

## Rebuilding

    # the three OCR files, and the fifteen transcription pages, named as above, then:
    python3 tools/parse-homeoint.py   # -> homeoint_sections.json (291, sixth edition only)
    python3 tools/extract.py          # -> sections.json (291 of 291, with corroboration)
    python3 tools/build-data.py       # -> docs/organon-data.js
    node test-node.js                 # the suite: 29 assertions
