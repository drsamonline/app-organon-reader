#!/usr/bin/env python3
"""build-organon2.py — the SECOND edition (1819): the printed Inhaltsanzeige.

*Organon der Heilkunst* (Dresden, Arnold, 1819), "Zweite vermehrte Auflage". It was never
translated into English; Brunnow's French of 1824 is its translation and has its own
bundle, `tools/build-organon2-fr.py`.

What this build carries is the book's own **Inhaltsanzeige**: the list, printed before the
Einleitung, that gives each paragraph's number in the margin — one number, or a range
where several paragraphs share one thought (`90 — 105`) — with its rubric. The paragraphs
themselves are printed after the Einleitung, and they are *not* carried here: both
surviving scans of the 1819 book misorder the body's pages (a spread is read line by line
across the fold, so a paragraph's tail lands in the next one), and setting that right is a
transcription, not a parse. The bundle says so in `meta` and in its notes; it does not
offer the contents list as if it were the text.

The numbering comes from two copies of the 1819 printing. `organonderheilku01hahn` is the
reading copy; `10476160bsb` (Bayerische Staatsbibliothek) reads several margin numbers the
reading copy mangled (`181 — 193.` where the other has `l8l — igS`), and it corroborates
the words of every block.

A range that lost one end to OCR keeps the end that was printed. The lost end is taken
from the entry beside it — the list enumerates the paragraphs in order — and only when
Brunnow's French contents list, which prints every paragraph 1–318, has the numbers the
restored range would cover. Every restored end is recorded on its block (`numbers_from`);
anything that cannot be settled that way stays a named gap.

    ORGANON_SRC=. PYTHONPATH=tools python3 tools/build-organon2.py
"""
import os
import re
import scanlib

MAX = 318            # the 1819 printing numbers its paragraphs to §318
FLOOR = 0.60
END_MATTER = re.compile(r"^\s*(?:Einleitung|Vorrede|Anhang|Inhalt|Register|Druckfehler|"
                        r"Verbesserungen|Nachschrift|Inhaltsanzeige)\b")
DROP = re.compile(r"^\s*(?:Organon\s+der\s+Heilkunst|Organon)\s*[.,]?\s*$", re.I)
# the list's first entry, which separates the title page and preface from it
BODY = re.compile(r"einzige\s+Beruf\s+des\s+Arztes", re.I)
# the second copy's OCR of the same first entry
BODY_BSB = re.compile(r"Beruf\s+des\s+Arztes", re.I)

SOURCES = [
    {"ident": "organonderheilku01hahn", "path": "organon2/organonderheilku01hahn.txt",
     "label": "Hahnemann-1819-BN", "require": ("ZWEITE", "AUFLAGE"),
     "refuse": ("DRITTE VERBESSERTE AUFLAGE", "WILLIAM BOERICKE", "DUDGEON", "DEVRIENT"),
     "edition": "second edition (1819), Hahnemann's German, Arnold, Dresden",
     "role": "reading copy of the Inhaltsanzeige and the check",
     "body": BODY},
    {"ident": "10476160bsb", "path": "organon2/10476160bsb.txt",
     "label": "Hahnemann-1819-BSB", "require": (), "refuse": ("WILLIAM BOERICKE",),
     "edition": "second edition (1819), Hahnemann's German, a second copy",
     "role": "second copy: reads margin numbers the other mangles",
     "body": BODY_BSB},
]

FRENCH = "docs/organon2-fr-data.js"      # built by tools/build-organon2-fr.py

NOTES = [
    "This is Hahnemann's German, but it is the printed Inhaltsanzeige — the list of "
    "paragraph numbers with their rubrics that the 1819 book sets before the Einleitung "
    "— not the paragraphs themselves. The paragraphs are printed later in the book, and "
    "both surviving scans of it misorder the body's pages, so their text cannot be set "
    "here without inventing the joins. The French beside it carries the paragraphs whole.",
    "No English translation of the second edition has ever been published, so no English "
    "edition is offered in its place: the German is the second edition's own list, and "
    "the machine translation beside it is generated text, not a translation anybody "
    "published.",
    "The 1819 list sets a paragraph number in the margin and, where several paragraphs "
    "share one thought, a range: §90–105 is one rubric under sixteen numbers, not sixteen "
    "statements. Each block is carried under its first number with the range recorded; "
    "nothing inside the range is invented or duplicated.",
    "Two copies of the 1819 printing were read. Where the reading copy's margin number is "
    "destroyed, the second copy's number is used; where a range lost one end, that end is "
    "taken from the entry beside it, and only if Brunnow's French contents list prints "
    "every number the restored range would cover. Each such block records where its "
    "number came from. Everything else is a named gap.",
]


def read_copy(src, corpus):
    """The entries of one copy of the printing, plus its bytes for the record."""
    path = os.path.join(os.environ.get("ORGANON_SRC", "."), src["path"])
    if not os.path.exists(path):
        print(f"  !! missing source {path} — skipped (recorded in data/README.md)")
        return None, None
    blob = open(path, "rb").read()
    text = blob.decode("utf-8", "replace")
    flat = re.sub(r"\s+", " ", text).upper()
    for word in src.get("refuse", ()):      # the edition guard
        if word in flat:
            raise SystemExit(f"refusing {src['label']}: names {word}")
    for word in src.get("require", ()):
        if word not in flat:
            raise SystemExit(f"refusing {src['label']}: does not declare {word}")
    entries = scanlib.overview_entries(path, MAX, src.get("body"), END_MATTER, DROP)
    corpus.update(scanlib.grams(text))
    evidence = scanlib.evidence_line(flat, src.get("require", ()))
    meta = scanlib.scan_meta(src["ident"], src["label"], blob, text, evidence,
                             src["edition"], role=src["role"], sections=len(entries))
    print(f"  scan {src['label']:22s} {len(entries):3d} entries readable")
    return entries, meta


def main():
    corpus, scans = set(), []
    entries_by_label = {}
    for src in SOURCES:
        entries, meta = read_copy(src, corpus)
        if entries is None:
            continue
        entries_by_label[src["label"]] = entries
        scans.append(meta)
    known = scanlib.bundle_numbers(FRENCH)
    for entries in entries_by_label.values():
        scanlib.resolve_entries(entries, MAX, known=known)

    primary = entries_by_label.get("Hahnemann-1819-BN") or next(iter(entries_by_label.values()))
    print(f"  french contents list: {len(known or ()) } numbered paragraphs (corroboration)")

    # the second copy can settle an entry the reading copy could not number at all
    others = [e for lab, es in entries_by_label.items() if lab != "Hahnemann-1819-BN"
              for e in es]
    borrowed = 0
    if others:
        for e in primary:
            if e["numbers"]:
                continue
            w = scanlib.same_entry(e["text"], others)
            if w and w["numbers"]:
                e["numbers"] = list(w["numbers"])
                e["restored"].append({"numbers": list(w["numbers"]),
                                      "from": "the second copy of the printing"})
                borrowed += 1
    print(f"  numbers settled by the second copy: {borrowed}")

    blocks = []
    for e in primary:
        if not e["numbers"]:
            continue
        n, to = min(e["numbers"]), max(e["numbers"])
        extra = {}
        if e["restored"]:
            extra["numbers_from"] = e["restored"]
        blocks.append({"n": n, "to": to, "text": e["text"], "from": "Hahnemann-1819-BN",
                       "extra": extra})

    meta, sections = scanlib.build_from(
        out_js="docs/organon2-data.js", out_json="organon2-sections.json",
        global_name="ORGANON2", max_n=MAX, blocks=blocks, scans=scans, corpus=corpus,
        head={"title": "Organon der Heilkunst — Inhaltsanzeige",
              "edition": "Second edition (1819), Hahnemann's German: the printed "
                         "Inhaltsanzeige",
              "part": "Inhaltsanzeige",
              "translator": "Samuel Hahnemann (German original)",
              "language": "de",
              "source": "https://archive.org/details/organonderheilku01hahn"},
        comment="The second edition (1819) in Hahnemann's German: the printed\n"
                "Inhaltsanzeige, read from two scans of the 1819 printing.\n"
                "The paragraphs themselves are not carried (see data/README.md).\n"
                "This edition has no English translation.",
        confidence_note="No transcription of this printing exists, so the check is scan "
                        "against scan: every block's words must be found in the copies. "
                        "That cannot catch a margin number both copies lost, so the "
                        "missing numbers are named rather than filled.",
        notes=NOTES, floor=FLOOR, generator="tools/build-organon2.py",
        extras=(("machine_translation", None),
                ("english_translation_exists", False),
                ("numbered_from_second_copy", borrowed)))
    print("  note: no English translation of this edition exists (see data/README.md)")


if __name__ == "__main__":
    main()
