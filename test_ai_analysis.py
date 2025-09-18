# test_ai_analysis.py
from utils.csv_parser import WebullTradeParser
from ai_analyst.trade_analyzer import TradeAnalyzer


def test_ai_analysis():
    print("Testing AI Trade Analysis...")

    # Parse trades
    parser = WebullTradeParser()
    parser.parse_webull_csv("Webull_Orders_Records.csv")
    trades = parser.match_trades_with_scaling()

    if not trades:
        print("No trades to analyze")
        return

    # Create AI analyzer
    analyzer = TradeAnalyzer()

    # Analyze first trade with sample voice input
    sample_voice_input = """
    I entered EVTV because I saw it gapping up with volume. 
    The setup looked good but I got in too quick without waiting for confirmation. 
    Market was choppy this morning and I was feeling impatient after missing some moves yesterday. 
    Should have waited for a better entry or used a smaller position size.
    """

    print(f"\nAnalyzing {trades[0]['symbol']} trade...")
    analysis = analyzer.analyze_trade(trades[0], sample_voice_input)

    print("AI ANALYSIS:")
    print(analysis["ai_analysis"])
    print(f"\nTRADE GRADE: {analysis['trade_grade']}")

    # Analyze overall session
    print(f"\n" + "=" * 50)
    print("SESSION ANALYSIS:")
    session_analysis = analyzer.analyze_trading_session(trades)
    print(session_analysis)


if __name__ == "__main__":
    test_ai_analysis()
