# Scraping documentation

This project extracts rebuild-ready structured content from
[nosetonose.info](https://www.nosetonose.info/) using Scrapy.

**Related docs:**

- [Structured data extraction](STRUCTURED_DATA.md) — courses, venues, people JSON
- [Static web site](WEB.md) — HTML browser (courses, people, all other content)

The live site is a hybrid of:

1. **Legacy Dreamweaver HTML** — static `.htm` pages (international hub, articles, team, etc.)
2. **Regional WordPress sites** — `/uk/`, `/na/`, `/de/`, `/it/`, `/pl/` (and a broken/empty `/ie/`)

---

## How the scrapers work

### Pipeline overview

```text
Spider  →  ContentItem  →  JsonByTypePipeline  →  data/{type}.json
                                           └→  data/bodies/{id}.md
```

All spiders yield the same `ContentItem` shape ([`ntn_scraper/items.py`](../ntn_scraper/items.py)).
The pipeline merges records by `id` into JSON arrays (so re-runs update rather than
duplicate) and writes Markdown bodies with YAML front matter.

Shared HTML cleaning lives in [`ntn_scraper/cleaners.py`](../ntn_scraper/cleaners.py):

- Strip Dreamweaver nav chrome (`.navtd`, `.buttons`, scripts, banner GIFs)
- Keep main content (`.contenttd` on legacy pages; WP `content.rendered` for API)
- Absolutize links/images
- Convert cleaned HTML → Markdown (`markdownify`)

Politeness / access settings ([`ntn_scraper/settings.py`](../ntn_scraper/settings.py)):

- Browser-like `USER_AGENT` (bare clients get HTTP 403)
- `DOWNLOAD_DELAY = 0.75`, one concurrent request per domain
- `ROBOTSTXT_OBEY = False` (robots.txt is empty/unhelpful)

### Spiders

| Spider | Command | Source | Output types |
|--------|---------|--------|--------------|
| **legacy** | `scrapy crawl legacy` | Static `.htm` crawl from hub pages | `page`, `people`, `article`, `thought` (+ optional `course_archive`) |
| **wordpress** | `scrapy crawl wordpress` | WP REST `wp-json/wp/v2/pages` and `posts` | `page`, `testimonial` |
| **courses** | `scrapy crawl courses` | Public WP course listing HTML | `course` |

Run all three:

```bash
./scripts/scrape_all.sh
```

#### `legacy`

- Starts from evergreen hubs (`/`, `articles.htm`, `thoughts.htm`, `new team.htm`, `approach.htm`, …) plus legacy regional mirrors (`nax/`, `itx/`).
- Follows same-host `.htm` / `.html` links.
- **Skips** WordPress paths (`/uk/`, `/na/`, `/de/`, `/it/`, `/pl/`, `/ie/`).
- Classifies URLs by path into `article` / `thought` / `people` / `page`.
- Historical course flyers under `courses/`, `previouscourses/`, `nax/courses/` are **not** scraped unless you set `INCLUDE_COURSE_ARCHIVE=True`.

#### `wordpress`

- For each region, paginates the public REST API.
- Maps WP **pages** → `page`, UK WP **posts** → `testimonial`.
- Skips junk slugs (`test`, `ball1`, `hello-world`) and empty bodies.
- Non-UK posts that do not look like testimonials are stored as `page` instead.
- `/ie/` returns non-JSON and is skipped with a warning.

#### `courses`

- Events Manager’s REST API (`events-manager/v1/events`) returns **401** without auth, so this spider parses listing HTML instead.
- Seeds listing URLs such as `/uk/courses` and `/uk/course-dates`.
- Collects `/events/…` permalinks, then fetches detail pages for full bodies.
- Dates are taken from text immediately after each listing link (not the whole list).

---

## What has been scraped

Counts from the current `data/` export (re-run to refresh):

| File | Type | Records | Notes |
|------|------|---------|-------|
| [`data/pages.json`](../data/pages.json) | `page` | 127 | Legacy about/booking/contact + WP regional pages |
| [`data/articles.json`](../data/articles.json) | `article` | 16 | Index + article bodies under `/articles/` |
| [`data/people.json`](../data/people.json) | `people` | 5 | Team / facilitators / associates pages |
| [`data/thoughts.json`](../data/thoughts.json) | `thought` | 2 | International + NA thoughts pages |
| [`data/testimonials.json`](../data/testimonials.json) | `testimonial` | 10 | UK WP posts (participant quotes) |
| [`data/courses_current.json`](../data/courses_current.json) | `course` | 33 | Current UK Events Manager events |
| `data/bodies/**/*.md` | — | 183 | Markdown mirrors of scraped bodies |

### Coverage by region (pages)

| Region | Approx. pages |
|--------|----------------|
| `international` (legacy root) | 20 |
| `uk` | 27 |
| `de` | 25 |
| `it` | 24 |
| `na` | 21 |
| `pl` | 10 |

Articles/people/thoughts are mostly `international` (English legacy site), with a few NA mirrors.
Current courses in this export are UK-centric (listings that expose `/uk/events/…`).

### Example evergreen content included

- Approach, booking, contact, brief history, course guidelines
- Team / facilitators-in-training / previous associates
- Published articles and “thoughts” reflections
- Regional WP pages (approach, courses landing copy, local about pages, etc.)
- UK testimonials and upcoming course event pages

---

## What has not been scraped

| Not scraped | Why |
|-------------|-----|
| Historical course flyers (`/courses/`, `/previouscourses/`, `/nax/courses/`, …) | Opt-in only via `INCLUDE_COURSE_ARCHIVE=True` (P2 archive) |
| Events Manager booking/ticket/availability API | Requires authentication (HTTP 401) |
| Binary media files (full image/PDF mirror) | Images are listed as URLs in `images[]`; not downloaded |
| External sites | Facebook, blogs, Reachmail newsletter forms, third-party articles |
| WordPress admin / `wp-content` assets as pages | Filtered out |
| `/ie/` WordPress region | No usable public REST JSON |
| Junk WP content | `test`, `ball1`, `hello-world`, empty posts |
| Login-only or private content | Public pages only |
| Structured per-person team records (raw scrape) | Team pages stored as whole `people` or `pages` documents; use `extract_structured.py` for individual people |
| Non-UK current course calendars | Only regions/listings that expose public `/events/` links are captured; DE/IT/PL/NA listing seeds often 404 or lack the same list markup |

Structured course/venue/people JSON and the static HTML browser are **not**
part of the scrape itself — they are produced by downstream scripts. See
[Downstream processing](#downstream-processing).

Raw scrape files `pages.json`, `articles.json`, `thoughts.json`,
`testimonials.json`, and `people.json` also feed the static site’s
**All other content** index and detail pages (see [WEB.md](WEB.md)).

Optional archive run:

```bash
scrapy crawl legacy -s INCLUDE_COURSE_ARCHIVE=True
```

That writes `data/course_archive.json` (many one-off 2013–2015 flyers).

---

## Data schema

Every record is a JSON object. Required fields are always present; optional fields appear when available (mainly WordPress and courses).

### Common record

```json
{
  "id": "approach",
  "type": "page",
  "source_url": "https://www.nosetonose.info/approach.htm",
  "title": "The Nose to Nose approach to teaching clowning",
  "region": "international",
  "language": "en",
  "body_html": "<h1>OUR APPROACH</h1><p>…</p>",
  "body_markdown": "# OUR APPROACH\n\n…",
  "images": [
    { "src": "https://www.nosetonose.info/images/example.jpg", "alt": "" }
  ],
  "scraped_at": "2026-08-27T17:30:50.123456+00:00",
  "meta": {}
}
```

### Field reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Stable slug derived from the URL path (no `.htm`). Unique within a type file; used as merge key. |
| `type` | string | yes | One of: `page`, `people`, `article`, `thought`, `testimonial`, `course`, `course_archive`. |
| `source_url` | string (URL) | yes | Canonical source URL on nosetonose.info. |
| `title` | string | yes | Page/event title (cleaned; site name suffix removed when possible). |
| `region` | string | yes | `international` \| `uk` \| `na` \| `de` \| `it` \| `pl` \| `ie`. |
| `language` | string | yes | BCP 47-ish short code: `en`, `de`, `it`, `pl`. |
| `body_html` | string | yes | Cleaned main HTML (nav/chrome removed). May be a short summary for listing-only course rows before detail merge. |
| `body_markdown` | string | yes | Markdown conversion of `body_html`. |
| `images` | array | yes | List of `{ "src": string, "alt": string }` with absolute URLs. May be empty. |
| `scraped_at` | string | yes | ISO-8601 UTC timestamp of the scrape. |
| `slug` | string | no | WordPress slug when sourced from WP REST. |
| `date` | string | no | WordPress `date` / `modified` (ISO-like local datetime string from WP). |
| `meta` | object | no | Source-specific extras (see below). |

### `meta` by source

**Legacy HTML**

```json
{ "encoding": "latin-1" }
```

**WordPress**

```json
{
  "wp_id": 927,
  "slug": "courses",
  "status": "publish",
  "wp_type": "page"
}
```

**Courses**

```json
{
  "listing_url": "https://www.nosetonose.info/uk/courses",
  "dates": ["12 Sep  - 17 Sep 2026"],
  "detail": true
}
```

- `dates`: human-readable date strings parsed from listings/detail text (not normalized ISO).
- `detail`: `true` when the body came from the event detail page.

### Type → file mapping

| `type` | Output file |
|--------|-------------|
| `page` | `data/pages.json` |
| `people` | `data/people.json` |
| `article` | `data/articles.json` |
| `thought` | `data/thoughts.json` |
| `testimonial` | `data/testimonials.json` |
| `course` | `data/courses_current.json` |
| `course_archive` | `data/course_archive.json` (optional) |

### Markdown bodies

For each record with a non-empty `body_markdown`, a file is written under `data/bodies/`:

```text
data/bodies/{id}.md
```

Nested ids become nested paths, e.g. `articles/jbarticle` → `data/bodies/articles/jbarticle.md`.

Front matter:

```markdown
---
id: approach
type: page
title: "The Nose to Nose approach to teaching clowning"
source_url: https://www.nosetonose.info/approach.htm
---

# OUR APPROACH

…
```

### JSON Schema (draft)

Useful for validation when importing into a CMS:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://nosetonose.local/schemas/content-item.json",
  "title": "NoseToNoseContentItem",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "id",
    "type",
    "source_url",
    "title",
    "region",
    "language",
    "body_html",
    "body_markdown",
    "images",
    "scraped_at"
  ],
  "properties": {
    "id": { "type": "string", "minLength": 1 },
    "type": {
      "type": "string",
      "enum": [
        "page",
        "people",
        "article",
        "thought",
        "testimonial",
        "course",
        "course_archive"
      ]
    },
    "source_url": { "type": "string", "format": "uri" },
    "title": { "type": "string" },
    "region": {
      "type": "string",
      "enum": ["international", "uk", "na", "de", "it", "pl", "ie"]
    },
    "language": { "type": "string", "minLength": 2, "maxLength": 5 },
    "body_html": { "type": "string" },
    "body_markdown": { "type": "string" },
    "images": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["src", "alt"],
        "properties": {
          "src": { "type": "string", "format": "uri" },
          "alt": { "type": "string" }
        }
      }
    },
    "scraped_at": { "type": "string", "format": "date-time" },
    "slug": { "type": "string" },
    "date": { "type": "string" },
    "meta": { "type": "object" }
  }
}
```

A machine-readable copy is also saved at [`docs/content-item.schema.json`](content-item.schema.json).

---

## Project layout

```text
ntn_scraper/
  cleaners.py          # HTML → cleaned HTML/Markdown helpers
  items.py             # ContentItem definition
  pipelines.py         # JSON + Markdown writers
  settings.py
  spiders/
    legacy.py
    wordpress.py
    courses.py
data/                  # Scrape output
  structured/          # Extracted courses, venues, people (see STRUCTURED_DATA.md)
  bodies/              # Markdown mirrors of scraped bodies
web/                   # Generated static HTML site (see WEB.md)
scripts/
  scrape_all.sh        # Run all three spiders
  extract_structured.py
  build_web.py
docs/
  SCRAPING.md          # This file
  STRUCTURED_DATA.md
  WEB.md
  content-item.schema.json
  structured-data.schema.json
```

---

## Downstream processing

After scraping, two optional scripts transform the data:

### Structured extraction

```bash
python scripts/extract_structured.py
```

Reads `courses_current.json` (detail pages only), `people.json`, and selected
regional team pages from `pages.json`. Writes HTML-free JSON to `data/structured/`.
See [STRUCTURED_DATA.md](STRUCTURED_DATA.md).

### Static web site

```bash
python scripts/build_web.py
```

Reads `data/structured/*.json` (courses, venues, people) and scraped content
from `data/pages.json`, `articles.json`, `thoughts.json`, `testimonials.json`,
and `people.json`.

Writes semantic HTML to `web/`:

- **Courses** — `index.html` + `courses/{slug}.html` from structured JSON
- **People** — `people.html` + `people/{id}.html` from `data/structured/people.json`
- **All other content** — `other-content.html` + ~160 pages under `content/` from raw scrape JSON

See [WEB.md](WEB.md).

Full pipeline:

```bash
./scripts/scrape_all.sh
python scripts/extract_structured.py
python scripts/build_web.py
```

---

## Caveats for the rebuild

- Bodies still contain some leftover WP shortcodes, embeds, or odd heading nesting from the source HTML.
- Course `dates` in raw scrape records are display strings, not timezone-aware ISO datetimes (structured extraction normalises to ISO dates where possible).
- Raw `people` records are whole pages; structured extraction splits individual people from team pages, regional `pages.json` team records, and course pages into `data/structured/people.json`. Each person has `person_type` (`team-facilitator`, `associate-facilitator`, or `team-passed-away`), `status` (`active` or `previous-associate`). Training-only roster entries without current courses are excluded.
- Re-scraping merges raw JSON by `id`; structured extraction overwrites `data/structured/` completely.
- Re-scraping: delete `data/*.json` (and optionally `data/bodies/`) for a clean raw rebuild.
