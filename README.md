# 🏛️ Israel Banking Sector Intelligence Bot

An automated financial analysis tool that monitors the 5 major Israeli banks and provides institutional-grade insights via Telegram.

## 🚀 Overview
This project was born out of a personal need to track the Israeli banking sector's performance in real-time, specifically before the daily mutual fund "cut-off" times (שעת ההקשה). The bot automates data collection, calculates sector-wide trends, and leverages Generative AI for market sentiment analysis.

## 📸 Preview
<img width="517" height="406" alt="image" src="https://github.com/user-attachments/assets/20f2af36-6c56-43ee-9e82-273cabefcd0d" />

## ✨ Key Features
* **Real-time Data:** Fetches live stock prices for Hapoalim, Leumi, Mizrahi, Discount, and First International using `yfinance`.
* **Market Benchmarking:** Compares sector-wide performance against the **TA-125 Index** to identify relative strength.
* **AI Strategic Insight:** Integrates **Google Gemini 2.5 Flash** to generate concise, 2-sentence market summaries in a professional Bloomberg/Reuters style.
* **Fully Automated:** Runs every trading day (Mon-Fri) via **GitHub Actions** (Serverless architecture).
* **Smart UI:** Sends clean HTML-formatted reports to Telegram with interactive action buttons.

## 🛠️ Tech Stack
* **Language:** Python 3.10+
* **Libraries:** `yfinance`, `pyTelegramBotAPI`, `requests`
* **AI Engine:** Google Gemini API (Generative Language API)
* **Automation:** GitHub Actions (Cron scheduled)

## ⚙️ Setup & Installation
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`.
3. Configure GitHub Secrets for:
   * `TELEGRAM_BOT_TOKEN`
   * `TELEGRAM_CHAT_ID`
   * `GM_TOKEN` (Gemini API Key)

## ⚠️ Disclaimer
This project is for **educational and personal use only**. The data and AI-generated insights do not constitute financial advice, investment recommendations, or a substitute for professional consultation. The author is not responsible for any financial decisions made based on this tool.
