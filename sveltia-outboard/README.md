# Nose to Nose — Sveltia site

Public website for Nose to Nose, built with SvelteKit and [Sveltia CMS](https://sveltiacms.app/en/). All content lives in this repository under `src/lib/data` and `src/lib/content` and is bundled at build time — there is no runtime database or external data source.

## Quick start

```sh
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
src/lib/data/*.json          ──┐
src/lib/content/*.md         ──┤
                               ▼
                    src/lib/data.ts
                    src/lib/markdown.ts
                               │
                               ▼
                    SvelteKit routes
                               │
                               ▼
                         build/
```

- **Stack:** SvelteKit 2, Svelte 5, `@sveltejs/adapter-static`, `marked` for Markdown.
- **Data loading:** JSON and Markdown are bundled at build time via `import.meta.glob` — there is no runtime API or database.
- **Course URLs:** The public slug is the last segment of the listing `id` (e.g. `uk/events/my-course` → `/courses/my-course`). Dated listings in `courses/` may optionally link to a date-agnostic **course type**.

## Data layout

| Location | Contents | CMS collection |
|----------|----------|------------------|
| `src/lib/data/course-types/*.json` | Date-agnostic programmes | **Course types** (folder) |
| `src/lib/data/courses/*.json` | One JSON file per dated listing (event) | **Courses** (folder) |
| `src/lib/data/venues/*.json` | One JSON file per venue | **Venues** (folder) |
| `src/lib/data/people/*.json` | One JSON file per person | **People** (folder) |
| `src/lib/data/testimonials/*.json` | One JSON file per testimonial | **Testimonials** (folder) |
| `src/lib/content/pages/*.md` | Editorial pages (YAML front matter + body) | **Pages** (file) |
| `src/lib/content/articles/*.md` | Article bodies | **Articles** (folder) |

JSON records keep `id` as the first key. The CMS field lists start with ID so saves stay in that order.

Edit content via the CMS or directly in git. Optional `source_url` fields on records are provenance metadata only.

### Courses and events

A **course type** is a date- and venue-agnostic programme (for example “Courage to Be – Clown Level 1”). A **listing** in the Courses collection is one run of a workshop (an event). Listings stay under `/courses` and in the CMS **Courses** tab.

| Course type | Listing (event) |
|-------------|-----------------|
| Level, medium, group size, fee, deposit, facilitators, description, schedule, prerequisites | Dates, region, country, venue, language, accommodation |
| `id`, `title` | `id`, `title`, optional `course` (course type `id`), plus optional copies of the course-type fields |

**Inheritance:** if a listing sets `course`, blank inheritable fields are filled from the course type. A filled listing field overrides the course type (so a London Clown 1 can keep a different fee). If `course` is empty, the listing’s own course-related fields are used.

`resolveListing()` in `src/lib/courses.ts` performs that merge at build time. The public `/courses` index is **course-first**: region → level → course type (or listing title if unlinked), with dated runs listed compactly under each course rather than as separate events. Detail URLs remain `/courses/[slug]` (last segment of the listing `id`).

Listings also reference venues and facilitators by `id`. In the CMS, **Course type**, **Venue**, and **Facilitators** are relation widgets.

## Sveltia CMS

1. Start the dev server.
2. In Chrome, Edge, or Brave, open [http://localhost:5173/admin/index.html](http://localhost:5173/admin/index.html).
3. Choose **Work with Local Repository** and select **this project root** (the folder that contains `package.json`).
4. Edit course types, course listings, venues, people, testimonials, pages, and articles. Commit with git as usual.

Configuration: `static/admin/config.yml`. Collection paths are relative to the project root (e.g. `src/lib/data/courses`).

Before using the GitHub backend in production, set `backend.repo` in `config.yml` to your GitHub repository (e.g. `your-org/sveltia-outboard`).

**Folder collections** (course-types, courses, venues, people, testimonials) — one file per entry; each record appears as its own CMS item.

**File collections** (pages) — single Markdown files with `title` and `body` fields.

When creating a course listing, set the entry **slug** to the last segment of the listing `id` so the public URL matches. When creating a course type, set the slug to the type `id`.

**Course description, schedule, and accommodation** are plain text fields (Markdown is still rendered on the public site). Sveltia’s rich-text editor cannot load some legacy HTML/Markdown in existing records: a `null` value or markup it cannot parse blanks the whole form, so other fields look empty even though the JSON is fine.

Leave **Course type** and **Venue** unset by omitting those keys. JSON `null` or `""` on a single relation blanks the editor. `output.omit_empty_optional_fields` in `config.yml` keeps CMS saves that way. Empty description/schedule/accommodation should be `""`.

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

### Courses index (`/courses`)

The index treats a **course** as the primary unit and each dated listing as an attendance option under it:

- **Course** — what it is (title, plus a short blurb when a course type is linked)
- **Instance** — when and where you can take it
- **Action** — the date row links to that listing’s detail page

Grouping is region → clown level → course type title (or the listing title if unlinked) → start date. Levels such as Clown 1 are category labels; the course name is the main heading. The sidebar lists regions with nested levels. There is no CMS field for grouping — it is derived in `src/lib/courses.ts` (`coursesByRegion`, `coursesByLevel`, `coursesByCourseTitle`).

A course with several dates (for example **Courage to Be – Clown Level 1**) shows the title once, an optional type-level summary, a **Course dates** label, and a compact list of instances. Summaries come from the linked course type (`courseGroupSummary()` / `listingSummary()`), not from venue-specific listing copy. In-person is the default and is not repeated on every row; online runs show an **Online** badge instead of a country. Desktop puts date and location in columns; narrow viewports stack them (date, then location). Unlinked listings still appear as their own group, using the listing title.

### Course detail (`/courses/[slug]`)

| Section | Source | Editable in CMS? |
|---------|--------|------------------|
| Title, dates, region, venue, language | Listing JSON | Yes — **Courses** |
| Level, medium, group size, fee, description, schedule, facilitators | Listing JSON, or inherited from the linked **Course type** when those listing fields are blank | Yes — **Courses** and **Course types** |
| Venue name/address | Linked venue JSON | Yes — **Venues** |
| Facilitators (photo + first paragraph of bio) | Linked people JSON; first paragraph via `firstParagraph()` in `src/lib/people.ts` | Yes — **People** (photo + background) |

Facilitators are taken from the merged listing in `src/routes/courses/[slug]/+page.ts` (`resolveListing()`). How the index groups courses is described under **Courses index** above.

### Team (`/team`)

| Section | Source | Editable in CMS? |
|---------|--------|------------------|
| Page intro | Hardcoded in `src/routes/team/+page.svelte` | No — change in code |
| Name lists | `src/lib/data/people/*.json`, grouped by `person_type` and region | Yes — **People** |
| Courses they facilitate | Merged listings whose facilitator ids include this person (`coursesForPerson()` in `src/lib/people.ts`); link text is the course type title when linked | Indirect — **Courses** / **Course types** |

### Other editorial routes

Approach, training pages, booking, contact, and articles index render a single Markdown file from `src/lib/content/pages/` via `getEditorialPage()` in `src/lib/markdown.ts`.

## Testimonials

Testimonials are stored as JSON and shown on the home page. They do not have their own route yet.

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
| `src/lib/courses.ts` | Listing merge (`resolveListing`), compact date ranges, course-type listing blurbs, region → level → course grouping |
| `static/admin/config.yml` | Sveltia CMS collections and fields |
