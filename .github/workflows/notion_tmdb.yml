name: Update Notion with TMDb Data

on:
  schedule:
    - cron: '0 * * * *'  # Run every hour
  workflow_dispatch:  # Allow manual triggering

jobs:
  update-notion:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.x'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests notion-client google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client gspread

      - name: Decode Google Sheets credentials
        run: echo "${{ secrets.GOOGLE_SHEETS_CREDENTIALS_BASE64 }}" | base64 --decode > credentials.json

      - name: Run script
        env:
          TMDB_API_KEY: ${{ secrets.TMDB_API_KEY }}
          NOTION_API_KEY: ${{ secrets.NOTION_API_KEY }}
          NOTION_DATABASE_ID: ${{ secrets.NOTION_DATABASE_ID }}
          SPREADSHEET_ID: ${{ secrets.SPREADSHEET_ID }}
        run: python script.py
