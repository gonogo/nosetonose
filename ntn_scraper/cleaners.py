"""HTML cleaning helpers for legacy Dreamweaver and WordPress content."""

from __future__ import annotations

import hashlib
import re
from html import unescape
from urllib.parse import urljoin, urlparse, unquote

from bs4 import BeautifulSoup, Comment, NavigableString
from markdownify import markdownify as md

WP_REGIONS = frozenset({"uk", "na", "de", "it", "pl", "ie"})
ARCHIVE_PATH_MARKERS = (
    "/courses/",
    "/previouscourses/",
    "/nax/courses/",
    "/fooleffect/",
)

NAV_SELECTORS = [
    ".buttonscontainer",
    ".buttons",
    ".navtd",
    "#navtop",
    "script",
    "style",
    "noscript",
]


def make_id(url: str, prefix: str | None = None) -> str:
    parsed = urlparse(url)
    path = unquote(parsed.path).strip("/")
    if not path or path.endswith("/"):
        path = (path.rstrip("/") + "/index").strip("/")
    path = re.sub(r"\.(htm|html)$", "", path, flags=re.I)
    path = re.sub(r"[^\w\-./]+", "-", path, flags=re.U)
    path = re.sub(r"-{2,}", "-", path).strip("-./")
    if prefix:
        path = f"{prefix}/{path}" if path else prefix
    return path or hashlib.sha1(url.encode()).hexdigest()[:12]


def is_wp_path(path: str) -> bool:
    parts = [p for p in unquote(path).lower().split("/") if p]
    if not parts:
        return False
    return parts[0] in WP_REGIONS and not parts[0].endswith("x")


def classify_legacy_url(url: str) -> str | None:
    """Return content type, or None to skip. Includes course_archive for P2."""
    parsed = urlparse(url)
    if parsed.netloc and parsed.netloc not in (
        "www.nosetonose.info",
        "nosetonose.info",
    ):
        return None

    path = unquote(parsed.path)
    path_l = path.lower()

    if is_wp_path(path_l):
        return None

    if not (path_l.endswith(".htm") or path_l.endswith(".html") or path_l in ("", "/")):
        return None

    if any(marker in path_l for marker in ARCHIVE_PATH_MARKERS):
        return "course_archive"

    if "/articles/" in path_l or path_l.rstrip("/").endswith("articles.htm"):
        return "article"
    if "articles na.htm" in path_l:
        return "article"
    if "thought" in path_l:
        return "thought"
    if any(
        key in path_l
        for key in ("team", "facilitator", "previousassociates", "jackiemoore")
    ):
        return "people"
    return "page"


def detect_region(url: str) -> str:
    path = unquote(urlparse(url).path).lower()
    parts = [p for p in path.split("/") if p]
    if not parts:
        return "international"
    region_map = {
        "uk": "uk",
        "na": "na",
        "nax": "na",
        "de": "de",
        "it": "it",
        "itx": "it",
        "pl": "pl",
        "ie": "ie",
    }
    return region_map.get(parts[0], "international")


def detect_language(url: str, html: str = "") -> str:
    region = detect_region(url)
    if region in ("de", "it", "pl"):
        return region
    m = re.search(r'<html[^>]+lang=["\']([a-z]{2})', html, re.I)
    if m:
        return m.group(1).lower()
    return "en"


def extract_title(soup: BeautifulSoup) -> str:
    if soup.title and soup.title.get_text(strip=True):
        title = soup.title.get_text(" ", strip=True)
        title = re.sub(r"\s*[-–|]\s*Nose to Nose.*$", "", title, flags=re.I)
        title = re.sub(r"\s+", " ", title).strip()
        if title:
            return unescape(title)
    h1 = soup.find("h1")
    if h1:
        return unescape(h1.get_text(" ", strip=True))
    return ""


def _remove_dreamweaver_noise(soup: BeautifulSoup) -> None:
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()
    for sel in NAV_SELECTORS:
        for node in soup.select(sel):
            node.decompose()
    for img in soup.find_all("img", src=True):
        src = img["src"].lower()
        if any(
            x in src
            for x in ("top.gif", "ntn.jpg", "nav-top.gif", "/images/top")
        ):
            img.decompose()


def extract_legacy_content(html: str, base_url: str) -> tuple[str, list[dict]]:
    soup = BeautifulSoup(html, "lxml")
    _remove_dreamweaver_noise(soup)

    content = soup.select_one("td.contenttd") or soup.select_one(".contenttd")
    if not content:
        content = soup.find("body") or soup

    images = _collect_images(content, base_url)
    _absolutize_links(content, base_url)
    body_html = _inner_html(content)
    body_html = _normalize_html(body_html)
    return body_html, images


def extract_wp_content(html_fragment: str, base_url: str) -> tuple[str, list[dict]]:
    soup = BeautifulSoup(html_fragment or "", "lxml")
    content = soup.find("body") or soup
    for sel in ("script", "style", "noscript"):
        for node in content.select(sel):
            node.decompose()
    images = _collect_images(content, base_url)
    _absolutize_links(content, base_url)
    body_html = _inner_html(content)
    body_html = _normalize_html(body_html)
    return body_html, images


def html_to_markdown(body_html: str) -> str:
    if not body_html.strip():
        return ""
    text = md(
        body_html,
        heading_style="ATX",
        strip=["script", "style"],
        bullets="-",
    )
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _collect_images(root, base_url: str) -> list[dict]:
    images = []
    seen = set()
    for img in root.find_all("img", src=True):
        src = urljoin(base_url, img["src"].strip())
        if src in seen:
            continue
        seen.add(src)
        images.append({"src": src, "alt": img.get("alt", "").strip()})
    return images


def _absolutize_links(root, base_url: str) -> None:
    for tag in root.find_all("a", href=True):
        tag["href"] = urljoin(base_url, tag["href"])
    for tag in root.find_all("img", src=True):
        tag["src"] = urljoin(base_url, tag["src"])


def _inner_html(node) -> str:
    if node is None:
        return ""
    parts = []
    for child in node.children:
        if isinstance(child, NavigableString):
            text = str(child)
            if text.strip():
                parts.append(text)
        else:
            parts.append(str(child))
    return "".join(parts)


def _normalize_html(html: str) -> str:
    html = unescape(html)
    html = re.sub(r">\s+<", "><", html)
    html = re.sub(r"[ \t]+", " ", html)
    for tag in ("p", "h1", "h2", "h3", "h4", "li", "tr", "div", "hr", "ul", "ol"):
        html = re.sub(rf"</{tag}>", f"</{tag}>\n", html, flags=re.I)
        html = re.sub(rf"<{tag}([\s>])", rf"\n<{tag}\1", html, flags=re.I)
    return html.strip()


def strip_wp_title(title: str) -> str:
    return unescape(re.sub(r"\s+", " ", title or "")).strip()
