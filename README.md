# bible-stats

## Data

This repository includes the King James Version (KJV) Bible as an SQLite database, sourced from [scrollmapper/bible_databases](https://github.com/scrollmapper/bible_databases).

| File | Description |
|------|-------------|
| `data/KJV.db` | KJV Bible SQLite database (31,102 verses, 66 books) |
| `data/daily_light.db` | *Daily Light on the Daily Path* devotional database (January 1–10 loaded) |

See [`docs/database_structure.md`](docs/database_structure.md) for KJV schema documentation and example queries.

See [`docs/daily_light_schema.md`](docs/daily_light_schema.md) for the Daily Light schema, including how to join it to the KJV database.