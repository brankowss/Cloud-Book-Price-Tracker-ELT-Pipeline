import scrapy
from booksscraper.items import BookItem
from urllib.parse import urlparse

class PrometejSpider(scrapy.Spider):
    name = "prometej"
    allowed_domains = ["https://www.prometej.rs"]
    start_urls = ["https://www.prometej.rs/prodavnica/"]

    def parse(self, response):
        for link in response.xpath('//div[@class="large-6 medium-4 columns product-listing"]//div[@class="book-meta"]/a/@href'):
            yield response.follow(link.get(), callback=self.parse_book_page)

            next_page = response.xpath('//a[@class="next page-numbers"]/@href').get()
            if next_page is not None:
                yield response.follow(next_page, callback=self.parse)
    
    def parse_book_page(self, response):    
        rd = response.xpath('//div[@id="content"]')
        for r in rd:
            item = BookItem()
            item['title'] = r.xpath('.//h1[@class="product_title entry-title"]/text()').get()
            item['author'] = r.xpath('(//div[@id="content"]//span[@itemprop="author"])[1]/text()').get()
            item['book_link'] = r.xpath('(//div[@class="book-cover small"]/a)[1]/@href').get()
            item['old_price'] = r.xpath('(//span[@class="old-price amount"]/del)[1]/text()').get() 
            item['discount_price'] = r.xpath('(//span[@class="sale-price amount"])[1]/text()').get()
            # Parse the publisher from the book link URL
            url = urlparse(item['book_link'])
            domain_parts = url.hostname.split('.')
            item['publisher'] = domain_parts[-2] if len(domain_parts) > 1 else domain_parts[0]
            item['currency'] = 'RSD'  
            item['description'] = r.xpath('(//div[@class="large-6 columns"])[1]').xpath('string()').getall()
            yield item

