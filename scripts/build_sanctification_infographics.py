"""Builds the five sanctification infographics (infographics/sanctification_*.html).

Usage: python3 scripts/build_sanctification_infographics.py [repo-root]

Every verse text and every count is fetched from data/KJV.db with the same SQL
the page prints, so the pages cannot drift from the queries they show."""
import html
import re
import sqlite3
import sys
from pathlib import Path
from urllib.parse import quote, quote_plus

REPO = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parent.parent)
OUT = REPO + "/infographics/"
con = sqlite3.connect(f"file:{REPO}/data/KJV.db?mode=ro", uri=True)

RAW = "https://raw.githubusercontent.com/tjhleeds/bible-stats/main/data/KJV.db"
CORE = ("(v.text LIKE '%sanctif%' OR v.text LIKE '%hallow%' OR v.text LIKE '%consecrat%'\n"
        "       OR v.text LIKE '%holiness%' OR v.text LIKE '%holily%')")
SELECT = "SELECT b.name AS book, v.chapter, v.verse, v.text\nFROM KJV_verses v\nJOIN KJV_books b ON b.id = v.book_id\n"
CORE_SQL = SELECT + f"WHERE {CORE}\nORDER BY v.book_id, v.chapter, v.verse"
NT_SQL = SELECT + f"WHERE v.book_id >= 40\n  AND {CORE}\nORDER BY v.book_id, v.chapter, v.verse"

SHORT = {"I Samuel": "1 Samuel", "II Samuel": "2 Samuel", "I Kings": "1 Kings", "II Kings": "2 Kings",
         "I Chronicles": "1 Chronicles", "II Chronicles": "2 Chronicles", "I Corinthians": "1 Corinthians",
         "II Corinthians": "2 Corinthians", "I Thessalonians": "1 Thessalonians",
         "II Thessalonians": "2 Thessalonians", "I Timothy": "1 Timothy", "II Timothy": "2 Timothy",
         "I Peter": "1 Peter", "II Peter": "2 Peter", "I John": "1 John", "II John": "2 John",
         "III John": "3 John", "Revelation of John": "Revelation", "Psalms": "Psalm"}
LONG = {v: k for k, v in SHORT.items()}


def rows(sql):
    return con.execute(sql).fetchall()


def ref(book, ch, vs):
    return f"{SHORT.get(book, book)} {ch}:{vs}"


def verses(sql):
    """{ 'Exodus 29:1': text } in canonical order."""
    return {ref(b, c, v): t.strip() for b, c, v, t in rows(sql)}


def link(sql):
    return f"https://lite.datasette.io/?url={quote(RAW, safe='')}#/KJV?sql={quote_plus(sql)}"


e = html.escape
HL = re.compile(r"\b(sanctif\w*|hallow\w*|consecrat\w*|holiness|holily|holy)\b", re.I)


def hl(text):
    return HL.sub(lambda m: f"<b>{m.group(0)}</b>", e(text, quote=False))


def sql_block(title, sql, note):
    return (f'<h3>{title}</h3>\n<pre><code>{e(sql)}</code></pre>\n'
            f'<p><a href="{e(link(sql))}">Run this query in Datasette Lite</a>, loaded directly from '
            f'<code>data/KJV.db</code> in this repository. {note}</p>\n')


def verse_li(r, text, ctx=None):
    c = f'<span class="ctx">{ctx}</span>' if ctx else ""
    return f'<li><span class="ref">{r}</span><div class="txt">{hl(text)}{c}</div></li>'


def check(name, got, want):
    got, want = list(got), list(want)
    assert sorted(got) == sorted(want), f"{name}: extra {set(got) - set(want)} missing {set(want) - set(got)}"


PAGES = [
    ("sanctification_vocabulary.html", "The words"),
    ("sanctification_across_the_bible.html", "Where it clusters"),
    ("sanctification_gods_part_and_ours.html", "God’s part and ours"),
    ("sanctification_sources_nt.html", "Who sanctifies"),
    ("sanctification_already_not_yet.html", "Already, now, not yet"),
]

LIGHT = dict(bg="#f7f5f0", panel="#ffffff", ink="#1f1c17", soft="#5e574b", muted="#8a8377", line="#e4dfd3",
             s1="#2a78d6", s2="#eb6834", s3="#1baf7a", s4="#eda100", s5="#e87ba4", s6="#6250d6")
DARK = dict(bg="#141311", panel="#1e1c19", ink="#efece6", soft="#b8b1a3", muted="#8a8377", line="#34302a",
            s1="#3987e5", s2="#d95926", s3="#199e70", s4="#c98500", s5="#d55181", s6="#9085e9")


def tokens(d):
    return "".join(f"--{k}:{v};" for k, v in d.items())


CSS = f"""
:root{{color-scheme:light;{tokens(LIGHT)}}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{color-scheme:dark;{tokens(DARK)}}}}}
:root[data-theme="dark"]{{color-scheme:dark;{tokens(DARK)}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;line-height:1.5}}
.sans,nav,.kicker,.stat,.chart,.legend,.count,.ref,.sql-section,footer,.tag{{font-family:system-ui,-apple-system,"Segoe UI",sans-serif}}
.wrap{{max-width:1040px;margin:0 auto;padding:28px 16px 72px}}
nav{{display:flex;flex-wrap:wrap;gap:6px;justify-content:center;font-size:13px;margin-bottom:32px}}
nav a,nav span{{padding:6px 12px;border-radius:999px;border:1px solid var(--line);color:var(--soft);text-decoration:none}}
nav span{{background:var(--ink);color:var(--bg);border-color:var(--ink)}}
nav a:hover{{border-color:var(--s1);color:var(--ink)}}
header{{text-align:center;margin-bottom:28px}}
.kicker{{text-transform:uppercase;letter-spacing:.16em;font-size:12px;color:var(--soft);margin-bottom:10px}}
h1{{font-size:clamp(28px,4.5vw,44px);margin:0 0 12px;line-height:1.15}}
.sub{{max-width:700px;margin:0 auto;color:var(--soft);font-size:16px}}
.stats{{display:flex;justify-content:center;gap:28px;flex-wrap:wrap;margin:30px 0 8px}}
.stat{{text-align:center;min-width:92px}}
.stat .n{{font-size:30px;font-weight:800;line-height:1}}
.stat .l{{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--soft);margin-top:6px}}
.panel{{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:22px 24px;margin:28px 0}}
.panel h2{{font-size:21px;margin:0 0 4px}}
.panel .lede{{color:var(--soft);margin:0 0 18px;font-size:15px}}
.insights{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin:28px 0}}
.insight{{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--s1);border-radius:12px;padding:14px 16px;font-size:15px}}
.insight b{{display:block;font-family:system-ui,-apple-system,"Segoe UI",sans-serif;font-size:13px;letter-spacing:.02em;margin-bottom:4px}}
.legend{{display:flex;flex-wrap:wrap;gap:8px 20px;font-size:12.5px;color:var(--soft);margin:0 0 14px}}
.legend .k{{display:flex;align-items:center;gap:7px}}
.sw{{width:10px;height:10px;border-radius:3px;flex:none}}
.hbar{{display:grid;grid-template-columns:minmax(92px,150px) 1fr;gap:6px 12px;align-items:center;font-size:13px}}
.hbar .lab{{color:var(--ink);text-align:right}}
.hbar .lab small{{display:block;color:var(--muted);font-size:11px}}
.track{{display:flex;align-items:center;gap:2px;min-height:18px}}
.seg{{height:16px;border-radius:0}}
.seg:first-child{{border-radius:4px 0 0 4px}}.seg:last-of-type{{border-radius:0 4px 4px 0}}.seg:only-of-type{{border-radius:4px}}
.track .v{{margin-left:8px;color:var(--soft);font-size:12px;white-space:nowrap}}
.track .v b{{color:var(--ink)}}
.grid{{columns:1;column-gap:22px;margin-top:8px}}
@media (min-width:760px){{.grid{{columns:2}}}}
.card{{break-inside:avoid;margin:0 0 22px;background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:20px 22px 16px;border-top:4px solid var(--c,var(--s1))}}
.card .top{{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}}
.card h3{{font-size:18px;margin:0}}
.card .phrase{{font-style:italic;font-size:14px;color:var(--soft);margin:4px 0 10px}}
.count{{font-size:12px;font-weight:700;padding:3px 10px;border-radius:999px;white-space:nowrap;border:1px solid var(--line);color:var(--ink)}}
ul.vv{{list-style:none;padding:0;margin:0}}
ul.vv li{{padding:10px 0;border-top:1px solid var(--line);display:grid;grid-template-columns:118px 1fr;gap:10px;font-size:15px}}
ul.vv li:first-child{{border-top:0}}
@media (max-width:520px){{ul.vv li{{grid-template-columns:1fr;gap:2px}}}}
.ref{{font-size:12.5px;font-weight:700;color:var(--soft);padding-top:2px}}
.txt b{{background:color-mix(in srgb,var(--c,var(--s1)) 22%,transparent);border-radius:3px;padding:0 2px;font-weight:600}}
.ctx{{display:block;font-size:13px;color:var(--soft);margin-top:5px;font-style:italic}}
.tag{{display:inline-block;font-size:11px;font-weight:700;border-radius:999px;padding:1px 8px;margin-right:4px;border:1px solid var(--line);color:var(--soft)}}
.sql-section{{margin-top:56px;font-size:14px}}
.sql-section h2{{font-size:20px}}
.sql-section h3{{font-size:15px;margin:26px 0 8px}}
.sql-section pre{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px;overflow-x:auto;font-size:12.5px;line-height:1.45}}
.sql-section p{{color:var(--soft)}}
.sql-section a,.panel a{{color:var(--s1)}}
footer{{margin-top:48px;text-align:center;font-size:12.5px;color:var(--muted)}}
footer a{{color:inherit}}
table{{border-collapse:collapse;width:100%;font-size:13px}}
th,td{{padding:5px 8px;border-bottom:1px solid var(--line);text-align:right}}
th:first-child,td:first-child{{text-align:left}}
details summary{{cursor:pointer;color:var(--soft);font-size:13px;margin-top:14px}}
"""


def page(fname, title, kicker, sub, body, extra_css=""):
    nav = "".join(f"<span>{lab}</span>" if f == fname else f'<a href="{f}">{lab}</a>' for f, lab in PAGES)
    nav = '<a href="../index.html">All infographics</a>' + nav
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>{CSS}{extra_css}</style>
</head>
<body>
<div class="wrap">
<nav aria-label="Sanctification series">{nav}</nav>
<header>
  <div class="kicker">{kicker}</div>
  <h1>{title}</h1>
  <p class="sub">{sub}</p>
</header>
{body}
<footer>Source: KJV text queried from <code>data/KJV.db</code> in this repository &middot; every quotation is the full verse exactly as stored in <code>KJV_verses.text</code> &middot; <a href="https://github.com/tjhleeds/bible-stats">Source on GitHub</a></footer>
</div>
</body>
</html>
"""
    with open(OUT + fname, "w", encoding="utf-8") as f:
        f.write(doc)


def stats(items):
    return '<div class="stats">' + "".join(
        f'<div class="stat"><div class="n">{n}</div><div class="l">{l}</div></div>' for n, l in items) + "</div>"


def insights(items, colours=None):
    out = []
    for i, (h, t) in enumerate(items):
        c = f' style="border-left-color:var(--{colours[i]})"' if colours else ""
        out.append(f'<div class="insight"{c}><b>{h}</b>{t}</div>')
    return '<div class="insights">' + "".join(out) + "</div>"


def card(title, phrase, items, colour, count_label=None):
    lis = "".join(verse_li(r, t, ctx) for r, t, ctx in items)
    n = count_label or f"{len(items)} verse{'s' if len(items) != 1 else ''}"
    ph = f'<div class="phrase">{phrase}</div>' if phrase else ""
    return (f'<div class="card" style="--c:var(--{colour})"><div class="top"><h3>{title}</h3>'
            f'<span class="count">{n}</span></div>{ph}<ul class="vv">{lis}</ul></div>')


def stacked(label, parts, total_max, small=""):
    """parts = [(value, colour, tooltip)]"""
    segs = "".join(
        f'<span class="seg" style="width:{100 * v / total_max:.2f}%;background:var(--{c})" title="{e(tip)}"></span>'
        for v, c, tip in parts if v)
    tot = sum(v for v, _, _ in parts)
    detail = " · ".join(f"{v}" for v, _, _ in parts)
    s = f"<small>{small}</small>" if small else ""
    return (f'<div class="lab">{label}{s}</div><div class="track" role="img" aria-label="{e(label)}: {tot} verses">'
            f'{segs}<span class="v"><b>{tot}</b> ({detail})</span></div>')


CORE_VERSES = verses(CORE_SQL)
assert len(CORE_VERSES) == 240, len(CORE_VERSES)
NT = verses(NT_SQL)
assert len(NT) == 46, len(NT)


def V(r, src=CORE_VERSES):
    return src[r]


def d_ok(fam):
    d = {r[0]: r for r in fam}
    return d['consecrate (consecrat-)'][3] == 2 and d['hallow'][3] == 2  # prose on page 1 relies on these


# ---------------------------------------------------------------- 1. vocabulary
def build_vocab():
    fam_sql = """SELECT w.word, COUNT(*) AS verses,
       SUM(v.book_id <= 39) AS ot, SUM(v.book_id >= 40) AS nt
FROM (SELECT 1 AS ord, 'sanctify (sanctif-)' AS word, '%sanctif%' AS pat
      UNION ALL SELECT 2, 'hallow', '%hallow%'
      UNION ALL SELECT 3, 'consecrate (consecrat-)', '%consecrat%'
      UNION ALL SELECT 4, 'holiness', '%holiness%'
      UNION ALL SELECT 5, 'holily', '%holily%'
      UNION ALL SELECT 6, 'saint(s)', '%saint%'
      UNION ALL SELECT 7, 'separate (separat-)', '%separat%'
      UNION ALL SELECT 8, 'cleanse (cleans-)', '%cleans%'
      UNION ALL SELECT 9, 'purify (purif-)', '%purif%'
      UNION ALL SELECT 10, 'blameless', '%blameless%'
      UNION ALL SELECT 11, 'undefiled', '%undefiled%'
      UNION ALL SELECT 12, 'unblameable', '%unblameab%') w
JOIN KJV_verses v ON v.text LIKE w.pat
GROUP BY w.ord, w.word
ORDER BY w.ord"""
    fam = rows(fam_sql)
    forms_sql = """SELECT w.form, COUNT(*) AS verses,
       SUM(v.book_id <= 39) AS ot, SUM(v.book_id >= 40) AS nt
FROM (SELECT 1 AS ord, 'sanctify' AS form
      UNION ALL SELECT 2, 'sanctified'
      UNION ALL SELECT 3, 'sanctifieth'
      UNION ALL SELECT 4, 'sanctification') w
JOIN KJV_verses v ON v.text LIKE '%' || w.form || '%'
GROUP BY w.ord, w.form
ORDER BY w.ord"""
    forms = rows(forms_sql)
    holy_sql = """SELECT COUNT(*) AS verses,
       SUM(v.text LIKE '%Holy Ghost%') AS holy_ghost,
       SUM(v.text LIKE '%holy place%') AS holy_place,
       SUM(v.text LIKE '%Holy One%') AS holy_one
FROM KJV_verses v
WHERE v.text LIKE '%holy%'"""
    holy = rows(holy_sql)[0]
    overlap_sql = f"""SELECT b.name AS book, v.chapter, v.verse, v.text,
       (v.text LIKE '%sanctif%') + (v.text LIKE '%hallow%') + (v.text LIKE '%consecrat%')
       + (v.text LIKE '%holiness%') + (v.text LIKE '%holily%') AS families
FROM KJV_verses v
JOIN KJV_books b ON b.id = v.book_id
WHERE {CORE}
  AND families >= 2
ORDER BY v.book_id, v.chapter, v.verse"""
    overlap = rows(overlap_sql)
    assert d_ok(fam)
    fsum = sum(r[1] for r in fam[:5])
    assert fsum - 240 == sum(r[4] - 1 for r in overlap)

    mx = max(r[1] for r in fam)
    core_bars = "".join(stacked(w, [(ot, "s1", f"{w}: {ot} Old Testament verses"), (nt, "s2", f"{w}: {nt} New Testament verses")], mx)
                        for w, n, ot, nt in fam[:5])
    rel_bars = "".join(stacked(w, [(ot, "s1", f"{w}: {ot} Old Testament verses"), (nt, "s2", f"{w}: {nt} New Testament verses")], mx)
                       for w, n, ot, nt in fam[5:])
    fmx = max(r[1] for r in forms)
    form_bars = "".join(stacked(f, [(ot, "s1", f"{f}: {ot} OT verses"), (nt, "s2", f"{f}: {nt} NT verses")], fmx)
                        for f, n, ot, nt in forms)
    legend = ('<div class="legend"><span class="k"><span class="sw" style="background:var(--s1)"></span>Old Testament</span>'
              '<span class="k"><span class="sw" style="background:var(--s2)"></span>New Testament</span>'
              '<span class="k">Figures are verses containing the word (OT · NT)</span></div>')
    d = {r[0]: r for r in fam}
    fm = {r[0]: r for r in forms}
    ov_items = [(ref(b, c, vs), t.strip(), None) for b, c, vs, t, n in overlap]

    body = stats([(240, "verses in the set"), (5, "word families"), (194, "Old Testament"), (46, "New Testament"),
                  (len(overlap), "use two families")])
    body += insights([
        ("“Sanctification” is a New Testament noun",
         f"The noun appears in {fm['sanctification'][1]} verses, all in the New Testament. The Old Testament only ever uses the verb: "
         f"“sanctify” is in {fm['sanctify'][2]} Old Testament verses."),
        ("“Hallow” almost vanishes",
         f"{d['hallow'][2]} of the {d['hallow'][1]} “hallow” verses are in the Old Testament. The other {d['hallow'][3]} are the same prayer, "
         "twice: “Hallowed be thy name” (Matthew 6:9, Luke 11:2)."),
        ("“Consecrate” is a priestly word",
         f"{d['consecrate (consecrat-)'][2]} of its {d['consecrate (consecrat-)'][1]} verses are Old Testament, most about ordaining priests. "
         "Its two New Testament uses are both in Hebrews, and both are about Christ."),
        ("“Holiness” is the most even",
         f"{d['holiness'][2]} Old Testament and {d['holiness'][3]} New Testament verses: about a third New Testament, against roughly a fifth for the set as a whole."),
    ], ["s1", "s2", "s3", "s4"])
    body += f"""<div class="panel"><h2>The five word families in the set</h2>
<p class="lede">The 240 verses on these pages are every KJV verse containing <em>sanctif-</em>, <em>hallow</em>, <em>consecrat-</em>, <em>holiness</em> or <em>holily</em>. The bars add up to {fsum}, not 240, because {len(overlap)} verses use two of the families at once.</p>
{legend}<div class="hbar">{core_bars}</div></div>
<div class="panel"><h2>The sanctify family, form by form</h2>
<p class="lede">The Old Testament commands and describes acts (“sanctify”, “sanctified”). The forms that describe sanctification as an ongoing action or a state (“sanctifieth”, “sanctification”) appear only in the New Testament.</p>
{legend}<div class="hbar">{form_bars}</div></div>
<div class="panel"><h2>Neighbouring words, searched but left out</h2>
<p class="lede">These words often appear alongside sanctification, but most of their uses are about something else: ritual washing, leprosy, the Nazarite vow, dividing land. They are counted here for comparison and are <strong>not</strong> in the 240-verse set. “Holy” is left out for the same reason: it is in {holy[0]} verses, but {holy[1]} of those are “Holy Ghost”, {holy[2]} “holy place” and {holy[3]} “Holy One”: mostly names and places, not the act of making holy.</p>
{legend}<div class="hbar">{rel_bars}</div></div>
<div class="grid">{card('Verses that use two families at once', 'Three of the four come from the ordination of Aaron and his sons', ov_items, 's3')}</div>
"""
    body += '<section class="sql-section"><h2>The queries</h2>'
    body += sql_block("The 240-verse set used on all five pages", CORE_SQL,
                      "<code>LIKE</code> is case-insensitive for ASCII in SQLite, so “Sanctify” and “sanctify” both match. <code>sanctif</code> catches sanctify, sanctified, sanctifieth and sanctification without catching “sanctuary”.")
    body += sql_block("Verses per word family, split by Testament (all three bar charts’ families)", fam_sql,
                      "Books 1–39 are the Old Testament and 40–66 the New. A verse is counted once per family it contains, however many times the word occurs in it.")
    body += sql_block("The sanctify family, form by form", forms_sql,
                      "Each form is a distinct substring (“sanctify” does not match “sanctified”), so no verse is double-counted within a form.")
    body += sql_block("Why “holy” is left out", holy_sql, "The three sub-counts can overlap and do not add up to the total.")
    body += sql_block(f"Verses using two families — the {len(overlap)} verses above", overlap_sql,
                      "Each <code>LIKE</code> comparison returns 1 or 0, so adding them counts how many families a verse uses.")
    body += "</section>"
    page(PAGES[0][0], "The Words for Sanctification", "Sanctification in the KJV · 1 of 5",
         "Which English words the King James Bible uses for making something holy, how often, and how the vocabulary shifts between the Old and New Testaments.",
         body)


# ---------------------------------------------------------------- 2. across the bible
def build_map():
    book_sql = f"""SELECT b.name AS book, COUNT(*) AS verses_in_book,
       SUM({CORE.replace(chr(10) + '       ', chr(10) + '           ')}) AS sanctification_verses,
       ROUND(1000.0 * SUM({CORE.replace(chr(10) + '       ', chr(10) + '           ')}) / COUNT(*), 1) AS per_1000
FROM KJV_verses v
JOIN KJV_books b ON b.id = v.book_id
GROUP BY b.id, b.name
ORDER BY b.id"""
    books = rows(book_sql)
    assert sum(r[2] for r in books) == 240
    ch_sql = f"""SELECT b.name AS book, v.chapter, COUNT(*) AS sanctification_verses
FROM KJV_verses v
JOIN KJV_books b ON b.id = v.book_id
WHERE {CORE}
GROUP BY b.id, b.name, v.chapter
HAVING COUNT(*) >= 4
ORDER BY sanctification_verses DESC, b.id, v.chapter"""
    chs = rows(ch_sql)
    mx = max(r[2] for r in books)
    cols = []
    for i, (name, n, s, per) in enumerate(books):
        h = 100 * s / mx
        colour = "s1" if i < 39 else "s2"
        lab = f'<span class="cv">{s}</span>' if s >= 9 else ""
        nm = SHORT.get(name, name)
        cols.append(f'<div class="col" title="{e(nm)}: {s} of {n} verses ({per} per 1,000)">{lab}'
                    f'<span class="bar" style="height:{h:.1f}%;background:var(--{colour})"></span>'
                    f'<span class="bn">{e(AXIS.get(name, ""))}</span></div>')
    col_html = "".join(cols)
    ot = sum(r[2] for r in books[:39])
    nt = sum(r[2] for r in books[39:])
    zero = [SHORT.get(r[0], r[0]) for r in books if r[2] == 0]
    dense = sorted(books, key=lambda r: -r[3])[:10]
    dmax = dense[0][3]
    dense_bars = "".join(stacked(SHORT.get(b, b), [(p, "s1" if idx(b) < 39 else "s2", f"{p} per 1,000 verses")], dmax,
                                 small=f"{s} of {n} verses").replace(f"<b>{p}</b> ({p})", f"<b>{p}</b> per 1,000")
                         for b, n, s, p in dense)
    notes = {
        ("Exodus", 29): "The consecration of Aaron and his sons as priests, and of the altar.",
        ("Leviticus", 8): "Moses carries out Exodus 29: the anointing of the tabernacle, the altar and the priests.",
        ("Leviticus", 27): "Houses, fields and firstlings sanctified to the Lord, and how they are valued and redeemed.",
        ("II Chronicles", 29): "Hezekiah has the priests and Levites sanctify themselves and cleanse the temple.",
        ("Leviticus", 22): "The holy things of the children of Israel, and “I the Lord do sanctify them”.",
        ("II Chronicles", 30): "Hezekiah’s Passover, delayed because not enough priests had sanctified themselves.",
        ("Exodus", 19): "The people sanctified “to day and to morrow” before the Lord comes down on Sinai on the third day.",
        ("Exodus", 28): "The priests’ garments, and the gold plate engraved “HOLINESS TO THE LORD”.",
        ("Exodus", 40): "The tabernacle set up, anointed and sanctified.",
        ("Leviticus", 21): "Rules for the priests: “for I the Lord do sanctify him”.",
        ("Numbers", 6): "The Nazarite vow: “the consecration of his God is upon his head”.",
        ("Hebrews", 10): "“… we are sanctified through the offering of the body of Jesus Christ once for all.”",
    }
    ch_items = []
    for b, c, n in chs:
        vs = [(r, t) for r, t in CORE_VERSES.items() if r.startswith(f"{SHORT.get(b, b)} {c}:")]
        assert len(vs) == n
        ch_items.append(f'<li><span class="ref">{SHORT.get(b, b)} {c}<br>{n} verses</span><div class="txt">{notes[(b, c)]}'
                        f'<span class="ctx">{", ".join(r.split(":")[1] for r, _ in vs)}</span></div></li>')
    pent = sum(r[2] for r in books[:5])
    body = stats([(240, "verses"), (ot, "Old Testament"), (nt, "New Testament"), (66 - len(zero), "of 66 books"),
                  (f"{100 * pent / 240:.0f}%", "in Genesis–Deuteronomy")])
    body += insights([
        ("The tabernacle books dominate",
         f"Exodus, Leviticus and Numbers hold {sum(r[2] for r in books[1:4])} of the 240 verses. Exodus 29 alone has {chs[0][2]}, more than any New Testament book."),
        ("Hezekiah’s reform is the second peak",
         f"2 Chronicles has {books[13][2]} verses, {sum(n for b, c, n in chs if b == 'II Chronicles')} of them in chapters 29–30, where the temple is cleansed and the Passover restored."),
        ("In the New Testament, the letters carry it",
         f"The four Gospels have {sum(r[2] for r in books[39:43])} verses between them. 1 Thessalonians has {books[51][2]} in 89 verses, making it the densest book in the Bible."),
        ("Where it never appears",
         f"{len(zero)} books have none, including Proverbs, Daniel, Mark, Galatians, James and Revelation."),
    ], ["s1", "s1", "s2", "s3"])
    body += f"""<div class="panel"><h2>Verses per book, Genesis to Revelation</h2>
<p class="lede">One column per book in canonical order. Hover a column for its exact figures; the full table is below the chart.</p>
<div class="legend"><span class="k"><span class="sw" style="background:var(--s1)"></span>Old Testament ({ot})</span><span class="k"><span class="sw" style="background:var(--s2)"></span>New Testament ({nt})</span></div>
<div class="cols" role="img" aria-label="Column chart of sanctification verses per book; the full figures are in the table below">{col_html}</div>
<details><summary>Show the table for all 66 books</summary><table><thead><tr><th>Book</th><th>Verses in book</th><th>Sanctification verses</th><th>Per 1,000</th></tr></thead><tbody>
{"".join(f"<tr><td>{e(SHORT.get(b, b))}</td><td>{n:,}</td><td>{s}</td><td>{p}</td></tr>" for b, n, s, p in books)}
</tbody></table></details></div>
<div class="panel"><h2>Densest books, per 1,000 verses</h2>
<p class="lede">Counting relative to book length changes the picture: short letters rise. Obadiah and Jude reach the top ten with a single verse each, so treat the smallest books with care.</p>
<div class="hbar">{dense_bars}</div></div>
<div class="panel"><h2>The hotspot chapters</h2>
<p class="lede">Every chapter with four or more verses in the set. Eleven of the twelve come from the Law and the temple history: priests, altar, offerings, vows. The twelfth, Hebrews 10, is the New Testament’s answer to them.</p>
<ul class="vv">{"".join(ch_items)}</ul></div>
"""
    body += '<section class="sql-section"><h2>The queries</h2>'
    body += sql_block("Sanctification verses per book, with density", book_sql,
                      "Each <code>LIKE</code> comparison returns 1 or 0, so <code>SUM</code> of the combined condition counts matching verses per book. Books with no match return 0, not a missing row.")
    body += sql_block("Hotspot chapters (four or more verses)", ch_sql,
                      "The one-line chapter summaries are editorial; the chapter list and counts are the query result.")
    body += sql_block("The 240-verse set itself", CORE_SQL, "See page 1 for how the word list was chosen.")
    body += "</section>"
    page(PAGES[1][0], "Where Sanctification Clusters", "Sanctification in the KJV · 2 of 5",
         "The 240 sanctification verses plotted across all 66 books: where they bunch together, where they thin out, and which chapters carry the most.",
         body, extra_css="""
.cols{display:flex;align-items:flex-end;gap:1px;height:220px;padding-top:18px;border-bottom:1px solid var(--line);font-family:system-ui,sans-serif}
.col{flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;height:100%;position:relative;min-width:0}
.col .bar{width:100%;max-width:14px;border-radius:4px 4px 0 0;min-height:0}
.col .cv{font-size:10px;font-weight:700;color:var(--ink);margin-bottom:2px}
.col .bn{position:absolute;bottom:-17px;font-size:9px;color:var(--soft);white-space:nowrap}
.col:hover .bar{opacity:.75}
@media (max-width:600px){.col .cv{display:none}}
.cols+details{margin-top:24px}
""")


AXIS = {"Leviticus": "Ex–Num", "II Chronicles": "2 Ch", "Psalms": "Ps", "Ezekiel": "Ezek", "Hebrews": "Heb"}


BOOK_IDS = {name: i for i, name in rows("SELECT id, name FROM KJV_books")}


def idx(book):
    return BOOK_IDS[LONG.get(book, book)] - 1


# ---------------------------------------------------------------- 3. God's part and ours
def build_parts():
    god_sql = SELECT + """WHERE v.text LIKE '%Lord that doth sanctify%'
   OR v.text LIKE '%Lord which sanctify%'
   OR v.text LIKE '%Lord, which sanctify%'
   OR v.text LIKE '%Lord do sanctify%'
   OR v.text LIKE '%Lord that sanctify%'
   OR v.text LIKE '%Lord which hallow%'
ORDER BY v.book_id, v.chapter, v.verse"""
    self_sql = SELECT + """WHERE v.text LIKE '%sanctify yourselves%'
   OR v.text LIKE '%sanctify now yourselves%'
   OR v.text LIKE '%sanctify themselves%'
   OR v.text LIKE '%sanctified themselves%'
   OR v.text LIKE '%sanctify myself%'
   OR v.text LIKE '%consecrate yourselves%'
   OR v.text LIKE '%consecrated yourselves%'
   OR v.text LIKE '%consecrate themselves%'
   OR v.text LIKE '%consecrate himself%'
ORDER BY v.book_id, v.chapter, v.verse"""
    holy_sql = SELECT + """WHERE v.text LIKE '%am holy%'
ORDER BY v.book_id, v.chapter, v.verse"""
    god = verses(god_sql)
    selfv = verses(self_sql)
    holy = verses(holy_sql)
    check("god", god, ["Exodus 31:13", "Leviticus 20:8", "Leviticus 21:8", "Leviticus 21:15", "Leviticus 21:23",
                       "Leviticus 22:9", "Leviticus 22:16", "Leviticus 22:32", "Ezekiel 20:12", "Ezekiel 37:28"])
    groups = [
        ("Israel, its priests and Levites", "s1", "Usually before God acts, or before a sacrifice or a holy task", [
            ("Exodus 19:22", "At Sinai, before the Lord comes down on the mount (19:11)."),
            ("Exodus 32:29", "After the golden calf."),
            ("Leviticus 11:44", None), ("Leviticus 20:7", "The next verse answers it: “I am the Lord which sanctify you.”"),
            ("Numbers 11:18", "Before the quails."),
            ("Joshua 3:5", "Before crossing the Jordan."),
            ("Joshua 7:13", "Before the lot falls on Achan."),
            ("1 Samuel 16:5", "Before the anointing of David."),
            ("1 Chronicles 15:12", "Before bringing up the ark."), ("1 Chronicles 15:14", None),
            ("Ezekiel 43:26", "In Ezekiel’s vision of the restored altar."),
        ]),
        ("Hezekiah and Josiah restore the temple", "s3", "Nine verses from two reforms: the house of the Lord cleansed and the Passover kept again", [
            ("2 Chronicles 29:5", None), ("2 Chronicles 29:15", None), ("2 Chronicles 29:31", None),
            ("2 Chronicles 29:34", "“The Levites were more upright in heart to sanctify themselves than the priests.”"),
            ("2 Chronicles 30:3", "The Passover had to be moved to the second month."),
            ("2 Chronicles 30:15", None), ("2 Chronicles 30:24", None), ("2 Chronicles 31:18", None),
            ("2 Chronicles 35:6", "Josiah’s Passover."),
        ]),
        ("Self-sanctification God rejects", "s5", "Sanctifying yourself outside what God commanded", [
            ("2 Chronicles 13:9", "Abijah condemning Jeroboam’s priests."),
            ("Isaiah 66:17", "Pagan rites in the gardens."),
        ]),
        ("“Sanctify myself”", "s6", "The first person singular is said only by the Lord in Ezekiel and by Jesus", [
            ("Ezekiel 38:23", "In the prophecy against Gog."),
            ("John 17:19", "Jesus praying for his disciples on the night before the crucifixion."),
        ]),
    ]
    check("self", selfv, [r for _, _, _, it in groups for r, _ in it])
    god_items = [(r, t, None) for r, t in god.items()]
    left = "".join(card(t, ph, [(r, selfv[r], c) for r, c in it], col) for t, col, ph, it in groups)
    holy_ctx = {"Psalm 86:2": "The only one not spoken by God: the psalmist says it of himself.",
                "1 Peter 1:16": "“Because it is written”: Peter quotes the Leviticus refrain to the church."}
    holy_items = [(r, t, holy_ctx.get(r)) for r, t in holy.items()]
    check("holy", holy, ["Leviticus 11:44", "Leviticus 11:45", "Leviticus 19:2", "Leviticus 20:26", "Leviticus 21:8",
                         "Psalm 86:2", "1 Peter 1:16"])
    lev = sum(1 for r in god if r.startswith("Leviticus"))
    body = stats([(len(selfv), "“sanctify yourselves”"), (len(god), "“I the Lord sanctify you”"), (len(holy), "“I am holy”")])
    body += f"""<div class="panel pair"><div><span class="ref">Leviticus 20:7</span><p>{hl(V('Leviticus 20:7'))}</p></div>
<div class="arrow" aria-hidden="true">⇄</div>
<div><span class="ref">Leviticus 20:8</span><p>{hl(V('Leviticus 20:8'))}</p></div></div>
<p class="sub" style="text-align:center;margin:-8px auto 24px">Two consecutive verses state both sides: the people are to sanctify themselves, and it is the Lord who sanctifies them.</p>"""
    body += insights([
        ("God’s refrain is concentrated in Leviticus",
         f"{lev} of the {len(god)} “I the Lord … sanctify” verses are in Leviticus, all of them in chapters 20–22. Ezekiel repeats it twice, both times as something Israel or the nations will come to know."),
        ("“Against to morrow”",
         "Several commands to sanctify come the day before God acts: Sinai (Exodus 19:10–11), the quails (Numbers 11:18), the Jordan (Joshua 3:5), Achan (Joshua 7:13)."),
        ("The Levites outdo the priests",
         "In Hezekiah’s reform the priests were “too few”, and the Passover itself was delayed because they “had not sanctified themselves sufficiently” (2 Chronicles 29:34, 30:3)."),
        ("“Be ye holy; for I am holy”",
         f"The reason given is always God’s own holiness. The phrase “am holy” is in {len(holy)} verses: five in Leviticus, one in Psalms, and Peter quoting it in 1 Peter 1:16."),
    ], ["s2", "s1", "s3", "s4"])
    body += f"""<div class="sides"><div><h2 class="side-h">Ours: “sanctify yourselves”</h2><p class="lede">Every verse where someone sanctifies or consecrates <em>themselves</em>, grouped by occasion.</p>{left}</div>
<div><h2 class="side-h">God’s: “I am the Lord which sanctify you”</h2><p class="lede">Every verse where the Lord names himself as the one who sanctifies.</p>
{card('The refrain', 'Usually closing a law, as its reason', god_items, 's2')}
{card('“For I am holy”', 'The ground of the command: the holiness of God himself', holy_items, 's4')}</div></div>
"""
    body += '<section class="sql-section"><h2>The queries</h2>'
    body += sql_block(f"“Sanctify yourselves” — the {len(selfv)} verses on the left", self_sql,
                      "These are the verb followed directly by a reflexive pronoun. Grouping them by occasion is editorial, done by reading each verse in its chapter.")
    body += sql_block(f"“I the Lord … sanctify” — the {len(god)} refrain verses", god_sql,
                      "Every spelling of the formula found in the KJV. Leviticus 22:32 uses “hallow” rather than “sanctify”.")
    body += sql_block(f"“I am holy” — {len(holy)} verses", holy_sql,
                      "This one reaches beyond the 240-verse set, since “holy” is not one of its search words (see page 1).")
    body += "</section>"
    page(PAGES[2][0], "God’s Part and Ours", "Sanctification in the KJV · 3 of 5",
         "“Sanctify yourselves” and “I am the Lord which sanctify you” run side by side through the Old Testament. Here is every verse of each.",
         body, extra_css="""
.pair{display:grid;grid-template-columns:1fr auto 1fr;gap:18px;align-items:center;font-size:18px}
.pair p{margin:6px 0 0}
.pair .arrow{font-size:28px;color:var(--soft)}
@media (max-width:640px){.pair{grid-template-columns:1fr}.pair .arrow{text-align:center}}
.pair b{background:color-mix(in srgb,var(--s2) 22%,transparent);border-radius:3px;padding:0 2px}
.sides{display:grid;grid-template-columns:1fr;gap:28px;margin-top:28px}
@media (min-width:860px){.sides{grid-template-columns:1fr 1fr}}
.side-h{font-size:20px;margin:0 0 4px}
.sides .lede{color:var(--soft);margin:0 0 16px;font-size:15px}
""")


# ---------------------------------------------------------------- 4. sources (NT)
def build_sources():
    groups = [
        ("Christ: his offering and blood", "s1", [
            ("1 Corinthians 1:2", "“in Christ Jesus”"), ("1 Corinthians 1:30", "Christ “made unto us … sanctification”"),
            ("1 Corinthians 6:11", "“in the name of the Lord Jesus”"),
            ("Ephesians 5:26", "Christ “gave himself for it” (5:25), the church"), ("Hebrews 2:11", "“he that sanctifieth”"),
            ("Hebrews 10:10", "“the offering of the body of Jesus Christ”"), ("Hebrews 10:14", "“by one offering”"),
            ("Hebrews 10:29", "“the blood of the covenant”"), ("Hebrews 13:12", "“with his own blood”"),
            ("John 17:19", "“I sanctify myself”"), ("1 Peter 1:2", "“sprinkling of the blood of Jesus Christ”")]),
        ("God the Father", "s2", [
            ("Jude 1:1", "“sanctified by God the Father”"), ("1 Thessalonians 5:23", "“the very God of peace”"),
            ("John 17:17", "Jesus asking the “Holy Father” (17:11)"), ("1 Corinthians 1:30", "“of God is made unto us”"),
            ("2 Thessalonians 2:13", "“God hath … chosen you”"), ("1 Peter 1:2", "“the foreknowledge of God the Father”"),
            ("Hebrews 12:10", "“the Father of spirits” (12:9) chastening his children"),
            ("John 10:36", "the Father sanctifying the Son")]),
        ("The word and the truth", "s3", [
            ("John 17:17", "“thy word is truth”"), ("John 17:19", "“through the truth”"),
            ("Ephesians 5:26", "“by the word”"), ("Acts 20:32", "“the word of his grace”"),
            ("2 Thessalonians 2:13", "“belief of the truth”"), ("1 Timothy 4:5", "“the word of God and prayer”")]),
        ("The Holy Spirit", "s4", [
            ("Romans 15:16", "“by the Holy Ghost”"), ("1 Corinthians 6:11", "“by the Spirit of our God”"),
            ("2 Thessalonians 2:13", "“sanctification of the Spirit”"), ("1 Peter 1:2", "“sanctification of the Spirit”")]),
        ("Faith", "s5", [("Acts 26:18", "“by faith that is in me”"), ("2 Thessalonians 2:13", "“belief of the truth”")]),
    ]
    things = [("Matthew 23:17", "The temple sanctifies the gold."), ("Matthew 23:19", "The altar sanctifies the gift."),
              ("1 Corinthians 7:14", "A believing spouse sanctifies an unbelieving one."),
              ("1 Timothy 4:5", "Food is sanctified by the word of God and prayer (4:3–4)."),
              ("Hebrews 9:13", "The blood of bulls and goats sanctified “to the purifying of the flesh” — the comparison that 9:14 completes with “how much more … the blood of Christ”.")]
    for _, _, it in groups:
        for r, _ in it:
            assert r in NT, r
    named = {r for _, _, it in groups for r, _ in it}
    mx = max(len(it) for _, _, it in groups)
    bars = "".join(stacked(t, [(len(it), c, f"{t}: {len(it)} verses")], mx).replace(f"({len(it)})", "verses")
                   for t, c, it in groups)
    cards = "".join(card(t, None, [(r, NT[r], c) for r, c in it], col) for t, col, it in groups)
    cards += card("Things that sanctify other things", "Five verses where the sanctifier is not God or a means of grace", [(r, NT[r], c) for r, c in things], "s6")
    body = stats([(46, "New Testament verses"), (len(named), "name who or what sanctifies"), (len(groups), "sources"),
                  (len(things), "things sanctifying things")])
    body += insights([
        ("Christ’s offering is named most",
         f"{len(groups[0][2])} verses connect sanctification to Christ, five of them in Hebrews: “by one offering he hath perfected for ever them that are sanctified” (10:14)."),
        ("Father, Son and Spirit together",
         "1 Peter 1:2 names all three in one verse, in order: the Father’s foreknowledge, the Spirit’s sanctification, the blood of Jesus Christ. 1 Corinthians 6:11 names the Lord Jesus and “the Spirit of our God” together."),
        ("Jesus himself is sanctified",
         "“Whom the Father hath sanctified, and sent into the world” (John 10:36); “for their sakes I sanctify myself” (John 17:19)."),
        ("Sanctification can be shared",
         "In 1 Corinthians 7:14 holiness spreads from a believing spouse to an unbelieving one and to the children: “else were your children unclean; but now are they holy”."),
    ], ["s1", "s2", "s6", "s5"])
    body += f"""<div class="panel"><h2>Who or what sanctifies, in the New Testament</h2>
<p class="lede">The New Testament verses of the 240-verse set ({len(NT)} verses), placed under every source they name as sanctifying, or as the means of it. A verse naming two sources is counted under both, so the bars add up to more than {len(named)}. The grouping is editorial: it comes from reading the verse and, where noted, the verses around it.</p>
<div class="hbar">{bars}</div></div>
<div class="grid">{cards}</div>
"""
    body += '<section class="sql-section"><h2>The query</h2>'
    body += sql_block(f"The {len(NT)} New Testament verses", NT_SQL,
                      f"{len(named)} of these name a source and are grouped above; four more appear only in the “things that sanctify” card (1 Timothy 4:5 is in both). The rest (such as “Hallowed be thy name”) are about something other than who sanctifies, and appear on page 5. The grouping itself is editorial and not in the query.")
    body += "</section>"
    page(PAGES[3][0], "Who Sanctifies?", "Sanctification in the KJV · 4 of 5",
         "In the New Testament, who or what does the sanctifying? The Father, Christ’s offering, the Spirit, the word, faith, and a few surprises.",
         body)


# ---------------------------------------------------------------- 5. already / now / not yet
def build_tenses():
    cols = [
        ("Already", "s1", "Stated as done: believers “are sanctified”", [
            ("Acts 20:32", None), ("Acts 26:18", None), ("Romans 15:16", None), ("1 Corinthians 1:2", None),
            ("1 Corinthians 1:30", None), ("1 Corinthians 6:11", "“Such were some of you: but ye are … sanctified.”"),
            ("2 Thessalonians 2:13", None), ("Hebrews 2:11", None), ("Hebrews 10:10", "“Once for all.”"),
            ("Hebrews 10:14", "“Perfected for ever.”"), ("Hebrews 10:29", "A warning to one who was sanctified and turns away."),
            ("Hebrews 13:12", None), ("1 Peter 1:2", None), ("Jude 1:1", None)]),
        ("Now", "s3", "Commanded, prayed for or worked out day by day", [
            ("Luke 1:75", "“All the days of our life.”"), ("John 17:17", "Jesus praying for it."),
            ("Romans 6:19", None), ("Romans 6:22", None), ("2 Corinthians 7:1", "“Perfecting holiness” — still in progress."),
            ("Ephesians 4:24", None), ("1 Thessalonians 2:10", "Paul’s own conduct."), ("1 Thessalonians 4:3", None),
            ("1 Thessalonians 4:4", None), ("1 Thessalonians 4:7", None), ("1 Timothy 2:15", None),
            ("2 Timothy 2:21", None), ("Titus 2:3", None), ("Hebrews 12:10", "Through the Father’s discipline."),
            ("Hebrews 12:14", "Follow it: “without which no man shall see the Lord.”")]),
        ("Not yet", "s2", "Completed at the coming of Christ", [
            ("Ephesians 5:26", "The purpose runs into 5:27: “that he might present it to himself a glorious church … holy and without blemish.”"),
            ("1 Thessalonians 3:13", None), ("1 Thessalonians 5:23", None)]),
    ]
    other = [
        ("God himself is hallowed", "s4", [("Matthew 6:9", None), ("Luke 11:2", None), ("1 Peter 3:15", None)]),
        ("Christ sanctified and consecrated", "s6", [("John 10:36", None), ("John 17:19", "For his disciples’ sakes."),
                                                     ("Romans 1:4", None), ("Hebrews 7:28", None), ("Hebrews 10:20", None)]),
        ("Things, and a disclaimer", "s5", [("Matthew 23:17", None), ("Matthew 23:19", None), ("1 Corinthians 7:14", None),
                                            ("1 Timothy 4:5", None), ("Hebrews 9:13", None),
                                            ("Acts 3:12", "Peter denies that the healing came by his own holiness.")]),
    ]
    allrefs = [r for *_, it in cols for r, _ in it] + [r for *_, it in other for r, _ in it]
    check("tenses", allrefs, NT)
    n = [len(it) for *_, it in cols]
    tot = sum(n)
    bar = "".join(f'<span style="flex:{k};background:var(--{c})" title="{t}: {k} verses"></span>' for (t, c, _, _), k in zip(cols, n))
    labels = "".join(f'<div style="flex:{k}"><b>{t}</b> {k}</div>' for (t, c, _, _), k in zip(cols, n))
    passive = sum("sanctified" in NT[r] for r, _ in cols[0][3])
    col_html = "".join(f'<div>{card(t, ph, [(r, NT[r], c) for r, c in it], col)}</div>' for t, col, ph, it in cols)
    other_html = "".join(card(t, None, [(r, NT[r], c) for r, c in it], col) for t, col, it in other)
    heb = {k: sum(r.startswith("Hebrews") for r, _ in it) for k, _, _, it in cols}
    body = stats([(46, "New Testament verses"), (n[0], "already"), (n[1], "now"), (n[2], "not yet"), (46 - tot, "about something else")])
    body += f"""<div class="panel"><h2>The {tot} verses about believers’ sanctification</h2>
<p class="lede">Each New Testament verse of the 240-verse set that speaks of believers being sanctified or holy, placed by when it says that happens. The {46 - tot} others are about God, Christ or objects, and are listed at the end. Placing a verse is editorial: it follows the verse’s own wording and, where noted, the verses around it.</p>
<div class="tri" role="img" aria-label="{', '.join(f'{t} {k}' for (t, *_), k in zip(cols, n))}">{bar}</div><div class="tri-l">{labels}</div></div>
"""
    body += insights([
        ("“Are sanctified” — a finished fact",
         f"{passive} of the {n[0]} “already” verses use “sanctified”, always passive: something done to believers, not by them."),
        ("Hebrews holds both ends",
         f"Hebrews has {heb['Already']} “already” verses (“perfected for ever”, 10:14) and {heb['Now']} “now” verses (“follow … holiness”, 12:14)."),
        ("1 Thessalonians looks ahead",
         "Two of the three “not yet” verses are in 1 Thessalonians, and both look to “the coming of our Lord Jesus Christ” (3:13, 5:23)."),
        ("The “now” verses are about life",
         "Sexual conduct, behaviour, service and discipline: “For this is the will of God, even your sanctification, that ye should abstain from fornication” (1 Thessalonians 4:3)."),
    ], ["s1", "s3", "s2", "s3"])
    body += f'<div class="three">{col_html}</div><h2 class="side-h">About something else</h2><div class="grid">{other_html}</div>'
    body += '<section class="sql-section"><h2>The query</h2>'
    body += sql_block(f"The {len(NT)} New Testament verses", NT_SQL,
                      "Every row is placed in exactly one group on this page. The groups are editorial and not in the query.")
    body += "</section>"
    page(PAGES[4][0], "Already, Now, Not Yet", "Sanctification in the KJV · 5 of 5",
         "The New Testament speaks of sanctification as done, as being done and as still to come. Here is each of its verses, sorted by which.",
         body, extra_css="""
.tri{display:flex;gap:2px;height:22px;margin-top:8px}
.tri span:first-child{border-radius:4px 0 0 4px}.tri span:last-child{border-radius:0 4px 4px 0}
.tri-l{display:flex;gap:2px;font-family:system-ui,sans-serif;font-size:13px;color:var(--soft);margin-top:6px}
.tri-l div{min-width:64px}
.tri-l b{color:var(--ink)}
.three{display:grid;grid-template-columns:1fr;gap:22px;margin:8px 0 28px}
@media (min-width:900px){.three{grid-template-columns:1fr 1fr 1fr}.three ul.vv li{grid-template-columns:1fr;gap:2px}}
.side-h{font-size:20px;margin:0 0 14px}
""")


build_vocab()
build_map()
build_parts()
build_sources()
build_tenses()
print("ok")
