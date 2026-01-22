import streamlit as st
from curl_cffi import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# It is 2026
current_year = 2026

# Create a global session to reuse the browser fingerprint
session = requests.Session(impersonate="chrome124")

def get_soup(url_short):
    url = "https://www.procyclingstats.com/" + url_short
    try:
        # impersonate="chrome124" makes the request look like a real browser
        response = session.get(url, timeout=15)
        
        if response.status_code != 200:
            st.error(f"PCS blocked the request (Status {response.status_code}).")
            return None
            
        return BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

def stage_scraper(short_url):
    soup = get_soup(short_url)
    if not soup: return {}

    stage_tables = soup.find_all('table')
    stage_table = None
    for table in stage_tables:
        if "Date" in table.get_text():
            stage_table = table
            break
    
    if not stage_table: return {}

    data = []
    headers = [th.get_text(strip=True) for th in stage_table.find_all('th')]
    
    for tr in stage_table.find_all('tr'):
        cells = tr.find_all('td')
        if not cells: continue
        
        row_data = []
        for td in cells:
            if len(td.find_all('a')) > 0:
                stage = td.find('a')
                stage_link = stage.get('href')
                row_data.append(stage_link if stage_link else "")
            else:
                text = td.get_text(strip=True)
                try:
                    formatted_date = datetime.strptime(text, "%d/%m").replace(year=current_year)
                    row_data.append(formatted_date.strftime("%Y-%m-%d"))
                except ValueError:
                    row_data.append(text)
        data.append(row_data)

    df = pd.DataFrame(data, columns=headers)
    stage_list = {f"{s}/": df.loc[df['Stage'] == s, 'Date'].item() for s in df['Stage'] if s}
    return stage_list

def info_scraper(short_url):
    soup = get_soup(short_url)
    if not soup: return {}

    info_list = soup.find('ul', class_='list keyvalueList fs14')
    if not info_list: return {}

    race_info = {}
    for li in info_list.find_all('li'):
        title_div = li.find('div', class_='title')
        value_div = li.find('div', class_='value')
        if title_div and value_div:
            title = title_div.get_text(strip=True).replace(':', '')
            race_info[title] = value_div.get_text(strip=True)
    return race_info

def result_scraper(url_short):
    soup = get_soup(url_short + "result")
    if not soup: return pd.DataFrame()

    table = soup.find('table', class_='results')
    if not table: return pd.DataFrame()

    data = []
    headers = [th.get_text(strip=True) for th in table.find_all('th')]

    for tr in table.find_all('tr'):
        cells = tr.find_all('td')
        if not cells: continue
        row_data = [td.find('a').get('href') if 'ridername' in td.get('class', []) else td.get_text(strip=True) for td in cells]
        data.append(row_data)

    df = pd.DataFrame(data, columns=headers)
    return df[['Rnk', 'Rider']] if 'Rider' in df.columns else df

def gc_scraper(url_short):
    soup = get_soup(url_short + "gc/result")
    if not soup: return pd.DataFrame()

    table = soup.find('table', class_='hide_td14')
    if not table: return pd.DataFrame()

    data = []
    headers = [th.get_text(strip=True) for th in table.find_all('th')]

    for tr in table.find_all('tr'):
        cells = tr.find_all('td')
        if not cells: continue
        row_data = [td.find('a').get('href') if 'ridername' in td.get('class', []) else td.get_text(strip=True) for td in cells]
        data.append(row_data)

    df = pd.DataFrame(data, columns=headers)
    return df[['Rnk', 'Rider']] if 'Rider' in df.columns else df
