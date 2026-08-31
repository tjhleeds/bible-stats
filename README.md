# bible-stats

## Data

This repository includes the King James Version (KJV) Bible as an SQLite database, sourced from [scrollmapper/bible_databases](https://github.com/scrollmapper/bible_databases).

| File | Description |
|------|-------------|
| `data/KJV.db` | KJV Bible SQLite database (31,102 verses, 66 books) |
| `data/daily_light.db` | *Daily Light on the Daily Path* devotional database (January 1–10 loaded) |

See [`docs/database_structure.md`](docs/database_structure.md) for KJV schema documentation and example queries.

See [`docs/daily_light_schema.md`](docs/daily_light_schema.md) for the Daily Light schema, including how to join it to the KJV database.

## Infographics

The [`infographics/`](infographics/) folder contains standalone HTML (and
one paired Markdown) infographics built from direct `KJV.db`/`daily_light.db`
queries — open the `.html` files directly in a browser, no build step
required:

| File | Description |
|------|-------------|
| [`infographics/daily_light_coverage.html`](infographics/daily_light_coverage.html) | What percentage of the KJV is quoted in *Daily Light* |
| [`infographics/leviticus_offerings.md`](infographics/leviticus_offerings.md) / [`.html`](infographics/leviticus_offerings.html) | Comparison of the five offerings in Leviticus 1–7 |
| [`infographics/pentateuch_abomination_infographic.html`](infographics/pentateuch_abomination_infographic.html) | Every "abomination" verse in Genesis–Deuteronomy, grouped by phrasing |