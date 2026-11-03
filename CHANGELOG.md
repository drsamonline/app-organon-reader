# Changelog

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
