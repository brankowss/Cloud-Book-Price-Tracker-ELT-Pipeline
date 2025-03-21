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
            item['currency'] = 'RSD'  
            
            # Parsing publisher from URL
            if item['book_link']:
                parsed_url = urlparse(response.urljoin(item['book_link']))
                domain_parts = parsed_url.hostname.split('.')
                item['publisher'] = domain_parts[-2] if len(domain_parts) > 1 else domain_parts[0]
                
                # Sending a request to the book's additional data page
                yield response.follow(item['book_link'], callback=self.parse_book_page, meta={'item': item})

        # Pagination - moving to the next page
        next_page = response.xpath("//*[contains(text(), 'Naredna »')]/@href").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_book_page(self, response):
        """Scrapuje stranicu knjige i dodaje opis u podatke."""
        item = response.meta['item']
        item['description'] = response.xpath('//div[@class="prikaz_k2"]//span[@class="prikaz_opis"]').xpath('string()').get()

        yield item
