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
t("the bundle carries the whole book, and says so", () => {
  assert.strictEqual(BOOK.meta.total_in_book, 291);
  assert.strictEqual(index.count, 291, "expected all 291 sections, got " + index.count);
  assert.strictEqual(BOOK.meta.recovered, index.count);
  assert.deepStrictEqual(BOOK.meta.missing, []);
  const said = R.coverage(BOOK.meta).sentence;
  assert.ok(/Every section is present/.test(said), "coverage must say the book is complete: " + said);
});

t("every section names its source, and the bundle beats the best single scan", () => {
  const labels = (BOOK.meta.scans || []).map(s => s.label);
  assert.ok(labels.length >= 2, "expected several sources, got " + JSON.stringify(labels));
  for (const s of BOOK.sections) {
    assert.ok(labels.includes(s.from), "§" + s.n + " has no recorded source (" + s.from + ")");
  }
  const best = Math.max(...(BOOK.meta.scans || []).filter(s => s.role === "scan").map(s => s.sections));
  assert.ok(index.count > best,
    "the assembled bundle (" + index.count + ") must beat the best single source (" + best + ")");
});

t("the transcription is corroborated by the scans, section by section", () => {
  const v = BOOK.meta.verification;
  assert.ok(v && typeof v.median === "number", "the bundle must carry a verification figure");
  assert.ok(v.median >= 0.9, "median corroboration must be high, got " + v.median);
  assert.ok(v.min >= 0.6, "no section may fall below the acceptance floor, got " + v.min);
  assert.strictEqual(v.sections_checked, 291);
  for (const s of BOOK.sections) {
    assert.ok(s.corroboration >= 0.6, "§" + s.n + " was accepted below the floor (" + s.corroboration + ")");
  }
});

t("every carried section is numbered, ordered and non-empty", () => {
  let prev = 0;
  for (const s of BOOK.sections) {
    assert.ok(s.n > prev, "sections must ascend: " + s.n + " after " + prev);
    prev = s.n;
    assert.ok(s.text.length >= 40, "§" + s.n + " is too short to be a section");
  }
});

t("a gap, if one existed, is named and never renumbered (fixture: a bundle with §7 absent)", () => {
  const holed = { total_in_book: 291, recovered: 2, missing: [7] };
  const said = R.coverage(holed).sentence;
  assert.ok(/could not be read/.test(said), "the coverage sentence must admit a gap: " + said);
  assert.ok(said.includes("§7"), "it must name the missing section: " + said);
  assert.ok(said.includes("2 of the book's 291"), "and say how many it does carry: " + said);
});

/* ---------- Done means #1: one-section phrase, returned first ---------- */
function phraseInExactlyOneSection() {
  // walk a few sections until a three-word phrase that occurs in exactly one is found
  for (const seed of BOOK.sections.slice(0, 40)) {
    const words = seed.text.split(/\s+/).filter(w => w.length > 6);
    for (let i = 0; i + 3 < words.length; i++) {
      const phrase = words.slice(i, i + 3).join(" ").replace(/[^\w\s]/g, "");
      if (phrase.length < 12) continue;
      const hits = BOOK.sections.filter(s => R.norm(s.text).includes(R.norm(phrase)));
      if (hits.length === 1) return { phrase, n: hits[0].n };
    }
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

t("the notes printed with a section are kept apart from its text", () => {
  const one = index.byNumber[1];
  assert.ok(one, "§1 must be in the bundle");
  assert.ok(!/His mission is not/.test(one.text), "the footnote must not run into the text");
  assert.ok(one.notes.length >= 1, "§1 must carry its printed note");
  assert.ok(/His mission is not/.test(one.notes[0]), "the note must be the note");
  const withNotes = BOOK.sections.filter(s => s.notes && s.notes.length).length;
  assert.ok(withNotes > 50, "expected the book's notes, got " + withNotes + " sections with notes");
});

t("a note is searchable — it is part of what the reader carries", () => {
  const res = R.search(index, "sick humanity sighs in vain");
  assert.ok(res.ok && res.results.length >= 1, "a phrase from a printed note must be findable");
});

/* ---------- browsing: the list, and next/previous ---------- */
t("the section list is the bundle, in order, with no duplicates", () => {
  const nums = R.numbers(index);
  assert.strictEqual(nums.length, index.count);
  for (let i = 1; i < nums.length; i++) assert.ok(nums[i] > nums[i - 1], "list must ascend");
});

t("next/previous step over a gap instead of stopping at it (fixture: §7 absent)", () => {
  const holed = R.createIndex(BOOK.sections.filter(s => s.n !== 7));
  assert.strictEqual(R.step(holed, 6, 1), 8, "from §6 next must be §8, not the missing §7");
  assert.strictEqual(R.step(holed, 8, -1), 6, "and back again");
});

t("the ends of the book are ends: no previous before the first, no next after the last", () => {
  const nums = R.numbers(index);
  assert.strictEqual(R.step(index, nums[0], -1), null);
  assert.strictEqual(R.step(index, nums[nums.length - 1], 1), null);
});

t("asking for a section that is not carried lands on the nearest one after it", () => {
  const holed = R.createIndex(BOOK.sections.filter(s => s.n !== 7));
  assert.strictEqual(R.step(holed, 7, 1), 8);
});

/* ---------- one edition, one translation ---------- */
t("every scan used declares the SIXTH edition in Boericke's translation", () => {
  const scans = BOOK.meta.scans || [];
  assert.ok(scans.length >= 2);
  for (const s of scans) {
    assert.ok(/sixth edition/i.test(s.edition), s.label + " must be the sixth edition");
    assert.ok(/boericke/i.test(s.edition), s.label + " must be Boericke's translation");
    if (s.role === "scan") {
      assert.ok(/SIXTH EDITION/.test((s.edition_evidence || "").toUpperCase()),
        s.label + " must carry its own front-matter evidence");
    }
    assert.ok(!/fifth edition/i.test(s.edition), s.label + " must not be a fifth-edition scan");
  }
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
