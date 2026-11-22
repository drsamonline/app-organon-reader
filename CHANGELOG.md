# Changelog

## 1.6.14 — 2026-11-22

**A leaf's page is confirmed by two witnesses within six leaves, or by anchors on both sides
of the gap — and a page that would unseat the run already read is refused.**

- **Two wider proofs, and the refusals that keep them honest.** 1.6.12–1.6.13 believed a
  folio only where a neighbouring leaf (within two) printed the number the difference
  predicted. `tools/pages.py` now also believes it where **two** leaves within six print
  that number, or where a leaf already believed lies on **each side** of the gap with none
  of a different numbering between them. A thread that reaches only one way is still
  refused: confirming a leaf from the last anchor alone is reading the page off a leaf
  index. Both wider proofs must also *fit the run already read* — greater than the nearest
  page believed before the leaf, smaller than the nearest after — because the 1819 reading
  copy prints two incompatible numberings (52–59 on one stretch of leaves, 41–55 on the
  next, 56+ from leaf 66); without that guard a bracket confirmed leaf 49 as page 59 and
  unseated the 57 and 58 already recorded at leaves 67–68. Pages are added, never
  withdrawn.
- **What the wider proofs found.** 20 blocks gain a printed page and none loses one: first
  §184–§186 (page 79), second §22–§24, §28, §29, §31–§33 (page 18) and §49, §60, §61, §64,
  §65 (page 21), fourth §121 (page 203, from its own leaf) and §173–§175 (page 231, borrowed
  from the Wellcome copy). Blocks without a page fall from **214 to 194**: 60→57, 76→63, 18,
  27, 33→29. Leaves that print a page rise where the rule widened — Wheeler 151→152, 1819
  reading copy 62→78, 1819 second copy 22→26, 1824 Google copy 236→237, Devrient-Wellcome
  260→263 — and no leaf loses the page it had. No carried text changed: the French and third
  bundles rebuild byte for byte, and the fourth's Dublin/Wellcome pair now compares 87/87
  (was 85/85) and borrows 36 pages (was 33).
- **The refusals are tested, not just measured.** `tools/test-pages.py` runs the rules on
  synthetic leaves, one page per leaf, where the answer is arithmetic: a lone witness four
  leaves away is refused, two at six are accepted, a bracket is accepted, a single far
  witness is refused, a page that runs the book backwards is refused, a number past the last
  leaf is refused. The suite executes it, so it is now **89 assertions** (was 88).

## 1.6.13 — 2026-11-21

**The suite holds the page claims, and a folio one copy lost is read from the other copy of
the printing — but only after the copies are proved to paginate alike.**

- **Page invariants, and the defect they caught.** `node test-node.js` now checks, for all
  five scan bundles, that an end page requires a start page, an end leaf requires a start
  leaf, a page range cannot advance faster than the leaves it covers, pages run forward
  across the whole printing, no page exceeds the leaves any copy has, and every borrowed page
  names its copy and appears in `meta.pages.cross_copy`. The forward-run check failed on the
  fourth bundle: the Dublin scan reads `§XXIII` as `§XXVIII`, so the bundle carried **§23's
  text twice**, as §23 and §28, and §28's page (118) ran backwards from §26's (119). The
  build now refuses a block whose opening duplicates a paragraph already carried; §28 comes
  from the Wellcome copy, which prints it (*It is therefore fully proved…*, page 121). That
  is the only carried text this change altered.
- **Two copies of one printing compared before any page is borrowed.** A block whose own leaf
  prints no readable folio takes the page the other copy prints on the same block, only where
  both copies carry it, their openings agree, and the pair is proved alike: at least eight
  agreeing comparisons and no disagreement. The bundle records every comparison, every
  exclusion and every fill under `meta.pages.cross_copy`. French 207 compared / 207 agree /
  48 borrowed, third 52 / 52 / 3, fourth 85 / 85 / 33. The two refusals are reported: the
  Wellcome copy of Wheeler reads only eight marks, so that pair compares on three blocks
  (below the eight needed); in the 1819 pair no block has a readable page in both copies, so
  all 76 stay named gaps.
- **Blocks with a printed page** (was, in 1.6.12: 196/22/248/267/175): first 196 of 256,
  second 22 of 98, French 296 of 314, third 270 of 297, fourth 208 of 241. Blocks without a
  page: 60, 76, 18, 27 and 33. The reader prints the borrowing copy — *printed page 61, leaf
  97; page read from Hahnemann-1824-Google* — where the page came from the other scan.
- **Fingerprints cover `page_from`** (format 3, re-recorded with that note); the suite is now
  **88 assertions** (was 83). All five bundles rebuild byte for byte from a fresh OCR tree,
  so the borrow is deterministic as well as evidenced.

## 1.6.12 — 2026-11-21

**Every carried block now records the printed page it was read from.**

- **Provenance stopped at the volume.** Each block of the five scan-derived bundles (first,
  second, second in French, third, fourth) named the scan it came from but not where in it,
  so a reader could reach the scan and no further. A scan's `_djvu.txt` has no page breaks;
  its `_djvu.xml` has one `<OBJECT>` per leaf. The new `tools/pages.py` maps each line of the
  text to its leaf by matching the running length of the two (the 1824 reading copy lands
  313 of 313 leaf boundaries on that leaf's own first line) and reads the page number the
  leaf prints (`31`, `RATIONAL ART OF HEALING 25`).
- **A page is recorded only where its neighbours confirm it.** OCR mangles folios as badly as
  it mangles marks — the 1819 reading copy prints `2<i J` for 24, `2f` for 25, `$0` for 20 —
  so a number counts only where another leaf within two prints the number that difference
  predicts and it continues the numbers already read. Anything else is unreadable and gets
  no page. Blocks now carry `page` and `leaf` (plus `page_to`/`leaf_to` when they run over
  more than one), and `meta.pages` names every unreadable leaf and every block left without
  a page.
- **What is still unreadable is reported, not filled.** Blocks with a printed page: first
  196 of 256, second 22 of 98, French 248 of 314, third 267 of 297, fourth 175 of 241. The
  1819 Inhaltsanzeige is the worst: only 62 of its 394 leaves print a number a neighbour
  confirms, so 76 of its 98 blocks carry a leaf and no page. Nothing is taken from the second
  copy's pagination or from where a block stands in the stream.
- **The reader prints it**: *text from the Hahnemann-1824-BN scan (printed page 84, leaf 114)
  · corroborated …*, and says so where the leaf prints no readable number. A block records
  an end page only when the page it begins on is readable too: a lone `page_to` would claim a
  range whose start is unknown. The sixth and fifth editions record no page: a transcription
  is not a leaf.
- **Fingerprints cover the new fields** (format 2, re-recorded with that note): the carried
  text is unchanged, and the suite is now **83 assertions** (was 77), checking that every
  block's page is either printed by its leaf or named, never invented.

## 1.6.11 — 2026-11-21

**The three scan builds are byte-for-byte reproducible.**

- **The rebuild was one key order away from matching.** `tools/scanlib.py`'s `_finish()` wrote
  `meta.range_conflicts` after `scans` and `notes`, while the committed 1824 bundle carries it
  between the `verification` figures it explains and the `scans` list. With the OCR fetched
  and the three builds run, the German came out the same 349892 bytes with the record in a
  different place — content-identical, but not byte-identical. The cut is now inserted before
  `scans`; a bundle with no cut keeps the layout it had, so neither other bundle moved.
- **This is measured, not asserted.** The six OCR files were fetched into `ORGANON_SRC` and
  the three builds run in the documented order, French first: `docs/organon2-fr-data.js`
  (448177 bytes, sha256 `ca19a6e2…`), `docs/organon2-data.js` (40862 bytes, `258ba084…`) and
  `docs/organon3-data.js` (349892 bytes, `36d2f070…`) each come back byte for byte. No bundle
  byte changed here, so the fingerprints stand 9/9 and every quoted figure is the same; the
  reproduction command and hashes are in `data/README.md` under **Rebuilding**.
- **The suite is unchanged at 77 assertions**, and runs green with the new order: the two
  bundles still carry the same §123 cut, and `tools/test-scanlib-range.py` still builds the
  synthetic book in both source orders.

## 1.6.10 — 2026-11-21

**The 1824 bundle stops carrying §124 twice.**

- **The section belongs to the block that prints its own mark.** The Google copy of the 1824
  printing reads its §123 mark as a range, `§123–124`, and its text is §123's one sentence —
  *Jede Arznei hat von der andern verschiedene Wirkungen. Anm. Es kann keine Surrogate geben.*
  The BN copy of the same printing prints §124 under its own mark: *So gewiß jede Pflanzenart
  in ihrer äußern Gestalt…*. Both blocks were kept, so the bundle carried §124 twice, with
  different text. §124 is now the BN block alone and the range stops at §123.
- **The decision is not a guess about which OCR read the page better.** It is Brunnow's French
  of the same year that settles it: his §124 opens *De même que chaque espèce de plantes
  diffère de toute autre espèce…* — the German block under BN's §124 mark — and his §123 is
  §123's sentence, *De chaque médicament résulte des effets particuliers…*.
- **`tools/scanlib.py` now lets no block claim a number another block already carries.** A
  block printed under its own mark takes that number first, whichever copy of the printing
  was read first, and a range is cut back to the numbers still unowned; the cut is written
  into the bundle as
  `meta.range_conflicts` (`{"n": 123, "printed_to": 124, "kept_to": 123, "owned_elsewhere":
  [124], "owner": {"124": 124}}`), so a trimmed block is a record rather than a silent edit.
  A number cut away that no other block carries becomes a named gap like any other; nothing
  is renumbered and no text is moved between sections.
- **The machine bundle mirrors the corrected range.** `docs/organon3-en-mt-data.js` is built
  block for block from the German, so §123's machine rendering stops at §123 as well, and it
  carries the same `range_conflicts` record.
- **The rule is exercised, not just described.** With the OCR uncommitted the real bundle
  cannot be rebuilt in a checkout, so `tools/test-scanlib-range.py` builds a synthetic book
  from two invented scans — one prints §5 on its own mark, the other reads its §4–§5 block as
  a range — and `scanlib.build` must keep §5 with its own mark, cut the range to §4, record
  the cut, and leave a range nobody contests whole. The suite runs it in both source orders,
  because the copy read first is not an argument about the page.
- **The suite now refuses any bundle that carries one number in two blocks**, and asserts the
  recorded cut in both 1824 bundles. **77 assertions** (was 75), and the `tests` badge is
  regenerated from the run.
- The OCR is not committed, so the two bundles are corrected in place; the rule is in
  `scanlib.build`, which is what a rebuild runs, so `tools/build-organon3.py` reproduces
  these blocks rather than the duplicated one.

## 1.6.9 — 2026-11-20

**Three guards on the books themselves: the figures, the carried text, and the numbering.**

- **The documents' figures are now checked against the bundles.** `README.md` and
  `data/README.md` quote the carried counts, medians, minima and named gaps of every edition;
  prose is not compiled, and the sixth edition's median was quoted as 0.976 for a while after
  the bundle said 0.981. Each of those sentences is now a claim in the suite with its figures
  captured and compared to the bundle that owns them, including the fifth-versus-sixth counts
  (`74` reworded, `§292–§294` only in the fifth), the 1819 list's `280 of 318`, the min-0 note's
  `99` checked against `98` blocks and its refused `§251`, and the assertion count both
  documents print against the `tests` badge. A reworded sentence fails too, so a figure and
  the sentence carrying it move together.
- **A rebuild that changes carried text now fails until it is recorded.** The OCR is not
  committed, so no CI job can rebuild the nine books and compare; `data/fingerprints.json`
  instead freezes every carried block — number, printed range end, source label, corroboration,
  text, printed notes and machine flag — and `node test-node.js` refuses any bundle whose blocks
  no longer match, naming the sections that moved. `tools/fingerprint.js record --note "why"`
  is the deliberate act that re-records them, and the note is the record of why.
- **The numbering across the books is finally visible.** A concordance view sets §1–320 (the
  widest book, the 1824 German) beside seven columns — Wheeler, Devrient, Dudgeon, Boericke,
  the two German editions and Brunnow's French — and every cell opens that book at the block
  that prints the number, ranges included. It is a map, not a merged text: no cell is filled in
  from another edition, a number a book does not carry stays empty, and the machine
  translations take no column because each covers exactly its German blocks. The matrix comes
  from `R.concordance` in the engine, and the suite checks each column against the bundle's own
  `numbered_paragraphs_carried` and `missing` list.
- **The map found a duplicated number in the 1824 bundle.** §124 is printed inside the Google
  copy's `§123–124` block *and* under its own mark in the BN copy, so the bundle carries §124
  twice, with different text. The map opens the block that prints the number under its own mark
  and reaches the range from its first number; the duplication itself is recorded here rather
  than quietly resolved.
- **75 assertions** (was 57), and the `tests` badge is regenerated from the suite.

## 1.6.8 — 2026-11-20

**The provenance line becomes a function the suite holds, and one figure is corrected.**

- **The sentence moved from the page into the engine.** `R.provenance(row, meta)` returns the
  line printed under a section number as plain text; `docs/play/index.html` now only wraps it
  in its `div` and escapes it once, whole. The page was the one part of the reader no test
  could reach, so the claim in `data/README.md` that the reader prints the source and the
  corroboration figure rested on markup nothing executed.
- **Every section of all nine bundles is asserted** — source label, the kind of source, the
  number of scans that checked it, and the figure itself, computed from each section's own
  `corroboration`. A machine section must say it is machine text and must never read as
  published text. A further assertion fails if the page grows its own copy of the sentence
  again, and checks that the function leaves its arguments untouched.
- **The sixth edition's median is 0.981, not 0.976.** `data/README.md` still quoted the figure
  from before the bundle was rebuilt. The bundle records `median: 0.981`, and the 291
  section-level figures give the same median. The minimum, 0.729, was already right.
- **Why the second edition records `min` 0 is now written down.** Its `meta.verification` counts
  what was *checked*, not what was kept: §251 scored 0.0 and was refused, so it is a named gap,
  while all 98 carried blocks sit at 0.996 or above. `data/README.md` says so beside the gaps, so
  the zero is not read as a fault in carried text.
- **57 assertions** (was 47), and the `tests` badge is regenerated from the suite. The stale
  counts in both READMEs (`40` in `data/README.md`, `46` in `README.md`) now read 57.

## 1.6.7 — 2026-11-20

**The French bundle's §1 opens with its printed word.**

- **The fragment is a printed drop cap, not a lost number.** The new guard flagged the
  French §1's `J— /a première…`; leaf 117 of the reading copy prints `§. 1.` above
  `La première et unique vocation du médecin`. Stripping the fragment as §181's was stripped
  would have deleted the printed `L` and left `/a première…`, so §1 is carried as
  `La première…`, read from the page.
- **The scans were fetched again and matched.** Both copies re-downloaded and hashed to the
  SHA-256 values in `meta.scans` (618,867 and 558,784 bytes), so the rebuild rests on the same
  bytes the bundle records.
- **`scanlib.build` takes a `text_fix` map.** `{number: (as_read, as_printed)}` is for a word
  the scan destroyed and the page settles; it is applied before verification, and the book's
  notes must name the page, so a transcription cannot pass as OCR. The French build uses it
  once, for §1, and says so in its notes.
- **No figures move.** 318 numbered paragraphs, 314 blocks, 314 covered, 4 named gaps
  (216–218, 287), 47 assertions; §1's text and the bundle's notes are the only changes.

## 1.6.6 — 2026-11-20

**A guard against the lost-number fragment.**

- **The 1.6.4 entry no longer claims §31 was a lost range end.** It records only §181, and adds
  that §31 was stripped on the same reasoning and should not have been; the correction stays in
  1.6.5.
- **The suite now refuses the fragment.** No rubric in the German bundle or its machine
  translation may begin with a short token followed by a dash (`igS- Mafsregeln…`). A printed
  sub-item such as §31's `I.` is prose and passes, because it carries a full stop rather than
  the dash the fragment had.
- **47 assertions** (was 46), and the `tests` badge is regenerated from the suite.

## 1.6.5 — 2026-11-20

**§31's fragment was a printed sub-item, not a lost range end.**

- **The Inhaltsanzeige page settles it.** Book page 18 (reading-copy leaf 27) prints
  `31. I. Die ältere, im Körper wohnende Krankheit hält…`, then `32. So heilen auch nie
  unhomöopathische Curen…`, and the entry after that opens `33. II. Oder eine…`. There is no
  range at §31 and no end to restore: OCR wrote the full stop after `31.` as a dash, which
  made the entry's own `I.` look like a number that failed to read.
- **1.6.4 over-corrected, and is corrected here.** Its strip took that printed `I.` away with
  §181's real fragment. A Roman sub-item after a number is now read as prose, so §31 carries
  `I. Die ältere…` again while §181 keeps its clean `Mafsregeln…`. The machine translation is
  re-mapped (`I. The older disease…`), not re-run, so its build stamp stands.
- **No figures change.** 98 blocks, 280 of 318 numbered paragraphs covered, 38 named gaps, 46
  assertions; §31 remains a single-number block and §32–41 were already carried one by one.

## 1.6.4 — 2026-11-20

**The mangled number that stood for a lost range end is no longer carried as text.**

- **§181 began with an OCR fragment instead of its words.** Where the reader kept the printed
  end of a range and lost the other, it started the rubric at the unreadable token: §181 read
  `igS- Mafsregeln bei Heilung…`. The page prints `Mafsregeln…`, so the token is now dropped
  with the dash, in the one reader that produces both books.
- **The machine translation is re-mapped, not re-run.** The English had been made from the old
  German and echoed the fragment (`igS measures…`); it now drops the echo and starts at the
  surviving word. Meta, the 2026-11-19 build stamp and all 98 sections are otherwise
  unchanged, because no new translation was made.
- **§31 was stripped on the same reasoning, and should not have been.** Its `I-` looked like a
  lost end but is the entry's own printed sub-item; 1.6.5 reads it as prose and restores
  `I. Die ältere…`.
- **No figures change.** 98 blocks, 280 of 318 numbered paragraphs covered, 38 named gaps, 46
  assertions; the page citations in `data/README.md` stand.

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
