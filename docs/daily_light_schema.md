# Daily Light Devotional Database Structure

Source: [dailylightdevotional.org](https://dailylightdevotional.org/)  
Devotional: *Daily Light on the Daily Path* by Samuel Bagster (public domain)

## Overview

The `data/daily_light.db` file is an SQLite database containing the verse
references from the *Daily Light on the Daily Path* devotional.  Each day of
the year contains two readings—one for the morning and one for the evening—each
consisting of a curated collection of thematically linked KJV scripture
passages with no added commentary.

The database is designed to be queried alongside `data/KJV.db` (see
[database_structure.md](database_structure.md)) using SQLite's `ATTACH`
mechanism so that the full text of each verse can be retrieved in a single
query.

## Tables

### `dl_readings`

One record per morning or evening reading for each calendar day.

| Column   | Type         | Description                                                      |
|----------|--------------|------------------------------------------------------------------|
| `id`     | int (PK)     | Unique identifier for each reading                               |
| `month`  | int          | Calendar month (1–12)                                            |
| `day`    | int          | Calendar day of month (1–31)                                     |
| `period` | text         | `'morning'` or `'evening'`                                       |
| `title`  | text         | Leading theme-verse text printed at the head of the reading      |

Constraint: `UNIQUE(month, day, period)`

### `dl_reading_verses`

One record per verse reference within a reading.  Multi-verse ranges such as
`Ps 37:23-24` are stored as a single row (`verse_start=23`, `verse_end=24`).
Non-consecutive verse groups within the same citation (e.g. `Ex 30:1, 6-8`)
are stored as separate rows with consecutive `sequence` values.

| Column          | Type    | Description                                                              |
|-----------------|---------|--------------------------------------------------------------------------|
| `id`            | int (PK)| Unique identifier                                                        |
| `reading_id`    | int (FK)| References `dl_readings.id`                                              |
| `sequence`      | int     | 1-based display order within the reading                                 |
| `kjv_book_name` | text    | Book name matching **exactly** `KJV_books.name` in `KJV.db`             |
| `chapter`       | int     | Chapter number                                                           |
| `verse_start`   | int     | First (or only) verse number in the reference                            |
| `verse_end`     | int     | Last verse number for a range; `NULL` for a single-verse reference       |
| `quoted_text`   | text    | The devotional's own printed wording for this citation; `NULL` when unavailable |
| `is_partial`    | int     | 1 when the quote omits words from the cited range; 0 when it quotes it in full  |
| `quote_score`   | real    | Alignment confidence, 0–1                                                |

Constraint: `UNIQUE(reading_id, sequence)`

Indexes: `(reading_id)`, `(kjv_book_name, chapter, verse_start)`

## Quoted text

*Daily Light* frequently quotes only **part** of a verse it cites — about 54%
of citations print less than 90% of the cited range, and a quarter print half
or less.  `quoted_text` records what Bagster actually printed, so a consumer
can show the original extract rather than assume the whole verse was quoted.

The wording is a lightly modernised KJV ("to" for "unto", "does" for "doth"),
so it is **not** interchangeable with `KJV_verses.text` — it is the
devotional's own presentation, kept alongside the KJV rather than in place of
it.  Square-bracketed insertions are Bagster's editorial additions (supplying
a name the KJV leaves as a pronoun, marginal readings, glosses) and are
preserved verbatim.  `…` marks an elision the source itself marked.

### How it is derived

The source JSON gives one run of printed prose per reading, with no
machine-readable link to the individual citations.  Mapping it by position
fails — the heading sometimes covers only part of the first citation, the
source sometimes omits trailing citations, and a comma-separated citation
sometimes prints as two segments.  So `scripts/load_daily_light.py` matches
printed segments to citations **by content**, scoring each candidate pairing
on how much of the segment's wording appears in the cited KJV text and
resolving the whole reading with an order-preserving dynamic program.

Of the 6,018 citations, 5,557 carry a quote; the remaining 461 are citations
whose text the source omits.  55% of stored quotes are flagged `is_partial`.

`quote_score` is the share of the quote's words found, in order, within the
cited KJV text.  Scores of about 0.46 and above are reliably correct; the
small number below that are where a quote may have been attached to the wrong
citation, so **consumers should suppress quotes below a threshold** rather
than display them.  Re-running the loader with `--self-check` asserts the
overall distribution still looks sane.

### Example: partial quotes for one reading

```sql
ATTACH DATABASE 'data/KJV.db' AS kjv;

SELECT
    rv.kjv_book_name || ' ' || rv.chapter || ':' || rv.verse_start AS reference,
    rv.is_partial,
    ROUND(rv.quote_score, 2) AS score,
    rv.quoted_text                                                 AS printed,
    group_concat(v.text, ' ')                                      AS full_verse
FROM dl_readings r
JOIN dl_reading_verses rv ON rv.reading_id = r.id
JOIN kjv.KJV_books  b ON b.name   = rv.kjv_book_name
JOIN kjv.KJV_verses v ON v.book_id = b.id
                     AND v.chapter  = rv.chapter
                     AND v.verse BETWEEN rv.verse_start
                                     AND COALESCE(rv.verse_end, rv.verse_start)
WHERE r.month = 1 AND r.day = 2 AND r.period = 'morning'
  AND rv.quoted_text IS NOT NULL
GROUP BY rv.id
ORDER BY rv.sequence;
```

### Adding these columns to an existing database

The loader repopulates rows but does not create tables.  Apply
`scripts/migrate_daily_light_quotes.sql` once before reloading:

```bash
sqlite3 data/daily_light.db < scripts/migrate_daily_light_quotes.sql
python3 scripts/load_daily_light.py --self-check
```

## Joining to the KJV Database

SQLite's `ATTACH DATABASE` statement allows a single query to span both files.

### Pattern

```sql
ATTACH DATABASE 'data/KJV.db' AS kjv;

SELECT
    r.month, r.day, r.period, r.title,
    rv.sequence,
    rv.kjv_book_name, rv.chapter, v.verse,
    v.text
FROM dl_readings r
JOIN dl_reading_verses rv ON rv.reading_id = r.id
JOIN kjv.KJV_books  b ON b.name   = rv.kjv_book_name
JOIN kjv.KJV_verses v ON v.book_id = b.id
                     AND v.chapter  = rv.chapter
                     AND v.verse   >= rv.verse_start
                     AND v.verse   <= COALESCE(rv.verse_end, rv.verse_start)
ORDER BY rv.sequence, v.verse;
```

## Example Queries

### All verses for one reading

```sql
ATTACH DATABASE 'data/KJV.db' AS kjv;

SELECT rv.sequence, rv.kjv_book_name, rv.chapter, v.verse, v.text
FROM dl_readings r
JOIN dl_reading_verses rv ON rv.reading_id = r.id
JOIN kjv.KJV_books  b ON b.name   = rv.kjv_book_name
JOIN kjv.KJV_verses v ON v.book_id = b.id
                     AND v.chapter  = rv.chapter
                     AND v.verse   >= rv.verse_start
                     AND v.verse   <= COALESCE(rv.verse_end, rv.verse_start)
WHERE r.month = 1 AND r.day = 1 AND r.period = 'morning'
ORDER BY rv.sequence, v.verse;
```

### Find all readings that cite a specific verse

```sql
ATTACH DATABASE 'data/KJV.db' AS kjv;

-- Which readings include Romans 8:38?
SELECT r.month, r.day, r.period, r.title
FROM dl_readings r
JOIN dl_reading_verses rv ON rv.reading_id = r.id
JOIN kjv.KJV_books b ON b.name = rv.kjv_book_name
WHERE b.name   = 'Romans'
  AND rv.chapter = 8
  AND rv.verse_start <= 38
  AND COALESCE(rv.verse_end, rv.verse_start) >= 38;
```

### Count citations per book across all readings

```sql
SELECT kjv_book_name, COUNT(*) AS citation_groups
FROM dl_reading_verses
GROUP BY kjv_book_name
ORDER BY citation_groups DESC;
```

### Show the full reading schedule for a single day

```sql
ATTACH DATABASE 'data/KJV.db' AS kjv;

SELECT
    r.period,
    r.title,
    rv.sequence,
    rv.kjv_book_name || ' ' || rv.chapter || ':' ||
        rv.verse_start ||
        CASE WHEN rv.verse_end IS NOT NULL
             THEN '-' || rv.verse_end
             ELSE '' END AS reference,
    group_concat(v.verse || '. ' || v.text, ' ') AS passage_text
FROM dl_readings r
JOIN dl_reading_verses rv ON rv.reading_id = r.id
JOIN kjv.KJV_books  b ON b.name   = rv.kjv_book_name
JOIN kjv.KJV_verses v ON v.book_id = b.id
                     AND v.chapter  = rv.chapter
                     AND v.verse   >= rv.verse_start
                     AND v.verse   <= COALESCE(rv.verse_end, rv.verse_start)
WHERE r.month = 1 AND r.day = 1
GROUP BY r.id, rv.id
ORDER BY r.period DESC, rv.sequence, v.verse;
-- Note: 'morning' sorts before 'evening' when ordering DESC on 'morning'/'evening'
```

## Database Statistics

- **Days loaded**: 366 (full year, including February 29)
- **Readings**: 732 (morning + evening × 366 days)
- **Verse references**: 6,018 (some reference multi-verse ranges)

## Source

*Daily Light on the Daily Path* is a public-domain devotional first published
by Samuel Bagster in 1875.  It uses the King James Version of the Bible
exclusively.  The verse references in this database are sourced from the
[brentn/DailyLight](https://github.com/brentn/DailyLight) repository
(`src/assets/DailyLight.json`), imported with
`scripts/load_daily_light.py`.
