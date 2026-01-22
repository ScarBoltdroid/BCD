import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
current_year = 2026

def stage_scraper(short_url):
    url = "https://www.procyclingstats.com/" + short_url
    scraper = cloudscraper.create_scraper(browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)
    response = scraper.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 1. Find the div that has the text "Classification:"
    # Note: PCS often has a space after "Classification: "
    stage_tables = soup.find_all('table')
    for table in stage_tables:
        if "Date" in table.get_text():
            stage_table = table
            break
    data = []
    headers = [th.get_text(strip=True) for th in table.find_all('th')]
    test_data = []
    for tr in stage_table.find_all('tr')[0:]:  # Skip the header row
        cells = tr.find_all('td')
        if not cells:
            continue
        
        row_data = []
        for td in cells:
            # Check if this is the ridername cell
            if len(td.find_all('a')) > 0:
                # Only extract text from the <a> tag
                stage = td.find('a')
                stage_link = stage.get('href')
                row_data.append(stage_link if stage_link else "")
            else:
                # For other cells, just get the normal text
                text = td.get_text(strip=True)
                try:
                    formatted_date = datetime.strptime(text, "%d/%m").replace(year=current_year)
                    date = formatted_date.strftime("%Y-%m-%d")
                    row_data.append(date)
                except ValueError:
                    row_data.append(text)
        data.append(row_data)


    df = pd.DataFrame(data, columns=headers)
    df_filtered = df['Stage']
    stage_list = {}
    for s in df_filtered:
        if s:
            stage_list[s+"/"] = df.loc[df['Stage'] == s, 'Date'].item()

    return stage_list

def info_scraper(short_url):
    url = "https://www.procyclingstats.com/" + short_url
    scraper = cloudscraper.create_scraper(browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    })
    response = scraper.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 1. Find the div that has the text "Classification:"
    # Note: PCS often has a space after "Classification: "
    info_list = soup.find('ul', class_='list keyvalueList fs14')
    race_info = {}

    for li in info_list.find_all('li'):
        try:
            title = li.find('div', class_='title').get_text(strip=True).replace(':', '')
            value = li.find('div', class_='value').get_text(strip=True)
            race_info[title] = value
        except AttributeError:
            continue

    return race_info
    # Output: {'Classification': '1.UWT', 'Date': '02 February 2025', ...}

def result_scraper(url_short):
    url = 'https://www.procyclingstats.com/' + url_short + 'result'
    scraper = cloudscraper.create_scraper(browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    })
    response = scraper.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find('table', class_='results')

    if table:
        data = []
        # 1. Get the headers
        headers = [th.get_text(strip=True) for th in table.find_all('th')]

        # 2. Iterate through rows
        for tr in table.find_all('tr')[0:]:  # Skip the header row
            cells = tr.find_all('td')
            if not cells:
                continue
                
            row_data = []
            for td in cells:
                # Check if this is the ridername cell
                if 'ridername' in td.get('class', []):
                    # Only extract text from the <a> tag
                    rider = td.find('a')
                    rider_link = rider.get('href')
                    row_data.append(rider_link if rider_link else "")
                else:
                    # For other cells, just get the normal text
                    row_data.append(td.get_text(strip=True))
            
            data.append(row_data)

        


        df = pd.DataFrame(data, columns=headers)
        df_filtered = df[['Rnk', 'Rider']]

        return df_filtered
    

def gc_scraper(url_short):
    url = 'https://www.procyclingstats.com/' + url_short + 'gc/result'
    scraper = cloudscraper.create_scraper(browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    })
    response = scraper.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find('table', class_='hide_td14')

    if table:
        data = []
        # 1. Get the headers
        headers = [th.get_text(strip=True) for th in table.find_all('th')]

        # 2. Iterate through rows
        for tr in table.find_all('tr')[0:]:  # Skip the header row
            cells = tr.find_all('td')
            if not cells:
                continue
                
            row_data = []
            for td in cells:
                # Check if this is the ridername cell
                if 'ridername' in td.get('class', []):
                    # Only extract text from the <a> tag
                    rider = td.find('a')
                    rider_link = rider.get('href')
                    row_data.append(rider_link if rider_link else "")
                else:
                    # For other cells, just get the normal text
                    row_data.append(td.get_text(strip=True))
            
            data.append(row_data)

        


        df = pd.DataFrame(data, columns=headers)
        df_filtered = df[['Rnk', 'Rider']]

        return df_filtered
