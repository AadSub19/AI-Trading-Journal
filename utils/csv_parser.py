# utils/csv_parser.py (Updated version)
import pandas as pd
from datetime import datetime
import numpy as np
import pytz


class WebullTradeParser:
    def __init__(self):
        self.raw_orders = None
        self.matched_trades = []

    def parse_webull_csv(self, csv_file_path):
        """
        Parse Webull CSV and extract order data
        """
        try:
            # Read the CSV file
            df = pd.read_csv(csv_file_path)

            print(f"📊 Loaded {len(df)} orders from Webull CSV")
            print(f"📋 Columns: {list(df.columns)}")

            # Clean and standardize the data
            df = self._clean_webull_data(df)

            # Filter only filled orders
            filled_orders = df[df["Status"] == "Filled"].copy()
            print(f"✅ Found {len(filled_orders)} filled orders")

            # Debug: Show first few rows after cleaning
            print("\n🔍 Sample cleaned data:")
            for i, row in filled_orders.head(3).iterrows():
                print(
                    f"  {row['Symbol']} {row['Side']}: {row['Filled Time']} (type: {type(row['Filled Time'])})"
                )

            self.raw_orders = filled_orders
            return filled_orders

        except Exception as e:
            print(f"❌ Error parsing CSV: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _clean_webull_data(self, df):
        """Clean and standardize Webull data with robust datetime handling"""

        # Clean price data (remove @ symbols)
        if "Price" in df.columns:
            df["Price"] = (
                df["Price"].astype(str).str.replace("@", "").str.replace(",", "")
            )
            df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

        # Ensure Avg Price is numeric
        if "Avg Price" in df.columns:
            df["Avg Price"] = pd.to_numeric(df["Avg Price"], errors="coerce")

        # Parse timestamps with proper timezone handling
        if "Filled Time" in df.columns:
            print("🕐 Parsing timestamps...")
            df["Filled Time"] = self._parse_datetime_robust(df["Filled Time"])

            # Check for any failed parsing
            failed_count = df["Filled Time"].isna().sum()
            if failed_count > 0:
                print(f"⚠️ Warning: {failed_count} timestamps failed to parse")
                print("Failed timestamps:")
                failed_rows = df[df["Filled Time"].isna()]
                for i, row in failed_rows.iterrows():
                    print(f"  Row {i}: {row.get('Filled Time', 'N/A')}")

        # Sort by symbol and time for easier matching (handle NaT values)
        df = df.sort_values(["Symbol", "Filled Time"], na_position="last")

        return df

    def _parse_datetime_robust(self, datetime_series):
        """Robust datetime parsing for Webull format"""
        parsed_times = []

        for dt_str in datetime_series:
            try:
                if pd.isna(dt_str) or dt_str == "":
                    parsed_times.append(pd.NaT)
                    continue

                # Convert to string if not already
                dt_str = str(dt_str).strip()

                # Handle Webull format: "09/15/2025 08:27:26 EDT"
                if "EDT" in dt_str:
                    # Remove EDT and parse manually
                    dt_str_clean = dt_str.replace(" EDT", "").strip()
                    dt = pd.to_datetime(dt_str_clean, format="%m/%d/%Y %H:%M:%S")
                    # Add Eastern timezone info
                    eastern = pytz.timezone("US/Eastern")
                    dt = eastern.localize(dt)
                elif "EST" in dt_str:
                    # Handle EST timezone
                    dt_str_clean = dt_str.replace(" EST", "").strip()
                    dt = pd.to_datetime(dt_str_clean, format="%m/%d/%Y %H:%M:%S")
                    eastern = pytz.timezone("US/Eastern")
                    dt = eastern.localize(dt)
                else:
                    # Fallback parsing
                    dt = pd.to_datetime(dt_str, errors="coerce")

                parsed_times.append(dt)

            except Exception as e:
                print(f"⚠️ Failed to parse datetime '{dt_str}': {e}")
                parsed_times.append(pd.NaT)

        return pd.Series(parsed_times)

    def match_trades_with_scaling(self):
        """
        Match buy/sell orders into complete trades with better error handling
        """
        if self.raw_orders is None:
            print("❌ No orders data. Parse CSV first.")
            return []

        trades = []

        # Group by symbol
        for symbol in self.raw_orders["Symbol"].unique():
            try:
                symbol_orders = self.raw_orders[
                    self.raw_orders["Symbol"] == symbol
                ].copy()
                # Filter out rows with invalid timestamps
                symbol_orders = symbol_orders.dropna(subset=["Filled Time"])

                if len(symbol_orders) == 0:
                    print(f"⚠️ No valid orders for {symbol} (all timestamps invalid)")
                    continue

                print(f"🔍 Processing {symbol}: {len(symbol_orders)} orders")
                symbol_trades = self._match_symbol_trades(symbol, symbol_orders)
                trades.extend(symbol_trades)

            except Exception as e:
                print(f"❌ Error processing {symbol}: {e}")
                continue

        self.matched_trades = trades
        print(f"✅ Matched {len(trades)} complete trades")

        return trades

    def _match_symbol_trades(self, symbol, orders):
        """Match trades for a single symbol with scaling support and error handling"""

        trades = []
        position = 0  # Current position size
        avg_cost = 0  # Average cost basis
        entry_time = None
        entry_orders = []  # Track multiple entries

        for _, order in orders.iterrows():
            try:
                if order["Side"] == "Buy":
                    # Handle buy orders (entries or additions)
                    if position == 0:
                        # New position
                        entry_time = order["Filled Time"]
                        avg_cost = order["Avg Price"]
                        position = order["Filled"]
                        entry_orders = [order]
                        print(f"  📈 {symbol} Entry: {position} @ ${avg_cost}")
                    else:
                        # Adding to existing position
                        total_cost = (position * avg_cost) + (
                            order["Filled"] * order["Avg Price"]
                        )
                        position += order["Filled"]
                        avg_cost = total_cost / position
                        entry_orders.append(order)
                        print(
                            f"  ➕ {symbol} Add: +{order['Filled']} @ ${order['Avg Price']} (avg: ${avg_cost:.2f})"
                        )

                elif order["Side"] == "Sell" and position > 0:
                    # Handle sell orders (exits)
                    exit_quantity = min(order["Filled"], position)

                    # Safely calculate duration
                    if (
                        entry_time is not None
                        and not pd.isna(entry_time)
                        and not pd.isna(order["Filled Time"])
                    ):
                        duration_delta = order["Filled Time"] - entry_time
                        duration_minutes = int(duration_delta.total_seconds() / 60)
                    else:
                        duration_minutes = 0
                        print(
                            f"⚠️ Could not calculate duration for {symbol} (invalid timestamps)"
                        )

                    # Calculate scale information
                    remaining_after_exit = position - exit_quantity

                    if remaining_after_exit > 0:
                        # Partial exit (scaling)
                        scale_num = (
                            len(
                                [
                                    t
                                    for t in trades
                                    if t["symbol"] == symbol
                                    and t["entry_time"] == entry_time
                                ]
                            )
                            + 1
                        )
                        total_planned_exits = self._estimate_total_exits(
                            orders, entry_time
                        )
                        scale_info = f"{scale_num}/{total_planned_exits}"
                        position_type = "Scale Out"
                    else:
                        # Final exit
                        scale_num = (
                            len(
                                [
                                    t
                                    for t in trades
                                    if t["symbol"] == symbol
                                    and t["entry_time"] == entry_time
                                ]
                            )
                            + 1
                        )
                        total_exits = scale_num
                        # Update previous trades with correct total
                        for prev_trade in trades:
                            if (
                                prev_trade["symbol"] == symbol
                                and prev_trade["entry_time"] == entry_time
                                and prev_trade["position_type"] == "Scale Out"
                            ):
                                prev_trade["scale_number"] = (
                                    prev_trade["scale_number"].split("/")[0]
                                    + f"/{total_exits}"
                                )

                        scale_info = f"{scale_num}/{total_exits}"
                        position_type = "Final Exit" if scale_num > 1 else "Full Exit"

                    # Safely format times
                    entry_time_str = (
                        entry_time.strftime("%H:%M:%S EDT")
                        if entry_time and not pd.isna(entry_time)
                        else "Unknown"
                    )
                    exit_time_str = (
                        order["Filled Time"].strftime("%H:%M:%S EDT")
                        if not pd.isna(order["Filled Time"])
                        else "Unknown"
                    )
                    date_str = (
                        entry_time.strftime("%Y-%m-%d")
                        if entry_time and not pd.isna(entry_time)
                        else "Unknown"
                    )

                    # Create trade record
                    trade = {
                        "date": date_str,
                        "symbol": symbol,
                        "company_name": order.get("Name", symbol),
                        "entry_price": round(avg_cost, 2),
                        "entry_time": entry_time_str,
                        "exit_price": order["Avg Price"],
                        "exit_time": exit_time_str,
                        "quantity": exit_quantity,
                        "pnl_dollar": round(
                            (order["Avg Price"] - avg_cost) * exit_quantity, 2
                        ),
                        "pnl_percent": round(
                            ((order["Avg Price"] - avg_cost) / avg_cost) * 100, 2
                        ),
                        "duration_minutes": duration_minutes,
                        "scale_number": scale_info,
                        "position_type": position_type,
                        # These will be filled by voice input later
                        "entry_reason": "",
                        "exit_reason": "",
                        "emotional_state": "",
                        "market_context": "",
                        "lessons_learned": "",
                        "ai_analysis": "",
                        "trade_grade": "",
                    }

                    trades.append(trade)
                    print(
                        f"  📉 {symbol} Exit: {exit_quantity} @ ${order['Avg Price']} | P&L: ${trade['pnl_dollar']:+.2f}"
                    )

                    # Update position
                    position -= exit_quantity

                    # If position is closed, reset for next trade
                    if position <= 0:
                        position = 0
                        avg_cost = 0
                        entry_time = None
                        entry_orders = []

            except Exception as e:
                print(f"❌ Error processing order for {symbol}: {e}")
                continue

        return trades

    def _estimate_total_exits(self, orders, entry_time):
        """Estimate total number of exits for scaling trades"""
        try:
            if entry_time is None or pd.isna(entry_time):
                return 1

            future_sells = orders[
                (orders["Filled Time"] > entry_time) & (orders["Side"] == "Sell")
            ]
            return max(len(future_sells), 1)
        except:
            return 1

    def display_trades_summary(self):
        """Display a summary of matched trades"""
        if not self.matched_trades:
            print("📊 No trades to display")
            return

        df = pd.DataFrame(self.matched_trades)

        print(f"\n📊 TRADING SUMMARY:")
        print(f"Total Trades: {len(df)}")
        print(f"Total P&L: ${df['pnl_dollar'].sum():.2f}")
        print(f"Win Rate: {(df['pnl_dollar'] > 0).mean():.1%}")
        print(f"Avg Trade Duration: {df['duration_minutes'].mean():.1f} minutes")

        print(f"\n📋 TRADE DETAILS:")
        for i, trade in enumerate(df.to_dict("records")):
            print(
                f"{i + 1}. {trade['symbol']} | "
                f"{trade['scale_number']} | "
                f"${trade['pnl_dollar']:+.2f} | "
                f"{trade['duration_minutes']}min | "
                f"{trade['entry_time']} → {trade['exit_time']}"
            )

        return df
