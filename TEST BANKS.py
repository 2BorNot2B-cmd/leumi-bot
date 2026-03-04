import yfinance as yf
import telebot
from telebot import types
import requests
import json
import warnings
import time

warnings.filterwarnings("ignore")

# ─── CONFIGURATION ───────────────────────────────────────────
BOT_TOKEN = "8234419025:AAHLtNHzgjrittzwDkO28GzhoaNcCFAbl30"
CHAT_ID = "1330762467"
HF_TOKEN = "YOUR_HUGGING_FACE_TOKEN_HERE"

PLAY_STORE_URL = "https://play.google.com/store/apps/details?id=com.leumi.iLeumiTrade.UI"

bot = telebot.TeleBot(BOT_TOKEN)

# Bank stocks for TA-Banks5 Index
BANKS = {
    "POLI.TA": {"name": "Hapoalim", "weight": 0.335},
    "LUMI.TA": {"name": "Leumi", "weight": 0.285},
    "MZTF.TA": {"name": "Mizrahi", "weight": 0.175},
    "DSCT.TA": {"name": "Discount", "weight": 0.135},
    "FIBI.TA": {"name": "First Intl", "weight": 0.070},
}


def get_ai_insight_hf(text_data):
    """Fetch financial insight from Mistral AI in English"""
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}

    # Prompt is now strictly in English to avoid encoding issues
    prompt = f"<s>[INST] You are a stock market analyst. Data: {text_data}. Write a 1-sentence professional insight for a trader. [/INST]"

    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 50, "temperature": 0.6}
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=15)
        res_json = response.json()

        # Extract response text
        if isinstance(res_json, list) and len(res_json) > 0:
            raw_text = res_json[0].get('generated_text', '')
            insight = raw_text.split("[/INST]")[-1].strip()
            return insight
        return "Market shows volatility, monitor bank sector closely."
    except Exception as e:
        print(f"❌ AI Error: {e}")
        return "Technical analysis currently unavailable."


def run():
    print(f"🚀 Execution started at {time.strftime('%H:%M:%S')}...")

    results = []
    weighted_sum = 0.0

    for symbol, info in BANKS.items():
        try:
            ticker = yf.Ticker(symbol)
            # Fetch fresh intraday data and daily history for previous close
            hist_daily = ticker.history(period="5d")
            hist_intra = ticker.history(period="1d", interval="1m")

            if not hist_intra.empty and len(hist_daily) >= 2:
                current_price = hist_intra['Close'].iloc[-1]
                prev_close = hist_daily['Close'].iloc[-2]

                change = ((current_price - prev_close) / prev_close) * 100
                results.append({"name": info["name"], "change": change, "weight": info["weight"]})
                weighted_sum += change * info["weight"]
                print(f"✅ {info['name']}: {change:+.2f}%")
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            continue

    if not results:
        print("❌ No data fetched.")
        return

    # 2. Get AI Insight
    print("🤖 Requesting AI Insight...")
    summary_text = ", ".join([f"{b['name']} {b['change']:+.2f}%" for b in results])
    insight = get_ai_insight_hf(f"Index change: {weighted_sum:+.2f}% | Components: {summary_text}")

    # 3. Build Telegram Message
    icon = "🟢" if weighted_sum > 0 else "🔴"

    lines = [
        f"🏦 *TA-BANKS5 INDEX UPDATE*",
        f"📊 Trend: *{weighted_sum:+.2f}%* {icon}",
        "──────────────────"
    ]

    for b in results:
        b_icon = "🟢" if b["change"] > 0 else "🔴"
        lines.append(f"{b_icon} {b['name']}: `{b['change']:+.2f}%`")

    lines += ["──────────────────", f"🤖 *AI Analysis:*", f"_{insight}_"]
    lines += ["──────────────────", "👇 Quick Actions:"]

    # 4. Keyboard and Send
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Open Leumi Trade", url=PLAY_STORE_URL))

    try:
        bot.send_message(CHAT_ID, "\n".join(lines), parse_mode="Markdown", reply_markup=markup)
        print("✅ Message sent successfully!")
    except Exception as e:
        print(f"❌ Telegram error: {e}")


if __name__ == "__main__":
    run()