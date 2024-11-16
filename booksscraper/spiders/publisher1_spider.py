import scrapy
from booksscraper.items import BookItem
from urllib.parse import urlparse

class LagunaSpider(scrapy.Spider):
    name = "laguna"
    allowed_domains = ["www.laguna.rs"]
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
            item['author'] = i.xpath('(//h2[1]/a)[1]/text()').get() 
            book_link = response.xpath('.//a[@class="komentar-podatak"]/@href').get()
            prefix = "https://www.laguna.rs/"
            item['book_link'] = prefix + book_link if book_link else None
            item['old_price'] = i.xpath('(//div[@class="cena"]/p[1]/text())[1]').get()
            item['discount_price'] = i.xpath('(//span[@class="naslov"]/following-sibling::text())[8]').get()
            # Parse the publisher from the book link URL
            url = urlparse(item['book_link'])
            domain_parts = url.hostname.split('.')
            item['publisher'] = domain_parts[-2] if len(domain_parts) > 1 else domain_parts[0]
            yield item

#vidi sta ti sve ne treba od foldera itd... trebace ti .gitignore licenca i idemo poslednja provera i push na github i
#onda menjamo sajt i sliku na X
#nastavak projekata samo bam bam neki idu na tvoj github pa neka gledaju i cao
#samo jednostavno kao CV sto si pravio
#dobro sve proveri
#14.11.2024.

#proveri ovaj gitignore sta da izbacis i sta ces da stavis u licencu proveri sve pre push-a.