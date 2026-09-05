# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A small data repository, not an application. It packages the King James
Version (KJV) Bible and the *Daily Light on the Daily Path* devotional as
SQLite databases, plus documentation describing their schemas and example
analytical queries. There is no build, lint, or test tooling — most "work"
here is either writing/running SQL queries against `data/*.db`, or
maintaining the one Python loader script.

## Repository layout

- `index.html` — GitHub Pages landing page linking to the infographics
  below. Served at https://tjhleeds.github.io/bible-stats/ once GitHub
  Pages is enabled (Settings → Pages → Source: Deploy from a branch →
  `main` → `/ (root)`). Update this file's cards when infographics are
  added, renamed, or removed.
- `data/KJV.db` — KJV Bible SQLite database (31,102 verses, 66 books),
  sourced from [scrollmapper/bible_databases](https://github.com/scrollmapper/bible_databases).
- `data/daily_light.db` — *Daily Light on the Daily Path* devotional
  database (full year: 366 days, 732 readings, 6,018 verse references).
- `docs/database_structure.md` — `KJV.db` schema and example queries.
- `docs/daily_light_schema.md` — `daily_light.db` schema, including the
  `ATTACH DATABASE` pattern for joining it to `KJV.db`.
- `infographics/daily_light_coverage.html` — standalone HTML infographic
  showing what percentage of `KJV.db` (by books, chapters, verses, words) is
  quoted in `daily_light.db`; includes the SQL queries used to compute each
  figure. Open it directly in a browser — no build step.
- `infographics/leviticus_offerings.md` / `infographics/leviticus_offerings.html`
  — a comparison of the five offerings in Leviticus 1–7 (burnt, meat, peace,
  sin, trespass), sourced entirely from direct `KJV.db` quotations; the
  `.html` file is a standalone illustrated version of the same table.
- `infographics/pentateuch_abomination_infographic.html` — standalone HTML
  infographic covering every verse in Genesis–Deuteronomy containing
  "abomination"/"abominations" (queried from `KJV.db`), grouped by phrasing
  pattern (e.g. "unto the LORD" vs. "unto you" vs. "unto the Egyptians").
- `scripts/load_daily_light.py` — one-off/idempotent loader that downloads
  `DailyLight.json` (or reads a local copy) and repopulates
  `data/daily_light.db`.
- `verses per book.md` — links to prebuilt [Datasette Lite](https://lite.datasette.io/)
  queries against `KJV.db` for verses/chapters/words per book.

## Working with the databases

Both databases are plain SQLite files — use the `sqlite3` CLI or Python's
`sqlite3` module (no ORM, no migrations framework).

### Running read-only queries

The `sqlite3` CLI is not guaranteed to be installed in every environment —
prefer Python's built-in `sqlite3` module, and always open connections in
read-only mode via a `file:` URI so an exploratory query can't accidentally
modify these files (there is no backup or regeneration path for `KJV.db`,
and `data/daily_light.db` is only rebuildable via
`scripts/load_daily_light.py`, which re-downloads its source data):

```bash
python3 -c "
import sqlite3
con = sqlite3.connect('file:data/KJV.db?mode=ro', uri=True)
for row in con.execute('SELECT name FROM KJV_books LIMIT 5'):
    print(row)
"
```

To query across both databases, `ATTACH` the second one using the same
`file:...?mode=ro` URI form so it also opens read-only:

```bash
python3 -c "
import sqlite3
con = sqlite3.connect('file:data/daily_light.db?mode=ro', uri=True)
con.execute(\"ATTACH DATABASE 'file:data/KJV.db?mode=ro' AS kjv\")
for row in con.execute('''
    SELECT r.month, r.day, r.period, rv.kjv_book_name, rv.chapter, v.verse, v.text
    FROM dl_readings r
    JOIN dl_reading_verses rv ON rv.reading_id = r.id
    JOIN kjv.KJV_books b ON b.name = rv.kjv_book_name
    JOIN kjv.KJV_verses v ON v.book_id = b.id
        AND v.chapter = rv.chapter
        AND v.verse BETWEEN rv.verse_start AND COALESCE(rv.verse_end, rv.verse_start)
    WHERE r.month = 1 AND r.day = 1 AND r.period = 'morning'
    ORDER BY rv.sequence, v.verse
'''):
    print(row)
"
```

If the `sqlite3` CLI is available, the equivalent is `sqlite3 -readonly
data/KJV.db "SELECT ..."` (`-readonly` is required — without it the CLI
opens the file read-write). See `docs/database_structure.md` and
`docs/daily_light_schema.md` for more example queries to adapt.

### `KJV.db`

Two main tables: `KJV_books` (id, name) and `KJV_verses` (id, book_id,
chapter, verse, text). See `docs/database_structure.md` for the full schema
and example queries (retrieve a book, get a chapter, search verse text by
`LIKE`, etc.).

### `daily_light.db`

Two tables: `dl_readings` (one row per morning/evening reading per calendar
day: month, day, period, title) and `dl_reading_verses` (one row per verse
reference within a reading: sequence, `kjv_book_name`, chapter, verse_start,
verse_end). `dl_reading_verses.kjv_book_name` must match `KJV_books.name`
in `KJV.db` **exactly** — this is how the two databases are joined.

To query full verse text for a devotional reading, `ATTACH DATABASE
'data/KJV.db' AS kjv` and join `dl_reading_verses` to `kjv.KJV_books`/
`kjv.KJV_verses` on `kjv_book_name = name`, `chapter`, and verse falling
between `verse_start` and `COALESCE(verse_end, verse_start)`. Full join
pattern and more examples (find readings citing a given verse, citation
counts per book, full day schedule) are in `docs/daily_light_schema.md`.

## Regenerating `daily_light.db`

`scripts/load_daily_light.py` rebuilds `dl_readings`/`dl_reading_verses`
from source data. It **deletes existing rows in both tables** before
reloading, but does not create the tables — the target database must
already have the schema described in `docs/daily_light_schema.md`.

```bash
# Downloads DailyLight.json from brentn/DailyLight via curl
python3 scripts/load_daily_light.py

# Or load from a local copy of DailyLight.json
python3 scripts/load_daily_light.py --json /path/to/DailyLight.json

# Target a different database file
python3 scripts/load_daily_light.py --db data/daily_light.db
```

The script maps abbreviated book names (from the source JSON's reference
strings, e.g. `1co`, `ps`, `re`) to canonical KJV book names via
`BOOK_NAME_MAP` — every mapped name must exist verbatim in `KJV_books.name`
(note: `re`/`rev` maps to `"Revelation of John"`, not `"Revelation"`). If
you add support for a new source or reference format, extend
`BOOK_NAME_MAP` and the `parse_refs`/`preprocess_refs` regex handling
rather than special-casing individual dates — reference strings mix
semicolon-separated citations, comma-separated verse/verse-range lists
within a citation, and occasional multi-book comma groups (e.g.
`"1Th 2:12, Jn 18:36"`), all handled by the same parser. Unparseable
reference strings are skipped and reported to stderr rather than failing
the load.

## Conventions

- Documentation in `docs/` is the source of truth for schema details —
  keep it in sync with any schema changes (there are no migration files).
- Book names throughout both databases use the KJV canonical form from
  `KJV_books.name` (e.g. `"I Samuel"`, `"Song of Solomon"`,
  `"Revelation of John"`), not common abbreviations or alternate titles.

## Keeping this file up to date

When a change alters something this file describes — a new/changed table
or column, a new data file, a new script, a changed CLI flag or command,
or a convention this file states no longer holding — update the relevant
section of `CLAUDE.md` in the same commit or pull request. If you're
unsure whether a change is significant enough to document here, err on
the side of updating it.
