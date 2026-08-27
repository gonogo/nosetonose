import scrapy


class ContentItem(scrapy.Item):
    id = scrapy.Field()
    type = scrapy.Field()
    source_url = scrapy.Field()
    title = scrapy.Field()
    region = scrapy.Field()
    language = scrapy.Field()
    body_html = scrapy.Field()
    body_markdown = scrapy.Field()
    images = scrapy.Field()
    scraped_at = scrapy.Field()
    # Optional extras
    slug = scrapy.Field()
    date = scrapy.Field()
    meta = scrapy.Field()
