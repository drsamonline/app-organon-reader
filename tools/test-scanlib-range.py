#!/usr/bin/env python3
"""test-scanlib-range.py — execute `scanlib.build`'s range rule on invented blocks.

The 1824 printing is the case the rule was written for, but its OCR is not committed, so
the bundle cannot be rebuilt in a checkout. This test builds a small invented book out of
two synthetic scans instead: one copy prints §5 under its own mark, the other reads its
§4–§5 block as a range. The bundle must keep §5 with the block that prints the number, cut
the range back to §4 and record the cut — and it must do the same whichever copy is read
first, because source order is not an argument about the page.

    python3 tools/test-scanlib-range.py

Prints a one-line JSON summary last and exits 1 on the first failed claim.
"""
import json, os, sys, tempfile

sys.dont_write_bytecode = True      # importing scanlib must not leave __pycache__ behind
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scanlib

# the copy whose marks the page prints one number at a time
OWN = """§ 1. Das erste Stück der erfundenen Ausgabe steht unter seiner Nummer.
§ 2. Das zweite Stück trägt seine Nummer ebenfalls selbst.
§ 3. Das dritte Stück trägt seine Nummer im Rand.
§ 5. Das fünfte Stück trägt seine Nummer selbst im Rand.
"""

# the copy that reads one thought as a range: §4–§5 here, §7–§9 with no other owner
RANGE = """§ 1. Das erste Stück der erfundenen Ausgabe steht unter seiner Nummer.
§ 4 — 5. Das vierte Stück ist mit dem fünften in einem Satz gedruckt.
§ 6. Das sechste Stück folgt der Spanne.
§ 7 — 9. Die Spanne, deren Nummern kein anderer Block druckt.
"""

CUT = {"n": 4, "printed_to": 5, "kept_to": 4, "owned_elsewhere": [5],
       "owner": {"5": 5}}


def source(path, label, role):
    return {"path": path, "label": label, "ident": "synthetic-" + label.lower(),
            "edition": "synthetic", "role": role}


def build(order, tmp):
    """Build the invented book, reading the two copies in the given order."""
    files = {}
    for label, body in (("SYN-OWN", OWN), ("SYN-RANGE", RANGE)):
        p = os.path.join(tmp, label + ".txt")
        open(p, "w", encoding="utf-8").write(body)
        files[label] = p
    sources = [source(files[label], label, "parser and corpus") for label in order]
    out_js = os.path.join(tmp, "-".join(order) + ".js")
    meta, sections = scanlib.build(
        out_js, None, "SYNRANGE", 9, sources, "synthetic", "Die erfundene Ausgabe",
        "", "de", "built by tools/test-scanlib-range.py",
        "both copies are invented for the test", generator="tools/test-scanlib-range.py")
    return meta, sections


def claim(cond, message):
    if not cond:
        raise AssertionError(message)


def check(order, tmp):
    meta, sections = build(order, tmp)
    by_n = {s["n"]: s for s in sections}
    claim(sorted(by_n) == [1, 2, 3, 4, 5, 6, 7],
          f"{order}: expected blocks 1–7, got {sorted(by_n)}")
    claim(by_n[4]["to"] == 4,
          f"{order}: the range 4–5 must stop at §4, got {by_n[4]['to']}")
    claim(by_n[4]["from"] == "SYN-RANGE",
          f"{order}: §4 belongs to the copy that printed the range, got {by_n[4]['from']}")
    claim(by_n[5]["from"] == "SYN-OWN" and "fünfte Stück trägt seine Nummer selbst" in by_n[5]["text"],
          f"{order}: §5 must carry the block printed under its own mark, got {by_n[5]['from']}")
    claim(by_n[7]["to"] == 9,
          f"{order}: a range no other block competes for must stay whole, got {by_n[7]['to']}")
    claim(meta["range_conflicts"] == [CUT],
          f"{order}: expected the cut {CUT}, got {meta['range_conflicts']}")
    claim(meta["missing"] == [],
          f"{order}: every number 1–9 is carried by some block, got missing {meta['missing']}")
    owner = {}
    for s in sections:
        for n in range(s["n"], s["to"] + 1):
            if n in owner:
                raise AssertionError(
                    f"{order}: §{n} is carried in §{owner[n]} and again in §{s['n']}")
            owner[n] = s["n"]
    return {"order": list(order), "blocks": len(sections),
            "section_5": by_n[5]["from"], "range_4": by_n[4]["to"],
            "range_7": by_n[7]["to"], "range_conflicts": meta["range_conflicts"]}


def main():
    with tempfile.TemporaryDirectory() as tmp:
        got = [check(("SYN-OWN", "SYN-RANGE"), tmp),
               check(("SYN-RANGE", "SYN-OWN"), tmp)]
        claim(got[0]["range_conflicts"] == got[1]["range_conflicts"],
              "the recorded cut must not depend on which copy is read first")
    print(json.dumps({"scanlib_range": got}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print("FAIL  " + str(e))
        sys.exit(1)
