#!/usr/bin/env python3
"""Draw the README badges locally, as SVG. No shields.io: an offline-first app whose
own page breaks without a network has made its rule a joke.

    python3 scripts/badges.py
"""
import os, re, subprocess

OUT = "docs/badges"
os.makedirs(OUT, exist_ok=True)

def suite_numbers():
    out = subprocess.run(["node", "test-node.js"], capture_output=True, text=True).stdout
    m = re.search(r"(\d+)/(\d+) assertions passed", out)
    return (m.group(1), m.group(2)) if m else ("?", "?")

def sections():
    js = open("docs/organon-data.js", encoding="utf-8").read()
    import json
    data = json.loads(js[js.index("return ") + 7: js.rindex(";\n});")])
    return data["meta"]["recovered"], data["meta"]["total_in_book"]

PASSED, TOTAL = suite_numbers()
GOT, OF = sections()

W = 118
BADGES = [
    ("live",      "online",        "#2ea043"),
    ("tests",     f"{PASSED}/{TOTAL}", "#2ea043"),
    ("offline",   "0 requests",    "#2ea043"),
    ("deps",      "0",             "#2ea043"),
    ("sections",  f"{GOT}/{OF}",   "#b08968"),
    ("licence",   "PolyForm NC",   "#4c6ef5"),
]

TPL = """<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" role="img" aria-label="{label}: {value}">
  <title>{label}: {value}</title>
  <linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>
  <rect width="{w}" height="20" rx="3" fill="#0f1115"/>
  <rect x="{lx}" width="{rx}" height="20" fill="{colour}"/>
  <rect width="{w}" height="20" rx="3" fill="url(#s)"/>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
    <text x="{lcx}" y="14">{label}</text>
    <text x="{rcx}" y="14">{value}</text>
  </g>
</svg>
"""

for label, value, colour in BADGES:
    lw = 8 * len(label) + 12
    rw = 7 * len(value) + 12
    w = lw + rw
    svg = TPL.format(w=w, label=label, value=value, colour=colour, lx=lw, rx=rw,
                     lcx=lw // 2, rcx=lw + rw // 2)
    open(os.path.join(OUT, label + ".svg"), "w", encoding="utf-8").write(svg)
    print("wrote", os.path.join(OUT, label + ".svg"))
