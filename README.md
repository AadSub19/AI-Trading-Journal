# AI Trading Journal 🎤📊

> An automated voice-enabled AI trading journal that combines CSV parsing, AI-powered trade analysis, and Google Sheets integration for systematic trading improvement.

---

## ✨ Features

- 🔄 **Automated Trade Parsing**: Import Webull CSV exports and automatically match buy/sell orders into complete trades
- 📈 **Scaling Trade Support**: Handles multiple exits (scale-outs) from single entries
- 🤖 **AI Trade Analysis**: Uses Claude AI to analyze trade execution, psychology, and provide actionable feedback
- 📊 **Persistent Google Sheets**: Maintains one continuous trading journal that builds over time
- 🎤 **Voice/Text Input**: Capture your trade reasoning through voice or text input
- 📉 **Performance Analytics**: Track win rates, P&L, and trading patterns over time

---

## 🛠️ Tech Stack

### 🖥️ Backend

- **Python 3.13**: Core language
- **pandas 2.3.2**: Data manipulation and CSV parsing
- **pytz 2025.2**: Timezone handling for trade timestamps

### 🤖 AI & Analysis

- **anthropic 0.67.0**: Claude API for trade analysis
- **openai 1.107.3**: Whisper API for speech-to-text (future enhancement)

### 🔗 Google Integration

- **google-api-python-client 2.182.0**: Google Sheets API
- **google-auth 2.40.3**: Authentication
- **google-auth-oauthlib 1.2.2**: OAuth flow

### 🌐 Web Interface

- **streamlit 1.49.1**: Web application framework
- **plotly 6.3.0**: Interactive charts and visualizations
