import scrapy
# no need to get shop name here, because all the products have unique names
class TeefurySpider(scrapy.Spider):
    name = "teefury"
    start_urls = [
        'https://teefury.com/collections/tees',
    ]
    item_count = 0
    stop_new_requests = False  # Flag to stop new product processing
    website = 'teefury'
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 32
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, self.parse, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'})

    def parse(self, response):
        if not self.stop_new_requests:
            for product in response.css('div.collection-product.medium-up--one-third.small-down--one-half'):
                if product is None or product == []:
                    print('No products found, refer back to website incase they have changed their structure')
                    break
                if self.item_count >= 2500:
                    self.stop_new_requests = True  # Set the flag to stop processing new items
                    break  # Stop the loop
                
                self.item_count += 1
                id_attr = product.css('a::attr(id)').get()
                product_id = id_attr.split('-')[-1]
                product_image = product.css('img.collect-prod__img::attr(src)').get()
                product_description = product.css('div.product-grid-item__meta a::text').get()
                
                try:
                    if product_id and product_image and product_description is not None:
                        yield {
                            'product_id': product_id,
                            'images': 'https:' + product_image,
                            'description': product_description,
                            'shop': None,
                            'website': self.website,
                            'popularity': self.item_count,
                                }
                except Exception as e:
                    print('Error: ', e)

        # Handle pagination only if not stopped
        if not self.stop_new_requests:
            next_page_url = response.xpath('//a[contains(@class, "btn") and contains(@class, "btn--tertiary") and contains(@class, "btn--narrow") and .//span[text()="Next page"]]/@href').get()
            if next_page_url:
                next_page = response.urljoin(next_page_url)
                yield response.follow(next_page, callback=self.parse)

        # Close the spider when 2500 items have been processed
        if self.item_count >= 2500:
            self.crawler.engine.close_spider(self, 'reached maximum item count')
