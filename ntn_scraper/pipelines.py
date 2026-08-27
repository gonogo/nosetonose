from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from itemadapter import ItemAdapter

logger = logging.getLogger(__name__)


class JsonByTypePipeline:
    """Merge items into data/{type}.json and write bodies/{id}.md."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.root: Path | None = None
        self.bodies_dir: Path | None = None
        self.buckets: dict[str, dict[str, dict]] = {}

    @classmethod
    def from_crawler(cls, crawler):
        pipe = cls(data_dir=crawler.settings.get("DATA_DIR", "data"))
        pipe.crawler = crawler
        return pipe

    def open_spider(self, spider=None):
        self.root = Path(self.data_dir)
        self.bodies_dir = self.root / "bodies"
        self.root.mkdir(parents=True, exist_ok=True)
        self.bodies_dir.mkdir(parents=True, exist_ok=True)
        self.buckets = {}

        for path in self.root.glob("*.json"):
            if path.name.startswith("_"):
                continue
            try:
                records = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if not isinstance(records, list):
                continue
            key = path.stem
            # Normalize plural filenames back to type keys
            type_key = {
                "pages": "page",
                "people": "people",
                "articles": "article",
                "thoughts": "thought",
                "testimonials": "testimonial",
                "course_archive": "course_archive",
                "courses_current": "course",
            }.get(key, key)
            self.buckets.setdefault(type_key, {})
            for rec in records:
                rid = rec.get("id")
                if rid:
                    self.buckets[type_key][rid] = rec

    def process_item(self, item, spider=None):
        adapter = ItemAdapter(item)
        item_type = adapter.get("type")
        item_id = adapter.get("id")
        if not item_type or not item_id:
            logger.warning("Dropping item without type/id: %s", adapter.asdict())
            return item

        record = {k: v for k, v in adapter.asdict().items() if v is not None}
        self.buckets.setdefault(item_type, {})[item_id] = record

        body_md = adapter.get("body_markdown") or ""
        if body_md and self.bodies_dir is not None:
            safe = re.sub(r"[^\w\-./]+", "-", item_id).strip("-")
            out = self.bodies_dir / f"{safe}.md"
            out.parent.mkdir(parents=True, exist_ok=True)
            front = (
                f"---\nid: {item_id}\ntype: {item_type}\n"
                f"title: {json.dumps(adapter.get('title') or '')}\n"
                f"source_url: {adapter.get('source_url')}\n---\n\n"
            )
            out.write_text(front + body_md + "\n", encoding="utf-8")

        return item

    def close_spider(self, spider=None):
        if self.root is None:
            return
        for item_type, by_id in sorted(self.buckets.items()):
            filename = {
                "page": "pages.json",
                "people": "people.json",
                "article": "articles.json",
                "thought": "thoughts.json",
                "testimonial": "testimonial.json",
                "course_archive": "course_archive.json",
                "course": "courses_current.json",
            }.get(item_type, f"{item_type}.json")
            # Prefer plural testimonials name from plan
            if item_type == "testimonial":
                filename = "testimonials.json"

            records = sorted(by_id.values(), key=lambda r: r.get("id", ""))
            path = self.root / filename
            path.write_text(
                json.dumps(records, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            logger.info("Wrote %s (%d records)", path, len(records))
