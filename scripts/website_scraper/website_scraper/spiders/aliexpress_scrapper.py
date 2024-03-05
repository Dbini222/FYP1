# Import necessary libraries
import scrapy
# Aliexpress stores all the products in a Javascript variable, so we have to use hidden web data scraping
class AliexpressSpider(scrapy.Spider):
    name = 'aliexpress_spider'
    start_urls = ['https://www.aliexpress.com/w/wholesale-men-t-shirts.html?g=y&SearchText=men+t+shirts&sortType=total_tranpro_desc']

    def parse(self, response):
        # Extract t-shirt designs and other relevant data
        for product in response.css('div.list--gallery--C2f2tvm search-item-card-wrapper-gallery'):
            tshirt_image = product.css('img.images--item--3XZa6xf').get()
            release_date = product.css('.date::text').get()

            # You can further process the data or save it to a file/database
            yield {
                'tshirt_design': tshirt_image,
                'release_date': release_date,
            }

        # Follow pagination links if available (for multiple pages)
        next_page = response.css('.next-page a::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

# Run the spider
if __name__ == '__main__':
    from scrapy.crawler import CrawlerProcess
    process = CrawlerProcess(settings={
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    })
    process.crawl(AliexpressSpider)
    process.start()
