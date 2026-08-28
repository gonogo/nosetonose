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

## Recent schema notes

- People: `team-facilitator`, `associate-facilitator`, `team-passed-away` (no separate `team` type)
- Courses and venues: `region` and venue `location` fields for regional grouping in the site
