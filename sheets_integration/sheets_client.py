# sheets_integration/sheets_client.py
# import json
# import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import GOOGLE_SHEETS_CONFIG, JOURNAL_COLUMNS


class TradingJournalSheets:
    def __init__(self, credentials_path="credentials.json"):
        """
        Initialize Google Sheets client for trading journal

        Args:
            credentials_path: Path to Google service account credentials JSON
        """
        self.credentials_path = credentials_path
        self.spreadsheet_id = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Sheets API"""
        try:
            # Load credentials from JSON file
            creds = Credentials.from_service_account_file(
                self.credentials_path, scopes=GOOGLE_SHEETS_CONFIG["scopes"]
            )

            # Build the service
            self.service = build("sheets", "v4", credentials=creds)
            print("✅ Successfully authenticated with Google Sheets")

        except FileNotFoundError:
            print(
                "❌ credentials.json not found. Please download from Google Cloud Console"
            )
            print(
                "📋 Instructions: https://developers.google.com/sheets/api/quickstart/python"
            )
        except Exception as e:
            print(f"❌ Authentication failed: {e}")

    def create_trading_journal_in_folder(
        self, folder_name="Trading Journal", spreadsheet_name=None
    ):
        """
        Create trading journal in a specific Drive folder
        """
        if not self.service:
            print("❌ Not authenticated. Cannot create spreadsheet.")
            return None

        if not spreadsheet_name:
            spreadsheet_name = GOOGLE_SHEETS_CONFIG["spreadsheet_name"]

        try:
            # First, find or create the folder
            drive_service = build(
                "drive", "v3", credentials=self.service._http.credentials
            )

            # Search for existing folder
            folder_query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
            folder_results = drive_service.files().list(q=folder_query).execute()

            if folder_results.get("files"):
                folder_id = folder_results["files"][0]["id"]
                print(f"✅ Found existing folder: {folder_name}")
            else:
                # Create folder
                folder_metadata = {
                    "name": folder_name,
                    "mimeType": "application/vnd.google-apps.folder",
                }
                folder = drive_service.files().create(body=folder_metadata).execute()
                folder_id = folder.get("id")
                print(f"✅ Created folder: {folder_name}")

            # Create spreadsheet in the folder
            spreadsheet_body = {
                "properties": {"title": spreadsheet_name},
                "sheets": [
                    {
                        "properties": {
                            "title": "Trade Log",
                            "gridProperties": {
                                "rowCount": 1000,
                                "columnCount": len(JOURNAL_COLUMNS),
                            },
                        }
                    },
                    {"properties": {"title": "Daily Summary"}},
                    {"properties": {"title": "Pattern Analysis"}},
                ],
            }

            # Create the spreadsheet
            result = self.service.spreadsheets().create(body=spreadsheet_body).execute()
            self.spreadsheet_id = result["spreadsheetId"]

            # Move spreadsheet to folder
            drive_service.files().update(
                fileId=self.spreadsheet_id, addParents=folder_id, removeParents="root"
            ).execute()

            print(f"✅ Created trading journal: {spreadsheet_name}")
            print(f"📊 Spreadsheet ID: {self.spreadsheet_id}")
            print(
                f"🔗 URL: https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"
            )

            # Set up the headers
            self._setup_trade_log_headers()

            return self.spreadsheet_id

        except HttpError as e:
            print(f"❌ Failed to create spreadsheet: {e}")
            return None

    def create_trading_journal(self, spreadsheet_name=None):
        """
        Create a new trading journal spreadsheet with proper formatting

        Returns:
            str: Spreadsheet ID if successful
        """
        if not self.service:
            print("❌ Not authenticated. Cannot create spreadsheet.")
            return None

        if not spreadsheet_name:
            spreadsheet_name = GOOGLE_SHEETS_CONFIG["spreadsheet_name"]

        try:
            # Create the spreadsheet
            spreadsheet_body = {
                "properties": {"title": spreadsheet_name},
                "sheets": [
                    {
                        "properties": {
                            "title": "Trade Log",
                            "gridProperties": {
                                "rowCount": 1000,
                                "columnCount": len(JOURNAL_COLUMNS),
                            },
                        }
                    },
                    {
                        "properties": {
                            "title": "Daily Summary",
                            "gridProperties": {"rowCount": 100, "columnCount": 10},
                        }
                    },
                    {
                        "properties": {
                            "title": "Pattern Analysis",
                            "gridProperties": {"rowCount": 50, "columnCount": 8},
                        }
                    },
                ],
            }

            result = self.service.spreadsheets().create(body=spreadsheet_body).execute()
            self.spreadsheet_id = result["spreadsheetId"]

            print(f"✅ Created trading journal: {spreadsheet_name}")
            print(f"📊 Spreadsheet ID: {self.spreadsheet_id}")
            print(
                f"🔗 URL: https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"
            )

            # Set up the headers and formatting
            self._setup_trade_log_headers()
            self._setup_daily_summary_headers()

            return self.spreadsheet_id

        except HttpError as e:
            print(f"❌ Failed to create spreadsheet: {e}")
            return None

    def _setup_trade_log_headers(self):
        """Set up headers and formatting for the Trade Log sheet"""

        # Write headers
        header_range = "Trade Log!A1:R1"  # Adjust based on number of columns
        header_values = [JOURNAL_COLUMNS]

        body = {"values": header_values}

        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=header_range,
            valueInputOption="RAW",
            body=body,
        ).execute()

        # Format headers (bold, background color)
        format_body = {
            "requests": [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": 0,  # Trade Log sheet
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": len(JOURNAL_COLUMNS),
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    "red": 0.2,
                                    "green": 0.6,
                                    "blue": 0.9,
                                },
                                "textFormat": {
                                    "foregroundColor": {
                                        "red": 1.0,
                                        "green": 1.0,
                                        "blue": 1.0,
                                    },
                                    "bold": True,
                                },
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat)",
                    }
                }
            ]
        }

        self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id, body=format_body
        ).execute()

        print("✅ Trade Log headers set up with formatting")

    # Continue in sheets_integration/sheets_client.py

    def write_trade_record(self, trade_data):
        """
        Write a single trade record to the Trade Log sheet

        Args:
            trade_data: Dictionary containing trade information
        """
        if not self.spreadsheet_id:
            print("❌ No spreadsheet ID. Create or connect to spreadsheet first.")
            return False

        try:
            # Find the next empty row
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=self.spreadsheet_id, range="Trade Log!A:A")
                .execute()
            )

            values = result.get("values", [])
            next_row = len(values) + 1  # +1 because sheets are 1-indexed

            # Prepare the row data in the correct order
            row_data = []
            for column in JOURNAL_COLUMNS:
                # Convert our trade_data keys to match column names
                value = trade_data.get(column.lower().replace("_", ""), "")
                row_data.append(value)

            # Write the data
            range_name = (
                f"Trade Log!A{next_row}:R{next_row}"  # Adjust column range as needed
            )
            body = {"values": [row_data]}

            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",  # This handles date/number formatting
                body=body,
            ).execute()

            print(f"✅ Trade record written to row {next_row}")
            return True

        except HttpError as e:
            print(f"❌ Failed to write trade record: {e}")
            return False

    def write_multiple_trades(self, trades_list):
        """
        Write multiple trade records at once (more efficient)

        Args:
            trades_list: List of trade dictionaries
        """
        if not trades_list:
            print("⚠️ No trades to write")
            return False

        try:
            # Find starting row
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=self.spreadsheet_id, range="Trade Log!A:A")
                .execute()
            )

            values = result.get("values", [])
            start_row = len(values) + 1

            # Prepare all rows
            all_rows = []
            for trade_data in trades_list:
                row_data = []
                for column in JOURNAL_COLUMNS:
                    value = trade_data.get(column.lower().replace("_", ""), "")
                    row_data.append(value)
                all_rows.append(row_data)

            # Write all at once
            end_row = start_row + len(all_rows) - 1
            range_name = f"Trade Log!A{start_row}:R{end_row}"

            body = {"values": all_rows}

            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            ).execute()

            print(
                f"✅ {len(trades_list)} trade records written to rows {start_row}-{end_row}"
            )
            return True

        except HttpError as e:
            print(f"❌ Failed to write multiple trades: {e}")
            return False

    def connect_to_existing_spreadsheet(self, spreadsheet_id):
        """Connect to an existing trading journal spreadsheet"""
        self.spreadsheet_id = spreadsheet_id
        print(f"✅ Connected to spreadsheet: {spreadsheet_id}")
