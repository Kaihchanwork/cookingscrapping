import requests
from bs4 import BeautifulSoup
import json

def get_html(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to retrieve page: {url}")
        return None

def get_category_links(base_url):
    html = get_html(base_url + '/recipes/most-popular-recipes')
    soup = BeautifulSoup(html, 'html.parser')
    category_div = soup.find('div', {'data-test-id': 'recipes|world-cuisines-tags'})
    if not category_div:
        print("Category div not found")
        return []
    
    links = category_div.find_all('a', class_='sc-9394dad-0 cQbWbr')
    category_urls = [{'tag': link.text.strip(), 'url': base_url + link['href'] + '?page=1000'} for link in links]
    return category_urls

def get_recipe_links(category_url):
    html = get_html(category_url)
    if not html:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    divs = soup.find_all('div', {'data-test-id': lambda x: x and x.startswith('recipe-card-')})
    recipe_urls = []
    for div in divs:
        link = div.find('a', class_='sc-9394dad-0 cQbWbr')
        if link:
            recipe_urls.append(link['href'])
    return recipe_urls

def scrape_recipe(recipe_url, tag):
    recipe_data = {'tag': tag, 'url': recipe_url}
    html = get_html(recipe_url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract title
    title_tag = soup.find('h1')
    recipe_data['title'] = title_tag.text.strip() if title_tag else 'No title found'
    
    # Extract hero image
    hero_image_div = soup.find('div', {'data-test-id': 'recipe-hero-image'})
    if hero_image_div:
        hero_image = hero_image_div.find('img')
        recipe_data['hero_image_url'] = hero_image['src'] if hero_image else ''
    else:
        recipe_data['hero_image_url'] = ''
    
    # Extract ingredients
    ingredients_section = soup.find('div', {'class': 'ceEdmx'})
    recipe_data['ingredients'] = []
    if ingredients_section:
        ingredients = ingredients_section.find_all('div', {'data-test-id': 'ingredient-item-shipped'})
        for ingredient in ingredients:
            name_tag = ingredient.find('p', class_='sc-9394dad-0 eERBYk')
            unit_tag = ingredient.find('p', class_='sc-9394dad-0 cJeggo')
            #image_div = ingredient.find('div', class_='gCQsju')
            #image_url = ''
            #if image_div:
            #    img_tag = image_div.find('img')
            #    image_url = img_tag['src'] if img_tag else ''
            img_tag = ingredient.find('img')
            image_url = img_tag['src'] if img_tag else ''
            if not image_url:
                    print(f"Log: Image src found in <div> with class 'gCQsju' for ingredient: {name_tag.text.strip() if name_tag else ''} is {img_tag['src'] if img_tag else 'No image tag found'}")
            unit_text = unit_tag.text.strip() if unit_tag else ''
            unit_text = unit_text.replace('\u00bd', '0.5')  # Replace "½" with "0.5"
            unit_text = unit_text.replace('\u00bc', '0.25')  # Replace "¼" with "0.25"
            recipe_data['ingredients'].append({
                'name': name_tag.text.strip() if name_tag else '',
                'unit': unit_text,
                'image_url': image_url
            })

    # Extract instructions
    instructions_section = soup.find('div', {'data-test-id': 'instructions'})
    recipe_data['instructions'] = []
    if instructions_section:
        steps = instructions_section.find_all('div', {'data-test-id': 'instruction-step'})
        for step in steps:
            step_text_tag = step.find('span', class_='sc-9394dad-0 FSngy')
            img_tag = step.find('img')
            step_text = step_text_tag.text.strip() if step_text_tag else ''
            image_url = img_tag['src'] if img_tag else ''
            recipe_data['instructions'].append({
                'text': step_text,
                'image_url': image_url
            })

    return recipe_data

def main():
    base_url = 'https://www.hellofresh.com'
    category_links = get_category_links(base_url)

    scraped_data = []
    count = 0
    limit = 10  # Limit the number of recipes to scrape

    for category in category_links:
        tag = category['tag']
        print(f"Processing category: {tag}")
        recipe_links = get_recipe_links(category['url'])
        
        for link in recipe_links:
            if count >= limit:
                break
            full_link = base_url + link if link.startswith('/') else link
            recipe = scrape_recipe(full_link, tag)
            if recipe:
                scraped_data.append(recipe)
                count += 1
                print(f"Scraped recipe: {recipe['title']} from {tag}")

    # Output the scraped data to a JSON file
    with open('scraped_recipes.json', 'w') as f:
        json.dump(scraped_data, f, indent=4)

if __name__ == '__main__':
    main()
