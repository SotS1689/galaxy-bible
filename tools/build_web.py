"""Pack data/chapters.json + data/books.json into site/data.js for the galaxy page."""
import json, os

ROOT = os.path.join(os.path.dirname(__file__), "..")
# Every chapter link is kept: the page draws the strongest N, but the book focus filter
# needs all links between the chosen books.
MAX_CHAPTER_LINKS = None

ch = json.load(open(os.path.join(ROOT, "data", "chapters.json")))
bk = json.load(open(os.path.join(ROOT, "data", "books.json")))

cidx = {n["id"]: i for i, n in enumerate(ch["nodes"])}
clinks = sorted(ch["links"], key=lambda l: -l[2])[:MAX_CHAPTER_LINKS]
bidx = {n["id"]: i for i, n in enumerate(bk["nodes"])}

out = {
    "books": [[n["id"], n["name"], n["chapters"], n["deg"]] for n in bk["nodes"]],
    "bookLinks": [[bidx[a], bidx[b], w] for a, b, w in sorted(bk["links"], key=lambda l: -l[2])],
    "chapters": [[n["b"], n["c"], n["deg"]] for n in ch["nodes"]],
    "chapterLinks": [[cidx[a], cidx[b], w] for a, b, w in clinks],
    "totalRefs": sum(1 for _ in open(os.path.join(ROOT, "data", "tsk_links.csv"), encoding="utf-8")) - 1,
}
# Saved star positions + camera (captured from the page) become the starting layout.
layout_path = os.path.join(ROOT, "data", "layout.json")
if os.path.exists(layout_path):
    out["layout"] = json.load(open(layout_path))
os.makedirs(os.path.join(ROOT, "site"), exist_ok=True)
with open(os.path.join(ROOT, "site", "data.js"), "w", encoding="utf-8") as f:
    f.write("window.TSK=" + json.dumps(out, separators=(",", ":")) + ";\n")
print("wrote site/data.js", os.path.getsize(os.path.join(ROOT, "site", "data.js")) // 1024, "KB")
