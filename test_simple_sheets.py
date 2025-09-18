# test_simple_sheets.py
# import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


def test_simple_create():
    try:
        # Authenticate
        creds = Credentials.from_service_account_file("credentials.json")
        service = build("sheets", "v4", credentials=creds)

        # Try creating a very simple spreadsheet
        spreadsheet_body = {"properties": {"title": "Test Trading Journal"}}

        result = service.spreadsheets().create(body=spreadsheet_body).execute()
        spreadsheet_id = result["spreadsheetId"]

        print(f"✅ Success! Created spreadsheet: {spreadsheet_id}")
        print(f"🔗 URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")

        return True

    except Exception as e:
        print(f"❌ Error details: {e}")
        return False


if __name__ == "__main__":
    test_simple_create()
