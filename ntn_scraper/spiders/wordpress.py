from __future__ import annotations

from datetime import datetime, timezone

import scrapy

from ntn_scraper.cleaners import (
    detect_language,
    extract_wp_content,
    html_to_markdown,
    make_id,
    strip_wp_title,
)
from ntn_scraper.items import ContentItem

REGIONS = ("uk", "na", "de", "it", "pl", "ie")


class WordpressSpider(scrapy.Spider):
    """Export WordPress pages + posts via the public REST API."""

    name = "wordpress"
    allowed_domains = ["nosetonose.info", "www.nosetonose.info"]

    async def start(self):
        for region in REGIONS:
            base = f"https://www.nosetonose.info/{region}/wp-json/wp/v2"
            for collection, item_type in (
                ("pages", "page"),
                ("posts", "testimonial"),
            ):
                url = f"{base}/{collection}?per_page=100&page=1"
                yield scrapy.Request(
                    url,
                    callback=self.parse_collection,
                    cb_kwargs={
                        "region": region,
                        "item_type": item_type,
                        "collection": collection,
                        "page": 1,
                    },
                    errback=self.errback_region,
                    dont_filter=True,
                )

    def errback_region(self, failure):
        self.logger.warning("WP request failed: %s", failure.request.url)

    def parse_collection(self, response, region, item_type, collection, page):
        if response.status >= 400:
            self.logger.info(
                "Skipping %s/%s (HTTP %s)", region, collection, response.status
            )
            return

        try:
            data = response.json()
        except Exception:
            self.logger.warning("Non-JSON response from %s", response.url)
            return

        if not isinstance(data, list):
            self.logger.warning("Unexpected payload from %s: %s", response.url, data)
            return

        for entry in data:
            item = self._item_from_entry(entry, region, item_type)
            if item is not None:
                yield item

        total_pages = int(response.headers.get("X-WP-TotalPages", b"1") or 1)
        if page < total_pages:
            next_page = page + 1
            base = f"https://www.nosetonose.info/{region}/wp-json/wp/v2"
            url = f"{base}/{collection}?per_page=100&page={next_page}"
            yield scrapy.Request(
                url,
                callback=self.parse_collection,
                cb_kwargs={
                    "region": region,
                    "item_type": item_type,
                    "collection": collection,
                    "page": next_page,
                },
                dont_filter=True,
            )

    def _item_from_entry(self, entry: dict, region: str, item_type: str) -> ContentItem | None:
        link = entry.get("link") or ""
        title = strip_wp_title((entry.get("title") or {}).get("rendered", ""))
        content_html = (entry.get("content") or {}).get("rendered", "")
        body_html, images = extract_wp_content(
            content_html, link or f"https://www.nosetonose.info/{region}/"
        )
        slug = entry.get("slug") or ""
        date = entry.get("date") or entry.get("modified") or ""

        skip_slugs = {"test", "ball1", "hello-world"}
        if slug in skip_slugs:
            return None
        if title.lower() in {"hello world!", "hello world"}:
            return None
        if len(body_html.strip()) < 40:
            return None

        resolved_type = item_type
        if item_type == "testimonial" and region != "uk":
            # Non-UK posts are often misc pages, not testimonials
            if not any(x in title for x in (" – ", " - ", " from ", ",", "’", "'")):
                resolved_type = "page"

        meta = {
            "wp_id": entry.get("id"),
            "slug": slug,
            "status": entry.get("status"),
            "wp_type": entry.get("type"),
        }
        item_id = make_id(link) if link else f"{region}/{item_type}/{entry.get('id')}"

        return ContentItem(
            id=item_id,
            type=resolved_type,
            source_url=link,
            title=title,
            region=region,
            language=detect_language(link or f"https://www.nosetonose.info/{region}/"),
            body_html=body_html,
            body_markdown=html_to_markdown(body_html),
            images=images,
            scraped_at=datetime.now(timezone.utc).isoformat(),
            slug=slug,
            date=date,
            meta=meta,
        )
