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


# --- reading a printed contents list -------------------------------------------
#
# The 1819 and 1824 German printings open with an Inhaltsanzeige: a list that gives
# the paragraph numbers — a single one, or a range where several paragraphs share one
# thought — and one rubric in the margin style, `90 — 105.  Vorschrift, wie ...`.  Its
# marks are the same margin numbers as the text, only compressed onto one line, so the
# reader is the same; what changes is that a range's *start* is often the character OCR
# mangled worst (`J.06` for 106, `JlO` for 110, `j5o` for 150), because a leading 1 is
# printed as a bare stroke and read as a letter.

GLYPHS = dict(DIGITS)
GLYPHS.update({"j": "1", "J": "1", "t": "1", "f": "1", "F": "1", "T": "1"})
SEP = r"[\s.,;:*+«'\u201a\u201e\"()\[\]|~?—–-]*"
MARK_TOKEN = re.compile(r"^([0-9A-Za-z|!~?]{1,4})" + SEP)
MARK_PREFIX = re.compile(r"^[§$Ss|*TtFfJj•.,;:'\"„“\s]*")
BARE_ONE = "JjIi|l!tfT1"           # a leading character OCR may have read for `1`


def _number(tok, max_n):
    value = "".join(GLYPHS.get(c, c) for c in tok)
    if not value.isdigit() or len(tok) > 4:
        return None
    # a number must show at least one digit of its own. A token of letters only is a
    # word more often than a number (`ist` reads as 151, `Jn` as 16), and a number
    # written wholly in letters cannot be told from the word it resembles — `igS` is
    # 193 or 195 — so it is left as a gap and given to the second scan instead.
    if not any(c.isdigit() for c in tok) and len(tok) > 1:
        return None
    n = int(value)
    return n if 1 <= n <= max_n else None


def _prose(r):
    """True when what follows the numbers is the entry's own words."""
    return bool(PROSE.match(r.lstrip(" .,;:*'$§—–-«\"„“()[]")))


def mark_readings(line, max_n):
    """Every way this line can be read as a printed contents entry, best first.

    Each reading is `(numbers, open_start, open_end, rest)`. `keep` is the reading
    that keeps a leading letter as the digit 1, because a leading 1 is printed as a
    bare stroke and read as a letter (`J.06` = 106). It is tried second, so a line
    that really does start with a mark character is not read as a number by accident.
    A full stop printed inside a number is folded away first.

    A range may lose one end to OCR. `open_end` says its first number was read but
    the number after the dash was not (`181 — igS-`); `open_start` says the number
    before the dash was lost but the one after it was read (`394 — -228.`). Neither
    end is filled in here: the caller decides, and says where the number came from.
    """
    s = re.sub(r"(?<=[0-9A-Za-z])[.,](?=[0-9])", "", line.strip())
    out = []
    for keep in (False, True):
        rest = s
        if not keep:
            m = MARK_PREFIX.match(rest)
            if m:
                rest = rest[m.end():]
        elif not rest or rest[0] not in BARE_ONE:
            continue
        nums, r, toks = [], rest, []
        while len(nums) < 4:
            m = MARK_TOKEN.match(r)
            if not m:
                break
            tok = m.group(1)
            # a lone letter that begins a word is a word, not a number (`Für`)
            if len(tok) == 1 and tok.isalpha() and r[m.end():m.end() + 1].isalpha():
                break
            n = _number(tok, max_n)
            if n is None:
                break
            nums.append(n)
            toks.append(tok)
            r = r[m.end():]
        # a reading that kept a leading letter must still show a real digit somewhere,
        # otherwise any word beginning with `i` would read as a number (`ist` = 151)
        if keep and not any(c.isdigit() for t in toks for c in t):
            nums = []
        if nums and _prose(r):
            if len(nums) == 1 or (max(nums) - min(nums) <= 40 and
                                  all(b > a for a, b in zip(nums, nums[1:]))):
                out.append((tuple(nums), False, False, r))
                continue
        # a range that cannot be read whole still keeps the end printed first
        if nums and re.match(r"^[0-9A-Za-z|!~?]{1,4}\s*[—–-]", rest):
            out.append((tuple(nums[:1]), False, True, r))
            continue
        # the first number is unreadable but a later one is printed: `394 — -228.`
        m = None if nums else re.match(
            r"^[0-9A-Za-z|!~?]{1,4}\s*[—–-]+\s*" + SEP, rest)
        if not m or keep:
            continue
        nums, r = [], rest[m.end():]
        while len(nums) < 4:
            t = MARK_TOKEN.match(r)
            if not t:
                break
            n = _number(t.group(1), max_n)
            if n is None:
                break
            nums.append(n)
            r = r[t.end():]
        if nums and _prose(r):
            out.append((tuple(nums), True, False, r))
    return out


OVERVIEW_STOP = re.compile(r"^\s*(?:Einleitung|Vorrede|Anhang|Inhalt|Register|"
                           r"Druckfehler|Verbesserungen|Nachschrift|Inhaltsanzeige)\b")


def overview_entries(path, max_n, body=None, end_matter=None, drop=None):
    """Ordered entries of a printed contents list: [{line, printed, readings, text}].

    The list ends at the next section heading (`Einleitung` in the 1819 printing), so
    the book's footnotes and the bookseller's advertisements cannot become entries.
    Each entry keeps every reading of its number line; `resolve_entries` decides, and
    an entry whose numbers cannot be settled simply carries none.
    """
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    start = 0
    if body is not None:
        for i, line in enumerate(lines):
            if body.search(line):
                start = max(0, i - 2)
                break
    marks = []
    for i, line in enumerate(lines):
        if i < start or not line.strip():
            continue
        if marks and (OVERVIEW_STOP.match(line) or OVERVIEW_STOP.match(line.strip())):
            break
        got = mark_readings(line, max_n)
        if got:
            marks.append((i, got, line))
    out = []
    for k, (i, got, line) in enumerate(marks):
        stop = marks[k + 1][0] if k + 1 < len(marks) else len(lines)
        block = "\n".join(lines[i + 1:stop])
        out.append({"line": i, "printed": line.strip(),
                    "readings": [{"numbers": list(n), "open_start": a, "open_end": b,
                                  "rest": r} for n, a, b, r in got],
                    "text": clean(got[0][3] + "\n" + block, end_matter, drop)})
    return out


def resolve_entries(entries, max_n=319, known=None):
    """Settle each entry's numbers, by what is printed first and by order second.

    Every reading of a line is offered; the one kept is the one whose first number
    still lies ahead of the previous kept entry. That is how `j54.` (read as 54 on its
    face, 154 with the leading `j` kept) is settled: 54 would run backwards.

    A range that lost one end to OCR keeps the end that was printed. The lost end is
    taken from the entry beside it (`181 — igS` ends where the next entry begins; the
    entry before `394 — 228` ends where this one begins) — the printed list enumerates
    the paragraphs in order, and Brunnow's French contents list prints every one of
    them, so the numbering has no hole for an entry to fall into. Each restored end is
    recorded on the entry (`restored`), never silently applied, and an end that cannot
    be settled that way stays unknown and becomes a named gap.
    """
    last = 0
    for e in entries:
        chosen = None
        for r in e["readings"]:
            nums = r["numbers"]
            if not nums:
                continue
            if nums[0] > last:
                chosen = r
                break
        e["numbers"] = list(chosen["numbers"]) if chosen else []
        e["open_start"] = bool(chosen and chosen["open_start"])
        e["open_end"] = bool(chosen and chosen["open_end"])
        e["restored"] = []
        if chosen:
            last = chosen["numbers"][-1]
    def corroborated(span):
        """Every number of the span is printed in the French contents list."""
        if known is None:
            return True
        have = sum(1 for n in span if n in known)
        return have >= 0.85 * len(span)

    for k, e in enumerate(entries):
        nxt = entries[k + 1] if k + 1 < len(entries) else None
        if e["numbers"] and e["open_end"] and nxt and nxt["numbers"] and not nxt["open_start"]:
            end = nxt["numbers"][0] - 1
            if end > e["numbers"][-1] and corroborated(range(e["numbers"][-1], end + 1)):
                e["numbers"].append(end)
                e["restored"].append({"end": end, "from": "the next entry's first number"})
        elif e["open_start"] and k and entries[k - 1]["numbers"]:
            start = entries[k - 1]["numbers"][-1] + 1
            if (e["numbers"] and start < e["numbers"][0]
                    and corroborated(range(start, e["numbers"][0] + 1))):
                e["numbers"].insert(0, start)
                e["restored"].append({"start": start,
                                      "from": "the previous entry's last number"})
    for e in entries:
        if e["numbers"] and e["open_end"] and not e["restored"]:
            e["numbers"] = e["numbers"][:1]
    return entries


def bundle_numbers(path):
    """The paragraph numbers a bundle already built from a scan carries."""
    if not os.path.exists(path):
        print(f"  !! {path} not built — the range ends cannot be corroborated")
        return None
    text = open(path, encoding="utf-8").read()
    text = text[text.index("return ") + 7:text.rindex("};") + 1]
    return {int(m) for m in re.findall(r'\{"n":(\d+)', text)}


def words(text):
    """The words of a rubric, folded to letters the two scans agree on."""
    return [w for w in (letters(x) for x in re.split(r"\s+", text)) if len(w) >= 4]


def same_entry(text, others, take=8, need=0.75):
    """The entry in a second scan of the same printing that prints the same words.

    A contents entry is one line of rubric, so its opening words identify it. A second
    scan is only used when its opening words agree (`need`), and only the numbers are
    taken from it — never its text.
    """
    mine = words(text)[:take]
    if len(mine) < 3:
        return None
    best, best_score = None, 0.0
    for other in others:
        theirs = set(words(other["text"])[:take])
        if not theirs:
            continue
        score = len(set(mine) & theirs) / len(mine)
        if score > best_score:
            best, best_score = other, score
    return best if best_score >= need else None


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

    _finish(merged, origin, to_of, {}, corpus, max_n, out_js, out_json, global_name,
            {"title": title, "edition": edition, "translator": translator,
             "language": language,
             "source": source_url or "https://archive.org/details/" + sources[0]["ident"]},
            comment, confidence_note, floor, notes, generator, extras, scan_meta_list)


def _finish(merged, origin, to_of, extra, corpus, max_n, out_js, out_json, global_name,
            head, comment, confidence_note, floor, notes, generator, extras, scans):
    """Verify every block against the scans, name the gaps, write the bundle."""
    verify, refused = {}, []
    for n in list(merged):
        if len(letters(merged[n])) < 12:
            # a rubric shorter than the window carries no sequence to look for; it is
            # kept and marked as unverifiable rather than refused
            verify[n] = None
            continue
        c = round(coverage(merged[n], corpus), 4)
        verify[n] = c
        if c < floor:
            refused.append({"n": n, "corroboration": c})
            del merged[n], origin[n], to_of[n]
            extra.pop(n, None)

    covered = set()
    for n, to in to_of.items():
        covered.update(range(n, to + 1))
    missing = [n for n in range(1, max_n + 1) if n not in covered]
    cov = [v for v in verify.values() if v is not None]
    meta = dict(head)
    meta.update({
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
        "scans": scans,
        "notes": list(notes),
    })
    for key, value in extras:
        meta[key] = value
    sections = []
    for n in sorted(merged):
        row = {"n": n, "to": to_of[n], "text": merged[n], "notes": [],
               "from": origin[n], "corroboration": verify[n], "accepted": True}
        row.update(extra.get(n, {}))
        sections.append(row)
    size = write_bundle(out_js, out_json, meta, sections, global_name, comment)
    print(f"  blocks {len(merged)} of {max_n} numbered paragraphs "
          f"({len(covered)} covered) | median {meta['verification']['median']} "
          f"| min {meta['verification']['min']} | refused {len(refused)}")
    print(f"  missing {len(missing)}: {missing[:24]}{'…' if len(missing) > 24 else ''}")
    print(f"  wrote {out_js} {size} bytes")
    return meta, sections


def build_from(out_js, out_json, global_name, max_n, blocks, scans, corpus, head,
               comment, confidence_note, notes, floor=0.60, generator="tools/", extras=()):
    """Assemble a bundle from blocks already read, numbered and named.

    `blocks` is [{n, to, text, from, extra}] in printed order; `scans` the metadata of
    the copies read; `corpus` the 12-letter sequences of those copies.
    """
    merged, origin, to_of, extra = {}, {}, {}, {}
    for b in blocks:
        merged[b["n"]] = b["text"]
        origin[b["n"]] = b["from"]
        to_of[b["n"]] = b["to"]
        if b.get("extra"):
            extra[b["n"]] = b["extra"]
    return _finish(merged, origin, to_of, extra, corpus, max_n, out_js, out_json,
                   global_name, head, comment, confidence_note, floor, notes, generator,
                   extras, scans)
