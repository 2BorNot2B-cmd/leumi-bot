import yfinance as yf
import telebot
from telebot import types
import requests
import warnings
import time
import os
from datetime import datetime

warnings.filterwarnings("ignore")

# ─── CONFIGURATION (משתני סביבה מאובטחים) ──────────────────
# הקוד ימשוך את הערכים האלו מה-GitHub Secrets בזמן הריצה
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HF_TOKEN = os.getenv("HF_TOKEN")

PLAY_STORE_URL = "https://play.google.com/store/apps/details?id=com.leumi.iLeumiTrade.UI"

# בדיקה בסיסית שהסודות נטענו
if not BOT_TOKEN or not CHAT_ID:
    print("❌ Critical Error: Missing Telegram Secrets!")
    # במחשב האישי שלך אתה יכול לשים את הטוקן פה זמנית לבדיקה, 
    # אבל לעולם אל תעלה אותו ל-GitHub ככה!
    # BOT_TOKEN = "כאן הטוקן שלך רק לבדיקה מקומית"

bot = telebot.TeleBot(BOT_TOKEN)

BANKS = {
    "POLI.TA": {"name": "Hapoalim", "weight": 0.335},
    "LUMI.TA": {"name": "Leumi", "weight": 0.285},
    "MZTF.TA": {"name": "Mizrahi", "weight": 0.175},
    "DSCT.TA": {"name": "Discount", "weight": 0.135},
    "FIBI.TA": {"name": "First Intl", "weight": 0.070},
}

def get_ai_insight_hf(text_data):
    if not HF_TOKEN:
        return "AI Insight unavailable: Missing API Token."
        
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    prompt = f"<s>[INST] You are a stock market analyst. Data: {text_data}. Write a 1-sentence professional insight for a trader. [/INST]"
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 50, "temperature": 0.6}}

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=15)
        res_json = response.json()
        if isinstance(res_json, list) and len(res_json) > 0:
            return res_json[0].get('generated_text', '').split("[/INST]")[-1].strip()
        return "Market shows volatility, monitor bank sector closely."
    except Exception:
        return "Technical analysis currently unavailable."

def get_accurate_change(symbol):
    try:
        # פתרון החגים: לוקחים 7 ימים כדי להבטיח שיש נתוני מסחר
        df = yf.download(symbol, period="7d", interval="1d", progress=False)
        if len(df) >= 2:
            current_close = float(df['Close'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2])
            change = ((current_close - prev_close) / prev_close) * 100
            return current_close, change
        return None, None
    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return None, None

def run():
    print(f"🚀 Execution started at {time.strftime('%H:%M:%S')}...")
    results = []
    weighted_sum = 0.0

    for symbol, info in BANKS.items():
        price, change = get_accurate_change(symbol)
        if price is not None:
            results.append({"name": info["name"], "change": change, "weight": info["weight"]})
            weighted_sum += (change * info["weight"])
            print(f"✅ {info['name']}: {change:+.2f}%")

    if not results:
        return

    summary_text = ", ".join([f"{b['name']} {b['change']:+.2f}%" for b in results])
    insight = get_ai_insight_hf(f"Index change: {weighted_sum:+.2f}% | Components: {summary_text}")

    icon = "🟢" if weighted_sum > 0 else "🔴"
    lines = [
        f"🏦 *TA-BANKS5 INDEX UPDATE*",
        f"📊 Trend: *{weighted_sum:+.2f}%* {icon}",
        f"🕒 Time: _{datetime.now().strftime('%H:%M')}_",
        "──────────────────"
    ]

    for b in results:
        b_icon = "🟢" if b["change"] > 0 else "🔴"
        lines.append(f"{b_icon} {b['name']}: `{b['change']:+.2f}%`")

    lines += ["──────────────────", "🤖 *AI Analysis:*", f"_{insight}_", "──────────────────", "👇 Quick Actions:"]
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Open Leumi Trade", url=PLAY_STORE_URL))

    try:
        bot.send_message(CHAT_ID, "\n".join(lines), parse_mode="Markdown", reply_markup=markup)
        print("✅ Success! Message sent.")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

if __name__ == "__main__":
    run()
