import scrapy


class AmazonSpider(scrapy.Spider):
    name = "amazon"
    start_urls = [
        "https://www.amazon.co.uk/Best-Sellers-Fashion-Mens-T-Shirts/zgbs/fashion/1731028031/ref=zg_bs_pg_1_fashion?_encoding=UTF8&pg=1"
    ]
    baseURL = 'https://www.amazon.co.uk'
    resolutions = ['4000', '3000', '2000', '1000', '800']  # Common resolutions to try

    def parse(self, response):
        for product in response.css('div.a-cardui._cDEzb_grid-cell_1uMOS.expandableGrid.p13n-grid-content'):
            if product is None or product == []:
                print('No products found, refer back to website incase they have changed their structure')
                break
            product_id = product.css('div.p13n-sc-uncoverable-faceout').attrib['id']
            description = product.css('div._cDEzb_p13n-sc-css-line-clamp-3_g3dy1::text').get()
            popularity = int(product.css('span.zg-bdg-text::text').get().replace("#", ""))
            images = product.css('img.a-dynamic-image.p13n-sc-dynamic-image.p13n-product-image::attr(data-old-hires)').get()
            try:
                if product_id and description and popularity is not None:
                    image_url = self.get_highest_resolution(images)
                    yield {
                        'product_id': product_id,
                        'images': image_url,
                        'description': description,
                        'shop': None,
                        'website': 'amazon',
                        'popularity': popularity,
                        'age': self.age,
                    }

            except Exception as e:
                print('Error: ', e)

        next_page = self.baseURL + response.css('li.a-last a::attr(href)').get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)

    def get_highest_resolution(self, image_url):
        for resolution in self.resolutions:
            new_url = image_url.replace("._AC_UL300_SR300,200_", "._AC_UL{}_SR300,200_".format(resolution))
            if self.url_exists(new_url):
                return new_url
        return image_url

    def url_exists(self, url):
        request = scrapy.Request(url, method='HEAD')
        response = self.crawler.engine.download(request, self)
        return response.status == 200
