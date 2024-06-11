import os
import json
import requests
from bs4 import BeautifulSoup
import time

def get_html(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Failed to retrieve page: {url} with error: {e}")
        return None

def get_recipe_links_from_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data if isinstance(data, list) else []

def replace_fractions(text):
    fractions = {
        '\u00bd': '0.5',   # ½
        '\u00bc': '0.25',  # ¼
        '\u2153': '0.333', # ⅓
        '\u2154': '0.667', # ⅔
        '\u00be': '0.75',  # ¾
        '\u215b': '0.125', # ⅛
        '\u215c': '0.375', # ⅜
        '\u215d': '0.625', # ⅝
        '\u215e': '0.875'  # ⅞
    }
    for frac, dec in fractions.items():
        text = text.replace(frac, dec)
    return text

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
    hero_image = hero_image_div.find('img') if hero_image_div else None
    recipe_data['hero_image_url'] = hero_image['src'] if hero_image else ''
    
    # Extract ingredients
    ingredients_section = soup.find('div', {'class': 'ceEdmx'})
    recipe_data['ingredients'] = []
    if ingredients_section:
        ingredients = ingredients_section.find_all('div', {'data-test-id': 'ingredient-item-shipped'})
        for ingredient in ingredients:
            name_tag = ingredient.find('p', class_='sc-9394dad-0 eERBYk')
            unit_tag = ingredient.find('p', class_='sc-9394dad-0 cJeggo')
            img_tag = ingredient.find('img')
            image_url = img_tag['src'] if img_tag else ''
            unit_text = replace_fractions(unit_tag.text.strip()) if unit_tag else ''
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
            step_text = replace_fractions(step_text_tag.text.strip()) if step_text_tag else ''
            image_url = img_tag['src'] if img_tag else ''
            recipe_data['instructions'].append({
                'text': step_text,
                'image_url': image_url
            })

    return recipe_data

def main():
    directory = 'recipesjsonfolder'
    scraped_data = []
    count = 0
    limit = 10  # Limit the number of recipes to scrape
    seen_titles = set()  # Set to track seen titles

    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            tag = filename.replace('.json', '')
            file_path = os.path.join(directory, filename)
            recipe_links = get_recipe_links_from_file(file_path)
            
            print(f"Processing {len(recipe_links)} recipes in category: {tag}")
            
            for link in recipe_links:
                if count >= limit:
                    break
                recipe = scrape_recipe(link, tag)
                if recipe and recipe['title'] not in seen_titles:
                    scraped_data.append(recipe)
                    seen_titles.add(recipe['title'])
                    count += 1
                    print(f"Scraped recipe: {recipe['title']} from {tag}")

    # Output the scraped data to a JSON file
    with open('scraped_recipes.json', 'w') as f:
        json.dump(scraped_data, f, indent=4)

if __name__ == '__main__':
    main()
