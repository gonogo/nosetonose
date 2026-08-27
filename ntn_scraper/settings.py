# Scrapy settings for ntn_scraper project

BOT_NAME = "ntn_scraper"

SPIDER_MODULES = ["ntn_scraper.spiders"]
NEWSPIDER_MODULE = "ntn_scraper.spiders"

ADDONS = {}

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36"
)

ROBOTSTXT_OBEY = False  # robots.txt is empty/unhelpful; stay polite via delay

CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 0.75

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
}

ITEM_PIPELINES = {
    "ntn_scraper.pipelines.JsonByTypePipeline": 300,
}

DATA_DIR = "data"

# Include P2 historical course pages when True (legacy spider)
INCLUDE_COURSE_ARCHIVE = False

TELNETCONSOLE_ENABLED = False
FEED_EXPORT_ENCODING = "utf-8"
LOG_LEVEL = "INFO"
