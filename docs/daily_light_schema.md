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

Constraint: `UNIQUE(reading_id, sequence)`

Indexes: `(reading_id)`, `(kjv_book_name, chapter, verse_start)`

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

## Database Statistics (January 1–10)

- **Days loaded**: 10 (January 1–10)
- **Readings**: 20 (morning + evening × 10 days)
- **Verse references**: 134 (some reference multi-verse ranges)

## Source

*Daily Light on the Daily Path* is a public-domain devotional first published
by Samuel Bagster in 1875.  It uses the King James Version of the Bible
exclusively.  The verse selections reviewed for this database were taken from
[dailylightdevotional.org](https://dailylightdevotional.org/) and
cross-checked against other public-domain archives (CCEL, StudyLight,
ChristiansUnite).
