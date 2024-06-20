import os
import requests
from notion_client import Client

# Get API keys and database ID from environment variables
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')

# Initialize Notion client
notion = Client(auth=NOTION_API_KEY)

def fetch_series_metadata(series_name):
    url = f'https://api.themoviedb.org/3/search/tv?api_key={TMDB_API_KEY}&query={series_name}'
    response = requests.get(url)
    data = response.json()
    if data['results']:
        series = data['results'][0]
        return {
            'name': series['name'],
            'release_date': series['first_air_date'],
            'rating': series['vote_average'],
            'overview': series['overview'],
            'poster': f"https://image.tmdb.org/t/p/w500{series['poster_path']}"
        }
    return None

def add_series_to_notion(series_data, category):
    new_page = {
        'Name': {'title': [{'text': {'content': series_data['name']}}]},
        'Category': {'select': {'name': category}},
        'Release Date': {'date': {'start': series_data['release_date']}},
        'Rating': {'number': series_data['rating']},
        'Overview': {'rich_text': [{'text': {'content': series_data['overview']}}]},
        'Poster': {'files': [{'type': 'external', 'name': 'poster', 'external': {'url': series_data['poster']}}]}
    }
    try:
        response = notion.pages.create(parent={'database_id': NOTION_DATABASE_ID}, properties=new_page)
        print(f"Page created: {response['id']}")
    except Exception as e:
        print(f"Error creating page: {e}")

# Example usage
series_name = 'Breaking Bad'
category = 'Watched'
series_data = fetch_series_metadata(series_name)
if series_data:
    add_series_to_notion(series_data, category)
else:
    print('Series not found.')
