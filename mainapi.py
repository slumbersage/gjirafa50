"""

Copyright (c) 2024 slumbersage

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""




from fastapi import FastAPI, Query, Header, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from bs4 import BeautifulSoup
import json
import re
import requests
from typing import List, Dict, Optional

app = FastAPI()

# Load valid API keys from JSON file
def load_valid_api_keys():
    with open("valid_api_keys.json", "r") as file:
        return json.load(file)

# Model for API key in header
class APIKeyHeader(BaseModel):
    api_key: str

# Custom exception for unauthorized access
class UnauthorizedAccess(HTTPException):
    def __init__(self):
        super().__init__(status_code=403, detail="Unauthorized access")

# Middleware for API key authentication
async def authenticate_api_key(api_key: str = Header(...), valid_api_keys: dict = Depends(load_valid_api_keys)):
    if api_key not in valid_api_keys:
        raise UnauthorizedAccess()
    else:
        # You can log the user associated with the API key here if needed
        print(f"User with API key '{api_key}' is authenticated")

# Model for product data
class Product(BaseModel):
    title: str
    price: str
    discount: Optional[str]
    link: str
    price_no_discount: str
    image_url: str

# Model for scraped data
class ScrapeResult(BaseModel):
    total_pages: int # update this to integer data type
    views: int # same for this, updated to int data type
    products: List[Product]

# Function to scrape website (omitted for brevity)

def scrape_website(pagenumber: int = Query(1, description="Page number to scrape"),
                   orderby: str = Query("10", description="Order by: 10 - Price: Low to High, 11 - Price: High to Low, 16 - Newest, 17 - Highest Discount"),
                   q: str = Query("laptop", description="Search query"),
                   advs: bool = Query(False, description="Advs"),
                   hls: bool = Query(False, description="Hls"),
                   is_param: bool = Query(False, description="Is"),
                   startprice: Optional[int] = Query(None, description="Start price"),
                   maxprice: Optional[int] = Query(None, description="Max price"),
                   _: int = Query(1710025383220, description="Underscore")):
    base_url = "https://gjirafa50.com/product/search"
    price_range = None
    if startprice is not None and maxprice is not None:
        price_range = f"{startprice}-{maxprice}"
    params = {
        "pagenumber": pagenumber,
        "orderby": orderby,
        "q": q, 
        "advs": advs,
        "hls": hls,
        "is": is_param,
        "_": _,
        "price": price_range
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        json_data = response.json()
        total_pages = json_data.get("totalpages", "N/A")
        views = json_data.get("totalHits", "N/A")
        html_content = json_data.get("html", "")

        soup = BeautifulSoup(html_content, "html.parser")

        products = []
        for item_box in soup.find_all("div", class_="item-box"):
            product_title = item_box.find("h2", class_="product-title").text.strip()
            price = item_box.find("span", class_="price").text.strip()
            
            # Filter products based on price range
            if startprice is not None and maxprice is not None:
                price_value = get_price_value(price)
                if price_value < startprice or price_value > maxprice:
                    continue
            
            discount_label = item_box.find("div", class_="discount__label")
            discount = discount_label.text.strip() if discount_label else None
            product_link = item_box.find("a")["href"]
            price_no_discount = price  # Assume availability holds the price without discount
            image_url = item_box.find("img")["src"]

            product = Product(
                title=product_title,
                price=price,
                discount=discount,
                link=product_link,
                price_no_discount=price_no_discount,
                image_url=image_url,
            )
            products.append(product)
        
        # Sort products based on orderby criteria
        if orderby == "10":
            products.sort(key=lambda x: float(re.sub(r'[^0-9.]', '', x.price)))
        elif orderby == "11":
            products.sort(key=lambda x: -float(re.sub(r'[^0-9.]', '', x.price)))
        elif orderby == "16":
            products.sort(key=lambda x: x.full_description)  # Example sorting by description
        elif orderby == "17":
            products.sort(key=lambda x: x.discount if x.discount else "0", reverse=True)  # Sorting by discount if available
        
        return ScrapeResult(total_pages=total_pages, views=views, products=products)
    else:
        return None

def get_price_value(price_str: str) -> float:
    """Extracts the numeric part of the price string and converts it to a float."""
    try:
        # Use regex to extract numeric part of the string
        numeric_part = re.sub(r'[^0-9.]', '', price_str)
        return float(numeric_part)
    except ValueError:
        # Handle cases where conversion to float fails
        return 0.0  # Return 0.0 as a default value or handle the error as needed

@app.get("/api/search", response_model=ScrapeResult, tags=["Search"], dependencies=[Depends(authenticate_api_key)])
def search_products(pagenumber: int = Query(..., ge=1, description="Page number to search"),
                    orderby: str = Query(..., regex=r"^(0|10|11|16|17)$", description="Order by: 0: Most relevant, 10 - Price: Low to High, 11 - Price: High to Low, 16 - Newest, 17 - Highest Discount"),
                    q: str = Query(..., min_length=1, description="Search query"),
                    advs: bool = Query(False, description="Advs"),
                    hls: bool = Query(False, description="Hls = Filter Products that ship within 24h "),
                    is_param: bool = Query(False, description="Is = Remove all sold out products "),
                    startprice: Optional[int] = Query(None, ge=0, description="Start price"),
                    maxprice: Optional[int] = Query(None, ge=0, description="Max price"),
                    _: int = Query(int(datetime.now().timestamp() * 1000), description="Underscore parameter = Current Time Snowflake ")):
    """
    Search for products.
    
    This endpoint searches for products based on the specified criteria and returns a list of matching products.
    
    Args:
        pagenumber (int): Page number to search (default is 1).
        orderby (str): Order by parameter (default is "0").
        q (str): Search query (default is "laptop asus gaming").
        advs (bool): Advs parameter (default is False).
        hls (bool): Hls parameter (default is False).
        is_param (bool): Is parameter (default is False).
        startprice (Optional[int]): Start price for filtering products (default is None).
        maxprice (Optional[int]): Max price for filtering products (default is None).
        _ (int): Underscore parameter (default is the current timestamp in milliseconds).
    """
    scraped_data = scrape_website(pagenumber, orderby, q, advs, hls, is_param, startprice, maxprice, _)
    if scraped_data:
        return scraped_data
    else:
        raise HTTPException(status_code=500, detail="Failed to search for products")


@app.get("/api/product/details", dependencies=[Depends(authenticate_api_key)])
async def get_product_details(product_url: str):
    """
    Retrieve details of a product from its URL.

    Args:
        product_url (str): The URL of the product.

    Returns:
        dict: A dictionary containing the short description, full description (without HTML tags), product specification model, delivery times for Prishtinë and Kosovë, të tjera,
        DefaultPictureModel (with Id and ImageUrl), and PictureModels (with Ids and ImageUrls).
        
    Raises:
        HTTPException: If the URL is invalid, or if there is an error fetching or parsing the product page.
    """
    
    try:
        # Check if the URL is valid
        if not is_valid_url(product_url):
            raise HTTPException(status_code=400, detail="Invalid URL provided.")
        
        response = requests.get(product_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract delivery times
            delivery_times = extract_delivery_times(soup)
            
            # Extract product models
            product_models = extract_product_models(response.text)
            
            # Extract ShortDescription and FullDescription (remove HTML tags)
            short_description = re.sub('<[^<]+?>', '', product_models.get("ShortDescription", "Short Description not available"))
            full_description = re.sub('<[^<]+?>', '', product_models.get("FullDescription", "Full Description not available"))
            
            # Simplify ProductSpecificationModel
            simplified_specification = simplify_specification(product_models)
            
            # Prepare image data
            image_data = prepare_image_data(product_models)
            
            # Extract Price and PriceWithDiscount
            product_price = product_models.get("ProductPrice", {})
            price = product_price.get("Price", "")
            price_with_discount = product_price.get("PriceWithDiscount", "")
            
            return {
                "Name": product_models.get("Name", ""),
                "Price": price,
                "PriceWithDiscount": price_with_discount,
                "InStock": product_models.get("InStock", False),
                "StockQuantity": product_models.get("StockQuantity", 0),
                "ShortDescription": short_description.strip(),
                "FullDescription": full_description.strip(),
                "ProductSpecificationModel": simplified_specification,
                "DeliveryTimes": delivery_times,
                "ImageModels": image_data
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch the product page.")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def is_valid_url(url):
    """
    Checks if the given string is a valid URL for gjirafa50 website.
    """
    return re.match(r"https?://(?:www\.)?[\w.-]*gjirafa50\.(?:com|mk|al)(?:/[^\s]*)?", url) is not None

def extract_delivery_times(soup):
    """
    Extract delivery times from the parsed HTML.
    """
    delivery_times = {}
    delivery_date_element_prishtine = soup.find("div", class_="flex flex-col justify-center pl-2 text-xs font-medium pr-2 mr-2 tablet:border-r")
    delivery_date_element_tjera = soup.find("div", class_="flex flex-col justify-center pl-2 text-xs font-medium")

    if delivery_date_element_prishtine:
        # Extract the text content of the element and remove HTML tags
        delivery_date_prishtine = re.sub('<[^<]+?>', '', delivery_date_element_prishtine.get_text(strip=True))
        
        # Extract and format the date range using regular expressions
        date_range_prishtine = re.search(r'\d+\s+\w+\s+\d+\s*-\s*\d+\s+\w+\s+\d+', delivery_date_prishtine)
        if date_range_prishtine:
            delivery_times["Prishtinë"] = date_range_prishtine.group()
    else:
        print("Delivery date element for Prishtinë not found on the page.")
    
    if delivery_date_element_tjera:
        # Extract the text content of the element and remove HTML tags
        delivery_date_tjera = re.sub('<[^<]+?>', '', delivery_date_element_tjera.get_text(strip=True))
        
        # Extract and format the date range using regular expressions
        date_range_tjera = re.search(r'\d+\s+\w+\s+\d+\s*-\s*\d+\s+\w+\s+\d+', delivery_date_tjera)
        if date_range_tjera:
            delivery_times["tjera"] = date_range_tjera.group()
    else:
        print("Delivery date element for Kosovë, të tjera not found on the page.")
    
    return delivery_times

def extract_product_models(response_text):
    """
    Extract product models from the response text.
    """
    product_model_pattern = re.compile(r"var productModel = (\{.*?\});", re.DOTALL)
    product_model_match = product_model_pattern.search(response_text)
    
    if product_model_match:
        # Extract the productModel dictionary/json
        product_model_json = product_model_match.group(1)
        
        # Convert the JSON string to a Python dictionary
        product_model_dict = json.loads(product_model_json)
        
        return product_model_dict
    else:
        raise HTTPException(status_code=500, detail="Product model not found on the page.")

def simplify_specification(product_models):
    """
    Simplify the product specification model.
    """
    simplified_specification = {}
    for group in product_models.get("ProductSpecificationModel", {}).get("Groups", []):
        for attribute in group.get("Attributes", []):
            simplified_specification[attribute["Name"]] = attribute["Values"][0]["ValueRaw"]
    
    return simplified_specification

def prepare_image_data(product_models):
    """
    Prepare image data from product models.
    """
    image_data = {}
    
    default_picture_model = product_models.get("DefaultPictureModel", {})
    image_data["DefaultPictureModel"] = {
        "Id": default_picture_model.get("Id", 0),
        "ImageUrl": default_picture_model.get("ImageUrl", "")
    }
    
    picture_models = product_models.get("PictureModels", [])
    picture_model_data = []
    for picture_model in picture_models:
        picture_model_data.append({
            "Id": picture_model.get("Id", 0),
            "ImageUrl": picture_model.get("ImageUrl", "")
        })
    
    image_data["PictureModels"] = picture_model_data
    
    return image_data




# Function to fetch categories and subcategories from gjirafa50.com
def fetch_categories():
    url = "https://gjirafa50.com"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            category_elements = soup.find_all('li', class_='category-item')
            categories = {}
            for category_element in category_elements:
                category_name_element = category_element.find('a', class_='category-item-content')
                category_name = category_name_element.get_text(strip=True)
                category_url = category_name_element['href']
                if category_element.find('ul', class_='sublist'):
                    subcategories_element = category_element.find('ul', class_='sublist')
                    subcategories = []
                    for subcategory_element in subcategories_element.find_all('a', class_='category-item-content'):
                        subcategory_name = subcategory_element.get_text(strip=True)
                        subcategory_url = subcategory_element['href']
                        subcategories.append({
                            'name': subcategory_name,
                            'url': subcategory_url
                        })
                    categories[category_name] = subcategories
                elif category_url not in categories:
                    categories[category_name] = [{'name': category_name, 'url': category_url}]
            return categories
        else:
            return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

# Load categories on startup
categories_data = fetch_categories()

@app.get("/api/categories", dependencies=[Depends(authenticate_api_key)], tags=["Categories"])
async def get_categories(
    q: Optional[str] = Query(None, description="Search query for categories"),
    min_subcategories: Optional[int] = Query(None, description="Minimum number of subcategories"),
    max_subcategories: Optional[int] = Query(None, description="Maximum number of subcategories"),
    include_empty_categories: Optional[bool] = Query(False, description="Include categories with no subcategories"),
    ):
    """Fetches and returns a list of available categories."""
    if categories_data:
        filtered_categories = {}
        for category, subcategories in categories_data.items():
            num_subcategories = len(subcategories)
            if (min_subcategories is None or num_subcategories >= min_subcategories) and \
               (max_subcategories is None or num_subcategories <= max_subcategories) and \
               (include_empty_categories or num_subcategories > 0) and \
               (q.lower() in category.lower() if q else True):
                filtered_categories[category] = subcategories
        return filtered_categories
    else:
        return {"message": "Failed to fetch categories from gjirafa50.com"}


# Model for banner data
class Banner(BaseModel):
    link: str
    image_url: str
    alt_text: str
    title: str

# Function to scrape banners from gjirafa50.com
def scrape_banners(url: str) -> List[Banner]:
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        banner_elements = soup.find_all('div', class_='swiper-slide')
        banners = []
        for banner_element in banner_elements:
            link_tag = banner_element.find('a')
            img_tag = banner_element.find('img')
            if link_tag and img_tag:
                banner_link = link_tag.get('href')
                img_src = img_tag.get('src')
                img_alt = img_tag.get('alt')
                img_title = img_tag.get('title')
                banner = Banner(link=banner_link, image_url=img_src, alt_text=img_alt, title=img_title)
                banners.append(banner)
        return banners
    else:
        return []


@app.get("/api/banners", response_model=List[Banner], tags=["Banners"], dependencies=[Depends(authenticate_api_key)])
async def get_banners():
    """
    Retrieve banners from gjirafa50.com.
    """
    url = "https://gjirafa50.com"
    return scrape_banners(url)




product_url = "https://gjirafa50.com/happy-hours"

@app.get("/api/happy-hours", tags=["Happy Hours"], dependencies=[Depends(authenticate_api_key)])
async def get_happy_hours():
    """
    Fetches and returns details of products on happy hours from gjirafa50.com.
    """
    transformed_products = fetch_and_transform_product_details(product_url)
    if transformed_products:
        return {"products": transformed_products}
    else:
        return {"message": "Failed to fetch happy hour products."}

def fetch_product_page(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to fetch the product page. Status code: {response.status_code}")
        return None

def extract_category_model(html_content):
    category_model_pattern = re.compile(r"var categoryModel = (\{.*?\});", re.DOTALL)
    category_model_match = category_model_pattern.search(html_content)
    
    if category_model_match:
        category_model_json = category_model_match.group(1)
        category_model_dict = json.loads(category_model_json)
        return category_model_dict
    else:
        print("Category model not found on the page.")
        return None

def extract_products(category_model):
    if category_model and "CatalogProductsModel" in category_model:
        products = category_model["CatalogProductsModel"]["Products"]
        return products
    else:
        print("Products not found in category model.")
        return None

def transform_product_details(products):
    if products:
        transformed_data = []
        for product in products:
            transformed_product = {
                "Name": product["Name"],
                "Price": product["ProductPrice"]["Price"],
                "Discount": product["ProductPrice"].get("DiscountPercentage", ""),
                "InStock": product["InStock"],
                "StockQuantity": product["StockQuantity"],
                "SeName": "/" + product.get("SeName", ""),  # Adding "/" before SeName
                "ImageUrl": product["DefaultPictureModel"]["ImageUrl"]
            }
            transformed_data.append(transformed_product)
        return transformed_data
    else:
        print("No products found.")
        return []

def fetch_and_transform_product_details(url):
    html_content = fetch_product_page(url)
    if html_content:
        category_model = extract_category_model(html_content)
        products = extract_products(category_model)
        transformed_data = transform_product_details(products)
        return transformed_data
