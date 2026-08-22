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

- `data/KJV.db` — KJV Bible SQLite database (31,102 verses, 66 books),
  sourced from [scrollmapper/bible_databases](https://github.com/scrollmapper/bible_databases).
- `data/daily_light.db` — *Daily Light on the Daily Path* devotional
  database (full year: 366 days, 732 readings, 6,018 verse references).
- `docs/database_structure.md` — `KJV.db` schema and example queries.
- `docs/daily_light_schema.md` — `daily_light.db` schema, including the
  `ATTACH DATABASE` pattern for joining it to `KJV.db`.
- `scripts/load_daily_light.py` — one-off/idempotent loader that downloads
  `DailyLight.json` (or reads a local copy) and repopulates
  `data/daily_light.db`.
- `verses per book.md` — links to prebuilt [Datasette Lite](https://lite.datasette.io/)
  queries against `KJV.db` for verses/chapters/words per book.

## Working with the databases

Both databases are plain SQLite files — use the `sqlite3` CLI or Python's
`sqlite3` module (no ORM, no migrations framework).

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
