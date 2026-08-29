#!/usr/bin/env python3
"""Copy pipeline data into this SvelteKit project so the site runs independently.

Reads from the parent nosetonose repo (../data) when present, writes into
src/lib/data and src/lib/content. Re-run after extract_structured.py or
editorial Markdown edits in the parent repo.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent
SRC_STRUCTURED = PARENT / "data" / "structured"
SRC_EDITORIAL = PARENT / "data"
SRC_TESTIMONIALS = PARENT / "data" / "testimonials.json"
SRC_ARTICLE_BODIES = PARENT / "data" / "bodies" / "articles"

DEST_DATA = ROOT / "src" / "lib" / "data"
DEST_PAGES = ROOT / "src" / "lib" / "content" / "pages"
DEST_ARTICLES = ROOT / "src" / "lib" / "content" / "articles"

LINK_REWRITES = (
    (r"applied-clowning\.html", "/training/for-organisations"),
    (r"training-programme\.html", "/training/clown-programme"),
    (r"approach\.html", "/approach"),
    (r"booking\.html", "/how-to-book"),
    (r"articles\.html", "/articles"),
    (r"people\.html", "/team"),
    (r"index\.html", "/"),
    (r"content/contact\.html", "/contact"),
    (r"content/sorry\.html", "/articles"),
    (r"content/articles/([^)\s]+)\.html", r"/articles/\1"),
)

EDITORIAL_PAGES = (
    {
        "src": "approach.md",
        "dest": "approach.md",
        "title": "Approach",
    },
    {
        "src": "training-programme.md",
        "dest": "clown-programme.md",
        "title": "Clown programme",
    },
    {
        "src": "applied-clowning.md",
        "dest": "for-organisations.md",
        "title": "For organisations",
    },
    {
        "src": "booking.md",
        "dest": "how-to-book.md",
        "title": "How to book",
    },
    {
        "src": "articles.md",
        "dest": "articles.md",
        "title": "Articles",
    },
)

CONTACT_MD = """---
title: Contact us
---

# Contact us

For course bookings and general enquiries, email [mail@nosetonose.info](mailto:mail@nosetonose.info) or [nosetonoseoffice@gmail.com](mailto:nosetonoseoffice@gmail.com).

# Join our mailing list

Fill in the form on the link below and receive our newsletter (*you can easily and automatically unsubscribe at any time*). We send updates and news twice a year. We do not share our mailing list.

[Join our newsletter](https://go.reachmail.net/SubscriptionForm/2b462544-0262-4f80-9928-aa4400d56563)
"""


def rewrite_links(text: str) -> str:
    for pattern, repl in LINK_REWRITES:
        text = re.sub(pattern, repl, text)
    return text


def clean_scraped_markdown(md: str) -> str:
    text = md.strip()
    text = re.sub(r"\n# Email me this article\b.*", "", text, flags=re.S | re.I)
    text = re.sub(r"\n© .*", "", text, flags=re.S)
    text = re.sub(r"\n:   \[!\[.*", "", text, flags=re.S)
    text = re.sub(r"^(#\s*\n)+", "", text)
    return text.strip()


def first_heading(md: str) -> str | None:
    match = re.search(r"^#\s+(.+)$", md, re.M)
    if not match:
        return None
    return re.sub(r"\s+", " ", match.group(1)).strip()


def yaml_escape(value: str) -> str:
    if any(ch in value for ch in (":", "#", "{", "}", "[", "]", ",", "&", "*", "!", "|", ">", "'", '"', "%", "@", "`")):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def write_markdown(path: Path, title: str, body: str, extra: dict[str, str] | None = None) -> None:
    lines = ["---", f"title: {yaml_escape(title)}"]
    if extra:
        for key, value in extra.items():
            lines.append(f"{key}: {yaml_escape(value)}")
    lines.append("---")
    lines.append("")
    lines.append(body.rstrip())
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def record_slug(record: dict, *, from_id_path: bool = False) -> str:
    record_id = str(record.get("id") or "")
    if from_id_path:
        return record_id.split("/")[-1]
    return record_id


def write_json_entries(dest: Path, records: list[dict], *, from_id_path: bool = False) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    wanted: set[str] = set()
    for record in records:
        slug = record_slug(record, from_id_path=from_id_path)
        if not slug:
            raise SystemExit(f"Record missing id: {record!r}")
        if slug in wanted:
            raise SystemExit(f"Duplicate filename slug {slug!r}")
        wanted.add(slug)
        (dest / f"{slug}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    for stale in dest.glob("*.json"):
        if stale.stem not in wanted:
            stale.unlink()


def copy_structured() -> None:
    if not SRC_STRUCTURED.is_dir():
        raise SystemExit(
            f"Parent structured data not found at {SRC_STRUCTURED}. "
            "The site already has its own copy; sync is only needed to refresh it."
        )
    DEST_DATA.mkdir(parents=True, exist_ok=True)
    specs = (
        ("courses.json", "courses", True),
        ("venues.json", "venues", False),
        ("people.json", "people", False),
    )
    for filename, folder, from_id_path in specs:
        src = SRC_STRUCTURED / filename
        if not src.is_file():
            raise SystemExit(f"Missing {src}")
        records = json.loads(src.read_text(encoding="utf-8"))
        write_json_entries(DEST_DATA / folder, records, from_id_path=from_id_path)
        combined = DEST_DATA / filename
        if combined.exists():
            combined.unlink()
        print(f"Wrote {len(records)} {folder} entries")


def testimonial_filename(record: dict) -> str:
    slug = str(record.get("slug") or "").strip()
    slug = unquote(slug)
    if not slug:
        slug = record_slug(record, from_id_path=True)
    slug = re.sub(r"[^\w\-]+", "-", slug).strip("-").lower()
    return slug or "testimonial"


def normalize_testimonial(record: dict) -> dict:
    quote = record.get("body_markdown") or record.get("quote") or ""
    quote = rewrite_links(clean_scraped_markdown(str(quote)))
    date = str(record.get("date") or "").strip()
    if "T" in date:
        date = date.split("T", 1)[0]
    return {
        "id": str(record.get("id") or ""),
        "title": str(record.get("title") or "").strip(),
        "source_url": str(record.get("source_url") or "").strip(),
        "date": date,
        "quote": quote,
    }


def copy_testimonials() -> None:
    if not SRC_TESTIMONIALS.is_file():
        print("No testimonials.json found; skipped.")
        return
    records = json.loads(SRC_TESTIMONIALS.read_text(encoding="utf-8"))
    dest = DEST_DATA / "testimonials"
    dest.mkdir(parents=True, exist_ok=True)
    wanted: set[str] = set()
    for record in records:
        normalized = normalize_testimonial(record)
        if not normalized["id"]:
            raise SystemExit(f"Testimonial missing id: {record!r}")
        slug = testimonial_filename(record)
        if slug in wanted:
            slug = f"{slug}-{record_slug(record, from_id_path=True)}"
        wanted.add(slug)
        (dest / f"{slug}.json").write_text(
            json.dumps(normalized, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    for stale in dest.glob("*.json"):
        if stale.stem not in wanted:
            stale.unlink()
    combined = DEST_DATA / "testimonials.json"
    if combined.exists():
        combined.unlink()
    print(f"Wrote {len(records)} testimonials entries")


def copy_editorial() -> None:
    DEST_PAGES.mkdir(parents=True, exist_ok=True)
    for page in EDITORIAL_PAGES:
        src = SRC_EDITORIAL / page["src"]
        if not src.is_file():
            raise SystemExit(f"Missing {src}")
        body = rewrite_links(src.read_text(encoding="utf-8").strip())
        write_markdown(DEST_PAGES / page["dest"], page["title"], body)
        print(f"Wrote pages/{page['dest']}")
    (DEST_PAGES / "contact.md").write_text(CONTACT_MD.lstrip(), encoding="utf-8")
    print("Wrote pages/contact.md")


def copy_articles() -> None:
    DEST_ARTICLES.mkdir(parents=True, exist_ok=True)
    for stale in DEST_ARTICLES.glob("*.md"):
        stale.unlink()
    if not SRC_ARTICLE_BODIES.is_dir():
        print("No article bodies found; skipped.")
        return
    count = 0
    for src in sorted(SRC_ARTICLE_BODIES.glob("*.md")):
        raw = src.read_text(encoding="utf-8")
        source_url = ""
        scrape_title = ""
        fm = re.match(r"^---\n([\s\S]*?)\n---\n?", raw)
        body = raw
        if fm:
            body = raw[fm.end() :]
            for line in fm.group(1).splitlines():
                if line.startswith("source_url:"):
                    source_url = line.split(":", 1)[1].strip()
                elif line.startswith("title:"):
                    scrape_title = line.split(":", 1)[1].strip().strip('"')
        body = rewrite_links(clean_scraped_markdown(body))
        title = first_heading(body) or scrape_title or src.stem
        extra = {"source_url": source_url} if source_url else None
        write_markdown(DEST_ARTICLES / src.name, title, body, extra)
        count += 1
    print(f"Wrote {count} articles")


def main() -> None:
    copy_structured()
    copy_testimonials()
    copy_editorial()
    copy_articles()
    print(f"Done. Data lives under {ROOT / 'src' / 'lib'}")


if __name__ == "__main__":
    main()
