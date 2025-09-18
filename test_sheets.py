# test_sheets.py (for testing)
from sheets_integration.sheets_client import TradingJournalSheets


# Test the sheets integration
def test_sheets_setup():
    journal = TradingJournalSheets()

    # Create a new journal (you'll do this once)
    spreadsheet_id = journal.create_trading_journal("My AI Trading Journal")

    # Test writing a sample trade
    sample_trade = {
        "date": "2024-01-15",
        "symbol": "TEST",
        "entry_price": 100.0,
        "exit_price": 105.0,
        "quantity": 100,
        "pnl_dollar": 500.0,
        "scale_number": "1/1",
    }

    journal.write_trade_record(sample_trade)


if __name__ == "__main__":
    test_sheets_setup()
