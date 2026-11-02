# Changelog

## 1.0.1 — 2026-11-02

- # Organon Reader — first release (1.0.0) Built from the app master list, entry **#132**, with the spec in `forge/QUEUE/app-organon-reader.md` (READY). - **The text**: *Organon of Medicine*, sixth edition, Boericke translation 1922, from the Internet Archive scan — public domain. 156 of the 291 sections carry a readable section mark; the reader publishes that number and names what is missing instead of renumbering. - **Search**: phrase search over the bundled text. A term that occurs in one section returns that section first, with its number and the matched line. A term shorter than two characters is refused as too short — never reported as "no matches". - **Bookmarks and notes**: kept on the device, verified by reading the value back; a write that cannot be made is reported and never shown as kept. - **Corrupt state**: an unreadable saved file is reported, offered for export, and does not stop the text opening. - **Offline**: no `fetch`, no `XMLHttpRequest`, no beacon, no socket, no off-origin resource. The suite asserts all four and that the bundle hashes the same twice.

## 1.0.0 — 2026-11-02

First release. An offline reader for the *Organon of Medicine*, sixth edition
(Boericke translation, 1922): full-text search, bookmarks and notes on the device,
156 of the book's 291 sections with the missing ones named rather than renumbered.
See `changes/2026-11-02-initial.md`.
