import json
import gspread
import requests
from notion_client import Client
import os

# Load Google Sheets credentials
creds = json.loads(os.getenv("GOOGLE_SHEETS_JSON"))

# Authenticate with Google Sheets
client = gspread.service_account_from_dict(creds)
sheet = client.open_by_key(os.getenv("SHEET_ID")).sheet1

# Authenticate with Notion
notion = Client(auth=os.getenv("NOTION_API_KEY"))

# TMDb API Key
tmdb_api_key = os.getenv("TMDB_API_KEY")

# Fetch the last processed row from the Notion database (or a local file)
last_row_file = "last_row.txt"
try:
    with open(last_row_file, "r") as f:
        last_row = int(f.read().strip())
except FileNotFoundError:
    last_row = 0

# Fetch rows from the Google Sheet
rows = sheet.get_all_values()

# Process new rows
for idx, row in enumerate(rows[last_row:], start=last_row):
    series_name = row[0]
    
    # Fetch metadata from TMDb API
    response = requests.get(f"https://api.themoviedb.org/3/search/tv", params={
        "api_key": tmdb_api_key,
        "query": series_name
    })
    data = response.json()
    
    if data['results']:
        series_info = data['results'][0]
        title = series_info['name']
        overview = series_info['overview']
        release_date = series_info['first_air_date']
        rating = series_info['vote_average']
        poster_path = series_info['poster_path']
        
        # Prepare properties for Notion page creation
        page_properties = {
            "Name": {"title": [{"text": {"content": title}}]},
            "Overview": {"rich_text": [{"text": {"content": overview}}]},
            "Release Date": {"date": {"start": release_date}},
            "Rating": {"number": rating}
        }
        
        if poster_path:
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            page_properties["Poster"] = {"url": poster_url}
        
        # Create page in Notion database
        notion.pages.create(
            parent={"database_id": "9c8a112777c4485f86b7dfeb4362bd8b"},
            properties=page_properties
        )
    
    # Update the last processed row
    with open(last_row_file, "w") as f:
        f.write(str(idx + 1))
