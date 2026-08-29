# Agent guide

Three-stage pipeline: **scrape → extract → build**. See [README.md](README.md) for quick start.

## Context for AI agents

| Resource | Purpose |
|----------|---------|
| [.cursor/rules/](.cursor/rules/) | Architecture and edit-location guidance (auto-injected in Cursor) |
| [docs/](docs/) | Full schemas, extraction logic, web generator docs |
| [docs/content-item.schema.json](docs/content-item.schema.json) | Raw scrape JSON schema |
| [docs/structured-data.schema.json](docs/structured-data.schema.json) | Structured course/venue/people schema |
| [.cursor/skills/nosetonose-pipeline/SKILL.md](.cursor/skills/nosetonose-pipeline/SKILL.md) | Pipeline workflow checklists |
| [sveltia/README.md](sveltia/README.md) | SvelteKit + Sveltia CMS site (separate from `web/`; course types vs events) |

## Pipeline commands

```bash
./scripts/scrape_all.sh              # Stage 1 → data/
python scripts/extract_structured.py # Stage 2 → data/structured/
python scripts/build_web.py          # Stage 3 → web/
```

## Where to edit

- **Raw content / scraping** → `ntn_scraper/`, `data/*.json`, `data/bodies/*.md`
- **Editorial pages** (Approach, Booking, …) → `data/*.md` + `EDITORIAL_PAGES` in `build_web.py`
- **Structured fields** → `scripts/extract_structured.py`
- **HTML / CSS / rendering** → `scripts/build_web.py` (not `web/` directly)
- **SvelteKit site / CMS** → `sveltia/` (see [sveltia/README.md](sveltia/README.md)); optional refresh via `cd sveltia && npm run sync-data`
- **Course types** (Sveltia only) → `sveltia/src/lib/data/course-types/` or CMS **Course types**; not produced by the Python extract

## Recent schema notes

- People: `team-facilitator`, `associate-facilitator`, `team-passed-away` (no separate `team` type)
- Courses and venues: `region` and venue `location` fields for regional grouping in the site
- Sveltia: dated listings in `courses/` may set `course` to a course-type `id`; blank listing fields inherit from that type. The Python `web/` site still treats each listing as a standalone course.
