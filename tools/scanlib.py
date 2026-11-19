#!/usr/bin/env python3
"""scanlib.py — the shared reader for the German and French ORGANON scans.

The first, fourth, fifth and sixth editions each had their own build script because
each was a different kind of book: a transcription with OCR as its check, or OCR whose
paragraph marks were Roman numerals or Arabic ones inside a running paragraph.

The second edition (1819), the third (1824) and Brunnow's French translation of the
second (1824) are a third kind. They print their paragraph numbers in the margin, and
where several paragraphs share one thought the margin carries a range — `90 — 105`,
`258 — 274` — with the text printed once. So the unit these books actually have is the
*block*, and a block is carried under its first number with `to` recording the last.
Expanding a block into one copy per number would duplicate Hahnemann's sentence fifteen
times; inventing text for the numbers inside it would be worse. The reader shows
`§90–105` and says so.

Marks are read tolerantly, because the numbers sit in the margin and OCR mangles them
(`§.` → `$.`, `S.`, `f.`, `J.`; `15` → `l5`; `61` → `Ql`). A mark is accepted only
where a number can still be read and the line carries prose after it, and a run is kept
only while it moves forward. Everything else is a named gap.

    import scanlib
    secs = scanlib.parse(path, max_n, END_MATTER)
"""
import hashlib, json, os, re, statistics

# OCR's own letter-for-digit confusions, applied inside a number only
DIGITS = {"l": "1", "I": "1", "|": "1", "i": "1", "!": "1", "O": "0", "o": "0",
          "Q": "0", "S": "5", "s": "5", "B": "8", "g": "9", "~": "7", "Z": "2"}
LONE = set("lIiOoQSsBgZ")          # a whole one-digit number read as a letter

# a section mark may be printed as any of these; the run of them is stripped first
PREFIX = re.compile(r"^[§$Ss|*TtfFJj•.,;:'\"„“\s]+")
TOKEN = re.compile(r"^([0-9A-Za-z|!~?]{1,3})\s*[.,;:*+]{0,3}\s*(?:[—–-]\s*)?")
PROSE = re.compile(r"^[A-Za-zÀ-ÿÄÖÜäöüß\"„'‘“(]")


def fix_number(tok):
    """Read a printed number the way OCR left it, or return None."""
    value = "".join(DIGITS.get(c, c) for c in tok)
    if not value.isdigit():
        return None
    # a number must carry at least one real digit, unless the whole number is one
    # character OCR read as a letter (`l.` for 1, `O.` for 0, `S.` for 5)
    if not any(c.isdigit() for c in tok) and not (len(tok) == 1 and tok in LONE):
        return None
    return int(value)


def read_marks(lines, max_n):
    """Every line that can only be read as a paragraph mark: number(s), then prose.

    The number is sometimes printed on a line of its own with the paragraph beneath it.
    That is accepted only where the line carried a mark character (`§. 17.`), because a
    bare number alone on a line is a page number (`50`), and a page number is not a
    section. A mark that carried its prose on the same line is accepted as before.
    """
    out = []
    for i, line in enumerate(lines):
        s = line.strip()
        if not s:
            continue
        marked = not s[0].isdigit()
        m0 = PREFIX.match(s)
        rest = s if not marked or not m0 else s[m0.end():]
        nums = []
        while len(nums) < 6:
            m = TOKEN.match(rest)
            if not m:
                break
            n = fix_number(m.group(1))
            if n is None or not 1 <= n <= max_n:
                break
            nums.append(n)
            rest = rest[m.end():]
        if not nums:
            continue
        if max(nums) - min(nums) > 40:          # not a range, but two unrelated numbers
            nums = nums[:1]
        if PROSE.match(rest):
            out.append((i, nums))
            continue
        if not marked or rest.strip(" .,;:*+—–-"):
            continue
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        nxt = lines[j].strip() if j < len(lines) else ""
        if len(nxt) >= 20 and PROSE.match(nxt) and not FOLIO.match(nxt):
            out.append((i, nums))
    return out


def chain(hits, tol=8, jump=60, start_with=2):
    """Keep a forward-moving run, so a page number cannot become a paragraph.

    A range advances the run to its *last* number: `49 — 59` is followed by 60, not 50.

    A gap bigger than `tol` is not the end of the book: the 1819 and 1824 printings lose
    whole stretches of margin numbers to OCR, and the paragraphs after the gap are still
    printed, still readable and still belong to the text. The run therefore resumes at the
    next mark ahead of it — but only up to `jump` numbers, so a stray reference to §300 in
    a footnote cannot open a second book. What lies between two accepted marks is a named
    gap, never text borrowed from somewhere else.
    """
    acc, last = [], 0
    for h in hits:
        lo, hi = min(h[1]), max(h[1])
        if (last == 0 and lo <= start_with) or 0 < lo - last <= jump:
            acc.append(h)
            last = hi
    return acc


def best_chain(hits, tol=8, jump=60, start_with=2):
    """The longest forward run that begins at the book's first paragraph."""
    return max((chain(hits[k:], tol, jump, start_with) for k, h in enumerate(hits)
                if min(h[1]) <= start_with), key=len, default=[])


PLATE = re.compile(r"^\s*(?:Digitized by [A-Za-z ]+|Google|THE END|SEITE)\s*[.,]?$", re.I)
FOLIO = re.compile(r"^\s*(?:\d{1,3}|[IVXLC]{1,7}|[0-9A-Za-z]{1,2})\s*[.,]?\s*$")


def clean(block, end_matter, drop=None):
    """Drop page furniture, fold hyphen breaks, keep the words."""
    out = []
    for ln in block.split("\n"):
        s = ln.rstrip()
        if end_matter and end_matter.match(s):
            break
        if PLATE.match(s) or FOLIO.match(s):
            continue
        if drop and drop.match(s.strip()):
            continue
        if not s.strip():
            if out and out[-1] != "":
                out.append("")
            continue
        out.append(s.strip())
    text = "\n".join(out).strip()
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)      # a word broken at the margin
    text = re.sub(r"\n+", " ", text)
    text = re.sub(r"(?i)\bdigitized\s+by\s*[a-z]*\s*[-–—]?\s*", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def parse(path, max_n, end_matter=None, drop=None, body=None):
    """Returns {first number: (text, last number, closed)}.

    `closed` is True when the next block's mark was also read, so the text cannot run on
    into a paragraph whose own number was lost.

    `body` is a regex for the book's own first sentence. Both the 1819 and 1824 printings
    open with a numbered synopsis of the whole work before the text proper, and a scan's
    front matter is full of numbers that look like paragraph marks; anchoring on the
    first sentence keeps the synopsis and the library stamps out of the book.
    """
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    start = 0
    if body:
        for i, line in enumerate(lines):
            if body.search(line):
                start = max(0, i - 3)
                break
    hit = best_chain([h for h in read_marks(lines, max_n) if h[0] >= start])
    secs = {}
    for i, (ln, nums) in enumerate(hit):
        stop = hit[i + 1][0] if i + 1 < len(hit) else len(lines)
        block = "\n".join(lines[ln + 1:stop])
        # the text after the numbers on the mark's own line belongs to the paragraph
        head = lines[ln]
        m0 = PREFIX.match(head.strip())
        rest = head.strip() if head.strip()[:1].isdigit() or not m0 else head.strip()[m0.end():]
        for _ in nums:
            rest = TOKEN.sub("", rest, count=1)
        block = rest.strip() + "\n" + block
        text = clean(block, end_matter, drop)
        if len(text) < 10:
            continue
        n, to = min(nums), max(nums)
        closed = i + 1 < len(hit) and hit[i + 1][1][0] - max(nums) <= 12
        if n not in secs or (closed and not secs[n][2]):
            secs[n] = (text, to, closed)
    return secs


def letters(s):
    """Fold to the letters both copies of a German or French page agree on."""
    s = s.lower()
    for a, b in (("ä", "a"), ("ö", "o"), ("ü", "u"), ("ß", "ss"), ("é", "e"), ("è", "e"),
                 ("ê", "e"), ("à", "a"), ("â", "a"), ("î", "i"), ("ï", "i"), ("ô", "o"),
                 ("û", "u"), ("ù", "u"), ("ç", "c"), ("œ", "oe"), ("æ", "ae")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z]", "", s)


def grams(text, size=12):
    flat = letters(text)
    return [flat[i:i + size] for i in range(0, max(0, len(flat) - size))]


def coverage(text, corpus):
    g = grams(text)
    return (sum(1 for x in g if x in corpus) / len(g)) if g else 0.0


def evidence_line(flat, required):
    """The words on the title page that establish which book this scan is."""
    for token in required:
        i = flat.find(token)
        if i >= 0:
            return flat[max(0, i - 120):i + 160].strip()
    return flat[:240].strip()


def scan_meta(ident, label, blob, text, evidence, edition, role="parser and corpus",
              sections=0, extras=None):
    meta = {"label": label, "identifier": ident, "role": "scan", "role_detail": role,
            "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
            "edition": edition, "edition_evidence": evidence[:240], "sections": sections}
    if extras:
        meta.update(extras)
    return meta


def write_bundle(out_js, out_json, meta, sections, global_name, comment, spans=True):
    bundle = {"meta": meta, "sections": sections}
    body = json.dumps(bundle, ensure_ascii=False, separators=(",", ":"))
    js = ("/* " + comment.replace("\n", "\n * ") + "\n"
          " * Generated by " + meta.get("generator", "tools/") + " — do not hand-edit.\n"
          " * Public domain (Hahnemann d. 1843). */\n"
          "(function (root, factory) {\n"
          '  if (typeof module === "object" && module.exports) module.exports = factory();\n'
          "  else root." + global_name + " = factory();\n"
          '})(typeof self !== "undefined" ? self : this, function () {\n'
          "  return " + body + ";\n});\n")
    open(out_js, "w", encoding="utf-8").write(js)
    if out_json:
        json.dump(bundle, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return len(js)


def build(out_js, out_json, global_name, max_n, sources, edition, title, translator,
          language, comment, confidence_note, floor=0.60, source_url=None, notes=(),
          generator="tools/", extras=()):
    """Shared body: read every scan, corroborate, name the gaps, write the bundle."""
    corpus, per_scan, scan_meta_list, seen = set(), {}, [], {}
    for src in sources:
        path = os.path.join(os.environ.get("ORGANON_SRC", "."), src["path"])
        if not os.path.exists(path):
            print(f"  !! missing source {path} — skipped (recorded in data/README.md)")
            continue
        blob = open(path, "rb").read()
        text = blob.decode("utf-8", "replace")
        flat = re.sub(r"\s+", " ", text).upper()
        for word in src.get("refuse", ()):  # the edition guard
            if word in flat:
                raise SystemExit(f"refusing {src['label']}: names {word}")
        for word in src.get("require", ()):
            if word not in flat:
                raise SystemExit(f"refusing {src['label']}: does not declare {word}")
        secs = (parse(path, max_n, src.get("end_matter"), src.get("drop"), src.get("body"))
                if src.get("parse", True) else {})
        if not secs:
            print(f"  scan {src['label']:22s}   no marks readable — corpus only")
        per_scan[src["label"]] = secs
        corpus.update(grams(text))
        evidence = src.get("evidence") or evidence_line(flat, src.get("require", ()))
        scan_meta_list.append(scan_meta(
            src["ident"], src["label"], blob, text, evidence, src["edition"],
            role=src.get("role", "parser and corpus"), sections=len(secs)))
        seen[src["label"]] = len(secs)
        if secs:
            print(f"  scan {src['label']:22s} {len(secs):3d} blocks readable")

    merged, origin, to_of, verify = {}, {}, {}, {}
    for closed_only in (True, False):
        for lab, secs in per_scan.items():
            for n, (text, to, closed) in secs.items():
                if n in merged or (closed_only and not closed):
                    continue
                merged[n] = text
                origin[n] = lab
                to_of[n] = to

    refused = []
    for n in list(merged):
        c = round(coverage(merged[n], corpus), 4)
        verify[n] = c
        if c < floor:
            refused.append({"n": n, "corroboration": c})
            del merged[n], origin[n], to_of[n]

    covered = set()
    for n, to in to_of.items():
        covered.update(range(n, to + 1))
    missing = [n for n in range(1, max_n + 1) if n not in covered]
    cov = [verify[n] for n in merged]
    meta = {
        "title": title, "edition": edition, "translator": translator, "language": language,
        "source": source_url or ("https://archive.org/details/" + sources[0]["ident"]),
        "licence": "Public domain: Hahnemann died 1843; this printing is from the 1820s",
        "total_in_book": max_n, "recovered": len(merged), "missing": missing,
        "blocks": len(merged), "numbered_paragraphs_carried": len(covered),
        "status": (f"OCR-derived, corroborated across scans; {len(missing)} numbered "
                   f"paragraph(s) not readable"),
        "verification": {
            "method": "fraction of each block's 12-letter sequences found verbatim in the scans",
            "median": round(statistics.median(cov), 4) if cov else None,
            "min": round(min(cov), 4) if cov else None,
            "sections_checked": len(cov), "floor": floor, "refused": refused,
            "note": confidence_note,
        },
        "scans": scan_meta_list,
        "notes": list(notes),
    }
    for key, value in extras:
        meta[key] = value
    sections = [{"n": n, "to": to_of[n], "text": merged[n], "notes": [],
                 "from": origin[n], "corroboration": verify[n], "accepted": True}
                for n in sorted(merged)]
    size = write_bundle(out_js, out_json, meta, sections, global_name, comment)
    print(f"  blocks {len(merged)} of {max_n} numbered paragraphs "
          f"({len(covered)} covered) | median {meta['verification']['median']} "
          f"| min {meta['verification']['min']} | refused {len(refused)}")
    print(f"  missing {len(missing)}: {missing[:24]}{'…' if len(missing) > 24 else ''}")
    print(f"  wrote {out_js} {size} bytes")
    return meta, sections
