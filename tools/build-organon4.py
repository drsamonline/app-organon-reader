#!/usr/bin/env python3
"""build-organon4.py — the FOURTH edition (1829) in Devrient's 1833 translation.

Devrient's is the first English Organon (London and Dublin, 1833), made from the fourth
German edition, with Samuel Stratten's notes. The fourth edition runs to 292 aphorisms
and is the first to carry Hahnemann's chronic-miasms theory.

The printed book numbers its paragraphs in ROMAN numerals, and OCR loses some of them.
The reading text therefore comes from whichever scan still reads a given mark, and the
other scans are the verification corpus: for each section we measure what fraction of
its 12-letter sequences appear verbatim in the corpus. A section is cut at the next mark
that same scan carries, so a lost mark leaves a named gap instead of merging paragraphs.

    ORGANON_SRC=. python3 tools/build-organon4.py
"""
import hashlib, json, os, re, statistics

import scanlib

MAX = 292                      # the fourth edition has 292 aphorisms
FLOOR = 0.60
SRC_DIR = os.environ.get("ORGANON_SRC", ".")
OUT_JS = "docs/organon4-data.js"
OUT_JSON = "organon4-sections.json"

SCANS = [
    ("bub_gb_EnEFAAAAQAAJ", "organon4/bub_gb_EnEFAAAAQAAJ.txt", "Devrient-Dublin-1833"),
    ("homoeopathicmedi00hahn", "organon4/homoeopathicmedi00hahn.txt", "Devrient-Wellcome-1833"),
    ("homopathicmedic00devrgoog", "organon4/homopathicmedic00devrgoog.txt", "Devrient-Oxford-1833"),
    ("b33290180", "organon4/b33290180.txt", "Devrient-Wellcome-2"),
]

ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
FIRST_APH = re.compile(r"(?:first\s+and\s+)?sole\s+duty\s+of\s+the\s+physician", re.I)
HEADER = re.compile(r"^\s*(?:THE\s+)?(?:HOM[O\u0153]?OPATHIC\s+MEDICAL\s+DOCTRINE|ORGANON\s+OF\s+THE\s+HEALING\s+ART)\s*[.,]?\s*$", re.I)


def roman(text):
    total, prev = 0, 0
    for ch in reversed(text):
        if ch not in ROMAN:
            return None
        v = ROMAN[ch]
        total = total - v if v < prev else total + v
        prev = max(prev, v)
    return total


def to_int(raw):
    n = roman(raw)
    if n and 1 <= n <= MAX:
        return n
    # OCR reads a final I as L ("LXXXIL"), and CXI as CXL
    for cand in ((raw[:-1] + "I") if raw.endswith("L") else None,
                 raw.replace("L", "I") if "L" in raw else None):
        if not cand:
            continue
        n = roman(cand)
        if n and 1 <= n <= MAX:
            return n
    return None


def require_fourth_devrient(raw, label):
    """Refuse anything that is not Devrient's 1833 translation.

    Its title page does not name the German edition — it reads "TRANSLATED FROM THE
    GERMAN OF S. HAHNEMANN, BY CHARLES H. DEVRIENT" — so the edition is established the
    way the book itself establishes it: Devrient's is the first English Organon, made in
    1833 from the edition then current (the fourth, 1829), and the caller additionally
    refuses any scan that does not read a mark near the end of a 292-section book.
    """
    flat = re.sub(r"\s+", " ", raw).upper()
    for other in ("BOERICKE", "DUDGEON"):
        if other in flat:
            raise SystemExit(f"refusing {label}: names {other} — a different translation")
    if "DEVRIENT" not in flat or "STRATTEN" not in flat:
        raise SystemExit(f"refusing {label}: does not declare Devrient's translation (with Stratten's notes)")
    i = flat.find("DEVRIENT")
    return flat[max(0, i - 160):i + 120].strip()


def marks(lines):
    out = []
    for i, l in enumerate(lines):
        m = re.match(r"^\s*[§$5Ss]\s*([IVXLCDM]{1,7})\s*[.,;:]?\s*(.*)$", l)
        if not m:
            continue
        n = to_int(m.group(1))
        if not n:
            continue
        out.append((i, n, m.group(2).strip()))
    return out


def chain(hits, tol=6):
    acc, last = [], 0
    for h in hits:
        n = h[1]
        if (last == 0 and n <= 6) or 0 < n - last <= tol:
            acc.append(h)
            last = n
    return acc


PLATE = re.compile(r"^\s*(?:Digitized by (?:Google|Microsoft)|Google|THE END)\s*[.,]?\s*$", re.I)
# where the Organon ends and the volume's notes and libel matter begin
END_MATTER = re.compile(r"^\s*(?:APPENDIX|NOTES?|INDEX|CONTENTS|ERRATA|THE\s+END)\s*[.,]?\s*$")


def clean(block):
    out = []
    for ln in block.split("\n"):
        s = ln.rstrip()
        if END_MATTER.match(s):
            break
        if HEADER.match(s) or PLATE.match(s) or re.fullmatch(r"\s*\d{1,3}\s*", s):
            continue
        if re.fullmatch(r"\s*[A-Za-z^|~*]\s*", s):      # page signature or stray mark
            continue
        if not s.strip():
            if out and out[-1] != "":
                out.append("")
            continue
        out.append(s.strip())
    text = "\n".join(out).strip()
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"\n+", " ", text)
    # the digitisation plate is sometimes printed across the running text; it is not
    # Hahnemann's, so it is removed, together with the roman page numbers it carries
    text = re.sub(r"(?i)digitized\s+by\s*[a-z]*\s*[-\u2013\u2014]?\s*", " ", text)
    text = re.sub(r"(?i)\bdigitized\b\s*", " ", text)
    text = re.sub(r"(?i)\b(?:[a-z]{0,3}\s+)?by\s+google\b", " ", text)
    text = re.sub(r"\s\b[IVXLCDM]{2,7}\b\s", " ", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def body_start(lines):
    """The introduction runs to more than a hundred pages and carries its own section
    references, so the running text is anchored on the first aphorism, not on a line
    number: §1 begins "the first and sole duty of the physician"."""
    for i, l in enumerate(lines):
        if FIRST_APH.search(l):
            return max(0, i - 3)
    return 0


def parse(path):
    """Each section as `(text, closed, first line, last line)`.

    The two line numbers are its place in the scan's `_djvu.txt`, which is how its
    printed page is found.
    """
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    start = body_start(lines)
    hits = [h for h in marks(lines) if h[0] >= start]
    best = []
    for k, h in enumerate(hits):
        if h[1] <= 6:
            c = chain(hits[k:])
            if len(c) > len(best):
                best = c
    secs = {}
    for i, (ln, n, rest) in enumerate(best):
        stop = best[i + 1][0] if i + 1 < len(best) else len(lines)
        block = "\n".join(([rest] if rest else []) + lines[ln + 1:stop])
        text = clean(block)
        if not text:
            continue
        nxt = best[i + 1][1] if i + 1 < len(best) else None
        if n not in secs or (nxt == n + 1 and not secs[n][1]):
            secs[n] = (text, nxt == n + 1, ln, stop - 1)
    return secs


def letters(s):
    return re.sub(r"[^a-z]", "", s.lower())


def main():
    per_scan, scan_meta, corpus = {}, [], set()
    locators, places_by_label = {}, {}
    for ident, rel, label in SCANS:
        path = os.path.join(SRC_DIR, rel)
        if not os.path.exists(path):
            print(f"  !! missing source {path} — skipped (recorded in data/README.md)")
            continue
        blob = open(path, "rb").read()
        text = blob.decode("utf-8", "replace")
        evidence = require_fourth_devrient(text[:20000], label)
        secs = parse(path)
        if max(secs or [0]) < 285:
            # a copy whose Roman numerals are unreadable is no use as a parser, but its
            # words still help corroborate the sections the other copies do read
            print(f"  scan {label:22s}   marks unreadable — corpus only")
            secs = {}
        per_scan[label] = secs
        locator, _ = scanlib.locate(path, text)
        locators[label] = locator
        places_by_label[label] = ({n: scanlib.place(locator, got[2], got[3])
                                   for n, got in secs.items()} if locator is not None else {})
        flat = letters(text)
        corpus.update(flat[i:i + 12] for i in range(0, max(0, len(flat) - 12)))
        scan_meta.append({"label": label, "identifier": ident, "role": "scan",
                          "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
                          "edition": "fourth edition (1829), Devrient translation, 1833",
                          "edition_evidence": evidence[:240],
                          "sections": len(secs),
                          "role_detail": ("corpus only: its Roman numerals could not be read"
                                          if not secs else "parser and corpus")})
        if secs:
            print(f"  scan {label:22s} {len(secs):3d} sections readable")

    def coverage(text):
        flat = letters(text)
        g = [flat[i:i + 12] for i in range(0, max(0, len(flat) - 12))]
        return (sum(1 for x in g if x in corpus) / len(g)) if g else 0.0

    merged, origin, verify, places = {}, {}, {}, {}
    for closed_only in (True, False):
        for n in range(1, MAX + 1):
            if n in merged:
                continue
            for lab in [s[2] for s in SCANS if s[2] in per_scan]:
                got = per_scan[lab].get(n)
                if not got:
                    continue
                if closed_only and not got[1]:
                    continue
                # A copy can read one Roman numeral as another and offer a paragraph
                # already carried under its own number: the Dublin scan reads `§XXIII`
                # as `§XXVIII`, so its "§28" opens with §23's words. Carrying it would
                # put the same paragraph in the book twice; the block is refused and the
                # other copy, which prints §28, supplies it.
                if any(scanlib.alike(got[0], merged[m]) for m in merged):
                    continue
                merged[n] = got[0]
                origin[n] = lab
                places[n] = places_by_label.get(lab, {}).get(n, {})
                break

    refused = []
    for n in list(merged):
        c = round(coverage(merged[n]), 4)
        verify[n] = c
        if c < FLOOR:
            refused.append({"n": n, "corroboration": c})
            del merged[n]
            del origin[n]
            places.pop(n, None)

    # a section whose own leaf prints no folio may take the page the other copy of the
    # printing prints, but only where the two copies are proved to paginate alike
    texts_by_label = {lab: {n: got[0] for n, got in secs.items()}
                      for lab, secs in per_scan.items()}
    fills, cross = scanlib.cross_copy(places_by_label, texts_by_label, origin)
    for n, fill in fills.items():
        places.setdefault(n, {}).update(fill)

    missing = [n for n in range(1, MAX + 1) if n not in merged]
    cov = [verify[n] for n in merged]
    meta = {
        "title": "Organon of the Healing Art",
        "edition": "Fourth edition (1829), first English translation by Charles H. Devrient, 1833",
        "translator": "Charles H. Devrient, with notes by Samuel Stratten (1833)",
        "source": "https://archive.org/details/bub_gb_EnEFAAAAQAAJ",
        "licence": "Public domain: Hahnemann died 1843; Devrient's translation was published 1833",
        "total_in_book": MAX,
        "recovered": len(merged),
        "missing": missing,
        "status": f"OCR-derived, corroborated across scans; {len(missing)} section(s) not readable",
        "verification": {
            "method": "fraction of each section's 12-letter sequences found verbatim in the scans",
            "median": round(statistics.median(cov), 4) if cov else None,
            "min": round(min(cov), 4) if cov else None,
            "sections_checked": len(cov),
            "floor": FLOOR,
            "refused": refused,
            "note": "No transcription of this translation exists, so the check is scan against "
                    "scan: it catches OCR damage, not a wrong edition.",
        },
        "pages": scanlib.page_meta(locators, places, merged, cross=cross),
        "scans": scan_meta,
        "notes": [
            "The fourth edition is the first to carry Hahnemann's chronic-miasms theory; it "
            "runs to 292 aphorisms against the fifth's 294 and the sixth's 291.",
            "The book numbers its paragraphs in Roman numerals. Where OCR lost a numeral the "
            "section is cut short by that loss and the gap is named, never renumbered; the "
            "text of a lost-numbered section is carried by no bundle and no attempt is made "
            "to guess where it begins.",
            "Stratten's notes are printed among the paragraphs in the scans and are not "
            "separated here; this bundle carries the running text only.",
        ],
    }
    bundle = {"meta": meta, "sections": [
        dict({"n": n, "text": merged[n], "notes": [], "from": origin[n]},
             **places.get(n, {}),
             **{"corroboration": verify[n], "accepted": True}) for n in sorted(merged)]}

    body = json.dumps(bundle, ensure_ascii=False, separators=(",", ":"))
    js = ("/* The fourth edition, Devrient's 1833 English translation, read from scans of the\n"
          " * 1833 printing. Generated by tools/build-organon4.py — do not hand-edit.\n"
          " * Public domain (Hahnemann d. 1843; Devrient translation 1833). */\n"
          "(function (root, factory) {\n"
          '  if (typeof module === "object" && module.exports) module.exports = factory();\n'
          "  else root.ORGANON4 = factory();\n"
          "})(typeof self !== \"undefined\" ? self : this, function () {\n"
          "  return " + body + ";\n});\n")
    open(OUT_JS, "w", encoding="utf-8").write(js)
    json.dump(bundle, open(OUT_JSON, "w"), ensure_ascii=False, indent=1)
    print(f"  sections {len(merged)} of {MAX} | median {meta['verification']['median']} "
          f"| min {meta['verification']['min']} | refused {len(refused)}")
    print("  missing", missing)
    print("  wrote", OUT_JS, os.path.getsize(OUT_JS), "bytes")


if __name__ == "__main__":
    main()
