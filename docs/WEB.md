# Static course browser

Plain **semantic HTML** pages for browsing structured course and people
data locally or on any static host, plus scraped site content (articles,
thoughts, pages, etc.).

**Generator:** [`scripts/build_web.py`](../scripts/build_web.py)

**Input:**

| Source | Used for |
|--------|----------|
| `data/structured/courses.json`, `venues.json`, `people.json` | Course and people pages |
| `data/approach.md`, `training-programme.md`, `applied-clowning.md`, `booking.md`, `articles.md` | Editorial top-level pages |
| `data/pages_content_analysis.json` | Content analysis page (optional) |
| `data/pages.json`, `articles.json`, `thoughts.json`, `testimonials.json`, `people.json` | All other content pages |

### Two different `people.json` files

| File | Records | Web output |
|------|---------|------------|
| `data/structured/people.json` | Individual people (bios, photos, courses) | `people.html`, `people/{id}.html` |
| `data/people.json` | 5 whole team pages from the scrape | “People & team” section on `other-content.html`, `content/{id}.html` |

Structured people come from `extract_structured.py`. Raw `data/people.json` is
scrape output only — it is not merged into structured people for the all-other-content pages.

**Output:** `web/` directory (committed or gitignored — your choice)

The SvelteKit site in `sveltia/` is a separate front end. It groups listings by region, then clown level, then course type. See [sveltia/README.md](../sveltia/README.md).

---

## Run

After structured extraction (and scraping for other content):

```bash
source .venv/bin/activate
python scripts/build_web.py
python3 -m http.server --directory web 8080
```

Then open:

| URL | Page |
|-----|------|
| [http://localhost:8080/](http://localhost:8080/) | Course list (by region and level) |
| [http://localhost:8080/approach.html](http://localhost:8080/approach.html) | Approach (editorial) |
| [http://localhost:8080/training-programme.html](http://localhost:8080/training-programme.html) | Training programme (editorial) |
| [http://localhost:8080/applied-clowning.html](http://localhost:8080/applied-clowning.html) | Applied clowning (editorial) |
| [http://localhost:8080/booking.html](http://localhost:8080/booking.html) | Booking (editorial) |
| [http://localhost:8080/articles.html](http://localhost:8080/articles.html) | Articles (editorial) |
| [http://localhost:8080/people.html](http://localhost:8080/people.html) | People list |
| [http://localhost:8080/other-content.html](http://localhost:8080/other-content.html) | All other content (index) |
| [http://localhost:8080/content-analysis.html](http://localhost:8080/content-analysis.html) | Content analysis |
| [http://localhost:8080/courses/{slug}.html](http://localhost:8080/courses/) | Course detail |
| [http://localhost:8080/people/{id}.html](http://localhost:8080/people/) | Person detail |
| [http://localhost:8080/content/{id}.html](http://localhost:8080/content/) | Scraped page detail |

Re-run `build_web.py` whenever structured JSON or scrape data changes.

---

## Generated files

```text
web/
  index.html              # Course list (by region and clown level)
  approach.html           # Editorial pages (from data/*.md)
  training-programme.html
  applied-clowning.html
  booking.html
  articles.html
  people.html             # People list (team/associate facilitators, previous associates, in memory)
  other-content.html      # Scraped content index with category sidebar
  content-analysis.html   # Page taxonomy and catalogue
  style.css               # Minimal typography stylesheet
  courses/
    {slug}.html           # One page per course
  people/
    {id}.html             # One page per person
  content/
    {id}.html             # One page per scraped item
    articles/…            # Nested paths mirror scrape ids
    uk/archives/…
```

Course URL slugs are the last path segment of the course `id`
(e.g. `uk/events/foo-bar` → `courses/foo-bar.html`).

Scraped content paths mirror the scrape record `id`
(e.g. `approach` → `content/approach.html`, `articles/bertilarticle` →
`content/articles/bertilarticle.html`).

---

## Page structure

### Site navigation

All pages share top nav: Courses · Approach · Training programme · Applied clowning · Booking · Articles · People · All other content · Content analysis.

### Course list (`index.html`)

- Sticky **sidebar** with links to each region (`UK`, `Europe`, `North America`) and nested links to clown level within each region
- Main content grouped by region, then by level (Clown 1, Clown 2, Clown 3, then Social Clowning, Masterclass, and other levels; uncategorised courses under **Other**)
- Within each level group, courses sorted by start date
- Each course: title link, dates, venue location (from linked venue, or country when no venue), medium

### Course detail (`courses/{slug}.html`)

- Breadcrumb back to course list, people index, and all-other-content page
- `<article>` with:
  - **Details** — definition list (`<dl>`) for scalar fields (including region:
    `UK`, `Europe`, or `North America`, inferred from location)
  - **Schedule**, **Course description**, **Accommodation and meals** — Markdown
    rendered to HTML (`<p>`, `<ul>`, `<strong>`, `<em>`, `<a>`, `<img>`,
    `<blockquote>`)
  - Venue and facilitator IDs resolved to names; facilitators link to people pages
  - Footer link to original `source_url`

### People list (`people.html`)

Sticky sidebar navigation links to four main sections. Team facilitators and
associate facilitators are further grouped by region (`UK`, `Europe`,
`North America`, `Other`) with in-page subsection anchors.

| Section | Structured data |
|---------|-----------------|
| **Team facilitators** | `person_type: "team-facilitator"`, `status: "active"` |
| **Associate facilitators** | `person_type: "associate-facilitator"`, `status: "active"` |
| **Previous associates** | `status: "previous-associate"` |
| **In memory** | `person_type: "team-passed-away"` |

Each name links to a detail page under `people/`.

### Person detail (`people/{id}.html`)

Every person page uses the same layout:

- Breadcrumb back to course list, people index, and all-other-content page
- Person type label at the top — `Team facilitator`, `Associate facilitator`, `Previous associate`, or `In memory`
- `<h1>` — person name
- **Details** — person type, status, country, and region
- **Photo** — `<figure>` with image, or “No photo available.”
- **Background** — Markdown bio rendered to HTML, or “No biography available.”
- **Courses** — linked list of courses (team and associate facilitators only); omitted for other types
- **Footer** — link(s) to original `source_urls` on nosetonose.info when present (facilitators typically omit this field)

Facilitator pages do not show source links or a redundant “Previous associate” type
label when `status` already conveys that role — the header shows “Previous associate”
instead of “Team facilitator” or “Associate facilitator” for those records.

Leading images are stripped from bios when the photo is shown separately.

Missing photo or bio show italic placeholder copy (`.unavailable`) so
every page has the same core sections.

Re-running `build_web.py` removes stale `people/*.html` files that no
longer appear in `people.json`.

### All other content (`other-content.html`)

Index of scraped site content, grouped by type with a sticky **sidebar** for
in-page navigation. The **Pages** section is further grouped by primary category
from `data/pages_content_analysis.json` when that file is present.

| Section | Source | Examples |
|---------|--------|----------|
| Pages | `pages.json` | Our approach, booking, brief history (grouped by analysis category) |
| Articles | `articles.json` | Published articles and interviews |
| Thoughts | `thoughts.json` | Quotes and reflections |
| Testimonials | `testimonials.json` | Course participant feedback |
| People & team | `people.json` | Team pages, associates |

Each item links to a detail page under `content/`.

### Editorial pages (`approach.html`, `training-programme.html`, etc.)

Top-level pages built from Markdown in `data/` (not from scrape JSON):

| File | Output |
|------|--------|
| `data/approach.md` | `web/approach.html` |
| `data/training-programme.md` | `web/training-programme.html` |
| `data/applied-clowning.md` | `web/applied-clowning.html` |
| `data/booking.md` | `web/booking.html` |
| `data/articles.md` | `web/articles.html` |

Configured in `EDITORIAL_PAGES` in `build_web.py`. Edit the Markdown file and re-run the build.

### Content analysis (`content-analysis.html`)

Overview, content patterns, suggested category taxonomy, and a full page catalogue
for scraped `page` records. Reads `data/pages_content_analysis.json` when present;
shows a placeholder message if the file is missing.

Linked from the Pages section on `other-content.html`.

### Scraped content detail (`content/{id}.html`)

- Breadcrumb nav (relative depth adjusts for nested ids)
- Content type label and title (from scrape metadata or first Markdown heading)
- Body rendered from `body_markdown` (headings, paragraphs, lists, links, images)
- Footer link to original `source_url` on nosetonose.info

Copyright footers and decorative image links from the scrape are stripped before
rendering.

Re-running `build_web.py` removes stale files under `content/` that no longer
appear in the scrape JSON.

### Stale paths removed on build

Older generator output is cleaned up automatically:

- `web/contents.html` (former site map)
- `web/facilitators.html` and `web/facilitators/` (renamed to `people`)
- Orphaned `people/*.html` and `content/**/*.html` not in current JSON

---

## Design

- Standard semantic HTML5 (`header`, `nav`, `main`, `article`, `section`, `dl`)
- No JavaScript
- Minimal CSS: serif body, sidebar layouts on index/people/other-content/content-analysis
- Sidebar layout on index, people, all-other-content, and content-analysis pages (responsive collapse on narrow screens)
- Suitable for static hosting (S3, GitHub Pages, Cloudflare Pages, etc.)

---

## Markdown rendering

The build script includes a small Markdown-to-HTML converter for text-block
fields. Supported:

- Headings (`#` … `######`, demoted to `h2`+ on detail pages)
- Paragraphs (double newlines)
- `**bold**`, `*italic*`
- `[links](url)` and `![images](url)`
- Linked images (`[![alt](thumb)](full)` → `<a><img></a>`)
- Bullet lists (`- item`)
- Blockquotes (`> line`, consecutive `>` lines grouped)

It does not implement full CommonMark. Complex nested Markdown in bios may
need manual cleanup at the source or a richer renderer later.

---

## Full rebuild pipeline

```bash
source .venv/bin/activate

# 1. Scrape live site
./scripts/scrape_all.sh

# 2. Extract structured JSON
python scripts/extract_structured.py

# 3. Build static HTML
python scripts/build_web.py

# 4. Preview
python3 -m http.server --directory web 8080
```

---

## See also

- [Structured data](STRUCTURED_DATA.md) — course/venue/people JSON schema
- [Scraping](SCRAPING.md) — raw scrape documentation and content types
