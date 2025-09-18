# test_oauth_sheets.py
from sheets_integration.simple_sheets import SimpleTradingJournalSheets


def test_oauth_sheets():
    print("Testing OAuth Google Sheets integration...")

    # Create sheets client (will open browser for authentication)
    journal = SimpleTradingJournalSheets()

    # Create the trading journal
    spreadsheet_id = journal.create_trading_journal("My OAuth Trading Journal")

    if spreadsheet_id:
        # Test writing a sample trade
        sample_trade = {
            "date": "2024-01-15",
            "symbol": "TURB",
            "company_name": "Turbo Energy SA",
            "entry_price": 11.83,
            "entry_time": "09:06:21 EDT",
            "exit_price": 12.84,
            "exit_time": "09:25:15 EDT",
            "quantity": 1000,
            "pnl_dollar": 1010.0,
            "pnl_percent": 8.53,
            "duration_minutes": 19,
            "scale_number": "1/1",
            "position_type": "Full Exit",
            "entry_reason": "Breakout above resistance with volume",
            "exit_reason": "Target reached",
            "emotional_state": "Confident",
            "market_context": "Morning momentum",
            "ai_analysis": "Good setup execution",
            "trade_grade": "A",
        }

        journal.write_trade_record(sample_trade)
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed - couldn't create spreadsheet")


if __name__ == "__main__":
    test_oauth_sheets()
