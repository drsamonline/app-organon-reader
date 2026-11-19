#!/usr/bin/env python3
"""build-organon3.py — the THIRD edition (1824), in Hahnemann's German.

The third edition is *Organon der Heilkunst* (Dresden, Arnold, 1824), "Dritte verbesserte
Auflage", 320 numbered paragraphs. Like the second it was never translated into English;
unlike the second it is a nearly unchanged reprint of it, with a few new paragraphs.

Two copies of the 1824 printing are used, and both read their marks well:
`organonderheilku02hahn` is the reading text and `organonderheilk01hahngoog` (Google's
scan) is the check and a second reading text.

Ranges are carried the same way as in the second edition: one block under its first
number, `to` recording the last. See `tools/scanlib.py`.

    ORGANON_SRC=. python3 tools/build-organon3.py
"""
import re
import scanlib

MAX = 320            # the 1824 printing numbers its paragraphs to §320
FLOOR = 0.60
END_MATTER = re.compile(r"^\s*(?:Einleitung|Vorrede|Anhang|Inhalt|Register|Druckfehler|"
                        r"Verbesserungen|Nachschrift|Inhaltsanzeige)\b")
DROP = re.compile(r"^\s*(?:Organon\s+der\s+Heilkunst|Organon)\s*[.,]?\s*$", re.I)
# the book's first sentence, which separates the printed synopsis from the text itself
BODY = re.compile(r"einzige\s+Beruf\s+des\s+Arztes", re.I)

SOURCES = [
    {"ident": "organonderheilku02hahn", "path": "organon3/organonderheilku02hahn.txt",
     "label": "Hahnemann-1824-BN", "require": ("DRITTE", "AUFLAGE"),
     "refuse": ("ZWEITE VERMEHRTE AUFLAGE", "WILLIAM BOERICKE", "DUDGEON", "DEVRIENT"),
     "edition": "third edition (1824), Hahnemann's German, Arnold, Dresden",
     "end_matter": END_MATTER, "drop": DROP, "body": BODY},
    {"ident": "organonderheilk01hahngoog", "path": "organon3/organonderheilk01hahngoog.txt",
     "label": "Hahnemann-1824-Google", "require": ("DRITTE", "AUFLAGE"),
     "refuse": ("WILLIAM BOERICKE", "DUDGEON", "DEVRIENT"),
     "edition": "third edition (1824), a second copy of the same printing",
     "end_matter": END_MATTER, "drop": DROP, "body": BODY},
]

NOTES = [
    "This is Hahnemann's German of 1824. No English translation of the third edition has "
    "ever been published; the English beside it is a machine translation, labelled as one.",
    "The 1824 preface records that the previous edition had by then been translated into "
    "French — Brunnow's *Organon de l'art de guérir*, Dresden, 1824, which is bundled "
    "separately. It is the same reason the second edition has a French text and no English "
    "one.",
    "The book sets a paragraph number in the margin, and a range where several paragraphs "
    "share one sentence (§90–105, §110–119, §258–274 and others). Each block is carried "
    "under its first number with the range recorded.",
    "Hahnemann's Introduction and footnotes are not part of the numbered text and are not "
    "carried; the reader says so rather than filling the gap.",
]


def main():
    scanlib.build(
        out_js="docs/organon3-data.js", out_json="organon3-sections.json",
        global_name="ORGANON3", max_n=MAX, sources=SOURCES,
        edition="Third edition (1824), Hahnemann's German",
        title="Organon der Heilkunst", translator="Samuel Hahnemann (German original)",
        language="de", source_url="https://archive.org/details/organonderheilku02hahn",
        comment="The third edition (1824) in Hahnemann's German, read from two scans of the\n"
                "1824 printing. This edition has no English translation.",
        confidence_note="No transcription of this printing exists, so the check is scan "
                        "against scan. Both copies are legible and independently parsed, "
                        "so the figure does catch words one scan lost and the other kept.",
        notes=NOTES, floor=FLOOR, generator="tools/build-organon3.py",
        extras=(("machine_translation", None),
                ("english_translation_exists", False)))


if __name__ == "__main__":
    main()
