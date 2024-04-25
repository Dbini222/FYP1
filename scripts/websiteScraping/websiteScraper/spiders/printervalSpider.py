# 100 items
import scrapy 


class PrintervalSpider(scrapy.Spider):
    name = "printerval"
    start_urls = [
        'https://printerval.com/uk/c/clothing/shirts-tops/t-shirts?order=sold',
    ]
    age = 0
    overall_position = 0
    
    custom_settings = {
        'CLOSESPIDER_ITEMCOUNT': 2500 # scrape 2500 items as index starts at 0
    }
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, self.parse, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'})

    def parse(self, response):
        for product in response.css('div.product-item-box.price-highlight.old-price-highlight'):
            self.overall_position += 1
            if self.overall_position > self.custom_settings['CLOSESPIDER_ITEMCOUNT']:
                raise scrapy.exceptions.CloseSpider('reached maximum item count')
            title_href = product.css('a.product-title::attr(href)').extract_first()
            product_id = title_href.split('p')[-1] #if 'p' in title_href else None
            product_image = product.css('a.product-link img::attr(src)').extract_first()
            product_description = product.css('h2.product-title::text').extract_first()
            product_shop = product.css('a.product-category-link::text').extract_first()
        
            try:
                if product_id and product_image and product_description is not None:
                    yield {
                        'product_id': product_id,
                        'images': product_image,
                        'description':  product_description,
                        'shop': product_shop,
                        'website': self.name,
                        'popularity': self.overall_position,
                        'age': self.age,
                        }
        
            except Exception as e:
                print('Error: ', e)
                    # yield {
                    #     'product_id': None,
                    #     'images': None,
                    #     'description': None,
                    #     'shop': None,
                    #     'website': None,
                    #     'popularity':None,
                    #     'age': None,
                    #     }
        try:
            next_page = response.css('a.flex-b.align-c.flex-e::attr(href)').get()
            if next_page is not None:
                yield response.follow(next_page, callback=self.parse, dont_filter=True)
        except Exception as e:
            print('Error: ', e) 
            # log.msg(f'Error: {e}', level=log.ERROR)