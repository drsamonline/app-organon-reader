#!/usr/bin/env node
/* Per-section fingerprints for the nine bundles.
 *
 * A build is not reproducible without the OCR, so nothing in CI can prove that a
 * rebuild produced the same book. This can: every carried block is fingerprinted
 * (number, printed range end, source label, corroboration, text, its printed notes,
 * and whether it is machine text), and `node test-node.js` refuses a bundle whose
 * fingerprint no longer matches `data/fingerprints.json`. A rebuild that changes the
 * text therefore fails until someone records the change on purpose.
 *
 *   node tools/fingerprint.js check            compare; exit 1 on any drift
 *   node tools/fingerprint.js record [--note "why the text changed"]
 *
 * `record` is the deliberate act: it rewrites the file from the bundles as they are
 * now, and the note is the record of why. Never run it to make a red suite green
 * without knowing what changed.
 */
"use strict";
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const FILE = path.join(ROOT, "data", "fingerprints.json");
const FORMAT = 2;

const BUNDLES = [
  ["sixth", "docs/organon-data.js"],
  ["fifth", "docs/organon5-data.js"],
  ["fourth", "docs/organon4-data.js"],
  ["first", "docs/organon1-data.js"],
  ["second", "docs/organon2-data.js"],
  ["third", "docs/organon3-data.js"],
  ["second (French)", "docs/organon2-fr-data.js"],
  ["second (machine)", "docs/organon2-en-mt-data.js"],
  ["third (machine)", "docs/organon3-en-mt-data.js"]
].map(([label, rel]) => ({ label, rel }));

/* the bundle is a script that exports its JSON; read it fresh every time */
function read(rel) {
  const abs = path.join(ROOT, rel);
  const resolved = require.resolve(abs);
  delete require.cache[resolved];
  return require(resolved);
}

/* One block, one string, every field the reader prints. Field order is the contract:
 * changing it changes every hash, so it is versioned by FORMAT. */
function canonical(s) {
  return JSON.stringify([
    s.n,
    s.to == null ? s.n : s.to,
    s.from || null,
    s.page == null ? null : s.page,
    s.page_to == null ? null : s.page_to,
    s.leaf == null ? null : s.leaf,
    s.leaf_to == null ? null : s.leaf_to,
    s.corroboration == null ? null : s.corroboration,
    s.text,
    s.notes || [],
    s.mt === true
  ]);
}

function hash(s) {
  return crypto.createHash("sha256").update(canonical(s)).digest("hex").slice(0, 16);
}

function fingerprint(book) {
  const sections = book.sections || [];
  const blocks = {};
  sections.forEach(s => { blocks[String(s.n)] = hash(s); });
  return {
    sections: sections.length,
    digest: crypto.createHash("sha256").update(sections.map(canonical).join("\n")).digest("hex"),
    blocks
  };
}

function compute() {
  const out = {};
  BUNDLES.forEach(b => { out[b.rel] = fingerprint(read(b.rel)); });
  return out;
}

function load() {
  return JSON.parse(fs.readFileSync(FILE, "utf8"));
}

/* Every way a bundle can disagree with the recorded file, in the reader's own terms. */
function diff(recorded) {
  const problems = [];
  BUNDLES.forEach(b => {
    const want = recorded.bundles && recorded.bundles[b.rel];
    if (!want) { problems.push({ label: b.label, rel: b.rel, why: "no fingerprint recorded" }); return; }
    const have = fingerprint(read(b.rel));
    if (have.sections !== want.sections) {
      problems.push({ label: b.label, rel: b.rel, why: "carries " + have.sections + " blocks, recorded " + want.sections });
    }
    const changed = Object.keys(want.blocks).filter(n => want.blocks[n] !== have.blocks[n]);
    const added = Object.keys(have.blocks).filter(n => !(n in want.blocks));
    if (changed.length || added.length) {
      const named = changed.concat(added).sort((a, b) => a - b).slice(0, 6).map(n => "\u00a7" + n);
      problems.push({ label: b.label, rel: b.rel,
        why: (changed.length + added.length) + " block(s) changed since it was recorded: " + named.join(", ") +
             (changed.length + added.length > 6 ? ", \u2026" : "") });
    }
  });
  return problems;
}

function main(argv) {
  const cmd = argv[0];
  if (cmd === "check") {
    const problems = diff(load());
    if (!problems.length) { console.log("fingerprints: all " + BUNDLES.length + " bundles match data/fingerprints.json"); return 0; }
    problems.forEach(p => console.error("DRIFT  " + p.label + " (" + p.rel + "): " + p.why));
    console.error("\nIf the change is intended: node tools/fingerprint.js record --note \"why\"");
    return 1;
  }
  if (cmd === "record") {
    const at = argv.indexOf("--note");
    const note = at === -1 ? null : argv[at + 1];
    const bundles = compute();
    const out = { format: FORMAT, algorithm: "sha256",
      covers: "every carried block's number, printed range end, source label, printed page and scan leaf, corroboration, text, printed notes and machine flag, in bundle order",
      note: note || null, bundles };
    fs.mkdirSync(path.dirname(FILE), { recursive: true });
    fs.writeFileSync(FILE, JSON.stringify(out, null, 2) + "\n");
    Object.keys(bundles).forEach(rel => console.log("recorded " + rel + " (" + bundles[rel].sections + " blocks)"));
    console.log("wrote " + path.relative(ROOT, FILE) + (note ? " \u2014 note: " + note : ""));
    return 0;
  }
  console.error("usage: node tools/fingerprint.js check | record [--note \"...\"]");
  return 2;
}

if (require.main === module) process.exit(main(process.argv.slice(2)));

module.exports = { FORMAT, BUNDLES, FILE, canonical, hash, fingerprint, read, compute, load, diff };
