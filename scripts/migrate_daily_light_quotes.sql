-- Add the columns that hold Daily Light's own printed wording for each citation.
--
-- Daily Light frequently quotes only part of a verse it cites; these columns
-- record what Bagster actually printed, so a consumer can show the original
-- extract instead of assuming the whole verse was quoted.
--
-- Populated by scripts/load_daily_light.py, which aligns the source JSON's
-- printed prose against KJV.db. See docs/daily_light_schema.md.
--
-- Additive and idempotent-by-intent: existing queries against
-- dl_reading_verses keep working unchanged. SQLite has no
-- "ADD COLUMN IF NOT EXISTS", so re-running this against an already-migrated
-- database reports "duplicate column name" and is safe to ignore.
--
-- Usage:
--     sqlite3 data/daily_light.db < scripts/migrate_daily_light_quotes.sql
--
-- or, without the sqlite3 CLI:
--     python3 -c "import sqlite3; sqlite3.connect('data/daily_light.db').executescript(open('scripts/migrate_daily_light_quotes.sql').read())"

-- The devotional's printed wording for this citation, cleaned but otherwise
-- verbatim. NULL when the source omits the citation entirely, or when the
-- alignment could not confidently attach any printed text to it.
ALTER TABLE dl_reading_verses ADD COLUMN quoted_text TEXT;

-- 1 when the quote omits a run of words from the start, middle or end of the
-- cited KJV range; 0 when it quotes the range in full. NULL alongside a NULL
-- quoted_text.
ALTER TABLE dl_reading_verses ADD COLUMN is_partial INTEGER;

-- Alignment confidence in 0..1: the share of the quote's words found, in
-- order, within the cited KJV text. Kept for auditing and so consumers can
-- suppress weak matches without a reload.
ALTER TABLE dl_reading_verses ADD COLUMN quote_score REAL;
