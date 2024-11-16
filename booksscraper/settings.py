# Scrapy settings for booksscraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "booksscraper"

SPIDER_MODULES = ["booksscraper.spiders"]
NEWSPIDER_MODULE = "booksscraper.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "booksscraper (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "booksscraper.middlewares.BooksscraperSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "booksscraper.middlewares.BooksscraperDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   "booksscraper.pipelines.SQLitePipeline": 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# User agent to make the scraper appear as a regular browser
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# This configuration is intended for presenting the project rather than actual web scraping.

# Disable image downloading to save bandwidth and time during the demonstration
IMAGES_ENABLED = False

# Set a download delay to avoid overwhelming the server with requests
DOWNLOAD_DELAY = 2  # 2-second delay between requests

# Increase the number of concurrent requests to speed up scraping (only for demonstration)
CONCURRENT_REQUESTS = 16  # Increase the number of requests sent at once

# Enable auto-throttling to dynamically adjust request speed based on server load
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1  # The minimum delay in seconds between requests
AUTOTHROTTLE_MAX_DELAY = 10  # The maximum delay in seconds
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0  # The average number of requests to send concurrently

# Set a page limit to stop crawling after a certain number of pages (for the demonstration purposes)
CLOSESPIDER_PAGECOUNT = 3 # Stop after crawling 3 pages

# Set the feed format to CSV for easy data export and presentation
FEED_FORMAT = 'csv'  # The format for the output feed, using CSV for simplicity
FEED_URI = '/data/books_data.csv'  # The output file name for the scraped data

# Specify the order of the columns in the exported feed.
FEED_EXPORT_FIELDS = ['title', 'author', 'book_link', 'discount_price', 'old_price', 'currency', 'publisher']  # Order of columns

# Disable specific middleware that is not necessary for this project or is causing issues.
# In this case, the 'OffsiteMiddleware' prevents scraping of websites outside the allowed domain.
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.offsite.OffsiteMiddleware': None,  # Disable this middleware to allow scraping external domains
}


