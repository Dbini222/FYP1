import random
import pytest
import asyncio
from scripts.AliexpressScraper import AliexpressScraper
from typing import List

# Testing the AliexpressScraper class
# All of these tests are suseptible to failing if they catch suspicious traffic on the website
@pytest.mark.asyncio
async def test_get_data():
    print("Test for getting data\n")
    scraper = AliexpressScraper()
    response = await scraper.session.get("https://www.aliexpress.com/w/wholesale-men-t-shirts.html?g=y&SearchText=men+t+shirts&sortType=total_tranpro_desc")
    data = await scraper.get_data(response)
    # print(data)
    # assert isinstance( sdata, List)
    assert len(data) > 0
    await scraper.close_session()

@pytest.mark.asyncio
async def test_get_product_id():
    print("Test for getting product ID\n")
    scraper = AliexpressScraper()
    response = await scraper.session.get("https://www.aliexpress.com/w/wholesale-men-t-shirts.html?g=y&SearchText=men+t+shirts&sortType=total_tranpro_desc")  # Provide a sample response URL
    product_ids = await scraper.get_product_id(response)
    print(product_ids)
    assert isinstance(product_ids, list)
    assert len(product_ids) > 0
    for product_id in product_ids:
        assert isinstance(product_id, dict)
        assert "id" in product_id
    await scraper.close_session()

# The below may not work if they detect unusual traffic
@pytest.mark.asyncio
async def test_parse_product():
    list_of_product_ids = [1005005866501109, 1005005443335313, 1005005900379973, 1005005996024886, 1005005858620129, 1005006030970234, 1005006019043419, 1005005888148924, 1005002049426485, 1005005479813159, 1005005552376470, 1005004985454698, 1005005028721650, 1005005872755078, 1005005893374035]
    # pick a random number between 0 and len(list_of_product_ids)
    random_number = random.randint(0, len(list_of_product_ids)-1)
    id = list_of_product_ids[random_number]
    print("Test for parsing a product\n")
    scraper = AliexpressScraper()
    response = await scraper.session.get(f"https://www.aliexpress.com/item/{id}.html")
    print(response)
    product = await scraper.parse_product(response)
    print(product)
    assert isinstance(product, dict)
    assert "name" in product
    assert "total_orders" in product
    assert "feedback" in product
    assert "images" in product
    await scraper.close_session()

@pytest.mark.asyncio
async def test_scrape_products():
    print("Test for scraping a product\n")
    scraper = AliexpressScraper()
    product_ids = ["1005005866501109"]
    response = await scraper.scrape_products(product_ids)
    print(response)
    assert isinstance(response, List)
    assert len(response) > 0    
    for product in response:
        assert isinstance(product, dict)
        assert "name" in product
        assert "total_orders" in product
        assert "feedback" in product
        assert "images" in product
    await scraper.close_session()

@pytest.mark.asyncio
async def test_scrape():
    print("Test for scraping data\n")
    scraper = AliexpressScraper()
    data = await scraper.scrape()
    # assert isinstance(data, list)
    # assert len(data) > 0
    # for product in data:
    #     assert isinstance(product, dict)
    #     assert "id" in product
    await scraper.close_session()

@pytest.mark.asyncio
async def test_run():
    print("Test for running the scraper\n")
    scraper = AliexpressScraper()
    await scraper.run() # This will print scraped data to console that you can manually inspect.
    await scraper.close_session()



if __name__ == "__main__":
    asyncio.run(test_get_data())
    asyncio.run(test_get_product_id())
    asyncio.run(test_parse_product())
    asyncio.run(test_scrape_products())
    asyncio.run(test_scrape())
    asyncio.run(test_run())
