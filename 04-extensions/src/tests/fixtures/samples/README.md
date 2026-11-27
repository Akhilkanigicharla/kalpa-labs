# Import samples

Built from the formats each vendor publishes, read 14 Nov 2026:

- `sessionbuddy-v4-docs.json`, `sessionbuddy-docs.csv`, `sessionbuddy-pairs.txt`: the examples and rules on
  https://sessionbuddy.com/formats/ (v4 backups = object with `collections`; v3 = object with `sessions`; CSV header must hold a URL column; "Title/URL pairs" separated by a blank line).
- `sessionbuddy-v3-object.json`: v3 object form from the same page (`sessions` → `windows` → `tabs`, `name` overrides `title`).
- OneTab "Export URLs" (`URL | Title`, blank line = new group) is generated in `../make-fixtures.mjs`.

These are format examples for interoperability tests, not anyone's real browsing data.

v0.3 samples (read 28 Nov 2026; sources are cited in `lib/importers.ts`):
- `pocket-list.csv`, `pocket-old-cursor.csv`: Pocket CSV, 5 columns `title,url,time_added,tags,status` (and the older 6 with `cursor`); first two rows quoted from a published example, the rest are hostile test rows.
- `pocket-ril_export.html`: Pocket's HTML export shape (`<title>Pocket Export</title>`, `<h1>Unread</h1>` / `<h1>Read Archive</h1>` + `ul li a`).
- `toby.json`: Toby `lists[].cards[]` with `title`, `customTitle`, `url`.
- `bookmarks.html`: Netscape bookmarks file (Chrome/Edge/Firefox "Export bookmarks").
- `edge-collections.csv`: SYNTHETIC. The real Edge Collections CSV header could not be verified; the importer reads any CSV with a URL and a Collection column.
