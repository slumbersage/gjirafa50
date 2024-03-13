# Gjirafa50 API Documentation

Welcome to the Gjirafa50 API documentation! Here, you'll find everything you need to know to interact with our API and harness its power for your applications.

## Table of Contents

1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [Endpoints](#endpoints)
    - [Search Products](#search-products)
    - [Get Product Details](#get-product-details)
    - [Fetch Categories](#fetch-categories)
    - [Retrieve Banners](#retrieve-banners)
    - [Happy Hours](#happy-hours)
4. [Example Usage](#example-usage)
5. [Conclusion](#conclusion)

## Introduction

Our API provides access to a wide range of functionalities related to product search, retrieval, and categorization. With easy-to-use endpoints and comprehensive documentation, developers can integrate our API seamlessly into their applications.



## Setup

To use the Gjirafa50 API in your project, follow these steps:

1. Clone the repository to your local machine or server:
   ```bash
   git clone https://github.com/slumbersage/gjirafa50.git
   ```

2. Navigate to the project directory:
   ```bash
   cd gjirafa50
   ```

3. Install the required packages using pip:
   ```bash
   pip install -r requirements.txt
   ```

4. Obtain your API key and add it to the `valid_api_keys.json` file.

5. Start the API server:
   ```bash
   uvicorn mainapi:app --reload
   ```




## Authentication

To access our API, you need to provide an API key in the headers of your requests. Without a valid API key, access will be denied.

You can go to to the file ``valid_api_keys.json`` to add a key 

## Endpoints

### Search Products

Endpoint: `/api/search`

Description: Search for products based on various criteria such as page number, search query, price range, and more.

Parameters:
- `pagenumber` (int): Page number to search (default is 1).
- `orderby` (str): Order by parameter (default is "10").
- `q` (str): Search query (default is "laptop asus gaming").
- `advs` (bool): Advs parameter (default is False).
- `hls` (bool): Hls parameter (default is False).
- `is` (bool): Is parameter (default is False).
- `startprice` (Optional[int]): Start price for filtering products (default is None).
- `maxprice` (Optional[int]): Max price for filtering products (default is None).
- `_` (int): Underscore parameter (default is the current timestamp in milliseconds).

Response:
```json
{
  "total_pages": "5",
  "views": "100",
  "products": [
    {
      "title": "Product Title",
      "price": "100.00",
      "discount": "10%",
      "link": "https://example.com/product",
      "price_no_discount": "90.00",
      "image_url": "https://example.com/image.jpg"
    },
    ...
  ]
}
```

### Get Product Details

Endpoint: `/api/product/details`

Description: Retrieve details of a product from its URL.

Parameters:
- `product_url` (str): The URL of the product.

Response:
```json
{
  "Name": "Product Name",
  "Price": "100.00",
  "PriceWithDiscount": "90.00",
  "InStock": true,
  "StockQuantity": 10,
  "ShortDescription": "Short product description.",
  "FullDescription": "Full product description.",
  "DeliveryTimes": {
    "Prishtinë": "2-3 days",
    "tjera": "3-5 days"
  },
  "ProductSpecificationModel": {
    "Attribute1": "Value1",
    "Attribute2": "Value2"
  },
  "ImageModels": {
    "DefaultPictureModel": {
      "Id": 1,
      "ImageUrl": "https://example.com/image.jpg"
    },
    "PictureModels": [
      {
        "Id": 2,
        "ImageUrl": "https://example.com/image2.jpg"
      },
      ...
    ]
  }
}
```

### Fetch Categories

Endpoint: `/api/categories`

Description: Fetch and return a list of available categories.

Parameters:
- `q` (Optional[str]): Search query for categories.
- `min_subcategories` (Optional[int]): Minimum number of subcategories.
- `max_subcategories` (Optional[int]): Maximum number of subcategories.
- `include_empty_categories` (bool): Include categories with no subcategories.

Response:
```json
{
  "Category1": [
    {
      "name": "Subcategory1",
      "url": "https://example.com/category1/subcategory1"
    },
    ...
  ],
  ...
}
```

### Retrieve Banners

Endpoint: `/api/banners`

Description: Retrieve banners from Gjirafa50.com.

Response:
```json
[
  {
    "link": "https://example.com/banner1",
    "image_url": "https://example.com/banner1.jpg",
    "alt_text": "Banner 1",
    "title": "Banner 1 Title"
  },
  ...
]
```

### Happy Hours

Endpoint: `/api/happy-hours`

Description: Fetch and return details of products on happy hours.

Response:
```json
{
  "products": [
    {
      "Name": "Product Name",
      "Price": "100.00",
      "Discount": "10%",
      "InStock": true,
      "StockQuantity": 10,
      "SeName": "/product-name",
      "ImageUrl": "https://example.com/image.jpg"
    },
    ...
  ]
}
```

## Example Usage


### Here's an example usage of the Gjirafa50 API Directly

```python
import requests

# Define the base URL and API key
BASE_URL = "http://127.0.0.1:8000"
API_KEY = "your_api_key"

# Define the endpoint URLs
SEARCH_ENDPOINT = f"{BASE_URL}/api/search"
PRODUCT_DETAILS_ENDPOINT = f"{BASE_URL}/api/product/details"
CATEGORIES_ENDPOINT = f"{BASE_URL}/api/categories"
BANNERS_ENDPOINT = f"{BASE_URL}/api/banners"
HAPPY_HOURS_ENDPOINT = f"{BASE_URL}/api/happy-hours"

# Function to make a GET request to the API
def make_get_request(url, params=None):
    headers = {"api-key": API_KEY}
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()

# Example usage of the API endpoints
def example_usage():
    # Search for products
    search_params = {
        "pagenumber": 1,
        "orderby": "10",
        "q": "laptop asus gaming"
    }
    search_result = make_get_request(SEARCH_ENDPOINT, params=search_params)
    print("Search Result:")
    print(search_result)

    # Get product details
    product_details_params = {"product_url": "https://example.com/product"}
    product_details = make_get_request(PRODUCT_DETAILS_ENDPOINT, params=product_details_params)
    print("Product Details:")
    print(product_details)

    # Fetch categories
    categories_result = make_get_request(CATEGORIES_ENDPOINT)
    print("Categories:")
    print(categories_result)

    # Retrieve banners
    banners_result = make_get_request(BANNERS_ENDPOINT)
    print("Banners:")
    print(banners_result)

    # Fetch happy hour products
    happy_hours_result = make_get_request(HAPPY_HOURS_ENDPOINT)
    print("Happy Hours Products:")
    print(happy_hours_result)

# Call the example usage function
example_usage()
```

### Here's an example usage of the Gjirafa50 API client:

First, install the API Client Wrapper;
```bash
pip install gjirafa50
```
Example Usage

```python
from Gjirafa50 import Gjirafa50APIClient

# Initialize the client
client = Gjirafa50APIClient("http://127.0.0.1:8000", "your_api_key")

# Search for products
client.search(pagenumber=1, orderby="10", q="laptop asus gaming", formatted=True)

# Get product details
client.productdetails(product_url="https://example.com/product", formatted=True)

# Fetch categories
client.fetch_categories(formatted=True)

# Retrieve banners
client.banners(formatted=True)

# Fetch happy hour products
client.happy_hours(formatted=True)
```

## Conclusion

With this documentation, you're now equipped to use the Gjirafa50 API in your projects. If you have any questions or need further assistance, feel free to join our Discord server:

[![Discord](https://img.shields.io/discord/1200531052876275806)](https://discord.gg/6SQ5HfaMsp)

Happy coding! 💻🎉
