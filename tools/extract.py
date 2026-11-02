#!/usr/bin/env python3
"""extract.py — Organon (6th ed., 1922 Boericke translation) djvu.txt -> sections.json

Rules it keeps:
  * a section exists only where the book prints a section mark we can actually read;
  * numbers are never invented and never renumbered - an unreadable mark is dropped
    and reported, so the reader can publish what it really carries;
  * the printed number must move forward, so an OCR'd page number cannot become one.
"""
import json, re

SRC, MAX = "organon.txt", 291
raw = open(SRC, encoding="utf-8", errors="replace").read()
body = raw[163700:]          # front matter + introduction end here; §1 follows

# marker lines: a short line carrying the section mark (§ or its OCR twins S/8)
marks = []
pos = 0
for ln in body.split("\n"):
    s = ln.strip()
    if 0 < len(s) <= 8 and re.search(r"[§S]", s):
        m = re.search(r"\d{1,3}", s)
        marks.append({"pos": pos, "printed": s, "num": int(m.group(0)) if m else None})
    pos += len(ln) + 1

PAGE_HEADER = re.compile(r"^\s*(?:\d{1,3}\s+)?(?:TEXT OF THE ORGANON|TRANSLATORS PREFACE|ORGANON OF MEDICINE)\s*(?:\d{1,3})?\s*$", re.I)

def clean(block):
    out = []
    for ln in block.split("\n"):
        s = ln.rstrip()
        if PAGE_HEADER.match(s) or re.fullmatch(r"\s*\d{1,3}\s*", s):
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

accepted, last = [], 0
for i, mk in enumerate(marks):
    n = mk["num"]
    if n is None or not (last < n <= MAX) or n - last > 6:
        continue                                  # unreadable, or not a forward step
    stop = next((m["pos"] for m in marks[i + 1:] if m["pos"] > mk["pos"]), len(body))
    text = clean(body[mk["pos"] + len(mk["printed"]):stop])
    if len(text) < 40:
        continue                                  # a mark with nothing under it
    accepted.append({"n": n, "printed": mk["printed"], "text": text})
    last = n

got = {s["n"] for s in accepted}
missing = [n for n in range(1, MAX + 1) if n not in got]
print(f"recovered {len(accepted)} of {MAX} aphorisms; missing {len(missing)}")
print("chars", sum(len(s["text"]) for s in accepted))
json.dump({
    "title": "Organon of Medicine",
    "edition": "Sixth edition (1842), English translation by William Boericke, 1922",
    "translator": "William Boericke",
    "source": "https://archive.org/details/organon-of-medicine-6th-edition-completed-1842-german-edition-published-1921-eng",
    "source_file": "Organon of Medicine 6th edition ... _djvu.txt (532,017 bytes, OCR)",
    "licence": "Public domain: Hahnemann d. 1843; Boericke translation 1922",
    "total_in_book": MAX,
    "recovered": len(accepted),
    "missing": missing,
    "sections": accepted,
}, open("sections.json", "w"), ensure_ascii=False)
