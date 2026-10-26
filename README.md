# Galaxy Bible

A 3D view of the Treasury of Scripture Knowledge (TSK) cross references from BibleWorks 10.

## Data

`tools/extract_tsk.py` reads `C:\Program Files (x86)\BibleWorks 10\databases\tsk.xrd` (read-only) and writes to `data/`:

| File | Contents |
|---|---|
| `tsk_links.csv` | 380,538 rows: `from_verse, keyword, to_start, to_end` (TSK keyword headings kept; ranges kept as start/end) |
| `chapters.json` | 1,189 chapters, 140,557 weighted chapter↔chapter links |
| `books.json` | 66 books, 2,026 weighted book↔book links |

Link weight = number of TSK references between the two chapters/books (either direction). A range that spans chapters counts once for each chapter.

`tools/build_web.py` packs the strongest 30,000 chapter links and all book links into `site/data.js`.
If `data/layout.json` exists (star positions + camera captured from the page), it is included and the page
opens in exactly that arrangement instead of running the layout simulation.

## Rebuild

```
python tools/extract_tsk.py
python tools/build_web.py
```

## Site

`site/` is a static page (three.js + 3d-force-graph from unpkg). Serve it with `python -m http.server --directory site`, or publish the folder with GitHub Pages.
