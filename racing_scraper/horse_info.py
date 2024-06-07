import requests
from bs4 import BeautifulSoup
import csv
import time

# Function to get the horse detail page links from an index page
def get_horse_links(index_url):
    response = requests.get(index_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    horse_links = []
    tables = soup.find_all('table', class_='bigborder')
    if len(tables) > 1:
        table = tables[1]  # Select the second table
        links = table.find_all('a', href=True)
        for link in links:
            horse_links.append('https://racing.hkjc.com' + link['href'])
    return horse_links

# Helper function to extract text from a specific label
def get_value(soup, label):
    for td in soup.find_all('td'):
        if label in td.get_text():
            next_td = td.find_next_sibling('td')
            if next_td:
                value_td = next_td.find_next_sibling('td')
                if value_td:
                    return value_td.get_text(strip=True)
    return ''

# Helper function to extract the trainer ID from the <a> tag
def get_trainer_id(soup):
    for td in soup.find_all('td'):
        if 'Trainer' in td.get_text():
            next_td = td.find_next_sibling('td')
            if next_td:
                value_td = next_td.find_next_sibling('td')
                if value_td:
                    a_tag = value_td.find('a')
                    if a_tag and 'href' in a_tag.attrs:
                        return a_tag['href'].split('TrainerId=')[-1]
    return ''

# Function to scrape horse details from the horse detail page
def get_horse_details(horse_url):
    print(f"Fetching details from URL: {horse_url}")
    response = requests.get(horse_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    details = {}

    try:
        horse_name_id = soup.find('span', class_='title_text').text.strip().split('(')
        details['Horse Name'] = horse_name_id[0].strip()
        details['Horse Id'] = horse_name_id[1].strip(')')
    except AttributeError:
        print(f"Error: Unable to find horse name and ID for URL: {horse_url}")
        return None

    country_age = get_value(soup, 'Country of Origin / Age')
    if country_age:
        details['Country of Origin'], details['Age'] = [item.strip() for item in country_age.split('/')]
    else:
        details['Country of Origin'] = ''
        details['Age'] = ''

    colour_sex = get_value(soup, 'Colour / Sex')
    if colour_sex:
        parts = [item.strip() for item in colour_sex.split('/')]
        details['Sex'] = parts[-1]
        details['Colour'] = ' | '.join(parts[:-1])
    else:
        details['Colour'] = ''
        details['Sex'] = ''

    details['Import Type'] = get_value(soup, 'Import Type')
    details['Season Stakes*'] = get_value(soup, 'Season Stakes*')
    details['Total Stakes*'] = get_value(soup, 'Total Stakes*')
    details['No. of 1-2-3-Starts*'] = get_value(soup, 'No. of 1-2-3-Starts*')
    details['No. of starts in past 10 race meetings'] = get_value(soup, 'No. of starts in past 10race meetings')

    stable_location_arrival = get_value(soup, 'Current Stable Location(Arrival Date)')
    if stable_location_arrival:
        location_date = stable_location_arrival.split('(')
        if len(location_date) > 1:
            details['Current Stable Location'] = location_date[0].strip()
            details['Arrival Date'] = location_date[1].strip(')')
        else:
            details['Current Stable Location'] = stable_location_arrival.strip()
            details['Arrival Date'] = ''
    else:
        details['Current Stable Location'] = ''
        details['Arrival Date'] = ''

    details['Import Date'] = get_value(soup, 'Import Date')
    details['Trainer'] = get_trainer_id(soup)
    details['Owner'] = get_value(soup, 'Owner')
    details['Current Rating'] = get_value(soup, 'Current Rating')
    details['Start of Season Rating'] = get_value(soup, 'Start ofSeason Rating')
    details['Sire'] = get_value(soup, 'Sire')
    details['Dam'] = get_value(soup, 'Dam')
    details['Dam\'s Sire'] = get_value(soup, 'Dam\'s Sire')

    # Extracting same sire options
    same_sire_select = soup.find('select', id='SameSire')
    if same_sire_select:
        same_sire = [option.text.strip() for option in same_sire_select.find_all('option')]
        details['Same Sire'] = ' | '.join(same_sire)
    else:
        details['Same Sire'] = ''

    return details

# Main function to scrape all horses and save to CSV
def main():
    base_url = 'https://racing.hkjc.com/racing/information/english/Horse/SelectHorsebyChar.aspx?ordertype='
    index_pages = [f"{base_url}{chr(i)}" for i in range(ord('A'), ord('Z') + 1)]

    all_horses = []
    horse_count = 0
    max_horses = 10000
    fetched_urls = set()

    for index_page in index_pages:
        horse_links = get_horse_links(index_page)
        for horse_link in horse_links:
            if horse_count >= max_horses:
                break
            if horse_link not in fetched_urls:
                horse_details = get_horse_details(horse_link)
                if horse_details:
                    all_horses.append(horse_details)
                    horse_count += 1
                fetched_urls.add(horse_link)
                time.sleep(1)  # To prevent overwhelming the server
        if horse_count >= max_horses:
            break

    if all_horses:
        keys = all_horses[0].keys()

        with open('horses.csv', 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(all_horses)

if __name__ == "__main__":
    main()
