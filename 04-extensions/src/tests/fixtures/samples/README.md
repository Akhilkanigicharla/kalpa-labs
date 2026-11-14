# Import samples

Built from the formats each vendor publishes, read 14 Nov 2026:

- `sessionbuddy-v4-docs.json`, `sessionbuddy-docs.csv`, `sessionbuddy-pairs.txt`: the examples and rules on
  https://sessionbuddy.com/formats/ (v4 backups = object with `collections`; v3 = object with `sessions`; CSV header must hold a URL column; "Title/URL pairs" separated by a blank line).
- `sessionbuddy-v3-object.json`: v3 object form from the same page (`sessions` → `windows` → `tabs`, `name` overrides `title`).
- OneTab "Export URLs" (`URL | Title`, blank line = new group) is generated in `../make-fixtures.mjs`.

These are format examples for interoperability tests, not anyone's real browsing data.
