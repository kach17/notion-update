import os
import requests
import json
import gspread
from google.oauth2.service_account import Credentials
from notion_client import Client
import base64

# Get API keys and database ID from environment variables
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

# Decode and save the Google Sheets credentials JSON
google_sheets_credentials_base64 = os.getenv('GOOGLE_SHEETS_CREDENTIALS_BASE64')
if google_sheets_credentials_base64 is None:
    raise ValueError("GOOGLE_SHEETS_CREDENTIALS_BASE64 environment variable is not set")

try:
    google_sheets_credentials_json = base64.b64decode(google_sheets_credentials_base64).decode('utf-8')
    with open('credentials.json', 'w') as f:
        f.write(google_sheets_credentials_json)
except Exception as e:
    raise ValueError(f"Error decoding or writing Google Sheets credentials: {e}")

# Initialize Notion client
notion = Client(auth=NOTION_API_KEY)

# Google Sheets API setup
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file('credentials.json', scopes=scopes)
client = gspread.authorize(creds)

def fetch_series_metadata(series_name):
    search_url = f'https://api.themoviedb.org/3/search/tv?api_key={TMDB_API_KEY}&query={series_name}'
    search_response = requests.get(search_url)
    search_data = search_response.json()

    if search_data['results']:
        series_id = search_data['results'][0]['id']
        details_url = f'https://api.themoviedb.org/3/tv/{series_id}?api_key={TMDB_API_KEY}'
        details_response = requests.get(details_url)
        details_data = details_response.json()
        
        return {
            'id': details_data['id'],
            'name': details_data['name'],
            'release_date': details_data['first_air_date'],
            'rating': details_data['vote_average'],
            'overview': details_data['overview'],
            'poster': f"https://image.tmdb.org/t/p/w500{details_data['poster_path']}",
            'backdrop': f"https://image.tmdb.org/t/p/w500{details_data['backdrop_path']}",
            'genres': [genre['name'] for genre in details_data['genres']]
        }
    return None

def add_series_to_notion(series_data, category):
    new_page = {
        'Name': {'title': [{'text': {'content': series_data['name']}}]},
        'Category': {'select': {'name': category}},
        'Release Date': {'date': {'start': series_data['release_date']}},
        'Rating': {'number': series_data['rating']},
        'Overview': {'rich_text': [{'text': {'content': series_data['overview']}}]},
        'Poster': {'url': series_data['poster']},
        'Backdrop': {'url': series_data['backdrop']},
        'TMDb ID': {'number': series_data['id']},
        'Genres': {'multi_select': [{'name': genre} for genre in series_data['genres']]}
    }
    try:
        response = notion.pages.create(parent={'database_id': NOTION_DATABASE_ID}, properties=new_page)
        print(f"Page created: {response['id']}")
    except Exception as e:
        print(f"Error creating page: {e}")

def read_series_from_sheet():
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    data = sheet.get_all_values()
    return [row[0] for row in data if row]

def read_last_processed_row():
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    try:
        last_row = int(sheet.cell(1, 2).value)
    except:
        last_row = 0
    return last_row

def write_last_processed_row(row_number):
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    sheet.update_cell(1, 2, row_number)

# Example usage
series_list = read_series_from_sheet()
last_processed_row = read_last_processed_row()
new_series_list = series_list[last_processed_row:]

category = 'Watched'  # Default category, modify as needed

for i, series_name in enumerate(new_series_list):
    series_data = fetch_series_metadata(series_name)
    if series_data:
        add_series_to_notion(series_data, category)
        write_last_processed_row(last_processed_row + i + 1)
    else:
        print(f'Series not found: {series_name}')
