import scrapy
from booksscraper.items import BookItem
from urllib.parse import urlparse

class MikrokSpider(scrapy.Spider):
    name = "mikrok"
    allowed_domains = ["https://www.mikroknjiga.rs"]
    start_urls = ["https://www.mikroknjiga.rs/store/index.php?IDvrste=1&o=2303&oblast=Ra%C4%8Dunari%20i%20Internet"]

    def parse(self, response):
        kv = response.xpath('//tr[@class="style_normal"]') 

        for k in kv:
            item = BookItem()
            item['title'] = k.xpath('.//span[@style="font-size:15px;"]/text()').get()
            item['author'] = k.xpath('.//td//i/text()').get()
            item['book_link'] = k.xpath('.//td//a/span[@style="font-size:15px;"]/../@href').get()
            item['old_price'] = k.xpath('.//td//strike/text()').get()
            item['discount_price'] = k.xpath('.//td//font[@color="#ff00ff"]/b/text()').get()
            url = urlparse(item['book_link'])
            domain_parts = url.hostname.split('.')
            item['publisher'] = domain_parts[-2] if len(domain_parts) > 1 else domain_parts[0]
            # Parse the publisher from the book link URL
            url = urlparse(item['book_link'])
            domain_parts = url.hostname.split('.')
            item['publisher'] = domain_parts[-2] if len(domain_parts) > 1 else domain_parts[0]
            yield item

            next_page = response.xpath("//*[contains(text(), 'Naredna »')]/@href").get()
            
            if next_page is not None:
                yield response.follow(next_page, callback=self.parse)
