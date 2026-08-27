from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse, unquote

import scrapy
from bs4 import BeautifulSoup

from ntn_scraper.cleaners import (
    WP_REGIONS,
    classify_legacy_url,
    detect_language,
    detect_region,
    extract_legacy_content,
    extract_title,
    html_to_markdown,
    make_id,
)
from ntn_scraper.items import ContentItem


class LegacySpider(scrapy.Spider):
    name = "legacy"
    allowed_domains = ["nosetonose.info", "www.nosetonose.info"]

    start_urls = [
        "https://www.nosetonose.info/",
        "https://www.nosetonose.info/index.htm",
        "https://www.nosetonose.info/articles.htm",
        "https://www.nosetonose.info/thoughts.htm",
        "https://www.nosetonose.info/new%20team.htm",
        "https://www.nosetonose.info/approach.htm",
        "https://www.nosetonose.info/booking.htm",
        "https://www.nosetonose.info/contact.htm",
        "https://www.nosetonose.info/briefhistory.htm",
        "https://www.nosetonose.info/coursedates.htm",
        "https://www.nosetonose.info/courseguideline.htm",
        "https://www.nosetonose.info/movie.htm",
        "https://www.nosetonose.info/social%20clowning.htm",
        "https://www.nosetonose.info/two-year%20training%20programme.htm",
        "https://www.nosetonose.info/previousassociates.htm",
        "https://www.nosetonose.info/facilitators%20in%20training.htm",
        "https://www.nosetonose.info/courses/new%20initiatives.htm",
        "https://www.nosetonose.info/nax/index.htm",
        "https://www.nosetonose.info/nax/thoughts%20na.htm",
        "https://www.nosetonose.info/nax/team%20na.htm",
        "https://www.nosetonose.info/nax/approach%20na.htm",
        "https://www.nosetonose.info/itx/index.htm",
        "https://www.nosetonose.info/itx/articoli.htm",
    ]

    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.9",
        }
    }

    def parse(self, response):
        include_archive = self.settings.getbool("INCLUDE_COURSE_ARCHIVE")
        content_type = classify_legacy_url(response.url)

        if content_type == "course_archive" and not include_archive:
            # Still follow links out of archive index pages if any were seeded
            yield from self._follow_links(response)
            return

        if content_type is None:
            yield from self._follow_links(response)
            return

        # Prefer latin-1 for legacy Dreamweaver pages
        try:
            html = response.body.decode("latin-1")
        except Exception:
            html = response.text

        soup = BeautifulSoup(html, "lxml")
        title = extract_title(soup)
        body_html, images = extract_legacy_content(html, response.url)
        body_md = html_to_markdown(body_html)

        # Map type names to schema
        type_name = {
            "article": "article",
            "thought": "thought",
            "people": "people",
            "page": "page",
            "course_archive": "course_archive",
        }[content_type]

        item = ContentItem(
            id=make_id(response.url),
            type=type_name,
            source_url=response.url,
            title=title,
            region=detect_region(response.url),
            language=detect_language(response.url, html),
            body_html=body_html,
            body_markdown=body_md,
            images=images,
            scraped_at=datetime.now(timezone.utc).isoformat(),
            meta={"encoding": "latin-1"},
        )
        yield item
        yield from self._follow_links(response)

    def _follow_links(self, response):
        include_archive = self.settings.getbool("INCLUDE_COURSE_ARCHIVE")
        for href in response.css("a::attr(href)").getall():
            href = (href or "").strip()
            if not href or href.startswith(("mailto:", "javascript:", "#")):
                continue
            absolute = urljoin(response.url, href).split("#")[0]
            parsed = urlparse(absolute)
            if parsed.netloc not in ("www.nosetonose.info", "nosetonose.info"):
                continue

            path = unquote(parsed.path).lower()
            parts = [p for p in path.split("/") if p]
            if parts and parts[0] in WP_REGIONS:
                continue

            content_type = classify_legacy_url(absolute)
            if content_type is None:
                continue
            if content_type == "course_archive" and not include_archive:
                continue

            yield response.follow(absolute, callback=self.parse)
