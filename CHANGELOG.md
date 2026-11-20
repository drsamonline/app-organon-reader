# Changelog

## 1.6.3 — 2026-11-20

**The four restored ranges are confirmed on the printed page.**

- **Read back on the scans' page images.** §110–119, §181–193, §194–228 and §245–250 were
  checked against the reading copy's leaves 33 and 35 (book pages 24 and 26). Page 24 prints
  `110 — 119.` and `120.`; page 26 prints `181 — 193.`, `194 — 228.` (with its `Anm.`),
  `229 — 244.` and `245 — 250.` Every end the build restores from a neighbouring entry or the
  second copy is therefore the number the page itself prints, and the 1.6.2 correction stands
  on the page, not only on the list's order.
- **No figures change.** 98 blocks, 280 of 318 numbered paragraphs covered, 38 named gaps, 46
  assertions. The provenance note in `data/README.md` is the only addition.

## 1.6.2 — 2026-11-20

**The 1819 list's local-ailment entry is §194–228, not §182–228; range ends are now borrowed
from the second copy for real, and the restoration fails closed without the French.**

- **A restored start that was wrong is corrected.** The reading copy prints the entry's start
  as `394` and its end as `228`. 1.6.1 restored the start from the entry beside it while that
  entry was still truncated to `§181`, giving §182–228 — a 46-number span, and a start that
  collided with the range above it. The second copy prints that entry whole, `181 — 193.`, so
  the local-ailment entry begins at §194, where Brunnow's §194 opens the same subject. The
  bundle now carries §181–193 and §194–228; `§182` is not a block start.
- **The second copy now actually settles numbers, and the claim is no longer empty.** 1.6.1
  printed "numbers settled by the second copy: 0": the entry match compared only the opening
  words of a rubric, so a scan that breaks a word across lines (`Krank-` / `heiten`) never
  matched the reading copy's line. It compares the printed line instead, matches `l8l — igS`
  against `181 — 193.`, and `meta.numbered_from_second_copy` is now 1 — counted from the
  blocks that record it in `numbers_from`, not asserted.
- **Range-end restoration fails closed.** With `docs/organon2-fr-data.js` absent there is no
  corroboration, so no end is restored from a neighbouring entry: the build prints that it
  will restore none that way and leaves those numbers as named gaps (232 covered, 86 gaps)
  instead of reading "not built" as consent. An end the second copy itself prints is still
  settled — §181–193 stands even then. Nothing else about the build depends on the French.
- **Figures.** 98 blocks covering 280 of 318 numbered paragraphs, 38 named gaps — unchanged;
  the widest carried range drops from 46 numbers to 34, so the suite's range guard is back to
  40. The suite is unchanged at 46 assertions, now with four more checks on this boundary.
- **The machine-translation bundle follows the German blocks** under the corrected numbers,
  carrying the same English for the same rubric; the translation itself was not re-run.

## 1.6.1 — 2026-11-19

**The 1819 German now says what it is, and carries 280 of 318 numbered paragraphs instead of
176.**

- **The second edition's German bundle is its printed *Inhaltsanzeige*, and now says so.**
  `tools/build-organon2.py` was reading the list of numbered rubrics the 1819 book sets
  before the Einleitung and presenting it as the paragraphs. The paragraphs are printed
  later, and both surviving scans read the body's pages across the fold — a paragraph's tail
  lands inside the next one — so they are not carried. Title, notes, the reader's book blurb
  and `data/README.md` now name the part correctly.
- **More of the numbering recovered.** §110–119 and §245–250 came back: an entry whose range
  lost one end to OCR keeps the end that was printed, and the lost end is taken from the
  entry beside it only where Brunnow's French contents list prints every number the restored
  range would cover. Each restored block records it in `numbers_from`. (A third, §182–228,
  was restored the same way and was wrong — see 1.6.2.)
- **A tolerant reader for printed number lines** (`tools/scanlib.py`): `J.06` is 106, `j54`
  is 154, `l5g` is 159, a full stop printed inside a number is folded away, junk between a
  number and its dash no longer hides the range. The second 1819 copy is read as well, for
  its words — and, from 1.6.2, for the range ends the reading copy mangled.
- **Gaps named, not filled.** 38 numbers remain unreadable in both copies — `§8–11`, `§13`,
  `§14`, `§42–44`, `§47`, `§67`, `§68`, `§72`, `§78`, `§251–257`, `§259–274`, `§311` — and
  are listed in `meta.missing` and shown as gaps.
- The machine translation of the second edition is regenerated from the new German text and
  says that what it translates is the Inhaltsanzeige.

## 1.6.0 — 2026-11-19

**The shelf is complete: the second and third editions join it, in the languages they were
printed in, with a machine translation where no published English exists.**

- **The second edition (1819), in Hahnemann's German** (`tools/build-organon2.py`): 88 blocks
  covering 176 of the book's 318 numbered paragraphs, read from two copies of the 1819
  printing. The reading copy is a poor scan — its margin numbers come out as `J.06` for §106
  — and the second copy's marks are unreadable, so 142 numbers are named as gaps rather than
  guessed.
- **The third edition (1824), in Hahnemann's German** (`tools/build-organon3.py`): 297 blocks
  covering 307 of its 320 numbered paragraphs, read from two legible copies. Median
  corroboration 1.000, minimum 0.956; the 13 lost numbers are named.
- **Brunnow's French of 1824** (`tools/build-organon2-fr.py`): 314 blocks covering 314 of 318
  numbered paragraphs — the second edition as French readers had it, untranslated here.
- **A new parser** (`tools/scanlib.py`) for a third kind of book. The 1819 and 1824 printings
  set a number in the margin and a **range** where several paragraphs share one sentence
  (`§90–105`), so one block is carried under its first number with `to` recording the last.
  Nothing inside a range is invented or sixteen times duplicated.
- **Machine English for both German editions** (`tools/translate-mt.py`), built once at build
  time through Google's endpoint. It is a separate bundle, carries `mt: true` and its engine
  in the meta, prints *machine translation — generated text* above every section and in the
  book's footer, and has its own store key so a bookmark cannot cross into a published
  edition. No key is used and the app still fetches nothing.
- **The badges are generated from the books, not typed.** `scripts/badges.py` now reads the
  bundles and the suite and rewrites the README badge block between `badges:start` and
  `badges:end`, so a figure that changes in the data changes in the badge. The old editions
  badge claimed `4 · 271+292+294+291` — a sum of the four English books' paragraph counts that
  read as if it were the number carried — and a `sections.svg` was generated but never shown.
  Both are fixed: *6 editions*, *4 English · 2 machine*, *1082/1148* sections.
- The suite went from 40 to 46 assertions: ranges cover every number they claim, the missing
  list is exactly the numbers no block covers, and every machine-translated section is
  labelled as one.

## 1.5.0 — 2026-11-19

**Four editions instead of two.** The first edition (1810) and the fourth (1829) join the
fifth and sixth, in the only English translations either has ever had.

- **The first edition — Wheeler, 1913** (`tools/build-organon1.py`): 256 of the book's 271
  aphorisms, read from two scans of the 1913 Everyman's printing. Wheeler printed no §158 and
  no §160 and omitted Hahnemann's Introduction and most of his footnotes; those omissions are
  his, and the reader does not fill them. Median corroboration 1.000, minimum 0.934.
- **The fourth edition — Devrient, 1833** (`tools/build-organon4.py`): 241 of 292 aphorisms,
  read from four scans of the 1833 printing — the first English Organon, and the edition that
  first carries the chronic miasms. The book numbers its paragraphs in Roman numerals and OCR
  loses some; where a numeral is lost the section is named as missing, never merged with its
  neighbour. Median corroboration 1.000, minimum 0.962.
- **The second and third editions are not offered, because no English translation of either
  exists.** They were translated into French and other languages, never into English; nothing
  was translated, paraphrased or generated to stand in for them.
- **A new method note:** these two bundles have no transcription to check against, so their
  verification is scan against scan. That catches OCR damage, not a wrong edition, and both
  bundles say so in `meta.verification.note`. Each records the SHA-256 of every scan it used.
- **The edition chips are generalised.** Every edition is now read beside a reference edition
  (the sixth for the earlier books, the fifth for the sixth) and says *only here*, *only
  there*, *wording differs* or *same wording* against it.
- The suite went from 35 to 40 assertions; the sixth- and fifth-edition assertions are
  unchanged.

## 1.4.0 — 2026-11-03

**Two editions, and the reader can tell them apart.** The fifth edition joins the sixth
as a second complete book, and the reader switches between them.

- **The fifth edition is a different book, not a re-rendering.** 74 of the sections are
  worded differently and three (\u00a7292\u2013\u00a7294) exist only in the fifth. The reader says so on every
  section: *only in the fifth edition*, *wording differs from the sixth edition*, or *same
  wording in both editions*.
- **Where it came from:** the same fifteen Medi\u2011T pages the sixth edition already used.
  `tools/parse-homeoint.py` skips a labelled fifth-edition block by design; the new
  `tools/build-organon5.py` keeps it instead, and takes a bare heading (the text both
  editions share) for either book. The fifteen pages were re-fetched through the Internet
  Archive and every one matched the SHA-256 already pinned in `homeoint_pages.json`.
- **Corroborated, not assumed:** three scans of Dudgeon's 1849 translation \u2014 Wellcome 1893,
  Internet Archive 1849, Google 1849 \u2014 with an edition guard that refuses any scan naming
  Boericke as translator. 12-letter-sequence coverage: median **0.979**, minimum **0.745**,
  all 294 sections above the 0.60 floor. (Boericke & Tafel published Dudgeon's translation
  too, so a bare \"Boericke\" in a scan proves nothing; the guard keys on the translator.)
- **Bookmarks stay in their own book.** Each edition has its own store key, because a note
  on \u00a7153 means a different paragraph in each.
- The suite went from 29 to 35 assertions; the sixth-edition assertions are unchanged.

## 1.3.1 — 2026-11-02

- # 1.3.0 — the whole book, and the sources audited The owner sent three sources and asked for the missing sections to be filled and the app audited. Result: **291 of 291 sections**, each one traceable. - **Reading text:** the MediT transcription (homeoint.org) of the 1922 Boericke translation, parsed sixth-edition-only (`tools/parse-homeoint.py`): where the site prints a fifth-edition variant beside a sixth, the fifth is skipped. - **Proof it is the same book:** for each section, the fraction of its 12-letter sequences found verbatim in the three OCR scans - median **0.976**, minimum **0.729**, floor for acceptance **0.60**. A paraphrase scores near zero, so this is a real check. - **Provenance on screen:** every section shows `text from the MediT transcription - corroborated against 3 scans (98% of its word-runs found verbatim)`. - **Refused, with reasons:** the drcherylkasdorf.com PDF is the **Kunzli/Naude/Pendleton 1982 translation, (c) The Hahnemann Foundation** - a different, in-copyright translation; `in.ernet.dli.2015.31779` is **Sarkar's edition with commentary**, a different book whose OCR cannot read its own marks; homeopathyworld.in drops footnotes and garbles the 150th aphorism. All recorded in `data/README.md`. - **Audit of the app itself:** the suite went 26 to 27 assertions; the gap-stepping tests now run against a purpose-built fixture (a bundle with the 7th section removed) because the real bundle no longer has gaps, and a new assertion checks the corroboration floor is met by every single section.

## 1.3.0 — 2026-11-02

**All 291 sections.** The reading text is now the MediT transcription of the 1922
Boericke translation, corroborated section by section against three OCR scans of the
printed book (median 98% of each section's word-runs found verbatim; nothing below 60%
accepted). Every section records its source and that figure, and the reader prints both.
The three sources the owner supplied were audited: the homeoint transcription is used,
while the Kasdorf PDF (a 1982 Kunzli translation, in copyright) and the Digital Library
of India copy (Sarkar's edition with commentary) are refused with reasons recorded. See
`changes/2026-11-02-full-text.md`.

## 1.2.0 — 2026-11-02

Browsing. Every section the bundle carries is now in the left-hand list, with the gaps
named in place; you can jump by number, and walk the book with Next/Previous or the ←
and → keys — the reader steps over a missing section instead of stopping at it. And the
text is now guarded to the **sixth edition only**: `tools/extract.py` refuses any scan
whose front matter does not declare the sixth edition in Boericke's translation. See
`changes/2026-11-02-browse.md`.

## 1.1.0 — 2026-11-02

The text is now read from **three** scans of the 1922 Boericke translation instead of
one, and merged: **255 of the book's 291 sections** (was 156), with each section
recording the scan it came from and the reader saying so. 36 sections remain unreadable
in every scan and are still named, not renumbered. See
`changes/2026-11-02-multi-scan.md`.

## 1.0.0 — 2026-11-02

First release. An offline reader for the *Organon of Medicine*, sixth edition
(Boericke translation, 1922): full-text search, bookmarks and notes on the device,
156 of the book's 291 sections with the missing ones named rather than renumbered.
See `changes/2026-11-02-initial.md`.
