import yfinance as yf
import telebot
from telebot import types
import requests
import warnings
import os
import time
from datetime import datetime


warnings.filterwarnings("ignore")

# ─── CONFIGURATION (משתני סביבה מאובטחים) ──────────────────
# הקוד ימשוך את הערכים האלו מה-GitHub Secrets בזמן הריצה
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GM_TOKEN = os.getenv("GM_TOKEN")


PLAY_STORE_URL = "https://play.google.com/store/apps/details?id=com.leumi.iLeumiTrade.UI"

bot = telebot.TeleBot(BOT_TOKEN)

BANKS = {
    "POLI.TA": {"name": "Hapoalim", "weight": 0.335},
    "LUMI.TA": {"name": "Leumi",    "weight": 0.285},
    "MZTF.TA": {"name": "Mizrahi", "weight": 0.175},
    "DSCT.TA": {"name": "Discount", "weight": 0.135},
    "FIBI.TA": {"name": "First Intl","weight": 0.070},
}

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]


def call_gemini(prompt: str) -> str | None:
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 1200, "temperature": 0.85},
    }

    for model in GEMINI_MODELS:
        url = (
            f"https://generativelanguage.googleapis.com"
            f"/v1beta/models/{model}:generateContent"
            f"?key={GM_TOKEN}"
        )
        try:
            print(f"⏳ Trying: {model}")
            resp = requests.post(url, headers=headers, json=payload, timeout=20)

            if resp.status_code == 200:
                data = resp.json()
                text = (
                    data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                    .strip()
                )
                if text:
                    print(f"✅ Success with: {model}")
                    return text
            elif resp.status_code == 404:
                print(f"❌ 404 on {model}, trying next...")
            else:
                print(f"❌ {resp.status_code}: {resp.text[:150]}")

        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout on {model}")
        except Exception as e:
            print(f"❌ Exception: {e}")

    return None


def get_gemini_analysis(bank_results: list, trend: float) -> str | None:
    summary = ", ".join([f"{b['name']} {b['change']:.2f}%" for b in bank_results])
    prompt = (
        f"You are a senior Wall Street analyst covering Israeli equities. "
        f"Today the Israeli banking sector moved {trend:+.2f}% overall. "
        f"Individual moves: {summary}. "
        f"Write exactly 2 sentences MAX. Be concise and sharp. "
        f"DO NOT use numbers, percentages, or digits. "
        f"Name the worst performer, give one macro reason, end with outlook. "
        f"Bloomberg style. Must end with a period. Keep it under 50 words. Must end with a period."
    )
    return call_gemini(prompt)


def get_accurate_change(symbol: str):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5d", interval="1d")
        if len(df) >= 2:
            prev  = float(df["Close"].iloc[-2])
            curr  = float(df["Close"].iloc[-1])
            change = ((curr - prev) / prev) * 100
            return curr, change
    except Exception as e:
        print(f"⚠️ yfinance error for {symbol}: {e}")
    return None, None


def run():
    print("🚀 Starting Israel Banking Sector Bot...")
    results, weighted_sum = [], 0.0

    for symbol, info in BANKS.items():
        price, change = get_accurate_change(symbol)
        if price is not None:
            results.append({"name": info["name"], "change": change})
            weighted_sum += change * info["weight"]

    if not results:
        print("❌ No data. Aborting.")
        return

    ai_insight = get_gemini_analysis(results, weighted_sum)

    if not ai_insight:
        leader = max(results, key=lambda x: abs(x["change"]))
        direction = "advances" if weighted_sum > 0 else "declines"
        ai_insight = (
            f"The Israeli banking sector {direction}, "
            f"with {leader['name']} leading the move, "
            f"reflecting broader market sentiment shifts."
        )

    # HTML encoding - בטוח לחלוטין, אף תו לא יפגע בפורמט
    ai_insight_safe = (
        ai_insight
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    icon = "🟢" if weighted_sum > 0 else "🔴"

    lines = [
        "🏛 <b>ISRAEL BANKING SECTOR: INTELLIGENCE REPORT</b>",
        f"📊 Market Trend: <b>{weighted_sum:+.2f}%</b> {icon}",
        "──────────────────",
    ]
    for b in results:
        b_icon = "🟢" if b["change"] > 0 else "🔴"
        lines.append(f"{b_icon} {b['name']}: <code>{b['change']:+.2f}%</code>")

    lines += [
        "──────────────────",
        "🤖 <b>AI STRATEGIC INSIGHT (Gemini 2.5):</b>",
        ai_insight_safe,
    ]

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Open Leumi Trade", url=PLAY_STORE_URL))

    try:
        bot.send_message(
            CHAT_ID,
            "\n".join(lines),
            parse_mode="HTML",        # ← HTML במקום Markdown
            reply_markup=markup,
        )
        print("✅ Message sent!")
    except Exception as e:
        print(f"❌ Telegram Error: {e}")


if __name__ == "__main__":
    run()


