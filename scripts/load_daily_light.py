#!/usr/bin/env python3
"""
Load Daily Light devotional data from DailyLight.json into daily_light.db.

Source: https://github.com/brentn/DailyLight/blob/master/src/assets/DailyLight.json

Usage:
    python3 scripts/load_daily_light.py [--db data/daily_light.db] [--json /path/to/DailyLight.json]

The script downloads DailyLight.json via curl if --json is not provided.
"""

import argparse
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

DAILY_LIGHT_URL = (
    "https://raw.githubusercontent.com/brentn/DailyLight/master/src/assets/DailyLight.json"
)

# Mapping from abbreviated book names (lowercase for case-insensitive lookup)
# to the exact KJV canonical book names used in KJV.db (KJV_books.name).
BOOK_NAME_MAP = {
    # Genesis
    "ge": "Genesis", "gen": "Genesis",
    # Exodus
    "ex": "Exodus", "exo": "Exodus",
    # Leviticus
    "le": "Leviticus", "lev": "Leviticus",
    # Numbers
    "nu": "Numbers", "num": "Numbers",
    # Deuteronomy
    "dt": "Deuteronomy", "deu": "Deuteronomy", "deut": "Deuteronomy",
    # Joshua
    "jos": "Joshua", "josh": "Joshua",
    # Judges
    "jdg": "Judges", "jud": "Judges", "judg": "Judges",
    # Ruth
    "ru": "Ruth", "ruth": "Ruth",
    # I Samuel
    "1sa": "I Samuel", "1sam": "I Samuel",
    # II Samuel
    "2sa": "II Samuel", "2sam": "II Samuel",
    # I Kings
    "1ki": "I Kings", "1kgs": "I Kings",
    # II Kings
    "2ki": "II Kings", "2kgs": "II Kings",
    # I Chronicles
    "1ch": "I Chronicles", "1chr": "I Chronicles",
    # II Chronicles
    "2ch": "II Chronicles", "2chr": "II Chronicles",
    # Ezra
    "ezra": "Ezra", "ezr": "Ezra",
    # Nehemiah
    "ne": "Nehemiah", "neh": "Nehemiah",
    # Esther
    "est": "Esther", "esth": "Esther",
    # Job
    "jb": "Job", "job": "Job",
    # Psalms
    "ps": "Psalms", "psa": "Psalms", "psalm": "Psalms", "psalms": "Psalms",
    # Proverbs
    "pr": "Proverbs", "pro": "Proverbs", "prov": "Proverbs",
    # Ecclesiastes
    "ec": "Ecclesiastes", "ecc": "Ecclesiastes", "eccl": "Ecclesiastes",
    # Song of Solomon (Canticles / Song of Songs)
    "ca": "Song of Solomon", "sos": "Song of Solomon",
    "song": "Song of Solomon", "ss": "Song of Solomon",
    # Isaiah
    "is": "Isaiah", "isa": "Isaiah",
    # Jeremiah
    "je": "Jeremiah", "jer": "Jeremiah",
    # Lamentations
    "la": "Lamentations", "lam": "Lamentations",
    # Ezekiel
    "ez": "Ezekiel", "eze": "Ezekiel", "ezek": "Ezekiel",
    # Daniel
    "da": "Daniel", "dan": "Daniel",
    # Hosea
    "ho": "Hosea", "hos": "Hosea",
    # Joel
    "joel": "Joel",
    # Amos
    "am": "Amos", "amos": "Amos",
    # Obadiah
    "ob": "Obadiah", "oba": "Obadiah", "obad": "Obadiah",
    # Jonah
    "jon": "Jonah", "jona": "Jonah",
    # Micah
    "mi": "Micah", "mic": "Micah",
    # Nahum
    "na": "Nahum", "nah": "Nahum",
    # Habakkuk
    "hab": "Habakkuk",
    # Zephaniah
    "zep": "Zephaniah", "zeph": "Zephaniah",
    # Haggai
    "hag": "Haggai",
    # Zechariah
    "zec": "Zechariah", "zech": "Zechariah",
    # Malachi
    "mal": "Malachi",
    # Matthew
    "mt": "Matthew", "mat": "Matthew", "matt": "Matthew",
    # Mark
    "mk": "Mark", "mar": "Mark", "mrk": "Mark",
    # Luke
    "lk": "Luke", "luk": "Luke",
    # John
    "jn": "John", "joh": "John", "john": "John",
    # Acts
    "ac": "Acts", "act": "Acts", "acts": "Acts",
    # Romans
    "ro": "Romans", "rom": "Romans",
    # I Corinthians
    "1co": "I Corinthians", "1cor": "I Corinthians",
    # II Corinthians
    "2co": "II Corinthians", "2cor": "II Corinthians",
    # Galatians
    "ga": "Galatians", "gal": "Galatians",
    # Ephesians
    "ep": "Ephesians", "eph": "Ephesians",
    # Philippians
    "php": "Philippians", "phi": "Philippians", "phil": "Philippians",
    # Colossians
    "col": "Colossians",
    # I Thessalonians
    "1th": "I Thessalonians", "1thes": "I Thessalonians", "1thess": "I Thessalonians",
    # II Thessalonians
    "2th": "II Thessalonians", "2thes": "II Thessalonians", "2thess": "II Thessalonians",
    # I Timothy
    "1ti": "I Timothy", "1tim": "I Timothy",
    # II Timothy
    "2ti": "II Timothy", "2tim": "II Timothy",
    # Titus
    "tit": "Titus",
    # Philemon
    "phm": "Philemon", "phlm": "Philemon",
    # Hebrews
    "he": "Hebrews", "heb": "Hebrews",
    # James
    "jas": "James",
    # I Peter
    "1pe": "I Peter", "1pet": "I Peter",
    # II Peter
    "2pe": "II Peter", "2pet": "II Peter",
    # I John
    "1jn": "I John", "1jo": "I John",
    # II John
    "2jn": "II John", "2jo": "II John",
    # III John
    "3jn": "III John", "3jo": "III John",
    # Jude
    "jude": "Jude",
    # Revelation
    "re": "Revelation of John", "rev": "Revelation of John",
}

MONTH_MAP = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}

# Regex matching "BookAbbr chapter:rest-of-verse-spec"
_BOOK_PREFIX_RE = re.compile(r"^([0-9]?[A-Za-z]+)\s+(\d+):(.+)$")
_VERSE_RANGE_RE = re.compile(r"^(\d+)(?:-(\d+))?$")


def lookup_book(abbr: str) -> str | None:
    """Return the KJV canonical book name for an abbreviation, or None if unknown."""
    return BOOK_NAME_MAP.get(abbr.lower())


def preprocess_refs(refs: str) -> str:
    """Normalise a raw references string before parsing."""
    # Replace double dashes (e.g. "1Co 1:27--29") with a single dash
    s = refs.replace("--", "-")
    # Insert a semicolon where a verse spec ends and a new reference begins
    # separated only by whitespace (e.g. "1Pe 2:3 Ps 5:11" -> "1Pe 2:3; Ps 5:11")
    s = re.sub(
        r"(\d+(?:-\d+)?)\s+([0-9]?[A-Za-z]+\s+\d+:)",
        r"\1; \2",
        s,
    )
    return s


def parse_refs(refs_string: str) -> list:
    """
    Parse a references string into a list of (kjv_book_name, chapter, verse_start, verse_end).

    Handles:
    - Semicolons as primary separators
    - Commas as verse-within-chapter separators ("Ps 63:1,7") or
      verse-range separators ("Ex 30:1,6-8"), or (rarely) between different
      book references ("1Th 2:12, Jn 18:36")
    - Multi-book comma groups ("Jn 11:4,40, Lk 2:52")
    - Skips tokens that cannot be resolved to a known book abbreviation
    """
    s = preprocess_refs(refs_string)

    results = []
    current_book = None
    current_chapter = None

    for semi_part in s.split(";"):
        semi_part = semi_part.strip()
        if not semi_part:
            continue

        m = _BOOK_PREFIX_RE.match(semi_part)
        if not m:
            # Could not parse as a reference – skip (e.g. December 1 stray text)
            continue

        new_book = lookup_book(m.group(1))
        if new_book is None:
            continue
        current_book = new_book
        current_chapter = int(m.group(2))
        verse_section = m.group(3)

        # verse_section may contain commas; iterate through comma-parts
        for comma_part in verse_section.split(","):
            comma_part = comma_part.strip()
            if not comma_part:
                continue

            # Is this comma-part the start of a new book reference?
            new_ref = _BOOK_PREFIX_RE.match(comma_part)
            if new_ref:
                nb = lookup_book(new_ref.group(1))
                if nb is not None:
                    current_book = nb
                    current_chapter = int(new_ref.group(2))
                    # The verse spec for the new ref may itself be
                    # comma-separated; take just the first token here
                    # (the loop continues with subsequent comma-parts)
                    comma_part = new_ref.group(3).split(",")[0].strip()

            # Parse as verse or verse range
            rm = _VERSE_RANGE_RE.match(comma_part)
            if rm and current_book is not None and current_chapter is not None:
                vs = int(rm.group(1))
                ve = int(rm.group(2)) if rm.group(2) else None
                results.append((current_book, current_chapter, vs, ve))

    return results


def parse_date(date_str: str) -> tuple[int, int]:
    """Return (month, day) from a string like 'January 1'."""
    parts = date_str.strip().split()
    return MONTH_MAP[parts[0]], int(parts[1])


def download_json(url: str) -> dict:
    """Download JSON from url using curl and return the parsed object."""
    print(f"Downloading {url} ...", file=sys.stderr)
    result = subprocess.run(
        ["curl", "-fsSL", url],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def load_data(db_path: str, data: dict) -> None:
    """Insert all Daily Light readings into the SQLite database."""
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    # Clear existing data so we start fresh from the JSON source
    cur.execute("DELETE FROM dl_reading_verses")
    cur.execute("DELETE FROM dl_readings")

    days_loaded = 0
    total_verse_refs = 0
    skipped_periods = []

    for day_entry in data["days"]:
        month, day = parse_date(day_entry["date"])

        for period in ("morning", "evening"):
            entry = day_entry[period]
            title = entry.get("heading", "").strip() or None
            refs_str = entry.get("references", "")

            cur.execute(
                "INSERT INTO dl_readings (month, day, period, title) VALUES (?, ?, ?, ?)",
                (month, day, period, title),
            )
            reading_id = cur.lastrowid

            parsed = parse_refs(refs_str)

            if not parsed and refs_str.strip():
                skipped_periods.append(
                    f"{day_entry['date']} {period}: {refs_str!r}"
                )

            for seq, (book, chapter, verse_start, verse_end) in enumerate(parsed, 1):
                cur.execute(
                    """INSERT INTO dl_reading_verses
                           (reading_id, sequence, kjv_book_name, chapter, verse_start, verse_end)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (reading_id, seq, book, chapter, verse_start, verse_end),
                )
                total_verse_refs += 1

        days_loaded += 1

    readings = cur.execute("SELECT COUNT(*) FROM dl_readings").fetchone()[0]
    verses = cur.execute("SELECT COUNT(*) FROM dl_reading_verses").fetchone()[0]
    con.commit()
    con.close()

    print(f"Loaded {days_loaded} days ({readings} readings, {verses} verse references).",
          file=sys.stderr)
    if skipped_periods:
        print(f"Could not parse references for {len(skipped_periods)} period(s):",
              file=sys.stderr)
        for s in skipped_periods:
            print(f"  {s}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        default="data/daily_light.db",
        help="Path to the SQLite database (default: data/daily_light.db)",
    )
    parser.add_argument(
        "--json",
        default=None,
        help="Path to a local DailyLight.json file (downloads via curl if omitted)",
    )
    args = parser.parse_args()

    if args.json:
        with open(args.json) as fh:
            data = json.load(fh)
    else:
        data = download_json(DAILY_LIGHT_URL)

    load_data(args.db, data)


if __name__ == "__main__":
    main()
