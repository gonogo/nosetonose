# Structured course data

This step turns scraped course pages into clean, HTML-free JSON for courses,
venues, and people. Text-block fields use **Markdown** (not HTML).

**Script:** [`scripts/extract_structured.py`](../scripts/extract_structured.py)

**Input:**

| File | Used for |
|------|----------|
| `data/courses_current.json` | Course detail pages (`meta.detail = true`) |
| `data/people.json` | Main team / associates / training pages |
| `data/pages.json` | Regional team pages, in-memory, previous associates |

**Output:**

| File | Description |
|------|-------------|
| `data/structured/courses.json` | One record per current UK course event |
| `data/structured/venues.json` | Deduplicated venues referenced by courses |
| `data/structured/people.json` | Deduplicated people (team facilitators, associate facilitators, previous associates, in memory) |

Machine-readable schemas: [`docs/structured-data.schema.json`](structured-data.schema.json).

The SvelteKit site in `sveltia/` can further group these dated listings under CMS-owned **course types**. That split is not part of this extract — see [sveltia/README.md](../sveltia/README.md).

---

## Run

From the repo root (after scraping):

```bash
source .venv/bin/activate
python scripts/extract_structured.py
```

Re-run whenever `courses_current.json`, `people.json`, or relevant `pages.json` records change.

---

## Pipeline

```text
courses_current.json ──┐
                       ├── extract_structured.py ──► courses.json
people.json ───────────┤                         ├── venues.json
pages.json (team) ─────┤                         └── people.json
                       │
                       └── Parses Markdown + HTML from course and team pages
                           (descriptions from body_markdown; sections from HTML)
                           Joins venue/facilitator IDs
                           Normalises dates, fees, clown level, medium
```

Only course records with `meta.detail: true` are included (full event pages,
not listing stubs).

---

## Course schema

Each object in `courses.json`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Same as scrape id, e.g. `uk/events/clown-1-week-…` |
| `title` | string | Event title |
| `source_url` | string | Original URL on nosetonose.info |
| `start_date` | string \| null | ISO date `YYYY-MM-DD` |
| `end_date` | string \| null | ISO date `YYYY-MM-DD` |
| `location_country` | string \| null | Country name, e.g. `United Kingdom` |
| `region` | string \| null | `UK`, `Europe`, or `North America` (inferred from `location_country`) |
| `venue` | string \| null | **Foreign key** → `venues.json` `id` |
| `language` | string \| null | e.g. `English`, `French` |
| `facilitators` | string[] | **Foreign keys** → `people.json` `id` (where `person_type` is `team-facilitator` or `associate-facilitator`) |
| `clown_level` | string \| null | Parsed from title: `Clown 1`, `Masterclass`, `Introduction`, etc. |
| `prerequisites` | string \| null | Plain text |
| `medium` | string | `In-person` or `Online` |
| `maximum_group_size` | number \| null | Integer when stated in body |
| `course_fee` | string \| null | Display string, e.g. `£590 – Tuition only` |
| `course_fee_deposit` | string \| null | Display string, e.g. `£220` |
| `schedule` | string \| null | **Markdown** — dates/times per day |
| `course_description` | string \| null | **Markdown** — from `body_markdown`; links and formatting preserved |
| `accommodation_and_meals` | string \| null | **Markdown** |

### Example

```json
{
  "id": "uk/events/clown-1-week-the-courage-to-be-near-leuven-belgium",
  "title": "CLOWN 1 WEEK – THE COURAGE TO BE – NEAR LEUVEN, BELGIUM",
  "source_url": "https://www.nosetonose.info/uk/events/clown-1-week-the-courage-to-be-near-leuven-belgium",
  "start_date": "2026-10-13",
  "end_date": "2026-10-18",
  "location_country": "Belgium",
  "region": "Europe",
  "venue": "huis-van-haroen",
  "language": "English",
  "facilitators": ["vivian-gladwell", "an-valenteyn"],
  "clown_level": "Clown 1",
  "prerequisites": null,
  "medium": "In-person",
  "maximum_group_size": 12,
  "course_fee": "570 EUR –",
  "course_fee_deposit": "250 EUR",
  "schedule": "13 – 18 octobre 2026\n\n- Tuesday 03 OCT – 19h-21h\n…",
  "course_description": "[![](https://www.nosetonose.info/uk/wp-content/uploads/2015/01/looking.jpg)](https://www.nosetonose.info/uk/wp-content/uploads/2015/01/looking.jpg)\n\n*with Vivian Gladwell and Ali Stockford*\n\nThe word \"courage\" comes from a root meaning \"heart.\"…\n\n***\"Nose to Nose is a transformative experience!…\" Astrid Olofsson- Actress***",
  "accommodation_and_meals": null
}
```

---

## Venue schema

Each object in `venues.json`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | URL slug derived from venue name |
| `name` | string | Venue name |
| `address` | string \| null | Street / city when available |
| `location` | string \| null | Town or city extracted from address or name, e.g. `East Grinstead` |
| `email` | string \| null | Contact email (often from accommodation block) |
| `phone` | string \| null | Phone number when available |

Venues are deduplicated across courses. Peredur Centre variants are normalised
to a single `peredur-centre` record.

`location` is extracted from the venue address or name (comma-separated parts,
postcodes and counties stripped). When that fails, the course title is used as
a fallback (e.g. `CENTRAL LONDON` → `London`, `… LEICESTER, UK` → `Leicester`).

---

## People schema

Each object in `people.json`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | URL slug derived from name |
| `name` | string | Display name |
| `person_type` | string | `team-facilitator`, `associate-facilitator`, or `team-passed-away` |
| `status` | string | `active` (default) or `previous-associate` |
| `country` | string \| null | Country where the person is based |
| `region` | string \| null | `UK`, `Europe`, or `North America` (inferred from `country`) |
| `source_urls` | string[] | Original site page URLs (rare; most people are facilitators and omit this field) |
| `background` | string \| null | **Markdown** bio |
| `photo` | string \| null | Absolute image URL |

### Person types

| `person_type` | Meaning | Typical sources |
|---------------|---------|-----------------|
| `team-facilitator` | Facilitator on core or regional team pages | `team`, `new-team`, `nax/team-na`, `uk/our-team`, `de/dozentinnen`, etc. |
| `associate-facilitator` | Facilitator who leads courses but is not on team pages | Course pages |
| `team-passed-away` | Deceased; remembered on the site | “In memory of … who died” sections, `uk/in-memory` |

Previous associates keep their facilitator subtype (`team-facilitator` or `associate-facilitator`) but are grouped on the site by **`status: "previous-associate"`**.
They come from `previousassociates` and `uk/previous-associates`. Someone listed there
who also facilitates a current UK course keeps `status: "active"`.

People who appear only on facilitators-in-training pages, are not on any team page,
and do not facilitate current courses are **excluded** from the export.

### Extraction sources

**Team facilitators** (`person_type: "team-facilitator"`) are merged from:

1. **Main team pages** in `people.json` (`team`, `new-team`, `nax/team-na`) — parsed from both HTML headings and Markdown
   sections (bios often sit in sibling blocks, not directly under the heading)
2. **Regional team pages** in `pages.json` (`uk/our-team`, `de/dozentinnen`, `it/il-nostro-gruppo`, `pl/team`, `na/our-team-in-north-america`)

**Associate facilitators** (`person_type: "associate-facilitator"`) are extracted from
course pages (facilitator sections, “with X and Y” intro lines, headings,
and inline “Name … bio text” paragraphs) when the person is not on a team page.

**Previous associates** (`status: "previous-associate"`) are identified from the
previous-associates pages above.

**In memory** (`person_type: "team-passed-away"`) is assigned from “in memory of … who died”
headings across team pages and the dedicated `uk/in-memory` page.

### Example (team facilitator)

```json
{
  "id": "hanna-mosch",
  "name": "Hanna Mosch",
  "person_type": "team-facilitator",
  "status": "active",
  "country": "Germany",
  "region": "Europe",
  "background": "Hanna has worked as a school teacher…",
  "photo": null
}
```

Facilitators omit `source_urls`. Previous associates use `"status": "previous-associate"`
and retain their facilitator subtype.

Name aliases are normalised (e.g. `Ali Stockford` → `Alison Stockford`).

When the same person appears in multiple sources, **photo** and **background**
are merged: empty fields are filled in, and the better bio is kept (prefers text
that mentions the person’s name over a longer but mismatched excerpt). Leading
images are stripped from `background` when a separate `photo` URL is stored.

`country` is inferred from, in order: parenthetical country in the display name,
residence or origin phrases in the bio, city/country mentions, team-page section
headings (e.g. `GERMANY - Munich`), courses the person facilitates, and finally
the regional context of team pages (`uk`, `na`, etc.).

`region` is derived from `country`: United Kingdom → `UK`; United States and
Canada → `North America`; all other countries → `Europe`.

`source_urls` lists original nosetonose.info pages when present. Facilitators
typically omit this field. Values are deduplicated and sorted when included.

---

## Extraction logic (summary)

### Dates

- Parsed from `meta.dates` on the scrape record and from schedule headings
- Normalised to ISO `YYYY-MM-DD` where possible

### Clown level

Inferred from the course title using patterns such as `CLOWN 1`, `CLOWN 2`,
`MASTERCLASS`, `INTRODUCTION TO CLOWNING`, `SOCIAL CLOWNING`, etc.

### Medium

`Online` only when the title or early body text explicitly says “online course”.
Deposit/booking text mentioning “online” does not trigger this.

### Region

Derived from `location_country` using the same rules as people: United Kingdom → `UK`;
United States and Canada → `North America`; all other countries → `Europe`.

### Venues

Extracted from, in order of preference:

1. `Venue:` heading followed by `<address>` or link
2. `Where:` / `Venue:` lines in Markdown
3. Title patterns (`at Dornach`, `– Peredur Centre, …`, city names)

Invalid venue names (course titles, postcodes alone, etc.) are filtered out.
Online courses have `venue: null`.

### Facilitators

Multiple sources are merged and deduplicated by canonical name/id:

| Source | Example |
|--------|---------|
| Team page heading + following content | `# Laura Geilen` → bio in next HTML block |
| Team page Markdown | `# Angie Foster` section in `body_markdown` |
| Facilitator section in HTML | `Facilitators: Vivian Gladwell & Andreas L. Maier` |
| Headings | `h2`/`h3` or `<strong>` name lines |
| Intro line | `with Vivian Gladwell and Ali Stockford` |
| Inline bio paragraph | `Andreas L. Maier Andreas has a degree in acting…` |
| French intro | `avec Vivian Gladwell` |

Most courses have **two** facilitators when the source page lists two. Solo
facilitator courses (Masterclass, some one-day intros) correctly retain one.

Duplicate entries from different extraction paths (e.g. intro line + section
bio) are merged into a single record rather than keeping the first match only.

### Text blocks

Schedule, description, and accommodation are extracted as Markdown. No HTML tags
in output.

#### Course description

`course_description` is taken from the scraped `body_markdown` field (not
re-converted from HTML), so links and inline formatting from the source page
are preserved.

Extraction:

1. Strip YAML front matter from `body_markdown` (if present).
2. Take content from the start of the body up to the first stop marker:
   - horizontal rule (`---`)
   - booking headings (`## **Step 1…**`, `## **Book on this course**`,
     `## [Click here to book…]`)
   - facilitator headings (`**Facilitators:**`, `### Facilitator`, etc.)
   - fee headings (`**Course fee:**`, `**Fee (Tuition only):**`, `**Bursaries:**`)
3. If Markdown extraction yields nothing useful, fall back to HTML via
   `node_to_markdown()` (images become `![alt](src)`; links become `[text](url)`).

Preserved in descriptions:

- **Bold** and *italic* text
- Blockquotes (`>`)
- Bullet lists (`- item`)
- Text links (`[label](url)`) and `mailto:` links
- Linked images (`[![](thumb)](full)`)

Excluded from descriptions (handled elsewhere or omitted intentionally):

- Facilitator bios (stored under `people.json`; linked from course pages)
- Booking CTAs and fee/deposit blocks (parsed into `course_fee` / `course_fee_deposit`
  where possible; booking links may appear in `schedule` on some pages)
- Accommodation blocks (`accommodation_and_meals`)

Schedule and accommodation still use HTML section parsing with Markdown output;
list items in descriptions are preserved as `-` bullet lists.

### Prerequisites, fees, group size

Regex and section parsing on the course Markdown body. Coverage depends on
how consistently the source page labels these fields.

---

## Current export stats

Typical counts after a full scrape + extract (re-run to refresh):

| File | Records |
|------|---------|
| `courses.json` | 33 |
| `venues.json` | ~10 |
| `people.json` | ~32 |

Typical `people.json` breakdown: ~17 team facilitators, ~13 associate facilitators,
~7 previous associates (by `status`), ~2 in memory (counts vary with scrape).
Training-only roster entries without current courses are excluded.

Field coverage varies by course (not every page has schedule, accommodation,
or prerequisites blocks). French-language pages on the UK events calendar
(e.g. Morges) use headings such as Tarif, Acompte, Lieu, and Date et heures;
those are parsed the same way as the English equivalents.

---

## Caveats

- **UK courses only** in this export (matches `courses_current.json` coverage).
- **Display strings** for fees are not normalised to a single currency/format.
- **Venue/facilitator extraction** is heuristic; spot-check unusual pages.
- **Re-extracting** overwrites `data/structured/*.json` completely (no merge).
- Facilitator bios on course pages may be shorter than team-page bios; when
  merging duplicates the extractor prefers the bio that best matches the person
  (typically team-page text), not simply the longest string.
- Some facilitators have no photo or no current UK courses in the export; the
  web site still renders a page with placeholder text for missing sections.

---

## Web site output

`build_web.py` reads this directory for course and people pages:

| Structured file | Generated pages |
|-----------------|-----------------|
| `courses.json` | `web/index.html`, `web/courses/{slug}.html` |
| `venues.json` | Joined into course detail pages (not standalone pages) |
| `people.json` | `web/people.html`, `web/people/{id}.html` |

Scraped articles, site pages, thoughts, testimonials, and whole team pages
(from raw `data/*.json`, not this directory) are published separately under
**All other content** — see [WEB.md](WEB.md).

---

## See also

- [Scraping](SCRAPING.md) — raw scrape pipeline and `ContentItem` schema
- [Static web site](WEB.md) — HTML browser generated from this data
