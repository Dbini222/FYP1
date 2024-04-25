# https://threadheads.co.uk/collections/shirts?filter.p.product_type=T-Shirt
# max items: 1603

import scrapy 


class ThreadheadsSpider(scrapy.Spider):
    name = "threadheads"
    start_urls = [
        'https://threadheads.co.uk/collections/shirts?filter.p.product_type=T-Shirt',
    ]
    baseURL = 'https://threadheads.co.uk'
    age = 0
    overall_position = 0
    
    custom_settings = {
        'CLOSESPIDER_ITEMCOUNT': 2500 # scrape 2500 items as index starts at 0
    }

    def parse(self, response):
        for product in response.css('product-card.product-card.product-card--blends.bg-custom.text-custom'):
            self.overall_position += 1
            if self.overall_position > self.custom_settings['CLOSESPIDER_ITEMCOUNT']:
                print("here")
                raise scrapy.exceptions.CloseSpider('reached maximum item count')
            raw_id = product.css('quick-buy-drawer.quick-buy-drawer.drawer::attr(id)').extract_first()
            product_id = raw_id.split('-')[-1] #if 'p' in title_href else None
            product_image ='https:' + product.css('img.product-card__image.product-card__image--primary.aspect-natural::attr(src)').extract_first()
            product_description = product.css('a.bold::text').extract_first()
            # product_shop = product.css('a.product-category-link::text').extract_first()
        
            try:
                if product_id and product_image and product_description is not None:
                    yield {
                        'product_id': product_id,
                        'images': product_image,
                        'description':  product_description,
                        'shop': None,
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

        next_page = response.css('a.pagination__item.group[rel="next"]::attr(href)').get()
        if next_page is not None:
            print('Next Page: ', self.baseURL + next_page)
            yield response.follow(self.baseURL + next_page, callback=self.parse)

