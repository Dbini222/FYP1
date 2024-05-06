import scrapy
import json
import re


class AmazonSpider(scrapy.Spider):
    name = "amazon"
    start_urls = [
        "https://www.amazon.co.uk/Best-Sellers-Fashion-Mens-T-Shirts/zgbs/fashion/1731028031/ref=zg_bs_pg_1_fashion?_encoding=UTF8&pg=1"
    ]
    baseURL = 'https://www.amazon.co.uk'

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, self.parse, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'})


    def parse(self, response):
        for product in response.css('div.a-cardui._cDEzb_grid-cell_1uMOS.expandableGrid.p13n-grid-content'):
            if product is None or product == []:
                print('No products found, refer back to website incase they have changed their structure')
                break
            product_id = product.css('div.p13n-sc-uncoverable-faceout').attrib['id']
            description = product.css('div._cDEzb_p13n-sc-css-line-clamp-3_g3dy1::text').get()
            popularity = int(product.css('span.zg-bdg-text::text').get().replace("#", ""))
            images = product.css('img.a-dynamic-image.p13n-sc-dynamic-image.p13n-product-image::attr(data-a-dynamic-image)').get()
            try:
                image_data = json.loads(images)
                image_first_url = next(iter(image_data.keys()))
            except Exception as e:
                print('Amazon image data could not be loaded, Error: ', e)
            try:
                if product_id and description and popularity is not None:
                    image_url = self.get_highest_resolution(image_first_url)
                    yield {
                        'product_id': product_id,
                        'images': image_url,
                        'description': description,
                        'shop': None,
                        'website': 'amazon',
                        'popularity': popularity,
                    }

            except Exception as e:
                print('Check that the website has not changed their html, Error: ', e)

        next_page = self.baseURL + response.css('li.a-last a::attr(href)').get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)
        else:
            print('Amazon next page is None, check website structure for changes or ran out of pages')

    def get_highest_resolution(self, image_url):
        pattern = re.compile(r"._AC_UL\d+_SR\d+,\d+_")
        new_url = pattern.sub("._AC_UL4000_SR300,200_", image_url)
        return new_url


    # def url_exists(self, url):
    #     request = scrapy.Request(url, method='HEAD')
    #     response = self.crawler.engine.download(request)
    #     return response.status == 200
