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

console.log("\n" + pass + "/" + (pass + fail) + " assertions passed");
process.exit(fail ? 1 : 0);
