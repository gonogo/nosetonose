#!/usr/bin/env python3
"""Download nosetonose.info images referenced in content and rewrite URLs to /media/."""

from __future__ import annotations

import re
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "static" / "media"

IMAGE_URL = re.compile(
    r"https?://(?:www\.)?nosetonose\.info[^\s\"')\]>]*?\.(?:jpg|jpeg|png|gif|webp|svg)",
    re.IGNORECASE,
)

USER_AGENT = "nosetonose-sveltia-mirror/1.0"


def url_path(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.lstrip("/")
    if not path:
        raise ValueError(f"No path in URL: {url}")
    return path


def local_public_path(url: str) -> str:
    return f"/media/{url_path(url)}"


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        dest.write_bytes(resp.read())


def main() -> None:
    text_files: list[Path] = []
    urls: set[str] = set()
    for path in ROOT.rglob("*"):
        if path.suffix not in {".json", ".md", ".svelte", ".ts", ".css", ".html"}:
            continue
        if "node_modules" in path.parts or ".svelte-kit" in path.parts:
            continue
        text_files.append(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        urls.update(IMAGE_URL.findall(text))

    # Normalize to canonical download URL (https + www)
    canonical: dict[str, str] = {}
    for url in urls:
        path = url_path(url)
        canon = f"https://www.nosetonose.info/{path}"
        canonical[url] = canon

    unique_canon = sorted(set(canonical.values()))
    print(f"Downloading {len(unique_canon)} images...")
    failed: list[tuple[str, str]] = []
    for canon in unique_canon:
        dest = MEDIA / url_path(canon)
        try:
            download(canon, dest)
        except urllib.error.HTTPError as exc:
            # Some assets omit www or use http only
            alt = canon.replace("https://www.", "https://")
            try:
                download(alt, dest)
            except Exception as exc2:
                failed.append((canon, str(exc2)))
        except Exception as exc:
            failed.append((canon, str(exc)))

    if failed:
        print("Failed downloads:")
        for url, err in failed:
            print(f"  {url}: {err}")

    # Build replacement map: every matched URL variant -> local /media/ path
    replacements: dict[str, str] = {}
    for url in urls:
        replacements[url] = local_public_path(url)

    changed_files = 0
    for path in text_files:
        original = path.read_text(encoding="utf-8", errors="replace")
        updated = original
        for old, new in sorted(replacements.items(), key=lambda item: -len(item[0])):
            updated = updated.replace(old, new)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed_files += 1

    print(f"Updated {changed_files} files.")
    print(f"Images stored under {MEDIA.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
