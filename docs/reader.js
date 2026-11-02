/* Organon Reader — the engine.
 * Pure functions + a storage adapter, so the whole thing is testable in node and
 * runs unchanged in the browser. No network, ever: there is no fetch, no XHR and
 * no URL in this file.
 * PolyForm Noncommercial 1.0.0. (c) 2026 Dr Sohil Momin.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.OrganonReader = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var MIN_TERM = 2;          // a one-character term is not a search, it is a shrug

  function norm(s) {
    return String(s == null ? "" : s)
      .replace(/[\u2018\u2019]/g, "'")
      .replace(/[\u201c\u201d]/g, '"')
      .replace(/\s+/g, " ")
      .toLowerCase();
  }

  /* ---------- the index ---------- */
  function createIndex(sections) {
    if (!Array.isArray(sections)) throw new TypeError("sections must be an array");
    var rows = sections.map(function (s) {
      return { n: s.n, text: s.text, from: s.from || null,
               notes: s.notes || [],
               corroboration: (s.corroboration == null ? null : s.corroboration),
               diffWords: (s.diffWords == null ? null : s.diffWords),
               hay: norm(s.text + " " + (s.notes || []).join(" ")) };
    });
    return {
      rows: rows,
      byNumber: rows.reduce(function (acc, r) { acc[r.n] = r; return acc; }, {}),
      count: rows.length
    };
  }

  /* ---------- search ---------- */
  function count(hay, needle) {
    if (!needle) return 0;          // an empty needle would loop forever
    var i = 0, hits = 0;
    while ((i = hay.indexOf(needle, i)) !== -1) { hits++; i += needle.length; }
    return hits;
  }

  function snippet(text, needle) {
    var hay = norm(text);
    var at = hay.indexOf(needle);
    if (at < 0) return "";
    var start = Math.max(0, at - 60);
    var end = Math.min(text.length, at + needle.length + 140);
    var out = text.slice(start, end).replace(/\s+/g, " ").trim();
    return (start > 0 ? "… " : "") + out + (end < text.length ? " …" : "");
  }

  /**
   * search(index, term) ->
   *   { ok:false, reason:"too-short", min:2 }        the term was refused, not "absent"
   *   { ok:true, term, results:[{n, hits, line}] }  best match first
   */
  function search(index, term) {
    var q = norm(term).trim();
    if (q.length < MIN_TERM) return { ok: false, reason: "too-short", min: MIN_TERM };
    var results = [];
    for (var i = 0; i < index.rows.length; i++) {
      var row = index.rows[i];
      var hits = count(row.hay, q);
      if (hits > 0) results.push({ n: row.n, hits: hits, line: snippet(row.text, q) });
    }
    results.sort(function (a, b) { return b.hits - a.hits || a.n - b.n; });
    return { ok: true, term: term.trim(), results: results };
  }

  /* ---------- moving through the book ---------- */
  function numbers(index) {
    return index.rows.map(function (r) { return r.n; });
  }

  /**
   * step(index, n, dir) -> the next/previous section that the bundle actually carries.
   * Gaps are stepped over, not stopped at: from §2 "next" is §4 when §3 was lost.
   * Returns null at either end of the book.
   */
  function step(index, n, dir) {
    var nums = numbers(index);
    if (!nums.length) return null;
    var i = nums.indexOf(n);
    if (i === -1) {                       // not a carried section: land on the nearest one
      for (var k = 0; k < nums.length; k++) if (nums[k] > n) return nums[k];
      return nums[nums.length - 1];
    }
    var j = i + (dir < 0 ? -1 : 1);
    return j >= 0 && j < nums.length ? nums[j] : null;
  }

  /* ---------- what the reader carries, said plainly ---------- */
  function coverage(meta) {
    var missing = (meta && meta.missing) || [];
    return {
      recovered: (meta && meta.recovered) || 0,
      total: (meta && meta.total_in_book) || 0,
      missing: missing,
      sentence: "This reader carries " + ((meta && meta.recovered) || 0) + " of the book's " +
        ((meta && meta.total_in_book) || 0) + " sections. " +
        (missing.length
          ? "The section marks for " + missing.length + " of them could not be read in the scanned text (" +
            missing.slice(0, 12).map(function (n) { return "§" + n; }).join(", ") +
            (missing.length > 12 ? ", …" : "") + "), so they are missing here rather than renumbered or invented."
          : "Every section is present.")
    };
  }

  /* ---------- state: bookmarks and notes, on the device ---------- */
  function Store(storage, key) {
    this.storage = storage;
    this.key = key || "organon-reader:v1";
  }

  Store.prototype.load = function () {
    var raw;
    try { raw = this.storage.get(this.key); }
    catch (e) { return { ok: false, reason: "unreadable", error: String(e && e.message || e) }; }
    if (raw == null) return { ok: true, state: empty(), fresh: true };
    var parsed;
    try { parsed = JSON.parse(raw); }
    catch (e) { return { ok: false, reason: "corrupt", raw: raw, error: String(e && e.message || e) }; }
    if (!parsed || typeof parsed !== "object") return { ok: false, reason: "corrupt", raw: raw };
    return { ok: true, state: normalise(parsed) };
  };

  Store.prototype.save = function (state) {
    var text = JSON.stringify(normalise(state));
    try { this.storage.set(this.key, text); }
    catch (e) { return { ok: false, reason: "unwritable", error: String(e && e.message || e), text: text }; }
    return { ok: true, text: text };
  };

  /* a write that must be visible: read back what we claim we kept */
  Store.prototype.commit = function (state) {
    var w = this.save(state);
    if (!w.ok) return w;
    var back = this.storage.get(this.key);
    if (back !== w.text) return { ok: false, reason: "unwritable", text: w.text };
    return { ok: true, text: w.text };
  };

  function empty() { return { bookmarks: [], notes: {}, last: null }; }

  function normalise(s) {
    var out = empty();
    if (Array.isArray(s.bookmarks)) {
      out.bookmarks = s.bookmarks.filter(function (n) { return typeof n === "number" && n > 0; })
        .filter(function (n, i, a) { return a.indexOf(n) === i; })
        .sort(function (a, b) { return a - b; });
    }
    if (s.notes && typeof s.notes === "object") {
      Object.keys(s.notes).forEach(function (k) {
        var n = Number(k);
        if (n > 0 && typeof s.notes[k] === "string" && s.notes[k].trim()) out.notes[n] = s.notes[k];
      });
    }
    if (typeof s.last === "number" && s.last > 0) out.last = s.last;
    return out;
  }

  function toggleBookmark(state, n) {
    var next = normalise(state);
    var i = next.bookmarks.indexOf(n);
    if (i === -1) next.bookmarks.push(n); else next.bookmarks.splice(i, 1);
    next.bookmarks.sort(function (a, b) { return a - b; });
    return next;
  }

  function setNote(state, n, text) {
    var next = normalise(state);
    if (String(text || "").trim()) next.notes[n] = String(text); else delete next.notes[n];
    return next;
  }

  function exportState(state) {
    return JSON.stringify(normalise(state), null, 2);
  }

  function importState(text) {
    try {
      var parsed = JSON.parse(text);
      if (!parsed || typeof parsed !== "object") return { ok: false, reason: "corrupt" };
      return { ok: true, state: normalise(parsed) };
    } catch (e) { return { ok: false, reason: "corrupt", error: String(e && e.message || e) }; }
  }

  return {
    MIN_TERM: MIN_TERM,
    norm: norm,
    createIndex: createIndex,
    search: search,
    numbers: numbers,
    step: step,
    coverage: coverage,
    Store: Store,
    empty: empty,
    normalise: normalise,
    toggleBookmark: toggleBookmark,
    setNote: setNote,
    exportState: exportState,
    importState: importState
  };
});
