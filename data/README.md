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
   or a different translation scores near zero; this transcription scores **median 0.981,
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
    node test-node.js                 # the suite: 57 assertions

## The fifth edition, added 2026-11-03

The same fifteen pages carry the fifth edition beside the sixth: where they differ the page
prints `§ N Fifth Edition` and `§ N Sixth Edition` one after another, and where they agree a
bare `§ N`. `tools/parse-homeoint.py` takes the sixth block and skips the fifth on one line;
`tools/build-organon5.py` inverts that selection — it takes the labelled fifth block and,
for a bare heading, the shared text (which is the same in both editions).

| | |
|---|---|
| Work | *Organon of Medicine*, fifth edition (1833) |
| Translation | R. E. Dudgeon, M.D. (1849) |
| Licence of the TEXT | Public domain — Hahnemann died 1843; Dudgeon 1849 |

**Verification corpus — three scans of the fifth edition in Dudgeon's translation**

| scan | Internet Archive item | sections admitted |
|---|---|---|
| `Wellcome-1893` | `b28136536` (Hahnemann Publishing Society, 1893) | all |
| `IA-1849` | `b21307957` (W. Headland, 1849) | all |
| `Google-1849` | `organonmedicine01hahngoog` (1849) | all |

**The edition guard.** A scan is admitted only if its title page declares Dudgeon's
translation *of the fifth German edition*, and only if it never names William Boericke as
translator. A bare "Boericke" is **not** disqualifying: Boericke & Tafel were the New York
publishers of Dudgeon's 1893 edition as well, so the name appears on its title page. The
guard keys on the translator, not the publisher. This was found the hard way — a
name-only guard refused the 1893 scan outright.

**Result.** 12-letter-sequence coverage per section: median **0.979**, minimum **0.745**,
all **294** sections above the 0.60 floor. Nothing was refused, so nothing was replaced by
scan text.

**What the fifth edition actually contains that the sixth does not:** 294 numbered
paragraphs against the sixth's 291. §292–§294 (the mesmerism material) are absent from the
sixth. 74 sections are worded differently. §89's body carries the transcription's own
editorial marker "(Added to the Sixth Edition)" — left verbatim rather than silently edited,
and recorded in the bundle's `meta.notes`.

## The first and fourth editions, added 2026-11-19

Six editions were written; four were ever translated into English. The two missing ones are
not missing from this repository by oversight:

| edition | text carried | in the reader |
|---|---|---|
| First (1810) | C. E. Wheeler, English, 1913 | **yes** — `tools/build-organon1.py` |
| Second (1819) | Hahnemann's **German** — the printed *Inhaltsanzeige* | **yes** — `tools/build-organon2.py` |
| Third (1824) | Hahnemann's **German** | **yes** — `tools/build-organon3.py` |
| Second (1819) | **Brunnow's French, 1824** | **yes** — `tools/build-organon2-fr.py` |
| Second, third | **machine English** of the German | **yes, labelled** — `tools/translate-mt.py` |
| Fourth (1829) | Charles H. Devrient, English, 1833 (the first English Organon) | **yes** — `tools/build-organon4.py` |
| Fifth (1833) | R. E. Dudgeon, English, 1849 | yes (above) |
| Sixth (1842) | William Boericke, English, 1922 | yes (above) |

The second and third editions were translated into French (Brunnow, 1824), Italian and
other languages; **no English version of either has ever been published.** Nothing is
paraphrased or reconstructed to stand in for them. The reader therefore carries the German
and the French *as printed*, and offers English only as a machine translation, generated
once at build time, kept in its own bundles, and labelled on every section it touches.

### The first edition — Wheeler, 1913

| | |
|---|---|
| Work | *Organon of the Rational Art of Healing*, first edition (1810) |
| Translation | C. E. Wheeler, M.D. (Everyman's Library, 1913) |
| Licence of the TEXT | Public domain — Hahnemann died 1843; Wheeler 1913 |
| Carried | **256 of 271** aphorisms |
| Corroboration | median **1.000**, minimum **0.934**, every carried section above the 0.60 floor |

**Sources.** There is no transcription of this translation, so the reading text is OCR of a
printed copy and the second copy is the check:

| scan | Internet Archive item | role |
|---|---|---|
| `Wheeler-1913` | `organonofrationa00hahn` (Boston University copy) | reading text and corpus |
| `Wellcome-1913` | `b24877529` (Wellcome copy of the same printing) | corpus, and §1's mark |

**The edition guard.** A scan is admitted only if its front matter declares *translated from
the first edition* and names Wheeler, and never names Boericke or Devrient. Dudgeon's name is
**not** disqualifying: Part II of the 1913 volume is his translation of four of Hahnemann's
essays, so the guard keys on the Organon's translator, not on every name in the book.

**Why 15 sections are missing.** Wheeler himself printed no §158 and no §160 (he misnumbered
158–160), so those gaps are the translation's, not OCR's. The other thirteen (§8, §11, §17,
§23, §32, §33, §61, §101, §106, §110, §111, §166, §181) are section marks the scans do not
print legibly; each is named in the section list and none is renumbered or guessed. §1 carries
no mark of its own in the primary copy — it is the block under the book's heading — so it is
carried only because the second copy does print its number, and the primary copy supplies the
cleaner text.

### The fourth edition — Devrient, 1833

| | |
|---|---|
| Work | *Organon of the Healing Art*, fourth edition (1829) |
| Translation | Charles H. Devrient, with notes by Samuel Stratten (1833) |
| Licence of the TEXT | Public domain — Hahnemann died 1843; Devrient 1833 |
| Carried | **241 of 292** aphorisms |
| Corroboration | median **1.000**, minimum **0.962**, every carried section above the 0.60 floor |

**Sources — four scans of the 1833 printing:**

| scan | Internet Archive item | role |
|---|---|---|
| `Devrient-Dublin-1833` | `bub_gb_EnEFAAAAQAAJ` | reading text and corpus |
| `Devrient-Wellcome-1833` | `homoeopathicmedi00hahn` | reading text and corpus |
| `Devrient-Oxford-1833` | `homopathicmedic00devrgoog` | corpus only — its Roman numerals are unreadable |
| `Devrient-Wellcome-2` | `b33290180` | corpus only — its Roman numerals are unreadable |

**The edition guard.** Devrient's title page reads "TRANSLATED FROM THE GERMAN OF S.
HAHNEMANN, BY CHARLES H. DEVRIENT" and **does not name the German edition**, so the guard is:
the scan must name Devrient and Stratten, must name neither Boericke nor Dudgeon, and must
read section marks up to the end of a **292**-paragraph book. A 294-paragraph fifth edition or
a 291-paragraph sixth cannot pass that last test.

**Why 51 sections are missing.** The book numbers its paragraphs in Roman numerals and OCR
loses numerals silently (`§ LXXXIL` for LXXXII, `§ 111` for III). A section is carried only
where a mark is legible, and its text is cut at the next mark the *same* scan reads, so a lost
numeral shortens the book rather than letting two paragraphs run together. The list of lost
numbers is in the bundle's `meta.missing`.

**Notes.** Stratten's editorial notes are printed among the paragraphs in the scans and are
not separated here; the bundle carries the running text, and the reader says so.

### Rebuilding these two

The OCR files are not committed (they are 400–600 KB each). Fetch them from the Internet
Archive items named above, name them as the scripts expect, and:

    ORGANON_SRC=. python3 tools/build-organon1.py   # -> docs/organon1-data.js
    ORGANON_SRC=. python3 tools/build-organon4.py   # -> docs/organon4-data.js
    node test-node.js

Each bundle records, in `meta.scans`, the SHA-256 and byte count of every OCR file it used,
and in `meta.verification` the median and minimum coverage it achieved, so the figures above
can be checked rather than taken on trust.

## The second and third editions, in German, and Brunnow's French — added 2026-11-19

A third kind of book needed a third kind of parser. The second edition (1819) and the third
(1824) print a paragraph number in the margin and, where several paragraphs share one
sentence, a **range** — `90 — 105`, `258 — 274` — with the text printed once. So the unit
these books actually have is the *block*, and `tools/scanlib.py` carries one block under its
first number with `to` recording the last. §90–105 is one sentence under five marks; expanding
it into sixteen copies would duplicate Hahnemann fifteen times, and inventing sixteen texts
would be worse. The reader prints `§90–105`.

| | second edition | third edition | French (Brunnow) |
|---|---|---|---|
| Work | *Organon der Heilkunst* (1819) | *Organon der Heilkunst* (1824) | *Organon de l'art de guérir* (1824) |
| Language | German | German | French |
| Reading text | `organonderheilku01hahn` | `organonderheilku02hahn` | `b2930538x` |
| Second copy | `10476160bsb` — range ends and corpus | `organonderheilk01hahngoog` | `bub_gb_Qr_z-ZNDW48C` |
| Numbered to | §318 | §320 | §318 |
| Blocks carried | 98 | 297 | 314 |
| Numbered paragraphs covered | 280 of 318 | 307 of 320 | 314 of 318 |
| Licence of the text | public domain | public domain | public domain |

**The edition guards.** A German scan is admitted only if its own front matter says
`ZWEITE AUFLAGE` (1819) or `DRITTE AUFLAGE` (1824), and only if it names neither Boericke,
Dudgeon nor Devrient — a translation is a different book. A French scan must say
`TRADUIT` and name Brunnow, and must name none of those translators.

**What the 1819 German bundle actually is.** The 1819 book sets an *Inhaltsanzeige* before its
Einleitung: a list giving each paragraph's number in the margin — singly, or as a range where
several paragraphs share one thought — with its rubric. That list is what this bundle carries.
The paragraphs themselves are printed after the Einleitung, and **they are not carried**: both
surviving scans read the body's pages across the fold, so a paragraph's tail lands inside the
next one (`§10` is clean, `§20` has a page of §19 spliced into it). Setting that right is a
transcription, not a parse, and the reader would rather carry the list whole than the
paragraphs broken. Brunnow's French beside it carries the paragraphs, 314 of 318.

**Why the 1819 German is still only mostly there.** The reading copy
(`organonderheilku01hahn`) mangles margin numbers (`§106` came out as `J.06`, `§110` as `JlO`,
`§181` as `l8l`); the second copy (`10476160bsb`, Bayerische Staatsbibliothek) reads some of
them whole where the other cannot (`181 — 193.` for `l8l — igS`), but not all. Reading the
list tolerantly — a leading `J` or
`j` kept as `1`, a full stop printed inside a number folded away, junk between a number and
its dash — brings 280 of the 318 numbered paragraphs under a block. The 38 that remain are
listed in `meta.missing` and shown in the section list as gaps, never guessed: the entries
whose numbers both copies destroyed (`§8–11` reads `<q. 10. 11.`, `§252–257` reads
`2Ö2 — - s5j.`), and one entry (`§259–274`) that the reading copy lost altogether.

**Why the bundle records a minimum of 0.** `meta.verification.min` is the lowest figure among the
entries that were *checked*, not among the blocks that were *kept*. Entry `§251` scored 0.0 — neither
copy reads its rubric — and was refused at the 0.60 floor, so it is dropped from the bundle and
shown in the section list as one of the 38 named gaps, with `meta.verification.refused` recording
`{"n": 251, "corroboration": 0.0}`. That is why `sections_checked` reads 99 where `blocks` reads 98.
The 98 carried blocks are all above the floor: their median is **1.000** and their minimum **0.996**,
not 0. A zero in this bundle means *checked and refused*, never *carried and doubtful*.

**Ranges that lost an end.** Three entries print one end of a range and mangle the other
(`J.06 — 108`, `245 — '200`, `394 — -228`). The printed end is kept. A lost end is taken
first from the other copy of the printing, where it prints the same rubric whole
(`181 — 193.` for `l8l — igS`), and otherwise from the entry beside it — the list
enumerates the paragraphs in order — and only when Brunnow's French contents list, which
prints every paragraph 1–318, has every number the restored range would cover. **When that
bundle is missing no end is restored from a neighbouring entry**: the neighbour rule fails
closed and those numbers stay named gaps, while an end the second copy itself prints is
still settled (`§181–193`). Each such block records where its number came from in
`numbers_from`, and the count is in `meta`; nothing is restored silently. Today that recovers
§110–119, §181–193 (the end from the second copy), §194–228 and §245–250 — all four read
back on the printed page. The mangled number is not carried as text: where an end was lost,
the rubric begins at its first printed word (`181 — igS- Mafsregeln…` is carried as
`Mafsregeln…`), so no OCR fragment is offered as Hahnemann's. Where the token is not a
number but the entry's own sub-item it stays: the page prints `31. I. Die ältere…`, so that
rubric keeps its `I.` — the OCR dash there is a full stop.

The local-ailment entry is **§194–228, not §182–228**. Version 1.6.1 restored its start from
the entry beside it while that entry was still truncated to `§181`; read whole, the entry
runs to `§193`, so the next one begins at `§194` — where Brunnow's §194 opens the same
subject ("les maux locaux"). `§182` is not a block start.

**The restored ends are printed on the page.** All four ranges the build recovers were read
back on the scans' page images (the reading copy, leaves 33 and 35 — book pages 24 and 26).
Page 24 prints `109.`, then `110 — 119. Vorerinnerung zur Erforschung der reinen
Arznei-Wirkungen an gesunden Menschen; Erstwirkung, Nachwirkung.`, then `120.` Page 26
prints `168 — 180.`, `181 — 193.`, `194 — 228.` (with its `Anm.`), `229 — 244.`, `245 — 250.`,
`251.` and `252 — 257.` So every end restored from a neighbouring entry or from the second
copy is the number the page itself prints: none of the four rests on inference about the
list's order. The images are not committed; the pages are cited here so the check can be
repeated.

**Why the 1824 German is nearly whole.** Both copies read their marks (`organonderheilku02hahn`
and Google's `organonderheilk01hahngoog`), so 297 blocks covering 307 of 320 paragraphs were
recovered; the 13 lost numbers are named. The two copies are different scans of the same
printing and are parsed independently.

**What is not carried.** Hahnemann's Introduction, prefaces and footnotes are not part of the
numbered text; none of these three bundles carries them, and the reader says so. The 1819
bundle also does not carry the 1819 paragraphs (see above) — only the list that numbers them.

**Rebuilding.** The OCR files are not committed. Fetch them (`<id>_djvu.txt` from
`https://archive.org/download/<id>/`) into `$ORGANON_SRC` as
`organon2/organonderheilku01hahn.txt`, `organon2/10476160bsb.txt`,
`organon3/organonderheilku02hahn.txt`, `organon3/organonderheilk01hahngoog.txt`,
`organon2fr/b2930538x.txt` and `organon2fr/bub_gb_Qr_z-ZNDW48C.txt`, then:

    ORGANON_SRC=. PYTHONPATH=tools python3 tools/build-organon2-fr.py
    ORGANON_SRC=. PYTHONPATH=tools python3 tools/build-organon2.py
    ORGANON_SRC=. PYTHONPATH=tools python3 tools/build-organon3.py

The French build runs first: `tools/build-organon2.py` corroborates the restored range ends
against the paragraph numbers in `docs/organon2-fr-data.js`, and if that bundle is not there
it restores no end from a neighbouring entry — the uncorroborated ends stay named gaps.

## The machine translations — generated text, quarantined

`tools/translate-mt.py` sends each German block to Google's `translate_a/single` endpoint
**once, at build time**, and writes `docs/organon2-en-mt-data.js` and
`docs/organon3-en-mt-data.js`. No key is used and nothing is fetched at run time: the
reader loads the result from disk like any other bundle.

What keeps it honest:

- it is a **separate bundle** with a **separate store key**, so a bookmark or a note cannot
  cross between a machine book and a published one;
- every section carries `mt: true` and `from: "machine translation"`, and the reader prints
  *machine translation — generated text, not a published translation* above the text of every
  such section, and in that book's footer;
- `meta.machine_translation` names the engine, the date, the German bundle it came from, and
  carries the caveat; `meta.verification` records that there is nothing to corroborate it
  against, because the translation it would be checked against does not exist;
- the figures on this page are the German ones. A machine bundle is a rendering of its German
  source, inherits its gaps, and adds its own errors; the German is the authority.

    ORGANON_MT_CACHE=/tmp/organon-mt-cache.json python3 tools/translate-mt.py

The cache holds each source paragraph by SHA-256, so a rebuild only sends what changed.
