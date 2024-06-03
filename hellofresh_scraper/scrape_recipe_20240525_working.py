import requests
from bs4 import BeautifulSoup
import json

# Base URL of the HelloFresh website
base_url = "https://www.hellofresh.com"

# Function to get the HTML content of a page
def get_html(url):
    response = requests.get(url)
    response.raise_for_status()  # Raise an HTTPError for bad responses
    return response.text

# Function to extract recipe category links from the main page
def get_category_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    category_div = soup.find('div', attrs={'data-test-id': 'recipes|world-cuisines-tags'})
    links = category_div.find_all('a', class_='cQbWbr')
    category_urls = [(link.text.strip(), base_url + link['href'] + '?page=1000') for link in links]
    return category_urls

# Function to extract recipe links from a category page
def get_recipe_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    divs = soup.find_all('div', attrs={'data-test-id': lambda value: value and value.startswith('recipe-card-')})
    recipe_urls = []
    for div in divs:
        link = div.find('a', class_='cQbWbr')
        if link and 'href' in link.attrs:
            recipe_urls.append(link['href'])
    return recipe_urls

# Function to scrape recipe details from a recipe page
def scrape_recipe(url, tag):
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    recipe = {'tag': tag}
    
    # Extracting recipe title
    title_tag = soup.find('h1')
    if title_tag:
        recipe['title'] = title_tag.text.strip()
    else:
        recipe['title'] = 'No title found'
    
    # Extracting hero banner image URL
    hero_image_div = soup.find('div', attrs={'data-test-id': 'recipe-hero-image'})
    if hero_image_div:
        hero_image_tag = hero_image_div.find('img')
        recipe['hero_image_url'] = hero_image_tag['src'] if hero_image_tag else ''
    else:
        recipe['hero_image_url'] = ''
    
    # Extracting ingredients
    ingredients_section = soup.find('div', attrs={'data-test-id': 'ingredients-list'})
    if ingredients_section:
        ingredients = ingredients_section.find_all('div', attrs={'data-test-id': 'ingredient-item-shipped'})
        recipe['ingredients'] = []
        for ingredient in ingredients:
            name = ingredient.find('p', class_='sc-9394dad-0 eERBYk').text.strip()
            amount = ingredient.find('p', class_='sc-9394dad-0 cJeggo').text.strip()
            
            image_tag = ingredient.find('img')
            image_url = image_tag['src'] if image_tag else ''
            recipe['ingredients'].append({
                'name': name,
                'unit': amount,
                'image_url': image_url
            })
    else:
        recipe['ingredients'] = []

    # Extracting instructions
    instructions_section = soup.find('div', attrs={'data-test-id': 'instructions'})
    if instructions_section:
        instructions = instructions_section.find_all('div', attrs={'data-test-id': 'instruction-step'})
        recipe['instructions'] = []
        for instruction in instructions:
            step_text = instruction.find('span', class_='sc-9394dad-0 FSngy').text.strip()
            image_tag = instruction.find('img')
            image_url = image_tag['src'] if image_tag else ''
            recipe['instructions'].append({
                'text': step_text,
                'image_url': image_url
            })
    else:
        recipe['instructions'] = []

    return recipe

# Main script
def main(limit=10):
    main_page_html = get_html(base_url + '/recipes/most-popular-recipes')
    category_links = get_category_links(main_page_html)
    
    recipes = []
    scraped_titles = set()
    count = 0

    for tag, category_url in category_links:
        print(f"Processing category page: {tag}")
        try:
            category_html = get_html(category_url)
            recipe_links = get_recipe_links(category_html)

            for link in recipe_links:
                if count >= limit:
                    break
                try:
                    recipe = scrape_recipe(link, tag)
                    if recipe['title'] not in scraped_titles:
                        recipes.append(recipe)
                        scraped_titles.add(recipe['title'])
                        count += 1
                        print(f"Scraped recipe: {recipe['title']} from {tag}")
                    else:
                        print(f"Skipped duplicate recipe: {recipe['title']}")
                except Exception as e:
                    print(f"Error scraping {link}: {e}")

            if count >= limit:
                break

        except Exception as e:
            print(f"Error fetching category page {category_url}: {e}")

    # Output recipes as JSON
    with open('recipes.json', 'w') as f:
        json.dump(recipes, f, indent=4)

    print("Recipes have been saved to recipes.json")

if __name__ == "__main__":
    main(limit=10)  # You can change the limit value here for testing
