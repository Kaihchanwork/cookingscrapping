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

# Function to extract ID from href
def extract_id(href, key):
    if key in href:
        return href.split(key + "=")[1].split("&")[0]
    return ""

# Function to scrape the race data from a race URL
def scrape_race_data(url, date, race_no):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table', {'class': 'f_tac table_bd draggable'})

    if not table:
        print(f"No results table found for {url}")
        return []

    race_data = []
    rows = table.find('tbody').find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        if len(cols) == 12:  # Ensure there are 12 columns as expected
            pla = cols[0].text.strip()
            horse_no = cols[1].text.strip()
            horse = cols[2].find('a')['href']
            horse_id = extract_id(horse, 'HorseId')
            jockey = cols[3].find('a')['href']
            jockey_id = extract_id(jockey, 'JockeyId')
            trainer = cols[4].find('a')['href']
            trainer_id = extract_id(trainer, 'TrainerId')
            act_wt = cols[5].text.strip()
            declar_horse_wt = cols[6].text.strip()
            dr = cols[7].text.strip()
            lbw = cols[8].text.strip()
            running_positions = cols[9].text.strip().replace('\n', ' ').split()
            running_positions = (running_positions + [""] * 5)[:5]  # Ensure there are 5 positions
            finish_time = cols[10].text.strip()
            win_odds = cols[11].text.strip()

            race_data.append([date, race_no, pla, horse_no, horse_id, jockey_id, trainer_id, act_wt, declar_horse_wt, dr, lbw] + running_positions + [finish_time, win_odds])

    if not race_data:
        print(f"No data found in results table for {url}")

    return race_data

# Main function to get and save all race data to CSV
def main():
    all_race_data = []
    race_dates = get_race_dates()
    url_count = 0

    for date in race_dates:
        race_urls = get_race_urls(date)
        for i, url in enumerate(race_urls):
            if url_count >= 20:  # Limit to the first 10 URLs
                break
            race_no = i + 1  # Race number starts from 1
            print(f"Scraping {url}...")
            race_data = scrape_race_data(url, date, race_no)
            all_race_data.extend(race_data)
            url_count += 1
        if url_count >= 20:
            break

    # Save the data to a CSV file
    if all_race_data:
        columns = ["date", "racing number", "pla.", "horse no.", "horse id", "jockey id", "trainer id", "Act. Wt.", "Declar. horse Wt.", "Dr.", "LBW", 
                   "Running Position 1", "Running Position 2", "Running Position 3", "Running Position 4", "Running Position 5", 
                   "Finish time", "Win Odds"]
        df = pd.DataFrame(all_race_data, columns=columns)
        df.to_csv('race_results.csv', index=False)
        print("Data saved to race_results.csv")
    else:
        print("No race data found.")

if __name__ == "__main__":
    main()
