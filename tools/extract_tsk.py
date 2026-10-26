"""Extract Treasury of Scripture Knowledge cross references from BibleWorks 10 (tsk.xrd).

Usage: python extract_tsk.py [path-to-tsk.xrd] [output-dir]

Writes:
  tsk_links.csv   one row per reference: from_verse, keyword, to_start, to_end
  chapters.json / books.json   aggregated graphs used by the galaxy page
"""
import csv, json, os, re, struct, sys
from collections import Counter

SRC = sys.argv[1] if len(sys.argv) > 1 else r"C:\Program Files (x86)\BibleWorks 10\databases\tsk.xrd"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "data")

BOOKS = ("Gen Exo Lev Num Deu Jos Jdg Rut 1Sa 2Sa 1Ki 2Ki 1Ch 2Ch Ezr Neh Est Job Psa Pro Ecc Sol Isa Jer "
         "Lam Eze Dan Hos Joe Amo Oba Jon Mic Nah Hab Zep Hag Zec Mal Mat Mar Luk Joh Act Rom 1Co 2Co Gal Eph "
         "Phi Col 1Th 2Th 1Ti 2Ti Tit Phm Heb Jam 1Pe 2Pe 1Jo 2Jo 3Jo Jud Rev").split()
NAMES = ("Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|1 Samuel|2 Samuel|1 Kings|2 Kings|"
         "1 Chronicles|2 Chronicles|Ezra|Nehemiah|Esther|Job|Psalms|Proverbs|Ecclesiastes|Song of Songs|Isaiah|"
         "Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|Jonah|Micah|Nahum|Habakkuk|Zephaniah|"
         "Haggai|Zechariah|Malachi|Matthew|Mark|Luke|John|Acts|Romans|1 Corinthians|2 Corinthians|Galatians|"
         "Ephesians|Philippians|Colossians|1 Thessalonians|2 Thessalonians|1 Timothy|2 Timothy|Titus|Philemon|"
         "Hebrews|James|1 Peter|2 Peter|1 John|2 John|3 John|Jude|Revelation").split("|")
BIDX = {b: i for i, b in enumerate(BOOKS)}

data = open(SRC, "rb").read()
REF = re.compile(rb"([\x05-\x0c])((?:%s) \d{1,3}:\d{1,3})" % b"|".join(b.encode() for b in BOOKS))
KEY = re.compile(rb"\xff\xff\xff\xff\x00(....)", re.S)

def parse(ref):
    b, cv = ref.split(" ")
    c, v = cv.split(":")
    return BIDX[b], int(c), int(v)

# Tokenise: length-prefixed references (length byte must equal string length) and keyword headers.
events = []
for m in REF.finditer(data):
    if m.group(1)[0] == len(m.group(2)):
        events.append((m.start(), m.end(), "ref", m.group(2).decode()))
for m in KEY.finditer(data):
    n = struct.unpack("<I", m.group(1))[0]
    if 0 < n < 400:
        events.append((m.start(), m.end() + n, "key", data[m.end():m.end() + n].decode("cp1252").rstrip(".")))
events.sort()

rows, anchor, keyword, i = [], None, "", 0
while i < len(events):
    s, e, kind, val = events[i]
    if kind == "key":
        keyword = val
    elif i + 1 < len(events) and events[i + 1][2] == "ref" and events[i + 1][0] == e:
        rows.append((anchor, keyword, val, events[i + 1][3]))   # (start, end) pair
        i += 1
    elif data[s - 4:s] == b"\xff\xff\xff\xff":
        anchor, keyword = val, ""                                # new verse entry
    i += 1
rows = [r for r in rows if r[0]]

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "tsk_links.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["from_verse", "keyword", "to_start", "to_end"])
    w.writerows(rows)

# Aggregate. A range spanning chapters counts once for every chapter it touches.
chap_links, book_links, chap_deg, chap_verses = Counter(), Counter(), Counter(), {}
for a, _, s, e in rows:
    ab, ac, av = parse(a)
    sb, sc, _ = parse(s)
    eb, ec, _ = parse(e)
    src = (ab, ac)
    chap_verses[src] = max(chap_verses.get(src, 0), av)
    targets = {(sb, c) for c in range(sc, (ec if eb == sb else sc) + 1)}
    for t in targets:
        if t == src:
            continue
        chap_links[tuple(sorted((src, t)))] += 1
        if t[0] != ab:
            book_links[tuple(sorted((ab, t[0])))] += 1

# Chapter count per book from what TSK covers.
nchap = Counter()
for (b, c) in chap_verses:
    nchap[b] = max(nchap[b], c)
for (x, y) in chap_links:
    for b, c in (x, y):
        nchap[b] = max(nchap[b], c)
for (x, y), n in chap_links.items():
    chap_deg[x] += n; chap_deg[y] += n

book_deg = Counter()
for (x, y), n in book_links.items():
    book_deg[x] += n; book_deg[y] += n

def cid(b, c): return f"{BOOKS[b]} {c}"

chapters = {
    "nodes": [{"id": cid(b, c), "b": b, "c": c, "deg": chap_deg[(b, c)]}
              for b in range(66) for c in range(1, nchap[b] + 1)],
    "links": [[cid(*x), cid(*y), n] for (x, y), n in chap_links.items()],
}
books = {
    "nodes": [{"id": BOOKS[b], "b": b, "name": NAMES[b], "chapters": nchap[b], "deg": book_deg[b]} for b in range(66)],
    "links": [[BOOKS[x], BOOKS[y], n] for (x, y), n in book_links.items()],
}
for name, obj in (("chapters.json", chapters), ("books.json", books)):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, separators=(",", ":"))

print(f"references: {len(rows):,}  anchor verses: {len({r[0] for r in rows}):,}")
print(f"chapters: {len(chapters['nodes']):,} nodes, {len(chap_links):,} links")
print(f"books: 66 nodes, {len(book_links):,} links")
top = sorted(chap_deg.items(), key=lambda kv: -kv[1])[:10]
print("most-connected chapters:", ", ".join(f"{cid(*k)} ({v:,})" for k, v in top))
