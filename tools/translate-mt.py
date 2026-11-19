#!/usr/bin/env python3
"""translate-mt.py — build-time machine translation of the German second and third editions.

The second and third editions have no English translation, and this script does not pretend
otherwise. It sends each German block to Google's translation endpoint **once, at build
time**, and writes the result into its own bundle: `docs/organon2-en-mt-data.js` and
`docs/organon3-en-mt-data.js`.

That bundle is quarantined, not merged:

  * it is a separate file with a separate store key, so a bookmark made in the machine
    edition cannot land in a published one;
  * every section records `mt: true` and the engine, and the reader labels it "machine
    translation" on the section and at the top of the book;
  * the app still loads it from disk, so the reader makes no network call, ever — the
    translation happens here, in the build, and the page ships with the result;
  * the German beside it stays the edition; this is a reading aid for a text that has no
    translation, and it says so in `meta`.

The endpoint is Google's public `translate_a/single` interface, which needs no key. It is
rate-limited politely, chunks long paragraphs below its limit, and retries. Results are
cached in `$ORGANON_MT_CACHE` so a rebuild does not re-send text it already translated.

    ORGANON_MT_CACHE=/tmp/mt-cache.json python3 tools/translate-mt.py
"""
import hashlib, json, os, re, sys, time, urllib.parse, urllib.request

API = "https://translate.googleapis.com/translate_a/single"
LIMIT = 4500
CACHE = os.environ.get("ORGANON_MT_CACHE", "/tmp/organon-mt-cache.json")

BOOKS = [
    {"src": "organon2-sections.json", "out": "docs/organon2-en-mt-data.js",
     "global": "ORGANON2MT", "de": "docs/organon2-data.js",
     "edition": "Second edition (1819), machine translation of Hahnemann's German",
     "source_title": "Organon der Heilkunst (1819)"},
    {"src": "organon3-sections.json", "out": "docs/organon3-en-mt-data.js",
     "global": "ORGANON3MT", "de": "docs/organon3-data.js",
     "edition": "Third edition (1824), machine translation of Hahnemann's German",
     "source_title": "Organon der Heilkunst (1824)"},
]

cache = {}
if os.path.exists(CACHE):
    try:
        cache = json.load(open(CACHE, encoding="utf-8"))
    except Exception:
        cache = {}


def chunks(text, limit=LIMIT):
    """Split at sentence ends where possible, never in the middle of a word."""
    out, buf = [], ""
    for part in re.split(r"(?<=[.!?;:])\s+", text):
        while len(part) > limit:
            cut = part.rfind(" ", 0, limit)
            cut = cut if cut > 0 else limit
            if buf:
                out.append(buf)
                buf = ""
            out.append(part[:cut])
            part = part[cut:].lstrip()
        if len(buf) + len(part) + 1 > limit:
            out.append(buf)
            buf = part
        else:
            buf = (buf + " " + part).strip()
    if buf:
        out.append(buf)
    return [c for c in out if c.strip()]


def translate(text, tries=5):
    """One paragraph, in chunks. Cached by the source text itself."""
    out = []
    for piece in chunks(text):
        key = hashlib.sha256(piece.encode("utf-8")).hexdigest()
        if key in cache:
            out.append(cache[key])
            continue
        query = urllib.parse.urlencode({"client": "gtx", "sl": "de", "tl": "en",
                                        "dt": "t", "q": piece})
        got = None
        for attempt in range(tries):
            try:
                req = urllib.request.Request(API + "?" + query,
                                             headers={"User-Agent": "Mozilla/5.0 (organon-reader build)"})
                with urllib.request.urlopen(req, timeout=45) as r:
                    data = json.loads(r.read().decode("utf-8"))
                got = "".join(seg[0] for seg in data[0] if seg and seg[0])
                break
            except Exception as e:                       # noqa: BLE001 - transient by nature
                wait = 1.5 * (attempt + 1)
                print(f"    retry {attempt + 1}/{tries} after {type(e).__name__}: {wait:.1f}s")
                time.sleep(wait)
        if got is None:
            raise SystemExit("translation endpoint failed; nothing was written")
        cache[key] = got
        out.append(got)
        time.sleep(0.25)
        if len(cache) % 25 == 0:
            json.dump(cache, open(CACHE, "w", encoding="utf-8"))
    return re.sub(r"\s{2,}", " ", " ".join(out)).strip()


def main():
    for book in BOOKS:
        if not os.path.exists(book["src"]):
            print(f"  !! {book['src']} missing — run the German build first")
            continue
        src = json.load(open(book["src"], encoding="utf-8"))
        de = json.load(open(book["de"].replace("docs/", "").replace("-data.js", "-sections.json"),
                            encoding="utf-8")) if os.path.exists(
            book["de"].replace("docs/", "").replace("-data.js", "-sections.json")) else src
        sections = []
        print(f"  {book['src']}: {len(src['sections'])} blocks to translate")
        for k, sec in enumerate(src["sections"], 1):
            english = translate(sec["text"])
            sections.append({"n": sec["n"], "to": sec.get("to", sec["n"]), "text": english,
                             "notes": [], "from": "machine translation", "mt": True,
                             "translated_from": sec.get("from"),
                             "corroboration": None, "accepted": True})
            if k % 25 == 0:
                print(f"    {k}/{len(src['sections'])}")
        meta = {
            "title": de["meta"]["title"],
            "edition": book["edition"],
            "translator": "Google Translate (machine translation, built " + time.strftime("%Y-%m-%d") + ")",
            "language": "en",
            "machine_translation": {
                "generated": True,
                "engine": "Google Translate, translate_a/single (no key, build time only)",
                "built": time.strftime("%Y-%m-%d"),
                "source_edition": de["meta"]["edition"],
                "source_language": "de",
                "source_bundle": os.path.basename(book["de"]),
                "paragraphs": len(sections),
                "caveat": ("This is generated text, not a translation anybody published. No "
                           "English translation of this edition exists. It is offered so the "
                           "edition can be read in English at all, is kept in its own bundle, "
                           "and is labelled wherever it appears. It is not Hahnemann's words "
                           "and it is not a substitute for the German printed beside it."),
            },
            "source": de["meta"]["source"],
            "licence": ("The German text is public domain (Hahnemann d. 1843). The machine "
                        "translation is generated, carries no translator's copyright, and is "
                        "offered as a reading aid only."),
            "total_in_book": de["meta"]["total_in_book"],
            "recovered": len(sections),
            "missing": de["meta"]["missing"],
            "blocks": len(sections),
            # the German book's figures, because a range block stands for a run of
            # numbered paragraphs and a machine rendering of it covers the same run
            "numbered_paragraphs_carried": de["meta"].get("numbered_paragraphs_carried"),
            "status": "machine translation, generated at build time; not a published translation",
            "verification": {
                "method": "none — generated text cannot be corroborated against a source that does not exist",
                "median": None, "min": None, "sections_checked": 0, "floor": None,
                "refused": [],
                "note": ("Every section is a machine rendering of the German block with the same "
                         "number. It inherits that block's gaps and adds its own errors; the "
                         "German is the authority."),
            },
            "scans": de["meta"].get("scans", []),
            "notes": [
                "Machine translation of the German text, made once when the bundle was built. "
                "It is not Hahnemann's English and no publisher ever issued it.",
                "It exists because the second and third editions were never translated into "
                "English. The French of 1824 is bundled as it was printed; this is the only "
                "English these editions can have, and it is labelled as generated.",
                "The reader still fetches nothing: the translation was made at build time and "
                "ships inside this file.",
            ],
            "generator": "tools/translate-mt.py",
        }
        bundle = {"meta": meta, "sections": sections}
        body = json.dumps(bundle, ensure_ascii=False, separators=(",", ":"))
        js = ("/* MACHINE TRANSLATION — generated text, not a published translation.\n"
              " * " + book["edition"] + ".\n"
              " * Built by tools/translate-mt.py at build time; the reader fetches nothing.\n"
              " * The German bundle is the edition; this is a reading aid. */\n"
              "(function (root, factory) {\n"
              '  if (typeof module === "object" && module.exports) module.exports = factory();\n'
              "  else root." + book["global"] + " = factory();\n"
              '})(typeof self !== "undefined" ? self : this, function () {\n'
              "  return " + body + ";\n});\n")
        open(book["out"], "w", encoding="utf-8").write(js)
        print(f"  wrote {book['out']} {len(js)} bytes, {len(sections)} blocks")
    json.dump(cache, open(CACHE, "w", encoding="utf-8"))


if __name__ == "__main__":
    main()
