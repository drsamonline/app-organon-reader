#!/usr/bin/env python3
"""build-organon2-fr.py — the SECOND edition (1819) in Brunnow's French, 1824.

Erneste George de Brunnow's *Organon de l'art de guérir, traduit de l'original allemand*
(Dresden, Arnold, 1824) is the French translation of the second German edition. The
evidence is Hahnemann's own: the preface to the third German edition (1824) records that
the previous edition had been translated into French, and the French book carries the same
318-numbered structure as the 1819 German, ranges and all.

Two copies of the 1824 printing are used: `b2930538x` is the reading text and
`bub_gb_Qr_z-ZNDW48C` (Google's scan) is the check and a second reading text.

It is carried untranslated. A French sentence given to a machine and printed back in
English is not a translation anybody published, and this reader does not present generated
prose as Hahnemann's words in a language he did not write.

    ORGANON_SRC=. python3 tools/build-organon2-fr.py
"""
import re
import scanlib

MAX = 318            # the French follows the 1819 numbering, §318 at the end
FLOOR = 0.60
END_MATTER = re.compile(r"^\s*(?:INTRODUCTION|TABLE|APPENDICE|NOTES?|ERRATA)\b")
DROP = re.compile(r"^\s*(?:Organon\s+de\s+l['’]art\s+de\s+gu[ée]rir)\s*[.,]?\s*$", re.I)
# §1 of the text proper: the book prints a condensed synopsis first, and only this
# sentence opens the translated paragraphs themselves
BODY = re.compile(r"premi[eè]re\s+et\s+unique\s+vocation", re.I)

SOURCES = [
    {"ident": "b2930538x", "path": "organon2fr/b2930538x.txt",
     "label": "Brunnow-1824-BN", "require": ("TRADUIT", "BRUN"),
     "refuse": ("BOERICKE", "DUDGEON", "DEVRIENT", "WHEELER"),
     "edition": "second edition (1819) in Brunnow's French translation, Dresden 1824",
     "end_matter": END_MATTER, "drop": DROP, "body": BODY},
    {"ident": "bub_gb_Qr_z-ZNDW48C", "path": "organon2fr/bub_gb_Qr_z-ZNDW48C.txt",
     "label": "Brunnow-1824-Google", "require": ("TRADUIT",),
     "refuse": ("BOERICKE", "DUDGEON", "DEVRIENT", "WHEELER"),
     "edition": "second edition (1819) in Brunnow's French translation, a second copy",
     "end_matter": END_MATTER, "drop": DROP, "body": BODY},
]

# §1 opens with a printed drop cap that the scan splits into `J— /a`, so the rubric
# began with a fragment that looks like a number but is the word `La`. Read on the page:
# leaf 117 of the reading copy prints `§. 1.` above `La première et unique vocation du
# médecin`. This is a transcription of that word, not a repair of the rest of the OCR.
TEXT_FIX = {1: ("J— /a première", "La première")}

NOTES = [
    "Brunnow's French is a translation of the second German edition (1819). The third "
    "German edition's preface says so: the previous edition had been translated into "
    "French by the time the third appeared in 1824.",
    "This is the French as printed in 1824, not a machine translation of it. French is "
    "carried because it is a published translation of a book that has no English one; "
    "nothing here is generated.",
    "The book sets a paragraph number in the margin with a range where several paragraphs "
    "share one sentence, exactly as the German does. Each block is carried under its first "
    "number with the range recorded.",
    "Brunnow numbers his paragraphs to §318, like the 1819 German he worked from.",
    "§1's first word is transcribed from the page: the scan splits the printed drop-cap "
    "`La` into `J— /a`, and the rubric is carried as `La première…` (leaf 117 of the "
    "reading copy). The rest of §1 is OCR, with its errors left as the scan gives them.",
]


def main():
    scanlib.build(
        out_js="docs/organon2-fr-data.js", out_json="organon2-fr-sections.json",
        global_name="ORGANON2FR", max_n=MAX, sources=SOURCES,
        edition="Second edition (1819) in Ernest George de Brunnow's French, 1824",
        title="Organon de l'art de guérir",
        translator="Erneste George de Brunnow (French translation, 1824)",
        language="fr", source_url="https://archive.org/details/b2930538x",
        comment="Brunnow's French translation (Dresden, 1824) of the second edition (1819),\n"
                "read from two scans. Public domain.",
        confidence_note="No transcription of this printing exists, so the check is scan "
                        "against scan; the two copies are different scans of the same "
                        "printing, so a word lost in one is usually kept in the other.",
        notes=NOTES, floor=FLOOR, generator="tools/build-organon2-fr.py",
        text_fix=TEXT_FIX,
        extras=(("machine_translation", None),
                ("english_translation_exists", False)))


if __name__ == "__main__":
    main()
