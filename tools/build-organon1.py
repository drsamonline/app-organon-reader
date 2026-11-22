#!/usr/bin/env python3
"""build-organon1.py — the FIRST edition (1810) in Wheeler's 1913 translation.

Editions 2 and 3 were never translated into English; the first and the fourth were, so
those are the two that can be added. Wheeler's is the only English translation of the
first edition (Everyman's Library, 1913).

There is no transcription of this translation, so the reading text is one OCR scan and
the other scans are the verification corpus: for each section we measure what fraction
of its 12-letter sequences appear verbatim in the other scans. A section is carried only
where a section mark can be read, and its text is cut at the next mark that scan itself
carries, so a lost mark never lets one aphorism run into the next.

    ORGANON_SRC=. python3 tools/build-organon1.py
"""
import hashlib, json, os, re, statistics

import scanlib

MAX = 271                      # the first edition has 271 aphorisms
FLOOR = 0.60
SRC_DIR = os.environ.get("ORGANON_SRC", ".")
OUT_JS = "docs/organon1-data.js"
OUT_JSON = "organon1-sections.json"

SCANS = [
    ("organonofrationa00hahn", "organon1/wheeler.txt", "Wheeler-1913"),
    ("b24877529", "organon1/b24877529.txt", "Wellcome-1913"),
]

HEADING = re.compile(r"RATIONAL\s+ART\s+OF\s+HEAL")
HEADER = re.compile(r"^\s*\d{0,3}\s*(?:ORGANON|RATIONAL|THE\s+RATIONAL)\b")
PLATE = re.compile(r"^\s*(?:Digitized by (?:Google|Microsoft)|Google|THE END)\s*[.,]?\s*$", re.I)
# where the Organon ends and the volume's other matter begins
# Case-sensitive and uppercase on purpose: Wheeler prints translator's notes in the
# running text, and a case-insensitive "note" would cut an aphorism at its own note.
END_MATTER = re.compile(r"^\s*(?:PART\s+II|PREFATORY\s+NOTE|AESCULAPIUS\s+IN\s+THE\s+BALANCE|"
                        r"PROTECTION\s+AGAINST|PLANS\s+FOR|SUGGESTIONS\s+FOR|APPENDIX|INDEX|"
                        r"CONTENTS|ERRATA|Richard\s+Clay|DO\s+NOT\s+REMOVE|Boston\s+University\s+Libraries)\b")


def require_first_wheeler(raw, label):
    """Refuse a scan that is not the first edition in Wheeler's translation. Dudgeon's
    name is *not* disqualifying here: Part II of this volume is his translation of four
    of Hahnemann's essays. The guard keys on the Organon's own translator and edition."""
    flat = re.sub(r"\s+", " ", raw).upper()
    for other in ("WILLIAM BOERICKE", "BOERICKE'S TRANSLATION", "DEVRIENT"):
        if other in flat:
            raise SystemExit(f"refusing {label}: {other} — a different edition or translation")
    m = re.search(r"TRANSLATED\s+FROM\s+THE\s+FIRST\s+EDITION", flat)
    if not m or "WHEELER" not in flat:
        raise SystemExit(f"refusing {label}: does not declare Wheeler's translation of the first edition")
    return flat[max(0, m.start() - 60):m.start() + 160].strip()


def body_start(lines):
    """The running text begins after the book's own heading. That heading is printed once
    as a title and again, broken over two lines, above §1: take the last one before the
    first section mark."""
    seen = [i for i, l in enumerate(lines) if HEADING.search(l) and i > 900]
    if not seen:
        return 0
    first_mark = marks(lines, allow_inline=True)
    first_mark = first_mark[0][0] if first_mark else len(lines)
    before = [i for i in seen if i < first_mark]
    return before[-1] if before else seen[0]


def marks(lines, allow_inline):
    """Section numbers: a bare number, or (in the noisier scan) a number that shares its
    line with the first word of the section. Running heads are not marks."""
    out = []
    for i, l in enumerate(lines):
        s = l.strip()
        if not s or HEADER.match(s):
            continue
        m = re.fullmatch(r"(\d{1,3})", s) if not allow_inline else \
            re.match(r"^(\d{1,3})(?:\s*$|\s+(?=[A-Za-z\"'(]))", s)
        if not m:
            continue
        n = int(m.group(1))
        if not 1 <= n <= MAX:
            continue
        # a mark is followed by prose, not by another number or a running head
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        nxt = lines[j].strip() if j < len(lines) else ""
        if len(nxt) < 20 or HEADER.match(nxt) or re.fullmatch(r"\d{1,3}", nxt):
            continue
        out.append((i, n, s[m.end(1):].strip()))
    return out


def chain(hits, tol=4):
    """Keep a forward-moving run, so a page number cannot become an aphorism."""
    acc, last = [], 0
    for h in hits:
        n = h[1]
        if (last == 0 and n <= 2) or 0 < n - last <= tol:
            acc.append(h)
            last = n
    return acc


def clean(block):
    out = []
    for ln in block.split("\n"):
        s = ln.rstrip()
        if END_MATTER.match(s):
            break
        if HEADER.match(s.strip()) or PLATE.match(s) or re.fullmatch(r"\s*\d{1,3}\s*", s):
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
    return re.sub(r"\s{2,}", " ", text).strip()


def parse(path):
    """Returns (sections read from a mark, §1 implied by position). §1 is used only when
    another scan actually reads its number; the primary copy prints no §1 mark.

    Each section is `(text, closed, first line, last line)`; the two line numbers are its
    place in the scan's `_djvu.txt`, which is how its printed page is found.
    """
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    start = body_start(lines)
    hits = [h for h in marks(lines, allow_inline=True) if h[0] >= start]
    hit = chain(hits)
    implied = None
    if hit and hit[0][1] == 2:
        block = lines[start + 1:hit[0][0]]
        first_line = start + 1
        while block and (not block[0].strip() or
                         sum(c.isupper() for c in block[0]) > sum(c.islower() for c in block[0])):
            block.pop(0)                      # the heading, broken over two lines
            first_line += 1
        text = clean("\n".join(block))
        if len(text) >= 40:
            implied = (text, True, min(first_line, len(lines) - 1), hit[0][0] - 1)
    secs = {}
    for i, (ln, n, rest) in enumerate(hit):
        stop = hit[i + 1][0] if i + 1 < len(hit) else len(lines)
        block = "\n".join(([rest] if rest else []) + lines[ln + 1:stop])
        text = clean(block)
        nxt = hit[i + 1][1] if i + 1 < len(hit) else None
        if not text:
            continue
        if n not in secs or (nxt == n + 1 and not secs[n][1]):
            secs[n] = (text, nxt == n + 1, ln, stop - 1)
    return secs, implied


def letters(s):
    return re.sub(r"[^a-z]", "", s.lower())


def main():
    per_scan, implied_first, scan_meta, corpus = {}, {}, [], set()
    locators, places_by_label = {}, {}
    for ident, rel, label in SCANS:
        path = os.path.join(SRC_DIR, rel)
        if not os.path.exists(path):
            print(f"  !! missing source {path} — skipped (recorded in data/README.md)")
            continue
        blob = open(path, "rb").read()
        text = blob.decode("utf-8", "replace")
        evidence = require_first_wheeler(text, label)
        secs, implied = parse(path)
        per_scan[label] = secs
        if implied:
            implied_first[label] = implied
        locator, _ = scanlib.locate(path, text)
        locators[label] = locator
        places = {n: scanlib.place(locator, got[2], got[3]) for n, got in secs.items()}
        if implied and locator is not None:
            places[1] = scanlib.place(locator, implied[2], implied[3])
        places_by_label[label] = places
        flat = letters(text)
        corpus.update(flat[i:i + 12] for i in range(0, max(0, len(flat) - 12)))
        scan_meta.append({"label": label, "identifier": ident, "role": "scan",
                          "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
                          "edition": "first edition (1810), Wheeler translation, 1913",
                          "edition_evidence": evidence[:240],
                          "sections": len(secs)})
        print(f"  scan {label:14s} {len(secs):3d} sections readable")

    def coverage(text):
        flat = letters(text)
        g = [flat[i:i + 12] for i in range(0, max(0, len(flat) - 12))]
        return (sum(1 for x in g if x in corpus) / len(g)) if g else 0.0

    marked = set()
    for secs in per_scan.values():
        marked.update(secs)
    merged, origin, verify, places = {}, {}, {}, {}
    # a section is taken from a scan that both reads its mark and reads the next one,
    # so no aphorism can carry the beginning of its neighbour; then any readable text;
    # and §1 may come from its position when another scan reads its number
    for stage in ("closed", "implied", "open"):
        for n in range(1, MAX + 1):
            if n in merged:
                continue
            for lab in [s[2] for s in SCANS if s[2] in per_scan]:
                got = per_scan[lab].get(n) or (implied_first.get(lab) if stage == "implied" and n in marked else None)
                if not got:
                    continue
                if stage == "closed" and not got[1]:
                    continue
                if stage == "implied" and n not in marked:
                    continue
                merged[n] = got[0]
                origin[n] = lab
                places[n] = places_by_label.get(lab, {}).get(n, {})
                break

    # §1 has no mark of its own in the primary copy; where it is printed as the first
    # block under the heading, and another copy reads its number, the primary's cleaner
    # text is preferred over the other copy's damaged line
    primary_label = SCANS[0][2]
    if 1 in marked and primary_label in implied_first and 1 not in per_scan.get(primary_label, {}):
        merged[1] = implied_first[primary_label][0]
        origin[1] = primary_label
        places[1] = places_by_label.get(primary_label, {}).get(1, {})

    refused = []
    for n in list(merged):
        c = round(coverage(merged[n]), 4)
        verify[n] = c
        if c < FLOOR:
            refused.append({"n": n, "corroboration": c})
            del merged[n]
            del origin[n]
            places.pop(n, None)

    # a block whose own leaf prints no folio may take the page the other copy of the
    # printing prints, but only where the two copies are proved to paginate alike
    texts_by_label = {lab: {n: got[0] for n, got in secs.items()}
                      for lab, secs in per_scan.items()}
    for lab, got in implied_first.items():
        texts_by_label.setdefault(lab, {})[1] = got[0]
    fills, cross = scanlib.cross_copy(places_by_label, texts_by_label, origin)
    for n, fill in fills.items():
        places.setdefault(n, {}).update(fill)

    missing = [n for n in range(1, MAX + 1) if n not in merged]
    cov = list(verify[n] for n in merged)
    meta = {
        "title": "Organon of the Rational Art of Healing",
        "edition": "First edition (1810), English translation by C. E. Wheeler, 1913",
        "translator": "C. E. Wheeler, M.D. (1913)",
        "source": "https://archive.org/details/organonofrationa00hahn",
        "licence": "Public domain: Hahnemann died 1843; Wheeler's translation was published 1913",
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
            "note": "This edition has no transcription to check against, so the check is "
                    "scan against scan; it catches OCR damage, not a wrong edition.",
        },
        "pages": scanlib.page_meta(locators, places, merged, cross=cross),
        "scans": scan_meta,
        "notes": [
            "The first edition is the only English translation of 1810: C. E. Wheeler's, "
            "Everyman's Library, 1913. It omits Hahnemann's Introduction and most of his "
            "footnotes; that omission is Wheeler's, and this bundle does not fill it.",
            "Sections are cut at the next section mark the same scan reads, so a lost mark "
            "leaves a named gap rather than merging two aphorisms.",
        ],
    }
    bundle = {"meta": meta, "sections": [
        dict({"n": n, "text": merged[n], "notes": [], "from": origin[n]},
             **places.get(n, {}),
             **{"corroboration": verify[n], "accepted": True}) for n in sorted(merged)]}

    body = json.dumps(bundle, ensure_ascii=False, separators=(",", ":"))
    js = ("/* The first edition, Wheeler's 1913 English translation, read from scans of the\n"
          " * 1913 printing. Generated by tools/build-organon1.py — do not hand-edit.\n"
          " * Public domain (Hahnemann d. 1843; Wheeler translation 1913). */\n"
          "(function (root, factory) {\n"
          '  if (typeof module === "object" && module.exports) module.exports = factory();\n'
          "  else root.ORGANON1 = factory();\n"
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
