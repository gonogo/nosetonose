from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import scrapy
from bs4 import BeautifulSoup

from ntn_scraper.cleaners import html_to_markdown, make_id, strip_wp_title
from ntn_scraper.items import ContentItem

# Public course listing / calendar pages per region
COURSE_LISTING_URLS = {
    "uk": [
        "https://www.nosetonose.info/uk/courses",
        "https://www.nosetonose.info/uk/course-dates",
    ],
    "na": [
        "https://www.nosetonose.info/na/",
        "https://www.nosetonose.info/na/courses",
        "https://www.nosetonose.info/na/course-dates",
    ],
    "de": [
        "https://www.nosetonose.info/de/",
        "https://www.nosetonose.info/de/kurse",
        "https://www.nosetonose.info/de/courses",
    ],
    "it": [
        "https://www.nosetonose.info/it/",
        "https://www.nosetonose.info/it/corsi",
        "https://www.nosetonose.info/it/courses",
    ],
    "pl": [
        "https://www.nosetonose.info/pl/",
        "https://www.nosetonose.info/pl/courses",
    ],
}


class CoursesSpider(scrapy.Spider):
    """Parse public WP course listing HTML (Events Manager REST is 401)."""

    name = "courses"
    allowed_domains = ["nosetonose.info", "www.nosetonose.info"]
    handle_httpstatus_list = [404]

    async def start(self):
        for region, urls in COURSE_LISTING_URLS.items():
            for url in urls:
                yield scrapy.Request(
                    url,
                    callback=self.parse_listing,
                    cb_kwargs={"region": region},
                    errback=self.errback,
                    dont_filter=True,
                )

    def errback(self, failure):
        self.logger.warning("Course listing failed: %s", failure.request.url)

    def parse_listing(self, response, region):
        if response.status >= 400:
            self.logger.info("Skip %s (HTTP %s)", response.url, response.status)
            return

        soup = BeautifulSoup(response.text, "lxml")
        seen: set[str] = set()

        # Events Manager list links are the reliable signal
        anchors = []
        anchors.extend(soup.select(".em-events-list a[href], .em-list a[href], .em-view-container a[href]"))
        anchors.extend(soup.select(".entry-content a[href], article a[href], main a[href]"))
        # Deduplicate while preserving order
        ordered = []
        for a in anchors:
            href = a.get("href") or ""
            key = (href, a.get_text(" ", strip=True))
            if key not in seen:
                seen.add(key)
                ordered.append(a)
        seen_urls: set[str] = set()

        for link_el in ordered:
            href = urljoin(response.url, link_el["href"]).split("#")[0]
            if href in seen_urls:
                continue
            if not self._looks_like_course_url(href, region):
                continue
            seen_urls.add(href)

            title = strip_wp_title(link_el.get_text(" ", strip=True))
            if not title or len(title) < 3:
                continue

            dates = self._dates_after_link(link_el)
            summary_html = f"<p><a href=\"{href}\">{title}</a>"
            if dates:
                summary_html += f" — {dates[0]}"
            summary_html += "</p>"

            yield ContentItem(
                id=make_id(href),
                type="course",
                source_url=href,
                title=title,
                region=region,
                language={"de": "de", "it": "it", "pl": "pl"}.get(region, "en"),
                body_html=summary_html,
                body_markdown=html_to_markdown(summary_html),
                images=[],
                scraped_at=datetime.now(timezone.utc).isoformat(),
                meta={
                    "listing_url": response.url,
                    "dates": dates,
                },
            )

            yield response.follow(
                href,
                callback=self.parse_detail,
                cb_kwargs={"region": region, "title": title, "dates": dates},
            )

    def parse_detail(self, response, region, title, dates):
        if response.status >= 400:
            return

        soup = BeautifulSoup(response.text, "lxml")
        content = (
            soup.select_one(".entry-content")
            or soup.select_one(".em-event-content")
            or soup.select_one("article")
            or soup.select_one("main")
        )
        if not content:
            return

        for sel in ("script", "style", "noscript", "nav", "header", "footer"):
            for node in content.select(sel):
                node.decompose()

        body_html = str(content)
        page_title = title
        h1 = soup.find("h1")
        h1_text = strip_wp_title(h1.get_text(" ", strip=True)) if h1 else ""
        bad_titles = {"menu", "home", "navigation", "search", ""}
        if h1_text and h1_text.lower() not in bad_titles and len(h1_text) > 3:
            # Prefer a real event heading over nav chrome
            if title.lower() in bad_titles or len(h1_text) >= len(title):
                page_title = h1_text
        elif soup.title:
            t = strip_wp_title(soup.title.get_text(" ", strip=True))
            # Strip trailing site name
            t = re.sub(r"\s*[|\-–]\s*Nose to Nose.*$", "", t, flags=re.I).strip()
            if t and t.lower() not in bad_titles:
                page_title = t or title

        # Prefer dates already captured from the listing row; enrich from detail
        # content only when listing had none.
        detail_dates = list(dates or [])
        if not detail_dates:
            detail_dates = self._extract_dates(
                (content.get_text(" ", strip=True) or "")[:1200]
            )

        images = []
        for img in content.find_all("img", src=True):
            images.append(
                {
                    "src": urljoin(response.url, img["src"]),
                    "alt": img.get("alt", "").strip(),
                }
            )

        yield ContentItem(
            id=make_id(response.url),
            type="course",
            source_url=response.url,
            title=page_title,
            region=region,
            language={"de": "de", "it": "it", "pl": "pl"}.get(region, "en"),
            body_html=body_html,
            body_markdown=html_to_markdown(body_html),
            images=images,
            scraped_at=datetime.now(timezone.utc).isoformat(),
            meta={"dates": detail_dates, "detail": True},
        )

    @staticmethod
    def _looks_like_course_url(url: str, region: str) -> bool:
        parsed = urlparse(url)
        if parsed.netloc not in ("www.nosetonose.info", "nosetonose.info"):
            return False
        path = parsed.path.lower()
        if f"/{region}/" not in path and not path.startswith(f"/{region}"):
            return False
        skip = (
            "/wp-json",
            "/wp-admin",
            "/wp-content",
            "/feed",
            "/tag/",
            "/category/",
            "/author/",
            "/xmlrpc",
        )
        if any(s in path for s in skip):
            return False
        # Listing / chrome pages
        listing_tails = (
            f"/{region}",
            f"/{region}/",
            f"/{region}/courses",
            f"/{region}/course-dates",
            f"/{region}/kurse",
            f"/{region}/corsi",
        )
        if path.rstrip("/") in {t.rstrip("/") for t in listing_tails}:
            return False
        # Prefer Events Manager event permalinks and known course pages
        if "/events/" in path:
            return True
        # Other WP pages that look course-like
        keywords = ("clown", "course", "workshop", "intro", "masterclass", "training")
        return any(k in path for k in keywords)

    @classmethod
    def _dates_after_link(cls, link_el) -> list[str]:
        """Grab date text that follows an event link until the next link."""
        chunks: list[str] = []
        for sib in link_el.next_siblings:
            name = getattr(sib, "name", None)
            if name == "a":
                break
            if name is not None and getattr(sib, "find", None):
                if sib.find("a"):
                    break
                chunks.append(sib.get_text(" ", strip=True))
            else:
                text = str(sib).strip()
                if text:
                    chunks.append(text)
            if len(" ".join(chunks)) > 120:
                break
        return cls._extract_dates(" ".join(chunks))

    @staticmethod
    def _extract_dates(text: str) -> list[str]:
        if not text:
            return []
        patterns = [
            r"\b\d{1,2}\s+[A-Za-z]{3,9}\s*[–\-]\s*\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b",
            r"\b\d{1,2}[–\-]\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b",
            r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b",
            r"\b[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}\b",
            r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
            r"\b\d{4}-\d{2}-\d{2}\b",
        ]
        found = []
        for pat in patterns:
            found.extend(re.findall(pat, text))
        out = []
        seen = set()
        for f in found:
            if f in seen:
                continue
            # Drop single dates already covered by a range match
            if any(f != other and f in other for other in found):
                continue
            seen.add(f)
            out.append(f)
        return out[:3]
