#!/usr/bin/env python3
"""pages.py — which printed page a block came from.

The build reads a scan's `_djvu.txt`, which is one flat stream of lines: it carries no
page breaks, so a block's place in the book was not recorded anywhere. The scan's
`_djvu.xml` does carry them — one `<OBJECT>` per leaf — and the printed page number is
usually read in the leaf's first line (`31`, `111`, `RATIONAL ART OF HEALING 25`). So the
two are used together: the xml supplies the leaf each `_djvu.txt` line falls on, and the
leaf supplies the number the page prints.

Nothing here guesses. A leaf whose own folio cannot be read is *unreadable*: it is
reported by leaf index and no page number is invented for it, and a block that begins
there carries no page. A leaf whose folio disagrees with the numbering its neighbours
establish is treated the same way.

    import pages
    loc = pages.Locator(xml_path, txt_lines)
    loc.leaf_of(line_index), loc.printed(leaf)
"""
import bisect
import re
import xml.etree.ElementTree as ET

FOLIO = re.compile(r"^(\d{1,3})$")
TOKEN = re.compile(r"^([0-9A-Za-z|!~?]{1,4})$")
# OCR's letter-for-digit confusions, as `tools/scanlib.py` applies them inside a mark
DIGITS = {"l": "1", "I": "1", "|": "1", "i": "1", "!": "1", "O": "0", "o": "0",
          "Q": "0", "S": "5", "s": "5", "B": "8", "g": "9", "~": "7", "Z": "2"}
# a folio set beside a running head: `RATIONAL ART OF HEALING 25`, `25 ORGANON ...`
TAIL = re.compile(r"^(?P<head>[^0-9]{3,}?)\s+(?P<n>\d{1,3})$")
HEAD = re.compile(r"^(?P<n>\d{1,3})\s+(?P<head>[^0-9]{3,})$")


def norm(s):
    """Letters and digits only, so whitespace and line breaks cannot shift the match."""
    return re.sub(r"[^0-9a-zà-ÿäöüßæœ]", "", s.lower())


def page_lines(xml_path):
    """The scan's leaves, each a list of its lines, in reading order."""
    root = ET.parse(xml_path).getroot()
    out = []
    for obj in root.iter("OBJECT"):
        lines = []
        for ln in obj.iter("LINE"):
            words = [(w.text or "").strip() for w in ln.iter("WORD")]
            lines.append(re.sub(r"\s+", " ", " ".join(w for w in words if w)).strip())
        out.append(lines)
    return out


def number(tok):
    """A folio as the page prints it, read through OCR's own confusions, or None.

    The mapping is the one `tools/scanlib.py` already applies to a printed number (`i8`
    for 18, `S0` for 50); it is confined to a short token that carries a real digit, so
    a word cannot become a page number.
    """
    if len(tok) > 4 or not any(c.isdigit() for c in tok):
        return None
    value = "".join(DIGITS.get(c, c) for c in tok)
    return int(value) if value.isdigit() else None


def folio_candidates(lines):
    """The numbers this leaf's own top and bottom lines print, best first.

    A folio is the page number the printer set at the head or foot of the leaf. It is
    read only where the line that carries it is nothing else — a bare number, or a
    number beside a running head (`RATIONAL ART OF HEALING 25`). A number that opens a
    paragraph (`31. Die ältere ...`) is the paragraph's mark, not the page's, and is not
    taken. The head of the leaf is read before its foot, because in these printings the
    folio sits at the top; the foot is tried only where the head prints none.
    """
    top = [l for l in lines[:2] if l.strip()]
    bot = [l for l in lines[-2:] if l.strip()]
    out = []
    for line in top + bot:
        s = line.strip()
        m = FOLIO.match(s) or TOKEN.match(s)
        if m:
            n = number(m.group(1))
            if n is not None:
                out.append(n)
            continue
        # a folio beside a running head, in capitals, with the number at either end
        for pat in (TAIL, HEAD):
            m = pat.match(s)
            if m and sum(c.isupper() for c in m.group("head")) >= 3:
                out.append(int(m.group("n")))
                break
    return out


NEAR = 2      # a leaf this close, printing the predicted number, is proof enough
FAR = 6       # a leaf this far out must have a second one saying the same


def read_folios(pages):
    """The printed page number of every leaf, or None where the leaf does not print one.

    The book numbers its pages one at a time, so a number a leaf prints must be the number
    a leaf near it implies: the difference between a leaf's index and the number it
    prints stays the same from leaf to leaf. One leaf's OCR can turn 22 into 23, which
    looks perfectly plausible on its own; but then it disagrees with the leaf beside it,
    and that is what settles it.

    A number the leaf prints is believed on one of three proofs, and on nothing else:

    * **a neighbour** within `NEAR` leaves prints the number that difference predicts —
      the two pages run on from one another;
    * **two neighbours** within `FAR` do, so a stretch of unreadable leaves between them
      does not hide the numbering — one witness is not enough that far out, because a
      single coincidental reading could stand alone;
    * **a bracket**: a leaf prints the number its gap predicts, and on both sides of it
      lies a leaf already believed on the same gap, with no leaf of a different gap
      between them. The two anchors prove the numbering did not shift across the span,
      so the page the leaf itself prints is the page it carries.

    A thread that only reaches one way is *not* proof, however consistent: confirming a
    leaf because the last anchor still fits it is reading the page off a leaf index,
    which is the inference this record exists to avoid. Those leaves stay unreadable.

    The wider proofs must also *fit the run already read*: the page has to be greater
    than the nearest page believed before the leaf and smaller than the nearest one
    believed after it. A scan that prints two incompatible numberings — the 1819 reading
    copy prints 52-59 on one stretch of leaves and 41-55 on the next — would otherwise
    let a bracket unseat pages that were already recorded. A page is added, never
    withdrawn; where the two proofs disagree the leaf keeps the page it had.

    Finally the pages must run forward. A leaf whose number is not greater than the last
    one read cannot be showing its own page number, whatever else it might be.
    """
    cands = [folio_candidates(p) for p in pages]
    total = len(pages)
    out = [None] * total

    def shows(j, gap):
        return any(m - j == gap for m in cands[j])

    def fits(i, n):
        """True where this page sits inside the run the neighbours already prove."""
        before = next((out[j] for j in range(i - 1, -1, -1) if out[j] is not None), None)
        after = next((out[j] for j in range(i + 1, total) if out[j] is not None), None)
        return (before is None or n > before) and (after is None or n < after)

    # a neighbour within NEAR leaves: the page runs on from the one beside it
    for i, got in enumerate(cands):
        for n in dict.fromkeys(got):
            # a page number larger than the number of leaves is not this book's folio
            # (it is a date, a price or a plate's own number, read as a page)
            if not 1 <= n <= total:
                continue
            gap = n - i
            if any(shows(j, gap) for j in range(max(0, i - NEAR),
                                                min(total, i + NEAR + 1)) if j != i):
                out[i] = n
                break

    # two neighbours within FAR: a stretch of unreadable leaves does not hide the run
    for i, got in enumerate(cands):
        if out[i] is not None:
            continue
        for n in dict.fromkeys(got):
            if not 1 <= n <= total:
                continue
            gap = n - i
            far = [j for j in range(max(0, i - FAR), min(total, i + FAR + 1))
                   if j != i and shows(j, gap)]
            if len(far) >= 2 and fits(i, n):
                out[i] = n
                break

    # a bracket: a believed anchor on both sides of the gap that agrees with this leaf
    changed = True
    while changed:
        changed = False
        for i, got in enumerate(cands):
            if out[i] is not None:
                continue
            for n in dict.fromkeys(got):
                if not 1 <= n <= total or not fits(i, n):
                    continue
                gap = n - i
                left = next((j for j in range(i - 1, -1, -1)
                             if out[j] is not None and out[j] - j == gap), None)
                right = next((j for j in range(i + 1, total)
                              if out[j] is not None and out[j] - j == gap), None)
                if left is None or right is None:
                    continue
                # a believed leaf of another gap between the anchors means the leaf
                # numbering shifted there, and the bracket spans two books
                if any(out[j] is not None and out[j] - j != gap
                       for j in range(left + 1, right)):
                    continue
                out[i] = n
                changed = True
                break

    last = None
    for i, n in enumerate(out):
        if n is None:
            continue
        if last is not None and n <= last:
            out[i] = None
        else:
            last = n
    return out


class Locator:
    """Where each line of a scan's `_djvu.txt` sits, and what page that leaf prints.

    The two files are the same OCR of the same leaves, so their text is the same text:
    the leaf of a line is found by matching the cumulative length of the two streams,
    which cannot drift without the text having changed. A mismatch anywhere is reported
    rather than smoothed over.
    """

    def __init__(self, xml_path, lines):
        self.pages = page_lines(xml_path)
        self.printed = read_folios(self.pages)
        self.cum_page, total = [], 0
        for p in self.pages:
            total += len(norm("\n".join(p)))
            self.cum_page.append(total)
        self.cum_line, total = [], 0
        for ln in lines:
            total += len(norm(ln))
            self.cum_line.append(total)
        self.leaves = len(self.pages)
        top = max(0, self.leaves - 1)
        self.leaf = []
        before = 0
        for c in self.cum_line:
            # the leaf that holds the point where this line begins: the first leaf whose
            # own text has not yet ended there. A line that begins exactly where a leaf
            # begins belongs to that leaf, not to the one before it.
            self.leaf.append(min(bisect.bisect_right(self.cum_page, before), top))
            before = c

    def leaf_of(self, line_index):
        if not self.leaf:
            return None
        i = max(0, min(line_index, len(self.leaf) - 1))
        return self.leaf[i]

    def page_of(self, line_index):
        """The printed page a line begins on, or None where the leaf prints none."""
        leaf = self.leaf_of(line_index)
        return None if leaf is None else self.printed[leaf]

    def span(self, first_line, last_line):
        """The leaves a block runs over, and the pages they print.

        Returns `(leaf, leaf_to, page, page_to)`; `leaf_to`/`page_to` are None when the
        block sits on one leaf, and `page`/`page_to` are None where the leaf prints no
        readable number.
        """
        a, b = self.leaf_of(first_line), self.leaf_of(last_line)
        if a is None:
            return None, None, None, None
        pa, pb = self.printed[a], self.printed[b]
        return (a + 1, (b + 1) if b != a else None,
                pa, pb if (b != a and pb != pa) else None)

    def agree(self, lines):
        """How many leaf boundaries land on that leaf's own first line.

        This is the check that the `_djvu.txt` and `_djvu.xml` are the same reading of
        the same leaves: at every leaf change, the first line of the text there must be
        the first line the xml gives that leaf. A build reports the count, so a scan
        whose two files disagree is visible rather than quietly mis-paged.
        """
        same = 0
        for i in range(1, len(self.leaf)):
            if self.leaf[i] == self.leaf[i - 1]:
                continue
            page = self.pages[self.leaf[i]]
            first = next((x for x in page if x.strip()), "")
            j = i
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and norm(first)[:20] and \
                    norm(first)[:20] == norm(lines[j])[:20]:
                same += 1
        return same


def main():
    import os
    import sys
    ident, txt = sys.argv[1], sys.argv[2]
    xml = sys.argv[3] if len(sys.argv) > 3 else os.path.join(
        os.environ.get("ORGANON_SRC", "."), ident + ".xml")
    lines = open(txt, encoding="utf-8", errors="replace").read().splitlines()
    loc = Locator(xml, lines)
    print(f"{ident}: {loc.leaves} leaves, {len(lines)} lines")
    unread = [i + 1 for i, p in enumerate(loc.printed) if p is None]
    print(f"  leaves that print no readable page number: {len(unread)} {unread[:20]}")
    for i in range(len(lines)):
        if i and loc.leaf[i] != loc.leaf[i - 1]:
            lo = loc.leaf[i]
            print(f"  line {i:5d} -> leaf {lo + 1:3d}  page {loc.printed[lo]}"
                  f"  | {lines[i][:40]!r}")


if __name__ == "__main__":
    main()
