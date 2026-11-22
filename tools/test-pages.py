#!/usr/bin/env python3
"""test-pages.py — the folio rules, on synthetic leaves where the answer is known.

`tools/pages.py` decides which printed page a leaf carries. The scans can show that a rule
works on real leaves, but they cannot show what it *refuses*: a page no evidence supports
never appears in the output. These leaves are therefore made up, one page per leaf, so the
expected answer is arithmetic and every refusal is a case that must stay unreadable.

    python3 tools/test-pages.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pages  # noqa: E402

FAILED = []


def book(printed):
    """Leaves from a list of folios (None where the leaf prints none)."""
    return [[str(p), "der Text dieser Seite"] if p is not None else ["der Text"]
            for p in printed]


def check(name, printed, want):
    got = pages.read_folios(book(printed))
    if got == want:
        print(f"PASS  {name}")
    else:
        print(f"FAIL  {name}\n      wanted {want}\n      got    {got}")
        FAILED.append(name)


N = None

check("a page is read where the leaf beside it prints the next one",
      [N, 2, N, 4, N], [N, 2, N, 4, N])

check("one witness four leaves away proves nothing",
      [N, N, N, N, 5, N, N, N, N], [N] * 9)

check("two witnesses six leaves away bridge the stretch",
      [N, 2, N, N, 5, N, N, 8, N], [N, 2, N, N, 5, N, N, 8, N])

# anchors at both ends of a long gap: too far for either witness rule, but bracketed
check("a leaf between two anchors of the same gap is confirmed",
      [1, 2, 3] + [N] * 16 + [20] + [N] * 7 + [28, 29, 30],
      [1, 2, 3] + [N] * 16 + [20] + [N] * 7 + [28, 29, 30])

# the run reaches the leaf, but only one witness does: still an inferred page
check("a page only one far witness supports is refused",
      [20, 21, N, N, N, N, N, 27] + [N] * 28, [20, 21] + [N] * 34)

# a second numbering in the same scan: locally consistent, but the book cannot go back
check("a page that would run the book backwards is refused",
      [1, 2, 3, 2], [1, 2, 3, N])

# a plate's number, a date or a price is not this book's folio
check("a number past the last leaf is refused",
      [2, 3, 99, 5, 6, N], [2, 3, N, 5, 6, N])

# OCR's letter-for-digit confusions are read, then judged like any other number
check("a mangled folio is read and then confirmed",
      [N, "l2", N, "l4", N] + [N] * 9, [N, 12, N, 14] + [N] * 10)

# a paragraph mark that opens the line is the paragraph's number, not the page's
check("a paragraph number that opens the text is not a page",
      ["31. Die aeltere Heilkunst", "Text", "Text", "32. Fortsetzung"], [N, N, N, N])

if FAILED:
    print(f"\n{len(FAILED)} failed")
    raise SystemExit(1)
print("\nall folio rules hold")
