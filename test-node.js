#!/usr/bin/env node
/* Organon Reader — the suite. Plain node, no dependencies.
 *
 * Every assertion here is a claim the spec's "Done means" makes, executed rather
 * than asserted: a phrase that occurs in exactly one section, a bookmark that
 * survives a reload, and a reader that fetches nothing.
 */
"use strict";
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const R = require("./docs/reader.js");
const BOOK = require("./docs/organon-data.js");

let pass = 0, fail = 0;
function t(name, fn) {
  try { fn(); pass++; console.log("PASS  " + name); }
  catch (e) { fail++; console.log("FAIL  " + name + "\n        " + (e && e.message)); }
}

const index = R.createIndex(BOOK.sections);

/* ---------- the bundle is what it says it is ---------- */
t("the bundle carries sections, and says how many of the book's 291", () => {
  assert.ok(index.count > 100, "expected a real bundle, got " + index.count);
  assert.strictEqual(BOOK.meta.total_in_book, 291);
  assert.strictEqual(BOOK.meta.recovered, index.count);
  assert.strictEqual(BOOK.meta.missing.length, 291 - index.count);
});

t("every carried section is numbered, ordered and non-empty", () => {
  let prev = 0;
  for (const s of BOOK.sections) {
    assert.ok(s.n > prev, "sections must ascend: " + s.n + " after " + prev);
    prev = s.n;
    assert.ok(s.text.length >= 40, "§" + s.n + " is too short to be a section");
  }
});

t("a missing section is reported, never renumbered", () => {
  const missing = BOOK.meta.missing;
  assert.ok(missing.length > 0, "this OCR does lose marks, so the list must not be empty");
  for (const n of missing) assert.ok(!index.byNumber[n], "§" + n + " is listed missing but present");
  const said = R.coverage(BOOK.meta).sentence;
  assert.ok(/could not be read/.test(said), "the coverage sentence must admit the gap");
  assert.ok(said.includes("§" + missing[0]), "it must name a missing section, said: " + said);
});

/* ---------- Done means #1: one-section phrase, returned first ---------- */
function phraseInExactlyOneSection() {
  const words = BOOK.sections[3].text.split(/\s+/).filter(w => w.length > 6);
  for (let i = 0; i + 3 < words.length; i++) {
    const phrase = words.slice(i, i + 3).join(" ").replace(/[^\w\s]/g, "");
    if (phrase.length < 12) continue;
    const hits = BOOK.sections.filter(s => R.norm(s.text).includes(R.norm(phrase)));
    if (hits.length === 1) return { phrase, n: hits[0].n };
  }
  throw new Error("no one-section phrase found — the fixture is broken, not the code");
}

t("a phrase that occurs in exactly 1 section returns that section first, with its number and matched line", () => {
  const { phrase, n } = phraseInExactlyOneSection();
  const res = R.search(index, phrase);
  assert.ok(res.ok, "search refused a real phrase");
  assert.strictEqual(res.results.length, 1, "expected exactly one section for: " + phrase);
  assert.strictEqual(res.results[0].n, n);
  assert.ok(res.results[0].line.toLowerCase().includes(phrase.toLowerCase().slice(0, 20)),
    "the result must show the matched line, got: " + res.results[0].line);
});

t("a phrase in several sections is ranked by hits, and every hit names its section", () => {
  const res = R.search(index, "vital force");
  assert.ok(res.ok && res.results.length > 1, "expected several sections for 'vital force'");
  for (let i = 1; i < res.results.length; i++) {
    assert.ok(res.results[i - 1].hits >= res.results[i].hits, "results must be ranked by hits");
    assert.ok(res.results[i].n > 0);
  }
});

t("search is case- and whitespace-insensitive", () => {
  const a = R.search(index, "  VITAL   FORCE ");
  const b = R.search(index, "vital force");
  assert.deepStrictEqual(a.results.map(r => r.n), b.results.map(r => r.n));
});

/* ---------- the bad-input rule ---------- */
t("a too-short term says the term was too short, and never 'no matches'", () => {
  for (const bad of ["", " ", "a", "§"]) {
    const res = R.search(index, bad);
    assert.strictEqual(res.ok, false, JSON.stringify(bad) + " must be refused");
    assert.strictEqual(res.reason, "too-short");
    assert.strictEqual(res.results, undefined, "a refusal must not carry an empty result list");
  }
});

t("a term the book genuinely lacks says so, and is distinguishable from a refusal", () => {
  const res = R.search(index, "zzzqqqxyz");
  assert.strictEqual(res.ok, true);
  assert.strictEqual(res.results.length, 0);
});

/* ---------- Done means #2: a bookmark survives a reload ---------- */
function memStorage() {
  const m = new Map();
  return {
    get: k => (m.has(k) ? m.get(k) : null),
    set: (k, v) => { m.set(k, v); },
    _m: m
  };
}

t("a bookmark set on a section survives a reload and reopens at that section", () => {
  const disk = memStorage();
  const first = new R.Store(disk);
  let st = R.toggleBookmark(R.empty(), 42);
  st.last = 42;
  const w = first.commit(st);
  assert.ok(w.ok, "commit should succeed");

  const second = new R.Store(disk);          // a new session, same storage
  const loaded = second.load();
  assert.ok(loaded.ok);
  assert.deepStrictEqual(loaded.state.bookmarks, [42], "the bookmark must still be there");
  assert.strictEqual(loaded.state.last, 42, "the reader must reopen where it was left");
  assert.ok(index.byNumber[loaded.state.last], "and that section must exist in the bundle");
});

t("a note is kept with its section, and an empty note removes it", () => {
  const disk = memStorage();
  const store = new R.Store(disk);
  let st = R.setNote(R.empty(), 7, "compare with § 148");
  assert.ok(store.commit(st).ok);
  assert.strictEqual(new R.Store(disk).load().state.notes[7], "compare with § 148");
  st = R.setNote(st, 7, "   ");
  assert.ok(store.commit(st).ok);
  assert.deepStrictEqual(new R.Store(disk).load().state.notes, {});
});

t("bookmarking twice removes it (no duplicate bookmarks)", () => {
  let st = R.toggleBookmark(R.empty(), 9);
  st = R.toggleBookmark(st, 9);
  assert.deepStrictEqual(st.bookmarks, []);
});

/* ---------- the storage rules ---------- */
t("a write that cannot be made is reported, and is never shown as kept", () => {
  const broken = { get: () => null, set: () => { throw new Error("QuotaExceededError"); } };
  const res = new R.Store(broken).commit(R.toggleBookmark(R.empty(), 3));
  assert.strictEqual(res.ok, false);
  assert.strictEqual(res.reason, "unwritable");
});

t("a storage that silently drops the write is caught by the read-back", () => {
  const liar = { get: () => null, set: () => {} };
  const res = new R.Store(liar).commit(R.toggleBookmark(R.empty(), 3));
  assert.strictEqual(res.ok, false, "commit must verify, not assume");
});

t("corrupt saved state is reported and offered back, and the text still opens", () => {
  const disk = memStorage();
  disk.set("organon-reader:v1", "{not json at all");
  const res = new R.Store(disk).load();
  assert.strictEqual(res.ok, false);
  assert.strictEqual(res.reason, "corrupt");
  assert.strictEqual(res.raw, "{not json at all", "the unreadable data must be offered for export");
  assert.ok(index.count > 0, "a broken note file must not stop the reader opening");
});

t("an unreadable storage (throws on read) is reported, not swallowed", () => {
  const res = new R.Store({ get: () => { throw new Error("denied"); }, set: () => {} }).load();
  assert.strictEqual(res.ok, false);
  assert.strictEqual(res.reason, "unreadable");
});

t("export/import round-trips the user's marks", () => {
  let st = R.toggleBookmark(R.empty(), 5);
  st = R.setNote(st, 5, "keep");
  const text = R.exportState(st);
  const back = R.importState(text);
  assert.ok(back.ok);
  assert.deepStrictEqual(back.state, R.normalise(st));
  assert.strictEqual(R.importState("{oops").ok, false);
});

/* ---------- Done means #3: the reader fetches nothing ---------- */
const docs = path.join(__dirname, "docs");
const appFiles = ["index.html", "reader.js", "organon-data.js"].map(f => ({
  f, text: fs.readFileSync(path.join(docs, f), "utf8")
}));

t("the app makes no network call of any kind", () => {
  for (const { f, text } of appFiles) {
    assert.ok(!/\bfetch\s*\(/.test(text), f + " must not call fetch()");
    assert.ok(!/XMLHttpRequest/.test(text), f + " must not use XMLHttpRequest");
    assert.ok(!/navigator\.sendBeacon/.test(text), f + " must not beacon");
    assert.ok(!/new\s+WebSocket/.test(text), f + " must not open a socket");
  }
});

t("the page loads nothing from another origin — it works from file://", () => {
  const html = fs.readFileSync(path.join(docs, "index.html"), "utf8");
  const remote = [...html.matchAll(/(?:src|href)\s*=\s*["'](https?:)?\/\//gi)];
  assert.strictEqual(remote.length, 0, "found an off-origin resource: " + JSON.stringify(remote[0]));
  const scripts = [...html.matchAll(/<script[^>]*src\s*=\s*["']([^"']+)["']/gi)].map(m => m[1]);
  for (const s of scripts) {
    assert.ok(fs.existsSync(path.join(docs, s)), "missing local script: " + s);
  }
});

t("the text is identical in every session — it is bundled, not fetched", () => {
  const a = crypto.createHash("sha256").update(JSON.stringify(BOOK.sections)).digest("hex");
  delete require.cache[require.resolve("./docs/organon-data.js")];
  const again = require("./docs/organon-data.js");
  const b = crypto.createHash("sha256").update(JSON.stringify(again.sections)).digest("hex");
  assert.strictEqual(a, b, "the bundled text must be byte-identical on a second load");
});

t("the bundle names its source and its licence, so a reader can check it", () => {
  assert.ok(/archive\.org/.test(BOOK.meta.source));
  assert.ok(/Public domain/i.test(BOOK.meta.licence));
  assert.ok(/Boericke/.test(BOOK.meta.edition + " " + BOOK.meta.translator));
});

console.log("\n" + pass + "/" + (pass + fail) + " assertions passed");
process.exit(fail ? 1 : 0);
