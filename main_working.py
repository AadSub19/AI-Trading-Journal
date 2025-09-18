# main_working.py (Updated with Sheets export)
import streamlit as st
import pandas as pd
import os

# Import modules we know work
try:
    from utils.csv_parser import WebullTradeParser

    csv_parser_available = True
except ImportError as e:
    st.error(f"CSV Parser import failed: {e}")
    csv_parser_available = False

try:
    from ai_analyst.trade_analyzer import TradeAnalyzer

    ai_analyzer_available = True
except ImportError as e:
    st.error(f"AI Analyzer import failed: {e}")
    ai_analyzer_available = False

try:
    from sheets_integration.simple_sheets import SimpleTradingJournalSheets

    sheets_available = True
except ImportError as e:
    st.error(f"Sheets integration import failed: {e}")
    sheets_available = False

st.set_page_config(page_title="AI Trading Journal", page_icon="📊", layout="wide")


def main():
    st.title("📊 AI Trading Journal")
    st.markdown("*Automated trade analysis with AI insights*")

    if not csv_parser_available:
        st.error("CSV Parser not available. Check imports.")
        return

    # Initialize session state for analyzed trades
    if "analyzed_trades" not in st.session_state:
        st.session_state.analyzed_trades = []

    # File upload
    st.header("Upload Your Trading CSV")
    uploaded_file = st.file_uploader(
        "Upload Webull CSV file",
        type=["csv"],
        help="Export your orders from Webull and upload here",
    )

    if uploaded_file is not None:
        # Save uploaded file
        with open("temp_trades.csv", "wb") as f:
            f.write(uploaded_file.getvalue())

        # Parse trades
        parser = WebullTradeParser()

        with st.spinner("Parsing your trades..."):
            orders = parser.parse_webull_csv("temp_trades.csv")

        if orders is not None:
            trades = parser.match_trades_with_scaling()

            if trades:
                st.success(f"✅ Successfully parsed {len(trades)} trades!")

                # Display trade summary
                trades_df = pd.DataFrame(trades)

                # Key metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total P&L", f"${trades_df['pnl_dollar'].sum():.2f}")
                with col2:
                    st.metric("Win Rate", f"{(trades_df['pnl_dollar'] > 0).mean():.1%}")
                with col3:
                    st.metric(
                        "Avg Duration", f"{trades_df['duration_minutes'].mean():.1f}min"
                    )
                with col4:
                    st.metric("Total Trades", len(trades))

                # Display trades table
                st.subheader("Your Trades")
                display_cols = [
                    "symbol",
                    "entry_price",
                    "exit_price",
                    "pnl_dollar",
                    "pnl_percent",
                    "duration_minutes",
                    "entry_time",
                    "exit_time",
                ]
                st.dataframe(trades_df[display_cols], use_container_width=True)

                # Voice input section (text-based for now)
                st.subheader("Add Your Trading Commentary")
                st.write("Add your reasoning for each trade:")

                voice_inputs = {}
                for i, trade in enumerate(trades):
                    with st.expander(
                        f"Trade {i + 1}: {trade['symbol']} - ${trade['pnl_dollar']:+.2f}"
                    ):
                        st.write(
                            f"**Entry:** ${trade['entry_price']} at {trade['entry_time']}"
                        )
                        st.write(
                            f"**Exit:** ${trade['exit_price']} at {trade['exit_time']}"
                        )
                        st.write(f"**Duration:** {trade['duration_minutes']} minutes")

                        voice_input = st.text_area(
                            "Why did you enter and exit this trade?",
                            key=f"voice_{i}",
                            placeholder="I entered because... I exited because... I was feeling...",
                            height=100,
                        )

                        if voice_input.strip():
                            voice_inputs[i] = voice_input

                # AI Analysis
                if voice_inputs and ai_analyzer_available:
                    if st.button("🤖 Generate AI Analysis"):
                        with st.spinner("Analyzing trades with AI..."):
                            analyzer = TradeAnalyzer()

                            st.subheader("AI Analysis Results")

                            analyzed_trades = []
                            for i, trade in enumerate(trades):
                                voice_input = voice_inputs.get(i, "")

                                if voice_input:
                                    analysis = analyzer.analyze_trade(
                                        trade, voice_input
                                    )

                                    with st.expander(
                                        f"Trade {i + 1}: {trade['symbol']} - Grade: {analysis['trade_grade']}"
                                    ):
                                        col1, col2 = st.columns([1, 1])

                                        with col1:
                                            st.write("**Trade Details:**")
                                            st.write(
                                                f"P&L: ${trade['pnl_dollar']:+.2f} ({trade['pnl_percent']:+.1f}%)"
                                            )
                                            st.write(
                                                f"Duration: {trade['duration_minutes']} minutes"
                                            )
                                            st.write("**Your Commentary:**")
                                            st.write(voice_input)

                                        with col2:
                                            st.write("**AI Analysis:**")
                                            st.write(analysis["ai_analysis"])

                                    # Update trade data
                                    trade["entry_reason"] = voice_input
                                    trade["ai_analysis"] = analysis["ai_analysis"]
                                    trade["trade_grade"] = analysis["trade_grade"]
                                    analyzed_trades.append(trade)

                            # Store analyzed trades in session state
                            st.session_state.analyzed_trades = analyzed_trades

                            # Session analysis
                            if analyzed_trades:
                                session_analysis = analyzer.analyze_trading_session(
                                    analyzed_trades
                                )
                                st.subheader("📊 Session Analysis")
                                st.write(session_analysis)

                elif not ai_analyzer_available:
                    st.warning(
                        "AI Analyzer not available. Check your Anthropic API key in .env file"
                    )

                # Google Sheets Export Section
                if st.session_state.analyzed_trades and sheets_available:
                    st.subheader("📊 Export to Google Sheets")
                    st.write(
                        "Export your analyzed trades to Google Sheets for permanent storage:"
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("🔗 Create New Google Sheet"):
                            with st.spinner(
                                "Creating Google Sheet and uploading data..."
                            ):
                                try:
                                    sheets_client = SimpleTradingJournalSheets()
                                    spreadsheet_id = (
                                        sheets_client.create_trading_journal()
                                    )

                                    if spreadsheet_id:
                                        # Write all analyzed trades
                                        for trade in st.session_state.analyzed_trades:
                                            success = sheets_client.write_trade_record(
                                                trade
                                            )
                                            if not success:
                                                st.error(
                                                    f"Failed to write trade: {trade['symbol']}"
                                                )
                                                break
                                        else:
                                            st.success(
                                                "✅ Successfully exported to Google Sheets!"
                                            )
                                            st.write(
                                                f"🔗 **[Open your trading journal](https://docs.google.com/spreadsheets/d/{spreadsheet_id})**"
                                            )
                                            st.write(
                                                f"Spreadsheet ID: `{spreadsheet_id}`"
                                            )
                                    else:
                                        st.error("Failed to create Google Sheet")

                                except Exception as e:
                                    st.error(f"Export failed: {e}")
                                    st.write(
                                        "Make sure you've completed the OAuth setup for Google Sheets"
                                    )

                    with col2:
                        # CSV Download as backup
                        results_df = pd.DataFrame(st.session_state.analyzed_trades)
                        csv = results_df.to_csv(index=False)

                        st.download_button(
                            label="📁 Download as CSV",
                            data=csv,
                            file_name="ai_trading_analysis.csv",
                            mime="text/csv",
                        )

                elif not sheets_available:
                    st.warning(
                        "Google Sheets integration not available. You can still download as CSV."
                    )

                    if st.session_state.analyzed_trades:
                        results_df = pd.DataFrame(st.session_state.analyzed_trades)
                        csv = results_df.to_csv(index=False)

                        st.download_button(
                            label="📁 Download Analysis Results",
                            data=csv,
                            file_name="ai_trading_analysis.csv",
                            mime="text/csv",
                        )

                # Clean up temp file
                if os.path.exists("temp_trades.csv"):
                    os.remove("temp_trades.csv")

            else:
                st.warning("No complete trades found in your CSV file")

        else:
            st.error("Failed to parse CSV file. Check the format.")


if __name__ == "__main__":
    main()
