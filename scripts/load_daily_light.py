#!/usr/bin/env python3
"""
Load Daily Light devotional data from DailyLight.json into daily_light.db.

Source: https://github.com/brentn/DailyLight/blob/master/src/assets/DailyLight.json

Usage:
    python3 scripts/load_daily_light.py [--db data/daily_light.db] [--json /path/to/DailyLight.json]

The script downloads DailyLight.json via curl if --json is not provided.
"""

import argparse
import difflib
import html
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


# ---------------------------------------------------------------------------
# Quoted-text alignment
#
# Daily Light frequently quotes only part of a verse it cites: of ~5,600
# citations, only about 46% reproduce the cited range in full. The source
# JSON's "text" field holds what was actually printed, but it arrives as one
# run of prose per reading with no machine-readable link back to the
# individual citations in "references".
#
# Mapping printed text to citations *by position* does not work. Three real
# cases break it:
#   - Jan 4 evening: the heading covers only part of citation 1 (1Co 15:55)
#     and the body's first segment continues that same citation (15:56).
#   - Feb 18 morning: the source omits the last three citations entirely.
#   - Jan 8 morning: "Ps 37:25,28" is one citation printed as two segments.
#
# So the segments are matched to citations *by content* instead, using an
# order-preserving dynamic program scored on how much of each segment's
# wording appears in the cited KJV text. Across the full year this assigns
# 99% of printed segments, with a median match score of 1.0.
# ---------------------------------------------------------------------------

# Daily Light modernises the KJV lightly ("to" for "unto", "does" for "doth").
# Folding the commonest of these keeps genuine quotes scoring near 1.0 so the
# score means "is this the right verse?" rather than "how archaic is it?".
MODERNISATIONS = {
    "thee": "you", "thou": "you", "ye": "you",
    "thy": "your", "thine": "your",
    "unto": "to", "toward": "to", "towards": "to",
    "upon": "on",
    "hath": "has", "hast": "have", "doth": "does",
    "shalt": "shall", "wilt": "will", "art": "are",
    "saith": "says", "cometh": "comes", "knoweth": "knows",
}

_WORD_RE = re.compile(r"[a-z']+")

# Citations are separated in the printed text by a paragraph break, or by a
# dash that follows whitespace (a bare "-" mid-word is a hyphen, not a break).
_SEGMENT_SPLIT_RE = re.compile(r"\n|(?<=\s)-|^-|—")

# Dynamic-program tuning. A pairing must score above MATCH_THRESHOLD to be
# worth making at all; skipping a citation is cheap (the source really does
# omit some), while dropping a printed segment is expensive (printed text
# almost always belongs to *some* citation).
MATCH_THRESHOLD = 0.45
SKIP_CITATION_COST = 0.05
DROP_SEGMENT_COST = 0.30

# A run of at least this many consecutive unquoted KJV words counts as a real
# elision rather than a wording difference. Calibrated: requiring a single
# contiguous match flags 87% of quotes as partial (modernised wording splits
# the match into several blocks even for complete quotes), whereas a 3-word
# gap flags 52% — matching the ~54% arrived at independently by comparing
# word counts. Tune here if the modernisation map changes.
ELISION_GAP = 3

# Matching blocks shorter than this are coincidence ("the", "and") rather than
# evidence that a phrase was quoted.
MIN_MATCH_BLOCK = 2


def normalise_words(text: str) -> list:
    """Return text as a list of lowercase words with archaic forms folded."""
    return [MODERNISATIONS.get(w, w) for w in _WORD_RE.findall(text.lower())]


def clean_quote(text: str) -> str:
    """Tidy one printed extract for storage.

    Decodes HTML entities (the source contains literal ``&nbsp;`` in
    "LORD&nbsp;OF LORDS"), normalises the source's ``...`` elision marker to a
    real ellipsis, and collapses whitespace.

    Square-bracketed insertions are deliberately kept: they are Bagster's own
    editorial additions — supplying a name the KJV leaves as a pronoun
    ("[Jesus] is able to save"), marginal readings ("[marg. orphans]") and
    glosses ("[Gr. citizenship]") — and are part of what makes the printed
    wording worth showing.
    """
    text = html.unescape(text)
    text = text.replace("...", "…")
    return re.sub(r"\s+", " ", text).strip()


def split_printed_text(heading: str, text: str) -> list:
    """Split one reading's printed prose into per-citation segments.

    The heading is the first printed chunk of the reading, so it leads the
    list and is aligned like any other segment.
    """
    segments = [heading] if heading and heading.strip() else []
    segments += _SEGMENT_SPLIT_RE.split(text or "")
    return [clean_quote(s) for s in segments if s and s.strip()]


def open_kjv(kjv_path: str) -> sqlite3.Connection:
    """Open KJV.db read-only, so alignment can never modify it."""
    return sqlite3.connect(f"file:{kjv_path}?mode=ro", uri=True)


def citation_words(con: sqlite3.Connection, cache: dict, citation: tuple) -> list | None:
    """Return the normalised KJV wording for one citation, or None if absent."""
    if citation in cache:
        return cache[citation]

    book, chapter, verse_start, verse_end = citation
    row = con.execute(
        """
        SELECT group_concat(v.text, ' ')
        FROM KJV_books b
        JOIN KJV_verses v ON v.book_id = b.id
        WHERE b.name = ? AND v.chapter = ? AND v.verse BETWEEN ? AND ?
        """,
        (book, chapter, verse_start, verse_end if verse_end else verse_start),
    ).fetchone()

    cache[citation] = normalise_words(row[0]) if row and row[0] else None
    return cache[citation]


def score_pair(segment_words: list, citation_words_: list | None) -> float:
    """Share of a segment's words found, in order, within the cited KJV text."""
    if not segment_words or not citation_words_:
        return 0.0
    matcher = difflib.SequenceMatcher(None, segment_words, citation_words_, autojunk=False)
    return sum(b.size for b in matcher.get_matching_blocks()) / len(segment_words)


def is_partial_quote(segment_words: list, citation_words_: list | None) -> bool | None:
    """Whether a quote omits a run of words from the cited range.

    Returns None when the citation's KJV text is unavailable, so the caller
    can store NULL rather than guess.
    """
    if not citation_words_:
        return None

    covered = [False] * len(citation_words_)
    matcher = difflib.SequenceMatcher(None, segment_words, citation_words_, autojunk=False)
    for block in matcher.get_matching_blocks():
        if block.size >= MIN_MATCH_BLOCK:
            for i in range(block.b, block.b + block.size):
                covered[i] = True

    if not any(covered):
        return None

    first = covered.index(True)
    last = len(covered) - 1 - covered[::-1].index(True)
    if first >= ELISION_GAP or (len(covered) - 1 - last) >= ELISION_GAP:
        return True

    run = 0
    for i in range(first, last + 1):
        run = 0 if covered[i] else run + 1
        if run >= ELISION_GAP:
            return True
    return False


def align_quotes(segments: list, citations: list, con, cache) -> dict:
    """Map citation index -> (quote text, score) by content alignment.

    Order-preserving dynamic program. Each citation takes at most one quote;
    a citation may absorb two consecutive segments (a quote the source split
    across a paragraph break), may be skipped entirely (the source omits it),
    and a segment may be dropped (it matches nothing).
    """
    seg_words = [normalise_words(s) for s in segments]
    cit_words = [citation_words(con, cache, c) for c in citations]
    n, m = len(seg_words), len(cit_words)
    if not n or not m:
        return {}

    unreachable = float("-inf")
    best = [[unreachable] * (m + 1) for _ in range(n + 1)]
    came_from = [[None] * (m + 1) for _ in range(n + 1)]
    best[0][0] = 0.0

    for i in range(n + 1):
        for j in range(m + 1):
            if best[i][j] == unreachable:
                continue
            if j < m and best[i][j] - SKIP_CITATION_COST > best[i][j + 1]:
                best[i][j + 1] = best[i][j] - SKIP_CITATION_COST
                came_from[i][j + 1] = ("skip_citation", i, j, None, None)
            if i < n and best[i][j] - DROP_SEGMENT_COST > best[i + 1][j]:
                best[i + 1][j] = best[i][j] - DROP_SEGMENT_COST
                came_from[i + 1][j] = ("drop_segment", i, j, None, None)
            if i < n and j < m:
                one = score_pair(seg_words[i], cit_words[j]) - MATCH_THRESHOLD
                if best[i][j] + one > best[i + 1][j + 1]:
                    best[i + 1][j + 1] = best[i][j] + one
                    came_from[i + 1][j + 1] = ("match", i, j, (i, i + 1), one + MATCH_THRESHOLD)
                if i + 1 < n:
                    merged = seg_words[i] + seg_words[i + 1]
                    two = score_pair(merged, cit_words[j]) - MATCH_THRESHOLD
                    if best[i][j] + two > best[i + 2][j + 1]:
                        best[i + 2][j + 1] = best[i][j] + two
                        came_from[i + 2][j + 1] = ("match", i, j, (i, i + 2), two + MATCH_THRESHOLD)

    assignments = {}
    i, j = n, m
    while i > 0 or j > 0:
        step = came_from[i][j]
        if step is None:
            break
        kind, prev_i, prev_j, span, score = step
        if kind == "match":
            quote = " ".join(segments[span[0] : span[1]])
            partial = is_partial_quote(normalise_words(quote), cit_words[prev_j])
            assignments[prev_j] = (quote, score, partial)
        i, j = prev_i, prev_j

    return assignments


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


def load_data(db_path: str, data: dict, kjv_path: str) -> None:
    """Insert all Daily Light readings into the SQLite database."""
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    kjv_con = open_kjv(kjv_path)
    kjv_cache = {}

    # Clear existing data so we start fresh from the JSON source
    cur.execute("DELETE FROM dl_reading_verses")
    cur.execute("DELETE FROM dl_readings")

    days_loaded = 0
    total_verse_refs = 0
    skipped_periods = []
    quotes_stored = 0
    partial_quotes = 0
    citations_without_quote = 0
    segments_seen = 0
    segments_assigned = 0

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

            # Attach the devotional's own printed wording to each citation.
            segments = split_printed_text(entry.get("heading", ""), entry.get("text", ""))
            quotes = align_quotes(segments, parsed, kjv_con, kjv_cache)
            segments_seen += len(segments)
            segments_assigned += len(quotes)

            for seq, (book, chapter, verse_start, verse_end) in enumerate(parsed, 1):
                quote, score, partial = quotes.get(seq - 1, (None, None, None))
                cur.execute(
                    """INSERT INTO dl_reading_verses
                           (reading_id, sequence, kjv_book_name, chapter, verse_start,
                            verse_end, quoted_text, is_partial, quote_score)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (reading_id, seq, book, chapter, verse_start, verse_end,
                     quote, None if partial is None else int(partial), score),
                )
                total_verse_refs += 1
                if quote is None:
                    citations_without_quote += 1
                else:
                    quotes_stored += 1
                    if partial:
                        partial_quotes += 1

        days_loaded += 1

    readings = cur.execute("SELECT COUNT(*) FROM dl_readings").fetchone()[0]
    verses = cur.execute("SELECT COUNT(*) FROM dl_reading_verses").fetchone()[0]
    con.commit()
    con.close()
    kjv_con.close()

    print(f"Loaded {days_loaded} days ({readings} readings, {verses} verse references).",
          file=sys.stderr)
    print(f"Quotes stored: {quotes_stored} "
          f"({partial_quotes} partial, {_percent(partial_quotes, quotes_stored)} of stored).",
          file=sys.stderr)
    print(f"Citations with no printed text: {citations_without_quote}. "
          f"Printed segments assigned: {segments_assigned}/{segments_seen} "
          f"({_percent(segments_assigned, segments_seen)}).",
          file=sys.stderr)
    if skipped_periods:
        print(f"Could not parse references for {len(skipped_periods)} period(s):",
              file=sys.stderr)
        for s in skipped_periods:
            print(f"  {s}", file=sys.stderr)


def _percent(part: int, whole: int) -> str:
    """Format part/whole as a percentage, tolerating a zero denominator."""
    return "n/a" if not whole else f"{part / whole * 100:.1f}%"


def self_check(db_path: str) -> None:
    """Assert the loaded quoted-text alignment looks sane, or exit non-zero.

    There is no test framework in this repository, so these are the guardrails
    against a regenerated database quietly attaching quotes to the wrong
    verses. Thresholds are deliberately looser than the figures actually
    observed, so ordinary source churn does not trip them.
    """
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    failures = []

    total, stored, partial = con.execute(
        """SELECT COUNT(*),
                  COUNT(quoted_text),
                  COALESCE(SUM(is_partial), 0)
           FROM dl_reading_verses"""
    ).fetchone()

    if stored / total < 0.85:
        failures.append(f"only {stored}/{total} citations carry a quote")
    if not 0.40 <= partial / stored <= 0.65:
        failures.append(
            f"{partial / stored * 100:.1f}% of quotes flagged partial; expected ~52%"
        )

    blank = con.execute(
        "SELECT COUNT(*) FROM dl_reading_verses WHERE TRIM(COALESCE(quoted_text, 'x')) = ''"
    ).fetchone()[0]
    if blank:
        failures.append(f"{blank} quotes stored as empty string rather than NULL")

    inconsistent = con.execute(
        """SELECT COUNT(*) FROM dl_reading_verses
           WHERE (quoted_text IS NULL) != (quote_score IS NULL)"""
    ).fetchone()[0]
    if inconsistent:
        failures.append(f"{inconsistent} rows have a quote without a score, or vice versa")

    # Two hand-checked readings: a heavy partial, and one whose elision the
    # source marks explicitly.
    for month, day, period, book, chapter, needle, want_partial in [
        (1, 2, "morning", "Isaiah", 42, "Sing to the Lord a new song", 1),
        (1, 1, "morning", "Philippians", 3, "…", 1),
    ]:
        row = con.execute(
            """SELECT rv.quoted_text, rv.is_partial
               FROM dl_readings r
               JOIN dl_reading_verses rv ON rv.reading_id = r.id
               WHERE r.month = ? AND r.day = ? AND r.period = ?
                 AND rv.kjv_book_name = ? AND rv.chapter = ?""",
            (month, day, period, book, chapter),
        ).fetchone()
        if not row or not row[0] or needle not in row[0]:
            failures.append(f"{book} {chapter} on {month}/{day} {period}: expected {needle!r}")
        elif row[1] != want_partial:
            failures.append(f"{book} {chapter} on {month}/{day} {period}: is_partial != {want_partial}")

    con.close()

    if failures:
        print("Self-check FAILED:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        sys.exit(1)
    print("Self-check passed.", file=sys.stderr)


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
    parser.add_argument(
        "--kjv",
        default="data/KJV.db",
        help="Path to KJV.db, opened read-only to align quoted text "
             "(default: data/KJV.db)",
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="After loading, assert the quoted-text alignment looks sane",
    )
    args = parser.parse_args()

    if args.json:
        with open(args.json) as fh:
            data = json.load(fh)
    else:
        data = download_json(DAILY_LIGHT_URL)

    load_data(args.db, data, args.kjv)

    if args.self_check:
        self_check(args.db)


if __name__ == "__main__":
    main()
