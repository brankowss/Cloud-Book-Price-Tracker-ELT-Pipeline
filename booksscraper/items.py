import scrapy


class BookItem(scrapy.Item):
    title = scrapy.Field()
    author = scrapy.Field()
    book_link = scrapy.Field()
    old_price = scrapy.Field()
    discount_price = scrapy.Field()
    currency = scrapy.Field()
    publisher = scrapy.Field() 