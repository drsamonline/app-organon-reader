# The bundled text, and its licence

| | |
|---|---|
| Work | *Organon of Medicine*, sixth edition (completed 1842) |
| Translation | William Boericke, 1922 (English) |
| Licence of the TEXT | Public domain — Hahnemann died 1843; the Boericke translation was published 1922 |
| Licence of this repo's CODE | PolyForm Noncommercial 1.0.0 |

## Why three scans

A single OCR of the 1922 printing loses a section mark here and there — `§ 40` is read
as `§ AO,`, `§ 1` as `Si`, `§ 2` as `S 2.` or `~ B-`. **It does not lose the same one
twice.** Three independent scans of the same translation were therefore read and merged:

| scan | Internet Archive item | OCR file | sections on its own |
|---|---|---|---|
| `IA-1842-1922` | `organon-of-medicine-6th-edition-completed-1842-german-edition-published-1921-eng` | 532,017 bytes | 170 |
| `Wellcome-0001` | `b3135452x_0001` (Wellcome Library, Boericke & Tafel 1922) | 609,973 bytes | 165 |
| `Wellcome-0002` | `b3135452x_0002` (the same edition, a second copy) | 610,585 bytes | 155 |

Merged, they carry **255 of the book's 291 sections**. Each section in the bundle
records which scan it came from (`"from"` in `docs/organon-data.js`, and the reader says
so under the section number), so any line can be checked against the scan it came from.

The SHA-256 of every file used is recorded in `sections.json` → `scans`, so the input is
pinned even though the files themselves are not committed.

## What the merge does, exactly

`tools/extract.py`:

1. finds the **body** by anchoring on the first aphorism's own closing words
   ("restore the sick" / "sick to health"), so the synopsis in the front matter — which
   numbers sections in its own style — cannot be mistaken for the text;
2. accepts a section mark only if its digits can be **read** (a small OCR digit map
   handles `O→0`, `l→1`, `S→5`, `B→8`, `g→9` …), and only inside a mark;
3. keeps the **longest run of marks whose numbers go up**, so a stray page number
   cannot become a section;
4. prefers, for each number, the scan whose text is the cleanest prose **and whose next
   mark is readable** (both edges known, so the text cannot run into the next section);
5. never renumbers and never invents: whatever no scan can read is listed in
   `missing` and named on screen.

## The 36 that remain

`3, 5, 11, 13, 17, 31, 39, 45, 67, 73, 77, 103, 111, 113, 114, 115, 119, 121, 125,
131, 132, 138, 171, 173, 178, 179, 183, 190, 205, 214, 223, 224, 250, 251, 272, 273`

In all three scans the mark for these is either destroyed or reads as something no rule
can recover. Note what that means for reading: where a mark is missing, the text after
it sits at the end of the **previous** section, which runs on until the next readable
mark. The reader says "this section carries the following text too" nowhere — but the
section lengths show it, and the count of 255 is honest about the gap.

Sources rejected, with reasons: `in.ernet.dli.2015.31779` (Digital Library of India,
fifth and sixth editions in one volume) — its body OCR yields only a handful of readable
marks, so it cannot fill a gap it cannot read either; the Dudgeon 5th edition and the
1913 "rational art of healing" scans — a different translation, so their wording cannot
be presented as Boericke's.

## Rebuilding

    # the three OCR files, named as above, then:
    python3 tools/extract.py          # -> sections.json  (255 of 291)
    python3 tools/build-data.py       # -> docs/organon-data.js
    node test-node.js                 # the suite: 21 assertions
