#!/usr/bin/env python3
"""parse_homeoint.py — read the Médi-T transcription of the Organon (homeoint.org) into
sections, sixth edition only.

The page prints BOTH editions: where the fifth and sixth differ it prints "§ N Fifth
Edition" and "§ N Sixth Edition" one after the other; where they agree it prints a bare
"§ N". So: a labelled *Sixth Edition* block is taken, a labelled *Fifth Edition* block is
skipped, and a bare heading is taken (it is the same text in both editions).
"""
import html as htmllib, json, re, sys, glob, os

# Every heading is anchored: <a name="P21">, and where the editions differ the anchor
# says so — "P20E5" is the fifth-edition variant, "P20E6" the sixth.
HEAD = re.compile(r'<a\s+name="P(\d{1,3})(E5|E6)?"\s*>', re.I)


def text_of(chunk):
    s = re.sub(r"<[^>]+>", " ", chunk)
    s = htmllib.unescape(s)
    s = s.replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


NOTE = re.compile(r'^\s*(\d{1,2})\s+')


def split_notes(html_block):
    """Separate the section's own text from its footnotes.

    The transcription puts each footnote in its own paragraph beginning with its number
    in a small font; without this split the footnote runs into the text ("termed. 1 1 His
    mission is not..."), which reads as a typo rather than as a note.
    """
    parts = re.split(r"<p[^>]*>", html_block, flags=re.I)
    main, notes = [], []
    for part in parts:
        txt = text_of(part)
        if not txt:
            continue
        m = NOTE.match(txt)
        if m and (len(txt) > 30) and not main:
            pass
        if m and len(txt) > 25 and (notes or re.match(r"^\s*\d{1,2}\s+[A-Z\u2018\u201c(]", txt)):
            notes.append(txt)
        else:
            main.append(txt)
    return " ".join(main).strip(), notes


def parse(path):
    raw = open(path, encoding="windows-1252", errors="replace").read()
    marks = list(HEAD.finditer(raw))
    out = {}
    for i, m in enumerate(marks):
        n = int(m.group(1))
        edition = {"E5": "fifth", "E6": "sixth"}.get((m.group(2) or "").upper(), "")
        if edition == "fifth":
            continue                      # a fifth-edition variant is never used
        stop = marks[i + 1].start() if i + 1 < len(marks) else len(raw)
        body = raw[m.end():stop]
        body = re.split(r"</blockquote>|<hr|</body>", body)[0]
        body = re.sub(r"^\s*§\s*\d{1,3}\s*(?:(?:Fifth|Sixth)\s+[Ee]dition)?\s*", "", body).strip()
        text, notes = split_notes(body)
        text = re.sub(r"^(?:§\s*\d{1,3}\s*)?(?:(?:Fifth|Sixth)\s+[Ee]dition\s*)?", "", text).strip()
        for i in range(len(notes)):
            notes[i] = re.sub(r"^(?:Fifth|Sixth)\s+[Ee]dition\s*", "", notes[i]).strip()
        if len(text) < 40:
            continue
        if n not in out or (edition == "sixth" and not out[n][1]):
            out[n] = ({"text": text, "notes": notes}, edition == "sixth")
    return {n: t for n, (t, _six) in out.items()}


def main():
    merged = {}
    for path in sorted(glob.glob("src/homeoint_*.html")):
        secs = parse(path)
        if not secs:
            print(f"  !! {path}: no sections parsed")
            continue
        print(f"  {os.path.basename(path):22s} {len(secs):3d} sections  {min(secs)}–{max(secs)}")
        for n, t in secs.items():
            merged.setdefault(n, t)
    json.dump(merged, open("homeoint_sections.json", "w"), ensure_ascii=False)
    missing = [n for n in range(1, 292) if n not in merged]
    print(f"homeoint total {len(merged)}; missing {missing}")


if __name__ == "__main__":
    main()
