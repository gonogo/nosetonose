# Nose to Nose — Sveltia site

Public website for Nose to Nose, built with SvelteKit and [Sveltia CMS](https://sveltiacms.app/en/). It lives in this directory and **runs from its own copy of the data** under `src/lib/data` and `src/lib/content`. It does not read `../data` at runtime.

This is a separate front end from the Python static site in `../web/`. Both can coexist: the scrape → extract → build pipeline feeds the legacy HTML site; this project can optionally refresh its data from the same pipeline output.

## Run

```sh
cd sveltia
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

| Path | Page |
|------|------|
| `/` | Home |
| `/courses` | Course list |
| `/courses/[slug]` | Course detail |
| `/approach` | Approach |
| `/training` | Training overview |
| `/training/clown-programme` | Clown programme |
| `/training/for-organisations` | For organisations |
| `/how-to-book` | How to book |
| `/team` | Team list |
| `/team/[id]` | Person detail |
| `/articles` | Articles index |
| `/articles/[slug]` | Article |
| `/contact` | Contact us |
| `/admin/index.html` | Sveltia CMS |

## Architecture

```text
Parent pipeline (optional)          This site (always)
../data/structured/*.json    ──►   src/lib/data/{courses,venues,people}/*.json
../data/testimonials.json    ──►   src/lib/data/testimonials/*.json
../data/*.md + bodies/       ──►   src/lib/content/pages/*.md, articles/*.md
                                          │
                                          ▼
                                   src/lib/data.ts  (import.meta.glob at build time)
                                   src/lib/markdown.ts
                                          │
                                          ▼
                                   SvelteKit routes → static build/
```

- **Stack:** SvelteKit 2, Svelte 5, `@sveltejs/adapter-static`, `marked` for Markdown.
- **Data loading:** JSON and Markdown are bundled at build time via `import.meta.glob` — there is no runtime API or database.
- **Course URLs:** The public slug is the last segment of the course `id` (e.g. `uk/events/my-course` → `/courses/my-course`).

## Data

| Location | Contents | CMS collection |
|----------|----------|------------------|
| `src/lib/data/courses/*.json` | One JSON file per course | **Courses** (folder) |
| `src/lib/data/venues/*.json` | One JSON file per venue | **Venues** (folder) |
| `src/lib/data/people/*.json` | One JSON file per person | **People** (folder) |
| `src/lib/data/testimonials/*.json` | One JSON file per testimonial | **Testimonials** (folder) |
| `src/lib/content/pages/*.md` | Editorial pages (YAML front matter + body) | **Pages** (file) |
| `src/lib/content/articles/*.md` | Article bodies | **Articles** (folder) |

Courses reference venues and facilitators by `id`. In the CMS, **Venue** and **Facilitators** fields are relation widgets that search those collections.

### Sync from the parent pipeline

To refresh from the scrape/extract pipeline (optional; the site already has its own copy):

```sh
npm run sync-data
```

`scripts/sync-data.py` reads from the parent repo when present:

| Source | Destination | Notes |
|--------|-------------|-------|
| `../data/structured/courses.json` | `src/lib/data/courses/*.json` | Filename = last segment of course `id` |
| `../data/structured/venues.json` | `src/lib/data/venues/*.json` | Filename = venue `id` |
| `../data/structured/people.json` | `src/lib/data/people/*.json` | Filename = person `id` |
| `../data/testimonials.json` | `src/lib/data/testimonials/*.json` | Normalized to `id`, `title`, `source_url`, `date`, `quote` |
| `../data/approach.md`, etc. | `src/lib/content/pages/*.md` | Internal links rewritten for this site |
| `../data/bodies/articles/*.md` | `src/lib/content/articles/*.md` | Links cleaned and rewritten |

**Warning:** Re-running sync **overwrites** synced files. CMS or manual edits to those paths will be lost unless you merge them back first.

**Not synced:** `home-team.md` (home-page “About us” copy) is maintained only in this project — edit it in the CMS or directly in `src/lib/content/pages/home-team.md`.

Link rewrites applied during sync (and in testimonial quotes) are defined in `LINK_REWRITES` in `scripts/sync-data.py`, e.g. `people.html` → `/team`, `approach.html` → `/approach`.

## Sveltia CMS

1. Start the dev server.
2. In Chrome, Edge, or Brave, open [http://localhost:5173/admin/index.html](http://localhost:5173/admin/index.html).
3. Choose **Work with Local Repository** and select the **nosetonose git root** (the folder that contains `.git` and `sveltia/`), not this directory alone.
4. Edit courses, venues, people, testimonials, pages, and articles. Commit with git as usual.

Configuration: `static/admin/config.yml`. Collection paths are relative to the git root (e.g. `sveltia/src/lib/data/courses`).

**Folder collections** (courses, venues, people, testimonials) — one file per entry; each record appears as its own CMS item.

**File collections** (pages) — single Markdown files with `title` and `body` fields.

When creating a course, set the entry **slug** to the last segment of the course `id` so the public URL matches.

## What is editable where

Not every part of every page is a CMS field. Some sections are assembled in code from multiple sources.

### Home (`/`)

| Section | Source | Editable in CMS? |
|---------|--------|------------------|
| Hero (title, intro, links) | `src/routes/+page.svelte` | No — change in code |
| About us | `src/lib/content/pages/home-team.md` | Yes — **Pages → Home — about us** |
| Our approach | Excerpt of `approach.md` up to heading `What happens in a workshop` | Partially — edit **Pages → Approach**; excerpt logic in `src/lib/home.ts` (`editorialExcerpt`) |
| Newsletter signup | Form in `+page.svelte`; URL in `src/lib/home.ts` (`NEWSLETTER_URL`) | Intro text in code; signup URL in code |
| Testimonials | All `src/lib/data/testimonials/*.json`, sorted by date then title | Yes — **Testimonials** collection |

Load logic: `src/routes/+page.ts`.

### Course detail (`/courses/[slug]`)

| Section | Source | Editable in CMS? |
|---------|--------|------------------|
| Title, dates, fees, descriptions | Course JSON | Yes — **Courses** |
| Venue name/address | Linked venue JSON | Yes — **Venues** |
| Facilitators (photo + first paragraph of bio) | Linked people JSON; first paragraph via `firstParagraph()` in `src/lib/people.ts` | Yes — **People** (photo + background) |

Facilitators are resolved from `course.facilitators` ids in `src/routes/courses/[slug]/+page.ts`.

### Team (`/team`)

| Section | Source | Editable in CMS? |
|---------|--------|------------------|
| Page intro | Hardcoded in `src/routes/team/+page.svelte` | No — change in code |
| Name lists | `src/lib/data/people/*.json`, grouped by `person_type` and region | Yes — **People** |

### Other editorial routes

Approach, training pages, booking, contact, and articles index render a single Markdown file from `src/lib/content/pages/` via `getEditorialPage()` in `src/lib/markdown.ts`.

## Testimonials

Testimonials are stored as structured data and shown on the home page. They do not have their own route yet.

After syncing from `../data/testimonials.json`, review entries in the CMS: the WordPress scrape sometimes included old course listings or promotional pages, not participant quotes. Delete miscategorized entries or clear their **Quote** field.

Fields per testimonial: `id`, `title` (attribution line), `source_url`, `date`, `quote` (Markdown).

## Build

```sh
npm run build
npm run preview
```

Static output is written to `build/`.

## Key source files

| Path | Role |
|------|------|
| `src/lib/data.ts` | Loads and normalizes all JSON via `import.meta.glob` |
| `src/lib/markdown.ts` | Front matter parsing, Markdown render, editorial/article loaders |
| `src/lib/home.ts` | Home-page helpers: newsletter URL, approach excerpt, testimonial sort |
| `src/lib/people.ts` | Team grouping, `firstParagraph()` for course facilitator intros |
| `src/lib/courses.ts` | Course slug helpers, date formatting, list grouping |
| `scripts/sync-data.py` | Copy and transform parent pipeline data into this project |
| `static/admin/config.yml` | Sveltia CMS collections and fields |
