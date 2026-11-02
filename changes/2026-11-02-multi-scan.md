# 1.1.0 — the text is read from three scans, not one

The first release carried 156 of the 291 sections because it trusted one OCR. A second
and third scan of the same 1922 Boericke translation lose *different* marks, so reading
all three and merging them carries **255**.

- `tools/extract.py` anchors the body on the first aphorism's own words, reads only
  marks whose digits it can actually read (with an OCR digit map applied inside the
  mark), keeps the longest forward-moving run, and prefers the scan with both edges of
  the section known and the cleanest prose.
- Every section carries `from`: `IA-1842-1922`, `Wellcome-0001` or `Wellcome-0002`. The
  reader prints it under the section number, so a line can be checked against its scan.
- `sections.json` records the SHA-256 of each OCR file used.
- 36 sections (3, 5, 11, 13, 17, 31, 39, 45, 67, 73, 77, 103, 111, 113, 114, 115, 119,
  121, 125, 131, 132, 138, 171, 173, 178, 179, 183, 190, 205, 214, 223, 224, 250, 251,
  272, 273) are unreadable in all three and stay named rather than renumbered.
- Suite 21/21, including a new assertion that the merged bundle beats the best single
  scan and that every section names its source.
