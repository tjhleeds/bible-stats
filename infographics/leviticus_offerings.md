# The five offerings (Leviticus 1–7)

Leviticus opens with instructions for five offerings — the burnt, meat,
peace, sin, and trespass offerings — given to Moses at the tabernacle. This
doc compares them facet by facet, using direct quotations from `KJV.db`
only (no outside commentary). An illustrated HTML version of the same
comparison is at [`leviticus_offerings.html`](leviticus_offerings.html).

Query used to pull the source text:

```bash
python3 -c "
import sqlite3
con = sqlite3.connect('file:data/KJV.db?mode=ro', uri=True)
for row in con.execute('''
    SELECT v.chapter, v.verse, v.text
    FROM KJV_verses v
    JOIN KJV_books b ON b.id = v.book_id
    WHERE b.name = 'Leviticus' AND v.chapter BETWEEN 1 AND 7
    ORDER BY v.chapter, v.verse
'''):
    print(f'{row[0]}:{row[1]} {row[2]}')
"
```

Run the same query online against `data/KJV.db` in this repo:
[Open in Datasette Lite](https://lite.datasette.io/?url=https%3A%2F%2Fraw.githubusercontent.com%2Ftjhleeds%2Fbible-stats%2F279a0c7d6e2e71bead032b0b26915d5c6208f844%2Fdata%2FKJV.db#/KJV?sql=SELECT+v.chapter%2C+v.verse%2C+v.text%0AFROM+KJV_verses+v%0AJOIN+KJV_books+b+ON+b.id+%3D+v.book_id%0AWHERE+b.name+%3D+%27Leviticus%27+AND+v.chapter+BETWEEN+1+AND+7%0AORDER+BY+v.chapter%2C+v.verse)

| | Burnt Offering<br>*Lev. 1; 6:8–13* | Meat Offering<br>*Lev. 2; 6:14–23* | Peace Offering<br>*Lev. 3; 7:11–34* | Sin Offering<br>*Lev. 4:1–5:13; 6:24–30* | Trespass Offering<br>*Lev. 5:14–6:7; 7:1–10* |
|---|---|---|---|---|---|
| **When it is offered** | "he shall offer it of his own voluntary will" (1:3) | "when any will offer a meat offering unto the Lord" (2:1) | "If he offer it for a thanksgiving" — or "a vow, or a voluntary offering" (7:12, 16) | "If a soul shall sin through ignorance against any of the commandments of the Lord" (4:2) | "If a soul commit a trespass, and sin through ignorance, in the holy things of the Lord" — or having "lied unto his neighbour … or deceived his neighbour" (5:15; 6:2) |
| **What is offered** | "of the herd, and of the flock", a male without blemish; or "turtledoves, or … young pigeons" (1:2–3, 10, 14) | "fine flour; and he shall pour oil upon it, and put frankincense thereon" (2:1) | "of the herd; whether it be a male or female … without blemish", or "of the flock" (3:1, 6) | Priest or congregation: "a young bullock without blemish". A ruler: "a kid of the goats, a male without blemish". One of the people: "a kid of the goats, a female without blemish". If poor: "two turtledoves, or two young pigeons", or "the tenth part of an ephah of fine flour" (4:3, 14, 23, 28; 5:7, 11) | "a ram without blemish out of the flock" (5:15, 18; 6:6) |
| **Laying on of hands** | "he shall put his hand upon the head of the burnt offering; and it shall be accepted for him to make atonement for him" (1:4) | *Not recorded for this offering.* | "he shall lay his hand upon the head of his offering, and kill it" (3:2) | "the elders of the congregation shall lay their hands upon the head of the bullock"; "he shall lay his hand upon the head of the sin offering" (4:15, 29) | *Not recorded for this offering.* |
| **The blood** | "the priests, Aaron's sons, shall bring the blood, and sprinkle the blood round about upon the altar" (1:5) | *None — a bloodless offering of flour, oil, and frankincense.* | "Aaron's sons the priests shall sprinkle the blood upon the altar round about" (3:2) | Priest or congregation: sprinkled "seven times before the Lord, before the vail" and put "upon the horns of the altar of sweet incense". Ruler or one of the people: put "upon the horns of the altar of burnt offering" (4:6–7, 25, 30) | "the blood thereof shall he sprinkle round about upon the altar" (7:2) |
| **What is burnt** | "the priest shall burn all on the altar, to be a burnt sacrifice, an offering made by fire, of a sweet savour unto the Lord" (1:9) | "the priest shall take from the meat offering a memorial thereof, and shall burn it upon the altar" (2:9) | "the fat that covereth the inwards … the two kidneys … the caul above the liver" — "all the fat is the Lord's" (3:3–4, 16) | "he shall take off from it all the fat … and burn them upon the altar"; the priest's or congregation's bullock is carried "without the camp" and burned entire (4:8, 10, 12, 21) | "all the fat thereof; the rump, and the fat that covereth the inwards … the priest shall burn them upon the altar" (7:3–5) |
| **What is eaten** | *Not eaten* — only "the priest … shall have to himself the skin of the burnt offering" (7:8) | "the remnant of the meat offering shall be Aaron's and his sons' … with unleavened bread shall it be eaten in the holy place" (2:3; 6:16) | "the breast shall be Aaron's and his sons'"; "the right shoulder shall ye give unto the priest"; the remainder "eaten the same day that it is offered" (7:15, 31–32) | "The priest that offereth it for sin shall eat it: in the holy place … All the males among the priests shall eat thereof" (6:26, 29) | "Every male among the priests shall eat thereof: it shall be eaten in the holy place: it is most holy" (7:6) |
| **Distinctive feature** | "The fire shall ever be burning upon the altar; it shall never go out" (6:13) | "with all thine offerings thou shalt offer salt"; "No meat offering … shall be made with leaven … nor any honey" (2:11, 13) | Eaten on the third day, "it shall not be accepted … it shall be an abomination" (7:18) | "no sin offering, whereof any of the blood is brought into the tabernacle of the congregation to reconcile withal in the holy place, shall be eaten: it shall be burnt in the fire" (6:30) | "he shall make amends for the harm that he hath done … and shall add the fifth part thereto" (5:16; 6:5) |

All quotations are King James Version text from `data/KJV.db`, Leviticus
chapters 1–7.
