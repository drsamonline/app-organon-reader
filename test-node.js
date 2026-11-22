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
const { execFileSync } = require("child_process");

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
// The reader lives at docs/play/ and docs/index.html is its title page. These
// assertions are about the APP, so they read the app: pointing them at the
// landing page is how they went red on a repository that was working.
const appPage = path.join(docs, "play", "index.html");
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

t("the title page leads to the reader, so moving the app cannot orphan it", () => {
  const html = fs.readFileSync(path.join(docs, "index.html"), "utf8");
  assert.ok(/href\s*=\s*["']play\/["']/.test(html), "docs/index.html must link to play/");
  assert.ok(fs.existsSync(appPage), "docs/play/index.html is missing");
});

t("the app loads nothing from another origin — it works from file://", () => {
  // The APP, not the title page: the title page carries outbound links to the
  // project's own pages on purpose. What must never leave the machine is a
  // resource the reader loads.
  const html = fs.readFileSync(appPage, "utf8");
  const remote = [...html.matchAll(/(?:src|href)\s*=\s*["'](https?:)?\/\//gi)];
  assert.strictEqual(remote.length, 0, "found an off-origin resource: " + JSON.stringify(remote[0]));
  const scripts = [...html.matchAll(/<script[^>]*src\s*=\s*["']([^"']+)["']/gi)].map(m => m[1]);
  for (const s of scripts) {
    // Relative to the PAGE, not to docs/: the app sits in play/ and reaches its
    // data with ../organon-data.js. Resolving against docs/ looked for the file
    // one directory too high and called a present script missing.
    assert.ok(fs.existsSync(path.join(path.dirname(appPage), s)), "missing local script: " + s);
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

/* ---------- the second edition ---------- */
const BOOK5 = require("./docs/organon5-data.js");
const index5 = R.createIndex(BOOK5.sections);

t("the fifth edition carries its own book, corroborated the same way", () => {
  assert.strictEqual(index5.count, BOOK5.sections.length);
  assert.strictEqual(BOOK5.meta.recovered, index5.count);
  assert.deepStrictEqual(BOOK5.meta.missing, []);
  assert.ok(/fifth edition/i.test(BOOK5.meta.edition), BOOK5.meta.edition);
  assert.ok(/Dudgeon/.test(BOOK5.meta.translator), BOOK5.meta.translator);
  const v = BOOK5.meta.verification;
  assert.ok(v && typeof v.median === "number", "the fifth bundle must carry a verification figure");
  assert.ok(v.median >= 0.9, "median corroboration must be high, got " + v.median);
  assert.ok(v.min >= 0.6, "no section may fall below the acceptance floor, got " + v.min);
  assert.strictEqual(v.sections_checked, index5.count);
  for (const s of BOOK5.sections) {
    assert.ok(s.corroboration >= 0.6, "§" + s.n + " was accepted below the floor (" + s.corroboration + ")");
  }
});

t("the fifth edition is never corroborated by a sixth-edition scan", () => {
  const scans = BOOK5.meta.scans || [];
  assert.ok(scans.length >= 1, "expected at least one scan");
  for (const s of scans) {
    assert.ok(/fifth edition/i.test(s.edition), s.label + " must be the fifth edition");
    assert.ok(/dudgeon/i.test(s.edition), s.label + " must be Dudgeon's translation");
    assert.ok(!/boericke/i.test(s.edition), s.label + " must not be a Boericke scan");
    assert.ok(/fifth/i.test(s.edition_evidence || ""), s.label + " must carry its edition evidence");
  }
});

t("the two editions are different books, and the bundle says where", () => {
  const six = {}, five = {};
  BOOK.sections.forEach(s => { six[s.n] = R.norm(s.text); });
  BOOK5.sections.forEach(s => { five[s.n] = R.norm(s.text); });
  let differ = 0, only5 = 0;
  for (const n of Object.keys(five)) {
    if (!(n in six)) only5++;
    else if (six[n] !== five[n]) differ++;
  }
  assert.ok(differ > 20, "expected many reworded sections, got " + differ);
  assert.ok(only5 > 0, "expected at least one section the sixth does not carry");
  for (const s of BOOK5.sections) {
    assert.strictEqual(typeof s.differsFromSixth, "boolean", "§" + s.n + " must record whether it differs");
    assert.strictEqual(typeof s.absentFromSixth, "boolean", "§" + s.n + " must record whether the sixth lacks it");
  }
});

t("the fifth edition is searchable on its own terms", () => {
  const res = R.search(index5, "vital force");
  assert.ok(res.ok && res.results.length > 1, "expected several sections for 'vital force'");
  assert.ok(res.results[0].n > 0);
});

t("all nine books are bundled and none is fetched", () => {
  const html = fs.readFileSync(appPage, "utf8");
  for (const f of ["organon-data.js", "organon5-data.js", "organon4-data.js", "organon1-data.js",
                   "organon2-data.js", "organon3-data.js", "organon2-fr-data.js",
                   "organon2-en-mt-data.js", "organon3-en-mt-data.js"]) {
    assert.ok(html.includes(f), "the page must load " + f);
    assert.ok(fs.existsSync(path.join(docs, f)), "missing bundled file: " + f);
  }
  assert.ok(/id="edition"/.test(html), "the page must offer an edition selector");
});

t("each edition keeps its own bookmarks, so a note cannot land in the wrong book", () => {
  const html = fs.readFileSync(appPage, "utf8");
  const keys = [...html.matchAll(/store:\s*"([^"]+)"/g)].map(m => m[1]);
  assert.strictEqual(keys.length, 9, "expected one store key per edition, got " + JSON.stringify(keys));
  assert.strictEqual(new Set(keys).size, keys.length, "the editions must not share a store key");
});

/* ---------- the first and the fourth edition ---------- */
const BOOK1 = require("./docs/organon1-data.js");
const BOOK4 = require("./docs/organon4-data.js");
const index1 = R.createIndex(BOOK1.sections);
const index4 = R.createIndex(BOOK4.sections);

function namedGapsAccurately(book, total) {
  const carried = new Set(book.sections.map(s => s.n));
  const expected = [];
  for (let n = 1; n <= total; n++) if (!carried.has(n)) expected.push(n);
  assert.deepStrictEqual(book.meta.missing, expected,
    "the missing list must be exactly the numbers the bundle does not carry");
  assert.strictEqual(book.meta.recovered, book.sections.length);
}

t("the first edition is Wheeler's 1913 translation, and says which sections it lost", () => {
  assert.strictEqual(BOOK1.meta.total_in_book, 271);
  assert.ok(/first edition/i.test(BOOK1.meta.edition), BOOK1.meta.edition);
  assert.ok(/Wheeler/.test(BOOK1.meta.translator), BOOK1.meta.translator);
  assert.ok(/Public domain/i.test(BOOK1.meta.licence));
  assert.ok(index1.count > 200, "expected most of the 271 aphorisms, got " + index1.count);
  namedGapsAccurately(BOOK1, 271);
  const v = BOOK1.meta.verification;
  assert.ok(v && v.median >= 0.9 && v.min >= 0.6, "corroboration must hold: " + JSON.stringify(v));
  assert.strictEqual(v.sections_checked, index1.count);
  const labels = BOOK1.meta.scans.map(s => s.label);
  for (const s of BOOK1.sections) {
    assert.ok(labels.includes(s.from), "§" + s.n + " has no recorded source (" + s.from + ")");
    assert.ok(s.corroboration >= 0.6, "§" + s.n + " was accepted below the floor");
  }
});

t("the first edition never claims to be another edition or translation", () => {
  for (const s of BOOK1.meta.scans) {
    assert.ok(/first edition/i.test(s.edition), s.label + " must be the first edition");
    assert.ok(/Wheeler/i.test(s.edition), s.label + " must be Wheeler's translation");
    assert.ok(!/Boericke|Dudgeon|Devrient/i.test(s.edition), s.label + " must not be another translation");
  }
});

t("the fourth edition is Devrient's 1833 translation, 292 paragraphs with gaps named", () => {
  assert.strictEqual(BOOK4.meta.total_in_book, 292);
  assert.ok(/fourth edition/i.test(BOOK4.meta.edition), BOOK4.meta.edition);
  assert.ok(/Devrient/.test(BOOK4.meta.translator), BOOK4.meta.translator);
  assert.ok(index4.count > 200, "expected most of the 292 aphorisms, got " + index4.count);
  namedGapsAccurately(BOOK4, 292);
  const v = BOOK4.meta.verification;
  assert.ok(v && v.median >= 0.9 && v.min >= 0.6, "corroboration must hold: " + JSON.stringify(v));
  const labels = BOOK4.meta.scans.map(s => s.label);
  for (const s of BOOK4.sections) {
    assert.ok(labels.includes(s.from), "§" + s.n + " has no recorded source (" + s.from + ")");
    assert.ok(s.corroboration >= 0.6, "§" + s.n + " was accepted below the floor");
  }
  for (const s of BOOK4.meta.scans) {
    assert.ok(/fourth edition/i.test(s.edition), s.label + " must be the fourth edition");
    assert.ok(/Devrient/i.test(s.edition), s.label + " must be Devrient's translation");
  }
});

t("the four editions are four different books, and none borrows another's text", () => {
  const firsts = {};
  BOOK1.sections.forEach(s => { firsts[s.n] = R.norm(s.text); });
  BOOK4.sections.forEach(s => { firsts[s.n] = R.norm(s.text); });
  let same = 0;
  BOOK.sections.forEach(s => { if (firsts[s.n] === R.norm(s.text)) same++; });
  assert.ok(same < 40, "the first/fourth editions must not be the sixth edition's text: " + same + " identical sections");
  assert.notStrictEqual(BOOK1.meta.total_in_book, BOOK4.meta.total_in_book);
  assert.ok(R.search(index1, "vital force").ok);
  assert.ok(R.search(index4, "miasm").ok, "the fourth edition carries the chronic miasms");
});

/* ---------- the second and third editions, their French, and the machine translation ---------- */
const BOOK2 = require("./docs/organon2-data.js");
const BOOK3 = require("./docs/organon3-data.js");
const BOOK2FR = require("./docs/organon2-fr-data.js");
const BOOK2MT = require("./docs/organon2-en-mt-data.js");
const BOOK3MT = require("./docs/organon3-en-mt-data.js");
const index2 = R.createIndex(BOOK2.sections);
const index3 = R.createIndex(BOOK3.sections);
const index2fr = R.createIndex(BOOK2FR.sections);
const index2mt = R.createIndex(BOOK2MT.sections);
const index3mt = R.createIndex(BOOK3MT.sections);

// the numbers a block stands for: §90–105 is one block covering sixteen numbers
t("a printed range is carried as a range, and every number it covers is covered", () => {
  for (const book of [BOOK2, BOOK3, BOOK2FR]) {
    const covered = new Set();
    for (const s of book.sections) {
      assert.ok(s.to >= s.n, "§" + s.n + " ends before it starts (" + s.to + ")");
      // the widest printed range is the 1819 list's §194–228 (34 numbers), whose start is
      // restored from the printed end of the entry before it; anything wider is a fault
      assert.ok(s.to - s.n <= 40, "§" + s.n + " claims an impossible range to " + s.to);
      for (let k = s.n; k <= s.to; k++) covered.add(k);
    }
    const expected = [];
    for (let n = 1; n <= book.meta.total_in_book; n++) if (!covered.has(n)) expected.push(n);
    assert.deepStrictEqual(book.meta.missing, expected,
      book.meta.edition + ": the missing list must be exactly the numbers no block covers");
    assert.strictEqual(book.meta.blocks, book.sections.length);
    assert.strictEqual(book.meta.numbered_paragraphs_carried, covered.size);
  }
});

t("the second edition is Hahnemann's German of 1819, and says it has no English translation", () => {
  assert.strictEqual(BOOK2.meta.total_in_book, 318);
  assert.strictEqual(BOOK2.meta.language, "de");
  assert.ok(/second edition/i.test(BOOK2.meta.edition), BOOK2.meta.edition);
  assert.ok(/1819/.test(BOOK2.meta.edition), BOOK2.meta.edition);
  assert.strictEqual(BOOK2.meta.english_translation_exists, false);
  assert.ok(index2.count > 80, "expected most of the 1819 blocks, got " + index2.count);
  assert.ok(BOOK2.meta.numbered_paragraphs_carried > 270,
    "expected ~280 of 318 numbered paragraphs, got " + BOOK2.meta.numbered_paragraphs_carried);
  assert.strictEqual(BOOK2.meta.part, "Inhaltsanzeige",
    "the 1819 German bundle carries the printed Inhaltsanzeige, and must say so");
  assert.ok(BOOK2.meta.notes.some(n => /Inhaltsanzeige/.test(n)),
    "the notes must say that the paragraphs themselves are not carried");
  for (const s of BOOK2.sections) {
    for (const r of s.numbers_from || []) {
      assert.ok(r.from && Object.keys(r).length >= 2,
        "§" + s.n + " restores a number and must record where it came from");
    }
  }
  // the second copy of the printing reads the range end the reading copy destroyed
  // (§181 — igS is §181–193 there); the figure counts the blocks that record it
  const fromSecond = BOOK2.sections.filter(s =>
    (s.numbers_from || []).some(r => /second copy/.test(r.from))).length;
  assert.strictEqual(BOOK2.meta.numbered_from_second_copy, fromSecond,
    "the recorded count must be the number of blocks that took a number from the second copy");
  assert.ok(fromSecond >= 1, "the second copy must settle at least one number, not none");
  // the 1819 list's local-ailment entry is §194–228, not §182–228: the entry before it
  // ends at §193 (second copy), so the restored start is 194. Keeping 182 was a fault.
  assert.strictEqual(index2.byNumber[181].to, 193, "§181 must end where the second copy reads it");
  assert.ok(index2.byNumber[194], "the local-ailment entry must start at §194");
  assert.strictEqual(index2.byNumber[194].to, 228, "and it ends at the printed 228");
  assert.ok(!BOOK2.sections.some(s => s.n === 182), "no block may begin at §182");
  assert.ok(/Public domain/i.test(BOOK2.meta.licence));
  for (const s of BOOK2.meta.scans) {
    assert.ok(/second edition/i.test(s.edition), s.label + " must be the second edition");
    assert.ok(!/Boericke|Dudgeon|Devrient/i.test(s.edition), s.label + " must not be a translation");
  }
});

// a rubric must not open with the fragment that stood for a lost number: `igS- Mafsregeln`
// is OCR, not Hahnemann's words. A printed sub-item such as §31's `I.` is prose and passes
// (it is followed by a full stop, not by the dash the fragment carried).
t("no 1819 rubric begins with the fragment that stood for a lost number", () => {
  for (const [book, label] of [[BOOK2, "§"], [BOOK2MT, "machine §"], [BOOK2FR, "French §"]]) {
    for (const s of book.sections) {
      assert.ok(!/^[0-9A-Za-z|!~?]{1,4}\s*[—–-]\s/.test(s.text),
        label + s.n + " begins with a lost-number fragment: " + JSON.stringify(s.text.slice(0, 40)));
    }
  }
});

t("the third edition is Hahnemann's German of 1824 and reads nearly whole", () => {
  assert.strictEqual(BOOK3.meta.total_in_book, 320);
  assert.strictEqual(BOOK3.meta.language, "de");
  assert.ok(/third edition/i.test(BOOK3.meta.edition), BOOK3.meta.edition);
  assert.strictEqual(BOOK3.meta.english_translation_exists, false);
  assert.ok(index3.count > 250, "expected nearly all 1824 blocks, got " + index3.count);
  assert.ok(BOOK3.meta.numbered_paragraphs_carried >= 300,
    "expected ~300 of 320 numbered paragraphs, got " + BOOK3.meta.numbered_paragraphs_carried);
  assert.strictEqual(BOOK3.meta.scans.length, 2, "two copies of the 1824 printing");
  for (const s of BOOK3.sections) {
    assert.ok(s.corroboration >= 0.6, "§" + s.n + " was accepted below the floor");
  }
});

t("the French is Brunnow's 1824 translation of the second edition, not generated text", () => {
  assert.strictEqual(BOOK2FR.meta.total_in_book, 318);
  assert.strictEqual(BOOK2FR.meta.language, "fr");
  assert.ok(/Brunnow/.test(BOOK2FR.meta.translator), BOOK2FR.meta.translator);
  assert.strictEqual(BOOK2FR.meta.machine_translation, null);
  assert.ok(index2fr.count > 250, "expected nearly all the French blocks, got " + index2fr.count);
  for (const s of BOOK2FR.sections) {
    assert.ok(s.mt !== true, "§" + s.n + " must not be marked as machine text");
  }
});

t("the machine translation is labelled generated everywhere, and is not the German", () => {
  for (const [book, german, index] of [[BOOK2MT, BOOK2, index2mt], [BOOK3MT, BOOK3, index3mt]]) {
    assert.ok(book.meta.machine_translation && book.meta.machine_translation.generated === true,
      "the bundle must declare itself machine-generated");
    assert.ok(/Google Translate/.test(book.meta.machine_translation.engine));
    assert.ok(book.meta.machine_translation.caveat.length > 80, "the caveat must say what it is");
    assert.strictEqual(book.meta.machine_translation.source_bundle,
      book === BOOK2MT ? "organon2-data.js" : "organon3-data.js",
      "the machine bundle must name the German bundle it was made from");
    assert.strictEqual(index.count, german.sections.length, "one translation per German block");
    assert.deepStrictEqual(book.meta.missing, german.meta.missing, "it inherits the German gaps");
    for (const s of book.sections) {
      assert.strictEqual(s.mt, true, "§" + s.n + " must be flagged as machine text");
      assert.ok(/machine translation/i.test(s.from), "§" + s.n + " must name its source as machine text");
    }
    const de = {};
    german.sections.forEach(s => { de[s.n] = R.norm(s.text); });
    let identical = 0;
    book.sections.forEach(s => { if (de[s.n] === R.norm(s.text)) identical++; });
    assert.ok(identical < 3, "the machine bundle must be translated, not copied: " + identical + " identical");
    assert.ok(R.search(index, "the").ok, "the machine text must be searchable like any other");
  }
});

t("the second and third editions are different books, and neither is the sixth", () => {
  assert.notStrictEqual(BOOK2.meta.total_in_book, BOOK3.meta.total_in_book);
  const six = {};
  BOOK.sections.forEach(s => { six[s.n] = R.norm(s.text); });
  let same = 0;
  BOOK3.sections.forEach(s => { if (six[s.n] === R.norm(s.text)) same++; });
  assert.strictEqual(same, 0, "German must not match the English sixth edition");
  assert.notStrictEqual(BOOK2.sections[0].text, BOOK3.sections[0].text,
    "the two German editions are separate readings from separate scans");
});

/* ---------- the provenance line, held for every section of every bundle ---------- */
// The reader prints this sentence under every section number; data/README.md says it does,
// and a line nobody executes is how it goes quietly wrong. Checked against the bundle that
// carries the section, so a row whose source label or figure drifts is caught here.
function checkProvenance(label, book) {
  const meta = book.meta;
  const scans = meta.scans || [];
  const scanCount = scans.filter(s => s.role === "scan").length;
  for (const s of book.sections) {
    const said = R.provenance(s, meta);
    assert.ok(said, label + " §" + s.n + " prints no provenance");
    assert.ok(!/undefined|\bnull\b|NaN/.test(said), label + " §" + s.n + " leaks a missing value: " + said);
    if (s.mt) {
      assert.ok(/machine translation of the German block/.test(said),
        label + " §" + s.n + " must say it is machine text: " + said);
      assert.ok(!/^text from the/.test(said), label + " §" + s.n + " must not read as published text: " + said);
      continue;
    }
    assert.ok(said.startsWith("text from the " + s.from + " "),
      label + " §" + s.n + " must name its source first: " + said);
    const src = scans.filter(x => x.label === s.from)[0];
    const kind = (src && src.role === "transcription") || /^MediT/.test(s.from) ? "transcription" : "scan";
    assert.ok(said.startsWith("text from the " + s.from + " " + kind + " "),
      label + " §" + s.n + " must say what kind of source it came from: " + said);
    if (s.corroboration == null) {
      assert.ok(!/corroborated/.test(said), label + " §" + s.n + " invents a figure: " + said);
    } else {
      assert.ok(said.includes("corroborated against " + scanCount + " scans of the same printing"),
        label + " §" + s.n + " must count the scans that checked it: " + said);
      assert.ok(said.includes(Math.round(s.corroboration * 100) + "% of its word-runs found verbatim"),
        label + " §" + s.n + " must print its own figure (" + s.corroboration + "): " + said);
    }
  }
}

for (const [label, book] of [
  ["sixth", BOOK], ["first", BOOK1], ["second", BOOK2], ["second (French)", BOOK2FR],
  ["second (machine)", BOOK2MT], ["third", BOOK3], ["third (machine)", BOOK3MT],
  ["fourth", BOOK4], ["fifth", BOOK5]
]) {
  t("every section of the " + label + " bundle prints its source and its corroboration", () =>
    checkProvenance(label, book));
}

/* ---------- every carried block says which printed page it was read from ----------
 * The text of these five books was cut from scans, and the leaves of a scan print their
 * own page numbers. The build records the page and the leaf of the scan the text came
 * from; a leaf whose number could not be read records no page and is named in
 * meta.pages.blocks_without_a_page instead of being given a plausible number. Where a
 * block's own leaf prints no folio, the page may have been read from the other copy of
 * the same printing, and then the block names that copy in `page_from`.
 *
 * This is the check that rows and meta agree, that a page never exceeds the leaves a
 * copy has, that a page range cannot advance faster than the leaves it covers, that the
 * pages run forward across the book, and that every borrowed page names the copy it came
 * from and appears in meta.pages.cross_copy's list of fills. */
function checkPages(label, book) {
  const meta = book.meta;
  assert.ok(meta.pages && meta.pages.by_scan, label + " records no page provenance");
  assert.ok(Array.isArray(meta.pages.blocks_without_a_page),
    label + " must name the blocks whose page could not be read");
  const copies = Object.keys(meta.pages.by_scan);
  const maxLeaves = Math.max(...copies.map(c => meta.pages.by_scan[c].leaves));
  const noPage = new Set(meta.pages.blocks_without_a_page);
  const cross = meta.pages.cross_copy;
  const filled = new Map(((cross && cross.filled_from_another_copy) || []).map(f => [f.n, f]));
  let prevPage = null, prevN = null, withPage = 0;
  for (const s of book.sections) {
    const scan = meta.pages.by_scan[s.from];
    assert.ok(scan, label + " §" + s.n + " comes from " + s.from + ", which has no leaf map");
    assert.ok(s.leaf != null && s.leaf >= 1 && s.leaf <= scan.leaves,
      label + " §" + s.n + " records leaf " + s.leaf + " of a scan with " + scan.leaves + " leaves");
    /* an end without a beginning would claim a range whose start is unknown */
    if (s.page_to != null) assert.ok(s.page != null,
      label + " §" + s.n + " records an end page but no page where the block begins");
    if (s.leaf_to != null) assert.ok(s.leaf != null,
      label + " §" + s.n + " records an end leaf but no leaf where the block begins");
    if (s.leaf_to != null) assert.ok(s.leaf_to >= s.leaf,
      label + " §" + s.n + " ends on leaf " + s.leaf_to + " before it begins on " + s.leaf);
    if (s.page == null) {
      assert.ok(noPage.has(s.n),
        label + " §" + s.n + " has no page and is not named among the blocks without one");
      assert.ok(!/printed page/.test(R.provenance(s, meta)),
        label + " §" + s.n + " prints a page it does not have: " + R.provenance(s, meta));
    } else {
      withPage++;
      assert.ok(s.page >= 1 && s.page <= maxLeaves,
        label + " §" + s.n + " claims page " + s.page + " of a printing whose copies have at most " +
        maxLeaves + " leaves");
      if (s.page_to != null) {
        assert.ok(s.page_to >= s.page,
          label + " §" + s.n + " ends on page " + s.page_to + " before it begins on " + s.page);
        /* one printed page per leaf: a page range may not run ahead of the leaves it covers */
        assert.ok(s.leaf_to != null && s.page_to - s.page <= s.leaf_to - s.leaf,
          label + " §" + s.n + " claims pages " + s.page + "–" + s.page_to + " over leaves " +
          s.leaf + "–" + s.leaf_to + ", which cannot be one page per leaf");
      }
      if (prevPage != null) {
        assert.ok(s.page >= prevPage,
          label + " §" + s.n + " was read from page " + s.page + " after §" + prevN +
          " on page " + prevPage + " of the same printing");
      }
      prevPage = s.page;
      prevN = s.n;
      assert.ok(!noPage.has(s.n),
        label + " §" + s.n + " carries page " + s.page + " and is also listed as without one");
      assert.ok(R.provenance(s, meta).includes("printed page " + s.page + (s.page_to == null ? "" : "–" + s.page_to)),
        label + " §" + s.n + " must print the page it was read from: " + R.provenance(s, meta));
    }
    /* a borrowed page names the other copy of the printing that printed it */
    if (s.page_from != null) {
      assert.ok(s.page != null, label + " §" + s.n + " names a copy but carries no page");
      assert.notStrictEqual(s.page_from, s.from,
        label + " §" + s.n + " says its page came from the copy its text came from");
      assert.ok(copies.includes(s.page_from),
        label + " §" + s.n + " names " + s.page_from + ", which has no leaf map");
      const f = filled.get(s.n);
      assert.ok(f && f.page === s.page && f.from === s.page_from,
        label + " §" + s.n + " names " + s.page_from + " for page " + s.page +
        " but is not recorded in cross_copy's fills");
      assert.ok(R.provenance(s, meta).includes("; page read from " + s.page_from),
        label + " §" + s.n + " must name the copy its page came from: " + R.provenance(s, meta));
    } else {
      assert.ok(!filled.has(s.n),
        label + " §" + s.n + " is listed as filled from another copy but names no copy");
    }
  }
  assert.ok(withPage > 0, label + " records no page on any block");
}

/* ---------- two copies of one printing paginate alike, or nothing is borrowed ----------
 * A block whose own leaf prints no folio can only take the page the other copy prints if
 * the two copies are proved to be the same pagination: they must compare on at least the
 * recorded minimum of blocks they both carry, agree on the page of every one, and agree
 * that those blocks are the same block. The bundle says how many comparisons were made,
 * names every disagreement and every block excluded as a different block, and fills
 * nothing from a pair whose proof failed. */
function checkCrossCopy(label, book) {
  const pages = book.meta.pages;
  assert.ok(pages && pages.cross_copy, label + " says nothing about cross-copy pagination");
  const cc = pages.cross_copy;
  assert.ok(Array.isArray(cc.pairs) && cc.pairs.length > 0, label + " made no copy comparison");
  assert.ok(Array.isArray(cc.filled_from_another_copy), label + " must list the pages it borrowed");
  const copies = Object.keys(pages.by_scan);
  const proven = new Set();
  for (const p of cc.pairs) {
    assert.strictEqual(p.copies.length, 2, label + " compares " + JSON.stringify(p.copies));
    for (const c of p.copies) assert.ok(copies.includes(c), label + " compares " + c + ", which has no leaf map");
    assert.ok(p.compared >= 0 && p.agree >= 0, label + " has a negative comparison count");
    assert.strictEqual(p.agree + p.disagreements.length, p.compared,
      label + "'s pair " + p.copies.join(" / ") + " counts pages it does not explain");
    assert.strictEqual(typeof p.paginate_alike, "boolean", label + " must say whether the copies paginate alike");
    if (p.paginate_alike) {
      assert.ok(p.compared >= cc.minimum_shared_blocks,
        label + " proves pagination on only " + p.compared + " blocks");
      assert.strictEqual(p.disagreements.length, 0,
        label + " calls a pair alike that disagrees on " + JSON.stringify(p.disagreements));
      proven.add(p.copies.slice().sort().join("|"));
    } else {
      assert.ok(p.disagreements.length > 0 || p.compared < cc.minimum_shared_blocks,
        label + " calls a pair unlike without saying why");
    }
  }
  const byN = new Map(book.sections.map(s => [s.n, s]));
  for (const f of cc.filled_from_another_copy) {
    const s = byN.get(f.n);
    assert.ok(s, label + " records a borrowed page for §" + f.n + ", which it does not carry");
    assert.strictEqual(s.page_from, f.from, label + " §" + f.n + " names a different copy than the record");
    assert.strictEqual(s.page, f.page, label + " §" + f.n + " carries a different page than the record");
  }
  /* a page is only ever borrowed where both copies are proved to paginate alike */
  for (const s of book.sections) {
    if (s.page_from == null) continue;
    const key = [s.from, s.page_from].sort().join("|");
    assert.ok(proven.has(key),
      label + " §" + s.n + " borrows a page from " + s.page_from +
      " without a proven pagination comparison between them");
  }
}


for (const [label, book] of [
  ["first", BOOK1], ["second", BOOK2], ["second (French)", BOOK2FR],
  ["third", BOOK3], ["fourth", BOOK4]
]) {
  t("every section of the " + label + " bundle says which printed page it was read from", () =>
    checkPages(label, book));
  t("the " + label + " bundle proves its copies paginate alike before borrowing a page", () =>
    checkCrossCopy(label, book));
}

t("a transcription records no page, because its text was not cut from a leaf", () => {
  for (const [label, book] of [["sixth", BOOK], ["fifth", BOOK5]]) {
    assert.ok(!book.meta.pages, label + " must not claim page provenance it does not have");
    for (const s of book.sections) {
      assert.strictEqual(s.page, undefined, label + " §" + s.n + " must record no printed page");
    }
  }
});

t("the provenance sentence is one pure function in the engine, and the page only wraps it", () => {
  const html = fs.readFileSync(appPage, "utf8");
  const engine = fs.readFileSync(path.join(docs, "reader.js"), "utf8");
  assert.ok(/R\.provenance\s*\(/.test(html), "the page must print R.provenance, not a copy of it");
  assert.ok(!/% of its word-runs found verbatim/.test(html), "the page must not assemble the sentence itself");
  assert.ok(!/machine translation of the German block/.test(html), "the machine sentence must live in one place");
  assert.ok(/corroborated against/.test(engine), "the engine must carry the sentence");
  // pure: same input, same sentence, and neither the row nor the meta is touched
  const row = BOOK.sections[0];
  const before = JSON.stringify([row, BOOK.meta.scans.length]);
  assert.strictEqual(R.provenance(row, BOOK.meta), R.provenance(row, BOOK.meta));
  assert.strictEqual(JSON.stringify([row, BOOK.meta.scans.length]), before,
    "provenance must not mutate what it is given");
  assert.strictEqual(R.provenance(null, BOOK.meta), "");
  assert.strictEqual(R.provenance({ n: 1, text: "x" }, BOOK.meta), "",
    "a row with no recorded source prints nothing rather than a guess");
});

/* ---------- the figures the documents quote are the bundles' own ----------
 * Every number README.md and data/README.md print about the books is a promise the
 * repository makes about its own data, and prose is not compiled: the sixth edition's
 * median was quoted as 0.976 for weeks while the bundle said 0.981. Each claim below
 * is a sentence with its figures captured, checked against the bundle that owns them.
 * A reworded sentence fails too: the figures and the claim move together, on purpose. */
const ver = b => (b.meta && b.meta.verification) || {};
const covered = b => b.meta.numbered_paragraphs_carried != null
  ? b.meta.numbered_paragraphs_carried : b.meta.recovered;

function sameNumber(text, value) {
  const n = Number(text);
  if (!Number.isFinite(n) || typeof value !== "number" || !Number.isFinite(value)) return false;
  const decimals = (String(text).split(".")[1] || "").length;
  if (decimals === 0) return n === value;
  return Math.abs(n - value) < 0.5 / Math.pow(10, decimals) + 1e-9;
}

function checkDoc(file, claims) {
  const text = fs.readFileSync(path.join(__dirname, file), "utf8");
  for (const c of claims) {
    const m = c.pattern.exec(text);
    assert.ok(m, file + ": the sentence carrying \u201c" + c.what + "\u201d is gone or reworded \u2014 " +
      "update the claim in test-node.js rather than the figure");
    c.expect.forEach((want, i) => {
      assert.ok(sameNumber(m[i + 1], want),
        file + " says " + m[i + 1] + " for " + c.what + ", the bundle says " + want);
    });
  }
}

// how the fifth and the sixth editions stand against each other, computed once
const FIFTH_DIFF = (() => {
  const six = {};
  BOOK.sections.forEach(s => { six[s.n] = R.norm(s.text); });
  let differ = 0;
  const onlyFifth = [];
  BOOK5.sections.forEach(s => {
    if (!(s.n in six)) onlyFifth.push(s.n);
    else if (six[s.n] !== R.norm(s.text)) differ++;
  });
  return { differ, onlyFifth };
})();

// the carried blocks of the second edition, which the min-0 note quotes
t("the figures README.md quotes about the books are the bundles' own", () => {
  checkDoc("README.md", [
    { what: "the sixth edition is complete", pattern: /All (\d+) sections are present\./,
      expect: [BOOK.meta.total_in_book] },
    { what: "the sixth edition's median coverage", pattern: /\(median (\d+)% of its word-runs\)/,
      expect: [Math.round(ver(BOOK).median * 100)] },
    { what: "the fifth edition's corroboration and length",
      pattern: /median \*\*([0-9.]+)\*\*, minimum \*\*([0-9.]+)\*\*, every one of its \*\*(\d+) sections\*\*/,
      expect: [ver(BOOK5).median, ver(BOOK5).min, BOOK5.meta.total_in_book] },
    { what: "the fourth edition's carried aphorisms",
      pattern: /\*\*(\d+) of the (\d+) are carried\*\* \(median coverage \*\*([0-9.]+)\*\*, minimum \*\*([0-9.]+)\*\*\)/,
      expect: [BOOK4.meta.recovered, BOOK4.meta.total_in_book, ver(BOOK4).median, ver(BOOK4).min] },
    { what: "the fourth edition's lost marks", pattern: /the (\d+) lost marks are named/,
      expect: [BOOK4.meta.missing.length] },
    { what: "the first edition's carried aphorisms",
      pattern: /\*\*(\d+) of the (\d+) aphorisms\*\* \(median \*\*([0-9.]+)\*\*, minimum \*\*([0-9.]+)\*\*\)/,
      expect: [BOOK1.meta.recovered, BOOK1.meta.total_in_book, ver(BOOK1).median, ver(BOOK1).min] },
    { what: "the first edition's lost marks", pattern: /with the (\d+) lost marks named/,
      expect: [BOOK1.meta.missing.length] },
    { what: "the second edition's blocks and paragraphs",
      pattern: /\*\*(\d+) blocks covering (\d+) of the (\d+) numbered paragraphs\*\*/,
      expect: [BOOK2.meta.blocks, covered(BOOK2), BOOK2.meta.total_in_book] },
    { what: "the third edition's blocks, paragraphs and corroboration",
      pattern: /\*\*(\d+) blocks covering (\d+) of its (\d+) numbered paragraphs\*\* \(median corroboration \*\*([0-9.]+)\*\*, minimum \*\*([0-9.]+)\*\*\)/,
      expect: [BOOK3.meta.blocks, covered(BOOK3), BOOK3.meta.total_in_book, ver(BOOK3).median, ver(BOOK3).min] },
    { what: "the third edition's lost numbers", pattern: /with the (\d+) lost numbers named/,
      expect: [BOOK3.meta.missing.length] },
    { what: "the French blocks and paragraphs",
      pattern: /\*\*(\d+) blocks covering (\d+) of (\d+) numbered paragraphs\*\*/,
      expect: [BOOK2FR.meta.blocks, covered(BOOK2FR), BOOK2FR.meta.total_in_book] },
    { what: "how many sections the fifth and sixth word differently",
      pattern: /(\d+) sections are worded differently and \u00a7292\u2013\u00a7294 exist only in the fifth/,
      expect: [FIFTH_DIFF.differ] },
    { what: "the assertion count README.md prints",
      pattern: /node test-node\.js +# the suite: (\d+) assertions, no dependencies/,
      expect: [badgeNumbers()[1]] }
  ]);
  assert.deepStrictEqual(FIFTH_DIFF.onlyFifth, [292, 293, 294],
    "the README says \u00a7292\u2013\u00a7294 exist only in the fifth; the bundles say " + JSON.stringify(FIFTH_DIFF.onlyFifth));
});

t("the figures data/README.md quotes about the books are the bundles' own", () => {
  checkDoc("data/README.md", [
    { what: "the sixth edition's median and minimum",
      pattern: /scores \*\*median ([0-9.]+),\s+minimum ([0-9.]+)\*\* across all (\d+) sections/,
      expect: [ver(BOOK).median, ver(BOOK).min, BOOK.meta.total_in_book] },
    { what: "the fifth edition's median and minimum",
      pattern: /coverage per section: median \*\*([0-9.]+)\*\*, minimum \*\*([0-9.]+)\*\*/,
      expect: [ver(BOOK5).median, ver(BOOK5).min] },
    { what: "the first edition's table",
      pattern: /### The first edition[\s\S]{0,400}?Carried \| \*\*(\d+) of (\d+)\*\* aphorisms[\s\S]{0,160}?median \*\*([0-9.]+)\*\*, minimum \*\*([0-9.]+)\*\*/,
      expect: [BOOK1.meta.recovered, BOOK1.meta.total_in_book, ver(BOOK1).median, ver(BOOK1).min] },
    { what: "the fourth edition's table",
      pattern: /### The fourth edition[\s\S]{0,400}?Carried \| \*\*(\d+) of (\d+)\*\* aphorisms[\s\S]{0,160}?median \*\*([0-9.]+)\*\*, minimum \*\*([0-9.]+)\*\*/,
      expect: [BOOK4.meta.recovered, BOOK4.meta.total_in_book, ver(BOOK4).median, ver(BOOK4).min] },
    { what: "the numbers the second, third and French books run to",
      pattern: /Numbered to \| \u00a7(\d+) \| \u00a7(\d+) \| \u00a7(\d+)/,
      expect: [BOOK2.meta.total_in_book, BOOK3.meta.total_in_book, BOOK2FR.meta.total_in_book] },
    { what: "the blocks carried by the second, third and French books",
      pattern: /Blocks carried \| (\d+) \| (\d+) \| (\d+)/,
      expect: [BOOK2.meta.blocks, BOOK3.meta.blocks, BOOK2FR.meta.blocks] },
    { what: "the paragraphs covered by the second, third and French books",
      pattern: /Numbered paragraphs covered \| (\d+) of (\d+) \| (\d+) of (\d+) \| (\d+) of (\d+)/,
      expect: [covered(BOOK2), BOOK2.meta.total_in_book, covered(BOOK3), BOOK3.meta.total_in_book,
               covered(BOOK2FR), BOOK2FR.meta.total_in_book] },
    { what: "the paragraphs the 1819 list brings under a block",
      pattern: /brings (\d+) of the (\d+) numbered paragraphs under a block\. The (\d+) that remain/,
      expect: [covered(BOOK2), BOOK2.meta.total_in_book, BOOK2.meta.missing.length] },
    { what: "the third edition's blocks in the rebuilding note",
      pattern: /so (\d+) blocks covering (\d+) of (\d+) paragraphs were/,
      expect: [BOOK3.meta.blocks, covered(BOOK3), BOOK3.meta.total_in_book] },
    { what: "the min-0 note's checked and carried counts",
      pattern: /`sections_checked` reads (\d+) where `blocks`\s+reads (\d+)/,
      expect: [ver(BOOK2).sections_checked, BOOK2.meta.blocks] },
    { what: "the min-0 note's refused entry",
      pattern: /`\{"n": (\d+), "corroboration": ([0-9.]+)\}`/,
      expect: [(ver(BOOK2).refused[0] || {}).n, (ver(BOOK2).refused[0] || {}).corroboration] },
    { what: "the min-0 note's carried median and minimum",
      pattern: /their median is \*\*([0-9.]+)\*\* and their minimum \*\*([0-9.]+)\*\*/,
      expect: [median(BOOK2.sections.map(s => s.corroboration)),
               Math.min.apply(null, BOOK2.sections.map(s => s.corroboration))] },
    { what: "the min-0 note's count of named gaps", pattern: /one of the (\d+) named gaps/,
      expect: [BOOK2.meta.missing.length] },
    { what: "the assertion count data/README.md prints",
      pattern: /node test-node\.js +# the suite: (\d+) assertions/,
      expect: [badgeNumbers()[1]] }
  ]);
});

function median(nums) {
  const s = nums.slice().sort((a, b) => a - b);
  return s[Math.floor(s.length / 2)];
}

// the badge is drawn from the suite's own run, so the prose and the badge must agree
function badgeNumbers() {
  const svg = fs.readFileSync(path.join(docs, "badges", "tests.svg"), "utf8");
  const m = /aria-label="tests: (\d+)\/(\d+)"/.exec(svg);
  assert.ok(m, "docs/badges/tests.svg does not carry its figures \u2014 run python3 scripts/badges.py");
  return [Number(m[1]), Number(m[2])];
}

/* ---------- the fingerprints: a rebuild that changes carried text must be recorded ----------
 * The OCR is not committed, so no CI job can rebuild the books and compare. This can
 * compare what is committed: every carried block is frozen in data/fingerprints.json, and
 * a rebuild that rewords, renumbers or re-sources a block fails here until the change is
 * recorded with `node tools/fingerprint.js record --note "why"` and committed with it. */
const FP = require("./tools/fingerprint.js");
const RECORDED = FP.load();

for (const b of FP.BUNDLES) {
  t("the " + b.label + " bundle still fingerprints as recorded", () => {
    const want = RECORDED.bundles && RECORDED.bundles[b.rel];
    assert.ok(want, b.rel + " has no recorded fingerprint \u2014 node tools/fingerprint.js record");
    const have = FP.fingerprint(FP.read(b.rel));
    assert.strictEqual(have.sections, want.sections,
      b.rel + " now carries " + have.sections + " blocks, the record says " + want.sections);
    const changed = Object.keys(want.blocks).filter(n => want.blocks[n] !== have.blocks[n]);
    const added = Object.keys(have.blocks).filter(n => !(n in want.blocks));
    const gone = Object.keys(want.blocks).filter(n => !(n in have.blocks));
    const named = changed.concat(added, gone).sort((x, y) => x - y).slice(0, 6).map(n => "\u00a7" + n);
    assert.strictEqual(changed.length + added.length + gone.length, 0,
      b.rel + ": carried text changed since data/fingerprints.json was recorded (" + named.join(", ") +
      (changed.length + added.length + gone.length > 6 ? ", \u2026" : "") +
      "). If the change is intended, record it: node tools/fingerprint.js record --note \"why\"");
    assert.strictEqual(have.digest, want.digest, b.rel + ": the bundle's block order or content changed");
  });
}

t("the fingerprints cover every bundle the app loads, and say what they freeze", () => {
  assert.strictEqual(RECORDED.format, FP.FORMAT, "data/fingerprints.json is from another format");
  const recorded = Object.keys(RECORDED.bundles || {}).sort();
  const expected = FP.BUNDLES.map(b => b.rel).sort();
  assert.deepStrictEqual(recorded, expected, "every bundled book must be fingerprinted, and none other");
  assert.ok(/machine flag/.test(RECORDED.covers || ""), "the file must say what it covers");
  assert.strictEqual(RECORDED.algorithm, "sha256");
});

/* ---------- the concordance: the numbering across the books, as a map ---------- */
const MAP_BOOKS = [
  { key: "first", label: "E1", meta: BOOK1.meta, sections: BOOK1.sections },
  { key: "fourth", label: "E4", meta: BOOK4.meta, sections: BOOK4.sections },
  { key: "fifth", label: "E5", meta: BOOK5.meta, sections: BOOK5.sections },
  { key: "sixth", label: "E6", meta: BOOK.meta, sections: BOOK.sections },
  { key: "second", label: "DE2", meta: BOOK2.meta, sections: BOOK2.sections },
  { key: "third", label: "DE3", meta: BOOK3.meta, sections: BOOK3.sections },
  { key: "secondFr", label: "FR", meta: BOOK2FR.meta, sections: BOOK2FR.sections }
];
const MAP = R.concordance(MAP_BOOKS);

t("the concordance runs 1 to the widest book's last paragraph, with no row dropped", () => {
  const widest = Math.max.apply(null, MAP_BOOKS.map(b => b.meta.total_in_book));
  assert.strictEqual(MAP.total, widest);
  assert.strictEqual(MAP.rows.length, widest);
  assert.strictEqual(MAP.rows[0].n, 1);
  assert.strictEqual(MAP.rows[widest - 1].n, widest);
  for (let i = 1; i < MAP.rows.length; i++) assert.ok(MAP.rows[i].n > MAP.rows[i - 1].n, "rows must ascend");
});

t("each column of the concordance carries exactly what its bundle says it carries", () => {
  for (const b of MAP_BOOKS) {
    assert.strictEqual(MAP.counts[b.key], covered(b),
      b.key + ": the map carries " + MAP.counts[b.key] + " numbered paragraphs, the bundle says " + covered(b));
    assert.strictEqual(MAP.counts[b.key], b.meta.total_in_book - b.meta.missing.length,
      b.key + ": the map must cover every number the bundle does not list as missing");
  }
});

t("a printed range fills every number the page prints with it, under a block that carries it", () => {
  for (const b of MAP_BOOKS) {
    // every block's own number points at that block, whatever a range before it said
    const starts = new Set(b.sections.map(s => s.n));
    const spans = {};
    b.sections.forEach(s => {
      const to = s.to == null ? s.n : s.to;
      for (let n = s.n; n <= to; n++) (spans[n] = spans[n] || []).push(s.n);
    });
    for (const s of b.sections) assert.deepStrictEqual(MAP.rows[s.n - 1].books[b.key],
      { start: s.n, label: s.to == null || s.to === s.n ? "\u00a7" + s.n : "\u00a7" + s.n + "\u2013" + s.to },
      b.key + " \u00a7" + s.n + " must open its own block");
    for (const key of Object.keys(spans)) {
      const cell = MAP.rows[Number(key) - 1].books[b.key];
      assert.ok(cell, b.key + " \u00a7" + key + " is printed in a block but the map leaves it empty");
      assert.ok(spans[key].includes(cell.start),
        b.key + " \u00a7" + key + " must open a block that prints it, got \u00a7" + cell.start);
      if (starts.has(Number(key))) assert.strictEqual(cell.start, Number(key),
        b.key + " \u00a7" + key + " is printed under its own mark and must open that block");
    }
  }
  // the widest printed range, §90–105, is one English block in the 1819 list
  assert.deepStrictEqual(MAP.rows[96].books.second, { start: 90, label: "\u00a790\u2013105" },
    "\u00a797 is printed with \u00a790\u2013105 and must point there");
  assert.strictEqual(MAP.rows[96].books.sixth.start, 97, "the sixth edition prints \u00a797 on its own");
  // §124 was claimed by the Google copy's §123–124 range as well as by BN's own §124 mark
  assert.deepStrictEqual(MAP.rows[123].books.third, { start: 124, label: "\u00a7124" },
    "§124 is printed under its own mark and only that block carries it");
  assert.deepStrictEqual(MAP.rows[122].books.third, { start: 123, label: "\u00a7123" },
    "the range that also printed §124 stops at §123");
});

t("no book carries a number in two blocks: a range stops where another block owns the number", () => {
  for (const b of MAP_BOOKS) {
    const owner = {};
    for (const s of b.sections) {
      const to = s.to == null ? s.n : s.to;
      for (let n = s.n; n <= to; n++) {
        assert.ok(owner[n] === undefined,
          b.key + " carries \u00a7" + n + " in \u00a7" + owner[n] + " and again in \u00a7" + s.n);
        owner[n] = s.n;
      }
    }
  }
  // the 1824 German cut the Google copy's §123–124 back to §123 and records the cut; the
  // machine mirror is built from those same blocks and must match them number for number
  for (const b of [BOOK3, BOOK3MT]) {
    const a = b.sections.find(s => s.n === 123);
    assert.strictEqual(a.to, 123, "§123 must stop before the block that prints §124");
    assert.deepStrictEqual(b.meta.range_conflicts,
      [{ n: 123, printed_to: 124, kept_to: 123, owned_elsewhere: [124], owner: { 124: 124 } }],
      "a range cut for another block's number must be recorded in the bundle");
  }
});

t("scanlib cuts a range back for the block that prints the number, whichever scan is read first", () => {
  // the 1824 OCR is not committed, so the rule is executed on a synthetic book: one copy
  // prints §5 under its own mark, the other reads its §4–§5 block as a range
  const py = process.env.PYTHON || "python3";
  let out;
  try {
    out = execFileSync(py, [path.join(__dirname, "tools/test-scanlib-range.py")],
      { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
  } catch (e) {
    throw new Error("scanlib.build could not be exercised with " + py + ": " +
      String((e.stdout || "") + (e.stderr || "")).trim());
  }
  const runs = JSON.parse(out.trim().split("\n").pop()).scanlib_range;
  assert.strictEqual(runs.length, 2, "the rule must be exercised in both source orders");
  for (const run of runs) {
    const where = run.order.join(" then ");
    assert.strictEqual(run.range_4, 4, where + ": the range §4–5 must stop at §4, got " + run.range_4);
    assert.strictEqual(run.section_5, "SYN-OWN", where + ": §5 must stay with its own mark, got " + run.section_5);
    assert.strictEqual(run.range_7, 9, where + ": a range no other block competes for must stay whole, got " + run.range_7);
    assert.deepStrictEqual(run.range_conflicts,
      [{ n: 4, printed_to: 5, kept_to: 4, owned_elsewhere: [5], owner: { 5: 5 } }],
      where + ": the cut must be recorded, not absorbed");
    assert.strictEqual(run.blocks, 7, where + ": the cut number must not open a block of its own");
  }
});

t("nothing is filled in from another edition: a number a book lacks is empty in its column", () => {
  // the fifth carries §292–§294 and the sixth does not; the first stops at §271
  assert.deepStrictEqual(MAP.rows[291].books.fifth, { start: 292, label: "\u00a7292" });
  assert.strictEqual(MAP.rows[291].books.sixth, undefined, "the sixth has no \u00a7292");
  assert.strictEqual(MAP.rows[293].books.sixth, undefined, "the sixth has no \u00a7294");
  assert.strictEqual(MAP.rows[318].books.first, undefined, "the first edition numbers only to \u00a7271");
  assert.ok(MAP.rows[317].books.second, "the 1819 list covers \u00a7318");
  assert.strictEqual(MAP.rows[319].books.second, undefined, "and stops there");
  // and no row invents a cell for a book that has ended
  for (const row of MAP.rows) {
    for (const b of MAP_BOOKS) {
      if (row.n > b.meta.total_in_book) assert.strictEqual(row.books[b.key], undefined,
        b.key + " \u00a7" + row.n + " is past the end of that book");
    }
  }
});

t("the machine translations need no column: each covers exactly its German blocks", () => {
  for (const [mt, de] of [[BOOK2MT, BOOK2], [BOOK3MT, BOOK3]]) {
    const a = {}, b = {};
    mt.sections.forEach(s => { for (let n = s.n; n <= (s.to == null ? s.n : s.to); n++) a[n] = true; });
    de.sections.forEach(s => { for (let n = s.n; n <= (s.to == null ? s.n : s.to); n++) b[n] = true; });
    assert.deepStrictEqual(Object.keys(a).sort(), Object.keys(b).sort(),
      "the machine bundle and its German must cover the same numbers");
  }
});

t("the page draws the concordance from the engine, and gives the machine books no column", () => {
  const html = fs.readFileSync(appPage, "utf8");
  assert.ok(/R\.concordance\s*\(/.test(html), "the page must call R.concordance, not rebuild the ranges");
  assert.ok(/for \(var n = s\.n; n <= to; n\+\+\)/.test(fs.readFileSync(path.join(docs, "reader.js"), "utf8")),
    "the range expansion must live in the engine");
  const mapKeys = [...html.matchAll(/\["(\w+)", "[A-Z0-9]+"\]/g)].map(m => m[1]);
  assert.deepStrictEqual(mapKeys, ["first", "fourth", "fifth", "sixth", "second", "third", "secondFr"],
    "seven columns: the four English books, the two German and the French");
  assert.ok(!/secondMt|thirdMt/.test(html.slice(html.indexOf("var MAP_BOOKS"), html.indexOf("var MAP_BOOKS") + 400)),
    "the machine books must not take a column of their own");
});

console.log("\n" + pass + "/" + (pass + fail) + " assertions passed");
process.exit(fail ? 1 : 0);
