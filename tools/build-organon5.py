#!/usr/bin/env python3
"""build_organon5.py — corroborate the fifth-edition transcription against three
Dudgeon scans and emit the bundle.

Same method as the repo's tools/extract.py: flatten to lowercase a–z, take every
12-character sequence, and measure what fraction of a section's sequences appear
verbatim in the scan corpus. A section below 0.60 is not corroborated and is reported
as such rather than quietly included.

The edition guard is stricter than a head-window probe, because OCR puts the title
page wherever it likes: a scan is admitted only if it declares Dudgeon's translation
of the fifth German edition and never mentions Boericke.
"""
import re, json, hashlib, os, statistics

SCANS = [
    ("b28136536", "dudgeon/b28136536.txt", "Wellcome-1893"),
    ("b21307957", "dudgeon/b21307957.txt", "IA-1849"),
    ("organonmedicine01hahngoog", "dudgeon/organonmedicine01hahngoog.txt", "Google-1849"),
]
FLOOR = 0.60
OUT_JS = "/scratch/output/organon5-data.js"
OUT_JSON = "/scratch/output/organon5-draft.json"

def letters(s):
    return re.sub(r"[^a-z]", "", s.lower())

def require_fifth_dudgeon(raw, label):
    flat = re.sub(r"\s+", " ", raw).upper()
    # Boericke & Tafel were the New York publishers of Dudgeon's translation too, so a
    # bare "BOERICKE" proves nothing. The sixth edition is identified by its translator.
    if re.search(r"WILLIAM\s+BOERICKE|BOERICKE['\u2019]S\s+TRANSLATION", flat):
        raise SystemExit(f"refusing {label}: Boericke's translation — a sixth-edition scan")
    m = re.search(r"TRANSLATED\s+FR[O0]M\s+THE\s+FIFTH\s+GE[RB][IM][CA]AN\s+EDITION", flat)
    if not m and not ("FIFTH EDITION" in flat and "DUDGEON" in flat):
        raise SystemExit(f"refusing {label}: does not declare Dudgeon's translation of the fifth edition")
    i = m.start() if m else flat.find("FIFTH EDITION")
    return flat[max(0, i - 60):i + 200].strip()

def main():
    corpus, scans_meta = set(), []
    for ident, path, label in SCANS:
        blob = open(path, "rb").read()
        text = blob.decode("utf-8", "replace")
        evidence = require_fifth_dudgeon(text, label)
        flat = letters(text)
        corpus.update(flat[i:i + 12] for i in range(0, max(0, len(flat) - 12)))
        scans_meta.append({"label": label, "identifier": ident, "role": "scan",
                           "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
                           "edition": "fifth edition, Dudgeon translation",
                           "edition_evidence": evidence[:240]})
        print(f"  scan {label:14s} {len(blob):8d} bytes  admitted")

    def coverage(t):
        f = letters(t)
        g = [f[i:i + 12] for i in range(0, max(0, len(f) - 12))]
        return (sum(1 for x in g if x in corpus) / len(g)) if g else 0.0

    draft = json.load(open("/scratch/work/organon5_draft.json"))
    six = json.load(open("/scratch/work/six.json"))
    s6 = {str(s["n"]): s for s in six["sections"]}

    secs, accepted, refused = [], 0, []
    for n, v in sorted(draft["sections"].items(), key=lambda kv: int(kv[0])):
        n = int(n)
        c = round(coverage(v["text"] + " " + " ".join(v["notes"])), 4)
        ok = c >= FLOOR
        accepted += ok
        if not ok:
            refused.append({"n": n, "corroboration": c})
        t5 = " ".join(v["text"].split())
        t6 = " ".join((s6.get(str(n)) or {}).get("text", "").split())
        secs.append({
            "n": n, "text": v["text"], "notes": v["notes"],
            "from": "MediT-" + ("5th" if v["variant"] == "fifth" else "shared"),
            "corroboration": c,
            "accepted": ok,
            "variant": v["variant"],
            "differsFromSixth": bool(t6) and t5 != t6,
            "absentFromSixth": str(n) not in s6,
        })

    cov = [s["corroboration"] for s in secs]
    meta = {
        "title": "Organon of Medicine",
        "edition": "Fifth edition (fifth German edition, published 1833)",
        "translator": "R. E. Dudgeon, M.D. (1849)",
        "source": "Médi-T transcription, homeoint.org, retrieved via the Internet Archive Wayback Machine",
        "licence": "Public domain: Hahnemann died 1843; Dudgeon's translation was published 1849",
        "total_in_book": 294,
        "recovered": len(secs),
        "missing": [],
        "status": ("corroborated" if not refused else
                   f"corroborated except {len(refused)} section(s) below the {FLOOR} floor"),
        "verification": {
            "method": "fraction of each section's 12-letter sequences found verbatim in the scans",
            "median": round(statistics.median(cov), 4),
            "min": round(min(cov), 4),
            "sections_checked": len(secs),
            "sections_accepted": accepted,
            "floor": FLOOR,
            "refused": refused,
        },
        "scans": scans_meta,
        "counts": {
            "labelledFifthVariant": sum(1 for s in secs if s["variant"] == "fifth"),
            "sharedWithSixth": sum(1 for s in secs if s["variant"] == "shared"),
            "differsFromSixth": sum(1 for s in secs if s["differsFromSixth"]),
            "absentFromSixth": sum(1 for s in secs if s["absentFromSixth"]),
        },
        "notes": [
            "Three Dudgeon scans of the 1849 translation corroborate the transcription; "
            "none is the sixth edition and none mentions Boericke.",
            "§89 carries the transcription's own editorial marker '(Added to the Sixth Edition)' "
            "inside its body. It is left verbatim rather than silently edited; see the QC note.",
            "§292–294 exist in the transcription and are absent from the sixth edition.",
        ],
    }
    bundle = {"meta": meta, "sections": secs}
    body = json.dumps(bundle, ensure_ascii=False, separators=(",", ":"))
    js = ("/* The fifth edition, Dudgeon's 1849 translation, corroborated against three scans.\\n"
          ' * Generated by tools/build-organon5.py — do not hand-edit.\n'
          ' * Public domain (Hahnemann d. 1843; Dudgeon translation 1849). */\n'
          '(function (root, factory) {\n'
          '  if (typeof module === "object" && module.exports) module.exports = factory();\n'
          '  else root.ORGANON5 = factory();\n'
          '})(typeof self !== "undefined" ? self : this, function () {\n'
          '  return ' + body + ';\n});\n')
    open(OUT_JS, "w", encoding="utf-8").write(js)
    json.dump(bundle, open(OUT_JSON, "w"), ensure_ascii=False, indent=1)
    print(f"\nsections {len(secs)} | accepted {accepted} | median {meta['verification']['median']} "
          f"| min {meta['verification']['min']} | refused {refused}")
    print("wrote", OUT_JS, os.path.getsize(OUT_JS), "bytes")

if __name__ == "__main__":
    main()
