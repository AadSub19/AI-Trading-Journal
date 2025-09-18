# test_csv_parser.py
from utils.csv_parser import WebullTradeParser


def test_csv_parsing():
    print("Testing Webull CSV Parser...")

    # Create parser instance
    parser = WebullTradeParser()

    # Parse your actual Webull CSV
    orders = parser.parse_webull_csv("Webull_Orders_Records.csv")

    if orders is not None:
        # Match trades with scaling support
        trades = parser.match_trades_with_scaling()

        # Display summary
        parser.display_trades_summary()

        print("\n✅ CSV parsing test completed!")
        print(f"📁 Ready to process {len(trades)} trades for voice input")

        return trades
    else:
        print("❌ CSV parsing failed")
        return []


if __name__ == "__main__":
    test_csv_parsing()
