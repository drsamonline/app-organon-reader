#!/usr/bin/env python3
"""extract.py — build the bundle from EVERY readable scan of the same translation.

Why more than one scan: OCR destroys a section mark here and there, and it does not
destroy the same one twice. Three independent scans of the 1922 Boericke translation
yield 168 / 169 / 160 sections on their own, and 256 of the book's 291 between them.

The rules, unchanged:
  * a section exists only where a section mark can be READ in at least one scan;
  * the mark must move forward through the book (longest increasing run), so a stray
    page number cannot become a section;
  * numbers are never invented and never renumbered — whatever no scan can read is
    listed as missing, with the reason;
  * when two scans both carry a section, the cleaner text wins, and every section
    records which scan it came from so the choice can be checked.

    python3 tools/extract.py        # reads SOURCES (see data/README.md), writes sections.json
"""
import bisect, hashlib, json, os, re, sys

MAX = 291
SRC_DIR = os.environ.get("ORGANON_SRC", ".")
SOURCES = [
    # id, file, short label
    ("organon-of-medicine-6th-edition-completed-1842-german-edition-published-1921-eng",
     "organon.txt", "IA-1842-1922"),
    ("b3135452x_0001", "src/b3135452x_0001.txt", "Wellcome-0001"),
    ("b3135452x_0002", "src/b3135452x_0002.txt", "Wellcome-0002"),
    # Only scans that declare the SIXTH edition in Boericke's translation are accepted.
    # The Dudgeon fifth edition and the 1913 "rational art of healing" are a different
    # translation and are refused by require_sixth_edition() — their wording cannot be
    # presented as Boericke's.
]

# OCR's favourite digit confusions, applied ONLY inside a section mark
DIGIT = {"O": "0", "o": "0", "Q": "0", "D": "0", "l": "1", "I": "1", "i": "1", "|": "1", "!": "1",
         "Z": "2", "z": "2", "J": "3", "A": "4", "S": "5", "s": "5", "G": "6", "b": "6",
         "T": "7", "B": "8", "E": "8", "g": "9", "q": "9"}
MARK = re.compile(r"[§$S8]\s*\.?\s*([0-9OoQDlIizZASGbTgqJ|!]{1,3})\s*(?:[.,:;•·]|$)", re.M)
FIRST_APH = re.compile(r"restore\s+the\s+sick|sick\s+to\s+health", re.I)
PAGE = re.compile(r"^\s*(?:\d{1,3}\s+)?(?:TEXT OF THE ORGANON|TRANSLATORS PREFACE|ORGANON OF MEDICINE|"
                  r"CONTENTS|INTRODUCTION)\s*(?:\d{1,3})?\s*$", re.I)


def require_sixth_edition(raw, label):
    """A scan is used ONLY if it says, in its own front matter, that it is the sixth
    edition in Boericke's translation. Different editions and different translations
    are never mixed in — their wording is not interchangeable, so a scan that cannot
    identify itself is refused rather than merged.
    """
    head = re.sub(r"\s+", " ", raw[:6000]).upper()
    ok = ("SIXTH EDITION" in head) and ("BOERicke".upper() in head)
    if not ok:
        raise SystemExit(f"refusing scan {label}: its front matter does not declare the "
                         f"sixth edition in Boericke's translation")
    i = head.find("SIXTH EDITION")
    return head[max(0, i - 80):i + 160].strip()


def marks(raw):
    out = []
    for m in MARK.finditer(raw):
        num = "".join(DIGIT.get(c, c) for c in m.group(1))
        if num.isdigit() and 1 <= int(num) <= MAX:
            out.append((m.start(), int(num), m.end()))
    out.sort()
    return out


def increasing(cands):
    """The longest run of marks whose numbers go up — the book's own order."""
    tails, idx, prev = [], [], [-1] * len(cands)
    for i, (_s, n, _e) in enumerate(cands):
        j = bisect.bisect_left(tails, n)
        if j == len(tails):
            tails.append(n); idx.append(i)
        else:
            tails[j] = n; idx[j] = i
        prev[i] = idx[j - 1] if j > 0 else -1
    chain, k = [], idx[-1]
    while k != -1:
        chain.append(k); k = prev[k]
    chain.reverse()
    return [cands[i] for i in chain]


def clean(block):
    out = []
    for ln in block.split("\n"):
        s = ln.rstrip()
        if PAGE.match(s) or re.fullmatch(r"\s*\d{1,3}\s*", s):
            continue
        if not s.strip():
            if out and out[-1] != "":
                out.append("")
            continue
        out.append(s.strip())
    text = "\n".join(out).strip()
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"\n+", " ", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def quality(text):
    """How much of this looks like prose rather than OCR debris. Higher is better."""
    tokens = text.split()
    if not tokens:
        return 0.0
    good = sum(1 for t in tokens if re.fullmatch(r"[A-Za-z][A-Za-z'’-]{2,}", t))
    debris = text.count("|") + text.count("~") + text.count("$") + text.count("©")
    return good / len(tokens) - debris / max(1, len(text)) * 100


def body_start(raw):
    """The mark that introduces the first aphorism.

    The front matter contains a synopsis that numbers sections in its own style, so the
    anchor is the first aphorism's own closing words and the mark is the nearest one
    before them. Everything before this point is front matter and is not searched.
    """
    hit = FIRST_APH.search(raw)
    if not hit:
        return 0
    before = [m for m in MARK.finditer(raw, max(0, hit.start() - 800), hit.start())]
    return before[-1].start() if before else hit.start()


def sections(path):
    raw = open(path, encoding="utf-8", errors="replace").read()
    start = body_start(raw)
    chain = increasing([m for m in marks(raw) if m[0] >= start])
    out = {}
    for i, (_s, n, e) in enumerate(chain):
        stop = chain[i + 1][0] if i + 1 < len(chain) else len(raw)
        text = clean(raw[e:stop])
        if len(text) >= 40 and n not in out:
            out[n] = {"text": text,
                      "closed": (i + 1 < len(chain) and chain[i + 1][1] == n + 1)}
    return out


def main():
    per_source, meta = {}, []
    for ident, path, label in SOURCES:
        full = os.path.join(SRC_DIR, path)
        if not os.path.exists(full):
            print(f"  !! missing source {full} — skipped (recorded in data/README.md)")
            continue
        blob = open(full, "rb").read()
        text = blob.decode("utf-8", "replace")
        evidence = require_sixth_edition(text, label)      # refuses anything else
        per_source[label] = sections(full)
        meta.append({"label": label, "identifier": ident, "bytes": len(blob),
                     "sha256": hashlib.sha256(blob).hexdigest(),
                     "edition": "sixth edition, Boericke translation",
                     "edition_evidence": evidence,
                     "sections": len(per_source[label])})
        print(f"  {label:14s} {len(per_source[label]):3d} sections from {path}")

    merged, origin = {}, {}
    for n in range(1, MAX + 1):
        best = None
        for label, secs in per_source.items():
            if n in secs:
                entry = secs[n]
                # a section whose NEXT mark is readable has both edges, so it cannot
                # run into the next section's text: prefer those, then the cleanest text
                q = quality(entry["text"]) + (0.5 if entry["closed"] else 0.0)
                if best is None or q > best[0]:
                    best = (q, label, entry["text"])
        if best:
            merged[n] = best[2]
            origin[n] = best[1]

    missing = [n for n in range(1, MAX + 1) if n not in merged]
    sections_out = [{"n": n, "text": merged[n], "from": origin[n]} for n in sorted(merged)]
    print(f"merged {len(sections_out)} of {MAX}; missing {len(missing)}: {missing}")

    json.dump({
        "title": "Organon of Medicine",
        "edition": "Sixth edition (completed 1842), English translation by William Boericke, 1922",
        "translator": "William Boericke",
        "source": "https://archive.org/details/organon-of-medicine-6th-edition-completed-1842-german-edition-published-1921-eng",
        "licence": "Public domain: Hahnemann died 1843; the Boericke translation was published 1922",
        "scans": meta,
        "total_in_book": MAX,
        "recovered": len(sections_out),
        "missing": missing,
        "sections": sections_out,
    }, open("sections.json", "w"), ensure_ascii=False)


if __name__ == "__main__":
    main()
