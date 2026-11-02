# Changelog

## 1.2.1 — 2026-11-02

- # 1.2.0 — browse the book, and sixth edition only **The complaint, and it was fair:** the reader showed one section at a time with no way to reach another except search. Now: - the left-hand column lists **every section the bundle carries**, in order, each row previewing its first line; a section that no scan could read appears in place as "§3 — not readable in any scan", so the shape of the gap is visible rather than hidden; - a **§ box** jumps to a number; asking for one that is not carried says so and opens the next section that is, never a different aphorism under the wrong number; - **Next / Previous** buttons at the top and bottom of the text, and the **← / →** keys, both stepping over gaps (`step()` in `docs/reader.js`, tested); - the current section is highlighted and scrolled into view. **Edition discipline.** The three scans are all the 1922 Boericke translation of the sixth edition, and that is now enforced rather than assumed: `require_sixth_edition()` in `tools/extract.py` reads each scan's own front matter and **refuses** any file that does not declare "SIXTH EDITION" and Boericke. The Dudgeon fifth edition and the 1913 "rational art of healing" are therefore not merely unused — they cannot be merged in. The evidence line for each scan is carried in the bundle's `meta.scans`. Suite: **26/26**, with new assertions for the ordered list, stepping over a gap, both ends of the book, jumping to an uncarried number, and "every scan declares the sixth edition in Boericke's translation".

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
