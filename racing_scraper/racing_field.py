import requests
from bs4 import BeautifulSoup
import pandas as pd

# Base URL for the starting page
base_url = "https://racing.hkjc.com/racing/information/English/racing/LocalResults.aspx"

# Function to get the race dates
def get_race_dates():
    response = requests.get(base_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    select_tag = soup.find('select', {'id': 'selectId'})
    options = select_tag.find_all('option')
    race_dates = [option['value'] for option in options if option['value']]
    return race_dates

# Function to get the race URLs for a specific date
def get_race_urls(date):
    race_date_url = f"https://racing.hkjc.com/racing/information/English/Racing/LocalResults.aspx?RaceDate={date.replace('/', '%2F')}"
    response = requests.get(race_date_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    race_urls = [race_date_url]

    table = soup.find('table', {'class': 'f_fs12 js_racecard'})
    if table:
        links = table.find_all('a', href=True)
        for link in links:
            race_url = f"https://racing.hkjc.com{link['href']}"
            race_urls.append(race_url)

    return race_urls

# Function to extract field information from the race tab
def extract_field_info(table):
    field_info = {
        'race_index': '',
        'class_summary': '',
        'class': '',
        'distance': '',
        'rnumber1': '',
        'rnumber2': '',
        'rc': '',
        'going': '',
        'track': '',
        'course': '',
        'times': ['', '', '', '', ''],
        'sectional_times': ['', '', '', '', '']
    }
    
    # Extract race index from thead
    try:
        race_index_text = table.find('thead').find('tr').find('td').text.strip()
        race_index_parts = race_index_text.split(' ')
        if len(race_index_parts) > 1:
            field_info['race_index'] = race_index_parts[-1].strip('()')
    except IndexError:
        field_info['race_index'] = ""
    print(f"Extracted race_index: {field_info['race_index']}")

    rows = table.find('tbody').find_all('tr')

    # Extract class and distance information from class summary
    try:
        class_distance_parts = field_info['class_summary'].split('-')
        field_info['class'] = class_distance_parts[0].strip().split()[1]
    except (IndexError, ValueError):
        field_info['class'] = ""
    try:
        field_info['distance'] = class_distance_parts[1].strip().split()[0].replace('M', '')
    except (IndexError, ValueError):
        field_info['distance'] = ""
    try:
        field_info['rnumber1'] = class_distance_parts[2].replace('(', '').strip()
        field_info['rnumber2'] = class_distance_parts[3].strip(')')
    except (IndexError, ValueError):
        field_info['rnumber1'] = field_info['rnumber2'] = ""
    print(f"Extracted class: {field_info['class']}, distance: {field_info['distance']}, rnumber1: {field_info['rnumber1']}, rnumber2: {field_info['rnumber2']}")


    # Extract RC
    try:
        field_info['rc'] = rows[2].find('td').text.strip()
    except IndexError:
        field_info['rc'] = ""
    print(f"Extracted rc: {field_info['rc']}")

    # Extract going
    try:
        field_info['going'] = rows[1].find_all('td')[2].text.strip()
    except IndexError:
        field_info['going'] = ""
    print(f"Extracted going: {field_info['going']}")

    # Extract track and course
    try:
        track_course_text = rows[2].find_all('td')[2].text.strip()
        track_course_parts = track_course_text.split('-')
        field_info['track'] = track_course_parts[0].strip()
        field_info['course'] = track_course_parts[1].strip().replace('"', '')
    except (IndexError, ValueError):
        field_info['track'] = field_info['course'] = ""
    print(f"Extracted track: {field_info['track']}, course: {field_info['course']}")

    # Extract times
    try:
        times = [col.text.strip().replace('(', '').replace(')', '') for col in rows[3].find_all('td')[2:]]
        field_info['times'] = (times + [""] * 5)[:5]
    except IndexError:
        field_info['times'] = [""] * 5
    print(f"Extracted times: {field_info['times']}")

    # Extract sectional times
    try:
        sectional_times = [col.text.strip().split()[0] for col in rows[4].find_all('td')[2:]]
        field_info['sectional_times'] = (sectional_times + [""] * 5)[:5]
    except IndexError:
        field_info['sectional_times'] = [""] * 5
    print(f"Extracted sectional times: {field_info['sectional_times']}")

    return field_info

# Function to scrape field information from a race URL
def scrape_field_info(url, date, race_no):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    race_tab = soup.find('div', {'class': 'race_tab'})

    if not race_tab:
        print(f"No field information table found for {url}")
        return []

    table = race_tab.find('table')
    if table:
        field_info = extract_field_info(table)
        return [[date, race_no, field_info['race_index'], field_info['class'], field_info['distance'], field_info['rnumber1'], field_info['rnumber2'], field_info['rc'], field_info['going'], field_info['track'], field_info['course'], field_info['class_summary']] + field_info['times'] + field_info['sectional_times']]
    else:
        print(f"No table found in race tab for {url}")
        return []

# Main function to get and save all field information data to CSV
def main():
    all_field_data = []
    race_dates = get_race_dates()
    url_count = 0

    for date in race_dates:
        race_urls = get_race_urls(date)
        for i, url in enumerate(race_urls):
            if url_count >= 10:  # Limit to the first 10 URLs
                break
            race_no = i + 1  # Race number starts from 1
            print(f"Scraping {url}...")
            field_data = scrape_field_info(url, date, race_no)
            all_field_data.extend(field_data)
            url_count += 1
        if url_count >= 10:
            break

    # Save the data to a CSV file
    if all_field_data:
        columns = ["Race date", "Race number", "Race index", "Class", "Distance", "RNumber1", "RNumber2", "RC", "Going", "Track", "Course", "ClassSummary",
                   "Time1", "Time2", "Time3", "Time4", "Time5", 
                   "Sectional Time1", "Sectional Time2", "Sectional Time3", "Sectional Time4", "Sectional Time5"]
        df = pd.DataFrame(all_field_data, columns=columns)
        df.to_csv('field_information.csv', index=False)
        print("Data saved to field_information.csv")
    else:
        print("No field data found.")

if __name__ == "__main__":
    main()
