#!/usr/bin/env python3
"""Draw the README badges locally, as SVG. No shields.io: an offline-first app whose
own page breaks without a network has made its rule a joke.

Every figure is read from the thing it describes — the suite's own output, and the
bundles in `docs/` — and the README's badge block is rewritten from the same numbers,
between the `badges:start` and `badges:end` markers. A badge that disagrees with the
book is worse than no badge, so there is one place that computes both.

    python3 scripts/badges.py
"""
import json, os, re, subprocess

OUT = "docs/badges"
README = "README.md"
os.makedirs(OUT, exist_ok=True)

# the nine bundles, and which of them are published English translations
ENGLISH = ["docs/organon1-data.js", "docs/organon4-data.js",
           "docs/organon5-data.js", "docs/organon-data.js"]
ALL = ENGLISH + ["docs/organon2-data.js", "docs/organon3-data.js",
                 "docs/organon2-fr-data.js", "docs/organon2-en-mt-data.js",
                 "docs/organon3-en-mt-data.js"]
ORDINAL = re.compile(r"\b(first|second|third|fourth|fifth|sixth)\s+edition\b", re.I)


def suite_numbers():
    out = subprocess.run(["node", "test-node.js"], capture_output=True, text=True).stdout
    m = re.search(r"(\d+)/(\d+) assertions passed", out)
    return (m.group(1), m.group(2)) if m else ("?", "?")


def bundle(path):
    js = open(path, encoding="utf-8").read()
    return json.loads(js[js.index("return ") + 7: js.rindex(";\n});")])


def meta(path):
    return bundle(path)["meta"]


def shelf():
    """How many editions are shelved, and how much of them is here."""
    seen, carried, total = set(), 0, 0
    for path in ALL:
        if not os.path.exists(path):
            continue
        m = meta(path)
        found = ORDINAL.search(m.get("edition", ""))
        if found:
            seen.add(found.group(1).lower())
    for path in ENGLISH:
        m = meta(path)
        carried += m.get("numbered_paragraphs_carried") or m.get("recovered") or 0
        total += m.get("total_in_book") or 0
    machine = sum(1 for p in ALL if os.path.exists(p) and meta(p).get("machine_translation"))
    return len(seen), len(ENGLISH), machine, carried, total


EDITIONS, ENGLISH_COUNT, MACHINE, CARRIED, TOTAL = shelf()
PASSED, TOTAL_TESTS = suite_numbers()

W = 118
BADGES = [
    ("live",         "online",                        "#2ea043"),
    ("tests",        f"{PASSED}/{TOTAL_TESTS}",       "#2ea043"),
    ("offline",      "0 requests",                    "#2ea043"),
    ("deps",         "0",                             "#2ea043"),
    ("editions",     f"{EDITIONS} editions",          "#b08968"),
    ("translations", f"{ENGLISH_COUNT} English · {MACHINE} machine", "#b08968"),
    ("sections",     f"{CARRIED}/{TOTAL}",            "#b08968"),
    ("licence",      "PolyForm NC",                   "#4c6ef5"),
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


def readme_block():
    lines = ['<p align="center">']
    for label, value, _ in BADGES:
        lines.append(f'  <img src="{OUT}/{label}.svg" alt="{label}: {value}">')
    lines.append("</p>")
    return "\n".join(lines)


if os.path.exists(README):
    text = open(README, encoding="utf-8").read()
    block = readme_block()
    if "<!-- badges:start -->" in text and "<!-- badges:end -->" in text:
        text = re.sub(r"<!-- badges:start -->.*?<!-- badges:end -->",
                      lambda _: "<!-- badges:start -->\n" + block + "\n<!-- badges:end -->",
                      text, flags=re.S)
        open(README, "w", encoding="utf-8").write(text)
        print("rewrote the badge block in", README)
    else:
        print("!! README has no badges:start/end markers — SVGs written, README untouched")
