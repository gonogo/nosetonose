# Nose to Nose — structured content scrape

Scrapy project that extracts rebuild-ready structured content from
[nosetonose.info](https://www.nosetonose.info/), then derives clean course/venue/people
JSON and a plain static HTML browser (courses, people, and scraped site content).

## Documentation

| Doc | Contents |
|-----|----------|
| [AGENTS.md](AGENTS.md) | Agent/AI context entry point |
| [.cursor/rules/](.cursor/rules/) | Cursor rules — architecture and edit guides |
| [docs/SCRAPING.md](docs/SCRAPING.md) | Scrapy spiders, raw JSON schema, coverage |
| [docs/STRUCTURED_DATA.md](docs/STRUCTURED_DATA.md) | Course/venue/people extraction |
| [docs/WEB.md](docs/WEB.md) | Static HTML site generator |

**JSON schemas:**

- Raw scrape items: [docs/content-item.schema.json](docs/content-item.schema.json)
- Structured data: [docs/structured-data.schema.json](docs/structured-data.schema.json)

---

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Full pipeline

```bash
# 1. Scrape the live site (legacy HTML + WordPress + UK courses)
./scripts/scrape_all.sh

# 2. Extract structured courses, venues, and people (Markdown text blocks)
python scripts/extract_structured.py

# 3. Build static HTML site (courses, people, all other content)
python scripts/build_web.py

# 4. Preview locally
python3 -m http.server --directory web 8080
```

Open [http://localhost:8080](http://localhost:8080) (courses),
[http://localhost:8080/people.html](http://localhost:8080/people.html), or
[http://localhost:8080/other-content.html](http://localhost:8080/other-content.html) (articles, pages, thoughts, etc.).

---

## Stage 1: Scrape (`data/`)

| Command | Spider | Source |
|---------|--------|--------|
| `./scripts/scrape_all.sh` | all three | Recommended |
| `scrapy crawl legacy` | Dreamweaver `.htm` pages |
| `scrapy crawl wordpress` | WP REST pages + testimonials |
| `scrapy crawl courses` | UK course/event HTML listings |

Optional historical course archive:

```bash
scrapy crawl legacy -s INCLUDE_COURSE_ARCHIVE=True
```

### Raw output

| File | Contents |
|------|----------|
| `pages.json` | About, approach, booking, contact, WP pages |
| `people.json` | Team / facilitator pages |
| `articles.json` | Published articles |
| `thoughts.json` | Thoughts pages |
| `testimonials.json` | WP posts (often testimonials) |
| `courses_current.json` | Current UK course/event pages |
| `course_archive.json` | Historical flyers (archive flag only) |
| `bodies/*.md` | Markdown bodies with YAML front matter |

Each record: `id`, `type`, `source_url`, `title`, `region`, `language`,
`body_html`, `body_markdown`, `images`, `scraped_at`. See [docs/SCRAPING.md](docs/SCRAPING.md).

---

## Stage 2: Structured data (`data/structured/`)

```bash
python scripts/extract_structured.py
```

| File | Contents |
|------|----------|
| `courses.json` | 33 UK courses — dates, fees, Markdown descriptions (with links), venue/facilitator refs |
| `venues.json` | Deduplicated venues (name, address, email, phone) |
| `people.json` | Deduplicated people — type, status, country, region, bio, photo; `source_urls` for non-facilitators |

No HTML in output. Courses link to venues and facilitators by `id`.
See [docs/STRUCTURED_DATA.md](docs/STRUCTURED_DATA.md).

---

## Stage 3: Static web site (`web/`)

```bash
python scripts/build_web.py
```

Generates plain semantic HTML:

- **Course list** — sorted by start date, links to detail pages
- **Course detail** — all structured fields; venue/facilitator names resolved
- **People list** — four sections (facilitators, team, previous associates, in memory)
- **Person detail** — photo, background, courses (facilitators only), source links
  (non-facilitators only); placeholders when data is missing
- **All other content** — index of scraped pages (articles, thoughts, site pages,
  testimonials, team) with sidebar navigation; one detail page per item under
  `web/content/`

See [docs/WEB.md](docs/WEB.md).

---

## Project layout

```text
ntn_scraper/              # Scrapy project
  cleaners.py             # HTML cleaning + Markdown conversion
  items.py                # ContentItem definition
  pipelines.py            # JSON + Markdown body writers
  settings.py
  spiders/
    legacy.py             # Dreamweaver HTML
    wordpress.py          # WP REST API
    courses.py            # UK Events Manager HTML
scripts/
  scrape_all.sh           # Run all spiders
  extract_structured.py   # courses/venues/people JSON
  build_web.py            # Static HTML generator
data/                     # Scrape output
  structured/             # Extracted course data
  bodies/                 # Markdown mirrors
web/                      # Generated static site
  index.html              # Course list
  people.html             # People (from structured data)
  other-content.html      # Scraped content index (articles, pages, …)
  courses/ people/ content/
docs/                     # Documentation + JSON schemas
```

---

## Notes

- A browser-like `USER_AGENT` is required (bare clients get HTTP 403).
- Requests are throttled (`DOWNLOAD_DELAY`, one concurrent request per domain).
- The Events Manager REST API is authenticated-only; course data comes from HTML.
- Re-running spiders merges into existing `data/*.json` by `id`.
- Re-running `extract_structured.py` replaces `data/structured/*.json` entirely.
- Re-running `build_web.py` regenerates all files under `web/`.
