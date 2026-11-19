#!/usr/bin/env python3
"""build-organon2.py — the SECOND edition (1819), in Hahnemann's German.

The second edition is *Organon der Heilkunst* (Dresden, Arnold, 1819), "Zweite vermehrte
Auflage". It was never translated into English. It was translated into French in 1824
(Brunnow), and that French book has its own bundle, `tools/build-organon2-fr.py`.

Two copies of the 1819 printing are used: `organonderheilku01hahn` is the reading text
and the check; `10476160bsb` is a library copy whose scan is too damaged to read marks
from, so it is a corpus only — it can corroborate words, not paragraph numbers.

The 1819 book prints a paragraph number in the margin, and where several paragraphs share
one sentence the margin carries a range (`90 — 105`). One block is carried under its first
number, with `to` recording the last; the numbers inside it are covered by that block,
not invented and not duplicated. See `tools/scanlib.py`.

    ORGANON_SRC=. python3 tools/build-organon2.py
"""
import re
import scanlib

MAX = 318            # the 1819 printing numbers its paragraphs to §318
FLOOR = 0.60
END_MATTER = re.compile(r"^\s*(?:Einleitung|Vorrede|Anhang|Inhalt|Register|Druckfehler|"
                        r"Verbesserungen|Nachschrift|Inhaltsanzeige)\b")
DROP = re.compile(r"^\s*(?:Organon\s+der\s+Heilkunst|Organon)\s*[.,]?\s*$", re.I)
# the book's first sentence, which separates the printed synopsis from the text itself
BODY = re.compile(r"einzige\s+Beruf\s+des\s+Arztes", re.I)

SOURCES = [
    {"ident": "organonderheilku01hahn", "path": "organon2/organonderheilku01hahn.txt",
     "label": "Hahnemann-1819-BN", "require": ("ZWEITE", "AUFLAGE"),
     "refuse": ("DRITTE VERBESSERTE AUFLAGE", "WILLIAM BOERICKE", "DUDGEON", "DEVRIENT"),
     "edition": "second edition (1819), Hahnemann's German, Arnold, Dresden",
     "end_matter": END_MATTER, "drop": DROP, "body": BODY},
    {"ident": "10476160bsb", "path": "organon2/10476160bsb.txt",
     "label": "Hahnemann-1819-BSB", "require": (), "refuse": ("WILLIAM BOERICKE",),
     "role": "corpus only: the library scan's paragraph numbers are unreadable",
     "parse": False,
     "edition": "second edition (1819), Hahnemann's German, a second copy",
     "end_matter": END_MATTER, "drop": DROP, "body": BODY},
]

NOTES = [
    "This is Hahnemann's German. No English translation of the second edition has ever "
    "been published, so no English edition is offered in its place: the German is the "
    "second edition, and the machine translation beside it is generated text, not a "
    "translation anybody published.",
    "The 1819 printing sets a paragraph number in the margin and, where several paragraphs "
    "share one sentence, a range: §90–105 is one sentence under five marks, not fifteen "
    "aphorisms. Each block is carried under its first number with the range recorded; "
    "nothing inside the range is invented or duplicated.",
    "The Introduction and Hahnemann's footnotes are not part of the numbered text and are "
    "not carried here; the reader says so rather than filling the gap.",
    "Two copies of the 1819 printing were used. The second (10476160bsb, Bayerische "
    "Staatsbibliothek) is a damaged library scan whose paragraph marks cannot be read, so "
    "it corroborates words only; the coverage figure cannot catch a mark the reading copy "
    "lost, and that limit is stated here rather than glossed over.",
]


def main():
    meta, _ = scanlib.build(
        out_js="docs/organon2-data.js", out_json="organon2-sections.json",
        global_name="ORGANON2", max_n=MAX, sources=SOURCES,
        edition="Second edition (1819), Hahnemann's German",
        title="Organon der Heilkunst", translator="Samuel Hahnemann (German original)",
        language="de", source_url="https://archive.org/details/organonderheilku01hahn",
        comment="The second edition (1819) in Hahnemann's German, read from scans of the\n"
                "1819 printing. This edition has no English translation.",
        confidence_note="No transcription of this printing exists, so the check is scan "
                        "against scan. The second copy is badly damaged, so the figure "
                        "mainly proves the reading copy is consistent with itself; it "
                        "cannot detect a paragraph mark that copy lost.",
        notes=NOTES, floor=FLOOR, generator="tools/build-organon2.py",
        extras=(("machine_translation", None),
                ("english_translation_exists", False)))
    print("  note: no English translation of this edition exists (see data/README.md)")


if __name__ == "__main__":
    main()
