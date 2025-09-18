# Create file: sheets_integration/simple_sheets.py
import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class SimpleTradingJournalSheets:
    def __init__(self):
        self.SCOPES = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
        ]
        self.service = None
        self.spreadsheet_id = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate using OAuth - opens browser once, saves token"""
        creds = None

        # Check for saved token
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists("oauth_credentials.json"):
                    print("❌ oauth_credentials.json not found!")
                    print("📋 Download OAuth credentials from Google Cloud Console")
                    print(
                        "   Credentials → Create Credentials → OAuth Client ID → Desktop App"
                    )
                    return

                flow = InstalledAppFlow.from_client_secrets_file(
                    "oauth_credentials.json", self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)

        self.service = build("sheets", "v4", credentials=creds)
        print("✅ Successfully authenticated with Google Sheets")

    def create_trading_journal(self, spreadsheet_name="AI Trading Journal"):
        """Create a new trading journal spreadsheet"""
        if not self.service:
            print("❌ Authentication failed")
            return None

        try:
            # Create spreadsheet
            spreadsheet_body = {
                "properties": {"title": spreadsheet_name},
                "sheets": [
                    {
                        "properties": {
                            "title": "Trade Log",
                            "gridProperties": {"rowCount": 1000, "columnCount": 20},
                        }
                    },
                    {"properties": {"title": "Daily Summary"}},
                ],
            }

            result = self.service.spreadsheets().create(body=spreadsheet_body).execute()
            self.spreadsheet_id = result["spreadsheetId"]

            print(f"✅ Created trading journal: {spreadsheet_name}")
            print(f"📊 Spreadsheet ID: {self.spreadsheet_id}")
            print(
                f"🔗 URL: https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"
            )

            # Set up headers
            self._setup_headers()

            return self.spreadsheet_id

        except HttpError as e:
            print(f"❌ Failed to create spreadsheet: {e}")
            return None

    def _setup_headers(self):
        """Set up the column headers"""
        headers = [
            "Date",
            "Symbol",
            "Company_Name",
            "Entry_Price",
            "Entry_Time",
            "Exit_Price",
            "Exit_Time",
            "Quantity",
            "PnL_Dollar",
            "PnL_Percent",
            "Duration_Minutes",
            "Scale_Number",
            "Position_Type",
            "Entry_Reason",
            "Exit_Reason",
            "Emotional_State",
            "Market_Context",
            "Lessons_Learned",
            "AI_Analysis",
            "Trade_Grade",
        ]

        try:
            # Write headers to first row
            range_name = "Trade Log!A1:T1"
            body = {"values": [headers]}

            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption="RAW",
                body=body,
            ).execute()

            # Format headers (make them bold and blue)
            format_body = {
                "requests": [
                    {
                        "repeatCell": {
                            "range": {
                                "sheetId": 0,
                                "startRowIndex": 0,
                                "endRowIndex": 1,
                                "startColumnIndex": 0,
                                "endColumnIndex": len(headers),
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

            print("✅ Headers set up with formatting")

        except HttpError as e:
            print(f"⚠️ Headers setup failed: {e}")

    def write_trade_record(self, trade_data):
        """Write a single trade record"""
        if not self.spreadsheet_id:
            print("❌ No spreadsheet. Create one first.")
            return False

        try:
            # Find next empty row
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=self.spreadsheet_id, range="Trade Log!A:A")
                .execute()
            )

            values = result.get("values", [])
            next_row = len(values) + 1

            # Prepare row data
            row_data = [
                trade_data.get("date", ""),
                trade_data.get("symbol", ""),
                trade_data.get("company_name", ""),
                trade_data.get("entry_price", ""),
                trade_data.get("entry_time", ""),
                trade_data.get("exit_price", ""),
                trade_data.get("exit_time", ""),
                trade_data.get("quantity", ""),
                trade_data.get("pnl_dollar", ""),
                trade_data.get("pnl_percent", ""),
                trade_data.get("duration_minutes", ""),
                trade_data.get("scale_number", ""),
                trade_data.get("position_type", ""),
                trade_data.get("entry_reason", ""),
                trade_data.get("exit_reason", ""),
                trade_data.get("emotional_state", ""),
                trade_data.get("market_context", ""),
                trade_data.get("lessons_learned", ""),
                trade_data.get("ai_analysis", ""),
                trade_data.get("trade_grade", ""),
            ]

            # Write the data
            range_name = f"Trade Log!A{next_row}:T{next_row}"
            body = {"values": [row_data]}

            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            ).execute()

            print(f"✅ Trade record written to row {next_row}")
            return True

        except HttpError as e:
            print(f"❌ Failed to write trade: {e}")
            return False
