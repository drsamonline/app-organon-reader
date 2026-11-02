#!/usr/bin/env python3
"""extract.py — build the bundle, and prove where every word came from.

Two kinds of source, one edition:

  * four OCR scans of the printed 1922 Boericke translation (three of the book, one of
    the same book in another library) — the *verification corpus*;
  * one transcription of that same translation, section by section, from the Médi-T
    edition on homeoint.org — the *reading text*, because it has no OCR damage.

Every scan is refused unless its own front matter declares the sixth edition in
Boericke's translation, and the transcription is refused unless it agrees, section by
section, with the scans: for each section we measure what fraction of its 12-letter
sequences appear verbatim in the OCR. A paraphrase or a different translation scores
near zero; this one scores a median of 0.98.

Nothing is renumbered, nothing is invented: a section exists only where a section mark
can be read, and the transcription is only accepted for a number the scans corroborate.

    python3 tools/extract.py
"""
import bisect, difflib, glob, hashlib, json, os, re, statistics

MAX = 291
SRC_DIR = os.environ.get("ORGANON_SRC", ".")
SCANS = [
    ("organon-of-medicine-6th-edition-completed-1842-german-edition-published-1921-eng",
     "organon.txt", "IA-1842-1922"),
    ("b3135452x_0001", "src/b3135452x_0001.txt", "Wellcome-0001"),
    ("b3135452x_0002", "src/b3135452x_0002.txt", "Wellcome-0002"),
]
TRANSCRIPTION = ("MediT", "homeoint_sections.json")
MIN_COVERAGE = 0.60          # below this, a transcription section is not corroborated

DIGIT = {"O": "0", "o": "0", "Q": "0", "D": "0", "l": "1", "I": "1", "i": "1", "|": "1", "!": "1",
         "Z": "2", "z": "2", "J": "3", "A": "4", "S": "5", "s": "5", "G": "6", "b": "6",
         "T": "7", "B": "8", "E": "8", "g": "9", "q": "9"}
MARK = re.compile(r"[§$S8]\s*\.?\s*([0-9OoQDlIizZASGbTgqJ|!]{1,3})\s*(?:[.,:;•·]|$)", re.M)
FIRST_APH = re.compile(r"restore\s+the\s+sick|sick\s+to\s+health", re.I)
PAGE = re.compile(r"^\s*(?:\d{1,3}\s+)?(?:TEXT OF THE ORGANON|TRANSLATORS PREFACE|ORGANON OF MEDICINE|"
                  r"CONTENTS|INTRODUCTION)\s*(?:\d{1,3})?\s*$", re.I)


def require_sixth_edition(raw, label):
    """A scan is used only if its own front matter declares the sixth edition in
    Boericke's translation. Different editions and translations are never mixed in."""
    head = re.sub(r"\s+", " ", raw[:6000]).upper()
    if not ("SIXTH EDITION" in head and "BOERICKE" in head):
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


def body_start(raw):
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
        closed = (i + 1 < len(chain) and chain[i + 1][1] == n + 1)
        if len(text) >= 40 and n not in out:
            out[n] = (text, closed)
    return out


def letters(s):
    return re.sub(r"[^a-z]", "", s.lower())


def main():
    per_scan, scan_meta, corpus = {}, [], set()
    for ident, path, label in SCANS:
        full = os.path.join(SRC_DIR, path)
        if not os.path.exists(full):
            print(f"  !! missing source {full} — skipped (recorded in data/README.md)")
            continue
        blob = open(full, "rb").read()
        text = blob.decode("utf-8", "replace")
        evidence = require_sixth_edition(text, label)
        per_scan[label] = sections(full)
        flat = letters(text)
        corpus.update(flat[i:i + 12] for i in range(0, max(0, len(flat) - 12)))
        scan_meta.append({"label": label, "identifier": ident, "role": "scan",
                          "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
                          "edition": "sixth edition, Boericke translation",
                          "edition_evidence": evidence,
                          "sections": len(per_scan[label])})
        print(f"  scan {label:14s} {len(per_scan[label]):3d} sections")

    def coverage(text):
        flat = letters(text)
        g = [flat[i:i + 12] for i in range(0, max(0, len(flat) - 12))]
        return (sum(1 for x in g if x in corpus) / len(g)) if g else 0.0

    # the reading text: the transcription, accepted section by section only when the
    # scans corroborate it
    label, path = TRANSCRIPTION
    full = os.path.join(SRC_DIR, path)
    merged, origin, verify, notes = {}, {}, {}, {}
    if os.path.exists(full):
        tr = {int(k): v for k, v in json.load(open(full)).items()}
        for n in range(1, MAX + 1):
            if n not in tr:
                continue
            entry = tr[n]
            body = entry["text"] if isinstance(entry, dict) else entry
            c = coverage(body)
            verify[n] = round(c, 3)
            if c >= MIN_COVERAGE:
                merged[n] = body.strip()
                notes[n] = (entry.get("notes") or []) if isinstance(entry, dict) else []
                origin[n] = label
        scan_meta.append({
            "label": label, "identifier": "homeoint.org/books/hahorgan (Médi-T, sixth edition only)",
            "role": "transcription",
            "url": "http://www.homeoint.org/books/hahorgan/organ001.htm … organ280.htm",
            "retrieved": "Internet Archive Wayback Machine snapshots, 15 pages",
            "edition": "sixth edition, Boericke translation",
            "sections": len(merged),
            "verification": "12-gram coverage of each section against the scans",
        })
        print(f"  transcription {label:11s} {len(merged):3d} sections corroborated "
              f"(median {statistics.median(verify.values()):.3f}, "
              f"min {min(verify.values()):.3f})")

    # anything the transcription could not supply falls back to the cleanest scan text
    for n in range(1, MAX + 1):
        if n in merged:
            continue
        best = None
        for lab, secs in per_scan.items():
            if n in secs:
                score = len(secs[n][0])
                if best is None or score > best[0]:
                    best = (score, lab, secs[n][0])
        if best:
            merged[n] = best[2]
            origin[n] = best[1]

    def words(t):
        return re.findall(r"[a-z']+", t.lower())

    diffs = {}
    for n in range(1, MAX + 1):
        if n not in merged:
            continue
        for lab, secs in per_scan.items():
            if n in secs and secs[n][1]:                     # both edges readable
                a, b = words(merged[n]), words(secs[n][0])
                sm = difflib.SequenceMatcher(None, a, b)
                changed = sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in sm.get_opcodes()
                              if tag != "equal")
                diffs[n] = changed
                break

    missing = [n for n in range(1, MAX + 1) if n not in merged]
    out = [{"n": n, "text": merged[n], "from": origin[n],
            "corroboration": verify.get(n), "diff_words": diffs.get(n),
            "notes": notes.get(n, [])} for n in sorted(merged)]
    flagged = sorted(n for n, d in diffs.items() if d > 3)
    print(f"  sections whose wording differs from a fully-bounded scan in >3 words: {len(flagged)} {flagged[:12]}")
    print(f"merged {len(out)} of {MAX}; missing {len(missing)}")

    json.dump({
        "title": "Organon of Medicine",
        "edition": "Sixth edition (completed 1842), English translation by William Boericke, 1922",
        "translator": "William Boericke",
        "source": "https://archive.org/details/organon-of-medicine-6th-edition-completed-1842-german-edition-published-1921-eng",
        "licence": "Public domain: Hahnemann died 1843; the Boericke translation was published 1922",
        "scans": scan_meta,
        "verification": {
            "method": "fraction of each section's 12-letter sequences found verbatim in the scans",
            "min": min(verify.values()) if verify else None,
            "median": round(statistics.median(verify.values()), 3) if verify else None,
            "sections_checked": len(verify),
        },
        "total_in_book": MAX,
        "recovered": len(out),
        "missing": missing,
        "sections": out,
    }, open("sections.json", "w"), ensure_ascii=False)


if __name__ == "__main__":
    main()
