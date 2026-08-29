---
name: nosetonose-pipeline
description: Run the Nose to Nose scrape-extract-build pipeline, add structured fields end-to-end, or rebuild the static site. Use when scraping nosetonose.info, refreshing data, adding course/people fields, or changing static HTML output.
---

# Nose to Nose pipeline

## Full rebuild

```bash
source .venv/bin/activate
./scripts/scrape_all.sh
python scripts/extract_structured.py
python scripts/build_web.py
python3 -m http.server --directory web 8080
```

Preview: [http://localhost:8080](http://localhost:8080)

## Task checklist

```
- [ ] Stage 1: scrape (if raw data changed)
- [ ] Stage 2: extract (if courses/people/structured data changed)
- [ ] Stage 3: build (always after data changes)
- [ ] Preview locally
```

## Common shortcuts

| Task | Commands |
|------|----------|
| Rendering only | `python scripts/build_web.py` |
| Structured data only | `python scripts/extract_structured.py && python scripts/build_web.py` |
| Manual JSON fix | Edit `data/structured/*.json`, then `python scripts/build_web.py` |
| Raw content edit | Edit `data/bodies/*.md` or `data/*.json`, then `python scripts/build_web.py` |
| Editorial page copy | Edit `data/approach.md` (etc.), then `python scripts/build_web.py` |

## Add a new structured field (end-to-end)

1. **Extract** — add parsing in `scripts/extract_structured.py` (typically `extract_courses()` or people merge in `main()`)
2. **Schema** — update `docs/structured-data.schema.json` and `docs/STRUCTURED_DATA.md`
3. **Render** — add field to `build_course_page()` or `build_person_page()` in `scripts/build_web.py`
4. **Rebuild** — `python scripts/extract_structured.py && python scripts/build_web.py`

## Add a new editorial page

1. Create `data/{slug}.md` with Markdown body
2. Add entry to `EDITORIAL_PAGES` in `scripts/build_web.py`
3. `python scripts/build_web.py`

## Fix rendering only

Edit `scripts/build_web.py` (`build_*()` for layout, `build_style()` for CSS, `markdown_to_html()` for Markdown). Do **not** edit `web/style.css` directly.

Then: `python scripts/build_web.py`

## Gotchas

- `data/people.json` (whole team pages) ≠ `data/structured/people.json` (individual people)
- Person types are `team-facilitator`, `associate-facilitator`, `team-passed-away` — not `facilitator` or `team`
- Stage 1 merges by `id`; Stages 2 and 3 fully overwrite their outputs
- UK courses only in structured export currently
- `data/pages_content_analysis.json` is optional; content-analysis page shows a placeholder if missing
- Sveltia course types (`sveltia/src/lib/data/course-types/`) are CMS-owned and are not produced by this pipeline. Syncing into `sveltia/` preserves listing `course` relations and does not overwrite course types.

## Documentation

- [docs/SCRAPING.md](../../docs/SCRAPING.md) — raw scrape, ContentItem, spiders
- [docs/STRUCTURED_DATA.md](../../docs/STRUCTURED_DATA.md) — course/venue/people schemas
- [docs/WEB.md](../../docs/WEB.md) — static site pages, Markdown support
- [sveltia/README.md](../../sveltia/README.md) — SvelteKit site; course types vs dated listings
- [.cursor/rules/](../../.cursor/rules/) — architecture and file-scoped edit guides
