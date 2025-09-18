# ai_analyst/trade_analyzer.py
import anthropic
from config import API_CONFIG


class TradeAnalyzer:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=API_CONFIG["anthropic_api_key"])

    def analyze_trade(self, trade_data, voice_input=None):
        """
        Analyze a single trade with AI insights
        """
        prompt = self._create_analysis_prompt(trade_data, voice_input)

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )

            analysis = response.content[0].text
            grade = self._extract_grade(analysis)

            return {"ai_analysis": analysis, "trade_grade": grade}

        except Exception as e:
            print(f"AI analysis failed: {e}")
            return {"ai_analysis": f"Analysis failed: {e}", "trade_grade": "N/A"}

    def _create_analysis_prompt(self, trade, voice_input):
        """Create analysis prompt for Claude"""

        voice_context = ""
        if voice_input:
            voice_context = f"\n\nTrader's Commentary: {voice_input}"

        prompt = f"""
Analyze this day trade for a trader who focuses on 7-10:30 AM momentum plays:

TRADE DETAILS:
Symbol: {trade["symbol"]} ({trade["company_name"]})
Entry: ${trade["entry_price"]} at {trade["entry_time"]}
Exit: ${trade["exit_price"]} at {trade["exit_time"]}
P&L: ${trade["pnl_dollar"]} ({trade["pnl_percent"]:+.1f}%)
Duration: {trade["duration_minutes"]} minutes
Position Type: {trade["position_type"]}

{voice_context}

Provide analysis in this format:
ANALYSIS: [2-3 sentences about execution, setup quality, and market timing]
LESSON: [Key takeaway for improvement]
GRADE: [A/B/C/D/F based on process, not just outcome]

Focus on:
- Trade execution and timing
- Risk management 
- Emotional factors if mentioned
- Specific improvements for next time
"""
        return prompt

    def _extract_grade(self, analysis):
        """Extract letter grade from analysis"""
        for char in ["A", "B", "C", "D", "F"]:
            if f"GRADE: {char}" in analysis:
                return char
        return "C"  # Default grade

    def analyze_trading_session(self, trades_list):
        """Analyze overall trading session patterns"""

        if not trades_list:
            return "No trades to analyze"

        total_pnl = sum(t["pnl_dollar"] for t in trades_list)
        avg_duration = sum(t["duration_minutes"] for t in trades_list) / len(
            trades_list
        )
        win_rate = sum(1 for t in trades_list if t["pnl_dollar"] > 0) / len(trades_list)

        session_prompt = f"""
Analyze this trading session for a day trader:

SESSION SUMMARY:
Total Trades: {len(trades_list)}
Total P&L: ${total_pnl:.2f}
Win Rate: {win_rate:.1%}
Avg Duration: {avg_duration:.1f} minutes

INDIVIDUAL TRADES:
"""

        for i, trade in enumerate(trades_list, 1):
            session_prompt += f"{i}. {trade['symbol']}: ${trade['pnl_dollar']:+.2f} in {trade['duration_minutes']}min\n"

        session_prompt += """
Provide session analysis focusing on:
1. Overall patterns and recurring issues
2. Risk management assessment  
3. Three specific improvements for next session
4. Psychological/emotional patterns observed

Keep response concise but actionable.
"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=400,
                messages=[{"role": "user", "content": session_prompt}],
            )

            return response.content[0].text

        except Exception as e:
            return f"Session analysis failed: {e}"
