# Static course browser

Plain **semantic HTML** pages for browsing structured course and people
data locally or on any static host, plus scraped site content (articles,
thoughts, pages, etc.).

**Generator:** [`scripts/build_web.py`](../scripts/build_web.py)

**Input:**

| Source | Used for |
|--------|----------|
| `data/structured/courses.json`, `venues.json`, `people.json` | Course and people pages |
| `data/pages.json`, `articles.json`, `thoughts.json`, `testimonials.json`, `people.json` | All other content pages |

### Two different `people.json` files

| File | Records | Web output |
|------|---------|------------|
| `data/structured/people.json` | ~36 individual people (bios, photos, courses) | `people.html`, `people/{id}.html` |
| `data/people.json` | 5 whole team pages from the scrape | “People & team” section on `other-content.html`, `content/{id}.html` |

Structured people come from `extract_structured.py`. Raw `data/people.json` is
scrape output only — it is not merged into structured people for the all-other-content pages.

**Output:** `web/` directory (committed or gitignored — your choice)

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
| [http://localhost:8080/](http://localhost:8080/) | Course list |
| [http://localhost:8080/people.html](http://localhost:8080/people.html) | People list (four sections by role) |
| [http://localhost:8080/other-content.html](http://localhost:8080/other-content.html) | All other content (index) |
| [http://localhost:8080/courses/{slug}.html](http://localhost:8080/courses/) | Course detail |
| [http://localhost:8080/people/{id}.html](http://localhost:8080/people/) | Person detail |
| [http://localhost:8080/content/{id}.html](http://localhost:8080/content/) | Scraped page detail |

Re-run `build_web.py` whenever structured JSON or scrape data changes.

---

## Generated files

```text
web/
  index.html              # Course list (sorted by start date)
  people.html             # People list (facilitators, team, previous associates, in memory)
  other-content.html      # Scraped content index with section sidebar
  style.css               # Minimal typography stylesheet
  courses/
    {slug}.html           # One page per course (~33 pages)
  people/
    {id}.html             # One page per person (~36 pages)
  content/
    {id}.html             # One page per scraped item (~160 pages)
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

### Course list (`index.html`)

- Site nav: Courses · People · All other content
- Unordered list of courses with title link, dates, country, clown level, medium

### Course detail (`courses/{slug}.html`)

- Breadcrumb back to course list, people index, and all-other-content page
- `<article>` with:
  - **Details** — definition list (`<dl>`) for scalar fields
  - **Schedule**, **Course description**, **Accommodation and meals** — Markdown
    rendered to HTML (`<p>`, `<ul>`, `<strong>`, `<em>`, `<a>`, `<img>`,
    `<blockquote>`)
  - Venue and facilitator IDs resolved to names; facilitators link to people pages
  - Footer link to original `source_url`

### People list (`people.html`)

Four sections, each a two-column name list with country and region:

| Section | Structured data |
|---------|-----------------|
| **Facilitators** | `person_type: "facilitator"`, `status: "active"` |
| **Team** | `person_type: "team"` |
| **Previous associates** | `person_type: "facilitator"`, `status: "previous-associate"` |
| **In memory** | `person_type: "team-passed-away"` |

Each name links to a detail page under `people/`.

### Person detail (`people/{id}.html`)

Every person page uses the same layout:

- Breadcrumb back to course list, people index, and all-other-content page
- Person type label at the top — `Facilitator`, `Team`, `Previous associate`, or `In memory`
- `<h1>` — person name
- **Details** — person type, status, country, and region
- **Photo** — `<figure>` with image, or “No photo available.”
- **Background** — Markdown bio rendered to HTML, or “No biography available.”
- **Courses** — linked list of courses (`facilitator` only); omitted for other types
- **Footer** — link(s) to original `source_urls` on nosetonose.info (**non-facilitators only**)

Facilitator pages do not show source links or a redundant “Previous associate” type
label when `status` already conveys that role — the header shows “Previous associate”
instead of “Facilitator” for those records.

Leading images are stripped from bios when the photo is shown separately.

Missing photo or bio show italic placeholder copy (`.unavailable`) so
every page has the same core sections.

Re-running `build_web.py` removes stale `people/*.html` files that no
longer appear in `people.json`.

### All other content (`other-content.html`)

Index of scraped site content, grouped by type with a sticky **sidebar** for
in-page navigation:

| Section | Source | Examples |
|---------|--------|----------|
| Pages | `pages.json` | Our approach, booking, brief history |
| Articles | `articles.json` | Published articles and interviews |
| Thoughts | `thoughts.json` | Quotes and reflections |
| Testimonials | `testimonials.json` | Course participant feedback |
| People & team | `people.json` | Team pages, associates |

Each item links to a detail page under `content/`.

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
- Minimal CSS: serif body, narrow column, simple list styling, muted placeholders
- Sidebar layout on the all-other-content index (responsive collapse on narrow screens)
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
