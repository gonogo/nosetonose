"""Extract structured courses, venues, and people from scraped data."""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup, NavigableString, Tag

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
OUT_DIR = DATA_DIR / "structured"

MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "octobre": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

COUNTRY_ALIASES = {
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "united kingdom": "United Kingdom",
    "england": "United Kingdom",
    "scotland": "United Kingdom",
    "wales": "United Kingdom",
    "northern ireland": "United Kingdom",
    "ireland": "Ireland",
    "usa": "United States",
    "u.s.a.": "United States",
    "us": "United States",
    "united states": "United States",
    "north america": "United States",
    "canada": "Canada",
    "germany": "Germany",
    "deutschland": "Germany",
    "france": "France",
    "italy": "Italy",
    "italia": "Italy",
    "belgium": "Belgium",
    "poland": "Poland",
    "czech republic": "Czech Republic",
    "czechia": "Czech Republic",
    "switzerland": "Switzerland",
    "netherlands": "Netherlands",
    "austria": "Austria",
    "denmark": "Denmark",
    "sweden": "Sweden",
    "norway": "Norway",
    "spain": "Spain",
    "portugal": "Portugal",
    "israel": "Israel",
    "taiwan": "Taiwan",
    "luxembourg": "Luxembourg",
    "britain": "United Kingdom",
}

REGION_COUNTRY_MAP = {
    "uk": "United Kingdom",
    "na": "United States",
    "de": "Germany",
    "it": "Italy",
    "pl": "Poland",
    "ie": "Ireland",
    "fr": "France",
}

SECTION_COUNTRY_PREFIXES = (
    ("israel", "Israel"),
    ("germany", "Germany"),
    ("ireland", "Ireland"),
    ("uk", "United Kingdom"),
    ("france", "France"),
    ("taiwan", "Taiwan"),
    ("canada", "Canada"),
    ("usa", "United States"),
    ("belgium", "Belgium"),
    ("italy", "Italy"),
    ("poland", "Poland"),
    ("switzerland", "Switzerland"),
)

CITY_COUNTRY_HINTS = {
    "potsdam": "Germany",
    "cologne": "Germany",
    "munich": "Germany",
    "gröbenzell": "Germany",
    "stuttgart": "Germany",
    "bristol": "United Kingdom",
    "leicester": "United Kingdom",
    "hastings": "United Kingdom",
    "brighton": "United Kingdom",
    "london": "United Kingdom",
    "east grinstead": "United Kingdom",
    "west sussex": "United Kingdom",
    "sutton courtenay": "United Kingdom",
    "oxford": "United Kingdom",
    "philadelphia": "United States",
    "brooklyn": "United States",
    "callan": "Ireland",
    "kilkenny": "Ireland",
    "dublin": "Ireland",
    "dornach": "Switzerland",
    "brussels": "Belgium",
    "luxembourg": "Luxembourg",
    "lille": "France",
    "ostuni": "Italy",
    "bari": "Italy",
    "amsterdam": "Netherlands",
    "toronto": "Canada",
    "tel aviv": "Israel",
    "ynys enlli": "United Kingdom",
    "peredur": "United Kingdom",
    "artemis school": "United Kingdom",
}

SKIP_FACILITATOR_HEADINGS = {
    "facilitator",
    "facilitators",
    "associate",
    "where we are",
    "our team",
    "our team in north america",
    "previous associates",
    "facilitators in training 2012-14",
}


def normalize_country_token(token: str) -> str | None:
    token = clean_text(token).strip(" .")
    if not token:
        return None
    lower = token.lower()
    if lower in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[lower]
    canonical = {country.lower(): country for country in set(COUNTRY_ALIASES.values())}
    if lower in canonical:
        return canonical[lower]
    for key, country in sorted(COUNTRY_ALIASES.items(), key=lambda x: -len(x[0])):
        if re.search(rf"\b{re.escape(key)}\b", lower):
            return country
    for city, country in sorted(CITY_COUNTRY_HINTS.items(), key=lambda x: -len(x[0])):
        if city in lower:
            return country
    return None


def country_from_section_heading(heading: str) -> str | None:
    heading = clean_text(heading).lower()
    for prefix, country in SECTION_COUNTRY_PREFIXES:
        if heading.startswith(prefix):
            return country
    return None


def extract_country_from_name(name: str) -> str | None:
    match = re.search(r"\(([^)]+)\)\s*$", name)
    if not match:
        return None
    for part in re.split(r"\s*/\s*", match.group(1)):
        country = normalize_country_token(part.strip())
        if country:
            return country
    return None


def extract_person_country(
    name: str,
    background: str | None = None,
    section_country: str | None = None,
) -> str | None:
    if country := extract_country_from_name(name):
        return country

    text = re.sub(r"\s+", " ", background or "")
    text_lower = text.lower()

    if re.search(r"\boxford university\b", text_lower):
        return "United Kingdom"

    if re.search(r"\bpracticing gp\b", text_lower):
        return "United Kingdom"

    intro = text_lower[:400]
    if re.search(r"\b(?:in the )?usa\b|\bunited states\b", intro):
        return "United States"

    bio_patterns = (
        r"lives (?:both )?in (?:the )?([^.,\n]+?)(?:\s+and\s+|\s+where|\s*[.,\n]|$)",
        r"(?:she|he|they) (?:live|lives) in ([^.,\n]+)",
        r"based in [^.,\n]*?\b(?:in the |in )?([^.,\n]+)",
        r"settling down in ([^.,\n]+)",
        r"now (?:works|reside[s]?) (?:as [^.,\n]+ )?in ([^.,\n]+)",
        r"reside in ([^.,\n]+)",
        r"teaches [^.,\n]+ in ([^.,\n]+)",
        r"born (?:and grew up )?in (?:the )?([^.,\n]+)",
        r"grew up in ([^.,\n]+)",
        r"(?:has |have )?(?:her|his|their) origins in ([^.,\n]+)",
        r"origins in ([^.,\n]+)",
    )
    for pattern in bio_patterns:
        match = re.search(pattern, text_lower, re.I)
        if match:
            country = normalize_country_token(match.group(1))
            if country:
                return country

    for city, country in sorted(CITY_COUNTRY_HINTS.items(), key=lambda x: -len(x[0])):
        if re.search(rf"\b{re.escape(city)}\b", text_lower):
            return country

    match = re.search(
        r"\b([A-Za-z\s]+),\s*(Germany|France|Belgium|Italy|Ireland|Canada|Poland|Switzerland|Luxembourg|Netherlands|United States|United Kingdom)\b",
        text,
        re.I,
    )
    if match:
        country = normalize_country_token(match.group(2))
        if country:
            return country

    head = text_lower[:600]
    for key, country in sorted(COUNTRY_ALIASES.items(), key=lambda x: -len(x[0])):
        if re.search(rf"\b{re.escape(key)}\b", head):
            return country

    if section_country:
        return section_country

    return None


def infer_region_from_country(country: str | None) -> str | None:
    if not country:
        return None
    if country == "United Kingdom":
        return "UK"
    if country in {"United States", "Canada"}:
        return "North America"
    return "Europe"


def infer_countries_from_courses(
    courses: list[dict], people_by_id: dict[str, dict] | None = None
) -> dict[str, str]:
    from collections import Counter

    people_by_id = people_by_id or {}
    counts: dict[str, Counter[str]] = {}
    for course in courses:
        country = course.get("location_country")
        if not country:
            continue
        for fid in course.get("facilitators") or []:
            counts.setdefault(fid, Counter())[country] += 1

    result: dict[str, str] = {}
    for fid, counter in counts.items():
        if not counter:
            continue
        top = counter.most_common()
        if len(top) > 1 and top[0][1] == top[1][1]:
            bio = (people_by_id.get(fid) or {}).get("background") or ""
            bio_lower = bio.lower()
            for country, _ in top:
                if country.lower() in bio_lower:
                    result[fid] = country
                    break
            else:
                result[fid] = top[0][0]
        else:
            result[fid] = top[0][0]
    return result


def build_page_country_hints(team_pages: list[dict]) -> dict[str, str]:
    hints: dict[str, str] = {}
    for page in team_pages:
        region_country = REGION_COUNTRY_MAP.get((page.get("region") or "").lower())
        for person in extract_team_people_from_page(page):
            fid = canonicalize_facilitator_id(canonicalize_facilitator_name(person["name"]))
            if person.get("country"):
                hints[fid] = person["country"]
            elif region_country:
                hints.setdefault(fid, region_country)
    return hints


def is_team_source_page(record: dict) -> bool:
    page_id = (record.get("id") or "").lower()
    slug = ((record.get("meta") or {}).get("slug") or "").lower()
    title = (record.get("title") or "").lower()
    url = (record.get("source_url") or "").lower()
    blob = f"{page_id} {slug} {title} {url}"
    if any(excluded in blob for excluded in TEAM_PAGE_EXCLUDES):
        return False
    return any(hint in blob for hint in TEAM_PAGE_HINTS)


def person_type_for_team_page(page: dict) -> str:
    page_id = page.get("id") or ""
    if page_id in FACILITATOR_SOURCE_PAGE_IDS:
        return "facilitator"
    if page_id in PREVIOUS_ASSOCIATE_PAGE_IDS:
        return "facilitator"
    if page_id in PASSED_AWAY_PAGE_IDS:
        return "team-passed-away"
    return "team"


def status_for_team_page(page: dict) -> str | None:
    page_id = page.get("id") or ""
    if page_id in PREVIOUS_ASSOCIATE_PAGE_IDS:
        return "previous-associate"
    return None


def merge_person_type(existing: str | None, new: str | None) -> str:
    existing = existing or "team"
    new = new or "team"
    if existing == "facilitator" or new == "facilitator":
        return "facilitator"
    if PERSON_TYPE_PRIORITY.get(existing, 0) >= PERSON_TYPE_PRIORITY.get(new, 0):
        return existing
    return new


def merge_status(existing: str | None, new: str | None) -> str:
    if existing == "active" or new == "active":
        return "active"
    if existing == "previous-associate" or new == "previous-associate":
        return "previous-associate"
    return "active"


def load_person_source_pages() -> list[dict]:
    pages = load_team_source_pages()
    seen = {page["id"] for page in pages}
    extra_ids = PREVIOUS_ASSOCIATE_PAGE_IDS | PASSED_AWAY_PAGE_IDS
    for filename in ("people.json", "pages.json"):
        path = DATA_DIR / filename
        if not path.exists():
            continue
        for record in json.loads(path.read_text(encoding="utf-8")):
            record_id = record.get("id") or ""
            if record_id in extra_ids and record_id not in seen:
                pages.append(record)
                seen.add(record_id)
    return pages


def parse_people_from_memory_references(md: str, page_region: str = "") -> list[dict]:
    people: list[dict] = []
    if not md:
        return people

    region_country = REGION_COUNTRY_MAP.get((page_region or "").lower())

    for match in re.finditer(
        r"(?:in memory of|and in memory of)\s+(.+?)\s+who died\b([^\n#]*)",
        md,
        re.I,
    ):
        name = normalize_people_heading_name(match.group(1))
        if is_skipped_people_heading(name) or not is_person_name(name):
            continue
        death_note = clean_text(match.group(2))
        start = match.end()
        next_memory = re.search(
            r"(?:in memory of|and in memory of)\s+[A-Z]",
            md[start:],
            re.I,
        )
        end = start + next_memory.start() if next_memory else len(md)
        bio = normalize_markdown(md[start:end].strip())
        bio = re.sub(r"^Read bio\.\.\.\s*", "", bio, flags=re.I)
        if death_note and bio:
            bio = f"{death_note.strip()}\n\n{bio}"
        elif death_note:
            bio = death_note.strip()
        people.append(
            {
                "name": name,
                "background": bio or None,
                "photo": None,
                "country": extract_person_country(name, bio, region_country),
            }
        )

    in_memory_section = False
    for line in md.splitlines():
        heading = re.sub(r"^#+\s*", "", line.strip())
        if re.search(r"in memory of", heading, re.I):
            in_memory_section = True
            continue
        if not in_memory_section or not line.strip().startswith("#"):
            continue
        date_match = re.match(
            r"^#+\s*(.+?)\s+(?:"
            r"\d{1,2}\s+(?:January|February|March|April|May|June|July|August|"
            r"September|October|November|December)\s+\d{4}"
            r"|(?:January|February|March|April|May|June|July|August|"
            r"September|October|November|December)\s+\d{4}"
            r")\s*$",
            line.strip(),
            re.I,
        )
        if not date_match:
            continue
        name = normalize_people_heading_name(date_match.group(1))
        if is_skipped_people_heading(name) or not is_person_name(name):
            continue
        people.append(
            {
                "name": name,
                "background": clean_text(line.strip()),
                "photo": None,
                "country": extract_person_country(name, line, region_country),
            }
        )

    for match in re.finditer(r"^#+\s*\.\.\.\s+and\s+(.+?)\s*$", md, re.I | re.M):
        name = normalize_people_heading_name(match.group(1))
        if is_skipped_people_heading(name) or not is_person_name(name):
            continue
        people.append({"name": name, "background": None, "photo": None})

    return people


def parse_people_from_memory_page(record: dict) -> list[dict]:
    return parse_people_from_memory_references(
        record.get("body_markdown") or "",
        record.get("region") or "",
    )


def extract_passed_away_people(pages: list[dict]) -> list[dict]:
    people_by_id: dict[str, dict] = {}
    order: list[str] = []
    for page in pages:
        src = page.get("source_url")
        parsed = parse_people_from_memory_references(
            page.get("body_markdown") or "",
            page.get("region") or "",
        )
        if (page.get("id") or "") in PASSED_AWAY_PAGE_IDS:
            parsed = merge_facilitator_results(parsed, parse_people_from_memory_page(page))
        for person in parsed:
            person_name = canonicalize_facilitator_name(person["name"])
            fid = canonicalize_facilitator_id(person_name)
            entry = {
                **person,
                "name": person_name,
                "person_type": "team-passed-away",
                "sources": [src] if src else [],
            }
            if fid not in people_by_id:
                people_by_id[fid] = entry
                order.append(fid)
            else:
                people_by_id[fid] = merge_facilitator(people_by_id[fid], entry)
    return [people_by_id[fid] for fid in order]


def load_team_source_pages() -> list[dict]:
    pages: list[dict] = []
    for filename in ("people.json", "pages.json"):
        path = DATA_DIR / filename
        if not path.exists():
            continue
        for record in json.loads(path.read_text(encoding="utf-8")):
            if is_team_source_page(record):
                pages.append(record)
    return pages


def parse_people_from_training_roster(md: str) -> list[dict]:
    people: list[dict] = []
    if not md:
        return people

    current_section_country = None
    for line in md.splitlines():
        heading = re.sub(r"^#+\s*", "", line.strip())
        section = country_from_section_heading(heading)
        if section and line.strip().startswith("#"):
            current_section_country = section
            continue

        match = re.search(
            r"\*{2,3}\s*([A-Z][^*\n]+?)\s*(?:\*{2,3})?\s*(?:-|–|$)",
            line,
        )
        if not match:
            continue

        name = normalize_people_heading_name(match.group(1).strip(" -"))
        if is_skipped_people_heading(name):
            continue

        remainder = clean_text(line[match.end() :])
        remainder = re.sub(r"^[-–]\s*", "", remainder)
        remainder = re.sub(r"^email\s+", "", remainder, flags=re.I)
        people.append(
            {
                "name": name,
                "background": normalize_markdown(remainder) if remainder else None,
                "photo": None,
                "country": extract_person_country(name, remainder, current_section_country),
            }
        )
    return people


def parse_people_from_strong_names(md: str) -> list[dict]:
    people: list[dict] = []
    if not md:
        return people

    matches = list(re.finditer(r"^\*\*(.+?)\*\*\s*$", md, flags=re.MULTILINE))
    for idx, match in enumerate(matches):
        name = normalize_people_heading_name(match.group(1))
        if is_skipped_people_heading(name):
            continue

        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(md)
        content = md[start:end].strip()
        content = re.sub(r"^!\[[^\]]*\]\([^)]+\)\s*", "", content)
        content = normalize_markdown(content)
        if content and not content.startswith("©"):
            people.append({"name": name, "background": content, "photo": None})
    return people


def extract_team_people_from_page(record: dict) -> list[dict]:
    md = record.get("body_markdown") or ""
    return merge_facilitator_results(
        parse_people_page(record),
        parse_people_from_training_roster(md),
        parse_people_from_strong_names(md),
    )


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    return text or "unknown"


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def node_to_markdown(node) -> str:
    """Convert a BeautifulSoup node subtree to plain markdown-ish text."""
    if node is None:
        return ""
    if isinstance(node, NavigableString):
        return str(node)
    if not isinstance(node, Tag):
        return ""

    name = node.name.lower()
    if name in ("script", "style", "noscript"):
        return ""

    if name == "br":
        return "\n"

    if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
        level = int(name[1])
        inner = "".join(node_to_markdown(c) for c in node.children).strip()
        return f"\n\n{'#' * level} {inner}\n\n" if inner else ""

    if name == "p":
        inner = "".join(node_to_markdown(c) for c in node.children).strip()
        return f"\n\n{inner}\n\n" if inner else ""

    if name == "li":
        inner = "".join(node_to_markdown(c) for c in node.children).strip()
        return f"\n- {inner}" if inner else ""

    if name in ("ul", "ol"):
        return "".join(node_to_markdown(c) for c in node.children)

    if name == "strong":
        inner = "".join(node_to_markdown(c) for c in node.children).strip()
        return f"**{inner}**" if inner else ""

    if name == "em":
        inner = "".join(node_to_markdown(c) for c in node.children).strip()
        return f"*{inner}*" if inner else ""

    if name == "a":
        href = node.get("href", "")
        inner = "".join(node_to_markdown(c) for c in node.children).strip()
        if inner and href:
            return f"[{inner}]({href})"
        return inner

    if name == "img":
        src = node.get("src", "")
        alt = node.get("alt", "")
        if src:
            return f"![{alt}]({src})"
        return ""

    if name == "hr":
        return "\n\n---\n\n"

    return "".join(node_to_markdown(c) for c in node.children)


def normalize_markdown(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip()


def parse_date_string(text: str) -> str | None:
    """Return ISO date YYYY-MM-DD if possible."""
    text = clean_text(text)
    if not text:
        return None

    # ISO
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    # 12 Sep 2026 / 12th September 2026
    m = re.search(
        r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})\b",
        text,
        re.I,
    )
    if m:
        day, mon, year = m.group(1), m.group(2).lower(), m.group(3)
        month = MONTHS.get(mon[:3]) or MONTHS.get(mon)
        if month:
            return f"{year}-{month:02d}-{int(day):02d}"

    # 04/09/2026
    m = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", text)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return datetime(y, mo, d).strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None


def parse_date_range(text: str) -> tuple[str | None, str | None]:
    text = clean_text(text)
    if not text:
        return None, None

    # 12 Sep - 17 Sep 2026
    m = re.search(
        r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s*[–\-]\s*"
        r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})",
        text,
        re.I,
    )
    if m:
        d1, m1, d2, m2, year = m.groups()
        mo1 = MONTHS.get(m1.lower()[:3]) or MONTHS.get(m1.lower())
        mo2 = MONTHS.get(m2.lower()[:3]) or MONTHS.get(m2.lower())
        if mo1 and mo2:
            return (
                f"{year}-{mo1:02d}-{int(d1):02d}",
                f"{year}-{mo2:02d}-{int(d2):02d}",
            )

    # Saturday 12th – Thursday 17th September 2026
    m = re.search(
        r"(\d{1,2})(?:st|nd|rd|th)?\s*[–\-]\s*"
        r"(?:\w+\s+)?(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})",
        text,
        re.I,
    )
    if m:
        d1, d2, mon, year = m.groups()
        mo = MONTHS.get(mon.lower()[:3]) or MONTHS.get(mon.lower())
        if mo:
            return (
                f"{year}-{mo:02d}-{int(d1):02d}",
                f"{year}-{mo:02d}-{int(d2):02d}",
            )

    # 3rd July 2026 – 8th July 2027 (cross-year)
    m = re.search(
        r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})\s*[–\-]\s*"
        r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})",
        text,
        re.I,
    )
    if m:
        d1, m1, y1, d2, m2, y2 = m.groups()
        mo1 = MONTHS.get(m1.lower()[:3]) or MONTHS.get(m1.lower())
        mo2 = MONTHS.get(m2.lower()[:3]) or MONTHS.get(m2.lower())
        if mo1 and mo2:
            return (
                f"{y1}-{mo1:02d}-{int(d1):02d}",
                f"{y2}-{mo2:02d}-{int(d2):02d}",
            )

    # 13 – 18 octobre 2026
    m = re.search(
        r"(\d{1,2})\s*[–\-]\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})",
        text,
        re.I,
    )
    if m:
        d1, d2, mon, year = m.groups()
        mo = MONTHS.get(mon.lower()[:3]) or MONTHS.get(mon.lower())
        if mo:
            return (
                f"{year}-{mo:02d}-{int(d1):02d}",
                f"{year}-{mo:02d}-{int(d2):02d}",
            )

    # Single date fallback
    single = parse_date_string(text)
    return (single, single) if single else (None, None)


VENUE_NAME_HINTS = (
    "centre",
    "center",
    "college",
    "house",
    "studio",
    "school",
    "hall",
    "theatre",
    "theater",
    "haroen",
    "island",
    "venue",
    "retreat",
    "foundation",
    "enlli",
    "bardsey",
)

VENUE_ALIASES = {
    "peredur centre for the arts": "Peredur Centre",
    "peredur": "Peredur Centre",
}

FACILITATOR_ALIASES = {
    "ali stockford": "Alison Stockford",
    "alison stockford (ali)": "Alison Stockford",
    "alison (ali) stockford": "Alison Stockford",
    "catherine bryden": "Catherine Bryden (Canada / UK)",
    "gisela mosch": "Hanna Mosch",
}

TEAM_PAGE_HINTS = (
    "team",
    "dozent",
    "facilitator-training",
    "facilitators-in-training",
    "il-nostro-gruppo",
    "equipe",
    "zesp",
)

FACILITATOR_SOURCE_PAGE_IDS = frozenset({
    "team",
    "new-team",
    "nax/team-na",
})

PREVIOUS_ASSOCIATE_PAGE_IDS = frozenset({
    "previousassociates",
    "uk/previous-associates",
})

PASSED_AWAY_PAGE_IDS = frozenset({
    "uk/in-memory",
})

PERSON_TYPE_PRIORITY = {
    "facilitator": 4,
    "team-passed-away": 3,
    "team": 1,
}

TEAM_PAGE_EXCLUDES = (
    "approach",
    "herangehensweise",
    "metodo",
    "guideline",
    "uk-clown-facilitator-training",
)


PERSON_ROLE_SUFFIX = re.compile(
    r"\s+(?:Fondatore|Facilitatore|Founder|Director|Coordinator)\b.*$",
    re.I,
)


def strip_person_role_suffix(name: str) -> str:
    return PERSON_ROLE_SUFFIX.sub("", name).strip()


def canonicalize_venue_name(name: str) -> str:
    name = clean_text(name).strip(" ,")
    # Strip trailing postcodes, keep place name
    m = re.match(r"^(.+?)\s+[A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2}$", name)
    if m:
        name = m.group(1).strip()
    if name.isupper() and len(name) > 3:
        name = name.title().replace(" / ", " / ")
    key = name.lower()
    if key in VENUE_ALIASES:
        return VENUE_ALIASES[key]
    if "peredur" in key and "centre" in key:
        return "Peredur Centre"
    if "bardsey" in key or "enlli" in key or "ynys" in key:
        return "Bardsey Island / Ynys Enlli"
    return name


def canonicalize_facilitator_name(name: str) -> str:
    name = clean_text(name.replace("**", ""))
    name = re.sub(r"\s*[–\-]\s*(?:Clowning|Dance|clowning|dance)\s*$", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    # "Alison (Ali) Stockford" -> keep full form; alias map handles Ali variants
    key = name.lower()
    return FACILITATOR_ALIASES.get(key, name)


def normalize_facilitator_heading(name: str) -> str | None:
    name = clean_text(name.replace("**", ""))
    if not name:
        return None
    name = re.sub(
        r"\s*[–\-]\s*(?:Clowning|Movement and Dance Improvisation|Movement|Dance|clowning|dance)\s*$",
        "",
        name,
    )
    name = strip_person_role_suffix(name)
    name = canonicalize_facilitator_name(name)
    return name if is_person_name(name) else None


def extract_leading_facilitator_name(text: str) -> str | None:
    """Extract a facilitator name from a heading line or div opener."""
    text = strip_markdown_noise(text)
    if not text:
        return None

    labeled = re.match(r"^Facilitators?\s*:\s*(.+)$", text, re.I)
    if labeled:
        names = parse_facilitator_name_list(labeled.group(1))
        return names[0] if len(names) == 1 else None

    candidate = normalize_facilitator_heading(text)
    if candidate:
        return candidate

    # "Ali Stockford – Clowning Ali has been..." or "Beth Maiden – Movement and Dance..."
    m = re.match(
        r"^((?:Dr\.|Prof\.)?\s*[A-Z][a-z]+(?:\s+\([^)]+\))?(?:\s+[A-Z]\.)?(?:\s+[A-Z][a-z]+)+)"
        r"\s*[–\-]\s*(?:Clowning|Movement and Dance Improvisation|Movement|Dance)\b",
        text,
    )
    if m:
        return normalize_facilitator_heading(m.group(1))

    # "Andreas L. Maier Andreas has..." or "Ali Stockford Ali has..."
    m = re.match(
        r"^((?:Dr\.|Prof\.)?\s*[A-Z][a-z]+(?:\s+[A-Z]\.)?\s+[A-Z][a-z]+)\s+([A-Z][a-z]+)\s+(has|is)\b",
        text,
    )
    if m and m.group(2) == m.group(1).split()[0]:
        return normalize_facilitator_heading(m.group(1))

    # "Ali Stockford Ali has been facilitating..."
    m = re.match(
        r"^((?:Dr\.|Prof\.)?\s*[A-Z][a-z]+(?:\s+\([^)]+\))?\s+[A-Z][a-z]+)\s+[A-Z][a-z]+\s+(?:has|is)\b",
        text,
    )
    if m:
        return normalize_facilitator_heading(m.group(1))

    # Plain two-word (or Dr + name) prefix before a long bio sentence.
    m = re.match(
        r"^((?:Dr\.|Prof\.)?\s*[A-Z][a-z]+(?:\s+\([^)]+\))?(?:\s+[A-Z]\.)?(?:\s+[A-Z][a-z]+)+)\s+[a-z]",
        text,
    )
    if m and len(text) > len(m.group(1)) + 20:
        return normalize_facilitator_heading(m.group(1))

    return None


def extract_inline_facilitator_bio(el: Tag, name: str) -> str | None:
    """Bio text in the same paragraph as the facilitator name."""
    text = clean_text(el.get_text(" ", strip=True))
    if not text or len(text) <= len(name) + 10:
        return None
    if not text.startswith(name):
        return None
    remainder = text[len(name) :].strip()
    return normalize_markdown(remainder) if remainder else None


def strip_markdown_noise(text: str) -> str:
    text = clean_text(text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    while "[" in text:
        new = re.sub(r"\[[^\]]*\]\([^)]*\)", "", text)
        if new == text:
            break
        text = new
    text = re.sub(r"\*+", "", text)
    text = re.sub(r"^Facilitators?\s*:\s*", "", text, flags=re.I)
    return text.strip(" :")


def parse_facilitator_name_list(text: str) -> list[str]:
    text = strip_markdown_noise(text)
    if not text:
        return []

    names: list[str] = []
    for part in re.split(r"\s+and\s+|,\s*|&\s*", text, flags=re.I):
        part = strip_markdown_noise(part)
        if not part:
            continue
        part = canonicalize_facilitator_name(part)
        if is_person_name(part):
            names.append(part)
    return names


def extract_facilitators_from_markdown(md: str) -> list[str]:
    names: list[str] = []

    # Intro with-lines only (before booking/fee sections).
    head = md.split("---")[0][:1500]
    for m in re.finditer(
        r"(?:^|\n)\*?(?:with|WITH|With|avec|mit)\s+(.+?)(?:\*|\n|$)",
        head,
        re.I,
    ):
        chunk = re.sub(r"\s+\d{1,2}(?:st|nd|rd|th)?\b.*$", "", m.group(1), flags=re.I)
        chunk = re.sub(r"\[.*?\]\(.*?\)", "", chunk)
        names.extend(parse_facilitator_name_list(chunk))

    # Explicit facilitator list on one line, e.g. "Facilitator: Vivian Gladwell and Ali Stockford"
    for m in re.finditer(
        r"(?:^|\n)(?:\*+)?Facilitators?(?:\*+)?:\s*(.+?)(?:\n|$)",
        md,
        re.I,
    ):
        line = strip_markdown_noise(m.group(1))
        if re.search(r"\b(?:in the|workshop in|course in)\b", line, re.I):
            continue
        if " and " in line.lower() or "&" in line or "," in line:
            names.extend(parse_facilitator_name_list(line))

    # ### Name headings within facilitator blocks in markdown.
    fac_section = re.search(
        r"Facilitators?:(.+?)(?:---|\n## \*\*Step 1|\n## \*\*Course fee|\Z)",
        md,
        re.I | re.S,
    )
    if fac_section:
        block = fac_section.group(1)
        for m in re.finditer(r"^###\s+(.+?)\s*$", block, re.I | re.M):
            name = normalize_facilitator_heading(m.group(1))
            if name:
                names.append(name)

    return names


def merge_facilitator_results(*groups: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    order: list[str] = []
    for group in groups:
        for entry in group:
            name = canonicalize_facilitator_name(entry["name"])
            fid = canonicalize_facilitator_id(name)
            normalized = {**entry, "name": name}
            if fid not in merged:
                merged[fid] = normalized
                order.append(fid)
            else:
                merged[fid] = merge_facilitator(merged[fid], normalized)
    return [merged[fid] for fid in order]


def canonicalize_facilitator_id(name: str) -> str:
    return slugify(canonicalize_facilitator_name(name))


def is_valid_venue_name(name: str) -> bool:
    name = clean_text(name)
    if not name or len(name) < 4:
        return False
    lower = name.lower().strip(".")
    if lower in ("uk", "usa", "weekend", "koln", "suisse", "leicester", "hastings", "london"):
        return False
    if re.search(r"\b[A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2}\b", name):
        return False
    if re.search(r"\b(?:\d[\d-]*\s*)?day\s+course\b|\bcourse\s+on\b|\bcourse\s+at\b|\bworkshop\b|\bintroduction\b", lower):
        return False
    if "online course" in lower or "day residential course" in lower or "weekly sessions" in lower:
        return False
    if any(h in lower for h in VENUE_NAME_HINTS):
        return True
    # Single-word place names used as venues (e.g. Dornach)
    if len(name.split()) == 1 and name[0].isupper() and lower not in COUNTRY_ALIASES:
        return True
    # Multi-word proper names with comma address often valid
    return len(name.split()) >= 2 and name[0].isupper()


def split_facilitator_names(name: str) -> list[str]:
    name = clean_text(name.replace("**", ""))
    parts = re.split(r"\s*&\s*|\s+and\s+", name, flags=re.I)
    out = []
    for part in parts:
        part = clean_text(part)
        if is_person_name(part):
            out.append(part)
    return out


def extract_clown_level(title: str) -> str | None:
    t = title.upper()
    patterns = [
        (r"\bFACILITATOR\s+TRAINING\b", "Facilitator Training"),
        (r"\bSOCIAL\s+CLOWNING\b", "Social Clowning"),
        (r"\bMASTERCLASS\b", "Masterclass"),
        (r"\bCLOWN\s*3\b|\bLEVEL\s*3\b|\bCLOWN\s+LEVEL\s*3\b", "Clown 3"),
        (r"\bCLOWN\s*2\b|\bLEVEL\s*2\b|\bCLOWN\s+LEVEL\s*2\b", "Clown 2"),
        (r"\bCLOWN\s*1\b|\bLEVEL\s*1\b|\bCLOWN\s+LEVEL\s*1\b", "Clown 1"),
        (r"\bINTRODUCTION\s+TO\s+CLOWNING\b|\bONE[- ]DAY\s+INTRO\b|\bINTRO\s+TO\s+CLOWNING\b", "Introduction"),
        (r"\bCOURAGE\s+TO\s+BE\b", "Courage to Be"),
        (r"\bPERFORMANCE\b", "Performance"),
        (r"\bCLOWN\s+AND\s+DANCE\b", "Clown and Dance"),
    ]
    for pat, label in patterns:
        if re.search(pat, t):
            return label
    return None


def extract_country(title: str, venue_text: str = "", region: str = "") -> str | None:
    combined = f"{title} {venue_text}".lower()
    # Explicit country at end of title after comma/dash
    tail = re.split(r"[–\-,]", title)[-1].strip().lower()
    if tail in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[tail]
    for key, country in sorted(COUNTRY_ALIASES.items(), key=lambda x: -len(x[0])):
        if re.search(rf"\b{re.escape(key)}\b", combined):
            return country
    region_map = {
        "uk": "United Kingdom",
        "na": "United States",
        "de": "Germany",
        "it": "Italy",
        "pl": "Poland",
        "ie": "Ireland",
    }
    return region_map.get(region)


def extract_money(text: str) -> str | None:
    m = re.search(
        r"([£€$]\s?\d[\d,]*(?:\.\d{2})?(?:\s*(?:GBP|EUR|USD|USD|USD|USD))?[^.\n]*)",
        text,
        re.I,
    )
    if m:
        return clean_text(m.group(1).rstrip(".,;"))
    m = re.search(r"\b(\d{2,4})\s*(GBP|EUR|USD|USD)\b", text, re.I)
    if m:
        sym = {"GBP": "£", "EUR": "€", "USD": "$"}.get(m.group(2).upper(), "")
        return f"{sym}{m.group(1)} {m.group(2).upper()}"
    return None


def extract_group_size(text: str) -> int | None:
    plain = re.sub(r"\*\*", "", text)
    patterns = [
        r"limited to\s+(\d+)\s+participants?",
        r"group is limited to\s+(\d+)",
        r"maximum\s+(?:of\s+)?(\d+)\s+participants?",
        r"max\.?\s+(\d+)\s+participants?",
        r"(\d+)\s+participants?\s+maximum",
    ]
    for pat in patterns:
        m = re.search(pat, plain, re.I)
        if m:
            return int(m.group(1))
    return None


def is_person_name(name: str) -> bool:
    name = clean_text(name)
    if not name:
        return False
    if re.search(r"^\*+$|^#+$", name):
        return False
    lower = name.lower()
    if lower in SKIP_FACILITATOR_HEADINGS:
        return False
    blocklist = (
        "participants",
        "course fee",
        "deposit",
        "step 1",
        "step 2",
        "booking",
        "nose to nose",
        "please click",
        "click here",
        "practical information",
        "fee",
        "tuition",
        "online course",
        "workshop in",
        "accommodation",
        "about ",
        "date and times",
        "venue",
        "italy",
        "germany",
        "france",
        "norway",
        "conference",
        "facilitating",
        "greystoke",
        "emerson",
        "college",
        "village hall",
        "who is this",
        "dance space",
    )
    if any(b in lower for b in blocklist):
        return False
    if re.search(r"\bis the\b", lower):
        return False
    if lower.startswith("the "):
        return False
    if name.endswith(":"):
        return False
    if re.search(r"\d", name):
        return False
    if "." in name and not re.match(r"^(Dr\.|Prof\.|Mr\.|Mrs\.|Ms\.)", name):
        if not re.fullmatch(r"[A-Z][a-z]+(?:\s+[A-Z]\.)?(?:\s+[A-Z][a-z]+)+", name):
            return False
    if name.split()[0][0].islower():
        return False
    if re.search(r"\bclowning\b|\bcourse open\b|\bopen to all\b|\bexpect\b|\bgames\b", lower):
        return False
    words = name.split()
    if len(words) >= 3 and words[0].lower() == words[2].lower():
        return False
    if len(words) < 2 or len(words) > 6:
        return False
    if name.isupper() and len(words) >= 3:
        return False
    if " – " in name or " - " in name:
        # Allow "Catherine Bryden (Canada / UK)" but not "Ali Stockford – Clowning"
        suffix = re.split(r"[–\-]", name, maxsplit=1)[-1].strip().lower()
        if suffix and not re.search(r"\(.*\)|\/", suffix) and len(suffix.split()) > 1:
            return False
    # Require at least one capitalized word typical of names
    if not any(w[0].isupper() for w in words if w):
        return False
    return True


def extract_medium(title: str, text: str) -> str:
    title_l = title.lower()
    if re.search(r"\bonline course\b|\ban online\b|\bonline workshop\b", title_l):
        return "Online"
    # First ~600 chars for workshop language hints
    head = text[:600].lower()
    if re.search(r"\ban online course\b|\bonline course of\b|\bonline ‘insight’ session\b", head):
        return "Online"
    return "In-person"


def extract_language(title: str, text: str, fallback: str = "en") -> str:
    combined = f"{title}\n{text}"
    if re.search(r"workshop in english|taught in english|in english", combined, re.I):
        return "English"
    if re.search(r"workshop in french|taught in french|en français|in french", combined, re.I):
        return "French"
    if re.search(r"workshop in german|taught in german|in german|auf deutsch", combined, re.I):
        return "German"
    if re.search(r"workshop in italian|taught in italian|in italian", combined, re.I):
        return "Italian"
    lang_map = {"en": "English", "de": "German", "it": "Italian", "pl": "Polish", "fr": "French"}
    return lang_map.get(fallback, fallback)


def find_section_nodes(soup: BeautifulSoup, headings: tuple[str, ...]) -> list:
    """Return content nodes following a matching heading until next major heading."""
    nodes = []
    capture = False
    for el in soup.find_all(["h1", "h2", "h3", "h4", "p", "ul", "ol", "hr"]):
        if el.name in ("h1", "h2", "h3", "h4"):
            heading = clean_text(el.get_text(" ", strip=True)).lower()
            heading = re.sub(r"^step \d+[–-]\s*", "", heading)
            if any(h in heading for h in headings):
                capture = True
                continue
            if capture and any(
                kw in heading
                for kw in (
                    "step 1",
                    "step 2",
                    "book",
                    "venue",
                    "date",
                    "more info",
                    "click here",
                )
            ):
                break
            if capture and el.name in ("h1", "h2") and not any(h in heading for h in headings):
                break
        if capture:
            nodes.append(el)
    return nodes


def extract_prerequisites(text: str) -> str | None:
    patterns = [
        r"Prerequisites?(?: for the course are)?[:\s]+(.+?)(?:\n\n|\*\*Facilitator|\*\*COURSE|\*\*FEE|Course fee|##|\Z)",
        r"\*\*PREREQUISITES:\*\*(.+?)(?:\*\*COURSE|\*\*FEE|Would you like|\Z)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I | re.S)
        if m:
            val = normalize_markdown(m.group(1))
            val = re.sub(r"^\*+|\*+$", "", val).strip()
            if val and len(val) > 3:
                return val
    if re.search(r"no prerequisites", text, re.I):
        return "No prerequisites"
    return None


def extract_fee_and_deposit(text: str) -> tuple[str | None, str | None]:
    fee = None
    deposit = None
    fee_patterns = [
        r"\*\*Course fee:?\*\*\s*(.+?)(?:\n|$)",
        r"Course fee:?\s*(.+?)(?:\n|$)",
        r"\*\*Fee(?: \(Tuition only\))?:?\*\*\s*(.+?)(?:\n|$)",
        r"Fee \(Tuition only\):\s*(.+?)(?:\n|Deposit)",
        r"\*\*FEE\*\*:\s*(.+?)(?:\n|$)",
    ]
    for pat in fee_patterns:
        m = re.search(pat, text, re.I)
        if m:
            fee = clean_text(m.group(1))
            break
    dep_patterns = [
        r"\*\*Deposit:?\*\*\s*(.+?)(?:\n|$)",
        r"Deposit[:\s–-]+\s*([£€$]?\s?\d[\d,]*(?:\.\d{2})?\s*(?:GBP|EUR|USD)?)",
        r"Deposit\s*[–-]\s*(\d+\s*(?:GBP|EUR|USD))",
    ]
    for pat in dep_patterns:
        m = re.search(pat, text, re.I)
        if m:
            deposit = clean_text(m.group(1))
            break
    return fee, deposit


def extract_venue_from_course(soup: BeautifulSoup, md: str, title: str = "") -> dict:
    venue = {"name": None, "address": None, "email": None, "phone": None, "website": None}

    # Venue: paragraph followed by address or link
    for el in soup.find_all(["p", "h2", "h3", "h4"]):
        heading = clean_text(el.get_text()).lower().rstrip(":")
        if heading not in ("venue", "venue:"):
            continue
        sib = el.find_next_sibling()
        while sib and isinstance(sib, Tag):
            if sib.name in ("h1", "h2", "h3", "hr"):
                break
            if sib.name == "address":
                link = sib.find("a", href=True)
                text = clean_text(sib.get_text(" ", strip=True))
                if link:
                    venue["name"] = clean_text(link.get_text())
                    venue["website"] = link["href"]
                elif text:
                    venue["name"] = text.strip(".")
                break
            if sib.name == "p":
                link = sib.find("a", href=True)
                text = clean_text(sib.get_text(" ", strip=True))
                if link and not is_person_name(text):
                    venue["name"] = clean_text(link.get_text())
                    venue["website"] = link["href"]
                    break
                if text and is_valid_venue_name(text) and not is_person_name(text):
                    venue["name"] = text
                    break
            sib = sib.find_next_sibling()
        if venue["name"]:
            break

    # h2 "Venue:" followed by h4 with link + address
    venue_heading = None
    for h in soup.find_all(["h2", "h4"]):
        heading = clean_text(h.get_text()).lower()
        if heading in ("venue:", "venue"):
            venue_heading = h
            continue
        if venue_heading is not None and h.name == "h4":
            link = h.find("a", href=True)
            full_text = clean_text(h.get_text(" ", strip=True))
            full_text = re.sub(r"Venue\s*$", "", full_text, flags=re.I).strip(" ,")
            if link:
                venue["name"] = clean_text(link.get_text())
                venue["website"] = link["href"]
                addr = full_text.replace(link.get_text(" ", strip=True), "").strip(" ,")
                venue["address"] = clean_text(addr) or None
            elif full_text:
                parts = full_text.split(",", 1)
                venue["name"] = parts[0]
                venue["address"] = parts[1].strip() if len(parts) > 1 else None
            venue_heading = None
            break

    # Standalone h4 with venue link (no preceding h2)
    if not venue["name"]:
        for h in soup.find_all("h4"):
            link = h.find("a", href=True)
            text = clean_text(h.get_text(" ", strip=True))
            if link and "centre" in text.lower() or (link and "college" in text.lower()):
                venue["name"] = clean_text(link.get_text())
                venue["website"] = link["href"]
                addr = text.replace(link.get_text(" ", strip=True), "").strip(" ,")
                addr = re.sub(r"Venue\s*$", "", addr, flags=re.I).strip(" ,")
                venue["address"] = clean_text(addr) or None
                break

    # Where: / Venue: in markdown (including link on following line)
    for pat in (
        r"Venue:\s*\n+\s*\[([^\]]+)\]\([^)]+\)",
        r"Where:\s*(.+?)(?:\n|$)",
        r"Venue:\s*(.+?)(?:\n|$)",
    ):
        m = re.search(pat, md, re.I)
        if m:
            line = clean_text(m.group(1))
            line = re.sub(r"\*\*", "", line)
            line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
            line = re.sub(r"Venue\s*$", "", line, flags=re.I).strip(" .,")
            if line and not venue["name"]:
                parts = line.split(",", 1)
                candidate = parts[0].strip()
                if is_valid_venue_name(candidate):
                    venue["name"] = candidate
                    venue["address"] = parts[1].strip() if len(parts) > 1 else line
            elif line and not venue["address"]:
                venue["address"] = line

    # Comma-separated title fallback: "… , BRIGHTON, UK"
    if not venue["name"] and title and "," in title:
        parts = [p.strip() for p in title.split(",") if p.strip()]
        country_words = {"uk", "usa", "belgium", "germany", "france", "wales", "ireland", "switzerland"}
        if len(parts) >= 2 and parts[-1].lower() in country_words:
            city = parts[-2]
            if city.lower() in ("brighton", "hastings", "leicester", "london", "greystoke", "dornach"):
                venue["name"] = city.title()
    if not venue["name"] and title:
        title_at = re.search(r"\b(?:at|on)\s+([^,–\-]+?)(?:,\s*(?:Switzerland|Wales|UK|Belgium|Germany|France|Italy))?\s*$", title, re.I)
        if title_at:
            candidate = clean_text(title_at.group(1))
            candidate = re.sub(r"^(?:a\s+\d[\d-]*\s*day\s+course\s+)", "", candidate, flags=re.I)
            if is_valid_venue_name(candidate):
                venue["name"] = candidate

    # Title fallback: "… – Peredur Centre, East Grinstead, UK"
    if not venue["name"] and title:
        parts = [p.strip() for p in re.split(r"[–\-]", title) if p.strip()]
        if len(parts) >= 2:
            country_words = {"uk", "usa", "belgium", "germany", "france", "wales", "ireland", "switzerland"}
            loc = parts[-1]
            if loc.lower() in country_words and len(parts) >= 3:
                loc = parts[-2]
            loc_parts = [x.strip() for x in loc.split(",")]
            if loc_parts:
                if loc_parts[-1].lower() in country_words and len(loc_parts) > 1:
                    loc_parts = loc_parts[:-1]
                if loc_parts:
                    candidate_name = loc_parts[0]
                    candidate_addr = ", ".join(loc_parts[1:]) if len(loc_parts) > 1 else None
                    if is_valid_venue_name(candidate_name):
                        venue["name"] = candidate_name
                        if candidate_addr:
                            venue["address"] = candidate_addr
                    elif len(loc_parts) == 1 and loc_parts[0].lower() in (
                        "brighton",
                        "hastings",
                        "leicester",
                        "london",
                        "greystoke",
                    ):
                        venue["name"] = loc_parts[0].title()

    # Contact details from accommodation block only
    acc_m = re.search(
        r"(?:Accommodation and meals|Step 2 – Accommodation)(.+?)(?:## \*\*Date|## Venue|\*\*Q:|\Z)",
        md,
        re.I | re.S,
    )
    acc_block = acc_m.group(1) if acc_m else ""
    email_m = re.search(r"[\w.+-]+@[\w.-]+\.\w+", acc_block)
    if email_m:
        venue["email"] = email_m.group(0)
    phone_m = re.search(r"\b0\d{2,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}\b", acc_block)
    if phone_m:
        venue["phone"] = clean_text(phone_m.group(0))

    if venue["name"]:
        venue["name"] = canonicalize_venue_name(
            clean_text(re.sub(r"\[.*?\]\(.*?\)", "", venue["name"]))
        )
        venue["name"] = re.sub(r"^#+\s*", "", venue["name"])
        venue["name"] = re.sub(r"^\*+|\*+$", "", venue["name"]).strip()
        if venue["name"].lower() in ("venue", "####") or venue["name"].startswith("<"):
            venue["name"] = None

    return venue


def extract_schedule(soup: BeautifulSoup, md: str) -> str | None:
    nodes = find_section_nodes(soup, ("date and times", "details date & times", "course dates"))
    if nodes:
        return normalize_markdown("".join(node_to_markdown(n) for n in nodes))

    m = re.search(
        r"(?:\*\*Details Date & Times:\*\*|\*\*COURSE DATES\*\*)(.+?)(?:---|\*\*Booking|\*\*Facilitator|## \*\*Step|\Z)",
        md,
        re.I | re.S,
    )
    if m:
        return normalize_markdown(m.group(1))

    # Day-by-day list items
    day_items = re.findall(
        r"^-?\s*(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday).+$",
        md,
        re.I | re.M,
    )
    if day_items:
        lines = re.findall(
            r"^-?\s*((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday).+)$",
            md,
            re.I | re.M,
        )
        return "\n".join(f"- {clean_text(l)}" for l in lines)

    m = re.search(
        r"The course begins.+?Ends.+?(?:\n\n|\Z)",
        md,
        re.I | re.S,
    )
    if m:
        return normalize_markdown(m.group(0))
    return None


def extract_accommodation(soup: BeautifulSoup, md: str) -> str | None:
    nodes = find_section_nodes(
        soup,
        ("accommodation and meals", "step 2 – accommodation and meals", "step 2 - accommodation and meals"),
    )
    if nodes:
        text = normalize_markdown("".join(node_to_markdown(n) for n in nodes))
        if text:
            return text
    m = re.search(
        r"## \*\*Step 2 – Accommodation and meals\*\*(.+?)(?:## \*\*Date|## Venue|\*\*Q:|\Z)",
        md,
        re.I | re.S,
    )
    if m:
        return normalize_markdown(m.group(1))
    return None


DESCRIPTION_STOP_RE = re.compile(
    r"(?:"
    r"\n---\s*\n"
    r"|\n## \*\*(?:Step 1|Book on this course)"
    r"|\n## \[(?:\*\*\*|\*\*)?Click here to book"
    r"|\n(?:\*\*Facilitators?:\*\*|###\s*Facilitators?:?|##\s*Facilitators?:?)"
    r"|\n\*\*(?:Course fee|Fee \(Tuition only\)|Bursaries):"
    r")",
    re.I,
)


def strip_markdown_front_matter(md: str) -> str:
    if md.startswith("---"):
        end = md.find("---", 3)
        if end != -1:
            return md[end + 3 :].lstrip("\n")
    return md


def extract_course_description_from_markdown(md: str) -> str | None:
    """Extract the course description block from scraped Markdown, preserving links."""
    text = strip_markdown_front_matter(md).strip()
    if not text:
        return None

    match = DESCRIPTION_STOP_RE.search(text)
    text = text[: match.start()].strip() if match else text

    if not text or len(text) < 40:
        return None
    return normalize_markdown(text)


def extract_course_description(soup: BeautifulSoup, md: str) -> str | None:
    desc = extract_course_description_from_markdown(md)
    if desc:
        return desc

    content = soup.select_one(".entry-content") or soup
    # Description = content before hr / facilitator / course fee sections
    parts = []
    for child in content.children:
        if not isinstance(child, Tag):
            continue
        text_lower = clean_text(child.get_text(" ", strip=True)).lower()
        if child.name == "hr":
            break
        if child.name in ("h2", "h3", "h4") and re.match(
            r"facilitators?:?\s*$", text_lower.rstrip(":")
        ):
            break
        if any(
            kw in text_lower
            for kw in (
                "course fee",
                "deposit:",
                "step 1",
                "booking this course",
                "facilitator:",
                "facilitators:",
                "prerequisites",
            )
        ):
            break
        if child.name in ("h2",) and any(k in text_lower for k in ("book", "fee", "date", "venue")):
            break
        parts.append(child)
    if parts:
        desc = normalize_markdown("".join(node_to_markdown(p) for p in parts))
        if len(desc) > 40:
            return desc
    return None


def extract_course_facilitators(soup: BeautifulSoup, md: str) -> list[dict]:
    """Extract facilitator name + bio blocks embedded in course pages."""
    section_results: list[dict] = []
    labeled_results: list[dict] = []
    intro_results: list[dict] = []
    content = soup.select_one(".entry-content") or soup
    children = [c for c in content.children if isinstance(c, Tag)]

    for el in children[:20]:
        if el.name != "p":
            continue
        text = clean_text(el.get_text(" ", strip=True))
        labeled = re.match(r"Facilitators?\s*:\s*(.+)$", text, re.I)
        if labeled and (" and " in labeled.group(1).lower() or "," in labeled.group(1) or "&" in labeled.group(1)):
            for name in parse_facilitator_name_list(labeled.group(1)):
                labeled_results.append({"name": name, "background": None, "photo": None})
            continue
        intro = re.match(r"(?:with|WITH|With|avec|mit)\s+(.+)$", text, re.I)
        if intro and (" and " in intro.group(1).lower() or "," in intro.group(1) or "&" in intro.group(1)):
            for name in parse_facilitator_name_list(intro.group(1)):
                intro_results.append({"name": name, "background": None, "photo": None})

    # Find start index at Facilitator(s): section
    start_idx = 0
    for i, el in enumerate(children):
        text = clean_text(el.get_text(" ", strip=True)).lower().rstrip(":")
        if text in ("facilitator", "facilitators") or re.match(
            r"^facilitators?\s*:", clean_text(el.get_text(" ", strip=True)), re.I
        ):
            start_idx = i + 1
            break

    def name_from_element(el: Tag) -> str | None:
        if el.name in ("h2", "h3", "h4"):
            return extract_leading_facilitator_name(el.get_text(" ", strip=True))
        if el.name == "p":
            strong = el.find("strong")
            if strong:
                raw_name = clean_text(re.sub(r"\[.*?\]\(.*?\)", "", strong.get_text(" ", strip=True)))
                raw_name = re.sub(r"!\[.*?\]\(.*?\)", "", raw_name).strip()
                return extract_leading_facilitator_name(raw_name)
            if start_idx > 0:
                text = clean_text(el.get_text(" ", strip=True))
                if text:
                    leading = extract_leading_facilitator_name(text)
                    if leading:
                        return leading
                    if len(text) < 60:
                        return extract_leading_facilitator_name(text)
        if el.name == "div" and start_idx > 0:
            strong = el.find("strong")
            raw = clean_text(strong.get_text(" ", strip=True) if strong else el.get_text(" ", strip=True))
            return extract_leading_facilitator_name(raw)
        return None

    i = start_idx
    while i < len(children):
        el = children[i]
        if el.name in ("h2", "hr") and not (el.name == "h2" and name_from_element(el)):
            if el.name == "h2" and any(
                k in clean_text(el.get_text(" ", strip=True)).lower()
                for k in ("step 1", "book this course", "click here to book", "course fee")
            ):
                break
            if el.name == "hr":
                break
        name_text = name_from_element(el)
        if name_text and (start_idx > 0 or el.name in ("h2", "h3")):
            bio_parts = []
            photo = None
            img = el.find("img", src=True)
            if img:
                photo = img["src"]
            inline_bio = extract_inline_facilitator_bio(el, name_text)
            if inline_bio:
                bio_parts.append(inline_bio)
            j = i + 1
            while j < len(children):
                nxt = children[j]
                if nxt.name == "hr":
                    break
                if nxt.name == "h2" and any(
                    k in clean_text(nxt.get_text(" ", strip=True)).lower()
                    for k in ("step 1", "book this course", "click here to book", "course fee")
                ):
                    break
                next_name = name_from_element(nxt)
                if next_name and j > i and next_name != name_text:
                    break
                nxt_text = clean_text(nxt.get_text(" ", strip=True)).lower()
                if any(k in nxt_text for k in ("course fee", "deposit:", "step 1", "booking", "course open")):
                    break
                if nxt.name in ("p", "div"):
                    bio_parts.append(normalize_markdown(node_to_markdown(nxt)))
                    if not photo:
                        img2 = nxt.find("img", src=True)
                        if img2:
                            photo = img2["src"]
                j += 1
            bio = "\n\n".join(p for p in bio_parts if p).strip()
            section_results.append({"name": name_text, "background": bio or None, "photo": photo})
            i = j
            continue
        if el.name == "h2" and start_idx == 0:
            break
        i += 1

    markdown_names = extract_facilitators_from_markdown(md)
    markdown_results = [{"name": n, "background": None, "photo": None} for n in markdown_names]

    return merge_facilitator_results(
        section_results,
        labeled_results,
        intro_results,
        markdown_results,
    )


def is_skipped_people_heading(name: str) -> bool:
    name = clean_text(name)
    name = re.sub(r"^\.\.\.\s+and\s+", "", name, flags=re.I)
    name = re.sub(r"\s+who died.*$", "", name, flags=re.I).strip()
    lower = name.lower()
    if (
        not name
        or len(name) < 3
        or not is_person_name(name)
        or lower.startswith("israel")
        or lower.startswith("germany")
        or lower.startswith("uk -")
        or lower.startswith("ireland")
        or lower.startswith("france")
        or lower.startswith("taiwan")
        or lower.startswith("where we")
        or lower in ("uk team", "associate", "our approach")
        or lower.startswith("course structure")
        or lower.startswith("length of course")
        or lower.startswith("in london")
        or "in memory" in lower
        or name.startswith("©")
    ):
        return True
    if re.match(r"^[A-Z]{2,}\s*-\s*", name) and " " not in name.split("-", 1)[-1].strip()[:20]:
        return True
    return False


def normalize_people_heading_name(name: str) -> str:
    name = clean_text(name)
    bold = re.search(r"\*\*(.+?)\*\*", name)
    if bold:
        name = bold.group(1)
    name = re.sub(r"^\.\.\.\s+and\s+", "", name, flags=re.I)
    name = re.sub(r"\s+who died.*$", "", name, flags=re.I).strip()
    name = re.sub(r"^\*+|\*+$", "", name).strip()
    leading = extract_leading_facilitator_name(name)
    if leading:
        return leading
    name = strip_person_role_suffix(name)
    return name


def next_person_heading(start: Tag) -> Tag | None:
    for el in start.find_all_next(["h1", "h2", "h3"]):
        if el is start:
            continue
        candidate = normalize_people_heading_name(el.get_text(" ", strip=True))
        if candidate and not is_skipped_people_heading(candidate):
            return el
    return None


def collect_bio_after_heading(heading: Tag) -> str:
    bio_parts: list[str] = []

    for el in heading.find_all_next(["p", "div", "ul", "ol"]):
        owner = None
        for prior in el.find_all_previous(["h1", "h2", "h3"]):
            candidate = normalize_people_heading_name(prior.get_text(" ", strip=True))
            if candidate and not is_skipped_people_heading(candidate):
                owner = prior
                break
        if owner is not heading:
            break

        if el.find(["h1", "h2", "h3"]):
            break

        text = normalize_markdown(node_to_markdown(el))
        if text and not text.startswith("©"):
            bio_parts.append(text)

    # Drop consecutive duplicate paragraphs from overlapping HTML blocks.
    deduped: list[str] = []
    for part in bio_parts:
        if not deduped or deduped[-1] != part:
            deduped.append(part)

    return "\n\n".join(deduped).strip()


def parse_people_from_markdown(md: str, page_region: str = "") -> list[dict]:
    people: list[dict] = []
    if not md:
        return people

    current_section_country = None
    parts = re.split(r"^#\s+(.+)$", md, flags=re.MULTILINE)
    i = 1
    while i < len(parts) - 1:
        name = normalize_people_heading_name(parts[i])
        content = re.split(r"\n#\s+", parts[i + 1], maxsplit=1)[0].strip()
        i += 2
        section = country_from_section_heading(name)
        if section:
            current_section_country = section
        if is_skipped_people_heading(name):
            continue
        content = re.sub(r"^!\[[^\]]*\]\([^)]+\)\s*", "", content)
        content = normalize_markdown(content)
        if content and not content.startswith("©"):
            people.append(
                {
                    "name": name,
                    "background": content,
                    "photo": None,
                    "country": extract_person_country(
                        name, content, current_section_country
                    ),
                }
            )
    return people


def strip_leading_images_from_background(background: str | None, photo: str | None = None) -> str | None:
    if not background:
        return background

    text = background.strip()
    text = re.sub(r"^(?:\[!\[[^\]]*\]\([^)]+\)\]\([^)]+\)\s*)+", "", text)
    text = re.sub(r"^(?:!\[[^\]]*\]\([^)]+\)\s*)+", "", text)
    text = re.sub(r"^(?:<a[^>]*>\s*)?<img[^>]*>\s*(?:</a>\s*)?", "", text, flags=re.I)

    if photo:
        photo_key = slugify(urlparse(photo).path.split("/")[-1].split(".")[0])
        if photo_key:

            def drop_matching_image(match: re.Match[str]) -> str:
                src = match.group(2) or match.group(1)
                if photo_key in slugify(urlparse(src).path):
                    return ""
                return match.group(0)

            text = re.sub(
                r"\[!\[[^\]]*\]\(([^)]+)\)\]\([^)]+\)|!\[[^\]]*\]\(([^)]+)\)",
                drop_matching_image,
                text,
                count=1,
            )

    return text.strip() or None


def parse_people_page(record: dict) -> list[dict]:
    html = record.get("body_html") or ""
    md = record.get("body_markdown") or ""
    page_region = record.get("region") or ""
    soup = BeautifulSoup(html, "lxml")
    images = {img["src"]: img for img in record.get("images") or [] if img.get("src")}
    people_by_id: dict[str, dict] = {}
    order: list[str] = []
    current_section_country = None

    for h in soup.find_all(["h1", "h2", "h3"]):
        name = normalize_people_heading_name(h.get_text(" ", strip=True))
        section = country_from_section_heading(name)
        if section:
            current_section_country = section
        if is_skipped_people_heading(name):
            continue

        photo = None
        img = h.find("img", src=True)
        if img:
            photo = img["src"]
        if not photo:
            for src in images:
                if slugify(name.split()[0]) in slugify(urlparse(src).path):
                    photo = src
                    break

        bio = collect_bio_after_heading(h)
        entry = {
            "name": name,
            "background": bio or None,
            "photo": photo,
            "country": extract_person_country(name, bio, current_section_country),
        }
        fid = canonicalize_facilitator_id(name)
        if fid not in people_by_id:
            people_by_id[fid] = entry
            order.append(fid)
        else:
            people_by_id[fid] = merge_facilitator(people_by_id[fid], entry)

    for person in parse_people_from_markdown(md, page_region):
        fid = canonicalize_facilitator_id(person["name"])
        if fid not in people_by_id:
            people_by_id[fid] = person
            order.append(fid)
        else:
            people_by_id[fid] = merge_facilitator(people_by_id[fid], person)

    return [people_by_id[fid] for fid in order if people_by_id[fid].get("background") or people_by_id[fid].get("photo")]


def score_facilitator_background(name: str, background: str | None) -> int:
    if not background:
        return 0
    lower = background.lower()
    first = name.split()[0].lower() if name.split() else ""
    score = 0
    if lower.startswith(first) or lower.startswith(name.lower()):
        score += 3
    elif first and first in lower[: max(len(name) + 20, 40)]:
        score += 1
    score += min(len(background), 800) // 100
    return score


def merge_facilitator(existing: dict, new: dict) -> dict:
    out = dict(existing)
    for key in ("background", "photo"):
        if key == "photo":
            if not out.get(key) and new.get(key):
                out[key] = new[key]
            continue
        existing_bg = out.get("background")
        new_bg = new.get("background")
        if not existing_bg:
            out[key] = new_bg
        elif not new_bg:
            continue
        else:
            existing_score = score_facilitator_background(out.get("name", ""), existing_bg)
            new_score = score_facilitator_background(out.get("name", ""), new_bg)
            if new_score > existing_score:
                out[key] = new_bg
    if not out.get("country") and new.get("country"):
        out["country"] = new["country"]
    out["sources"] = sorted(set(out.get("sources", []) + new.get("sources", [])))
    return out


def merge_person(existing: dict, new: dict) -> dict:
    out = merge_facilitator(existing, new)
    out["person_type"] = merge_person_type(
        existing.get("person_type"),
        new.get("person_type"),
    )
    out["status"] = merge_status(existing.get("status"), new.get("status"))
    return out


def extract_courses(raw_courses: list[dict], venue_registry: dict, people_registry: dict) -> list[dict]:
    courses = []
    for raw in raw_courses:
        if not (raw.get("meta") or {}).get("detail"):
            continue

        soup = BeautifulSoup(raw.get("body_html") or "", "lxml")
        md = raw.get("body_markdown") or ""
        title = raw.get("title") or ""
        medium = extract_medium(title, md)

        venue_data = extract_venue_from_course(soup, md, title)
        venue_id = None
        if medium != "Online" and venue_data.get("name"):
            if is_valid_venue_name(venue_data["name"]):
                vid = slugify(canonicalize_venue_name(venue_data["name"]))
                canonical_name = canonicalize_venue_name(venue_data["name"])
                if vid not in venue_registry:
                    venue_registry[vid] = {
                        "id": vid,
                        "name": canonical_name,
                        "address": venue_data.get("address"),
                        "email": venue_data.get("email"),
                        "phone": venue_data.get("phone"),
                    }
                else:
                    for k in ("address", "email", "phone"):
                        if venue_data.get(k) and not venue_registry[vid].get(k):
                            venue_registry[vid][k] = venue_data[k]
                venue_id = vid

        start_date, end_date = parse_date_range(
            " ".join((raw.get("meta") or {}).get("dates") or [])
        )
        schedule = extract_schedule(soup, md)
        if schedule:
            s, e = parse_date_range(schedule.split("\n")[0] if schedule else "")
            start_date = start_date or s
            end_date = end_date or e

        facilitator_ids = []
        for fac in extract_course_facilitators(soup, md):
            for fac_name in split_facilitator_names(fac["name"]):
                fac_name = canonicalize_facilitator_name(fac_name)
                entry = {**fac, "name": fac_name}
                fid = canonicalize_facilitator_id(fac_name)
                if fid in people_registry:
                    people_registry[fid] = merge_person(
                        people_registry[fid],
                        {
                            **entry,
                            "person_type": "facilitator",
                            "status": "active",
                            "country": extract_person_country(fac_name, entry.get("background")),
                            "sources": [raw["source_url"]],
                        },
                    )
                else:
                    people_registry[fid] = {
                        "id": fid,
                        "name": fac_name,
                        "person_type": "facilitator",
                        "status": "active",
                        "background": entry.get("background"),
                        "photo": entry.get("photo"),
                        "country": extract_person_country(fac_name, entry.get("background")),
                        "sources": [raw["source_url"]],
                    }
                if fid not in facilitator_ids:
                    facilitator_ids.append(fid)

        fee, deposit = extract_fee_and_deposit(md)
        prereq = extract_prerequisites(md)
        description = extract_course_description(soup, md)
        accommodation = extract_accommodation(soup, md)
        country = extract_country(title, venue_data.get("address") or "", raw.get("region", ""))

        courses.append(
            {
                "id": raw["id"],
                "title": title,
                "source_url": raw.get("source_url"),
                "start_date": start_date,
                "end_date": end_date,
                "location_country": country,
                "venue": venue_id,
                "language": extract_language(title, md, raw.get("language", "en")),
                "facilitators": facilitator_ids,
                "clown_level": extract_clown_level(title),
                "prerequisites": prereq,
                "medium": medium,
                "maximum_group_size": extract_group_size(md),
                "course_fee": fee,
                "course_fee_deposit": deposit,
                "schedule": schedule,
                "course_description": description,
                "accommodation_and_meals": accommodation,
            }
        )
    return courses


def main() -> None:
    raw_courses = json.loads((DATA_DIR / "courses_current.json").read_text(encoding="utf-8"))
    person_pages = load_person_source_pages()

    venue_registry: dict[str, dict] = {}
    people_registry: dict[str, dict] = {}
    previous_associate_ids: set[str] = set()

    # People from team pages (facilitators and regional team members)
    for page in person_pages:
        page_id = page.get("id") or ""
        for person in extract_team_people_from_page(page):
            person_name = canonicalize_facilitator_name(person["name"])
            fid = canonicalize_facilitator_id(person_name)
            src = page.get("source_url")
            entry = {
                "id": fid,
                "name": person_name,
                "person_type": person_type_for_team_page(page),
                "background": person.get("background"),
                "photo": person.get("photo"),
                "country": person.get("country"),
                "sources": [src] if src else [],
            }
            page_status = status_for_team_page(page)
            if page_status:
                entry["status"] = page_status
            if page_id in PREVIOUS_ASSOCIATE_PAGE_IDS:
                previous_associate_ids.add(fid)
            if fid in people_registry:
                people_registry[fid] = merge_person(people_registry[fid], entry)
            else:
                people_registry[fid] = entry

    for person in extract_passed_away_people(person_pages):
        person_name = canonicalize_facilitator_name(person["name"])
        fid = canonicalize_facilitator_id(person_name)
        entry = {
            "id": fid,
            "name": person_name,
            "person_type": "team-passed-away",
            "background": person.get("background"),
            "photo": person.get("photo"),
            "country": person.get("country"),
            "sources": person.get("sources") or [],
        }
        if fid in people_registry:
            people_registry[fid] = merge_person(people_registry[fid], entry)
        else:
            people_registry[fid] = entry

    courses = extract_courses(raw_courses, venue_registry, people_registry)

    current_course_facilitator_ids = {
        fid for course in courses for fid in course.get("facilitators", [])
    }

    course_countries = infer_countries_from_courses(courses, people_registry)
    page_country_hints = build_page_country_hints(person_pages)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Drop invalid venue names
    venues_out = [
        v for v in venue_registry.values()
        if v.get("name") and is_valid_venue_name(v["name"])
    ]
    venues_out = sorted(venues_out, key=lambda v: v["id"])
    people_out = sorted(people_registry.values(), key=lambda p: p["id"])
    people_out = [p for p in people_out if is_person_name(p.get("name", ""))]
    for person in people_out:
        person.setdefault("person_type", "team")
        if person.get("person_type") == "team-previous-associate":
            person["person_type"] = "facilitator"
            person["status"] = "previous-associate"
        person.setdefault("status", "active")
        if (
            person["id"] in previous_associate_ids
            and person["id"] not in current_course_facilitator_ids
            and person.get("person_type") == "facilitator"
        ):
            person["status"] = "previous-associate"
        person["country"] = extract_person_country(person.get("name", ""), person.get("background"))
        if not person["country"]:
            person["country"] = course_countries.get(person["id"])
        if not person["country"]:
            person["country"] = page_country_hints.get(person["id"])
        person["region"] = infer_region_from_country(person.get("country"))
        sources = person.pop("sources", None) or []
        if person.get("person_type") != "facilitator":
            source_urls = sorted({url for url in sources if url})
            if source_urls:
                person["source_urls"] = source_urls
        if person.get("background"):
            person["background"] = strip_leading_images_from_background(
                person["background"], person.get("photo")
            )

    (OUT_DIR / "venues.json").write_text(
        json.dumps(venues_out, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OUT_DIR / "people.json").write_text(
        json.dumps(people_out, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    valid_fac_ids = {p["id"] for p in people_out if p.get("person_type") == "facilitator"}
    valid_venue_ids = {v["id"] for v in venues_out}
    for course in courses:
        course["facilitators"] = [f for f in course.get("facilitators", []) if f in valid_fac_ids]
        if course.get("venue") and course["venue"] not in valid_venue_ids:
            course["venue"] = None

    (OUT_DIR / "courses.json").write_text(
        json.dumps(courses, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {len(courses)} courses -> {OUT_DIR / 'courses.json'}")
    print(f"Wrote {len(venues_out)} venues -> {OUT_DIR / 'venues.json'}")
    print(f"Wrote {len(people_out)} people -> {OUT_DIR / 'people.json'}")


if __name__ == "__main__":
    main()
