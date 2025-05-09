import scrapy
from booksscraper.items import BookItem
from urllib.parse import urlparse

class LagunaSpider(scrapy.Spider):
    name = "laguna"
    allowed_domains = ["laguna.rs", "www.laguna.rs"]
    start_urls = ["https://www.laguna.rs/s1_laguna_knjige_spisak_naslova.html"]

    def parse(self, response):
        for link in response.xpath('//div[@class="podaci"]/a[1]/@href'):
            yield response.follow(link.get(), callback=self.parse_book)

            next_page = response.css('a.sledeca::attr(href)').get()
            if next_page is not None:
                yield response.follow(next_page, callback=self.parse)
                
    def parse_book(self,response):
        for i in response.xpath('//body[@id="knjiga_page"]'):
            item = BookItem()
            item['title'] = i.xpath('(//h1[@class="naslov"])[3]/text()').get() 
            item['author'] = i.xpath('(//h2[1]/a)[1]/text()').get() or '' 
            book_link = response.xpath('.//a[@class="komentar-podatak"]/@href').get()
            prefix = "https://www.laguna.rs/"
            item['book_link'] = prefix + book_link if book_link else None
            item['category'] = i.xpath('//span[@class="naslov_podatka"]/following-sibling::h3/a/text()').get()
            item['old_price'] = i.xpath('(//div[@class="cena"]//span[@class="naslov"]/following-sibling::text())[1]').get()
            item['discount_price'] = i.xpath('(//div[@class="cena"]//span[@class="naslov"]/following-sibling::text())[2]').get()
            # Parse the publisher from the book link URL
            url = urlparse(item['book_link'])
            domain_parts = url.hostname.split('.')
            item['currency'] = 'RSD'
            item['publisher'] = domain_parts[-2] if len(domain_parts) > 1 else domain_parts[0]            
            item['description'] =i.xpath('.//div[@id="podaci-korica"]/div').xpath('string()').getall()
            yield item
