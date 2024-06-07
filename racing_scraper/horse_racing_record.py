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

# Function to scrape race records from the horse detail page
def get_race_records(horse_url):
    print(f"Fetching details from URL: {horse_url}")
    response = requests.get(horse_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    race_records = []

    # Extract horse number and horse name
    horse_number = horse_url.split('HorseId=')[-1]
    horse_name_tag = soup.find('span', class_='title_text')
    horse_name = horse_name_tag.text.strip().split('(')[0].strip() if horse_name_tag else ''

    table = soup.find('table', class_='bigborder', width="1000")
    if table:
        rows = table.find_all('tr', bgcolor=True)
        for row in rows:
            columns = row.find_all('td', class_='htable_eng_text')
            if len(columns) == 19:  # Make sure the row contains race data
                racecourse_track_course = columns[3].get_text(strip=True).split(' / ')
                course = racecourse_track_course[2] if len(racecourse_track_course) > 2 else ''
                if course.startswith('"') and course.endswith('"'):
                    course = course[1:-1]

                race_record = {
                    'Horse Number': horse_number,
                    'Horse Name': horse_name,
                    'Race Index': columns[0].get_text(strip=True),
                    'Placing': columns[1].get_text(strip=True),
                    'Date': columns[2].get_text(strip=True),
                    'Racecourse': racecourse_track_course[0] if len(racecourse_track_course) > 0 else '',
                    'Track': racecourse_track_course[1] if len(racecourse_track_course) > 1 else '',
                    'Course': course,
                    'Distance': columns[4].get_text(strip=True),
                    'Going': columns[5].get_text(strip=True),
                    'Race Class': columns[6].get_text(strip=True),
                    'Draw': columns[7].get_text(strip=True),
                    'Rating': columns[8].get_text(strip=True),
                    'Trainer': columns[9].find('a')['href'].split('TrainerId=')[-1].split('&')[0] if columns[9].find('a') else columns[9].get_text(strip=True),
                    'Jockey': columns[10].find('a')['href'].split('JockeyId=')[-1].split('&')[0] if columns[10].find('a') else columns[10].get_text(strip=True),
                    'LBW': columns[11].get_text(strip=True),
                    'Win Odds': columns[12].get_text(strip=True),
                    'Actual Weight': columns[13].get_text(strip=True),
                    'Finish Time': columns[15].get_text(strip=True),
                    'Declared Horse Weight': columns[16].get_text(strip=True),
                }

                running_positions = columns[14].get_text(strip=True).split()
                for i in range(5):
                    if i < len(running_positions):
                        race_record[f'Running Position{i + 1}'] = running_positions[i]
                    else:
                        race_record[f'Running Position{i + 1}'] = ''

                # Handle gear field
                gears = ["B", "BO", "CC", "CP", "CO", "E", "H", "P", "PC", "PS", "SB", "SR", "TT", "V", "VO", "XB"]
                gear_variances = [f"{gear}{suffix}" for gear in gears for suffix in ['', '1', '2', '-']]

                gear_values = columns[17].get_text(strip=True).split('/')
                for variance in gear_variances:
                    race_record[variance] = variance in gear_values

                race_records.append(race_record)

    return race_records

# Main function to scrape all race records and save to CSV
def main():
    base_url = 'https://racing.hkjc.com/racing/information/english/Horse/SelectHorsebyChar.aspx?ordertype='
    index_pages = [f"{base_url}{chr(i)}" for i in range(ord('A'), ord('Z') + 1)]

    all_race_records = []
    horse_count = 0
    max_horses = 10
    fetched_urls = set()

    for index_page in index_pages:
        horse_links = get_horse_links(index_page)
        for horse_link in horse_links:
            if horse_count >= max_horses:
                break
            if horse_link not in fetched_urls:
                race_records = get_race_records(horse_link)
                if race_records:
                    all_race_records.extend(race_records)
                    horse_count += 1
                fetched_urls.add(horse_link)
                time.sleep(1)  # To prevent overwhelming the server
        if horse_count >= max_horses:
            break

    if all_race_records:
        keys = all_race_records[0].keys()

        with open('race_records.csv', 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(all_race_records)

if __name__ == "__main__":
    main()
