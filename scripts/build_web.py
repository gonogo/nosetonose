"""Generate plain static HTML pages from structured course data."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "structured"
RAW_DATA_DIR = ROOT / "data"
WEB_DIR = ROOT / "web"
COURSES_DIR = WEB_DIR / "courses"
PEOPLE_DIR = WEB_DIR / "people"
CONTENT_DIR = WEB_DIR / "content"

SCRAPED_CONTENT_FILES = (
    "pages.json",
    "articles.json",
    "thoughts.json",
    "testimonials.json",
    "people.json",
)

CONTENT_TYPE_LABELS = {
    "page": "Pages",
    "article": "Articles",
    "thought": "Thoughts",
    "testimonial": "Testimonials",
    "people": "People & team",
}

CONTENT_TYPE_ORDER = ("page", "article", "thought", "testimonial", "people")

GENERIC_TITLES = {
    "Clown workshops with Nose to Nose",
}


def load_json(name: str) -> list[dict]:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def course_slug(course_id: str) -> str:
    return course_id.split("/")[-1]


def format_date(value: str | None) -> str:
    if not value:
        return ""
    year, month, day = value.split("-")
    months = (
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    )
    return f"{int(day)} {months[int(month) - 1]} {year}"


def format_date_range(start: str | None, end: str | None) -> str:
    if start and end and start != end:
        return f"{format_date(start)} – {format_date(end)}"
    if start:
        return format_date(start)
    return ""


def markdown_to_html(text: str) -> str:
    """Minimal Markdown to HTML for course text blocks."""
    if not text:
        return ""

    text = re.sub(r"\n\n(?=[-*]\s)", "\n", text.strip())
    blocks = re.split(r"\n\n+", text)
    parts: list[str] = []

    for block in blocks:
        lines = [line for line in block.split("\n") if line.strip()]
        if len(lines) == 1:
            heading = re.match(r"^(#{1,6})\s+(.+)$", lines[0].strip())
            if heading and heading.group(2).strip():
                level = min(len(heading.group(1)), 6)
                if level == 1:
                    level = 2
                parts.append(
                    f"<h{level}>{inline_markdown(heading.group(2).strip())}</h{level}>"
                )
                continue

        if lines and all(line.lstrip().startswith(">") for line in lines):
            quote_lines = [re.sub(r"^>\s?", "", line.lstrip()) for line in lines]
            quote_html = "<br>\n".join(inline_markdown(line) for line in quote_lines)
            parts.append(f"<blockquote><p>{quote_html}</p></blockquote>")
            continue

        list_lines = [line for line in lines if re.match(r"^[-*]\s+", line)]
        prose_lines = [line for line in lines if not re.match(r"^[-*]\s+", line)]

        if list_lines:
            for line in prose_lines:
                parts.append(f"<p>{inline_markdown(line)}</p>")
            items = []
            for line in list_lines:
                item = re.sub(r"^[-*]\s+", "", line.strip())
                items.append(f"<li>{inline_markdown(item)}</li>")
            parts.append("<ul>" + "".join(items) + "</ul>")
            continue

        paragraph = "<br>\n".join(inline_markdown(line) for line in lines)
        if paragraph:
            parts.append(f"<p>{paragraph}</p>")

    return "\n".join(parts)


def inline_markdown(text: str) -> str:
    text = html.escape(text)
    text = re.sub(
        r"\[!\[([^\]]*)\]\(([^)]+)\)\]\(([^)]+)\)",
        lambda m: (
            f'<a href="{html.escape(m.group(3), quote=True)}">'
            f'<img src="{html.escape(m.group(2), quote=True)}" alt="{m.group(1)}">'
            f"</a>"
        ),
        text,
    )
    text = re.sub(
        r"!\[([^\]]*)\]\(([^)]+)\)",
        lambda m: f'<img src="{html.escape(m.group(2), quote=True)}" alt="{m.group(1)}">',
        text,
    )
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>',
        text,
    )
    return text


def page_shell(title: str, body: str, css_href: str = "style.css", body_class: str = "") -> str:
    class_attr = f' class="{body_class}"' if body_class else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="{css_href}">
</head>
<body{class_attr}>
{body}
</body>
</html>
"""


def format_person_type(person_type: str | None) -> str:
    if not person_type:
        return ""
    labels = {
        "facilitator": "Facilitator",
        "team": "Team",
        "team-passed-away": "In memory",
    }
    return labels.get(person_type, person_type.replace("_", " ").replace("-", " ").title())


def format_status(status: str | None) -> str:
    if not status or status == "active":
        return "Active"
    labels = {
        "previous-associate": "Previous associate",
    }
    return labels.get(status, status.replace("_", " ").replace("-", " ").title())


def person_display_label(person: dict) -> str:
    person_type = person.get("person_type")
    status = person.get("status") or "active"
    if person_type == "facilitator" and status == "previous-associate":
        return "Previous associate"
    return format_person_type(person_type)


def meta_row(label: str, value: str | None) -> str:
    if not value:
        return ""
    return f"      <dt>{html.escape(label)}</dt>\n      <dd>{value}</dd>\n"


def site_nav(active: str, prefix: str = "") -> str:
    links = [
        ("courses", "Courses", f"{prefix}index.html"),
        ("people", "People", f"{prefix}people.html"),
        ("other-content", "All other content", f"{prefix}other-content.html"),
    ]
    parts = []
    for key, label, href in links:
        if key == active:
            parts.append(f"<strong>{html.escape(label)}</strong>")
        else:
            parts.append(f'<a href="{href}">{html.escape(label)}</a>')
    return " · ".join(parts)


def breadcrumb_nav(prefix: str = "") -> str:
    return (
        f'<a href="{prefix}index.html">Courses</a> · '
        f'<a href="{prefix}people.html">People</a> · '
        f'<a href="{prefix}other-content.html">All other content</a>'
    )


def courses_by_facilitator(courses: list[dict]) -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = {}
    for course in courses:
        for fid in course.get("facilitators") or []:
            index.setdefault(fid, []).append(course)
    for fid in index:
        index[fid].sort(key=lambda c: (c.get("start_date") or "9999-99-99", c.get("title") or ""))
    return index


def build_index(courses: list[dict]) -> str:
    sorted_courses = sorted(
        courses,
        key=lambda c: (c.get("start_date") or "9999-99-99", c.get("title") or ""),
    )

    items = []
    for course in sorted_courses:
        slug = course_slug(course["id"])
        title = html.escape(course.get("title") or "Untitled course")
        dates = html.escape(format_date_range(course.get("start_date"), course.get("end_date")))
        meta_bits = [
            bit
            for bit in (
                dates,
                course.get("location_country"),
                course.get("clown_level"),
                course.get("medium"),
            )
            if bit
        ]
        meta = html.escape(" · ".join(meta_bits))
        items.append(
            f'    <li>\n'
            f'      <a href="courses/{slug}.html">{title}</a>\n'
            f'      <p>{meta}</p>\n'
            f"    </li>"
        )

    body = f"""  <header>
    <nav aria-label="Site">
      {site_nav("courses")}
    </nav>
    <h1>Courses</h1>
    <p>{len(sorted_courses)} courses from structured data.</p>
  </header>
  <main>
    <ul class="course-list">
{"\n".join(items)}
    </ul>
  </main>
"""
    return page_shell("Courses", body, css_href="style.css")


def person_list_items(people: list[dict], href_prefix: str) -> str:
    items = []
    for person in sorted(people, key=lambda p: (p.get("name") or "").lower()):
        pid = person["id"]
        name = html.escape(person.get("name") or "Untitled")
        country = person.get("country")
        region = person.get("region")
        meta_parts = [part for part in (country, region) if part]
        meta_html = ""
        if meta_parts:
            meta_html = (
                f'\n      <span class="person-meta">{html.escape(" · ".join(meta_parts))}</span>'
            )
        items.append(
            f'    <li><a href="{href_prefix}{html.escape(pid)}.html">{name}</a>{meta_html}</li>'
        )
    return "\n".join(items)


def people_by_type(people_list: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {
        "facilitator": [],
        "team": [],
        "previous-associate": [],
        "team-passed-away": [],
    }
    for person in people_list:
        person_type = person.get("person_type") or "team"
        status = person.get("status") or "active"
        if person_type == "facilitator" and status == "previous-associate":
            groups["previous-associate"].append(person)
        elif person_type == "facilitator":
            groups["facilitator"].append(person)
        else:
            groups.setdefault(person_type, []).append(person)
    return groups


def build_people_section(section_id: str, heading: str, description: str, people: list[dict]) -> str:
    if not people:
        return ""
    items = person_list_items(people, "people/")
    return f"""    <section class="people-section" id="{section_id}" aria-labelledby="{section_id}-heading">
      <h2 id="{section_id}-heading">{html.escape(heading)}</h2>
      <p>{html.escape(description.format(count=len(people)))}</p>
      <ul class="name-list">
{items}
      </ul>
    </section>"""


def build_people_index(people_list: list[dict]) -> str:
    groups = people_by_type(people_list)
    sections = [
        build_people_section(
            "facilitators",
            "Facilitators",
            "{count} course facilitators.",
            groups["facilitator"],
        ),
        build_people_section(
            "team",
            "Team",
            "{count} regional team members and trainees.",
            groups["team"],
        ),
        build_people_section(
            "previous-associates",
            "Previous associates",
            "{count} people who completed facilitator training but no longer facilitate with Nose to Nose.",
            groups["previous-associate"],
        ),
        build_people_section(
            "in-memory",
            "In memory",
            "{count} people remembered on the site.",
            groups["team-passed-away"],
        ),
    ]

    body = f"""  <header>
    <nav aria-label="Site">
      {site_nav("people")}
    </nav>
    <h1>People</h1>
    <p>{len(people_list)} people from structured data.</p>
  </header>
  <main>
{"\n".join(section for section in sections if section)}
  </main>
"""
    return page_shell("People", body, css_href="style.css", body_class="people-page")


def load_scraped_content() -> list[dict]:
    records: list[dict] = []
    for filename in SCRAPED_CONTENT_FILES:
        path = RAW_DATA_DIR / filename
        if not path.exists():
            continue
        records.extend(json.loads(path.read_text(encoding="utf-8")))
    return records


def content_href(content_id: str, prefix: str = "") -> str:
    return f"{prefix}content/{content_id}.html"


def content_file_path(content_id: str) -> Path:
    return CONTENT_DIR / f"{content_id}.html"


def content_path_prefix(content_id: str) -> str:
    return "../" * len(content_id.split("/"))


def content_css_href(content_id: str) -> str:
    return content_path_prefix(content_id) + "style.css"


def is_generic_title(title: str) -> bool:
    if title in GENERIC_TITLES:
        return True
    if title.startswith("Articles about clowning"):
        return True
    return False


def is_usable_heading(heading: str) -> bool:
    heading = heading.strip()
    if not heading or heading in ("", " "):
        return False
    if len(heading) > 120:
        return False
    if "http://" in heading or "https://" in heading or "mailto:" in heading:
        return False
    if heading.startswith("<") or "[" in heading or "]( " in heading:
        return False
    return True


def heading_from_markdown(md: str) -> str | None:
    for line in md.splitlines():
        match = re.match(r"^#\s+(.+)$", line.strip())
        if match:
            heading = match.group(1).strip()
            if is_usable_heading(heading):
                return heading
    return None


def display_title(record: dict) -> str:
    title = (record.get("title") or "").strip()
    if title and not is_generic_title(title):
        return title
    heading = heading_from_markdown(record.get("body_markdown") or "")
    if heading:
        return heading
    slug = record["id"].split("/")[-1]
    return slug.replace("-", " ").replace("%20", " ").title()


def clean_scraped_markdown(md: str) -> str:
    text = md.strip()
    text = re.sub(r"\n© .*", "", text, flags=re.S)
    text = re.sub(r"\n:   \[!\[.*", "", text, flags=re.S)
    text = re.sub(r"^(#\s*\n)+", "", text)
    return text.strip()


def group_scraped_content(records: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {key: [] for key in CONTENT_TYPE_ORDER}
    for record in records:
        content_type = record.get("type")
        if content_type in grouped:
            grouped[content_type].append(record)
    for items in grouped.values():
        items.sort(key=lambda r: display_title(r).lower())
    return grouped


def build_other_content_index(records: list[dict]) -> str:
    grouped = group_scraped_content(records)
    sections = [
        (content_type, CONTENT_TYPE_LABELS[content_type])
        for content_type in CONTENT_TYPE_ORDER
        if grouped[content_type]
    ]
    sidebar_items = "\n".join(
        f'        <li><a href="#{content_type}">{html.escape(label)}</a></li>'
        for content_type, label in sections
    )

    section_blocks = []
    for content_type, label in sections:
        items = grouped[content_type]
        link_items = []
        for record in items:
            title = html.escape(display_title(record))
            href = content_href(record["id"])
            link_items.append(f'      <li><a href="{href}">{title}</a></li>')
        list_class = "link-list name-list" if len(items) > 8 else "link-list"
        section_blocks.append(
            f"""      <section class="contents-section" id="{content_type}" aria-labelledby="{content_type}-heading">
        <h2 id="{content_type}-heading">{html.escape(label)}</h2>
        <p>{len(items)} pages.</p>
        <ul class="{list_class}">
{"\n".join(link_items)}
        </ul>
      </section>"""
        )

    body = f"""  <header>
    <nav aria-label="Site">
      {site_nav("other-content")}
    </nav>
    <h1>All other content</h1>
    <p>Pages scraped from nosetonose.info — articles, thoughts, site pages, testimonials, and team information.</p>
  </header>
  <div class="contents-layout">
    <nav class="contents-sidebar" aria-label="Sections">
      <h2 class="visually-hidden">Jump to section</h2>
      <ul>
{sidebar_items}
      </ul>
    </nav>
    <main class="contents-main">
{"\n".join(section_blocks)}
    </main>
  </div>
"""
    return page_shell("All other content", body, css_href="style.css", body_class="contents-page")


def build_scraped_content_page(record: dict) -> str:
    content_id = record["id"]
    prefix = content_path_prefix(content_id)
    title = display_title(record)
    type_label = CONTENT_TYPE_LABELS.get(record.get("type", ""), record.get("type", "Content"))
    body_md = clean_scraped_markdown(record.get("body_markdown") or "")
    if body_md:
        content_html = markdown_to_html(body_md)
    else:
        content_html = '<p class="unavailable">No content available.</p>'

    source = record.get("source_url")
    source_html = ""
    if source:
        escaped = html.escape(source, quote=True)
        source_html = f'        <p>Original page: <a href="{escaped}">{html.escape(source)}</a></p>\n'

    body = f"""  <header>
    <nav aria-label="Breadcrumb">
      {breadcrumb_nav(prefix)}
    </nav>
    <p class="content-type">{html.escape(type_label)}</p>
    <h1>{html.escape(title)}</h1>
  </header>
  <main>
    <article class="scraped-content">
      {content_html}
      <footer>
{source_html}      </footer>
    </article>
  </main>
"""
    return page_shell(title, body, css_href=content_css_href(content_id))


def strip_leading_images(text: str | None, photo: str | None = None) -> str | None:
    """Remove leading image markup from background text when photo is shown separately."""
    if not text:
        return text
    cleaned = text.strip()
    cleaned = re.sub(r"^(?:\[!\[[^\]]*\]\([^)]+\)\]\([^)]+\)\s*)+", "", cleaned)
    cleaned = re.sub(r"^(?:!\[[^\]]*\]\([^)]+\)\s*)+", "", cleaned)
    cleaned = re.sub(r"^(?:<a[^>]*>\s*)?<img[^>]*>\s*(?:</a>\s*)?", "", cleaned, flags=re.I)
    return cleaned.strip() or None


def build_person_page(
    person: dict,
    courses: list[dict],
) -> str:
    name = person.get("name") or "Untitled person"
    person_type = format_person_type(person.get("person_type"))
    display_label = person_display_label(person)
    status = person.get("status") or "active"
    is_facilitator = person.get("person_type") == "facilitator"
    country = person.get("country")
    region = person.get("region")
    country_display = (
        html.escape(country)
        if country
        else '<span class="unavailable">Not specified</span>'
    )
    region_display = (
        html.escape(region)
        if region
        else '<span class="unavailable">Not specified</span>'
    )

    metadata_html = "".join(
        row
        for row in (
            meta_row("Person type", html.escape(person_type) if person_type else ""),
            meta_row("Status", html.escape(format_status(status))),
            meta_row("Country", country_display),
            meta_row("Region", region_display),
        )
        if row
    )

    photo = person.get("photo")
    if photo:
        src = html.escape(photo, quote=True)
        photo_block = f"""        <figure>
          <img src="{src}" alt="{html.escape(name)}" width="225">
        </figure>"""
    else:
        photo_block = '        <p class="unavailable">No photo available.</p>'

    background = strip_leading_images(person.get("background"), photo)
    if background:
        background_block = markdown_to_html(background)
    else:
        background_block = '<p class="unavailable">No biography available.</p>'

    courses_section = ""
    if is_facilitator:
        course_items = []
        for course in courses:
            slug = course_slug(course["id"])
            title = html.escape(course.get("title") or "Untitled course")
            dates = html.escape(format_date_range(course.get("start_date"), course.get("end_date")))
            meta = f" — {dates}" if dates else ""
            course_items.append(
                f'        <li><a href="../courses/{slug}.html">{title}</a>{meta}</li>'
            )

        if course_items:
            courses_block = "<ul>\n" + "\n".join(course_items) + "\n        </ul>"
        else:
            courses_block = '<p class="unavailable">No courses listed.</p>'

        courses_section = f"""      <section aria-labelledby="courses">
        <h2 id="courses">Courses</h2>
        {courses_block}
      </section>
"""

    source_footer = ""
    if not is_facilitator:
        source_urls = person.get("source_urls") or []
        if source_urls:
            if len(source_urls) == 1:
                escaped = html.escape(source_urls[0], quote=True)
                source_footer = (
                    f"      <footer>\n"
                    f'        <p>Original page: <a href="{escaped}">'
                    f"{html.escape(source_urls[0])}</a></p>\n"
                    f"      </footer>\n"
                )
            else:
                source_items = []
                for source in source_urls:
                    escaped = html.escape(source, quote=True)
                    source_items.append(
                        f'        <li><a href="{escaped}">{html.escape(source)}</a></li>'
                    )
                source_footer = (
                    "      <footer>\n"
                    "        <p>Original pages:</p>\n"
                    "        <ul>\n"
                    + "\n".join(source_items)
                    + "\n        </ul>\n"
                    "      </footer>\n"
                )

    body = f"""  <header>
    <nav aria-label="Breadcrumb">
      {breadcrumb_nav("../")}
    </nav>
    <p class="content-type">{html.escape(display_label)}</p>
    <h1>{html.escape(name)}</h1>
  </header>
  <main>
    <article>
      <section aria-labelledby="person-details">
        <h2 id="person-details">Details</h2>
        <dl>
{metadata_html}        </dl>
      </section>
      <section aria-labelledby="photo">
        <h2 id="photo">Photo</h2>
{photo_block}
      </section>
      <section aria-labelledby="background">
        <h2 id="background">Background</h2>
        {background_block}
      </section>
{courses_section}{source_footer}    </article>
  </main>
"""
    return page_shell(name, body, css_href="../style.css")


def build_course_page(
    course: dict,
    venues: dict[str, dict],
    people: dict[str, dict],
) -> str:
    slug = course_slug(course["id"])
    title = course.get("title") or "Untitled course"

    venue_html = ""
    venue_id = course.get("venue")
    if venue_id and venue_id in venues:
        venue = venues[venue_id]
        venue_bits = [
            f"<strong>{html.escape(venue['name'])}</strong>",
        ]
        if venue.get("address"):
            venue_bits.append(html.escape(venue["address"]))
        if venue.get("email"):
            email = html.escape(venue["email"])
            venue_bits.append(f'<a href="mailto:{email}">{email}</a>')
        if venue.get("phone"):
            venue_bits.append(html.escape(venue["phone"]))
        venue_html = "<br>\n".join(venue_bits)

    facilitator_items = []
    for fid in course.get("facilitators") or []:
        person = people.get(fid)
        if person:
            facilitator_items.append(
                f'<li><a href="../people/{html.escape(fid)}.html">'
                f"{html.escape(person['name'])}</a></li>"
            )
    facilitators_html = (
        "<ul>\n" + "\n".join(facilitator_items) + "\n</ul>" if facilitator_items else ""
    )

    group_size = course.get("maximum_group_size")
    group_size_text = str(group_size) if group_size is not None else None

    metadata = [
        meta_row("Start date", html.escape(format_date(course.get("start_date")) or "")),
        meta_row("End date", html.escape(format_date(course.get("end_date")) or "")),
        meta_row("Location", html.escape(course.get("location_country") or "")),
        meta_row("Venue", venue_html),
        meta_row("Language", html.escape(course.get("language") or "")),
        meta_row("Facilitators", facilitators_html),
        meta_row("Clown level", html.escape(course.get("clown_level") or "")),
        meta_row("Prerequisites", html.escape(course.get("prerequisites") or "")),
        meta_row("Medium", html.escape(course.get("medium") or "")),
        meta_row("Maximum group size", html.escape(group_size_text or "")),
        meta_row("Course fee", html.escape(course.get("course_fee") or "")),
        meta_row("Course fee deposit", html.escape(course.get("course_fee_deposit") or "")),
    ]
    metadata_html = "".join(row for row in metadata if row)

    sections = []
    for heading, field in (
        ("Schedule", "schedule"),
        ("Course description", "course_description"),
        ("Accommodation and meals", "accommodation_and_meals"),
    ):
        content = course.get(field)
        if content:
            sections.append(
                f"""    <section>
      <h2>{html.escape(heading)}</h2>
      {markdown_to_html(content)}
    </section>"""
            )

    source = course.get("source_url")
    source_html = ""
    if source:
        escaped = html.escape(source, quote=True)
        source_html = f'    <p>Original page: <a href="{escaped}">{html.escape(source)}</a></p>\n'

    body = f"""  <header>
    <nav aria-label="Breadcrumb">
      {breadcrumb_nav("../")}
    </nav>
    <h1>{html.escape(title)}</h1>
  </header>
  <main>
    <article>
      <section aria-labelledby="course-details">
        <h2 id="course-details">Details</h2>
        <dl>
{metadata_html}        </dl>
      </section>
{"\n".join(sections)}
      <footer>
{source_html}      </footer>
    </article>
  </main>
"""
    return page_shell(title, body, css_href="../style.css")


def build_style() -> str:
    return """body {
  font-family: Georgia, "Times New Roman", serif;
  line-height: 1.5;
  max-width: 42rem;
  margin: 1.5rem auto;
  padding: 0 1rem;
  color: #111;
  background: #fff;
}

header {
  margin-bottom: 2rem;
}

nav a {
  color: inherit;
}

h1 {
  font-size: 1.5rem;
  line-height: 1.3;
}

h2 {
  font-size: 1.1rem;
  margin-top: 2rem;
}

dl {
  margin: 0;
}

dt {
  font-weight: bold;
  margin-top: 0.75rem;
}

dd {
  margin: 0.25rem 0 0 0;
}

.course-list {
  list-style: none;
  padding: 0;
}

.course-list li {
  margin-bottom: 1.25rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid #ccc;
}

.course-list a {
  color: inherit;
}

.course-list p {
  margin: 0.25rem 0 0;
  color: #444;
}

.name-list {
  list-style: none;
  padding: 0;
  columns: 2;
  column-gap: 2rem;
}

.name-list li {
  margin-bottom: 0.5rem;
  break-inside: avoid;
}

.person-meta {
  display: block;
  margin-top: 0.15rem;
  color: #444;
  font-size: 0.9rem;
}

figure {
  margin: 0;
}

figure img {
  max-width: 100%;
  height: auto;
}

.unavailable {
  margin: 0;
  color: #666;
  font-style: italic;
}

a {
  color: #0044cc;
}

footer {
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid #ccc;
  font-size: 0.9rem;
}

.people-section {
  margin-bottom: 2.5rem;
  scroll-margin-top: 1.5rem;
}

.people-section > p {
  margin: 0 0 0.75rem;
  color: #444;
}

body.people-page .name-list {
  margin-bottom: 0;
}

body.contents-page {
  max-width: 56rem;
}

.contents-layout {
  display: grid;
  grid-template-columns: 10rem 1fr;
  gap: 2rem;
  align-items: start;
}

.contents-sidebar {
  position: sticky;
  top: 1.5rem;
  font-size: 0.95rem;
}

.contents-sidebar ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.contents-sidebar li {
  margin-bottom: 0.35rem;
}

.contents-sidebar a {
  color: inherit;
  text-decoration: none;
}

.contents-sidebar a:hover {
  text-decoration: underline;
}

.contents-section {
  margin-bottom: 2.5rem;
  scroll-margin-top: 1.5rem;
}

.contents-section > p {
  margin: 0 0 0.75rem;
  color: #444;
}

.link-list {
  list-style: none;
  padding: 0;
}

.link-list li {
  margin-bottom: 0.5rem;
}

.link-list .meta {
  color: #444;
  font-size: 0.9rem;
}

.content-type {
  margin: 0 0 0.25rem;
  color: #666;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.scraped-content h2,
.scraped-content h3,
.scraped-content h4 {
  margin-top: 1.5rem;
}

.scraped-content img {
  max-width: 100%;
  height: auto;
}

.scraped-content blockquote {
  margin: 1rem 0;
  padding-left: 1rem;
  border-left: 3px solid #ccc;
  color: #333;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 40rem) {
  .contents-layout {
    grid-template-columns: 1fr;
  }

  .contents-sidebar {
    position: static;
    border-bottom: 1px solid #ccc;
    padding-bottom: 1rem;
    margin-bottom: 0.5rem;
  }

  .contents-sidebar ul {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem 1rem;
  }
}
"""


def main() -> None:
    courses = load_json("courses.json")
    venues = {v["id"]: v for v in load_json("venues.json")}
    people_list = load_json("people.json")
    people = {p["id"]: p for p in people_list}
    person_courses = courses_by_facilitator(courses)
    scraped_content = load_scraped_content()

    COURSES_DIR.mkdir(parents=True, exist_ok=True)
    PEOPLE_DIR.mkdir(parents=True, exist_ok=True)
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    (WEB_DIR / "index.html").write_text(build_index(courses), encoding="utf-8")
    (WEB_DIR / "people.html").write_text(build_people_index(people_list), encoding="utf-8")
    (WEB_DIR / "other-content.html").write_text(
        build_other_content_index(scraped_content), encoding="utf-8"
    )
    (WEB_DIR / "style.css").write_text(build_style(), encoding="utf-8")

    stale_contents = WEB_DIR / "contents.html"
    if stale_contents.exists():
        stale_contents.unlink()

    stale_facilitators_index = WEB_DIR / "facilitators.html"
    if stale_facilitators_index.exists():
        stale_facilitators_index.unlink()

    for course in courses:
        slug = course_slug(course["id"])
        page = build_course_page(course, venues, people)
        (COURSES_DIR / f"{slug}.html").write_text(page, encoding="utf-8")

    valid_people_ids = {p["id"] for p in people_list}
    for person in people_list:
        pid = person["id"]
        page = build_person_page(person, person_courses.get(pid, []))
        (PEOPLE_DIR / f"{pid}.html").write_text(page, encoding="utf-8")

    for stale in PEOPLE_DIR.glob("*.html"):
        if stale.stem not in valid_people_ids:
            stale.unlink()

    stale_facilitators_dir = WEB_DIR / "facilitators"
    if stale_facilitators_dir.exists():
        for stale in stale_facilitators_dir.glob("*.html"):
            stale.unlink()
        if not any(stale_facilitators_dir.iterdir()):
            stale_facilitators_dir.rmdir()

    valid_content_paths = set()
    for record in scraped_content:
        path = content_file_path(record["id"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(build_scraped_content_page(record), encoding="utf-8")
        valid_content_paths.add(path.resolve())

    for stale in CONTENT_DIR.rglob("*.html"):
        if stale.resolve() not in valid_content_paths:
            stale.unlink()

    print(f"Wrote {WEB_DIR / 'index.html'}")
    print(f"Wrote {WEB_DIR / 'people.html'}")
    print(f"Wrote {WEB_DIR / 'other-content.html'}")
    print(f"Wrote {len(courses)} course pages in {COURSES_DIR}")
    print(f"Wrote {len(people_list)} people pages in {PEOPLE_DIR}")
    groups = people_by_type(people_list)
    group_labels = {
        "facilitator": "facilitator",
        "team": "team",
        "previous-associate": "previous associate",
        "team-passed-away": "in memory",
    }
    for group_key, members in groups.items():
        if members:
            print(f"  ({len(members)} {group_labels.get(group_key, group_key)})")
    print(f"Wrote {len(scraped_content)} scraped content pages in {CONTENT_DIR}")


if __name__ == "__main__":
    main()
